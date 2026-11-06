#!/usr/bin/env python3
"""Print the first message for a drafting session: python3 tools/mktask.py <slug> [template]
The template defaults to prompts/task-message.md's fenced block; placeholders SLUG REPO SUB SHA LIC LICRULE."""
import json, re, sys, os
slug = sys.argv[1]
here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
tmpl_path = sys.argv[2] if len(sys.argv) > 2 else os.path.join(here, "prompts", "task-message.md")
p = [x for x in json.load(open("projects.json"))["projects"] if x["slug"] == slug][0]
lic = p.get("license") or "none (no LICENSE file)"
rule = ("This repo has NO licence: reproduce none of its source (no Lean code blocks, no verbatim statements, no walkthrough lean: fields); explain in prose and link exact lines."
        if not p.get("license") else f"Licence {p['license']} permits quoting; keep quotes short and attribute.")
t = open(tmpl_path, encoding="utf-8").read()
m = re.search(r"```\n(.*?)```", t, re.S)
t = m.group(1) if m else t
for k, v in (("LICRULE", rule), ("SLUG", slug), ("REPO", p["repo"]), ("SUB", p["submodule"]), ("SHA", p["sha"]), ("LIC", lic)):
    t = t.replace(k, v)
print(" ".join(t.split()))
