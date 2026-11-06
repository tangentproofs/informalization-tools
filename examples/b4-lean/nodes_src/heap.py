NODES = []
def node(id, title, summary, body, quiz, caveats=(), widgets=None):
    NODES.append(dict(id=id, title=title, summary=summary, body=body, quiz=quiz, caveats=list(caveats), widgets=widgets))
def q(text, choices, answer, explain):
    return {"q": text, "type": "choice", "choices": choices, "answer": answer, "explain": explain}
def walk(title, steps):
    return [{"type": "walkthrough", "title": title, "config": {"steps": steps}}]

node("Heap.Blk",
 "Blocks: the heap as a list",
 "The allocator's model sees the heap as a list of blocks, each recorded only as the size of its data and whether it is used. Headers are implicit: each block costs h extra units in front of its data.",
 r"""## Plain English

**Structure (`Heap.Blk`, B4/Heap.lean lines 20–25).** A block is a data size (a natural number) and a used flag.

The model is in B4/Heap.lean, which imports nothing, not even B4.Basic. It is pure list code, independent of the
machine. The block at position *k* starts at offset Σ (*h* + size) over the blocks before it, where *h* is the
header size. The real allocator keeps a 12-byte header in memory (next pointer, size, used flag), and
[`MM.blocks`](#/node/MM.code) reads such a heap back into this list form.

`Blk.scale k` (line 72) multiplies the size by *k*: the same block counted in units *k* times smaller.
""",
 [q("What does a `Blk` record?",
    ["Its data size and whether it is used", "Its address, size and next pointer", "Only its size"], 0,
    "B4/Heap.lean lines 20–24."),
  q("Does B4.Heap depend on the b4 machine?",
    ["No, it imports nothing; it is a pure list model", "Yes, it reads machine memory"], 0, "B4/Heap.lean has no imports."),
  q("Where do header sizes enter the model?",
    ["As the parameter h added per block when computing offsets and merging", "As a field of Blk"], 0,
    "`absorb` (line 29) and `alloc` (line 53)."),
 ])

node("Heap.alloc",
 "First-fit allocation with merging and splitting, on lists",
 "Status: DEFINED, termination PROVEN. `alloc h sp n` walks the blocks first-fit. At each free block it absorbs the free blocks right after it, takes the result if it is big enough and splits off the rest if at least sp would remain. It returns the offset (or none) and the merged list.",
 r"""## Plain English

**Definition (`Heap.absorb`, B4/Heap.lean lines 28–30).** Starting from a free block of size *s*, swallow each
following free block, adding its size plus one header *h*, and stop at the first used block.

**Definition (`Heap.claim`, lines 42–43).** To take *n* units out of a free block of size *s*: if *n* + *sp* ≤ *s*,
the result is a used block of *n* followed by a free block of *s* − *n* − *h*. Otherwise the whole block becomes
used.

**Definition (`Heap.alloc`, lines 48–62).**
* empty list: no block found;
* a used block: keep it and search the rest, adding *h* + its size to any offset found;
* a free block: absorb its free neighbours. If the merged size is at least *n*, claim it at offset 0. Otherwise keep
  the merged free block and search what follows.

The recursion is on a list that `absorb` may have shortened, so Lean needs a termination proof. `absorb_length`
(lines 32–38) shows absorbing never makes the list longer, and the `termination_by` / `decreasing_by` clause
(lines 61–62) uses it.

**Definition (`Heap.free`, lines 65–67).** Mark the block at offset *o* unused. Freeing does **not** merge. Merging
happens lazily, during later allocations.

### Not stated

There are no correctness lemmas about the model itself: nothing says the returned block is at least *n* big,
that total size (data + headers) is preserved, that a free followed by an alloc can reuse space, or that `alloc`
returns `none` only when no merged free run is big enough. The only theorems about `alloc` are the
[scaling theorem](#/node/Heap.alloc_scale) and its instance.
""",
 [q("When does `claim` split a block?",
    ["When at least sp units would be left over after taking n", "Always", "Never"], 0, "B4/Heap.lean line 43."),
  q("Does `free` merge neighbouring free blocks?",
    ["No. Merging happens during later `alloc` searches", "Yes, immediately"], 0, "B4/Heap.lean lines 65–67."),
  q("If no block is big enough, is the list returned unchanged?",
    ["Not necessarily: free runs the search passed over have been merged", "Yes, always"], 0,
    "Docstring, B4/Heap.lean lines 45–47, and line 60."),
  q("Why does `alloc` need an explicit termination proof?",
    ["It recurses on the list left after `absorb`, not on the plain tail", "It is partial", "Because of the split"], 0,
    "B4/Heap.lean lines 59–62, using `absorb_length`."),
 ],
 caveats=["Status: DEFINED, and termination PROVEN (absorb_length). No functional-correctness property of the model is stated."])

