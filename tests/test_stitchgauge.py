"""Tests for StitchGauge.

Standard-library unittest tests; also collected by pytest. Every CLI test
drives the real script as a subprocess so stdin piping, stdout/stderr routing
and exit codes are exercised exactly as a user or script would see them.
"""

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "stitchgauge.py"

sys.path.insert(0, str(ROOT))
import stitchgauge  # noqa: E402  (path set up above)


def run_cli(*args, stdin_text=None):
    """Run the tool exactly as a user would; return the completed process."""
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        input=stdin_text,
        capture_output=True,
        text=True,
        cwd=str(ROOT),
        timeout=60,
    )


def run_interactive(stdin_text):
    return run_cli(stdin_text=stdin_text)


class GaugeCalculatorTests(unittest.TestCase):
    def test_one_shot_prints_both_gauges_and_echoes_inputs(self):
        proc = run_cli("gauge", "--stitches", "40", "--rows", "56",
                       "--width", "8", "--height", "8")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("GAUGE", proc.stdout)
        self.assertIn("Stitch count", proc.stdout)
        self.assertIn(": 40", proc.stdout)
        self.assertIn("Row count", proc.stdout)
        self.assertIn(": 56", proc.stdout)
        self.assertIn("Swatch width (in)", proc.stdout)
        self.assertIn("Swatch height (in)", proc.stdout)
        self.assertIn("Stitches per inch     : 5.00", proc.stdout)
        self.assertIn("Rows per inch         : 7.00", proc.stdout)
        self.assertEqual(proc.stderr, "")

    def test_decimal_measurements_render_two_decimals(self):
        proc = run_cli("gauge", "--stitches", "30", "--rows", "42",
                       "--width", "6.5", "--height", "6.25")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("6.50", proc.stdout)
        self.assertIn("6.25", proc.stdout)
        self.assertIn("4.62", proc.stdout)  # 30 / 6.5
        self.assertIn("6.72", proc.stdout)  # 42 / 6.25

    def test_output_is_deterministic(self):
        first = run_cli("gauge", "--stitches", "40", "--rows", "56",
                        "--width", "8", "--height", "8")
        second = run_cli("gauge", "--stitches", "40", "--rows", "56",
                         "--width", "8", "--height", "8")
        self.assertEqual(first.stdout, second.stdout)

    def test_zero_width_is_rejected_with_no_result_block(self):
        proc = run_cli("gauge", "--stitches", "40", "--rows", "56",
                       "--width", "0", "--height", "8")
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(proc.stdout, "")
        self.assertIn("width must be greater than zero", proc.stderr)
        self.assertEqual(len(proc.stderr.strip().splitlines()), 1)
        self.assertTrue(proc.stderr.startswith("error: "))

    def test_negative_and_zero_counts_are_rejected(self):
        for arg, value, field in (
            ("--stitches", "-40", "stitch count"),
            ("--stitches", "0", "stitch count"),
            ("--rows", "0", "row count"),
            ("--rows", "-5", "row count"),
            ("--height", "-8", "height"),
        ):
            args = ["gauge", "--stitches", "40", "--rows", "56",
                    "--width", "8", "--height", "8"]
            flag_index = args.index(arg) if arg in args else None
            if flag_index is None:
                args.extend([arg, value])
            else:
                args[flag_index + 1] = value
            proc = run_cli(*args)
            with self.subTest(flag=arg, value=value):
                self.assertEqual(proc.returncode, 1)
                self.assertEqual(proc.stdout, "")
                self.assertIn("{} must be greater than zero".format(field), proc.stderr)

    def test_non_numeric_value_fails_with_one_error_line(self):
        proc = run_cli("gauge", "--stitches", "abc", "--rows", "56",
                       "--width", "8", "--height", "8")
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(proc.stdout, "")
        self.assertTrue(proc.stderr.startswith("error: "))
        self.assertIn("must be a number", proc.stderr)
        self.assertEqual(len(proc.stderr.strip().splitlines()), 1)

    def test_nan_and_infinity_never_produce_a_block(self):
        # "=value" form so argparse does not read "-inf" as an option token.
        for raw in ("nan", "inf", "-inf", "1e400"):
            proc = run_cli("gauge", "--stitches", "40", "--rows", "56",
                           "--width=" + raw, "--height", "8")
            with self.subTest(raw=raw):
                self.assertEqual(proc.returncode, 1)
                self.assertEqual(proc.stdout, "")
                self.assertIn("width must be a number", proc.stderr)
                self.assertNotIn("NaN", proc.stdout)
                self.assertNotIn("Infinity", proc.stdout)

    def test_fractional_stitch_count_is_rejected(self):
        proc = run_cli("gauge", "--stitches", "40.5", "--rows", "56",
                       "--width", "8", "--height", "8")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("stitch count must be a whole number", proc.stderr)


