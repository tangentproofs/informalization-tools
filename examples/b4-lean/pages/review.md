# Review: what is proved, what is tested, what is only claimed

Nothing below was checked by building Lean. It all comes from reading the source at the pinned commit.

The b4 Lean code is a working implementation with a verification layer that is a few weeks old. The author's
commit messages and docstrings are careful about what is and isn't proved, and this review found no claim of a
proof that isn't there. The main points:

* **The theory is about the real interpreter.** B4.Theory imports B4.Basic and every step lemma is about the same
  `step` / `runOp` that the shell runs. No separate model needs connecting.
* **Everything proved is about a single step**, or about the list model of the heap. There are no multi-step or
  whole-program theorems yet, and nothing about the swarm beyond unfolding lemmas.
* **The two models (swarm semantics and heap model) are connected to code only by tests**, and the author says
  so for the heap.

## Status table

PROVEN = a complete-looking Lean proof in the file (not built here). TESTED = checked only by an `#eval`,
example or external acceptance test. UNPROVEN = stated in a docstring or commit message, or implied by a name,
but not proved.

| Claim | Where | Status |
|---|---|---|
| A written cell reads back; disjoint cells don't interfere | B4/Theory.lean lines 55–78 | PROVEN (needs `bv_decide`, see Trust) |
| Writing one register leaves the others, the stacks and high memory alone | B4/Theory.lean lines 137–369 | PROVEN |
| Push/pop append to/remove from the stack lists, keep `WF` | B4/Theory.lean lines 414–488 | PROVEN |
| `runN` is total | B4/Theory.lean lines 493–495 | PROVEN (structural recursion) |
| `runN (n+1) = runN n ∘ step` when running | B4/Theory.lean lines 500–502 | PROVEN |
| `runN` agrees with `run` for enough fuel | — | UNPROVEN (not stated; `run` is partial) |
| Step lemmas: ad sb ml an or xr eq lt (via `step_binop'`), li, nt, ri, wi, jm, h0, hl, @T, !T, dc, cd, cl, rt | B4/Theory.lean lines 580–1060 | PROVEN |
| Step lemmas for dv md sh du sw ov zp rb wb lb rs ls hp nx io db, ^R, +R, other @R/!R, the float/rn/ct ops | — | not stated |
| Every instruction preserves `WF`; the initial state is `WF` | — | not stated |
| Any multi-step program behaviour | — | not stated |
| Swarm `Steps` composes; `stepAt` unfolds case by case | B4/Swarm.lean lines 165–207 | PROVEN |
| With one owner per channel, machine order doesn't matter | B4/Swarm.lean lines 39–40 | UNPROVEN (docstring) |
| `k` behaves like Hehner's √c | B4/Swarm.lean lines 15–19 | UNPROVEN (design claim) |
| `settle`'s 0 answer is correct ("no message can come in time") | B4/Swarm.lean lines 128–130 | UNPROVEN (docstring; see below) |
| Sender/receiver demo: receiver gets 2 at clock 1 | B4/Swarm.lean lines 221–233 | TESTED (`#eval`, expected value in a comment) |
| Heap `alloc` terminates | B4/Heap.lean lines 32–62 | PROVEN |
| `alloc_scale`: scaling all units by k > 0 commutes with allocation | B4/Heap.lean lines 74–130 | PROVEN |
| `alloc_cells`: byte model (12, 16) = cell model (3, 4) × 4 | B4/MM.lean lines 101–104 | PROVEN |
| The heap model is a correct allocator (sizes, no overlap, conservation) | — | not stated |
| b4a `mm` code implements `MM.alloc` / `MM.free` | B4/MM.lean lines 19–21; examples/MMTest.lean | TESTED (2,000 seeded random ops; the author says "proving it is still to do") |
| `Asm.assemble` reads b4a as `ub4asm.pas` does | B4/Asm.lean lines 6–7 | UNPROVEN (examples only) |
| The `rn` op equals the b4a `rnd` routine | examples/Inline.lean | TESTED (`#eval`, comment) |
| `mix32` is a bijection | B4/Basic.lean lines 204–205 | UNPROVEN (docstring; true of MurmurHash3's finalizer) |
| The interpreter passes the shared b4 acceptance suite | commit 344ccce | TESTED (outside imp/lean, not run here) |

## Headline by headline

### runOp (B4/Basic.lean): CODE, TESTED

A straightforward interpreter. No claims attached beyond the acceptance tests. One oddity: the shell's mnemonic
table names byte 0xBE `tm`, but `runOp` has no case for it.

### step_binop and the step lemmas (B4/Theory.lean): PROVEN, faithful

The statements say exactly what each instruction does, with realistic side conditions: a well-formed state, code
above the register area, enough items, enough room, targets inside memory. The conclusions include a frame
(`Same` / `Frame`), so they are strong enough to compose. Two limits. They never mention programs that run from,
or write into, the register area. And the coverage is partial (see the table).

### runN (B4/Theory.lean): PROVEN, but only its unfolding

The name and docstring ("`run`, with fuel: at most `n` steps") are accurate. What the module doc presents it as,
"a total, fuelled `runN` beside the partial `run`", is a foundation: no theorem yet uses it to prove anything
about a run.

### Swarm.settle (B4/Swarm.lean): DEFINED, soundness UNPROVEN

The docstring's argument: when nothing can move, the earliest waiting check can't receive a message stamped
before its clock. That holds if every machine's clock is non-decreasing, because then any machine that later sends
does so at a clock at least as late as the checker's. But a b4 program can lower its own clock: `!T` stores any
value ([step_wrT](#/node/step_wrT)), and `wi` can write byte 80. So the rule is sound for well-behaved programs,
and a theorem would need that as a hypothesis. This is this site's reading. The author makes no claim that
settle is proved.

### Heap.alloc_scale (B4/Heap.lean): PROVEN, faithful, relative

The statement is exactly the docstring ("counted in units k times smaller, the heap does the same"), with the
necessary k > 0. It is a relation between two instances of the same model, not a correctness property of the
allocator.

### MM.code (B4/MM.lean): TESTED

Honestly labelled by its author. The test is a good one: it compares the whole heap layout after every operation,
not just return values. But it is a single seeded run of 2,000 operations with requests under 200 bytes, and it is
an `#eval` that would not fail the build if it printed a non-zero count.

## Anything surprising

* The swarm's channels are **broadcast logs**: each machine has its own read cursor, so every reader sees every
  message. The docstrings say "receive the next message", which is true per reader. Readers used to queue
  semantics might assume otherwise.
* `Heap.free` doesn't merge neighbours. Merging happens lazily during `alloc`, so an `alloc` that fails can still
  change the heap (it merges what it passed over). The docstring says so (B4/Heap.lean lines 45–47).
