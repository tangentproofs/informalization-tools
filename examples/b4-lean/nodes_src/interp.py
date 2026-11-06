NODES = []
def node(id, title, summary, body, quiz, caveats=(), widgets=None):
    NODES.append(dict(id=id, title=title, summary=summary, body=body, quiz=quiz, caveats=list(caveats), widgets=widgets))
def q(text, choices, answer, explain):
    return {"q": text, "type": "choice", "choices": choices, "answer": answer, "explain": explain}
def walk(title, steps):
    return [{"type": "walkthrough", "title": title, "config": {"steps": steps}}]

# ---------------------------------------------------------------- headline: the interpreter

node("runOp",
 "Headline (code): the b4 interpreter, one opcode at a time",
 "Status: CODE, checked by TESTS. `runOp` is the whole b4 instruction set as one Lean function from a machine state and an opcode byte to a new state. It is the real interpreter that the command-line program runs, and it is the same function the step lemmas in B4.Theory are about.",
 r"""## Plain English

**Definition (`runOp`, B4/Basic.lean lines 212–415).** Given a [machine state](#/node/State) and one byte, do
what that byte means and return the new state. [`step`](#/node/step) reads the byte at the instruction pointer,
calls `runOp`, and then moves the pointer on by one.

b4 is a small Forth-flavoured virtual machine: 64 KB of byte memory, a data stack and a control (return) stack
of 32-bit cells, and 32 *registers* that live in memory cells at the bottom of the address space.

### How the byte is decoded

The first four ranges are the **register ops**, each taking a register number in its low five bits
(B4/Basic.lean lines 213–230):

| Bytes | Op | What it does |
|---|---|---|
| `00` | nop | nothing |
| `01`–`1F` | `^R` invoke | push a return address, jump to the address held in register R |
| `20`–`3F` | `@R` read | push the value in register R |
| `40`–`5F` | `!R` write | pop a value into register R |
| `60`–`7F` | `+R` stream | push register R, then add the popped amount to it |

Everything from `80` up is a named two-letter op, dispatched by one big `match` (lines 231–415):

* **arithmetic and logic** `ad sb ml dv md sh an or xr nt eq lt` (lines 232–282). Arithmetic is signed 32-bit,
  done by converting to an integer and back modulo 2³² (`toInt32` / `fromInt32`, lines 169–174). Division and
  remainder by zero leave the stack with both operands popped and push nothing (lines 244–251). Comparisons push
  all-ones (−1) for true and 0 for false.
* **stack shuffles** `du sw ov zp` and **stack transfer** `dc` (data to control) and `cd` (control to data)
  (lines 283–302);
* **memory** `rb ri wb wi rs` (read/write a byte or a 32-bit cell at an address; lines 303–331);
* **literals** `lb li ls` (the byte or cell after the opcode, pushed and skipped; lines 317–337) and the constants
  `c0 c1 c2 n1 c4` (lines 397–401);
* **control flow** `jm` (absolute jump), `hp` (relative hop), `h0` (hop if zero), `cl` / `rt` (call, return), `nx`
  (count down the top of the control stack and hop back while it is non-zero) (lines 338–368);
* the [extension ops](#/node/f32op) `fa fs fm fd fl fi rn ct` (lines 369–396);
* `io` (lines 402–412): pop a command character; `'e'` and `'o'` pop a character and append it to the output
  buffer. **Every other command does nothing here.** The channel commands `'s'`, `'r'`, `'k'` are handled one
  level up, by the [swarm](#/node/Swarm.stepAt);
* `db` sets the debug register and `hl` clears the run flag (lines 413–414). Any other byte does nothing.

### What "fail" looks like

There is no error state. Popping an empty stack gives 0 and leaves the stack alone; pushing onto a full stack does
nothing ([dpush / dpop](#/node/dpush)); reading a cell past the end of memory gives 0
([getVal](#/node/getVal_setVal_self)). This is why `runOp` is a plain total function, and also why the
[step lemmas](#/node/step_binop) need hypotheses saying the stack has enough items and enough room.

### Who checks it

The command-line program (Main.lean, see the [Roadmap](#/roadmap)) is built on this function, and the repository's
cross-implementation acceptance suite (`b4-tests.org`, run by `imp/test-lean`) drives that program. Commit
344ccce reports "all 52 b4-tests pass". The suite lives outside `imp/lean` and was not run for this site.
""",
 [q("What does `runOp` do with an `io` command byte `'s'` (send) when the machine runs on its own?",
    ["Nothing: only 'e' and 'o' are handled; channel commands belong to the swarm layer",
     "It sends on a channel", "It halts the machine", "It raises an error"], 0,
    "B4/Basic.lean lines 402–412: the fallback case returns the state unchanged. Swarm.lean lines 21–23 say the same."),
  q("Which bytes are the register ops?",
    ["0x01–0x7F, in four blocks of 32: invoke, read, write, stream", "0x80–0x9F", "Only 0xFD", "0xC0–0xC1"], 0,
    "B4/Basic.lean lines 214–230."),
  q("What happens on `dv` when the divisor is 0?",
    ["Both operands are popped and nothing is pushed", "The machine halts", "0 is pushed", "Lean throws an exception"], 0,
    "B4/Basic.lean lines 244–247."),
  q("Is `runOp` the same function the step lemmas reason about?",
    ["Yes. B4.Theory imports B4.Basic and its lemmas are about `step`, which calls `runOp`",
     "No, B4.Theory defines its own separate model"], 0,
    "B4/Theory.lean line 1 imports B4.Basic; for example `step_of` (lines 515–519) unfolds the real `step`."),
 ],
 caveats=["Status: CODE + TESTED. It is a definition, so it is not 'proved'. It is exercised by the shared b4 acceptance suite (outside imp/lean, not run here) and by the `#eval` examples. B4.Theory proves facts about only some of its cases (see the review page).",
          "The CLI's disassembler names byte 0xBE `tm` (Main.lean line 58), but `runOp` has no case for 0xBE, so it does nothing. Probably a leftover.",
          "Main.lean also contains its own small assembler inside the REPL loop, separate from B4.Asm. The 52 tests exercise that one, not `Asm.assemble`."],
 widgets=walk("How one opcode is decoded (B4/Basic.lean, lines 212-421)", [
  {"text": "`step` fetches the byte at the instruction pointer (lines 417–419).", "link": "step"},
  {"text": "Byte 0 is a no-op; 0x01–0x7F are register ops, split by the top three bits into invoke, read, write and stream (lines 213–230)."},
  {"text": "Bytes from 0x80 go through one match on the byte value, one case per named op (lines 231–415).", "link": "runOp"},
  {"text": "Stack ops go through `dpush` / `dpop`, which quietly do nothing on overflow or underflow (lines 138–166).", "link": "dpush"},
  {"text": "Back in `step`, the pointer moves on by one (line 421). Ops with an inline argument (li, lb, jumps) have already moved it to the last byte of the argument, so the +1 lands on the next instruction.", "link": "step"},
 ]))