class AdjustmentTests(unittest.TestCase):
    def test_plan_example_rescales_stitches_and_rows(self):
        proc = run_cli("adjust", "--pattern-sts", "5", "--pattern-rows", "7",
                       "--your-sts", "5.5", "--your-rows", "7.5",
                       "--stitches", "100", "--rows", "120")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("ADJUSTMENT", proc.stdout)
        self.assertIn("Stitch ratio          : 1.10", proc.stdout)
        self.assertIn("Adjusted stitches     : 110", proc.stdout)
        self.assertIn("Row ratio             : 1.07", proc.stdout)
        self.assertIn("Adjusted rows         : 129", proc.stdout)

    def test_matching_gauges_leave_counts_unchanged(self):
        proc = run_cli("adjust", "--pattern-sts", "6", "--pattern-rows", "6",
                       "--your-sts", "6", "--your-rows", "6",
                       "--stitches", "100", "--rows", "120")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("Stitch ratio          : 1.00", proc.stdout)
        self.assertIn("Adjusted stitches     : 100", proc.stdout)
        self.assertIn("Row ratio             : 1.00", proc.stdout)
        self.assertIn("Adjusted rows         : 120", proc.stdout)

    def test_half_up_rounding_beats_bankers_rounding(self):
        # 90 x (4.2 / 4.0) is exactly 94.5 -> half-up gives 95, not 94.
        proc = run_cli("adjust", "--pattern-sts", "4.0", "--pattern-rows", "7",
                       "--your-sts", "4.2", "--your-rows", "7",
                       "--stitches", "90", "--rows", "120")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("Adjusted stitches     : 95", proc.stdout)

    def test_zero_gauge_fails_without_division_by_zero_output(self):
        for flag in ("--pattern-sts", "--pattern-rows", "--your-sts", "--your-rows"):
            args = {"--pattern-sts": "5", "--pattern-rows": "7",
                    "--your-sts": "5.5", "--your-rows": "7.5"}
            args[flag] = "0"
            proc = run_cli("adjust",
                           "--pattern-sts", args["--pattern-sts"],
                           "--pattern-rows", args["--pattern-rows"],
                           "--your-sts", args["--your-sts"],
                           "--your-rows", args["--your-rows"],
                           "--stitches", "100", "--rows", "120")
            with self.subTest(flag=flag):
                self.assertEqual(proc.returncode, 1)
                self.assertEqual(proc.stdout, "")
                self.assertIn("must be greater than zero", proc.stderr)
                self.assertNotIn("NaN", proc.stdout)
                self.assertNotIn("Infinity", proc.stdout)

    def test_zero_row_count_is_rejected(self):
        proc = run_cli("adjust", "--pattern-sts", "5", "--pattern-rows", "7",
                       "--your-sts", "5.5", "--your-rows", "7.5",
                       "--stitches", "120", "--rows", "0")
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(proc.stdout, "")
        self.assertIn("pattern row count must be greater than zero", proc.stderr)


