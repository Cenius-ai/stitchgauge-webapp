# Using StitchGauge

Two front ends, one set of calculations. The interactive menu and the one-shot
flags print byte-identical result blocks, so your terminal session and your
shell script never disagree.

## 1. Gauge calculator

**Question:** my swatch is *N* stitches x *M* rows over *W* x *H* inches - what
is my gauge?

Interactive: run `python3 stitchgauge.py`, then pick `1`.

```
Choose 1-6: 1
Stitch count of your swatch: 40
Row count of your swatch: 56
Swatch width in inches: 8
Swatch height in inches: 8

  GAUGE
  --------------------------------------------------------
  Stitch count          : 40
  Row count             : 56
  Swatch width (in)     : 8.00
  Swatch height (in)    : 8.00
  --------------------------------------------------------
  Stitches per inch     : 5.00
  Rows per inch         : 7.00
```

One-shot:

```bash
python3 stitchgauge.py gauge --stitches 40 --rows 56 --width 8 --height 8
```

`stitches per inch = stitches / width`, `rows per inch = rows / height`, both
printed to two decimals with all four inputs echoed so the block is
self-checking.

## 2. Adjust for your gauge

**Question:** the pattern is written at one gauge and I knit at another - how
many stitches and rows do I need?

Interactive: pick `2` and answer the six prompts in order (pattern stitch
gauge, pattern row gauge, your stitch gauge, your row gauge, pattern stitch
count, pattern row count).

One-shot:

```bash
python3 stitchgauge.py adjust --pattern-sts 5 --pattern-rows 7 \
                              --your-sts 5.5 --your-rows 7.5 \
                              --stitches 100 --rows 120
```

```
  ADJUSTMENT
  --------------------------------------------------------
  Pattern stitch gauge  : 5.00 sts/in
  Pattern row gauge     : 7.00 rows/in
  Your stitch gauge     : 5.50 sts/in
  Your row gauge        : 7.50 rows/in
  --------------------------------------------------------
  Stitch ratio          : 1.10
  Pattern stitches      : 100
  Adjusted stitches     : 110
  Row ratio             : 1.07
  Pattern rows          : 120
  Adjusted rows         : 129
```

Rules:

- `stitch ratio = your stitch gauge / pattern stitch gauge`
- `row ratio = your row gauge / pattern row gauge`
- `adjusted count = pattern count x ratio`, rounded **half-up** to a whole
  stitch or row - 94.5 becomes 95 (Python's `round()` would give 94).

Matching gauges are a no-op: ratio 1.00 leaves the counts unchanged.

## 3. Yarn weight lookup

**Question:** my gauge is *G* stitches per inch - which standard yarn weight is
that?

Interactive: pick `3`, then type the gauge.

One-shot:

```bash
python3 stitchgauge.py yarn --gauge 4.0
```

```
  YARN
  --------------------------------------------------------
  Gauge                 : 4.00 sts/in
  --------------------------------------------------------
  Category              : Worsted (4)
  Range                 : 3.50-4.49 sts/in
```

Outside the table's 1.00-10.00 sts/in span the tool names the span instead of
guessing the nearest category:

```bash
python3 stitchgauge.py yarn --gauge 12.0
```

```
  Category              : (none)
  Note                  : gauge 12.00 sts/in is outside the built-in table (1.00-10.00 sts/in)
```

An out-of-range gauge is still a successful answer: exit status 0.

## 4. The full table

Interactive: pick `4`. One-shot:

```bash
python3 stitchgauge.py yarn --table
```

```
  YARN WEIGHT TABLE - standard CYC categories
  --------------------------------------------------------
  CYC  Category     Stitches per inch
  ---  -----------  -----------------
    6  Super Bulky  1.00-2.49
    5  Bulky        2.50-3.49
    4  Worsted      3.50-4.49
    3  DK           4.50-5.49
    2  Sport        5.50-6.49
    1  Fingering    6.50-7.99
    0  Lace         8.00-10.00
```

Bounds are inclusive at both ends: 10.00 sts/in is Lace, 1.00 sts/in is Super
Bulky.

## 5. Help

Interactive: pick `5`. One-shot: `python3 stitchgauge.py --help`. Both print the
same reference - the three subcommands with their flags, the yarn table in
brief, the input rules and the exit-code contract. `python3 stitchgauge.py
--version` prints just the version line.

## Validation, in both modes

| Input | Interactive | One-shot |
|-------|-------------|----------|
| empty line | `! stitch count is required - please enter a value`, re-ask | `error: stitch count is required - please enter a value`, exit 1 |
| `abc` | `! width must be a number`, re-ask | `error: width must be a number`, exit 1 |
| `0` / `-4` | `! gauge must be greater than zero`, re-ask | `error: gauge must be greater than zero`, exit 1 |
| `40.5` as a count | `! stitch count must be a whole number`, re-ask | same text on stderr, exit 1 |
| unknown subcommand or flag | - | usage on stderr, exit 2 |

Nothing invalid ever reaches the arithmetic, so `NaN`, `Infinity` and
division-by-zero cannot be printed, and no result block is produced for an
invalid value.

## Scripting notes

- Results go to stdout, the single error line to stderr.
- Exit codes: `0` result printed, `1` invalid value, `2` usage error.
- Output is plain ASCII, fixed two decimals, deterministic: the same inputs
  always produce byte-identical text.
- No prompts are ever issued in one-shot mode, so piped and cron use is safe.