node("State",
 "The machine state",
 "A b4 machine is 64 KB of byte memory, two fixed-size arrays for the data and control stacks, and an output string. The registers, including the instruction pointer and the stack heights, are not separate fields: they are 32-bit cells in the first 256 bytes of memory.",
 r"""## Plain English

**Structure (`State`, B4/Basic.lean lines 88–93).** Four fields: `mem` (a byte array), `ds` and `cs` (arrays of
32-bit words for the data and control stacks), and `ob` (an output buffer that `io 'e'` / `io 'o'` append to).

The initial state (`mkInitialState`, lines 95–99) has 65,536 zero bytes and two stacks of 256 zero cells.

### Registers live in memory

Register *n* is the 4-byte little-endian cell at byte 4·*n*. Some registers have fixed jobs, at fixed byte
offsets (lines 9–19): the instruction pointer at 132, the data-stack height at 140, the control-stack height at
152, the run flag `ST` at 160, the debug flag at 164, the random seed at 180, the host clock at 184. B4.Theory
adds the *clock register* `T`, which is register 20, at byte 80 (B4/Theory.lean lines 307–313).

Because the instruction pointer and stack heights are memory cells, a program can overwrite them with `!R`. The
theory has to show that ordinary writes leave them alone. That is the job of the
[cell lemmas](#/node/getVal_setVal_self) and of the code-lives-above-256 assumption in the step lemmas.

### The stacks

The stack arrays always have 256 slots. The *contents* of a stack are the slots below its height register.
B4.Theory turns that into an ordinary list, [dstack](#/node/dstack).
""",
 [q("Where is the instruction pointer stored?",
    ["In a 32-bit memory cell at byte 132", "In a separate `ip` field of the structure", "On the control stack"], 0,
    "B4/Basic.lean lines 9 and 122–123."),
  q("How many slots does each stack array have?",
    ["256, always; the height register says how many are in use", "It grows as needed", "65,536"], 0,
    "STACKSZ, B4/Basic.lean line 6; mkInitialState, lines 95–99."),
  q("Can a b4 program change its own stack height directly?",
    ["Yes, by writing the register cell that holds it", "No, the heights are hidden fields"], 0,
    "The height is the cell at byte 140 (data) or 152 (control), and `!R` writes any register (lines 221–224)."),
 ])