node("Heap.alloc_scale",
 "Headline: one heap model, any unit (`alloc_scale`)",
 "Status: PROVEN (not built). Multiply every block size, the header, the split threshold and the request by the same k > 0, and allocation picks the same block, at k times the offset, with the result scaled by k. So one model serves both the byte-counted and the cell-counted allocator.",
 r"""## Plain English

**Theorem (`Heap.alloc_scale`, B4/Heap.lean lines 100–130).** For every *k* > 0, header *h*, split threshold *sp*,
request *n* and block list *bs*: allocating *k n* with header *k h* and threshold *k sp* in the list with every
size multiplied by *k* gives

* the original offset multiplied by *k* (or none, if the original found none), and
* the original resulting list with every size multiplied by *k*.

It rests on two smaller facts, both proved:
* `absorb_scale` (lines 74–83): merging commutes with scaling;
* `claim_scale` (lines 85–95): splitting commutes with scaling. This needs *k* > 0, because the split test
  *n* + *sp* ≤ *s* must hold before scaling exactly when it holds after, and dividing by *k* needs *k* ≠ 0.

### Why it matters here

The module doc (lines 10–14) says the model is stated once and used twice: the b4a allocator
[mm](#/node/MM.code) counts **bytes** with a 12-byte header and a 16-byte split threshold, and a version of the
allocator in Hehner's language counts **cells** of 4 bytes with a 3-cell header and a 4-cell threshold. Since
12 = 4 · 3 and 16 = 4 · 4, `alloc_scale` with *k* = 4 says the two agree on heaps whose byte sizes are multiples of 4.
That instance is [`MM.alloc_cells`](#/node/MM.alloc_cells).

### What it does not say

It is a *relative* statement: it says two instances of the model agree, not that either one is a good allocator,
and not that the b4a code implements the model. The cell-counted allocator in Hehner's language is not in
`imp/lean`, and nothing here connects it to this model.
""",
 [q("Which quantities are multiplied by k in `alloc_scale`?",
    ["Header, split threshold, request and every block size", "Only the request", "Only block sizes"], 0,
    "B4/Heap.lean lines 100–102."),
  q("Why is k > 0 required?",
    ["To divide the split test back down, which fails for k = 0 (everything becomes 0)", "For termination", "It isn't"], 0,
    "`claim_scale`, B4/Heap.lean lines 85 and 94."),
  q("Does `alloc_scale` show that the b4a code is correct?",
    ["No. It relates two instances of the list model to each other", "Yes"], 0,
    "The b4a code is related to the model only by a random test (B4/MM.lean lines 19–21)."),
  q("What happens to the returned offset?",
    ["It is multiplied by k", "It is unchanged", "It is divided by k"], 0, "B4/Heap.lean line 102."),
 ],
 caveats=["Status: PROVEN (not built). No sorry, no extra axioms; the instance `MM.alloc_cells` uses `decide` only to check 0 < 4.",
          "Relative, not absolute: it doesn't state any allocator-correctness property."],
 widgets=walk("How alloc_scale is proved (B4/Heap.lean, lines 74-130)", [
  {"text": "`absorb_scale`: induction on the list. A used block stops both sides the same way. A free block adds k·h + k·size = k·(h + size), by distributivity (lines 74–83).", "link": "Heap.alloc"},
  {"text": "`claim_scale`: the split test k·n + k·sp ≤ k·s holds exactly when n + sp ≤ s (cancel k > 0), and the leftover k·s − k·n − k·h is k·(s − n − h) (lines 85–95)."},
  {"text": "`alloc_scale`, used block: the induction hypothesis on the tail, and the offset shift k·h + k·size = k·(h + size) (lines 107–114)."},
  {"text": "Free block: rewrite the merged block with `absorb_scale`. The test k·n ≤ k·m is n ≤ m (lines 105–106, 115–121)."},
  {"text": "Big enough: `claim_scale` finishes (line 123). Not big enough: the induction hypothesis on the shorter list after absorbing, with the same offset shift (lines 124–128)."},
  {"text": "Termination: the same measure as `alloc`, the list length (lines 129–130)."},
 ]))

