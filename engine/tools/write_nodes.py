#!/usr/bin/env python3
"""Write <site>/nodes/<id>.md from the node data in <site>/nodes_src/*.py (keeps the YAML valid).

  python3 tools/write_nodes.py          # write nodes/, and delete node files no source defines any more
  python3 tools/write_nodes.py --check  # fail if nodes/ is not what nodes_src/ generates

Files in nodes_src/ starting with "_" hold shared wording (e.g. _terms.py); they define no nodes and the
node files may import from them. A node's `authors` defaults to "nodeAuthors" in site.json."""
import importlib.util, json, os, sys, yaml
SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = os.path.join(SITE, "nodes")
os.makedirs(out, exist_ok=True)
check = "--check" in sys.argv
cfg_path = os.path.join(SITE, "scan.config.json")
CFG = json.load(open(cfg_path, encoding="utf-8")) if os.path.exists(cfg_path) else {}
DEFAULT_AUTHORS = CFG.get("nodeAuthors", ["claude (AI-assisted, unofficial)"])
sys.path.insert(0, os.path.join(SITE, "nodes_src"))
want = {}
for f in sorted(os.listdir(os.path.join(SITE, "nodes_src"))):
    if not f.endswith(".py") or f.startswith("_"): continue
    spec = importlib.util.spec_from_file_location(f[:-3], os.path.join(SITE, "nodes_src", f))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    for n in m.NODES:
        fm = {"id": n["id"], "title": n["title"], "summary": n["summary"], "review": "draft", "authors": n.get("authors", DEFAULT_AUTHORS)}
        if n["caveats"]: fm["caveats"] = n["caveats"]
        if n["widgets"]: fm["widgets"] = n["widgets"]
        fm["quiz"] = n["quiz"]
        assert n["id"] + ".md" not in want, f"node {n['id']} is defined twice"
        want[n["id"] + ".md"] = "---\n" + yaml.safe_dump(fm, allow_unicode=True, sort_keys=False, width=110) + "---\n" + n["body"].lstrip("\n")
have = {f for f in os.listdir(out) if f.endswith(".md")}
if check:
    bad = sorted(f for f in want if f not in have or open(os.path.join(out, f), encoding="utf-8").read() != want[f]) + sorted(have - set(want))
    if bad: sys.exit("FAIL: nodes/ is stale; run python3 tools/write_nodes.py: " + ", ".join(bad))
    print(f"write_nodes: ok ({len(want)} nodes)"); sys.exit()
for f, text in want.items(): open(os.path.join(out, f), "w", encoding="utf-8").write(text)
for f in have - set(want): os.remove(os.path.join(out, f)); print("removed stale", f)
print("ok")
