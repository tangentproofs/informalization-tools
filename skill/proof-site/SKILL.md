---
name: proof-site
description: >-
  Build, update, or audit a proof ("informalization") site that reads a finished
  Lean 4 proof back into plain English: creating a new site for a Lean repo,
  adding/fixing explainer nodes, rolling a layout change across sites,
  re-extracting after Lean changes, or checking a site against the conventions.
---
# proof-site

The rules are in [`docs/CONVENTIONS.md`](../../docs/CONVENTIONS.md). The background is in [`docs/GUIDE.md`](../../docs/GUIDE.md). This file is the procedure. When this file and CONVENTIONS.md disagree, CONVENTIONS.md wins. The reference implementation is `tangentproofs/star-height` `site/`; copy from it rather than writing from scratch. For a hub-built site (this repo's `engine/`), the worked example is [`examples/rakesieve/`](../../examples/rakesieve/): build it first (README, "Try it") and copy its shape.

## Ground rules (always)

1. **Read before writing.** Open the reference site's code for whatever you're changing (`app.js`, `progress.js`, `build_site.mjs`, `style.css`). Don't describe or build features from memory.
2. **The Lean is the ground truth.** Statements come from the compiled build via `ExtractDecls.lean`; never retype them. English must match the Lean as written; looseness goes under `caveats`.
3. **No push without the owner's explicit OK** for that specific push. Branch, commit locally, show screenshots or a diff, wait. Run `git remote -v` before pushing.
4. **Prototype on the reference site first**, then roll out one site at a time.
5. **Don't build Lean on small shared hosts.** Build where the proof fits (some need >5 GB RAM) and commit the JSON outputs.
6. **Don't touch a worktree someone else is using.** Use `git worktree add` or `git show <ref>:<path>`.
7. **Shared files stay identical** across sites (`progress.js`, `statement.js`, `leanlines.js`, `lean.js`). Change them in one place and copy byte-for-byte; add a migration and test for any stored-progress change.
8. Clean up temp files, screenshots and scratch worktrees.

## A. Create a new proof site

1. **Scope.** Identify the repo, the Lean root module, the namespace prefix, and the **headline theorems** (main first). Note the proof's author, licence and any vendored code.
2. **Scaffold** `site/` by copying the reference site's `index.html`, `package.json`, `assets/{app,progress,statement,leanlines,lean,dom,widgets,walkthrough}.js`, `assets/style.css`, `schema/node.schema.json`, `tools/{ExtractDecls.lean,build_decls.py,build_xref.py,build_site.mjs,test_*.mjs}`, and `.github/workflows/site.yml`. Strip site-specific widgets and nodes.
3. **Configure.** Put every per-site value in one block (`site.config.json` once supported, else the constants at the top of `app.js`): `repo`, `branch`, `namespace`, `modulePrefix`, `headlines`, `mathlibGloss`, `progressKey` (new, never renamed later), `giscus` (enable Discussions, category **Announcements**), `labels.understand`, brand, credit. Set `NS` in `build_decls.py` and `projPrefix` + the root import in `ExtractDecls.lean`.
4. **Extract** (on a capable machine): `lake build`; `lake env lean site/tools/ExtractDecls.lean` → `data/decls.raw.json`; `python3 site/tools/build_xref.py` → `data/xref.json`; `python3 site/tools/build_decls.py` → `data/decls.json`. Commit all three. Sanity-check counts, `depth`, and that every headline is present.
5. **Explain, in this order:** (a) each headline; (b) the **statement set** (`#/start` lists it: the headlines' mentions, transitively, stopping at Mathlib), simplest first; (c) outward by `depth` using `data/needs-explainer.json`. Per node: `site/nodes/<id>.md` with front matter (`id`, `title`, `summary`, `review: draft`, `authors`, `caveats`, `quiz` of 3–6 questions with `answer` + `explain`, optional `widgets`) and a body with `## Plain English`. Link mentions as `#/node/<id>`. Write a gloss for each Mathlib name on the Start here page.
6. **Honesty pass.** For each headline: get an independent model audit of the Lean statement against the classical claim; commit it as `*_AUDIT.md`; apply fixes. Don't use a classical name if hypotheses smuggle the result; label conditional results **CONDITIONAL** and name each gap. Run `#print axioms` per headline and write the **Trust page** (`#/trust`), disclosing `native_decide`/`Lean.ofReduceBool`, `sorryAx`, vendored or unchecked parts, and `extracted: false` nodes.
7. **Widgets** only where a statement is hard to read cold. Pure logic module + `test_widgets.mjs` assertions keyed to the Lean definition. Mount under the plain English. Never present a widget as evidence. No step-through/show-all toggle on outlines.
8. **Source pages.** Render only this repo's Lean, with `L<n>` anchors, range highlight, project identifiers linked on-site, Mathlib identifiers linked to Mathlib docs, declaration badges back to nodes, a small "view on GitHub" link. Make every "file lines a–b" reference on the site link to `src/<file>.html#L<a>-L<b>`.
9. **Head and card.** All meta tags in CONVENTIONS.md §10; `assets/og.png` 1200×630 (render `tools/og.html` with headless Chrome `--window-size=1200,630`); add `?v=N` to image URLs when the card changes.
10. **CI.** `site.yml` triggers on `site/**`, the Lean dirs, and itself; runs `npm ci`, `npm test`, the `decls.json` staleness diff, `npm run build`, deploys `dist/`. Set Pages to workflow builds (`gh api -X POST repos/<repo>/pages -f build_type=workflow` with the owner's OK).
11. **Verify locally:** `cd site && npm ci && npm test && npm run serve`; open `http://localhost:8765/`, check graph, `#/start`, a headline node, a stub, mobile width (< 800px), and take screenshots.
12. **Ask for the OK**, then push and check the live URL with a hard refresh.
13. **Register on the hub:** add the repo to `informalization` in `tangentproofs.github.io/tools/overrides.json`, run `node tools/update.mjs`, commit `repos.json` + `index.html`, push with OK, confirm the card appears.

## B. Add or fix explainer nodes

1. Pick from `data/needs-explainer.json` (prefer nodes whose mentions are explained) or the node named in the request.
2. Read the declaration's Lean (`decls.json` `statement`, `file`, `line`–`endLine`) and every mention's explainer.
3. Write or edit `nodes/<id>.md`; keep `review: draft` unless a human reviewed it.
4. `npm run validate` (schema, id exists, quiz keys valid, `## Plain English` present), then `npm test`.

## C. After the Lean changed

1. Rebuild and re-extract (A.4). `npm test`: removed ids fail validation; fix or delete those nodes.
2. Diff the `statement` fields of the old and new `decls.json`; reset changed nodes to `review: draft` and re-read them.
3. Re-run the honesty audit and `#print axioms` for any changed headline; update the Trust page.

## D. Roll out a layout or engine change

1. Build it on the reference site on a branch; screenshots (desktop + < 800px); owner's OK; push.
2. For each other site: new branch; copy shared files byte-for-byte; port `app.js`/`style.css` changes, keeping site-specific pages and widgets; keep the stored-progress key; `npm test`; screenshots; OK; push; verify live.
3. Update the conformance table in CONVENTIONS.md §14.

## E. Conformance audit

Walk the checklist in CONVENTIONS.md §15 and report each item as pass/fail with the evidence (file + line, command output, or screenshot). List failures as migration items. Don't fix anything in an audit unless asked.

## Reporting

Report what changed (files, branch, commit), what was verified (tests, screenshots, live check), what still needs the owner's decision or OK, and any honesty issue found (smuggled hypotheses, undisclosed axioms, conditional results not labelled).