node("step",
 "One machine step",
 "`step` runs the opcode under the instruction pointer and then adds one to the pointer. Every lemma in B4.Theory is ultimately a statement about this function.",
 r"""## Plain English

**Definition (`step`, B4/Basic.lean lines 417–421).** Read the byte at the instruction pointer, apply
[runOp](#/node/runOp) to it, then add one to the pointer.

The "+1 afterwards" convention explains several details. A jump to address *a* sets the pointer to *a* − 1
(`go`, lines 177–179) so that the +1 lands on *a*. Ops with an inline argument leave the pointer on the argument's
last byte. B4.Theory restates this as `step_of` (B4/Theory.lean lines 515–519): if the byte at the pointer is
*op* and the pointer is in code memory (≥ 256), then a step is `runOp` for *op* followed by the increment.

`go` also clamps jump targets below 256 up to 256 (line 178), so a jump never lands in the register area.
""",
 [q("After `step`, where does the pointer point for an ordinary one-byte op?",
    ["The next byte", "The same byte", "Two bytes on"], 0, "B4/Basic.lean line 421."),
  q("Why does a jump to address *a* set the pointer to *a* − 1?",
    ["Because `step` adds one after every op", "Because addresses are 1-based", "It is a bug"], 0,
    "`go`, B4/Basic.lean lines 177–179, and `go_eq`, B4/Theory.lean line 804."),
  q("What happens on a jump to address 10?",
    ["It is clamped up to 256, the start of code memory", "It jumps into the registers", "The machine halts"], 0,
    "B4/Basic.lean line 178."),
 ])

node("run",
 "`run`: the partial run loop",
 "`run` steps the machine while its run flag is 1 and its debug flag is 0. It is a `partial def`, so Lean accepts it without a termination proof, but it can't be unfolded in proofs. That is why B4.Theory introduces the total, fuelled runN.",
 r"""## Plain English

**Definition (`run`, B4/Basic.lean lines 423–427).** If the run flag `ST` is 1 and the debug flag `DB` is 0,
step and repeat; otherwise stop.

A b4 program can loop forever, so `run` really can fail to terminate. Lean only accepts such a definition when it
is marked `partial`. A partial definition runs normally when compiled, but Lean treats it as an opaque constant
in proofs, so no theorem can look inside it. Nothing in this repository proves anything about `run`.

The REPL in Main.lean (see the [Roadmap](#/roadmap)), the allocator harness ([MM.call](#/node/MM.code)) and the examples all execute
programs with `run`. Proofs use [runN](#/node/runN) instead.
""",
 [q("Why is `run` marked `partial`?",
    ["A b4 program can loop forever, so there is no termination proof", "For speed", "Because it does I/O"], 0,
    "B4/Basic.lean line 423."),
  q("Can a theorem in this repository unfold `run`?",
    ["No. A partial def is opaque to proofs, and no lemma mentions it", "Yes, freely"], 0,
    "No lemma in B4/Theory.lean mentions `run`. The theory works with `runN` (lines 493–495)."),
  q("What two conditions keep `run` going?",
    ["ST = 1 and DB = 0", "The stack is non-empty", "The pointer is below 64 KB"], 0, "B4/Basic.lean line 424."),
 ],
 caveats=["No theorem connects `run` to `runN`. This is expected, since `run` is opaque, but it means results about `runN` don't formally carry over to what the CLI executes."])

