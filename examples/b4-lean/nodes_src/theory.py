NODES = []
def node(id, title, summary, body, quiz, caveats=(), widgets=None):
    NODES.append(dict(id=id, title=title, summary=summary, body=body, quiz=quiz, caveats=list(caveats), widgets=widgets))
def q(text, choices, answer, explain):
    return {"q": text, "type": "choice", "choices": choices, "answer": answer, "explain": explain}
def walk(title, steps):
    return [{"type": "walkthrough", "title": title, "config": {"steps": steps}}]

# ---------------------------------------------------------------- headline: runN

node("runN",
 "Headline: runN, a total run with fuel",
 "Status: PROVEN, but only the unfolding lemma. `runN n s` runs the real machine for at most n steps. Recursion on n makes it total, so proofs can unfold it, unlike the partial `run`. Nothing yet links it to `run` or proves anything about runs longer than one step.",
 r"""## Plain English

**Definition (`runN`, B4/Theory.lean lines 493–495).** With 0 fuel, return the state unchanged. With *n* + 1 fuel,
if the run flag is 1 and the debug flag is 0, take one [step](#/node/step) and continue with *n*; otherwise stop.

**Theorem (`runN_succ_of_running`, lines 500–502).** If the machine is `Running` (run flag 1, debug flag 0,
line 498), then running with *n* + 1 fuel is one step followed by running with *n* fuel.

### Why total matters

[`run`](#/node/run) is a `partial def`. It executes fine, but Lean gives proofs no way to look inside it, so you
can't prove anything about what `run` returns. `runN` does the same thing as `run`, cut off after *n* steps, and is
defined by ordinary recursion on *n*. So Lean knows it terminates, and a proof can unfold it one step at a time
with `runN_succ_of_running` and then use a [step lemma](#/node/step_binop) for that step. This is the standard
fuel technique for reasoning about interpreters in a total language.

### What it does not give (yet)

* **No link to `run`.** Nothing states that `run s` equals `runN n s` once *n* is large enough. Such a statement
  can't even be proved while `run` is partial.
* **No multi-step theorems.** At the pinned commit, `runN` appears only in its definition and in
  `runN_succ_of_running`. No lemma composes several steps into a statement about a whole program, for example
  "this sequence of instructions leaves *x* + *y* on the stack and halts".
* **No lemma that `hl` stops `runN`.** [`step_hl`](#/node/step_h0) shows the run flag is 0 after `hl`, and
  `runN`'s definition then stops by unfolding, but nobody has written that down as a lemma.

So `runN` is the foundation for program proofs, and those proofs are still to come.
""",
 [q("Why can proofs reason about `runN` but not `run`?",
    ["`runN` recurses on a fuel number, so it is total. `run` is partial and opaque to proofs",
     "`runN` is faster", "`run` uses I/O"], 0,
    "B4/Theory.lean lines 492–495 versus B4/Basic.lean line 423."),
  q("What does `runN_succ_of_running` say?",
    ["If the machine is running, n+1 fuel is one step then n fuel",
     "runN always halts the machine",
     "runN n s = run s for large n"], 0, "B4/Theory.lean lines 500–501."),
  q("Is there a theorem that `runN` agrees with `run` for enough fuel?",
    ["No", "Yes, in B4/Theory.lean"], 0,
    "Nothing mentions `run` in B4/Theory.lean. It can't, since `run` is partial."),
  q("What does `runN 0 s` return?",
    ["s, unchanged", "The halted state", "The initial state"], 0, "B4/Theory.lean line 494."),
 ],
 caveats=["Status: PROVEN for `runN_succ_of_running` (a one-line `simp`, not built here). Everything about whole-program behaviour is UNPROVEN: there are no multi-step lemmas yet.",
          "`runN` is about the real `step` from B4/Basic.lean, not a separate model."],
 widgets=walk("How runN and its lemma go (B4/Theory.lean, lines 492-502)", [
  {"text": "Zero fuel: stop (line 494)."},
  {"text": "Fuel n+1: if ST = 1 and DB = 0, step and continue with n, else stop. The same test as `run` (line 495; compare B4/Basic.lean line 424).", "link": "run"},
  {"text": "`Running s` packages the two flag conditions as a proposition (line 498)."},
  {"text": "`runN_succ_of_running`: under `Running s`, the `if` takes its true branch, and `simp` with the two flag facts closes the goal (lines 500–502)."},
  {"text": "A program proof would then rewrite with this lemma once per instruction and use a step lemma for each one. No such proof exists yet.", "link": "step_binop"},
 ]))

