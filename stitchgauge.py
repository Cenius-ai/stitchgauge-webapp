#!/usr/bin/env python3
"""StitchGauge - knitting gauge swatch calculator.

One file, standard library only, fully offline. Three calculators share one
set of pure arithmetic functions and one result-block renderer:

  * gauge  - swatch stitches/rows over measured width/height -> sts/in, rows/in
  * adjust - rescale a pattern's stitch and row counts to the knitter's gauge
  * yarn   - classify a gauge against the seven standard CYC yarn weights

Two front ends call the same calculations: the interactive numbered menu
(run with no arguments) and the one-shot argparse subcommands.
"""

import argparse
import math
import sys

PROGRAM = "stitchgauge.py"
VERSION = "1.0.0"

EXIT_OK = 0
EXIT_INVALID = 1
EXIT_USAGE = 2

# Seven standard yarn-weight categories, ordered coarsest to finest.
# Ranges are inclusive stitches-per-inch bands covering 1.00-10.00 sts/in.
YARN_WEIGHTS = (
    {"name": "Super Bulky", "cyc": 6, "min_sts": 1.00, "max_sts": 2.49},
    {"name": "Bulky", "cyc": 5, "min_sts": 2.50, "max_sts": 3.49},
    {"name": "Worsted", "cyc": 4, "min_sts": 3.50, "max_sts": 4.49},
    {"name": "DK", "cyc": 3, "min_sts": 4.50, "max_sts": 5.49},
    {"name": "Sport", "cyc": 2, "min_sts": 5.50, "max_sts": 6.49},
    {"name": "Fingering", "cyc": 1, "min_sts": 6.50, "max_sts": 7.99},
    {"name": "Lace", "cyc": 0, "min_sts": 8.00, "max_sts": 10.00},
)
TABLE_MIN = 1.00
TABLE_MAX = 10.00

LABEL_WIDTH = 22
RULE_WIDTH = 56


# --------------------------------------------------------------------------
# Arithmetic (pure functions shared by both front ends)
# --------------------------------------------------------------------------
def round_half_up(value):
    """Round to the nearest whole number, halves going up (not banker's)."""
    return int(math.floor(value + 0.5 + 1e-9))


def compute_gauge(stitches, rows, width, height):
    """Return (stitches_per_inch, rows_per_inch) for one swatch."""
    return stitches / width, rows / height


def compute_adjustment(pattern_sts_gauge, pattern_rows_gauge,
                       your_sts_gauge, your_rows_gauge, stitches, rows):
    """Rescale a pattern's counts to the knitter's gauge.

    ratio = your gauge / pattern gauge; adjusted count = pattern count x ratio.
    The product is kept unrounded so a .5 boundary still rounds up.
    """
    ratio_sts = your_sts_gauge / pattern_sts_gauge
    ratio_rows = your_rows_gauge / pattern_rows_gauge
    adjusted_sts = round_half_up(stitches * your_sts_gauge / pattern_sts_gauge)
    adjusted_rows = round_half_up(rows * your_rows_gauge / pattern_rows_gauge)
    return ratio_sts, ratio_rows, adjusted_sts, adjusted_rows


def classify_yarn(gauge):
    """Return the YarnWeight matching a gauge in sts/in, or None if out of range."""
    if gauge < TABLE_MIN or gauge > TABLE_MAX:
        return None
    for weight in YARN_WEIGHTS:
        # Scan coarsest to finest so the band above a max bound picks up
        # gauges that sit between two printed two-decimal bounds.
        if gauge <= weight["max_sts"]:
            return weight
    return None


def format_range(weight):
    return "{0:.2f}-{1:.2f}".format(weight["min_sts"], weight["max_sts"])


# --------------------------------------------------------------------------
# Rendering: one block per calculator, identical in both front ends
# --------------------------------------------------------------------------
def _field(label, value):
    return "  {0:<{1}}: {2}".format(label, LABEL_WIDTH, value)


def _block(title, fields, results=()):
    """Render a titled result block as a single string."""
    lines = ["", "  " + title, "  " + "-" * RULE_WIDTH]
    lines.extend(_field(label, value) for label, value in fields)
    if results:
        lines.append("  " + "-" * RULE_WIDTH)
        lines.extend(_field(label, value) for label, value in results)
    return "\n".join(lines)


def render_gauge(stitches, rows, width, height):
    spi, rpi = compute_gauge(stitches, rows, width, height)
    return _block(
        "GAUGE",
        (
            ("Stitch count", "{0}".format(int(stitches))),
            ("Row count", "{0}".format(int(rows))),
            ("Swatch width (in)", "{0:.2f}".format(width)),
            ("Swatch height (in)", "{0:.2f}".format(height)),
        ),
        (
            ("Stitches per inch", "{0:.2f}".format(spi)),
            ("Rows per inch", "{0:.2f}".format(rpi)),
        ),
    )


