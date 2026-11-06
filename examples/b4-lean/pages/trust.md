# Trust: what was and wasn't checked

## Not built

**The Lean was not built for this site.** No `lake`, `lean` or `elan` was run, and neither were the `#eval`
tests, the random allocator test or the shared acceptance suites. "Proved" on this site means the file contains
what looks like a complete proof, not that Lean's kernel accepted it.

The project pins Lean `v4.35.0-rc1` (commit 344ccce) and depends only on Lean's own `Std` (no Mathlib).

## Gaps, axioms and escape hatches

A text search of the 13 `.lean` files under `imp/lean` at the pinned commit:

| What | Count | Where |
|---|---|---|
| `sorry` | 0 | |
| `admit` | 0 | |
| `axiom` declarations | 0 | |
| `native_decide` | 0 | |
| `bv_decide` | 1 | B4/Theory.lean line 39 (`bytes_word`) |
| `decide` | 5 | B4/Theory.lean line 84; B4/Swarm.lean lines 199, 203–204; B4/MM.lean line 104. Small closed facts; also one *function* use, `decide (… < …)` in B4/Swarm.lean line 100, which is ordinary code |
| `implemented_by`, `extern`, `opaque`, `unsafe` | 0 | |
| `partial def` | 3 | B4/Basic.lean line 423 (`run`), B4/Asm.lean line 109 (`tokenize`), Main.lean line 113 (`loop`) |

### bv_decide

`bv_decide` proves bit-vector facts by bit-blasting to SAT and checking the solver's certificate. The check runs
as compiled code, so the resulting proof depends on Lean's `Lean.ofReduceBool` axiom, the same extra trust as
`native_decide`. Here it proves one fact: splitting a 32-bit word into four bytes and reassembling it gives the word.
`getVal_setVal_self` uses it, and through the register read-back lemmas (`getIP_setIP`, `getDSH_setDSH`, …) so
does every step lemma. The fact itself is elementary and certainly true. The point is only which axioms the step
lemmas rest on.

### partial def

The three `partial def`s are all programs, not proofs, and nothing proved depends on them. `run` matters most:
because it is partial, no theorem can say anything about what it returns. That is why B4.Theory introduces
[runN](#/node/runN), and why no theorem connects the two. The allocator test and the shell both execute with `run`.

## Tests that can't fail

Every test in `imp/lean` is an `#eval` whose expected output is written in a comment (B4/Swarm.lean line 233;
examples/Inline.lean lines 33–37; examples/MMTest.lean line 32). Building the files succeeds whatever they print.
None was run here.

## Declarations

All declarations were found by scanning the source text (`extracted: false`), not from a compiled build, so some
dependency links can be missing or wrong. Known artefacts on this site:

* **Scope of the scan.** The scan covers `imp/lean/B4`, `B4.lean`, examples/MMTest.lean and examples/DSLTest.lean.
  Main.lean and examples/Inline.lean are left out because they reuse names the scanner can't tell apart from
  the library's (`State`, `go`), which produced false dependency cycles. Those files are described in prose, on the
  [Roadmap](#/roadmap), and their line references are not links.
* Hypotheses named `hop` in the step lemmas show up as "mentions" of the function `hop`.
* Short names are matched by spelling, so a mention of `T` or `R` can show up as `Register.toNat`, and `word` in
  B4.Theory and in B4.Asm can be confused.

## Who wrote this

All explanations were written by an AI (Claude), and nobody has reviewed them. The b4 project's author, Michal
Wallace, also runs this explainer site, but these pages are not the project's documentation.
