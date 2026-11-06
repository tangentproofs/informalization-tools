# Proof sites: guide

**Status:** draft v0.1, 2026-10-22. The rules live in [`CONVENTIONS.md`](CONVENTIONS.md); the agent procedure
in [`SKILL.md`](../skill/proof-site/SKILL.md). This document is the why, the architecture, the workflow, and the plan for making
proof sites a reusable product rather than four hand-maintained copies.

> In this repo, the worked example to start from is [`examples/rakesieve/`](../examples/rakesieve/) (live: [RakeSieve, explained](https://tangentproofs.github.io/rakesieve/learn/)), built with `engine/build.sh`; see the README.

## 1. What a proof site is for

Formalization usually runs English → Lean and is done when Lean accepts the proof. A tangentproofs proof site
(an *informalization*) runs the other way: the Lean proof is finished and checks, and the job is done when a
**reader** accepts it, when they can say what each formal statement means and, if they like, back that up with a quiz.

So the site's unit is one Lean declaration (a **node**), and its central claim is narrow and checkable:
*this English says what that Lean says*. Everything follows from that:

- The Lean is the ground truth. It's extracted from the compiled build, never retyped.
- The English sits **next to** the Lean so a reader can compare them line by line.
- Understanding is earned bottom-up: a node counts as understood only when everything its *statement* mentions is
  understood, just as Lean won't accept a statement whose ingredients it doesn't know. Proofs don't count toward
  reading a statement.
- The first thing a reader needs is the **statement** of the headline theorem and only the definitions it uses
  (the *Start here* page). Proof internals come later.
- Signing off is quick and self-reported; the quiz is a bonus that shows up as stars.
- The site is honest about what is proved, what is conditional, and what was trusted.

Instances today (canonical first):

| Site | Repo | Proof | Folder |
|---|---|---|---|
| [star-height](https://tangentproofs.github.io/star-height/) | tangentproofs/star-height | OpenAI, generalized star height ≤ 3 (~12k lines) | `site/` |
| [fourcolor-lean](https://tangentproofs.github.io/fourcolor-lean/) | tangentproofs/fourcolor-lean | Chris Emery's Lean 4CT (vendored `4ct/`) | `site/` |
| [turyn](https://tangentproofs.github.io/turyn/) | tangentproofs/turyn | TT(n) ⇒ Hadamard, 6 headlines, some `native_decide` | `site/` |
| [eulers-gem /learn/](https://tangentproofs.github.io/eulers-gem/learn/) | tangentproofs/eulers-gem | Euler's formula + Platonic solids (some CONDITIONAL) | `learn/` + `/docs/` source |

## 2. Architecture

```
            ┌──────────── needs Lean (run locally, commit outputs) ────────────┐
 Lean repo ─┤ lake build ─▶ ExtractDecls.lean ─▶ data/decls.raw.json           │
            │            └▶ .ilean ─▶ build_xref.py ─▶ data/xref.json           │
            └───────────────────────────────────────────────────────────────────┘
                     ┌────────────── pure Node/Python (CI) ───────────────┐
 decls.raw.json ─▶ build_decls.py ─▶ decls.json (CI fails if stale)       │
 nodes/*.md ─────▶ build_site.mjs --check (schema + decls + quiz keys)    │
                   build_site.mjs ─▶ dist/{index.html, assets/, data/nodes.json,
                                          needs-explainer.json, informal-map.json, src/}
                     └──────────────────────────────▶ GitHub Pages (workflow) ┘
 browser: app.js (router, pages) + progress.js (localStorage) + widgets + giscus
```

Design choices worth keeping:

- **Static and serverless.** One `index.html`, a hash router, JSON data. Progress is in localStorage with
  Export/Import. Discussion is giscus on the repo's Discussions, so there's no backend to run.
- **CI never builds Lean.** Lean outputs (`decls.raw.json`, `xref.json`) are committed; CI only re-derives
  `decls.json` and fails if the committed copy is stale. That keeps deploys to about a minute even when the proof
  takes an hour and 5 GB to check.
- **Exact name resolution.** Dependency edges come from the elaborated environment (`ExtractDecls.lean`), and source
  cross-references from `.ilean` files, not regex. Regex is a fallback, and misses fall through to the Mathlib docs.
- **Pure widget logic.** Each widget's maths is a pure module tested in `test_widgets.mjs` against the Lean definition
  it mirrors. The DOM layer is thin.
- **Agent-first contribution.** Each stub page carries a ready agent prompt; `data/needs-explainer.json` is the work
  list, nearest to the main headline first; the schema check is the gate.

## 3. Reader model

Three independent facts per node: *viewed*, *signed* (ticked the understanding box), *quiz passed* (each question
answered right at least once, stars sticky). Shown as three greens, lightest to darkest: signed, quiz, both. A
dashed purple ring means "you ticked this but something it mentions isn't understood yet". Progress bars count
*understood* nodes (signed + all mentions understood). Quiz-only lights a node but doesn't move a bar, because the quiz
is a bonus and self-assessment is what we count. See CONVENTIONS.md §8 for storage and the migration rules.

## 4. Workflow

### 4.1 New site

1. Pick the repo (the proof's own repo under tangentproofs; vendor upstream code as a subfolder if needed, with credit and licence).
2. Scaffold `site/` from star-height (or, once it exists, the kit; §7). Fill `site.config.json` (or the constants block).
3. Adapt `ExtractDecls.lean` (`projPrefix`, root import) and `build_decls.py` (`NS`). Run the Lean steps **on a machine
   that can build the proof** (not on small/shared hosts). Commit the raw outputs.
4. Write explainers: headlines first, then the statement set (Start here), then outward by `depth`.
5. Honesty pass (§5) and Trust page.
6. Widgets for the ideas that are hard to read cold, with tests.
7. `og.png` 1200×630, meta tags, CI workflow, Pages `build_type=workflow`, giscus.
8. Register on the hub (§6). The repo owner's OK before any push (§8).

### 4.2 Updating a site when the Lean changes

Rebuild Lean → re-extract → `build_decls.py` → `npm test`. Nodes whose `id` vanished fail validation; nodes whose
statement changed need re-reading (diff `decls.json` statements and set those nodes back to `review: draft`).
Re-run the honesty audit for any headline whose statement changed.

### 4.3 Changing the shared layout (rollouts)

Prototype on **star-height** first, on a branch, with screenshots to the owner; push only on their OK; then roll out to the
other sites, one commit per site, carrying the shared files byte-for-byte and listing site-specific deltas. CONVENTIONS.md §14
is the rollout worklist.

## 5. Honesty and audit rules

These carry the site's credibility and are non-negotiable (CONVENTIONS.md §13 has the checklist form):

- **Independent statement audit.** For each headline, a second model (Claude) compares the Lean statement against the
  classical claim it's named for and the paper's statement: hypotheses, quantifiers, edge cases (empty alphabet,
  n = 0, degenerate polytopes), whether a hypothesis does the hard part. The audit is committed next to the proof
  (`*_CLAUDE_AUDIT.md`, e.g. eulers-gem `lean/PLATONIC_CLAUDE_AUDIT.md`), and fixes are applied before publishing.
- **No smuggling.** A theorem whose hypotheses imply or contain the result doesn't get the classical name.
- **CONDITIONAL label.** Results resting on unproved hypotheses say so in the title and summary, name each gap, and
  keep the gaps in a library the main build doesn't import.
- **Axioms.** `#print axioms` for every headline on the Trust page. `native_decide` (`Lean.ofReduceBool`) is disclosed,
  with what it was used for and why (turyn's Trust page is the model).
- **Trust page.** What was checked, where and on which build; what's vendored or not re-checked; declarations read
  from source rather than from the build.
- **Explanations are drafts** until a human checks them against the Lean, and the footer says the Lean is the ground truth.

## 6. The hub index (tangentproofs/tangentproofs.github.io)

<https://tangentproofs.github.io/> is plain static HTML from `main` (legacy Pages build, `.nojekyll`), regenerated by
`tools/update.mjs` from `gh repo list` plus each site's Open Graph tags. To feature a proof site:

1. Add the repo name to `informalization` in `tools/overrides.json` (and `sites` / `siteLabel` if it has more than one site,
   as eulers-gem does).
2. `node tools/update.mjs` (needs an authenticated `gh`), check `repos.json` and `index.html`, commit both.
3. A card image shows only if `og:image` returns 200. Bump `?v=N` when the card changes.


## 7. Proposal: a shared kit (`tangentproofs/proof-site-kit`)

**Proposal only; the repo doesn't exist.** Today each site carries copies of the same engine, and they have already
drifted: `progress.js` differs by 27 lines between star-height and the others (the stars API), the status bar,
side-by-side layout, `statement.js` and `leanlines.js` exist only on star-height, and the walkthrough toggle
survives on three sites. Every layout change becomes four hand-ports.

Proposed split:

| In the kit (versioned, identical everywhere) | In each site (instance) |
|---|---|
| `assets/progress.js`, `statement.js`, `leanlines.js`, `lean.js`, `dom.js`, `walkthrough.js` | `site.config.json` |
| `assets/app.js` shell: router, graph, node, list, start, about/trust frames, status bar, quiz, giscus, agent prompt, all driven by config | `nodes/*.md`, `data/*.json` |
| `assets/proof-site.css` (tokens + layout) | `assets/site.css` (site extras), `og.png` |
| `tools/build_site.mjs`, `build_decls.py` (namespace from config), `build_xref.py`, source renderer, `ExtractDecls.lean` template | `assets/widgets-interactive.js` + pure logic modules + their tests |
| `schema/node.schema.json`, `site-config.schema.json` | narrowed widget enum; About/Trust prose (Markdown) |
| tests: `test_progress`, `test_statement`, `test_leanlines`, `test_app` (generic parts), `check_conformance.mjs` | `test_widgets.mjs` |
| `workflows/site.yml` reusable workflow (`workflow_call`) | 5-line caller workflow |

Consumption options, simplest first:

1. **Vendored copy + hash check** (recommended to start): `site/kit/` copied at a tagged version; `check_conformance.mjs`
   fails CI if any kit file differs from the tagged hashes. No tooling change, works offline, easy to diff.
2. **npm package from GitHub** (`"proof-site-kit": "github:tangentproofs/proof-site-kit#v1.2.0"`) with a build step
   that copies assets into `dist/`. Cleaner upgrades, one more moving part.
3. **Git submodule.** Pinned by commit; awkward for contributors, not recommended.

Also: a hub-side scheduled job that runs `check_conformance.mjs` against every `informalization` repo and shows a
conformance badge on the index. Migration order: extract from star-height (canonical) → star-height consumes the kit
with zero visual change → turyn, fourcolor-lean, eulers-gem one at a time, closing the CONVENTIONS.md §14 gaps.

## 8. Operating rules (for people and agents)

- **Never push to the owner's repos without their explicit OK** for that push. Work on a branch, commit locally, show
  screenshots or a diff, and wait. Run `git remote -v` before any push to confirm the target.
- Prototype on star-height; don't roll a layout out to the other sites until the owner is happy with it.
- No heavy Lean builds on small shared hosts; use a build machine or CI. Commit Lean-derived JSON instead of
  making CI build Lean.
- Don't modify a worktree another worker is using; use a separate worktree or read via `git show`.
- Clean up temporary files, screenshots and scratch worktrees when done.
- After a deploy, check the live URL (hard refresh / cache-busted fetch) before saying it's live.

## 9. Open decisions

- Side-by-side **proof** view: which mock-up (CONVENTIONS.md §6.4). Decided: both, with a toggle (see CONVENTIONS.md §6.4).
- Checkbox label: "I think I understand this" (current) vs a short "Understood".
- Rendered source location for star-height (`src/` proposed) and whether eulers-gem moves from `/docs/` to match.
- Whether progress bars should also count quiz-only nodes (currently: no).
- Kit adoption (§7): vendored vs npm.
