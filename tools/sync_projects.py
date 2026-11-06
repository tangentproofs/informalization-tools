#!/usr/bin/env python3
"""Mark projects whose explainer exists (sites/<slug>/site.json) and record their node counts in projects.json."""
import json, os, glob, importlib.util, sys
pj = json.load(open("projects.json", encoding="utf-8"))
for p in pj["projects"]:
    s = p.get("slug")
    if not s or not os.path.exists(f"sites/{s}/site.json"): continue
    n = 0
    sys.modules.pop("_common", None); sys.path.insert(0, f"sites/{s}/nodes_src")
    for f in sorted(glob.glob(f"sites/{s}/nodes_src/*.py")):
        if os.path.basename(f).startswith("_"): continue
        spec = importlib.util.spec_from_file_location(f"m_{s}_{os.path.basename(f)[:-3]}", f); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
        n += len(m.NODES)
    sys.path.pop(0)
    p["explainer"], p["nodeCount"] = True, n
json.dump(pj, open("projects.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(", ".join(f"{p['slug']}={p.get('nodeCount')}" for p in pj["projects"] if p.get("explainer")))
