# Review passes (after drafting, before the audit)

Run a few short passes, each a fresh session with one job, and re-run the build after each. These were used on
the larger sites (five passes on an 82-node site); small sites can merge them.

1. **Coverage.** Every headline and every declaration in the statement set (`#/start`) has a node; nothing in
   `data/needs-explainer.json` that a headline mentions is left unexplained. Each headline has a walkthrough
   whose title names the file and lines.
2. **Faithfulness.** For each node, reread the Lean at its lines and the node side by side. Fix anything the
   English states more strongly than the Lean; move looseness into `caveats`.
3. **Quizzes.** Each quiz tests the statement (what it says and does not say), the answer key is right, and
   each explanation cites lines.
4. **Links and line references.** Every "File.lean lines a–b" points at the lines it describes (the build
   fails on out-of-range references; `tools/srcrefs_lock.py --lock` then `--check` catches drift later), and
   every `#/node/<id>` link resolves.
5. **Plain words.** Short sentences, define terms on first use, lead with the takeaway, no hype. The summary
   is the single most important thing about the declaration.

Then run the independent honesty audit (`honesty-audit.md`) and apply its fixes.
