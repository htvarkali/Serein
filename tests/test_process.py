import ctypes
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from serein.eval.process import run_logged


def run_python(tmp_path, code, *, timeout=5, env=None, arguments=()):
    with (tmp_path / "child.log").open("w", encoding="utf-8") as stream:
        return run_logged([sys.executable, "-c", code, *arguments], cwd=tmp_path,
                          env=os.environ.copy() if env is None else env,
                          stdout=stream, timeout=timeout)


def test_logged_child_preserves_arguments_unicode_directory_and_exit_code(tmp_path):
    root = tmp_path / "working directory with spaces"
    root.mkdir()
    env = dict(os.environ, SEREIN_PROCESS_PROBE="test \u00b5 value", PYTHONIOENCODING="utf-8")
    arguments = ('a b', 'quote"inside', 'trailing\\', '', '\u00b5g/m3', '$HOME', 'literal`text')
    code = ("import json,os,sys; "
            "print(json.dumps([os.getcwd(), os.environ['SEREIN_PROCESS_PROBE'], sys.argv[1:]])); "
            "print('child stderr',file=sys.stderr); sys.exit(7)")
    result = run_python(root, code, env=env, arguments=arguments)
    assert result.returncode == 7
    log = (root / "child.log").read_text(encoding="utf-8").splitlines()
    assert log[0].startswith("process pid: ")
    data = json.loads(next(line for line in log if line.startswith("[")))
    assert Path(data[0]) == root
    assert data[1] == "test \u00b5 value"
    assert data[2] == list(arguments)
    assert "child stderr" in log
    assert "SEREIN_PROCESS_PROBE" not in os.environ


def test_child_has_noninteractive_empty_standard_input(tmp_path):
    assert run_python(tmp_path, "import sys; assert sys.stdin.read() == ''").returncode == 0


@pytest.mark.parametrize("exit_code", [0, 7])
def test_finished_parent_does_not_leave_workers_behind(tmp_path, exit_code):
    marker = tmp_path / "survived.txt"
    child = ("import pathlib,time; time.sleep(.8); "
             f"pathlib.Path({str(marker)!r}).write_text('survived')")
    code = ("import subprocess,sys; "
            f"subprocess.Popen([sys.executable, '-c', {child!r}]); sys.exit({exit_code})")
    assert run_python(tmp_path, code).returncode == exit_code
    time.sleep(1)
    assert not marker.exists()


def test_timeout_kills_owned_processes_and_keeps_unrelated_process_alive(tmp_path):
    outside = tmp_path / "outside.txt"
    inside = tmp_path / "inside.txt"
    code = lambda path: ("import pathlib,time; time.sleep(.8); "
                         f"pathlib.Path({str(path)!r}).write_text('finished')")
    unrelated = subprocess.Popen([sys.executable, "-c", code(outside)])
    try:
        with pytest.raises(subprocess.TimeoutExpired):
            run_python(tmp_path, code(inside), timeout=.2)
        assert unrelated.wait(timeout=5) == 0
        assert outside.exists()
        assert not inside.exists()
    finally:
        if unrelated.poll() is None:
            unrelated.kill()
            unrelated.wait(timeout=5)


@pytest.mark.skipif(os.name != "nt", reason="native Windows job behavior")
def test_job_configuration_failure_cannot_run_an_uncontained_child(tmp_path, monkeypatch):
    from serein.eval import windows_process

    actual = windows_process._api()
    marker = tmp_path / "should_not_start.txt"

    class DeniedJobList:
        def __getattr__(self, name):
            return getattr(actual, name)

        def UpdateProcThreadAttribute(self, attributes, flags, attribute, *args):
            if attribute == 0x2000D:
                ctypes.set_last_error(5)
                return 0
            return actual.UpdateProcThreadAttribute(attributes, flags, attribute, *args)

    monkeypatch.setattr(windows_process, "_api", DeniedJobList)
    with pytest.raises(OSError):
        run_python(tmp_path, f"import pathlib; pathlib.Path({str(marker)!r}).write_text('started')")
    assert not marker.exists()


