#!/usr/bin/env bash
# StitchGauge installer.
#
# Installs project-level dependencies only (runtime: standard library only, so
# the pinned test runner is the only package), then makes the optional
# `stitchgauge` console script available and proves the module imports.
# Safe to re-run. Never uses sudo/system packages, never starts the tool.
set -euo pipefail
cd "$(dirname "$0")"

PYTHON="${PYTHON:-python3}"

echo "==> Upgrading pip/setuptools/wheel"
"$PYTHON" -m pip install --upgrade pip setuptools wheel

echo "==> Installing declared dependencies (requirements.txt)"
"$PYTHON" -m pip install -r requirements.txt

echo "==> Installing the stitchgauge console script (editable, no deps)"
if ! "$PYTHON" -m pip install --no-deps -e .; then
    # Unprivileged systems may only allow a per-user install.
    "$PYTHON" -m pip install --no-deps --user -e .
fi

echo "==> Import self-check"
"$PYTHON" -c 'import stitchgauge; print("stitchgauge", stitchgauge.VERSION, "imports OK")'

echo "==> Verifying the CLI runs"
"$PYTHON" stitchgauge.py --version

cat <<'DONE'

Setup complete.

  Run the interactive menu : python3 stitchgauge.py
  Run the demo             : bash demo.sh
  Run the tests            : python3 -m pytest    (or: python3 -m unittest discover -s tests)
DONE
