"""Start a command in its own session so it outlives the shell that launched it."""

import subprocess
import sys

log = open(sys.argv[1], "a")
subprocess.Popen(
    sys.argv[2:],
    stdout=log,
    stderr=subprocess.STDOUT,
    stdin=subprocess.DEVNULL,
    start_new_session=True,
)
print("detached:", " ".join(sys.argv[2:]))