node("MM.alloc",
 "The byte model: Heap with header 12 and threshold 16",
 "Status: DEFINITION (an abbreviation). `MM.alloc` is `Heap.alloc 12 16`: the model of the b4a allocator, counting bytes, with 12-byte headers, and splitting only when at least 16 bytes would be left. `MM.absorb`, `MM.claim` and `MM.free` are the matching instances.",
 r"""## Plain English

**Abbreviations (B4/MM.lean lines 79–96).** `MM.Blk` is `Heap.Blk`. `MM.absorb` is `Heap.absorb 12`. `MM.claim`
is `Heap.claim 12 16`. [`MM.alloc`](#/node/Heap.alloc) is `Heap.alloc 12 16`. `MM.free` is `Heap.free 12`.

The numbers come from the b4a code's layout (module doc, lines 8–17): a block header is three 4-byte cells
(next, size, used), and `mm-claim` splits when size − n ≥ 16 (that is `lb 10 lt nt`, line 47).

Commit e582743 introduced this arrangement: before it, MM had its own copy of the list model. Now MM's byte model
is literally an instance of the general one, so `alloc_scale` applies to it directly.

`MM.round` (line 107) rounds a request up to a multiple of 4, as `mm-alloc` does on entry (line 60).
""",
 [q("Which instance of `Heap.alloc` is `MM.alloc`?",
    ["Header 12, split threshold 16", "Header 3, threshold 4", "Header 16, threshold 12"], 0, "B4/MM.lean line 93."),
  q("Why 12?",
    ["Three 4-byte header cells: next, size, used", "A cache line", "Arbitrary"], 0, "B4/MM.lean lines 8–10."),
  q("Is `MM.alloc` a separate definition that needed its own proofs?",
    ["No, it is an abbreviation for the general model", "Yes"], 0, "`abbrev`, B4/MM.lean line 93."),
 ])

