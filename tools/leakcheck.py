#!/usr/bin/env python3
"""For a no-licence site: report source lines (>= 30 chars, stripped) that appear verbatim in the explainer text."""
import json, sys, glob, os
slug = sys.argv[1]; S = json.load(open(f"sites/{slug}/site.json"))
text = "".join(open(f, encoding="utf-8").read() for f in glob.glob(f"sites/{slug}/nodes_src/*.py") + glob.glob(f"sites/{slug}/pages/*.md"))
hits = []
for f in glob.glob(f"{S['submodule']}/**/*.lean", recursive=True):
    for ln in open(f, encoding="utf-8", errors="ignore"):
        t = ln.strip()
        if len(t) >= 30 and not t.startswith(("--", "/-", "import", "open", "namespace", "end ")) and t in text: hits.append((os.path.relpath(f, S["submodule"]), t))
print(f"{slug}: license={S['license'].get('spdx')} code-fences={text.count('```')} lean-fields={text.count(chr(34)+'lean'+chr(34))} verbatim-lines={len(hits)}")
for h in hits[:15]: print("   ", h)
