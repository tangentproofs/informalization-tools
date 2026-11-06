# Task message for one drafting session

One drafting session per site, each in its own git worktree on its own branch (`explainer/<slug>`). The
coordinator fills in the placeholders from `projects.json` with `tools/mktask.py <slug>` and sends the result as
the session's first message. (Reconstructed from the generator script; the wording the sessions received
was the same in substance.)

```
Read sites/AUTHORING.md first and follow it exactly. Your site: slug SLUG, upstream REPO, submodule SUB pinned at
SHA, licence LIC. LICRULE Start by renaming sites/SLUG/site.json.todo to site.json, then fill in the fields
AUTHORING.md lists, write nodes_src/*.py and pages/{about,review,trust}.md (and pages/roadmap.md if a reading
order helps), and loop on engine/build.sh SLUG until it ends with "built _site/SLUG". No Lean builds. Work only in
sites/SLUG/. Commit on your branch when done; do not push. Write NOTES.md for the coordinator, including the
places where you are least sure your explanation is right.
```

`LICRULE` is one of:

- no licence: "This repo has NO licence: reproduce none of its source (no Lean code blocks, no verbatim
  statements, no walkthrough lean: fields); explain in prose and link exact lines."
- a licence: "Licence LIC permits quoting; keep quotes short and attribute."
