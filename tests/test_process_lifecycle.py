from __future__ import annotations

import sys
import time
from pathlib import Path

from seven.runtime.process import run_tracked


def test_timeout_terminates_descendant_process(tmp_path):
    marker = tmp_path / "child-survived.txt"
    child_code = f"import time; time.sleep(1.2); open({str(marker)!r}, 'w').write('survived')"
    parent = tmp_path / "parent.py"
    parent.write_text(
        "import subprocess, sys, time\n"
        f"subprocess.Popen([sys.executable, '-c', {child_code!r}])\n"
        "time.sleep(30)\n",
        encoding="utf-8",
    )
    result = run_tracked([sys.executable, str(parent)], timeout=0.3)
    assert result.timed_out is True
    assert result.terminated_pids
    time.sleep(1.4)
    assert marker.exists() is False


def test_output_and_exit_code_are_preserved():
    result = run_tracked(
        [sys.executable, "-c", "import sys; print('out'); print('err', file=sys.stderr); raise SystemExit(7)"],
        timeout=5,
    )
    assert result.timed_out is False
    assert result.returncode == 7
    assert result.stdout.strip() == "out"
    assert result.stderr.strip() == "err"
