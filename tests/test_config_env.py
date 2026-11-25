"""load_env reads the optional .env file the same way on every system."""

import os

from serein import config


def test_load_env_reads_a_file_saved_with_a_byte_order_mark(tmp_path, monkeypatch):
    # Windows PowerShell 5.1 writes this mark with Out-File or Set-Content -Encoding utf8.
    (tmp_path / ".env").write_bytes(b"\xef\xbb\xbfFIRMS_MAP_KEY=first\r\nPURPLEAIR_API_KEY=second\r\n")
    env = {}
    monkeypatch.setattr(config, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(os, "environ", env)
    config.load_env()
    assert env == {"FIRMS_MAP_KEY": "first", "PURPLEAIR_API_KEY": "second"}


def test_load_env_keeps_shell_values_and_skips_comments(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text(
        "# FIRMS_MAP_KEY=commented_out\n\nFIRMS_MAP_KEY=from_file\n"
        "PURPLEAIR_API_KEY = \"has=sign\"\nnot a setting\n",
        encoding="utf-8",
    )
    env = {"FIRMS_MAP_KEY": "from_shell"}
    monkeypatch.setattr(config, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(os, "environ", env)
    config.load_env()
    assert env == {"FIRMS_MAP_KEY": "from_shell", "PURPLEAIR_API_KEY": "has=sign"}


def test_load_env_without_a_file_changes_nothing(tmp_path, monkeypatch):
    env = {"FIRMS_MAP_KEY": "from_shell"}
    monkeypatch.setattr(config, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(os, "environ", env)
    config.load_env()
    assert env == {"FIRMS_MAP_KEY": "from_shell"}
