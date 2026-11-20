"""Development scripts must stop at failures instead of printing false success."""

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(os.name == "nt", reason="POSIX shell scripts")

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
STEPS = ["dev", "figures", "impact", "map", "dev_holdout", "abl_full", "abl_no_wind",
         "abl_no_hrrr", "abl_no_aqm", "abl_no_fires", "abl_no_hms", "abl_no_sensors"]


@pytest.fixture
def script_repo(tmp_path):
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    for name in ("run_dev_suite.sh", "run_ablations.sh", "run_scale_suite.sh", "sweep_graph.sh",
                 "sweep_peaks.sh"):
        shutil.copy2(SCRIPTS / name, scripts / name)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    uv = bin_dir / "uv"
    uv.write_text(f"#!{sys.executable}\n" + '''
import os
import sys

args = sys.argv[1:]
if "--tag" in args:
    step = args[args.index("--tag") + 1]
elif "serein.eval.figures" in args:
    step = "figures"
elif "serein.eval.impact" in args:
    step = "impact"
elif "map" in args:
    step = "map"
elif "scripts/compare_runs.py" in args:
    step = "compare_runs"
elif "build-table" in args:
    step = "conus_table_" + args[args.index("--split") + 1]
else:
    raise SystemExit("unexpected command")
with open(os.environ["SEREIN_TEST_CALLS"], "a") as handle:
    handle.write(step + "\\n")
if step == os.environ.get("SEREIN_TEST_FAIL"):
    print("injected failure in " + step)
    raise SystemExit(7)
print("completed " + step)
''')
    uv.chmod(0o755)
    env = {"PATH": str(bin_dir) + os.pathsep + os.environ["PATH"],
           "SEREIN_TEST_CALLS": str(tmp_path / "calls.txt")}
    return tmp_path, env


@pytest.mark.parametrize("step", ["dev", "figures", "impact", "map", "dev_holdout",
                                  "abl_full", "abl_no_wind"])
def test_dev_suite_stops_and_reports_failed_step(script_repo, step):
    repo, env = script_repo
    env["SEREIN_TEST_FAIL"] = step
    result = subprocess.run(["bash", "scripts/run_dev_suite.sh"], cwd=repo, env=env,
                            capture_output=True, text=True, check=False, timeout=10)

    assert result.returncode == 7
    assert "ALLDONE" not in result.stdout
    assert "FAILED (exit 7): see " in result.stderr
    assert (repo / "calls.txt").read_text().splitlines() == STEPS[:STEPS.index(step) + 1]
    log_path = result.stderr.strip().split("see ")[-1]
    assert "injected failure" in (repo / log_path).read_text()


def test_dev_suite_runs_every_step_before_reporting_success(script_repo):
    repo, env = script_repo
    result = subprocess.run(["bash", "scripts/run_dev_suite.sh"], cwd=repo, env=env,
                            capture_output=True, text=True, check=False, timeout=10)

    assert result.returncode == 0, result.stderr
    assert (repo / "calls.txt").read_text().splitlines() == STEPS
    assert result.stdout.rstrip().endswith("ALLDONE")


@pytest.mark.parametrize(("script", "failed_step", "called_steps"), [
    ("run_scale_suite.sh", "scale_s", ["scale_s"]),
    ("run_scale_suite.sh", "conus_table_train",
     ["scale_s", "scale_m", "scale_l", "hist4", "hist7", "conus_table_train"]),
    ("sweep_graph.sh", "sweep_mask0_reg", ["sweep_mask0_reg"]),
    ("sweep_peaks.sh", "peaks_w3", ["peaks_w1", "peaks_w3"]),
])
def test_research_sweeps_stop_when_a_command_fails(script_repo, script, failed_step, called_steps):
    repo, env = script_repo
    env["SEREIN_TEST_FAIL"] = failed_step
    result = subprocess.run([str(repo / "scripts" / script)], cwd=repo, env=env,
                            capture_output=True, text=True, check=False, timeout=10)

    assert result.returncode == 7
    assert "ALLDONE" not in result.stdout
    assert f"FAILED (exit 7): see outputs/logs/{failed_step}.log" in result.stderr
    assert (repo / "calls.txt").read_text().splitlines() == called_steps
    assert "injected failure" in (repo / "outputs/logs" / f"{failed_step}.log").read_text()
