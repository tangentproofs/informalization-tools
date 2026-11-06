# Proof-site conventions (the "style sheet")

**Status:** draft v0.1, 2026-10-22. Canonical reference implementation: **star-height `main` @ `06ce74a`**.
Normative words: **MUST** = required for conformance; **SHOULD** = default unless the site's
`site.config.json` or this document records a reason; **MAY** = optional. Anything marked
**PROPOSED** is not built yet and is waiting on a decision; don't build it as if it were settled.

This document defines what a tangentproofs *proof site* (an "informalization" site: a site that
reads a finished Lean proof back into plain English) is: its repository layout, data schemas, page
structure, visual tokens, link rules and honesty rules. It is written for **any** future site. The
four existing sites are instances of it. Where they differ from the rule, the gap is listed in §14
as a migration item.

Companion files in this folder:

| File | What it is |
|---|---|
| `GUIDE.md` | Why these sites exist, architecture, workflow, honesty/audit rules, rollout, and the proposed shared kit |
| `SKILL.md` | Step-by-step procedure an agent follows to create or update a site |
| `proof-site.css` | Theme tokens and the canonical layout CSS (copied from star-height) |
| `node.schema.json` | Generic schema for node front matter (sites narrow the widget enum) |
| `site-config.schema.json` | Schema for the per-site `site.config.json` (**PROPOSED**; today these values are constants in `app.js`) |

---

## 1. Vocabulary