node("MM.alloc_cells",
 "Bytes are four times cells (`alloc_cells`)",
 "Status: PROVEN (one line, from alloc_scale). The byte model on blocks four times the size does exactly what the cell model (header 3, threshold 4) does, with offsets four times larger.",
 r"""## Plain English

**Theorem (`MM.alloc_cells`, B4/MM.lean lines 101–104).** For any request *n* and block list *bs*: `MM.alloc`
of 4·*n* on *bs* with each size times 4 equals the cell model `Heap.alloc 3 4` of *n* on *bs*, with the
offset times 4 and the sizes times 4.

The proof is [`alloc_scale`](#/node/Heap.alloc_scale) with *k* = 4, plus `decide` to check 0 < 4.
For this to typecheck, Lean has to see the byte model's 12 and 16 as 4·3 and 4·4. These are closed numerals,
so they reduce by computation.

The docstring (lines 98–100) calls the cell model "the allocator of Hehner's language". That allocator isn't in
`imp/lean`. The theorem relates two instances of the list model, and so it carries over to real code only as far
as each code matches its model, which for the b4a code is [tested, not proved](#/node/MM.blocks).
""",
 [q("What is `alloc_cells` an instance of?",
    ["alloc_scale with k = 4", "A separate induction", "A test"], 0, "B4/MM.lean line 104."),
  q("Which header and threshold does the cell model use?",
    ["3 and 4", "12 and 16", "4 and 4"], 0, "B4/MM.lean line 102."),
  q("Does it apply to a request of 13 bytes?",
    ["Only to multiples of 4. `mm-alloc` rounds requests up to whole cells first", "Yes, to any size"], 0,
    "The left side allocates 4·n (line 102). `round`, line 107."),
 ],
 caveats=["Status: PROVEN (not built). It relates two models. The cell-counted allocator it is named for lives outside imp/lean and wasn't examined."])

node("MM.code",
 "Headline (code): mm, a first-fit allocator written in b4a",
 "Status: TESTED, not proved. `MM.code` is the first-fit allocator in b4 assembly (merging free neighbours as it searches, splitting big blocks), assembled at compile time by `b4a!`. The author's docstring says only a random test relates it to its list model, and a proof is still to do.",
 r"""## Plain English

**Definition (`MM.code`, B4/MM.lean lines 27–75).** A `b4a!` block (see [the macro](#/node/Asm.elabB4a)), so the
assembly text sits in the Lean file and is assembled into a `Program` when the file is compiled. Three cells hold
the allocator's variables (`mm-heap`, `mm-n`, `mm-p`, lines 28–30). Then:

* `mm-init (a size --)` makes one free block of *size* bytes at *a* (lines 32–36);
* `mm-merge` absorbs the free blocks after `mm-p`, in a `.w … .d … .o` while-loop (lines 38–44);
* `mm-claim` takes `mm-p` for `mm-n` bytes, splitting off a new free block when at least 16 bytes would remain
  (lines 46–57);
* `mm-alloc (n -- a)` rounds *n* up to a multiple of 4, walks the list from `mm-heap`, merges at each free block,
  claims the first one big enough and returns its data address (block + 12), or 0 if none is (lines 59–71);
* `mm-free (a --)` clears the used flag at *a* − 12 + 8 (lines 73–74).

Its model is [`MM.alloc`](#/node/MM.alloc) = `Heap.alloc 12 16`.

### How code and model are compared

`MM.blocks` (lines 112–117) walks the header chain in a machine's memory and returns the list of blocks.
`MM.boot` loads the code; `MM.call` (lines 123–128) pushes arguments and a 0 return address, jumps to a label and
runs with the partial `run`. The [random test](#/node/MM.blocks) in examples/MMTest.lean runs 2,000 random allocs and
frees on both and counts disagreements.

### Status, in the author's words

The module doc (lines 19–21), as revised in commit 7016a16: the two "are related only by a random test (the
machine and the model agree); proving it is still to do."
""",
 [q("How is `MM.code` related to its model `MM.alloc`?",
    ["Only by a random test. No proof yet", "By a refinement theorem", "Not at all"], 0, "B4/MM.lean lines 19–21."),
  q("When is the b4a source in `MM.code` assembled?",
    ["When the Lean file is compiled, by the `b4a!` macro", "When the CLI starts", "Never, it is interpreted as text"], 0,
    "B4/AsmSyntax.lean lines 30–37."),
  q("What address does `mm-alloc` return on success?",
    ["The block's address + 12, the start of its data", "The block's header address", "The size"], 0,
    "B4/MM.lean line 67 adds 12 (hex 0C) to the block address and returns."),
  q("Where does `mm-alloc` merge free blocks?",
    ["At each free block it passes during the search", "Only in mm-free", "Never"], 0,
    "`mm-merge` is called at each free block (B4/MM.lean lines 63–65)."),
 ],
 caveats=["Status: TESTED. The author states plainly that it isn't proved (B4/MM.lean lines 19–21; commit 7016a16). The test itself is an `#eval` whose 'expected' result is a comment, and it was not run for this site.",
          "To prove it you would need multi-step reasoning about `run`, which is partial. The proof would have to go through `runN`, for which no multi-step lemmas exist yet. See runN."],
 widgets=walk("How mm-alloc runs (B4/MM.lean, lines 59-71)", [
  {"text": "Round the request up to a multiple of 4 (add 3, AND with −4) and store it in mm-n (line 60).", "link": "MM.alloc"},
  {"text": "Start at the first block: p := mm-heap (line 61)."},
  {"text": "While p ≠ 0 (lines 62–70): if p's used flag is 0, call mm-merge to absorb the free blocks after it (lines 63–65).", "link": "Heap.alloc"},
  {"text": "If p's size is now ≥ n, call mm-claim (split if ≥ 16 bytes would remain, mark used) and return p + 12 (lines 66–67)."},
  {"text": "Otherwise p := next(p) (line 69)."},
  {"text": "End of list: return 0 (line 71). The model `Heap.alloc 12 16` makes the same choices on lists. That agreement is what the random test checks.", "link": "MM.blocks"},
 ]))