class YarnWeightTests(unittest.TestCase):
    def test_gauge_four_is_worsted(self):
        proc = run_cli("yarn", "--gauge", "4.0")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("Worsted (4)", proc.stdout)
        self.assertIn("3.50-4.49 sts/in", proc.stdout)

    def test_boundaries_are_inclusive_on_both_ends(self):
        low = run_cli("yarn", "--gauge", "1.00")
        high = run_cli("yarn", "--gauge", "10.0")
        self.assertIn("Super Bulky (6)", low.stdout)
        self.assertIn("Lace (0)", high.stdout)

    def test_adjacent_bounds_land_in_their_own_category(self):
        cases = {
            "2.49": "Super Bulky (6)",
            "2.50": "Bulky (5)",
            "3.49": "Bulky (5)",
            "3.50": "Worsted (4)",
            "4.49": "Worsted (4)",
            "4.50": "DK (3)",
            "5.49": "DK (3)",
            "5.50": "Sport (2)",
            "6.49": "Sport (2)",
            "6.50": "Fingering (1)",
            "7.99": "Fingering (1)",
            "8.00": "Lace (0)",
        }
        for gauge, expected in cases.items():
            with self.subTest(gauge=gauge):
                proc = run_cli("yarn", "--gauge", gauge)
                self.assertEqual(proc.returncode, 0, proc.stderr)
                self.assertIn(expected, proc.stdout)

    def test_gauge_above_table_reports_the_span_and_no_category(self):
        proc = run_cli("yarn", "--gauge", "12.0")
        self.assertEqual(proc.returncode, 0)
        self.assertIn("gauge 12.00 sts/in is outside the built-in table", proc.stdout)
        self.assertIn("(1.00-10.00 sts/in)", proc.stdout)
        for category in ("Super Bulky", "Bulky", "Worsted", "DK", "Sport",
                         "Fingering", "Lace"):
            self.assertNotIn(category, proc.stdout.replace("built-in table", ""))

    def test_gauge_below_table_reports_the_span(self):
        proc = run_cli("yarn", "--gauge", "0.5")
        self.assertEqual(proc.returncode, 0)
        self.assertIn("outside the built-in table", proc.stdout)

    def test_zero_and_negative_gauges_are_rejected(self):
        for raw in ("0", "-4"):
            with self.subTest(raw=raw):
                proc = run_cli("yarn", "--gauge", raw)
                self.assertEqual(proc.returncode, 1)
                self.assertEqual(proc.stdout, "")
                self.assertIn("gauge must be greater than zero", proc.stderr)

    def test_table_lists_all_seven_categories(self):
        proc = run_cli("yarn", "--table")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        expected = (
            ("6", "Super Bulky", "1.00-2.49"),
            ("5", "Bulky", "2.50-3.49"),
            ("4", "Worsted", "3.50-4.49"),
            ("3", "DK", "4.50-5.49"),
            ("2", "Sport", "5.50-6.49"),
            ("1", "Fingering", "6.50-7.99"),
            ("0", "Lace", "8.00-10.00"),
        )
        for cyc, name, span in expected:
            self.assertIn(cyc, proc.stdout)
            self.assertIn(name, proc.stdout)
            self.assertIn(span, proc.stdout)
        body = [line for line in proc.stdout.splitlines() if "Super Bulky" in line]
        self.assertEqual(len(body), 1)

    def test_yarn_requires_exactly_one_of_gauge_or_table(self):
        neither = run_cli("yarn")
        both = run_cli("yarn", "--gauge", "4", "--table")
        self.assertEqual(neither.returncode, 2)
        self.assertEqual(both.returncode, 2)
        self.assertEqual(neither.stdout, "")
        self.assertEqual(both.stdout, "")


class YarnTableUnitTests(unittest.TestCase):
    def test_table_has_seven_ordered_categories(self):
        self.assertEqual(len(stitchgauge.YARN_WEIGHTS), 7)
        cyc_numbers = [w["cyc"] for w in stitchgauge.YARN_WEIGHTS]
        self.assertEqual(cyc_numbers, [6, 5, 4, 3, 2, 1, 0])

    def test_ranges_are_contiguous_from_one_to_ten(self):
        self.assertEqual(stitchgauge.YARN_WEIGHTS[0]["min_sts"], 1.00)
        self.assertEqual(stitchgauge.YARN_WEIGHTS[-1]["max_sts"], 10.00)
        for coarser, finer in zip(stitchgauge.YARN_WEIGHTS,
                                  stitchgauge.YARN_WEIGHTS[1:]):
            self.assertAlmostEqual(coarser["max_sts"] + 0.01, finer["min_sts"], places=6)
            self.assertLess(coarser["min_sts"], coarser["max_sts"])

    def test_classification_at_every_printed_bound(self):
        for weight in stitchgauge.YARN_WEIGHTS:
            self.assertIs(stitchgauge.classify_yarn(weight["min_sts"]), weight)
            self.assertIs(stitchgauge.classify_yarn(weight["max_sts"]), weight)

    def test_out_of_range_values_return_none(self):
        for gauge in (0.99, 10.01, 0.0, 25.0):
            self.assertIsNone(stitchgauge.classify_yarn(gauge))


class RoundingUnitTests(unittest.TestCase):
    def test_round_half_up(self):
        self.assertEqual(stitchgauge.round_half_up(94.5), 95)
        self.assertEqual(stitchgauge.round_half_up(92.5), 93)  # not banker's 92
        self.assertEqual(stitchgauge.round_half_up(94.4), 94)
        self.assertEqual(stitchgauge.round_half_up(110.0), 110)
        self.assertEqual(stitchgauge.round_half_up(128.57142857142858), 129)