# ---------------------------------------------------------------- headline: step lemmas

node("step_binop",
 "Headline: the step lemmas, read through the binary-op family",
 "Status: PROVEN (not built). On a well-formed machine whose next op is a binary op such as `ad`, one step replaces the top two items x, y by f(x, y), advances the pointer by one and changes nothing else. Sibling lemmas cover li nt ri wi jm h0 hl dc cd cl rt @T !T.",
 r"""## Plain English

**Theorem (`step_binop`, B4/Theory.lean lines 582–588).** Suppose:

* the state is [well-formed](#/node/WF) (memory 64 KB, stacks 256, heights in range);
* the instruction pointer is in code memory (at least 256) and one more still fits in 32 bits;
* the byte at the pointer is *op*;
* the [data stack](#/node/dstack), as a list, is *xs* followed by *x* and then *y* (so *y* is on top);
* `runOp` on *op* is "pop *y*, pop *x*, push *f x y*".

Then after one [step](#/node/step): the state is still well-formed, the pointer has advanced by one, the data stack
is *xs* followed by *f x y*, and the new state is [`Same`](#/node/Same) as the old one in everything else (control
stack, run and debug flags, code memory, output buffer, clock).

`step_binop'` (lines 658–664) is the same with the last hypothesis stated for every state. The eight
`runOp_ad` … `runOp_lt` lemmas (lines 590–621) supply that hypothesis for `ad sb ml an or xr eq lt`, with *f* the
signed 32-bit add, subtract and multiply, the bitwise and/or/xor, and the −1/0 comparisons.

### The family

All the step lemmas have the same shape: hypotheses about the pointer, the opcode byte and the stacks as lists,
and conclusions saying what changed, plus a frame (`Same` or [`Frame`](#/node/Same)) for what didn't:

| Lemma | Lines | Effect |
|---|---|---|
| `step_li` | 641–653 | push the 4-byte word after the opcode, pointer +5 ([node](#/node/step_li)) |
| `step_nt` | 671–684 | complement the top |
| `step_ri` | 691–706 | replace an address on top by the word in code memory there |
| `step_wi` | 778–801 | store a word into code memory: high memory becomes `writeWord` of it |
| `step_jm` | 811–820 | jump to the inline address |
| `step_h0`, `step_hl` | 831–874 | hop if zero; halt ([node](#/node/step_h0)) |
| `step_rdT`, `step_wrT`, `step_wi_clk` | 881–932 | read and write the clock register T ([node](#/node/step_wrT)) |
| `step_dc`, `step_cd` | 974–1010 | move a value between the stacks |
| `step_cl`, `step_rt` | 1020–1060 | call and return ([node](#/node/step_cl)) |

### What makes these lemmas possible

Registers are memory cells, so "pushing doesn't move the pointer" is a real fact about bytes, not a given. It rests
on two [cell lemmas](#/node/getVal_setVal_self) (a written cell reads back, and disjoint cells don't interfere),
on `reg_offs` (the register cells are 4 bytes apart and below 256, line 83), and on the
[push/pop list views](#/node/dpush).

### Not covered

There are no step lemmas for `dv md sh du sw ov zp rb wb lb rs ls hp nx io db`, the register ops other than `@T`
and `!T` (including `^R` invoke and `+R` stream), or the [extension ops](#/node/f32op).
""",
 [q("In `step_binop`, which stack item is `y`?",
    ["The top", "The second from top", "The bottom"], 0,
    "The stack is *xs* followed by [x, y], bottom first (B4/Theory.lean line 584, and `dstack`'s docstring at line 102)."),
  q("Which of these does `step_binop` NOT require?",
    ["That the result fits in 16 bits", "A well-formed state", "Pointer at least 256", "At least two items on the stack"], 0,
    "B4/Theory.lean lines 583–585 list the hypotheses. f is arbitrary."),
  q("Is there a step lemma for `dv` (division)?",
    ["No. The binary-op family covers ad sb ml an or xr eq lt only", "Yes"], 0,
    "There is no `runOp_dv` in B4/Theory.lean. `dv` has a divide-by-zero branch (B4/Basic.lean lines 244–247), so it doesn't fit the pattern."),
  q("What does `Same s s'` guarantee?",
    ["Control stack, flags, code memory, output and clock are unchanged", "The states are equal", "Only the pointer is unchanged"], 0,
    "B4/Theory.lean lines 522–528."),
  q("Are these lemmas about the interpreter the CLI runs?",
    ["Yes. They are about `step` and `runOp` from B4/Basic.lean", "No, about a simplified copy"], 0,
    "`step_of` (lines 515–519) unfolds B4.Basic's `step` directly."),
 ],
 caveats=["Status: PROVEN, meaning the file has complete-looking proofs with no sorry. Not built for this site.",
          "Trust note: the cell read-back lemma at the bottom of this stack uses `bv_decide` (B4/Theory.lean line 39). `bv_decide` checks a SAT certificate by compiled evaluation, so it relies on Lean's `Lean.ofReduceBool` axiom, the same extra trust that `native_decide` needs. Through `getVal_setVal_self` and the register read-back lemmas, every step lemma that sets the pointer depends on it.",
          "The lemmas assume code runs from high memory (≥ 256). They say nothing about a program that executes from, or writes into, the register area, which is exactly where the pointer and stack heights live."],
 widgets=walk("How step_binop is proved (B4/Theory.lean, lines 536-588)", [
  {"text": "`step_of`: when the pointer is ≥ 256, the fetched byte is the code-memory byte, so a step is `runOp` then pointer +1 (lines 515–519).", "link": "step"},
  {"text": "`dpop_same`, twice: popping a well-formed stack *xs*++[x]++[y] returns y then x, keeps well-formedness and leaves everything in `Same` alone (lines 542–547).", "link": "dpush"},
  {"text": "The height after two pops is below 256, so `dpush_same` applies: the list becomes *xs*++[f x y] (lines 572–575)."},
  {"text": "`binop_same` chains these three, composing the `Same` frames by transitivity (lines 566–578).", "link": "Same"},
  {"text": "`step_next` adds the pointer increment, using `setIP_same` and the cell read-back for the pointer register (lines 555–563).", "link": "getVal_setVal_self"},
  {"text": "`step_binop` is `step_next` applied to `binop_same`, rewritten by the hypothesis about `runOp` (line 588)."},
 ]))

