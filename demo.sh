#!/usr/bin/env bash
# StitchGauge demo: exercises all three calculators end to end, non-interactively.
#
# Nothing is installed, nothing is downloaded, and no prompt ever waits for a
# human - the interactive menu is driven from a here-string so the recording
# shows real output.
set -euo pipefail
cd "$(dirname "$0")"

PYTHON="${PYTHON:-python3}"
SG=("$PYTHON" stitchgauge.py)

section() {
    printf '\n================================================================\n'
    printf '%s\n' "$1"
    printf '================================================================\n'
}

section "1) Gauge calculator - a 40-stitch, 56-row swatch on 8 x 8 inches"
"${SG[@]}" gauge --stitches 40 --rows 56 --width 8 --height 8

section "2) Adjust for your gauge - pattern 5 sts/7 rows, yours 5.5 sts/7.5 rows"
"${SG[@]}" adjust --pattern-sts 5 --pattern-rows 7 --your-sts 5.5 --your-rows 7.5 \
    --stitches 100 --rows 120

section "3) Yarn weight lookup - 4.0 sts/in"
"${SG[@]}" yarn --gauge 4.0

section "4) Yarn weight lookup - 12.0 sts/in is outside the table"
"${SG[@]}" yarn --gauge 12.0

section "5) The full seven-category standard weight table"
"${SG[@]}" yarn --table

section "6) Bad input: one-shot mode fails once on stderr and exits 1"
set +e
"${SG[@]}" gauge --stitches 40 --rows 56 --width 0 --height 8
status=$?
set -e
printf 'exit status: %s (1 = invalid value)\n' "$status"

section "7) The interactive menu driving the same calculations"
printf '1\n40\n56\nabc\n8\n8\n3\n4.0\n6\n' | "${SG[@]}"

section "Done"
printf 'Run `%s stitchgauge.py --help` for the full flag reference.\n' "$PYTHON"