class HelpAndUsageTests(unittest.TestCase):
    def test_help_lists_all_three_subcommands_and_flags(self):
        proc = run_cli("--help")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        for token in ("gauge", "adjust", "yarn", "--stitches", "--rows",
                      "--width", "--height", "--pattern-sts", "--pattern-rows",
                      "--your-sts", "--your-rows", "--gauge", "--table",
                      "Exit codes"):
            self.assertIn(token, proc.stdout)
        self.assertEqual(proc.stderr, "")

    def test_version_flag(self):
        proc = run_cli("--version")
        self.assertEqual(proc.returncode, 0)
        self.assertIn("StitchGauge", proc.stdout)

    def test_unknown_subcommand_prints_usage_to_stderr_and_exits_two(self):
        proc = run_cli("frobnicate")
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(proc.stdout, "")
        self.assertIn("usage:", proc.stderr)

    def test_unknown_flag_exits_two(self):
        proc = run_cli("gauge", "--stitches", "40", "--rows", "56",
                       "--width", "8", "--height", "8", "--bogus", "1")
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(proc.stdout, "")
        self.assertIn("usage:", proc.stderr)

    def test_missing_required_flag_exits_two(self):
        proc = run_cli("gauge", "--stitches", "40")
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(proc.stdout, "")


class InteractiveMenuTests(unittest.TestCase):
    def test_menu_lists_six_entries_and_prompts(self):
        proc = run_interactive("6\n")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        for entry in ("1) Gauge calculator", "2) Adjust for your gauge",
                      "3) Yarn weight lookup", "4) Show yarn weight table",
                      "5) Help", "6) Quit"):
            self.assertIn(entry, proc.stdout)
        self.assertIn("Choose 1-6:", proc.stdout)

    def test_gauge_walkthrough_returns_to_menu_then_quits(self):
        proc = run_interactive("1\n40\n56\n8\n8\n6\n")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("Stitch count of your swatch:", proc.stdout)
        self.assertIn("Row count of your swatch:", proc.stdout)
        self.assertIn("Swatch width in inches:", proc.stdout)
        self.assertIn("Swatch height in inches:", proc.stdout)
        self.assertIn("Stitches per inch     : 5.00", proc.stdout)
        self.assertIn("Rows per inch         : 7.00", proc.stdout)
        self.assertEqual(proc.stdout.count("Choose 1-6:"), 2)  # menu returned

    def test_invalid_width_is_reprompted_then_accepted(self):
        proc = run_interactive("1\n40\n56\nabc\n8\n8\n6\n")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("! width must be a number", proc.stdout)
        self.assertEqual(proc.stdout.count("Swatch width in inches:"), 2)
        self.assertIn("Stitches per inch     : 5.00", proc.stdout)

    def test_zero_width_is_reprompted_without_result_block(self):
        proc = run_interactive("1\n40\n56\n0\n8\n8\n6\n")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("! width must be greater than zero", proc.stdout)
        self.assertEqual(proc.stdout.count("Swatch width in inches:"), 2)
        self.assertEqual(proc.stdout.count("Stitches per inch"), 1)

    def test_empty_answer_asks_for_a_value(self):
        proc = run_interactive("1\n\n40\n56\n8\n8\n6\n")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("! stitch count is required", proc.stdout)
        self.assertEqual(proc.stdout.count("Stitch count of your swatch:"), 2)
        self.assertIn("Stitches per inch     : 5.00", proc.stdout)

    def test_adjust_walkthrough(self):
        proc = run_interactive("2\n5\n7\n5.5\n7.5\n100\n120\n6\n")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("Pattern stitch gauge in stitches per inch:", proc.stdout)
        self.assertIn("Adjusted stitches     : 110", proc.stdout)
        self.assertIn("Adjusted rows         : 129", proc.stdout)

    def test_yarn_walkthrough_and_out_of_range(self):
        proc = run_interactive("3\n12.0\n3\n4.0\n6\n")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("outside the built-in table", proc.stdout)
        self.assertIn("Worsted (4)", proc.stdout)

    def test_yarn_table_and_help_menu_options(self):
        proc = run_interactive("4\n5\n6\n")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("Super Bulky", proc.stdout)
        self.assertIn("Lace", proc.stdout)
        self.assertIn("Exit codes:", proc.stdout)

    def test_unrecognised_choice_reprompts(self):
        proc = run_interactive("9\nnonsense\n6\n")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout.count("! please choose 1-6"), 2)

    def test_eof_exits_cleanly(self):
        proc = run_interactive("")
        self.assertEqual(proc.returncode, 0)
        self.assertIn("Choose 1-6:", proc.stdout)

    def test_interactive_and_one_shot_print_the_same_block(self):
        one_shot = run_cli("gauge", "--stitches", "40", "--rows", "56",
                           "--width", "8", "--height", "8")
        interactive = run_interactive("1\n40\n56\n8\n8\n6\n")
        self.assertIn(one_shot.stdout.strip(), interactive.stdout)

        adjust_one_shot = run_cli("adjust", "--pattern-sts", "5", "--pattern-rows", "7",
                                  "--your-sts", "5.5", "--your-rows", "7.5",
                                  "--stitches", "100", "--rows", "120")
        adjust_interactive = run_interactive("2\n5\n7\n5.5\n7.5\n100\n120\n6\n")
        self.assertIn(adjust_one_shot.stdout.strip(), adjust_interactive.stdout)


