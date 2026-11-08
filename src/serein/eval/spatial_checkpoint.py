"""Retain completed spatial ensemble members across interrupted local runs."""

from __future__ import annotations

import hashlib
import io
import json
import uuid
from pathlib import Path

import numpy as np


class MemberCache:
    def __init__(self, root: Path, plan: dict, *, resume: bool = False):
        self.root = root
        self.reused = 0
        path = root / "run_plan.json"
        if resume:
            if (root / "manifest.json").exists():
                raise ValueError("experiment is already complete; choose a new output")
            if json.loads(path.read_text(encoding="utf-8")) != plan:
                raise ValueError("resume inputs, code, settings or runtime do not match run_plan.json")
        else:
            path.write_text(json.dumps(plan, indent=2, allow_nan=False) + "\n", encoding="utf-8")

    def load(self, model, seed, *, calibration_shape, prediction_shape):
        import torch

        parent = self.root / "members" / f"{model}_{seed}"
        completed = sorted(parent.glob("*/member.json"))
        if not completed:
            return None
        if len(completed) != 1:
            raise ValueError(f"ambiguous member checkpoints for {model}, seed {seed}")
        marker = completed[0]
        metadata = json.loads(marker.read_text(encoding="utf-8"))
        if metadata.get("model") != model or metadata.get("seed") != seed:
            raise ValueError("member checkpoint identity does not match its directory")
        payloads = {}
        for name in ("state.pt", "predictions.npz"):
            payload = (marker.parent / name).read_bytes()
            if hashlib.sha256(payload).hexdigest() != metadata["sha256"][name]:
                raise ValueError(f"member checkpoint checksum mismatch: {model}, seed {seed}, {name}")
            payloads[name] = payload
        state = torch.load(io.BytesIO(payloads["state.pt"]), map_location="cpu", weights_only=True)
        with np.load(io.BytesIO(payloads["predictions.npz"]), allow_pickle=False) as arrays:
            calibration, prediction = arrays["calibration"], arrays["prediction"]
        if (calibration.shape != calibration_shape or prediction.shape != prediction_shape
                or calibration.dtype != np.float32 or prediction.dtype != np.float32
                or np.isinf(calibration).any() or np.isinf(prediction).any()):
            raise ValueError("member checkpoint prediction shape or values do not match the experiment")
        self.reused += 1
        return state, calibration, prediction, metadata["history"]

    def save(self, model, seed, state, calibration, prediction, history):
        import torch

        # Keep interrupted attempts intact; a new attempt never overwrites them.
        attempt = self.root / "members" / f"{model}_{seed}" / uuid.uuid4().hex
        attempt.mkdir(parents=True, exist_ok=False)
        torch.save(state, attempt / "state.pt")
        np.savez_compressed(attempt / "predictions.npz", calibration=calibration, prediction=prediction)
        metadata = {"model": model, "seed": seed, "history": history,
                    "sha256": {name: hashlib.sha256((attempt / name).read_bytes()).hexdigest()
                               for name in ("state.pt", "predictions.npz")}}
        marker = attempt / "member.json.tmp"
        marker.write_text(json.dumps(metadata, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        marker.rename(attempt / "member.json")