node("MM.blocks",
 "Reading the heap back, and the random test against the model",
 "Status: TESTED (an `#eval`, not run here). `MM.blocks` reads the header chain in machine memory back into a block list. A test runs 2,000 seeded random allocs and frees on the machine and on the model and counts disagreements. A comment says 0.",
 r"""## Plain English

**Definition (`MM.blocks`, B4/MM.lean lines 112–117).** Follow the header chain in a machine's memory from address
*a*: read each block's size (at +4) and used flag (at +8) into a [Blk](#/node/Heap.Blk), and move to the next
pointer (at +0) until it is 0 or the fuel runs out. `MM.call` (lines 123–128) runs a routine: push the arguments,
push 0 as the return address, jump to the label, `run`. `MM.clear` (line 131) empties the data stack.

**The test (`check`, examples/MMTest.lean lines 12–29).** It uses these to drive the machine. A
linear-congruential generator picks each operation.

* **free** (when the draw is divisible by 3 and something is live): pick a live address *a*, call `mm-free` on the
  machine, and `free` at offset *a* − 0x1000 − 12 on the model;
* **alloc** otherwise: *n* = a draw mod 200. Call `mm-alloc` on the machine, and `alloc (round n)` on the model.
  On success the machine's address must be 0x1000 + offset + 12; on failure it must be 0.

After each operation the machine's heap is read back with `MM.blocks` (`heap`, line 8: at most 1,000 blocks from
0x1000) and compared with the model's list.

Line 32 starts it from a 4,000-byte heap at 0x1000, and line 31 records the expected output: "0 disagreements in
2000 random operations".

### What this does and doesn't establish

It is good evidence that the b4a code and the model agree on this particular random sequence: one seed, one heap
size, requests under 200 bytes. It runs the real interpreter with the partial `run`. But it is an `#eval`, not a
`#guard`, so building the file succeeds whatever number comes out. It was not run for this site.
""",
 [q("What does `check` count?",
    ["Operations where machine and model disagree", "Successful allocations", "Bytes allocated"], 0,
    "Docstring, examples/MMTest.lean lines 10–11."),
  q("Would building the file fail if there were disagreements?",
    ["No. It is an `#eval` that prints a number; only the comment says 0", "Yes"], 0,
    "examples/MMTest.lean lines 31–32."),
  q("How many seeds and heap sizes does the test try?",
    ["One of each: seed 42 and a 4,000-byte heap", "Many"], 0, "examples/MMTest.lean line 32."),
 ],
 caveats=["Status: TESTED (not re-run here). A single seeded run is evidence, not proof."])