class DocumentationTests(unittest.TestCase):
    """The README/USAGE commands and the recorded transcript must stay true."""

    def _documented_commands(self):
        """Every `python3 stitchgauge.py ...` line in the docs, joined at line continuations."""
        commands = []
        for name in ("README.md", "USAGE.md"):
            pending = ""
            for raw_line in (ROOT / name).read_text().splitlines():
                piece = raw_line.strip()
                if pending:
                    line = pending + " " + piece
                elif piece.startswith("python3 stitchgauge.py"):
                    line = piece
                else:
                    continue
                if line.endswith("\\"):
                    pending = line[:-1].rstrip()
                    continue
                pending = ""
                line = line.split("#")[0].strip()
                if line.startswith("python3 stitchgauge.py"):
                    commands.append((name, line.split()[2:]))
        return commands

    def test_every_documented_command_runs(self):
        commands = self._documented_commands()
        self.assertGreaterEqual(len(commands), 6)
        invalid = {"--width", "0"}
        for name, args in commands:
            if not args:
                continue  # the bare interactive form is covered by the menu tests
            with self.subTest(doc=name, args=args):
                proc = run_cli(*args)
                self.assertIn(proc.returncode, (0, 1), proc.stderr)
                if proc.returncode == 0:
                    self.assertNotIn("error:", proc.stderr)
                self.assertEqual(invalid.issubset(set(args)), proc.returncode == 1)

    def test_transcript_matches_live_output(self):
        transcript = (ROOT / "demo" / "transcript.txt").read_text()
        self.assertIn("width must be a number", transcript)
        self.assertIn("outside the built-in table", transcript)

        chunks = []
        current = None
        for line in transcript.splitlines():
            if line.startswith("$ "):
                current = [line[2:].strip(), []]
                chunks.append(current)
            elif current is not None:
                if line.startswith("---"):
                    current = None
                else:
                    current[1].append(line)

        replayed = 0
        for command, output in chunks:
            parts = command.split()
            if parts[:2] != ["python3", "stitchgauge.py"]:
                continue
            args = parts[2:]
            if not args:
                continue
            while output and not output[-1].strip():
                output.pop()
            body = "\n".join(output)
            if not any(head in body for head in ("  GAUGE", "  ADJUSTMENT", "  YARN")):
                continue
            proc = run_cli(*args)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn(body, proc.stdout, "transcript drifted from live output")
            replayed += 1
        self.assertGreaterEqual(replayed, 3)


class ExitCodeContractTests(unittest.TestCase):
    def test_only_zero_one_and_two_are_returned(self):
        cases = (
            (("gauge", "--stitches", "40", "--rows", "56", "--width", "8",
              "--height", "8"), 0),
            (("gauge", "--stitches", "0", "--rows", "56", "--width", "8",
              "--height", "8"), 1),
            (("bogus",), 2),
            (("yarn", "--table"), 0),
            (("yarn", "--gauge", "0"), 1),
        )
        for args, expected in cases:
            with self.subTest(args=args):
                self.assertEqual(run_cli(*args).returncode, expected)

    def test_success_writes_nothing_to_stderr(self):
        proc = run_cli("adjust", "--pattern-sts", "6", "--pattern-rows", "6",
                       "--your-sts", "6.5", "--your-rows", "6.5",
                       "--stitches", "120", "--rows", "150")
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stderr, "")
        self.assertIn("Adjusted stitches     : 130", proc.stdout)
        self.assertIn("Adjusted rows         : 163", proc.stdout)


if __name__ == "__main__":
    unittest.main()