def render_adjustment(pattern_sts_gauge, pattern_rows_gauge, your_sts_gauge,
                      your_rows_gauge, stitches, rows):
    ratio_sts, ratio_rows, adjusted_sts, adjusted_rows = compute_adjustment(
        pattern_sts_gauge, pattern_rows_gauge, your_sts_gauge, your_rows_gauge,
        stitches, rows,
    )
    return _block(
        "ADJUSTMENT",
        (
            ("Pattern stitch gauge", "{0:.2f} sts/in".format(pattern_sts_gauge)),
            ("Pattern row gauge", "{0:.2f} rows/in".format(pattern_rows_gauge)),
            ("Your stitch gauge", "{0:.2f} sts/in".format(your_sts_gauge)),
            ("Your row gauge", "{0:.2f} rows/in".format(your_rows_gauge)),
        ),
        (
            ("Stitch ratio", "{0:.2f}".format(ratio_sts)),
            ("Pattern stitches", "{0}".format(int(stitches))),
            ("Adjusted stitches", "{0}".format(adjusted_sts)),
            ("Row ratio", "{0:.2f}".format(ratio_rows)),
            ("Pattern rows", "{0}".format(int(rows))),
            ("Adjusted rows", "{0}".format(adjusted_rows)),
        ),
    )


def render_yarn(gauge):
    fields = (("Gauge", "{0:.2f} sts/in".format(gauge)),)
    weight = classify_yarn(gauge)
    if weight is None:
        message = (
            "gauge {0:.2f} sts/in is outside the built-in table "
            "({1:.2f}-{2:.2f} sts/in)"
        ).format(gauge, TABLE_MIN, TABLE_MAX)
        return _block(
            "YARN",
            fields,
            (("Category", "(none)"), ("Note", message)),
        )
    return _block(
        "YARN",
        fields,
        (
            ("Category", "{0} ({1})".format(weight["name"], weight["cyc"])),
            ("Range", "{0} sts/in".format(format_range(weight))),
        ),
    )


def render_yarn_table():
    widths = (
        max(len("Category"), max(len(w["name"]) for w in YARN_WEIGHTS)),
        max(len("Stitches per inch"), max(len(format_range(w)) for w in YARN_WEIGHTS)),
    )
    lines = [
        "",
        "  YARN WEIGHT TABLE - standard CYC categories",
        "  " + "-" * RULE_WIDTH,
        "  {0:>3}  {1:<{2}}  {3}".format("CYC", "Category", widths[0], "Stitches per inch"),
        "  {0:>3}  {1}  {2}".format("---", "-" * widths[0], "-" * widths[1]),
    ]
    for weight in YARN_WEIGHTS:
        lines.append(
            "  {0:>3}  {1:<{2}}  {3}".format(
                weight["cyc"], weight["name"], widths[0], format_range(weight)
            ).rstrip()
        )
    lines.append("")
    lines.append("  Ranges are inclusive; anything outside {0:.2f}-{1:.2f} sts/in".format(
        TABLE_MIN, TABLE_MAX
    ))
    lines.append("  is reported as out of range instead of being rounded to a category.")
    return "\n".join(lines)


_ADJUST_FLAGS = "--your-rows G --stitches N --rows N"
_PROGRAM_ADJUST = "adjust --pattern-sts G --pattern-rows G --your-sts G \\"


def _continuation(indent):
    """Indent that lines up the wrapped second half of the adjust command."""
    return " " * (indent + len(PROGRAM) + len(" adjust "))


def _usage_text():
    indent = len("       ")
    lines = [
        "usage: {0}                        interactive menu".format(PROGRAM),
        "       {0} gauge --stitches N --rows N --width W --height H".format(PROGRAM),
        "       {0} {1}".format(PROGRAM, _PROGRAM_ADJUST),
        _continuation(indent) + _ADJUST_FLAGS,
        "       {0} yarn --gauge G".format(PROGRAM),
        "       {0} yarn --table".format(PROGRAM),
        "       {0} --help".format(PROGRAM),
    ]
    return "\n".join(lines)


USAGE = _usage_text()

