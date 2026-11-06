# Roadmap: reading the b4 Lean code in order

A reading order through `imp/lean`, from the interpreter to the shell. Line ranges are at the pinned commit.
Status labels: **PROVEN** (complete-looking proof, not built here), **TESTED** (`#eval` or acceptance tests only),
**CODE** (a program, with no claim attached), **UNPROVEN** (a claim stated in prose only).

## 1. The interpreter: B4/Basic.lean (453 lines, CODE)

The machine itself. Everything else imports it.

* lines 5–19: memory and stack sizes, and the byte offsets of the system registers (pointer 132, data height 140,
  control height 152, run flag 160, debug flag 164, seed 180, host clock 184);
* lines 21–86: `Register` and `Op`, names for registers and opcodes, with `Op.toByte`;
* lines 88–99: [State](#/node/State) and `mkInitialState`;
* lines 101–135: little-endian cells `getVal` / `setVal` and the register accessors;
* lines 137–166: [stack push and pop](#/node/dpush);
* lines 168–209: signed arithmetic, jumps (`go`, `hop`) and the helpers for the [extension ops](#/node/f32op);
* lines 212–415: [runOp](#/node/runOp), the opcode dispatch;
* lines 417–427: [step](#/node/step) and the partial [run](#/node/run);
* lines 429–451: an older `assemble` from a list of `Op` values (used with B4/DSL.lean).

## 2. The theory: B4/Theory.lean (1,062 lines, PROVEN)

Lemmas about the interpreter of step 1. It is not a separate model.

* lines 14–78: bytes and cells: a written cell reads back, disjoint cells don't interfere
  ([node](#/node/getVal_setVal_self)). `bytes_word` at lines 36–39 uses `bv_decide`;
* lines 80–301: register bookkeeping, dozens of `@[simp]` "writing X leaves Y alone" lemmas;
* lines 89–123: [WF](#/node/WF), [stacks as lists](#/node/dstack), `high`, `View`;
* lines 303–389: the clock register T (byte 80) ([node](#/node/step_wrT));
* lines 391–488: push and pop as list operations (the `_view` lemmas);
* lines 490–502: [runN](#/node/runN) and `runN_succ_of_running`;
* lines 504–578: `step_of`, the frame [Same](#/node/Same), and the composition lemmas `step_next`, `binop_same`;
* lines 580–1060: the step lemmas: [binary ops](#/node/step_binop), [li](#/node/step_li), nt, ri, wi, jm,
  [h0 and hl](#/node/step_h0), @T and !T, and [dc cd cl rt](#/node/step_cl).

## 3. The swarm: B4/Swarm.lean (237 lines, mostly CODE)

Several machines talking over channels. Imports B4.Theory.

* lines 1–24: the module doc, the best summary of the design (send, receive, check, waiting);
* lines 28–48: [Swarm](#/node/Swarm), messages, and the three io command codes;
* lines 50–100: `ioCmd`, [send and receive](#/node/Swarm.recv), [check](#/node/Swarm.check);
* lines 102–126: [stepAt](#/node/Swarm.stepAt), `sweep` and the fuelled `Swarm.run`;
* lines 128–153: [settle and runK](#/node/Swarm.settle) (soundness UNPROVEN);
* lines 155–207: `Step` / `Steps` and unfolding lemmas (PROVEN, all short);
* lines 209–235: loading code, and a two-machine demo (TESTED by `#eval`).

## 4. The heap model and the allocator: B4/Heap.lean (132 lines) and B4/MM.lean (133 lines)

* B4/Heap.lean lines 1–15: the module doc: one model, two instances;
* B4/Heap.lean lines 19–67: [blocks](#/node/Heap.Blk), `absorb`, `claim`, [alloc](#/node/Heap.alloc), `free`
  (CODE; termination PROVEN);
* B4/Heap.lean lines 69–130: `absorb_scale`, `claim_scale`, [alloc_scale](#/node/Heap.alloc_scale) (PROVEN);
* B4/MM.lean lines 1–22: the module doc, with the author's status note ("related only by a random test");
* B4/MM.lean lines 27–75: [the allocator in b4a](#/node/MM.code) (TESTED);
* B4/MM.lean lines 77–107: the [byte model](#/node/MM.alloc) as `Heap` with (12, 16), and
  [alloc_cells](#/node/MM.alloc_cells) (PROVEN);
* B4/MM.lean lines 109–131: [reading the heap back](#/node/MM.blocks) and calling routines;
* examples/MMTest.lean lines 1–32: the random test (TESTED).

## 5. The assembler and the inline macro: B4/Asm.lean (292 lines), B4/AsmSyntax.lean (39 lines)

* B4/Asm.lean lines 1–21: the b4a syntax in one list;
* B4/Asm.lean lines 25–151: `Program`, the op table, the tokenizer;
* B4/Asm.lean lines 153–261: the assembler state and the per-token step, including the structured macros;
* B4/Asm.lean lines 263–290: [assemble](#/node/Asm.assemble), `addr`, `code`, `load`;
* B4/AsmSyntax.lean lines 1–37: the [`b4a!`](#/node/Asm.elabB4a) term elaborator;
* examples/Inline.lean (37 lines): `rn` and the control macros written inline, with `#eval`s (TESTED by comments);
* B4/DSL.lean (165 lines) and examples/DSLTest.lean: the older `b4!` list-of-ops notation. Not imported by
  `B4.lean`.

## 6. The shell: Main.lean (298 lines, CODE + acceptance tests)

The `b4` executable that the shared test suites drive (`imp/test-lean` builds it and runs `b4-tests.org` and
`b4x-tests.org`).

* Main.lean lines 5–101: number formatting, a mnemonic table and an op-name parser;
* Main.lean lines 113–291: `loop`, the read-eval loop. Each input line first refreshes the host clock cell for `ct`.
  `/q /s /g /C` quit, step, go and reset; `?d ?c ?i ?R ?addr` print the stacks, the pointer, a register or memory;
  `:name ops…` assembles the rest of the line into memory at "here" (a separate small assembler, not B4.Asm);
  a label or `^R` calls code by pushing 0 as the return address and running until `rt` to 0 clears the run flag;
  a bare op runs once; a hex number is pushed;
* Main.lean lines 293–298: `main` makes the initial state and starts the loop.

Commit 344ccce reports that all 52 b4-tests pass. The tests weren't run for this site.
