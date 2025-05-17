#!/usr/bin/env python3
"""
Script to check for mypy errors
"""
import sys
import subprocess
from typing import Tuple

def run_cmd(cmd: str) -> Tuple[str, str, int]:
    """Run a command and return its output and exit code"""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip(), result.stderr.strip(), result.returncode

# Run mypy with types-requests
stdout, stderr, exit_code = run_cmd("cd /root/projects/animal_names && /root/projects/animal_names/.venv/bin/mypy --ignore-missing-imports src/")

# Print the result
print("\nMyPy Result:")
if stdout:
    print(stdout)
if stderr:
    print(stderr)

print(f"\nExit code: {exit_code}")
if exit_code == 0:
    print("SUCCESS: No mypy errors found!")
    sys.exit(0)
else:
    print("ERROR: Mypy still has issues!")
    sys.exit(1)