@pytest.mark.skipif(os.name != "nt", reason="native Windows job behavior")
def test_interrupt_while_waiting_cleans_up_descendants(tmp_path, monkeypatch):
    from serein.eval import windows_process

    actual = windows_process._api()
    marker = tmp_path / "survived.txt"
    ready = tmp_path / "started.txt"
    child = ("import pathlib,time; "
             f"pathlib.Path({str(ready)!r}).write_text('started'); time.sleep(.8); "
             f"pathlib.Path({str(marker)!r}).write_text('survived')")
    code = ("import subprocess,sys,time; "
            f"subprocess.Popen([sys.executable, '-c', {child!r}]); time.sleep(2)")

    class InterruptedWait:
        interrupted = False

        def __getattr__(self, name):
            return getattr(actual, name)

        def WaitForSingleObject(self, handle, milliseconds):
            if not self.interrupted and ready.exists():
                self.interrupted = True
                raise KeyboardInterrupt
            return actual.WaitForSingleObject(handle, milliseconds)

    monkeypatch.setattr(windows_process, "_api", InterruptedWait)
    with pytest.raises(KeyboardInterrupt):
        run_python(tmp_path, code)
    assert ready.exists()
    time.sleep(1)
    assert not marker.exists()


@pytest.mark.skipif(os.name != "nt", reason="native Windows handles")
def test_windows_handle_count_is_stable_across_repeated_commands(tmp_path):
    from ctypes import wintypes

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    kernel.GetProcessHandleCount.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
    kernel.GetProcessHandleCount.restype = wintypes.BOOL

    def count():
        handles = wintypes.DWORD()
        assert kernel.GetProcessHandleCount(kernel.GetCurrentProcess(), ctypes.byref(handles))
        return handles.value

    run_python(tmp_path, "pass")
    before = count()
    for _ in range(12):
        assert run_python(tmp_path, "pass").returncode == 0
    # Other code in the test process can close handles during the loop; only growth is a leak.
    assert count() <= before


@pytest.mark.skipif(os.name != "nt", reason="native Windows handle inheritance")
def test_unrelated_inheritable_event_is_not_available_to_the_child(tmp_path):
    from ctypes import wintypes

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateEventW.argtypes = [ctypes.c_void_p, wintypes.BOOL, wintypes.BOOL, wintypes.LPCWSTR]
    kernel.CreateEventW.restype = wintypes.HANDLE
    kernel.SetHandleInformation.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.DWORD]
    kernel.SetHandleInformation.restype = wintypes.BOOL
    kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel.WaitForSingleObject.restype = wintypes.DWORD
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    event = kernel.CreateEventW(None, True, False, None)
    assert event
    try:
        assert kernel.SetHandleInformation(event, 1, 1)
        code = ("import ctypes; from ctypes import wintypes; "
                "k=ctypes.WinDLL('kernel32'); k.SetEvent.argtypes=[wintypes.HANDLE]; "
                f"k.SetEvent({event})")
        assert run_python(tmp_path, code).returncode == 0
        assert kernel.WaitForSingleObject(event, 0) == 0x102
    finally:
        kernel.CloseHandle(event)


@pytest.mark.skipif(os.name != "nt", reason="Windows jobs close when their owner exits")
def test_abrupt_owner_exit_cannot_leave_a_job_worker_running(tmp_path):
    ready, marker = tmp_path / "ready.txt", tmp_path / "survived.txt"
    child = ("import pathlib,time; "
             f"pathlib.Path({str(ready)!r}).write_text('ready'); time.sleep(.8); "
             f"pathlib.Path({str(marker)!r}).write_text('survived')")
    parent = f"""
import os,sys,threading,time
from pathlib import Path
from serein.eval.process import run_logged
def exit_when_ready():
    deadline=time.monotonic()+5
    while time.monotonic()<deadline:
        if Path({str(ready)!r}).exists():
            os._exit(0)
        time.sleep(.01)
    os._exit(7)
threading.Thread(target=exit_when_ready,daemon=True).start()
with Path({str(tmp_path / 'owner.log')!r}).open('w',encoding='utf-8') as log:
    run_logged([sys.executable,'-c',{child!r}],cwd=Path.cwd(),env=os.environ.copy(),stdout=log,timeout=5)
"""
    result = subprocess.run([sys.executable, "-c", parent], check=False, timeout=10)
    assert result.returncode == 0
    assert ready.exists()
    time.sleep(1)
    assert not marker.exists()


@pytest.mark.skipif(os.name != "nt", reason="native Windows job accounting")
def test_cleanup_accounting_failure_is_reported_instead_of_success(tmp_path, monkeypatch):
    from serein.eval import windows_process

    actual = windows_process._api()

    class UnavailableAccounting:
        def __getattr__(self, name):
            return getattr(actual, name)

        def QueryInformationJobObject(self, *args):
            ctypes.set_last_error(5)
            return 0

    monkeypatch.setattr(windows_process, "_api", UnavailableAccounting)
    with pytest.raises(OSError):
        run_python(tmp_path, "pass")