| Term | Meaning |
|---|---|
| **declaration** | One Lean constant of the project (def, theorem, inductive, structure, instance…), extracted from the compiled build. |
| **node** | A declaration as shown on the site. A node is **explained** if `nodes/<id>.md` exists, otherwise it's a **stub**. |
| **id** | Declaration name with the site's namespace prefix stripped (`OAI.GeneralizedStarHeight.Expression.height` → `Expression.height`). |
| **headline** | A theorem the site exists to explain. Configured per site (`headlines`). The first one is the **main** headline. |
| **mentions** (`meaningDeps`) | Project declarations used in a declaration's *statement* (type), plus the *body* for defs/inductives, since the body is what a definition means. |
| **proof uses** (`proofDeps`) | Project declarations used only in a theorem's proof term. |
| **statement set** | The transitive closure of the headlines' **mentions** only, stopping at Mathlib (and at anything outside the project). Proof edges are never followed. Computed by `assets/statement.js` `statementSet()`. |
| **signed** | The reader ticked the understanding checkbox on a node. |
| **quiz passed** | The reader has answered every quiz question correctly at least once. |
| **understood** | Signed **and** every mention is understood, recursively. Quiz-only doesn't count. |
| **pending** | Signed but not understood (a mention isn't yet). |

## 2. Repository layout

A proof site lives **inside the repository of the Lean proof it explains**, in one folder: **`site/`**
(canonical). Use `learn/` only when `site/` is already taken by another Pages artefact (eulers-gem). The
site folder is self-contained: CI builds it with Node alone, no Lean toolchain.

```
<repo>/
  lean sources …                  # the proof (repo root, lean/, 4ct/, …)
  CONTRIBUTING.md                 # node format for humans and agents (MUST)
  .github/workflows/site.yml      # build + test + deploy (MUST; §12)
  site/
    index.html                    # shell: <head> meta (§10), header nav, <main id="app">, footer
    site.config.json              # PROPOSED: per-site settings (§3); today: constants at top of app.js
    package.json, package-lock.json
    nodes/<id>.md                 # one explainer per declaration (§4)
    schema/node.schema.json       # front-matter schema (site copy of ./node.schema.json, widget enum narrowed)
    data/decls.raw.json           # written by tools/ExtractDecls.lean (needs a Lean build; committed)
    data/decls.json               # written by tools/build_decls.py from decls.raw.json (committed; CI checks in sync)
    data/xref.json                # source cross-references from .ilean files (tools/build_xref.py; star-height, in progress)
    assets/
      app.js                      # router + pages (graph, node, list, start, about, trust, playground)
      progress.js                 # SHARED reader-progress model; MUST be byte-identical across sites
      statement.js                # SHARED statement-set computation
      leanlines.js                # SHARED wrapped-Lean line splitter
      lean.js                     # SHARED Lean highlighter + linkMap
      dom.js, widgets.js          # widget host + shared widget helpers
      widgets-interactive.js, <domain>.js   # site-specific widgets and their pure logic modules
      style.css                   # tokens + layout (§9; proof-site.css is the reference)
      og.png                      # 1200×630 preview card (§10)
    tools/
      ExtractDecls.lean           # Lean metaprogram: dump declarations + dependency edges
      build_decls.py              # post-process raw → decls.json (statement text, Mathlib mentions, reverse edges, depth)
      build_xref.py               # .ilean → data/xref.json (for source pages)
      build_site.mjs              # validate nodes, build dist/ (§11)
      og.html                     # MAY: source of og.png
      test_progress.mjs           # MUST
      test_widgets.mjs            # MUST if the site has widgets
      test_app.mjs                # SHOULD (quiz checking, progress import, source anchors; turyn has one)
      test_statement.mjs, test_leanlines.mjs   # MUST once statement.js / leanlines.js are present
    dist/                         # build output, git-ignored
```

Data pipeline (who runs what):

```
lake build  →  lake env lean site/tools/ExtractDecls.lean  →  data/decls.raw.json   (local, needs Lean; commit result)
            →  python3 site/tools/build_xref.py           →  data/xref.json       (local, needs .ilean; commit result)
python3 site/tools/build_decls.py  →  data/decls.json     (pure Python; CI re-runs and fails if the diff isn't empty)
node site/tools/build_site.mjs     →  dist/               (CI)
```

## 3. Site configuration (generalised settings)

Every per-site value MUST live in one place. **Canonical (PROPOSED):** `site/site.config.json`
validated by `site-config.schema.json`, read by `app.js`, `build_decls.py` and `build_site.mjs`.
**Today:** the same values are constants at the top of `app.js` (and `NS` in `build_decls.py`,
`projPrefix` in `ExtractDecls.lean`). Until the config file lands, keep the constants together at the top of
those files with the same names:

| Key | star-height today | Meaning |
|---|---|---|
| `repo` | `REPO = "tangentproofs/star-height"` | GitHub `owner/name`; drives edit links, GitHub blob links, agent prompt |
| `branch` | `main` (in `BLOB`) | Branch the site links to |
| `namespace` | `NS = "OAI.GeneralizedStarHeight."` | Prefix stripped to form ids |
| `modulePrefix` | `projPrefix = OAI.Computability.StarHeight` | Which modules count as "the project" |
| `headlines` | `HEADLINES = ["main"]` | Headline theorem ids, main first (turyn has 6) |
| `mathlibGloss` | `MATHLIB_GLOSS = {…}` | One-line gloss per Mathlib notion in the statement set (Start here page) |
| `progressKey` | `KEY = "star-height-progress-v1"` | localStorage key. **Never rename** (§8) |
| `giscus` | `GISCUS = {repo, repoId, category: "Announcements", categoryId}` | Discussion settings |
| `labels.understand` | `"I think I understand this"` | Checkbox label (§6.2) |
| `sourceBase` | PROPOSED `"src/"` | Where rendered Lean source pages live, relative to the site root (§7) |
| `brand` | header HTML in `index.html` | Short name + emphasised fragment, e.g. `star-height <span>≤ 3</span> <em>informalized</em>` |
| `credit` | footer in `index.html` | Who proved it, licence, "explanations are community-written, the Lean is the ground truth" |

## 4. Node files: `site/nodes/<id>.md`

One Markdown file per explained declaration: YAML front matter between `---` lines, then a body.
Schema: `node.schema.json` in this folder (sites copy it to `site/schema/` and narrow `widgets[].type`
to the widgets they implement). `build_site.mjs --check` MUST enforce all of this:

- `id` equals the file name without `.md`, and exists in `data/decls.json`.
- Required: `id`, `title` (3–80 chars), `summary` (one sentence, 10–300 chars, inline Markdown),
  `review` (`draft` | `human-reviewed`), `authors` (≥1), `quiz` (3–6 questions).
- Optional: `caveats` (faithfulness notes, list of inline Markdown), `widgets` (`{type, title?, config?}`).
- Body MUST contain a `## Plain English` heading. Further `##` sections (e.g. `## Why it matters`,
  `## Proof idea`) are allowed.
- Quiz items: `{q, type, choices?, answer, explain}`; `type ∈ choice | number | text`.
  `choice` → `answer` is a 0-based index into `choices`; `number` → numeric `answer`;
  `text` → list of accepted strings (compared case-, whitespace- and quote-insensitively).
  `explain` (≥10 chars) says *why*, pointing at the Lean.
- `review: human-reviewed` only after a person checked the text and the quiz key against the Lean.
- A node whose mentions have no explainer is a **warning**, not an error (stubs may land first).

Writing rules for the body: faithful to the Lean *as written* (hypotheses, quantifier order, which side is
complemented, ∃ vs ∀, universes when they matter). Don't import claims from the paper that the Lean
doesn't state. Link mentioned declarations by id (`[Expression.height](#/node/Expression.height)`).
Put every place the English is looser than the Lean under `caveats`.

## 5. Declaration data: `data/decls.json`

Array of objects, one per project declaration (star-height: 1060). Fields (all MUST):

| Field | Type | Notes |
|---|---|---|
| `id`, `name` | string | short id; fully qualified name |
| `kind` | `def`, `theorem`, `inductive`, `structure`, `instance`, … | |
| `file`, `module` | string | repo-relative path; module short name (graph "Files" view) |
| `line`, `endLine` | int | 1-based source range of the declaration |
| `statement` | string | verbatim source text up to the top-level `:=` (theorems), whole text for short defs |
| `truncated` | bool | statement was cut (shows `:= … (proof omitted)`) |
| `variables` | string[] | `variable` lines in scope |
| `mathlib` | string[] | Mathlib names mentioned (boring core names filtered) |
| `meaningDeps`, `proofDeps`, `usedBy` | id[] | mentions, proof-only uses, reverse edges |
| `depth` | int \| null | distance from the main headline over all edges; `null` = not used by it |
| `docs` | string | MAY: relative URL of the declaration in the rendered source (eulers-gem) |
| `extracted` | bool | MAY: `false` if read from source rather than the compiled build (fourcolor, turyn); MUST be disclosed on the node page |

## 6. Pages and their structure

Hash router, single `index.html`. Canonical routes:

| Route | Page | Status |
|---|---|---|
| `#/` | Proof graph + side panel | MUST |
| `#/start` | **Start here: what the theorem says** | MUST |
| `#/node/<id>` | Node page | MUST |
| `#/nodes[?file=M]` | All declarations table | MUST |
| `#/about` | How "understood" works, contributing, credit | MUST |
| `#/trust` | What was checked, where, with which axioms | MUST (§13) |
| `#/playground` | Free-form widgets | MAY |
| `src/<path>.html#L<a>-L<b>` | Rendered Lean source (§7) | MUST (rollout in progress) |

Header nav order: **Start here · Proof graph · Nodes · [Playground] · About · [Trust] · GitHub**.

### 6.1 Proof graph (`#/`)

- Cytoscape + dagre (CDN pinned: cytoscape 3.30.2, dagre 0.8.5, cytoscape-dagre 2.5.0); `cose` for "All".
- Views: *Explained spine* (default), *Spine + direct deps*, *Files* (one node per module), *All declarations*; plus a find box (Enter opens the best match).
- Node fill = own status colour (§8). Explained nodes are large (26) and labelled; stubs small and dim.
- **Headline theorems: solid pink/red border** (`#f92672`, 3px, bold label). Every headline in `headlines`, not just main.
- **Statement set: blue outer ring** (`outline` 3px `#66d9ef`, offset 3). Legend text: "needed to read the main statement".
- **Pending: dashed purple border** (`#ae81ff`).
- Edges point from a declaration to what it uses. Solid = mention, dashed (opacity .45) = proof-only.
- Hover fades everything outside the node's closed neighbourhood.
- Side panel (in this order): *Your progress* (spine bar, whole-proof bar, sentence about the main statement), *Legend*, *Start here* (ordered list = statement set then headlines), *Progress file* (Export / Import / Reset).
- A prominent **"Start here: what the theorem says →"** link (`a.start-link`) under the intro paragraph.
- Progress bars count **understood** nodes only (quiz-only doesn't advance a bar).

### 6.2 Node page (`#/node/<id>`): order is normative

```
┌───────────────────────────────────────────────────────────────────────────┐
│ ← graph                    [● colour dot | ☐ I think I understand this | ★★☆☆ 2/4] │  1. status bar (top)
│ Title                                                                     │  2. head
│ [kind pill] [review pill]  fully.qualified.Name                           │
│ Summary sentence                                                          │
│ (headline → "Start here" link; statement-set member → "Needed to read…")  │
│ status note: what's still pending                                         │
├──────────────────────────────┬────────────────────────────────────────────┤
│ Plain English (body)         │ Formal statement   (sticky, own scroll)    │  3. side by side
│ widgets                      │ wrapped Lean                               │
│ Faithfulness notes (caveats) │ Main.lean lines 9–28  · section variables  │
│                              │ Mentions · Proof uses · From Mathlib · Used by │
├──────────────────────────────┴────────────────────────────────────────────┤
│ Bonus: check yourself (quiz)                                              │  4. quiz
│ Edit on GitHub · agent prompt                                             │  5. edit
│ Discussion (giscus)                                                       │  6. discussion
└───────────────────────────────────────────────────────────────────────────┘
```

1. **Status bar**, at the very top, right of "← graph" (`.topline` > `.statusbar#statusbar`), left border and dot in the node's colour (`--st`):
   - the **understanding checkbox**, always enabled, never gated by the quiz. Label is configurable
     (`labels.understand`); canonical today **"I think I understand this"**; a short label such as
     **"Understood"** is explicitly allowed. Use the same label everywhere on a site
     (status bar, Start here cards).
   - **quiz stars**: one star per question, `★` filled once that question has been answered correctly and
     *sticky* thereafter, then `right/total`. It's a button that scrolls to the quiz.
   - stubs show only the dot and the status label.
2. **Head**: title, kind pill + review pill (`draft` in orange), fully qualified name, summary, Start-here link
   (headline) or "Needed to read the main statement" (statement-set member), status note (hidden when empty).
3. **Side by side** (`.sbs`, grid `minmax(0,1fr) | minmax(0,1.2fr)`, gap 2rem):
   - **left** `.sbs-plain`: plain-English body, then **widgets** (directly under the plain English; never after the quiz), then *Faithfulness notes* (`caveats`, orange left rule).
   - **right** `.sbs-formal` > `.sbs-formal-inner`: **sticky** below the header (`top: var(--hdr)+.5rem`, `max-height: 100vh−hdr−1rem`, own scroll). Contents: "Formal statement", **wrapped Lean** (§9.3), source reference line (§7), section variables, then dependency lists:
     *Mentions* (always open), *Proof uses* (theorems; collapsed in `<details>` when > 12), *From Mathlib* (links to Mathlib docs), *Used by* (collapsed `<details>`, first 40 then "+N more").
   - Stub: left column holds a "Needs explainer" panel with an edit/new-file link and a collapsible agent prompt.
4. **Bonus quiz**: heading "Bonus: check yourself" (`#quiz-head`), one-line note that each right answer fills a star; "Check answers" button; per-question verdict + explanation.
5. Edit link to `nodes/<id>.md` on GitHub + collapsible **agent prompt** (target, source range, variables, statement, mentions, proof uses, instructions to follow CONTRIBUTING.md and the schema, faithfulness rules, `npm run validate`).
6. **Discussion**: giscus, mapping `specific`, term **`node: <id>`**, category **Announcements**, strict, reactions on, input top, theme dark, lazy. Show a note instead on `file:` URLs.

**Mobile (< 800px)**: one column, same order: status bar → head → plain English → widgets → caveats → formal statement → quiz → edit → discussion. The formal column stops being sticky. < 560px: `.topline` stacks, status bar left-aligned.

### 6.3 Start here (`#/start`)

"Start here: what the theorem says." Before any proof: (a) each **headline** as a card with pink border,
(b) "Definitions it uses (N), simplest first": the statement set in dependency order (everything a
definition mentions comes before it; ties by id), (c) "From Mathlib (taken as given)": every Mathlib
name the set mentions, linked to Mathlib docs with its `mathlibGloss` line (fallback: "see the Mathlib docs").
Each card: colour dot, title link, kind pill, understanding checkbox (same label), stars, summary, wrapped Lean.
Ticking a box re-renders in place, keeping the scroll position. The page says how many of the definitions are understood.

### 6.4 Walkthrough / proof outline widget

- **No step-through / show-all toggle and no dimming** (removed 2026-10-22: it added little).
  The outline shows every step; clicking a step selects it and shows its note, Lean, and the nodes it uses
  below the outline; the first step starts selected. Markup in `assets/walkthrough.js`.
- **Proof view** (shipped on star-height 2026-10-26: both the linked panes and the minimap,
  with a toggle to switch). For a theorem with `site/proofs/<id>.yml`, the node page shows its tactic proof as
  English steps beside the real Lean, and this **replaces** the walkthrough widget for that node. Markup in
  `assets/proofview.js`, mounted by `app.js` from `data/proofs.json`.
  - **Data**: `site/proofs/<id>.yml` lists `segments` with `lines: [a, b]` (absolute, inclusive), `src`
    (`explainer` | `comment` | `draft`), `title`, optional `note`, `uses` (declaration ids, checked) and `hard`.
    The Lean is never written by hand: `tools/build_proof_steps.mjs` copies it verbatim from the source into
    `data/proofs.json` (committed). `npm test` (`test_proof_steps.mjs`) fails on a gap, an overlap, an unknown
    `uses` id, or drift between `proofs.json` and the sources. Segments cover the proof body exactly (first
    starts after the `:= by` line; last ends on the declaration's last line).
  - **Badges are honest**: `explainer` only for English taken from the node's reviewed explainer, `comment` for a
    Lean comment, `draft` for anything else.
  - **Two layouts, one toggle** ("Linked panes" | "Outline"): *linked panes* = English steps left, Lean segments
    right, each in its own scroll; selecting or hovering a step on either side highlights its partner.
    *Outline* = numbered steps with a one-line Lean peek, the selected step expanded, and a sticky **minimap** of
    the whole proof on the right (hidden < 800px). "Show all Lean" / "Compact Lean" expands or folds every
    segment. The chosen layout is remembered per width class (`localStorage`, key `<site>-proofview`);
    narrow screens default to Outline.
  - Each step's `L<a>–<b>` and the header's "File.lean lines a–b" link to the on-site source (§7), with a
    small GitHub link beside the header range.

## 7. Source references and rendered Lean source

Rule: **every reference to a source line or range anywhere on a site (node page, agent prompt excepted,
widgets, about/trust prose, walkthrough steps, Start here cards) MUST be a link to the on-site rendered
source at that line**, e.g. `Main.lean lines 9–28` → `src/OAI/…/Main.lean.html#L9-L28`, which scrolls to and
highlights the range. A small secondary **"view on GitHub"** link (`blob/<branch>/<file>#L<a>-L<b>`) MAY sit next to it.
The agent prompt keeps the GitHub URL (agents work from the repo).

Rendered source pages:
- Only **this repository's** Lean is rendered. Mathlib and other dependencies are not; identifiers that resolve to
  them link out to the Mathlib docs (`https://leanprover-community.github.io/mathlib4_docs/find/?pattern=<name>#doc`).
- Identifiers that resolve to project declarations link to their definition line on-site.
- Name resolution SHOULD come from Lean's `.ilean` files (`tools/build_xref.py` → `data/xref.json`: exact ranges,
  no regex guessing) so CI renders without building Lean. Regex extraction (eulers-gem's
  `scripts/build-source-pages.py`) is acceptable as a fallback, with misses falling through to Mathlib docs.
- Every line has an `id="L<n>"` anchor; `#L<a>-L<b>` highlights the range; the page scrolls it into view below the header.
- Every declaration header carries a **badge linking back to its plain-English node** (`#/node/<id>`)
  when one exists (eulers-gem: `--informal-map` generated by `build_site.mjs` as `data/informal-map.json`).
- Page chrome: file tree sidebar, per-file outline, site links back to the proof site (eulers-gem: `--site-links`),
  small "view on GitHub" link, same Monokai tokens as the site (eulers-gem uses Pygments `github-dark`; migrate).
- Location: `dist/src/<path>.lean.html` (canonical; shipped on star-height 2026-10-26, rendered by
  `tools/build_source.mjs` at build time, checked by `npm run test:source`). eulers-gem serves it at `/docs/` beside `/learn/`.
- **One link helper**: every reader-facing source link goes through `assets/source.js` — `sourceUrl(file, a, b, root?)`
  (on-site, `SOURCE_BASE = "src/"`), `githubSourceUrl` (secondary link, agent prompt), `sourceLabel`
  ("Main.lean lines 9–28"), `anchor`. The build's linkifier for "File.lean lines a–b" in node prose
  (`tools/srcrefs.mjs`) and the source pages use it too. A test forbids hand-built source URLs.

## 8. Progress model (shared `assets/progress.js`)

MUST be byte-identical across sites (header comment says so; `test_progress.mjs` tests it). localStorage only;
nothing leaves the browser.

- Storage: `{ v: 2, nodes: { [id]: { viewed?, signedOff?, quizPassed?, correct?: bool[], answers? } } }`. Timestamps are ms.
- Key: the site's `progressKey`. The key name stays even when the schema version changes (star-height's key is still `…-v1` holding v2 data).
- **Versioning rules:** bump `PROGRESS_VERSION` for any change in meaning; `migrateProgress()` MUST accept every older
  version and any garbage (returns empty, never throws), run on load **and** on Import; migrations only *add*
  information that the old version implied (v1→v2: every v1 sign-off had passed the quiz, so set `quizPassed`);
  never drop a reader's sign-offs; add a test per migration.
- Own status (`ownStatus`) and colours (`COLORS`), darkest = most done:

| status | meaning | colour |
|---|---|---|
| `both` | signed + quiz passed | `#4caf50` |
| `quiz` | quiz passed only | `#a6e22e` |
| `signed` | signed only | `#d9f99d` |
| `explained` | has explainer, nothing done | `#66d9ef` |
| `stub` | no explainer (can't be signed) | `#75715e` |
| pending (overlay) | signed but a mention isn't understood | dashed `#ae81ff` ring |

  Greens take `#111` text at ≥ 6.7:1 and stand out from panels at ≥ 5:1 (checked by `contrast()` in tests).
- Stars: `quizScore`, `recordQuizResults` (per-question `correct[]`, sticky; passing all sets `quizPassed` once),
  `starString`. Records without `correct` count as all-filled if `quizPassed`.
- Export/Import/Reset buttons on the graph page; export file `<site>-progress.json`.

## 9. Visual tokens and CSS

Reference: `proof-site.css`. Dark Monokai theme, MUST use these tokens:

```
--bg #1e1f1c  --panel #272822  --panel2 #2f302a  --fg #f8f8f2  --dim #a59f85  --line #3e3d32
--pink #f92672  --orange #fd971f  --yellow #e6db74  --green #a6e22e  --blue #66d9ef  --purple #ae81ff
--unread #75715e  --explained #66d9ef
--signed #d9f99d  --quiz #a6e22e  --both #4caf50  --pending #ae81ff     (= COLORS in progress.js)
```

9.1 Type: `system-ui` 16px/1.55; code `"JetBrains Mono", "Fira Code", ui-monospace`. Widths: `main` 1100px, `.wide` none, `.node` 1560px.
9.2 Lean colours: keywords/operators pink, types blue italic, numbers purple, comments `--unread` italic, strings yellow, constructors orange,
project references (`a.ref`) green with dotted underline, linking to `#/node/<id>`. `pre.lean` has a 3px pink left rule.
9.3 **Wrapped Lean**: statements are never horizontally scrolled on node/start pages. `leanlines.js` splits highlighted HTML into
balanced per-line fragments; each `.ln` wraps (`pre-wrap`, `overflow-wrap:anywhere`) with a **hanging indent** of 4ch past the
line's own indentation (`padding-left: calc((var(--i)+4)*1ch); text-indent:-4ch`).
9.4 Pills: kind (theorem green, def/instance blue, inductive purple), status (filled greens with `#111` text), draft orange.
9.5 Status bar/cards use `--st` for left border (6px) and dot.

## 10. `index.html` head, preview card, caching

- `<title>` and `description`, plus `og:type website`, `og:site_name tangentproofs`, `og:title`, `og:description`,
  `og:url` (the site's canonical URL), `og:image` (absolute URL to `assets/og.png`), `og:image:width 1200`,
  `og:image:height 630`, `og:image:alt`, `twitter:card summary_large_image`, `twitter:title/description/image`.
- `og.png` MUST be exactly 1200×630 and show the theorem in a phrase, in the site's theme (render from `tools/og.html` with headless Chrome).
- **Cache-bust**: when `og.png` changes, append `?v=N` (increment N) to both `og:image` and `twitter:image`, since card
  caches key on the URL. The hub index (`tools/update.mjs`) only shows an image that returns 200.
- Footer: credit for the theorem and Lean proof (with licence), "Explanations are community-written and may be wrong;
  the Lean is the ground truth.", "Progress is stored only in this browser."

## 11. Build and tests

`package.json` scripts (canonical names):

```
"validate": "node tools/build_site.mjs --check",
"build":    "node tools/build_site.mjs",
"test":     "node tools/test_progress.mjs && node tools/test_leanlines.mjs && node tools/test_statement.mjs
             && [node tools/test_regex.mjs etc.] && node tools/test_widgets.mjs [&& node tools/test_app.mjs]
             && node tools/build_site.mjs --check",
"serve":    "node tools/build_site.mjs && python3 -m http.server -d dist 8765"
```

Dependencies: `ajv` (2020 draft), `js-yaml`, `marked` only. `build_site.mjs` output in `dist/`: `index.html`, `assets/`,
`data/decls.json`, `data/nodes.json` (rendered HTML fields `summaryHtml`, `bodyHtml`, `caveatsHtml`, quiz `qHtml/choicesHtml/explainHtml`),
`data/needs-explainer.json` (agent work list: reachable stubs sorted by depth), `data/node.schema.json`,
`data/informal-map.json` (full name → node URL, for source badges), `src/` (rendered source, §7), `.nojekyll`.

Widget tests: every widget's logic lives in a pure module (`regex.js`, `automata.js`, …) with assertions in
`test_widgets.mjs` **keyed to the Lean definition it mirrors**. A widget is a demonstration, not evidence; the About page says so.

## 12. CI and deployment

`.github/workflows/site.yml` (canonical = star-height plus a `paths` filter):

- Triggers: `push` to `main` and `pull_request`, both with `paths: [site/**, <lean source dirs>/**, .github/workflows/site.yml]`
  (Lean changes MUST trigger, because the rendered source and decls must stay in sync), and `workflow_dispatch`.
- Job `build` (working dir `site`): checkout, Node 20 with npm cache, `npm ci`, `npm test`, **re-run `build_decls.py` and
  `git diff --exit-code data/decls.json`** (stale data fails CI), `npm run build`, upload `site/dist` as the Pages artifact (not on PRs).
- Job `deploy`: `actions/deploy-pages@v4`, `pages: write`, `id-token: write`, environment `github-pages`.
- Repo Pages setting: **`build_type = workflow`** (`gh api repos/<repo>/pages` shows `"build_type":"workflow"`).
- Lean verification is a separate workflow (e.g. eulers-gem `lean.yml`, axiom audit script). CI never needs Lean to build the site.

## 13. Honesty rules (MUST)

1. **Every headline statement is audited** by an independent model (Claude) against the classical claim it's named for:
   does the Lean say what the English name says, with no extra or missing hypotheses? The audit is committed (e.g. `*_CLAUDE_AUDIT.md`)
   and its fixes applied before the site calls the result by its classical name.
2. **No classical name if the hypotheses smuggle in the result.** If a hypothesis is (equivalent to) the conclusion or does the hard part,
   the theorem isn't the classical theorem; rename it or label it.
3. **Conditional results are labelled CONDITIONAL** in the title and summary, and the node names each open hypothesis
   (e.g. eulers-gem "Face data of a regular polyhedron", conditional on `FaceLatticeFacts`). Gaps live in a library the main build doesn't import.
4. **Axioms disclosed**: the Trust page lists `#print axioms` for each headline. Anything beyond `propext`, `Classical.choice`, `Quot.sound`
   (notably `Lean.ofReduceBool` from `native_decide`, or `sorryAx`) is named on the Trust page and on the affected node.
5. **Trust page** (`#/trust`): what was checked, by whom/what, on which build, which parts were vendored or not re-checked, which
   declarations were read from source rather than the compiled build (`extracted: false`), generated modules.
6. Widgets and outlines are summaries/demonstrations, never evidence, and the About/Trust page says so.
7. Explanations are `review: draft` until a human checks them against the Lean.

## 14. Current sites: conformance and migration items

Canonical = star-height `main` @ `bcafcf9`. Gaps (✗) are migration items for the layout rollout:

| Rule | star-height | fourcolor-lean | turyn | eulers-gem (`learn/`) |
|---|---|---|---|---|
| Folder | `site/` ✓ | `site/` ✓ | `site/` ✓ | `learn/` (allowed: `site/` holds the Pages root) |
| `progress.js` identical | ✓ (has stars API) | ✗ lacks `quizScore`/`recordQuizResults`/`starString` (27-line diff) | ✗ same | ✗ same |
| Three greens + pending ring | ✓ | ✓ | ✓ | ✓ |
| Status bar at top, stars | ✓ | ✗ | ✗ | ✗ |
| Side-by-side + sticky formal + wrapped Lean (`leanlines.js`) | ✓ | ✗ | ✗ | ✗ |
| Widgets under plain English, before quiz | ✓ | ✓ (but formal statement is above plain English, stacked) | ✓ (same) | ✓ (same) |
| Statement set ring + `#/start` (`statement.js`) | ✓ | ✗ | ✗ (has 6 `HEADLINES`, no start page) | ✗ (`START_HERE` hand list, `ROOTS` = Results theorems) |
| All headlines red-bordered | ✓ (1) | ✓ (`MAIN` only) | ✓ (6) | ✓ |
| Proof view (panes + outline/minimap, `proofview.js`) | ✓ (3 nodes) | ✗ | ✗ | ✗ |
| Walkthrough: no toggle | ✓ | ✗ toggle in `widgets.js` | ✗ toggle in `widgets.js` | ✗ toggle in `widgets.js` |
| Trust page | ✗ **add one** | ✓ | ✓ (discloses `native_decide`) | ✓ |
| Rendered source, on-site line links (one helper, `source.js`) | ✓ | ✗ | ✗ | partial: `/docs/` + back-link badges; node page links "Read it in the browsable source" by declaration, but the "lines a–b" link still goes to GitHub |
| Source page theme = Monokai | ✓ | – | – | ✗ Pygments `github-dark` |
| CI `paths` include Lean dirs | ✓ (push: all; PR: `site/**`, `OAI/**`, `ComparatorChallenges/**`, `Check.lean`) | partial (PR only: `4ct/FourColor/**`) | ✓ `lean/**` | separate `pages.yml` on every push to main ✓ |
| `decls.json` staleness check in CI | ✓ | ✓ | ✓ | ✓ |
| `test_app.mjs` | ✗ | ✗ | ✓ | ✗ |
| `test_statement`/`test_leanlines` | ✓ | ✗ | ✗ | ✗ |
| `site.config.json` | ✗ (constants) | ✗ | ✗ | ✗ |
| `og:image` `?v=N` cache-bust | ✗ | ✗ | ✗ | ✗ |
| Pages `build_type=workflow` | ✓ | ✓ | ✓ | ✓ |

## 15. Conformance checklist

A site is **conformant** when every item holds. Proposed automation: `tools/check_conformance.mjs` in the shared kit
(see GUIDE.md §7) run in each site's CI, plus a hub-side job that runs it against every repo in `informalization`.

- [ ] `site/` (or documented alternative) with the layout in §2; `CONTRIBUTING.md` at repo root.
- [ ] `site.config.json` valid against `site-config.schema.json` (or, until then, constants grouped at the top of `app.js`).
- [ ] `assets/progress.js`, `statement.js`, `leanlines.js`, `lean.js` byte-identical to the kit version (hash compare).
- [ ] `npm test` passes and includes `test_progress`, `test_statement`, `test_leanlines`, `test_widgets` (if widgets), `build_site.mjs --check`.
- [ ] Every `nodes/*.md` validates against the schema; ids exist in `decls.json`; `## Plain English` present; quiz keys valid.
- [ ] `decls.json` regenerates identically from `decls.raw.json`.
- [ ] Every `headlines` id has an explainer, is red-bordered on the graph, and appears on `#/start`.
- [ ] Every statement-set member has an explainer (else a warning) and every Mathlib name in the set has a gloss.
- [ ] Node page DOM order: `#statusbar` before `h1`; `.sbs-plain` before `.sbs-formal`; `#widgets` inside `.sbs-plain`; `#quiz-head` after `.sbs`; `#giscus` last. (Testable with a headless DOM or jsdom.)
- [ ] Understanding checkbox never disabled; stars count = quiz length.
- [ ] No walkthrough toggle (`grep -i "step through"` in assets finds nothing outside `dom.js` stepper helpers).
- [ ] No `href` to `github.com/.../blob/...#L` in rendered pages except elements with class `gh` ("view on GitHub") and the agent prompt.
- [ ] `index.html` has all §10 meta tags; `og.png` is 1200×630; `og:image` URL returns 200.
- [ ] `#/trust` exists and lists `#print axioms` for each headline; any non-standard axiom is named.
- [ ] Each headline has a committed audit file; conditional headlines say CONDITIONAL in title/summary.
- [ ] `site.yml` triggers on site and Lean paths; Pages `build_type=workflow`.
- [ ] Repo is listed in the hub's `tools/overrides.json` `informalization` and appears on <https://tangentproofs.github.io/>.
