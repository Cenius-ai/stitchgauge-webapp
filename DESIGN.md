# StitchGauge design system

Committed direction (do not fall back to a generic palette):

| Axis | Decision |
|------|----------|
| Archetype | `cli` - the terminal *is* the product surface |
| Style family | calm-precise |
| Surface | terminal dark (the only honest CLI surface) |
| Type | system monospace, single family, no display face |
| Density | compact |
| Accent | one only: `oklch(0.58 0.12 279)` = `#6c71c0` |
| Signature | aligned columns; one accent for primary status; no colour-only signal |

## Tokens

Because the plan fixes the output contract (*"Plain ASCII output with no ANSI
colour"* - **F5 / non-functionals**), the tokens below are the palette any
colour-capable renderer must use if one is ever added; today they are honoured
as *shape* rules (alignment, separators, wording) so the surface stays
identical in every terminal, in `less`, and in a redirected file. The accent
hex `#6c71c0` is the non-CSS form for any chart/canvas tooling.

```
--accent:          #6c71c0   oklch(0.58 0.12 279)   primary status, rules
--accent-strong:   #8b90e0                         accent used as text (>= 6.4:1)
--bg:              #12131a                          terminal dark
--surface:         #191b24                          block background (if painted)
--border:          #262a38                          separators, table rules
--text:            #e6e7f0                          body (>= 15:1 on --bg)
--text-muted:      #a2a6bd                          labels, hints (7.8:1 on --bg)
--ok:              --text (words do the work)       status is never colour-only
```

Contrast floor: body text `#e6e7f0` and label text `#a2a6bd` clear WCAG AA on
`#12131a`; the raw accent is reserved for rules/marks and the lightened
`--accent-strong` carries accent *text* at 6.4:1.

## Type ramp (monospace, compact)

| Role | Treatment |
|------|-----------|
| Product name / block title | UPPERCASE or title case, no decoration, followed by an ASCII rule |
| Field label | lowercase or sentence case, left column, `:` separator |
| Value | right of the label, always two decimals for measurements and ratios |
| Hint / note | one indented line under the block, same size, muted if colour exists |

## Layout skeleton (committed)

- **Help-first**: every screen starts with what it is, then the options.
- **Aligned columns**: one label column of 22 characters, separator `:`, value
  column starts at the same offset in every block (`GAUGE`, `ADJUSTMENT`,
  `YARN`, the yarn table).
- **Box separators, ASCII only**: `-` rules of 56 characters instead of
  Unicode box-drawing, so output survives any code page.
- **Compact spacing scale**: `0, 1, 2` blank lines only - one blank line around
  a block, two around a screen change. No other spacing values exist.
- **No chrome**: no headers per line, no borders around every line, no splash
  screen, no spinner (everything is local and instant).

## Status language

Status is carried by **words**, never colour alone:

| State | Rendering |
|-------|-----------|
| success | the result block itself; `Category : Worsted (4)` |
| rejected input | one line prefixed `! ` in interactive mode, `error: ` on stderr in one-shot mode |
| out of range | `Category : (none)` plus a `Note` line naming the covered span |
| menu error | `! please choose 1-6` |

## Motion

None. Transitions in a terminal renderer would be latency, not polish.
