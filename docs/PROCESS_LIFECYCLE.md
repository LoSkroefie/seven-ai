# Command and Process Lifecycle

Seven has unrestricted L4 command and Python execution. Completion therefore requires ownership of processes Seven starts, including descendants.

`seven/runtime/process.py` starts commands in a distinct process group/session, captures output and enforces timeouts. On timeout it discovers descendants through `psutil`, terminates descendants before the parent, waits for graceful exit, kills survivors and records affected process IDs. A dedicated ordering regression test prevents the parent-first orphaning bug found during daemon completion work.

`run_shell` and `run_python` use this shared runner. Their result includes exit code, stdout, stderr and explicit timeout/process-tree evidence.

This is lifecycle control, not sandboxing. Commands retain the logged-in user's normal environment and host access. The baseline `subprocess.run(..., timeout=...)` could stop waiting while descendant processes survived independently.

Shell, generated Python, coding agents, SSH, music workers and daemon shutdown use the shared ownership rules where their lifecycle requires subprocess cleanup.