node("dpush",
 "Stack push and pop",
 "`dpush` writes a value at the current height and bumps the height, unless the stack is full. `dpop` returns the top value and lowers the height, or returns 0 if the stack is empty. Overflow and underflow are silent.",
 r"""## Plain English

**Definitions (`dpush`, `dpop`, B4/Basic.lean lines 138–151; `cpush`, `cpop` lines 153–166).** The height lives
in a register cell. Push stores into the array slot at that height and adds one, but only when the height is below
256. Pop reads the slot below the height and subtracts one, but only when the height is positive. Otherwise pop
returns 0 and changes nothing.

B4.Theory's view of these: when the state is [well-formed](#/node/WF) and the stack really has room or an item,
pushing appends to the [list view](#/node/dstack) and popping removes its last element, leaving the registers,
the other stack, high memory and the output alone (`dpush_view`, `dpop_view`, `cpush_view`, `cpop_view`,
B4/Theory.lean lines 414–480). These four are the building blocks of every step lemma.
""",
 [q("What does `dpop` return on an empty stack?",
    ["0, with the state unchanged", "An error", "The bottom slot"], 0, "B4/Basic.lean lines 145–151."),
  q("What do the `_view` lemmas need in order to say a push appends to the list?",
    ["A well-formed state and a height below 256", "Nothing", "An empty stack"], 0,
    "`dpush_view`, B4/Theory.lean line 414: hypotheses `WF s` and `getDSH s < STACKSZ`."),
  q("Does pushing onto a full stack overwrite the top?",
    ["No, it does nothing", "Yes"], 0, "B4/Basic.lean line 140."),
 ],
 caveats=["Status of the `_view` lemmas: PROVEN (complete-looking proofs, not built here)."])

node("f32op",
 "Extension ops: floats, random numbers, clock time",
 "Status: CODE only, no lemmas. Eight extra ops share b4's 32-bit cells: fa fs fm fd fl fi treat cells as IEEE single-precision bit patterns, rn draws from a seeded generator, and ct reads the host clock.",
 r"""## Plain English

These were added in commit 7096622 ("floats, as in bend", meaning the b4 implementation in the Bend language).

**Floats (`f32op`, `f32lt`, `itof`, B4/Basic.lean lines 187–199; cases at lines 369–391).** A cell holds the bit
pattern of a 32-bit float. `fa fs fm fd` reinterpret the top two cells as floats, add, subtract, multiply or
divide them, and push the bits of the result. `fl` pushes −1 if the second is less than the top, otherwise 0. `fi`
converts a signed integer to a float.

**Random numbers (`rnNext`, `mix32`, lines 201–209; case at lines 392–394).** The seed lives in a system cell
(byte 180, starting at 0, so every run draws the same numbers unless the program seeds it). Each `rn` adds the
32-bit golden-ratio constant 0x9E3779B9 to the seed (a Weyl sequence), stores it, and pushes the seed scrambled by
MurmurHash3's 32-bit finalizer. The b4a version of the same routine is in examples/Inline.lean lines 7–18, whose
comment says it gives the same numbers as the op.

**Clock time (`ct`, lines 395–396).** Pushes the cell at byte 184, which the CLI sets to the Unix time in seconds
before each input line (Main.lean lines 118–121). Inside a pure Lean evaluation that cell is just 0.

`ct` is different from the clock register `T` that B4.Theory and the swarm use. `T` is a logical clock
that programs set themselves; `ct` is the wall clock.
""",
 [q("How is a float stored on the b4 stack?",
    ["As the 32-bit IEEE bit pattern in an ordinary cell", "In a separate float stack", "As a fixed-point number"], 0,
    "B4/Basic.lean lines 187–192."),
  q("Does `rn` give different numbers on each run of the same program?",
    ["Not unless the program seeds it, because the seed cell starts at 0", "Yes, it reads the host's entropy"], 0,
    "Docstring at B4/Basic.lean lines 14–16."),
  q("Is `ct` the same clock as register T used by the swarm?",
    ["No. `ct` reads the host's wall-clock cell, and T is a logical clock", "Yes"], 0,
    "RCK_OFF (byte 184) versus CLK_OFF (byte 80), B4/Basic.lean line 19 and B4/Theory.lean line 307."),
 ],
 caveats=["Status: CODE, with UNPROVEN docstring claims. No lemma covers any extension op. The `mix32` docstring says it is a bijection (B4/Basic.lean lines 204–205). That is true of MurmurHash3's finalizer, but it is not proved here.",
          "The rn/b4a agreement claimed in examples/Inline.lean line 32 is TESTED only by an `#eval` whose expected output is written in a comment. Nothing fails if it differs."])
