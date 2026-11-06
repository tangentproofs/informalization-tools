# Writing one explainer (brief for the drafting model session)

This is the brief given to each Claude session that drafted a hub explainer. Put it in the hub repo as
`sites/AUTHORING.md` and point the session at it from its task message (see `task-message.md`).

You are writing an **unofficial, plain-English explainer** of one Lean project for an informalization hub
(a site built with this toolkit; its URL is in `hub.json`). You write the content. The engine, the build and the deployment
already exist. Your slug, upstream repo, submodule and pinned commit are given in your task message and in
`projects.json`.

## Hard rules

1. **No Lean builds, anywhere.** Never run `lake`, `lean`, `elan` or anything that compiles Lean. The engine
   scans the source text (`engine/tools/scan_decls.py`). If you need to know what something means, read the source.
2. **Work only in `sites/<slug>/`.** Do not edit `engine/`, `projects/`, other sites, `index.html` or `projects.json`.
   If the engine has a bug, describe it in `sites/<slug>/NOTES.md` and work around it.
3. **Never touch the upstream repo.** Do not push to it, and do not open issues or PRs on it or anywhere else.
   Commit on your branch only. **Do not push** (the coordinator fetches your branch).
4. **No authorship claims.** The project belongs to its authors. Don't write "our proof" or "we prove", and don't
   name the hub's owner or organisation as authors. Credit the authors named in the
   upstream README or LICENSE/NOTICE, and fix `authors` in `site.json` if the README says otherwise.
5. **Respect the licence** (`license` in `site.json`; the engine decides `allowSource` from the SPDX id):
   - **No licence (`spdx: null`):** the site must not reproduce the project's source. In everything you write
     (bodies, summaries, caveats, quizzes, pages), use **no Lean code blocks** and **no verbatim Lean
     statements**. Walkthrough steps get **no `lean:` field**. Inline identifiers such as `movesAreValid` are
     fine. Describe the math in your own words and link to the exact lines ("TicTacToe/Lemma.lean lines 10–14").
     The engine strips statements from the published data and links every line reference to GitHub at the
     pinned commit.
   - **Permissive licence** (Apache-2.0, MIT, GPL-3.0 …): short quotes and walkthrough `lean:` snippets are
     fine. The engine renders the highlighted source with the licence and NOTICE.
6. **Honesty.**
   - Grep the project for `sorry`, `admit`, `axiom`, `native_decide`, `implemented_by`, `extern`, `opaque`.
   - Any headline whose proof (or anything it uses) has a `sorry` is labelled **PARTIAL (sorry)**. A result that
     assumes extra hypotheses is labelled **CONDITIONAL**, and every gap is named.
   - Don't use a classical theorem's name if the Lean statement is weaker than the classical claim, or if its
     hypotheses smuggle in the result.
   - Say plainly that the Lean was **not built** for this site, so "proved" means "the file has a complete-looking
     proof", not "the kernel accepted it".
   - Many repos are not theorem libraries (tools, benchmarks, agents, DSLs). Explain what the Lean actually *is*.
     For example, "these are benchmark problem statements, deliberately left as `sorry`".
7. **Not official documentation.** The engine adds a banner saying so; never write anything that reads as the
   authors' own documentation or endorsement.

## What to produce, in `sites/<slug>/`

Start by renaming `site.json.todo` to `site.json`. CI builds only sites that have a `site.json`. If the upstream README states a licence that has no LICENSE file, **don't** change `license` yourself. Report it in NOTES.md and the coordinator decides.

- **`site.json`.** The coordinator filled in `slug`, `repo`, `submodule`, `sha`, `members`, `authors`,
  `authorUrl` and `license`. You fill in:
  - `title`: "<Project>, explained".
  - `brand`: short HTML, e.g. `cubing <em>explained</em>`.
  - `h1`: the home-page headline.
  - `lead`: HTML, 1–3 sentences. **The key takeaway**, shown set apart at the top of the home page. No
    "The surprise:" label or any other label: just say the most important thing.
  - `desc`: one or two sentences, also used on the hub card.
  - `startNote`: HTML for the "Start here" page.
  - `sizeNote`: e.g. "About 2,600 lines of Lean in 18 files."
  - `agentCtx`: a one-line description of the project.
  - `roots`: the Lean dirs and files to scan, relative to the submodule root (leave out `.lake`, tests, examples
    unless they matter).
  - `ns`: an optional namespace prefix to strip from ids, e.g. `"Cubing."`.
  - `headlines`: the 1–6 main results, by id as `scan_decls` names them.
  - `mathlibNamespaces`, `mathlibNames`: as in the reference sites.
  - `gloss`: `{MathlibName: "HTML gloss"}` for each Mathlib/core notion that a headline statement uses.
  - `headlineFiles`: optional list of file paths to badge as "headline" on the source index.
