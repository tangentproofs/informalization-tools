NODES = []
def node(id, title, summary, body, quiz, caveats=(), widgets=None):
    NODES.append(dict(id=id, title=title, summary=summary, body=body, quiz=quiz, caveats=list(caveats), widgets=widgets))
def q(text, choices, answer, explain):
    return {"q": text, "type": "choice", "choices": choices, "answer": answer, "explain": explain}

node("Asm.assemble",
 "The b4a assembler",
 "Status: CODE, exercised only by examples. `Asm.assemble` turns b4a source into bytes at addresses plus a label table, following the Pascal assembler `ub4asm.pas`: ops, hex, labels, forward references, register ops, and the macros `.i .e .t`, `.w .d .o`, `.f .n`, which compile to hops.",
 r"""## Plain English

**Definition (`Asm.assemble`, B4/Asm.lean lines 264–273).** Three passes:

1. **Tokenize** (`tokenize`, lines 109–151): skip whitespace and `#` comments. Then classify each token: a hex
   byte (`1F`, `-5`), a 4-byte `$12345678`, a character `'c`, a string `"abc"` or a counted string `."abc"`, a macro
   `.i` and friends, `..` for a zero byte, a prefixed word (`:name`, `^R`, `` `name ``, `@name`, `!name`,
   `>name`, `+R`), or a bare word. It is a `partial def`, ordinary for a parser.
2. **Assemble each token** (`step`, lines 210–261) into a state (`St`, lines 154–161) holding the current address,
   the writes so far, the labels, the pending *fixups* (forward references to patch at the end) and a compile-time
   stack for the macros. A bare word is an op if it is one of the two-letter names (`opcode`, lines 37–50), and
   otherwise a call (`cl`) to that label. `@name` and `!name` become `li name ri` and `li name wi`. `:R` with a
   one-letter register name stores the current address into that register's cell.
3. **Patch fixups** (lines 268–272): every forward reference gets its label's address, or the assembly fails with
   "unknown word".

### The structured macros

`.i` (if) and `.d` (do) lay down an `h0` with an empty distance byte and remember where it is; `.t` (then) fills it
in with a hop to here; `.e` (else) adds an `hp` over the else-part. `.w` remembers the loop top; `.o` hops back to
it and fills the `.d`. `.f` lays down `dc` (push the count on the control stack) and `.n` lays down `nx` with a hop
back. Hops are one signed byte, so the assembler rejects distances over about 127 bytes (lines 193–205).

### What uses it

[`b4a!`](#/node/Asm.elabB4a) calls it at compile time; `Program.load` (lines 287–288) writes a program into a
machine; `Program.addr` (line 278) looks up a label. The allocator [MM.code](#/node/MM.code) and the examples in
examples/Inline.lean are written this way.

There is also an older, much simpler `assemble` in B4/Basic.lean (lines 429–451) that turns a list of `Op` values
into bytes. It goes with the `b4!` term syntax of B4/DSL.lean, a list-of-ops notation with no labels or macros,
shown in examples/DSLTest.lean. `B4.lean` doesn't import B4.DSL, so it isn't part of the library build.
""",
 [q("What does a bare word that isn't an op name assemble to?",
    ["A call (`cl`) to the label of that name", "An error", "A string"], 0, "B4/Asm.lean lines 259–261."),
  q("What does `.t` do?",
    ["Fills in the pending hop distance so the hop lands here", "Halts", "Starts a loop"], 0, "B4/Asm.lean lines 193–198 and 255."),
  q("Is there a proof that `Asm.assemble` agrees with `ub4asm.pas`?",
    ["No. It is a design claim checked only by examples", "Yes"], 0, "B4/Asm.lean lines 6–7. No theorem in the file."),
  q("What happens to a reference to a label defined later in the source?",
    ["A placeholder is written and patched at the end", "It is an error", "It becomes 0 forever"], 0,
    "`emitAddr` (lines 172–176) and the fixup pass (lines 268–272)."),
 ],
 caveats=["Status: CODE, with UNPROVEN fidelity to ub4asm.pas. It is exercised by examples/Inline.lean and, through MM.code, by the MMTest random test, both `#eval`s with expected output in comments. The CLI's 52 acceptance tests go through Main.lean's own assembler, not this one."])

node("Asm.elabB4a",
 "`b4a!`: assembly inline in a Lean file",
 "Status: CODE. `b4a! \"...\"` is a Lean term whose value is the assembled `Program`. The assembler runs while Lean elaborates the file, so a mistake in the assembly, such as an unknown word or an unbalanced `.i`, is reported as a Lean compile error at that spot.",
 r"""## Plain English

**Definition (`Asm.elabB4a`, B4/AsmSyntax.lean lines 30–37).** A term elaborator for the new syntax
`b4a!`, with an optional origin address before the string (line 28). It reads the string literal, runs
[Asm.assemble](#/node/Asm.assemble) on it, and on success turns the resulting `Program` into a Lean expression
with a `ToExpr` instance (lines 23–25). On failure it raises an error prefixed "b4a:", which Lean shows as an
ordinary error in the file.

So the bytes are computed once, at compile time, and the definition (for example [MM.code](#/node/MM.code)) is
just a literal list of (address, byte) pairs and labels. Nothing is parsed at run time.

**Examples (examples/Inline.lean).** `rnd` (lines 7–18) is the `rn` random-number op written in plain b4a.
`demo` (lines 21–26) uses `.i .e .t` for absolute value and `.w .d .o` for a triangular-number loop. `#eval`s
at lines 33–37 run them, with expected results in comments: the same two numbers as the `rn` op, `[5, 7]` and
`[55]`.

This is a clean example of Lean as a host for a small language: no proofs, but a compile-time check that
every assembly block in the library assembles.
""",
 [q("When is the assembly inside `b4a!` processed?",
    ["While Lean compiles the file", "Each time the program runs", "By the CLI"], 0,
    "B4/AsmSyntax.lean lines 4–17 (module doc) and 30–37."),
  q("What happens if a `b4a!` block calls an undefined label?",
    ["The Lean file fails to compile, with a 'b4a: unknown word' error", "It assembles a 0", "It is caught at run time"], 0,
    "B4/Asm.lean line 272 and B4/AsmSyntax.lean line 37."),
  q("Does `b4a!` check that the program is correct?",
    ["Only that it assembles, not what it computes", "Yes, it proves it"], 0,
    "It only runs `assemble` (B4/AsmSyntax.lean line 35)."),
 ],
 caveats=["Status: CODE. The `#eval` examples are TESTED only by comments stating their expected output."])
