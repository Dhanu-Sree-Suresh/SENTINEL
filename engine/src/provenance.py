"""
Shared provenance-record helper.

Every results JSON this repo produces includes one of these records,
so a result can never be silently detached from the exact code/config
that produced it -- the brief's "result integrity" requirement.
"""
import subprocess
import sys
import time
import numpy as np


def get_provenance(**extra):
    try:
        git_commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL
        ).decode().strip()
    except Exception:
        git_commit = "not_a_git_repo"
    record = {
        "timestamp_unix": time.time(),
        "git_commit": git_commit,
        "python_version": sys.version,
        "numpy_version": np.__version__,
    }
    record.update(extra)
    return record