_HELP_BODY = [
    "StitchGauge {version} - knitting gauge swatch calculator",
    "",
    "Three calculators, each reachable from the interactive menu (run with no",
    "arguments) or from a single scriptable command that prints the same block.",
    "",
    "  1) Gauge calculator",
    "     {program} gauge --stitches N --rows N --width W --height H",
    "     stitches per inch = stitches / width",
    "     rows per inch     = rows / height",
    "",
    "  2) Adjust for your gauge",
    "     {program} " + _PROGRAM_ADJUST,
    _continuation(5) + _ADJUST_FLAGS,
    "     stitch ratio   = your stitch gauge / pattern stitch gauge",
    "     row ratio      = your row gauge / pattern row gauge",
    "     adjusted count = pattern count x ratio, rounded half-up",
    "",
    "  3) Yarn weight lookup",
    "     {program} yarn --gauge G      match one gauge to a CYC category",
    "     {program} yarn --table        print the full seven-row table",
    "",
    "Yarn weight table (inclusive stitches per inch):",
    "   6 Super Bulky 1.00-2.49     5 Bulky 2.50-3.49    4 Worsted 3.50-4.49",
    "   3 DK 4.50-5.49              2 Sport 5.50-6.49    1 Fingering 6.50-7.99",
    "   0 Lace 8.00-10.00",
    "",
    "Input rules: every count, width, height and gauge must be a number greater",
    "than zero; stitch and row counts must be whole numbers. Plain decimal",
    "inches only - no unit suffixes, no centimetres.",
    "",
    "Exit codes:",
    "   0  a result block was printed",
    "   1  invalid input (exactly one 'error:' line on stderr)",
    "   2  usage error (unknown subcommand or flag)",
]


def _help_text():
    body = "\n".join(_HELP_BODY).format(version=VERSION, program=PROGRAM)
    return USAGE + "\n\n" + body


HELP_TEXT = _help_text()


# --------------------------------------------------------------------------
# Validation shared by both front ends
# --------------------------------------------------------------------------
def parse_positive(raw, field, whole=False):
    """Validate one numeric answer. Returns (value, reason); reason is None on success."""
    text = raw.strip()
    if not text:
        return None, "{0} is required - please enter a value".format(field)
    try:
        value = float(text)
    except ValueError:
        return None, "{0} must be a number".format(field)
    if not math.isfinite(value):
        return None, "{0} must be a number".format(field)
    if whole and value != int(value):
        return None, "{0} must be a whole number".format(field)
    if value <= 0:
        return None, "{0} must be greater than zero".format(field)
    return value, None


class _EndOfInput(Exception):
    """Raised when stdin closes mid-prompt so the menu can exit cleanly."""


def _read_line(prompt):
    try:
        return input(prompt)
    except EOFError:
        print()
        raise _EndOfInput() from None


def prompt_value(prompt, field, whole=False):
    """Ask until a valid value arrives; one short reason line per rejection."""
    while True:
        raw = _read_line(prompt)
        value, reason = parse_positive(raw, field, whole=whole)
        if reason is None:
            return value
        print("  ! " + reason)


# --------------------------------------------------------------------------
# Interactive front end
# --------------------------------------------------------------------------
MENU_ENTRIES = (
    "1) Gauge calculator",
    "2) Adjust for your gauge",
    "3) Yarn weight lookup",
    "4) Show yarn weight table",
    "5) Help",
    "6) Quit",
)

GAUGE_PROMPTS = (
    ("Stitch count of your swatch: ", "stitch count", True),
    ("Row count of your swatch: ", "row count", True),
    ("Swatch width in inches: ", "width", False),
    ("Swatch height in inches: ", "height", False),
)

ADJUST_PROMPTS = (
    ("Pattern stitch gauge in stitches per inch: ", "pattern stitch gauge", False),
    ("Pattern row gauge in rows per inch: ", "pattern row gauge", False),
    ("Your stitch gauge in stitches per inch: ", "your stitch gauge", False),
    ("Your row gauge in rows per inch: ", "your row gauge", False),
    ("Pattern stitch count: ", "pattern stitch count", True),
    ("Pattern row count: ", "pattern row count", True),
)


def show_menu():
    print()
    print("StitchGauge - knitting gauge swatch calculator")
    print("=" * 46)
    print()
    for entry in MENU_ENTRIES:
        print("  " + entry)
    print()


def run_gauge_interactive():
    answers = [prompt_value(*spec) for spec in GAUGE_PROMPTS]
    print(render_gauge(*answers))


def run_adjust_interactive():
    answers = [prompt_value(*spec) for spec in ADJUST_PROMPTS]
    print(render_adjustment(*answers))


def run_yarn_interactive():
    gauge = prompt_value("Your gauge in stitches per inch: ", "gauge")
    print(render_yarn(gauge))


def run_table_interactive():
    print(render_yarn_table())


def run_help_interactive():
    print()
    print(HELP_TEXT)
    print()


MENU_ACTIONS = {
    "1": run_gauge_interactive,
    "2": run_adjust_interactive,
    "3": run_yarn_interactive,
    "4": run_table_interactive,
    "5": run_help_interactive,
}