# ---------------------------------------------------------------- statement set / supporting

node("WF",
 "Well-formed states",
 "A state is well-formed when memory is exactly 64 KB, both stack arrays have 256 slots, and both stack heights are at most 256. Every step lemma assumes it and gives it back.",
 r"""## Plain English

**Structure (`WF`, B4/Theory.lean lines 90–100).** Five facts: memory size is 65,536; the data and control arrays
have size 256; the data and control heights are at most 256.

The interpreter never changes the sizes, but a program could write a large number into a height register. `WF`
rules that out, and the step lemmas show that the instructions they cover keep it.

The initial state satisfies all five facts, but **no lemma in the file says so**, and no lemma says every
instruction preserves `WF`. Only the instructions that have step lemmas are covered.
""",
 [q("Which is NOT part of `WF`?",
    ["The pointer is at least 256", "Memory is 64 KB", "Data height ≤ 256", "Control stack array has 256 slots"], 0,
    "B4/Theory.lean lines 90–100. The pointer condition is a separate hypothesis of each step lemma."),
  q("Is it proved that `mkInitialState` is well-formed?",
    ["No, it isn't stated", "Yes"], 0, "Search B4/Theory.lean: no lemma mentions mkInitialState."),
  q("Why can a height be out of range at all?",
    ["Heights are memory cells a program can overwrite", "Lean arrays can shrink"], 0,
    "B4/Basic.lean lines 10–11 and 221–224."),
 ])