- **`nodes_src/*.py`:** the explainer nodes (format below). Cover:
  - (a) every headline;
  - (b) the **statement set**: the definitions the headline statements mention, transitively, stopping at Mathlib;
  - (c) a few key proof lemmas, if they help.

  Typical size: 8–25 nodes. For a huge repo, pick the main thread and say on the About page what you left out.
- **`pages/about.md`:** what the project is and who made it (from its README), what the Lean covers, and where
  to start. The engine appends a standard "Credit, licence and status" section, so don't duplicate it.
- **`pages/review.md`:** for each headline, is the Lean statement faithful to what its name, README or paper
  claims? Note conditional or partial results, weak or vacuous statements, and anything surprising.
- **`pages/trust.md`:** what was and wasn't checked:
  - not built;
  - counts of `sorry`, axioms and `native_decide`, with file/line links;
  - declarations scanned from text (`extracted: false`);
  - explanations AI-written and unreviewed.
- **`NOTES.md`:** for the coordinator, not published:
  - the time you spent;
  - what was hard;
  - **the places where you are least sure your explanation is right** (concrete: node id + why);
  - anything the author might object to.

## Node format (`nodes_src/<any>.py`, files starting with `_` are helpers)

```python
NODES = []
def node(id, title, summary, body, quiz, caveats=(), widgets=None):
    NODES.append(dict(id=id, title=title, summary=summary, body=body, quiz=quiz, caveats=list(caveats), widgets=widgets))
def q(text, choices, answer, explain):
    return {"q": text, "type": "choice", "choices": choices, "answer": answer, "explain": explain}

node("Cubing.solved_after_moves",            # id exactly as in build/<slug>/data/decls.json
 "Headline: …",                              # title, ≥ 3 chars
 "The key takeaway in one or two sentences: the most important or surprising thing, stated plainly.",  # summary, shown set apart
 r"""## Plain English

**Theorem (`solved_after_moves`, Cubing/Moves.lean lines 120–131).** …

Link other nodes as [Move](#/node/Cubing.Move).
""",
 [q("…?", ["…", "…"], 0, "Why, with a line reference such as Cubing/Moves.lean lines 120–124."), …],   # 3–6 questions
 caveats=["Faithfulness notes: anything the plain English simplifies, PARTIAL/CONDITIONAL labels, …"],
 widgets=[{"type": "walkthrough", "title": "How the proof goes (Cubing/Moves.lean, lines 120-131)",
           "config": {"steps": [{"text": "…", "link": "Cubing.Move"},            # optional link = node id
                                 {"text": "…", "lean": "exact verbatim proof line"}]}}])   # `lean` ONLY if licensed
```

- **Line references** are written as `Dir/File.lean lines a–b` (or `File.lean line a` when the file name is
  unique). The build turns them into links to those exact lines at the pinned commit, and **fails if a range is
  outside the file**. The file name must start with a capital letter to be linked.
- **Every headline gets a walkthrough** (its proof outline), with its title naming the file and lines. For long
  proofs, outline the key steps.
- Quizzes test understanding of *the statement* (what it says, what it doesn't), not trivia.

## Build loop

```
git submodule update --init <submodule>       # once
(cd engine && npm ci)                          # once
engine/build.sh <slug>                         # until it ends with "built _site/<slug>"
cat build/<slug>/dist/data/needs-explainer.json | head   # what's still unexplained, nearest first
```

- Warnings about unexplained meaning-dependencies are fine for minor ones. Explain the statement set.
- To preview, run `python3 -m http.server -d _site 8765`, but you don't have to.
- When done: `git add sites/<slug> && git commit -m "<slug>: unofficial plain-English explainer"`. Don't push.
