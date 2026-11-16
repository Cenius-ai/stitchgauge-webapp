# Installing StitchGauge

StitchGauge has **no runtime dependencies**. Unpack it, run
`python3 stitchgauge.py`, done. The optional installer below adds the pinned
test runner and a `stitchgauge` console script (handy for typing
`stitchgauge gauge …` instead of `python3 stitchgauge.py gauge …`).

## Prerequisites (not installed by any script)

| Requirement | Notes |
|-------------|-------|
| Python 3.8 or newer | Any CPython from python.org, your distro, or Homebrew. Check with `python3 --version`. |
| pip (optional) | Only needed for the console script and the test runner; comes with CPython and every distro package. |
| A terminal | Linux, macOS or the Windows console / PowerShell. |

There are no system packages to install: no compiler, no database, no service.
Nothing in this project requires `sudo`.

## Step 1 - install (one command, and it exits)

```bash
bash install.sh
```

It runs, in order:

1. `python3 -m pip install --upgrade pip setuptools wheel`
2. `python3 -m pip install -r requirements.txt` (the only pinned package is
   `pytest`, the test runner; the runtime needs nothing)
3. `python3 -m pip install --no-deps -e .` (the optional `stitchgauge` console
   script)
4. an import self-check, so a broken environment fails loudly here instead of
   at first use

The script is idempotent - run it again any time. It **installs only** and
exits: it never starts the tool and never opens a prompt.

Skipping the installer is fully supported: `python3 stitchgauge.py` works from
the unpacked folder with no install at all.

## Step 2 - run it

```bash
python3 stitchgauge.py                    # interactive menu
python3 stitchgauge.py --help             # full flag reference
python3 stitchgauge.py yarn --table       # e.g. the standard weight table
```

## Step 3 - run the tests

```bash
python3 -m pytest                 # if pip installed the pinned runner
python3 -m unittest discover -s tests   # standard library only, no install
```

The suite drives the real script as a subprocess: it checks the three
calculators, the validation rules in both modes, the exit-code contract, and
that the interactive and one-shot paths print identical result blocks.

## Step 4 - see the demo

```bash
bash demo.sh
```

Runs all three calculators end to end, non-interactively (including an invalid
value and an out-of-range gauge), in well under a second.

## Uninstalling

```bash
python3 -m pip uninstall stitchgauge
rm -rf __pycache__ tests/__pycache__ .pytest_cache *.egg-info
```

Nothing else is written to your machine: no config file, no cache, no database.
