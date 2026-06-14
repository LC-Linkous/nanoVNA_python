"""Run the full nvnapython test suite (mock + hardware).

Mirrors the tinySA_python test runner pattern: a plain script you can
run from anywhere, no pytest flags to remember.

    uv run python tests/run_all_tests.py            # mock tests only
    uv run python tests/run_all_tests.py hardware   # hardware tests only
    uv run python tests/run_all_tests.py all        # everything

Works from any directory: it anchors pytest's rootdir to the project
folder this file lives in, so the 'inifile: None' / wrong-rootdir
problem can't happen.
"""
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent  # the nvnapython/ dir


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else "mock"
    base = ["--rootdir", str(PROJECT_ROOT), str(PROJECT_ROOT / "tests")]

    if mode == "mock":
        args = ["-m", "not hardware", *base]
    elif mode == "hardware":
        args = ["-m", "hardware", *base]
    elif mode == "all":
        # No marker filter: collect and run everything. (Hardware tests still
        # self-skip via conftest when no device is detected.)
        args = [*base]
    else:
        print(f"unknown mode '{mode}'; use: mock | hardware | all")
        return 2

    print(f"Running {mode} tests from {PROJECT_ROOT}")
    return pytest.main(args)


if __name__ == "__main__":
    raise SystemExit(main())
