# informalization-tools

The engine, prompts and procedure behind the tangentproofs "informalization" sites, such as the
[Lean NYC member-project explainers](https://tangentproofs.github.io/lean-nyc/) and
[Jacobian, explained](https://tangentproofs.github.io/jacobian-variety/learn/).

## What an informalization site is

A Lean 4 proof is checked by a computer, but most people can't read it. An informalization site reads
the proof back into plain English, one declaration at a time:

- a **node** for each important definition and theorem, with a plain-English explanation next to the
  exact Lean statement, and a short quiz;
- a **proof graph** and a **Start here** page that lists what you need to understand the main results;
- the **highlighted source**, with every "File.lean lines a–b" reference linked to those lines;
- a **Review** page that says whether each main result really is what its name claims;
- a **Trust** page that says what was and wasn't checked (sorries, axioms, whether the Lean was built).

The Lean is always the ground truth. The English is a guide to it, and the site says so.

## The pipeline

1. **Scan the declarations.** `engine/tools/scan_decls.py` reads the Lean source text (no Lean build)
   and writes `data/decls.json`: every `def`/`theorem`/`structure`/…, its file and lines, its statement,
   and which other declarations it mentions or its proof uses.
2. **Pick the nodes.** The headlines (main results) first, then the *statement set* (everything the
   headline statements mention, transitively, stopping at Mathlib), then a few key lemmas.
   `data/needs-explainer.json` lists what's still unexplained, nearest first.
3. **Claude drafts.** One drafting session per site, given
   [`prompts/draft-explainer.md`](prompts/draft-explainer.md) and a task message from
   [`prompts/task-message.md`](prompts/task-message.md). It writes `nodes_src/*.py` and the About,
   Review and Trust pages, and loops on the build until it passes.
4. **Review passes.** Short single-purpose passes: coverage, faithfulness, quizzes, links, plain
   words ([`prompts/review-pass.md`](prompts/review-pass.md)).
5. **Honesty audit.** A separate model session audits every node and page against the Lean
   ([`prompts/honesty-audit.md`](prompts/honesty-audit.md)) and writes a verdict
   (PASS / PASS WITH CAVEATS / FAIL). The verdict goes on the Review page.
6. **Build.** `engine/build.sh <slug>` generates the config, writes the nodes, runs the tests and
   builds a static site in `_site/<slug>/`.
7. **Pages.** A GitHub Actions workflow ([`templates/workflows/pages.yml`](templates/workflows/pages.yml))
   builds every site and deploys to GitHub Pages.

## Layout

| path | what |
|---|---|
| `engine/` | the site engine: browser app (`assets/`), build tools (`tools/`), node schema, `gen.py` (per-site config and `index.html` from `site.json`), `build.sh` |
| `engine/tools/scan_decls.py` | declaration scanner (source text, no Lean build) |
| `engine/tools/build_site.mjs`, `build_source.mjs` | validate nodes, build the site and the highlighted source pages (Lean, plus a small generic highlighter for other languages via `sourceExts`) |
| `engine/tools/srcrefs_lock.py` | optional: lock "File.lean lines a–b" references to the text they cite, and re-point them after the Lean changes (needs full repo paths in references) |
| `tools/` | hub tools: `update.mjs` renders the hub page from `projects.json` + `hub.json`; `sync_projects.py` records node counts; `mktask.py` prints a drafting task message; `leakcheck.py` finds verbatim source lines in a no-licence site's text |
| `templates/` | `hub.json`, `projects.json`, a site skeleton (`site/`), hub page CSS and favicon, and the Pages workflow |
| `examples/rakesieve/` | a complete worked example: the site config, 69 nodes and the About/Review/Trust pages of [RakeSieve, explained](https://tangentproofs.github.io/rakesieve/learn/), for [tangentproofs/rakesieve](https://github.com/tangentproofs/rakesieve) (MIT), a prime sieve with both mathematical proofs (infinitude of primes as a corollary) and proofs about the program (every step emits the next prime) |
| `prompts/` | the briefs given to Claude for drafting, review passes and the honesty audit |
| `docs/` | `CONVENTIONS.md` (the rules for a proof site) and `GUIDE.md` (background) |
| `skill/proof-site/SKILL.md` | the step-by-step agent procedure |

### Config

- **`hub.json`** (hub root): the hub's name, base URL, repo, nav label, credit line, the browser-storage
  prefix for reader progress (never change it once live), giscus ids for comments (leave `repoId` empty to
  turn comments off), and the hub page text. See `templates/hub.json`.
- **`projects.json`**: one entry per hub card (`slug`, `repo`, `submodule`, `sha`, `members`, `authors`,
  `license`, `description`; optional `name`, `kind`, `own`, `tooling`/`toolDesc`, `secondaryOf`, `sites`,
  `talk`/`talkUrl`, `demo`, `url`).
- **`sites/<slug>/site.json`**: one site. The coordinator fills in `slug`, `repo`, `submodule`, `sha`,
  `authors`, `authorUrl` and `license` (`spdx`, `name`, `file`, optional `notice`, optional
  `authorPermission`). The drafting session fills in `title`, `brand`, `h1`, `lead`, `desc`, `startNote`,
  `sizeNote`, `agentCtx`, `roots`, `ns`, `headlines`, `gloss`, `headlineFiles`. Optional: `lang` (for
  non-Lean projects), `sourceRoots`/`sourceExts` (which files the source pages render), `ownProject`
  (banner wording for the hub owner's own project), `snapshot` (explain a public website instead of a repo).
- **`sites/<slug>/pages/roadmap.md`**: if present, the site gets a Roadmap tab.
- **Scanner options** in `site.json` (all off by default; the RakeSieve example uses them):
  `indentedDecls` (read declarations indented inside a `section`), `instanceNames: "lean"` (name anonymous
  instances the way Lean does, e.g. `instPrimeGenPrimeSieve`, instead of `instance_<line>`), `shortDefBodies`
  (show definitions under 6 lines with their body), `manualEdges` (`{"proofDeps": {id: [ids]}, "meaningDeps":
  {id: [ids]}}` for links the text scan can't see, such as a theorem that goes through a type class
  instance), `sectionVariables` (`{id: ["(α : Type)", "[C α]"]}`, the `variable`s in scope), `nodeAuthors`
  (default `authors` on every node), and `writtenBy` / `writtenByAbout` (who drafted the text, for the footer
  and the About page's credit section).

## Try it: build the RakeSieve example

```sh
git clone https://github.com/tangentproofs/informalization-tools hub && cd hub
cp templates/hub.json hub.json                 # edit name, baseUrl, repo
mkdir -p sites projects
cp -r examples/rakesieve sites/
git clone https://github.com/tangentproofs/rakesieve projects/tangentproofs-rakesieve
git -C projects/tangentproofs-rakesieve checkout 1c165f93c0292f2c52f88c5325faabbdfbcfbc7e
(cd engine && npm ci) && pip install pyyaml
engine/build.sh rakesieve                      # -> _site/rakesieve/
python3 -m http.server -d _site 8765           # open http://localhost:8765/rakesieve/
```

RakeSieve is a good first example: the mathematics is simple (primes, crossing out multiples), and it has
both kinds of proof. Some are mathematical: there are infinitely many primes, obtained as a corollary of the
sieve never running empty. Others are about the program: every step of the sieve emits the next prime, none
skipped. Its Review page labels the one circular route (`SimpleGen` assumes Euclid) instead of hiding it.

## Running it on a new repo

```sh
# 1. a hub repo: copy engine/ and tools/ from here, plus templates/hub.json, templates/projects.json,
#    templates/hub-assets/ -> assets/, templates/workflows/pages.yml -> .github/workflows/
# 2. add the project as a pinned submodule
git submodule add https://github.com/OWNER/REPO projects/owner-repo
git -C projects/owner-repo checkout <sha>
# 3. a projects.json entry, and sites/<slug>/ from templates/site/ (rename site.json.todo when ready;
#    examples/rakesieve/ shows a finished one)
# 4. draft: give a Claude session prompts/draft-explainer.md (as sites/AUTHORING.md) and
python3 tools/mktask.py <slug>
# 5. build until it passes
(cd engine && npm ci)
pip install pyyaml
engine/build.sh <slug>              # -> _site/<slug>/
python3 -m http.server -d _site 8765
# 6. review passes, honesty audit, then publish the hub page
python3 tools/sync_projects.py && node tools/update.mjs
```

Never run a Lean build on a small shared machine: the scanner works from source text. If you want
`#print axioms` for the Trust page, run it where the project already builds and record the result.

## Honesty rules

- **The Lean is the ground truth.** The English must match the Lean as written. Anything looser goes
  under the node's `caveats`.
- **No smuggled hypotheses.** Don't use a classical theorem's name if the Lean statement is weaker, or
  if a hypothesis assumes the hard part.
- **Label partial results.** A result that rests on a `sorry` is **PARTIAL (sorry)**. A result with
  extra assumptions is **CONDITIONAL**, and every gap is named.
- **Say what was checked.** The Trust page lists sorries, axioms and `native_decide` with links, says
  whether the Lean was built, and says the explanations are AI-written drafts (`review: draft`) until a
  person reviews them.
- **Respect licences.** The engine reproduces a project's source only under a licence that permits it
  (or with the author's explicit permission), and includes the licence text. Without a licence, the
  site explains in prose and links to the exact lines on GitHub; `tools/leakcheck.py` checks nothing
  was copied.
- **Not official documentation.** Every page carries a banner saying the explainer is unofficial,
  AI-assisted and not reviewed by the project's authors, and credits them. Authors can ask for changes
  or removal.

## Status

Extracted from the live sites in November 2026. The engine here is the configurable one used by the
Lean NYC hub, with hub-specific text moved into `hub.json`. The Jacobian site uses an earlier
single-site copy with its settings written into `app.js`; this engine includes that copy's improvements
(`srcrefs_lock.py`, proof uses on instances). The original reference sites (star-height and others)
extract declarations from a Lean build with `ExtractDecls.lean`, which is not included here.

## License

MIT. See [LICENSE](LICENSE). The RakeSieve example's text explains tangentproofs/rakesieve, which is also MIT.