node("dstack",
 "The stacks as lists",
 "`dstack s` is the data stack as a list, bottom first: the first `height` slots of the array. `cstack` is the same for the control stack. Stating lemmas on lists hides the array slots above the height, whose stale contents are irrelevant.",
 r"""## Plain English

**Definitions (`dstack`, `cstack`, B4/Theory.lean lines 103–106).** Take the array as a list and keep the first
*h* elements, where *h* is the height register.

With these, pushing *v* is "append *v*" and popping is "remove the last element"
([push/pop lemmas](#/node/dpush)). The top of the stack is the **last** element of the list.

`high s` (line 109) is the same idea for memory: the byte at *a* if *a* ≥ 256, and 0 in the register area.
`View` and `view` (lines 112–123) gather pointer, both stack lists, the two flags, `high` and the output: what a
program "sees". `view` isn't used by any lemma yet.
""",
 [q("Which end of `dstack s` is the top of the stack?",
    ["The last element", "The first element"], 0, "Bottom first, B4/Theory.lean line 102."),
  q("What does `high s a` return for an address below 256?",
    ["0, hiding the register area", "The register byte"], 0, "B4/Theory.lean line 109."),
  q("Do stale values above the height appear in `dstack`?",
    ["No, only the first `height` slots are taken", "Yes"], 0, "B4/Theory.lean line 103."),
 ])

node("Same",
 "Frame conditions: Same and Frame",
 "`Same s s'` says everything a step might touch, other than the pointer and the data stack, is unchanged: the control stack, the run and debug flags, code memory, output and clock. `Frame` drops the control stack, for the instructions that move values between the stacks.",
 r"""## Plain English

**Structure (`Same`, B4/Theory.lean lines 522–528).** Six equalities between *s* and *s'*: the control stack,
`ST`, `DB`, high memory, the output buffer and the clock register are the same.

**Structure (`Frame`, lines 938–943).** The same without the control stack. It is used by `dc cd cl rt`, which change
both stacks.

Both are reflexive and transitive (`Same.refl`, `Same.trans`, `Frame.trans`, lines 530–534 and 947–949), and
`Frame.of_same` (line 945) weakens one to the other. So a proof can chain per-operation frames into one frame for
the whole step.
""",
 [q("Which is NOT preserved according to `Same`?",
    ["The data stack", "The control stack", "Code memory", "The clock"], 0, "B4/Theory.lean lines 522–528."),
  q("Why is there a second, weaker frame `Frame`?",
    ["For instructions that also change the control stack", "For floats", "For I/O"], 0,
    "B4/Theory.lean lines 935–943."),
  q("Does `Same` say the two states are equal?",
    ["No. The pointer, the data stack and the register area can differ", "Yes"], 0,
    "It lists only six components."),
 ])

node("getVal_setVal_self",
 "Cells read back what was written",
 "Status: PROVEN (with a bv_decide trust note). Writing a 32-bit value into four little-endian bytes and reading them back gives the value, and writing one cell leaves any disjoint cell unchanged. All the register bookkeeping in B4.Theory reduces to these two facts.",
 r"""## Plain English

**Theorem (`getVal_setVal_self`, B4/Theory.lean lines 55–68).** If the cell at *off* fits in memory, reading it
after writing *v* there gives *v*.

**Theorem (`getVal_setVal_of_disjoint`, lines 71–78).** If two cells don't overlap, writing one doesn't change
what the other reads.

The first needs `bytes_word` (lines 36–39): splitting a word into four bytes and OR-ing them back with shifts gives
the word. That is proved by `bv_decide`, a bit-blasting decision procedure.

Several dozen short `@[simp]` lemmas follow (lines 137–369): writing the data height leaves the pointer alone, writing
the pointer leaves the debug flag alone, and so on, for every pair of the pointer, the two heights, the two flags and
the clock. Each one is `getVal_setVal_of_disjoint` with the two offsets.

`getVal` and `setVal` themselves (B4/Basic.lean lines 102–119) return 0 or do nothing when the cell would run off the
end of memory.
""",
 [q("What does `getVal` return for a cell that runs off the end of memory?",
    ["0", "An error", "The partial bytes"], 0, "B4/Basic.lean line 109."),
  q("What tactic proves the byte-reassembly fact `bytes_word`?",
    ["bv_decide", "decide", "omega"], 0, "B4/Theory.lean line 39."),
  q("Why do the register lemmas follow from the disjoint-cell lemma?",
    ["Each register is its own non-overlapping 4-byte cell", "Registers are separate fields"], 0,
    "`reg_offs`, B4/Theory.lean lines 83–84."),
 ],
 caveats=["`bv_decide` relies on the `Lean.ofReduceBool` axiom (a compiled check of the SAT certificate). This is the one place in the repository where extra trust beyond Lean's three standard axioms enters, and everything that reads back the pointer or a height depends on it."])

