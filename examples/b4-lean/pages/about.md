# About b4 and its Lean implementation

## What b4 is

**b4** is a tiny virtual machine with a Forth-like flavour, by Michal Wallace (repository
[tangentstorm/b4](https://github.com/tangentstorm/b4)). It has 64 KB of byte memory, a data stack and a control
stack of 32-bit cells, and 32 registers kept in memory. Its instruction set is about sixty one-byte ops with
two-letter names (`ad`, `du`, `cl`, `rt`, …). Programs are written in **b4a**, a small assembly language with
labels and structured if/while/for macros.

The README lists implementations in J, Free Pascal, Lil, JavaScript, C, Rust, Bend, GDScript and Lean. They are
kept compatible by shared acceptance test suites (`b4-tests.org` and others) that drive each implementation's
interactive shell.

## What this site covers

Only **`imp/lean/`**, about 2,900 lines of Lean 4. It does two jobs:

1. **A working implementation.** The interpreter ([runOp](#/node/runOp), [step](#/node/step)), the command-line
   shell in Main.lean (see the [Roadmap](#/roadmap)), a b4a assembler ([Asm.assemble](#/node/Asm.assemble)) and
   the [`b4a!`](#/node/Asm.elabB4a) macro, which assembles b4a written inside a Lean file when that file compiles.
2. **The beginnings of a verification effort**, all of it written in October 2026 (commits 2e6b72d–e582743):
   * B4.Theory: [step lemmas](#/node/step_binop) about the **real** interpreter and a total, fuelled
     [runN](#/node/runN);
   * B4.Swarm: several machines joined by timestamped channels, with a "check" instruction after Eric Hehner's √c and
     a [settle](#/node/Swarm.settle) rule for deadlocks. **Defined, mostly unproved**;
   * B4.Heap and B4.MM: a [heap-allocator model](#/node/Heap.alloc) on lists with a proved
     [scaling theorem](#/node/Heap.alloc_scale), and a [b4a allocator](#/node/MM.code) that is **tested against
     the model, not proved**.

The author's own docstrings say plainly what is proved and what isn't. This site follows them, and the
[Review](#/page/review) page classifies every claim as PROVEN, TESTED or UNPROVEN.

## Where to start

* For a reading order through the files, see the [Roadmap](#/roadmap).
* For the proofs, read [step_binop](#/node/step_binop), then [runN](#/node/runN), then
  [alloc_scale](#/node/Heap.alloc_scale).
* For the concurrency design, read [Swarm](#/node/Swarm), [check](#/node/Swarm.check) and
  [settle](#/node/Swarm.settle).

## What is left out

* The other implementations and the rest of the repository (bios, b4i, b4ix, the web and electron front-ends).
* The acceptance suites themselves, which live outside `imp/lean` and weren't run.
* The "allocator in Hehner's language" that the cell-counted heap instance is named after. It isn't in
  `imp/lean`.
* Main.lean, examples/Inline.lean and B4/DSL.lean get prose (Roadmap, assembler node) but no declaration
  nodes, because this site's source scanner confuses their names with the library's (see [Trust](#/page/trust)).