def run_interactive():
    while True:
        show_menu()
        try:
            try:
                choice = input("Choose 1-6: ").strip()
            except EOFError:
                print()
                print("Goodbye.")
                return EXIT_OK
            if choice == "6":
                print("Goodbye.")
                return EXIT_OK
            action = MENU_ACTIONS.get(choice)
            if action is None:
                print("  ! please choose 1-6")
                continue
            action()
        except _EndOfInput:
            print("Goodbye.")
            return EXIT_OK


# --------------------------------------------------------------------------
# One-shot front end
# --------------------------------------------------------------------------
def _fail(reason):
    print("error: " + reason, file=sys.stderr)
    return EXIT_INVALID


def validate_all(specs):
    """specs: sequence of (raw, field, whole). Returns (values, reason)."""
    values = []
    for raw, field, whole in specs:
        value, reason = parse_positive(raw, field, whole=whole)
        if reason is not None:
            return None, reason
        values.append(value)
    return values, None


def run_gauge_once(args):
    values, reason = validate_all((
        (args.stitches, "stitch count", True),
        (args.rows, "row count", True),
        (args.width, "width", False),
        (args.height, "height", False),
    ))
    if reason is not None:
        return _fail(reason)
    print(render_gauge(*values))
    return EXIT_OK


def run_adjust_once(args):
    values, reason = validate_all((
        (args.pattern_sts, "pattern stitch gauge", False),
        (args.pattern_rows, "pattern row gauge", False),
        (args.your_sts, "your stitch gauge", False),
        (args.your_rows, "your row gauge", False),
        (args.stitches, "pattern stitch count", True),
        (args.rows, "pattern row count", True),
    ))
    if reason is not None:
        return _fail(reason)
    print(render_adjustment(*values))
    return EXIT_OK


def run_yarn_once(args):
    if args.table:
        print(render_yarn_table())
        return EXIT_OK
    gauge, reason = parse_positive(args.gauge, "gauge")
    if reason is not None:
        return _fail(reason)
    print(render_yarn(gauge))
    return EXIT_OK


def build_parser():
    parser = argparse.ArgumentParser(
        prog=PROGRAM,
        add_help=False,
        allow_abbrev=False,
        description="Knitting gauge swatch calculator (offline, standard library only).",
    )
    subparsers = parser.add_subparsers(dest="command")

    gauge = subparsers.add_parser(
        "gauge", add_help=False, allow_abbrev=False,
        help="swatch measurement -> stitches per inch and rows per inch",
    )
    gauge.add_argument("--stitches", required=True, metavar="N", help="stitch count of the swatch")
    gauge.add_argument("--rows", required=True, metavar="N", help="row count of the swatch")
    gauge.add_argument("--width", required=True, metavar="W", help="swatch width in inches")
    gauge.add_argument("--height", required=True, metavar="H", help="swatch height in inches")
    gauge.set_defaults(handler=run_gauge_once)

    adjust = subparsers.add_parser(
        "adjust", add_help=False, allow_abbrev=False,
        help="rescale a pattern's stitch and row counts to your gauge",
    )
    adjust.add_argument("--pattern-sts", required=True, metavar="G",
                        help="pattern stitch gauge in stitches per inch")
    adjust.add_argument("--pattern-rows", required=True, metavar="G",
                        help="pattern row gauge in rows per inch")
    adjust.add_argument("--your-sts", required=True, metavar="G",
                        help="your stitch gauge in stitches per inch")
    adjust.add_argument("--your-rows", required=True, metavar="G",
                        help="your row gauge in rows per inch")
    adjust.add_argument("--stitches", required=True, metavar="N", help="pattern stitch count")
    adjust.add_argument("--rows", required=True, metavar="N", help="pattern row count")
    adjust.set_defaults(handler=run_adjust_once)

    yarn = subparsers.add_parser(
        "yarn", add_help=False, allow_abbrev=False,
        help="match a gauge to a standard yarn weight, or print the table",
    )
    yarn_group = yarn.add_mutually_exclusive_group(required=True)
    yarn_group.add_argument("--gauge", metavar="G", help="gauge in stitches per inch")
    yarn_group.add_argument("--table", action="store_true", help="print all seven yarn weights")
    yarn.set_defaults(handler=run_yarn_once)

    return parser


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        return run_interactive()
    if any(arg in ("-h", "--help") for arg in args):
        print(HELP_TEXT)
        return EXIT_OK
    if any(arg in ("-V", "--version") for arg in args):
        print("StitchGauge {0}".format(VERSION))
        return EXIT_OK

    parser = build_parser()
    parsed = parser.parse_args(args)  # argparse writes usage to stderr and exits 2 on misuse
    if parsed.command is None:
        parser.print_usage(sys.stderr)
        return EXIT_USAGE
    return parsed.handler(parsed)


if __name__ == "__main__":
    sys.exit(main())