node("step_li",
 "Step lemma: `li` pushes an inline word",
 "Status: PROVEN. If the next instruction is `li` and there is room on the stack, one step pushes the 4-byte little-endian word stored right after the opcode and moves the pointer on by five.",
 r"""## Plain English

**Theorem (`step_li`, B4/Theory.lean lines 641–653).** Hypotheses: well-formed, pointer ≥ 256 and pointer + 5 below
64 KB, byte `0x97` at the pointer, the data stack is *xs* with fewer than 256 items. Conclusions: still
well-formed, pointer + 5, the stack is *xs* followed by `word (high s) (pointer + 1)`, and the rest is unchanged
(`Same`).

`word` (lines 624–626) reads four bytes of a byte-function as a little-endian word, and `getVal_high`
(lines 629–634) says `getVal` on high memory equals `word` of `high`. So the lemma's conclusion talks only about
the program-visible [view](#/node/dstack), not about raw byte arrays.
""",
 [q("By how much does `li` move the pointer?",
    ["5: the opcode plus a 4-byte argument", "1", "4"], 0, "B4/Theory.lean line 644."),
  q("Which extra hypothesis does `step_li` need that `step_binop` doesn't?",
    ["Room on the stack, and pointer + 5 inside memory", "An empty stack", "The clock is 0"], 0,
    "B4/Theory.lean lines 642–643."),
  q("Where does the pushed value come from?",
    ["The four bytes after the opcode, read little-endian", "Register X", "The control stack"], 0,
    "B4/Theory.lean line 645 and `word`, lines 624–626."),
 ],
 caveats=["Status: PROVEN (not built)."])

node("step_h0",
 "Step lemmas: `h0` (hop if zero) and `hl` (halt)",
 "Status: PROVEN. `h0 d` pops a value: if it was 0 the pointer moves by the signed byte d, measured from the h0 instruction, otherwise it skips past the 2-byte instruction. `hl` sets the run flag to 0.",
 r"""## Plain English

**Theorem (`step_h0`, B4/Theory.lean lines 831–866).** If the next byte is `0x9C`, the stack is *xs* followed by
*v*, and the hop target is inside code memory, then after one step the stack is *xs* and the pointer is
pointer + `sbyte`(next byte) if *v* = 0, else pointer + 2. `sbyte` (line 824) reads a byte as a signed distance
−128…127. The rest is `Same`.

`h0` is the branch that the assembler's structured macros `.i` (if) and `.d` (do) lay down
([assembler](#/node/Asm.assemble)).

**Theorem (`step_hl`, lines 872–874).** After a step on `0xFF`, the run flag is 0. That is all it states. With the
definition of [runN](#/node/runN), that means a fuelled run stops at the next check, though no lemma says so.

`step_jm` (lines 811–820) covers unconditional jumps. There is no lemma for the unconditional relative hop `hp`
or for the loop instruction `nx`.
""",
 [q("Where does an `h0` hop measure its distance from?",
    ["From the h0 instruction itself", "From the next instruction", "From address 0"], 0,
    "B4/Theory.lean lines 830 and 836."),
  q("When the popped value is non-zero, where does the pointer go?",
    ["pointer + 2, past the opcode and its distance byte", "pointer + 1", "It halts"], 0,
    "B4/Theory.lean line 837."),
  q("What exactly does `step_hl` conclude?",
    ["The run flag is 0 after the step", "runN returns immediately", "The stack is empty"], 0,
    "B4/Theory.lean lines 872–873."),
 ],
 caveats=["Status: PROVEN (not built)."])

node("step_cl",
 "Step lemmas: call and return (`cl`, `rt`, `dc`, `cd`)",
 "Status: PROVEN. `cl a` pushes the address after the 5-byte instruction on the control stack and jumps to a. `rt` pops an address and jumps there. `dc` and `cd` move one value between the data and control stacks. All four come with a `Frame` saying flags, code memory, output and clock are unchanged.",
 r"""## Plain English

**Theorem (`step_cl`, B4/Theory.lean lines 1020–1037).** With room on the control stack and an inline target
≥ 256: after one step the pointer is the target, the data stack is unchanged, and the control stack has
pointer + 5 appended.

**Theorem (`step_rt`, lines 1044–1060).** If the control stack is *cs* followed by *a* and *a* ≥ 256, then after
one step the pointer is *a* and the control stack is *cs*. (`rt` to address 0 means "return to the host", which
clears the run flag. That case is excluded by *a* ≥ 256.)

**Theorems (`step_dc`, `step_cd`, lines 974–1010).** Move the top of one stack to the top of the other.

Together these are enough to reason about subroutine calls, which is the next step toward multi-step program
proofs.
""",
 [q("What return address does `cl` push?",
    ["pointer + 5, the byte after the instruction and its 4-byte target", "pointer + 1", "the target"], 0,
    "B4/Theory.lean line 1024."),
  q("Why does `step_rt` require the return address to be ≥ 256?",
    ["Returning to 0 halts the machine instead, a different case", "Lean needs it for termination"], 0,
    "B4/Basic.lean line 352."),
  q("Which frame do these lemmas use?",
    ["`Frame`, since the control stack changes", "`Same`"], 0, "B4/Theory.lean lines 935–943."),
 ],
 caveats=["Status: PROVEN (not built)."])

node("step_wrT",
 "Step lemmas for the clock register T (`@T`, `!T`)",
 "Status: PROVEN. Register T (byte 80) is the machine's logical clock, after the time variable of Hehner's timed programs. `@T` pushes it, `!T` pops a value into it, and a `wi` into code memory leaves it alone. A program may set T to any value, including an earlier one.",
 r"""## Plain English

**Definitions (`CLK_OFF`, `getClk`, `setClk`, B4/Theory.lean lines 305–313).** The clock is register T, number 20,
so its cell is at byte 80.

**Theorem (`step_rdT`, lines 881–890).** On byte `0x34` (that is `@T`), push the clock.

**Theorem (`step_wrT`, lines 897–918).** On byte `0x54` (`!T`), pop *v* and the clock becomes *v*. The pointer,
the other stack, the flags, code memory and the output are unchanged.

**Theorem (`step_wi_clk`, lines 921–932).** A `wi` into code memory doesn't change the clock.

The clock is also part of the `Same` / `Frame` conditions, so every step lemma above says the clock is untouched.
The [swarm](#/node/Swarm.recv) is where the clock gets its meaning: a receive moves it forward past the message's
send time.
""",
 [q("Which register is the clock?",
    ["T, register 20, the cell at byte 80", "CK, the host clock", "PC"], 0, "B4/Theory.lean line 307."),
  q("Can `!T` move the clock backwards?",
    ["Yes. It stores whatever value is popped", "No, it takes the maximum"], 0, "B4/Theory.lean line 899."),
  q("Is the clock the same as the `ct` wall-clock op?",
    ["No", "Yes"], 0, "`ct` reads byte 184 (B4/Basic.lean line 396)."),
 ],
 caveats=["Status: PROVEN (not built). Note for the swarm: nothing prevents a program from moving its own clock backwards, and the reasoning behind `Swarm.settle` seems to assume clocks only move forward (see that node)."])
