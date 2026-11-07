#!/usr/bin/env python3
"""Keep the explainer's "File.lean lines a–b" references pointing at the Lean they were written about.

The nodes and pages cite Lean by line number. When the Lean changes, a bare number goes stale silently
(it still links somewhere, just to the wrong lines). So every reference is recorded in a lock file together
with the text of the lines it cites:

  python3 tools/srcrefs_lock.py --lock    # record the current text for every reference (after writing new prose)
  python3 tools/srcrefs_lock.py --check   # fail if any reference's lines no longer read as locked
  python3 tools/srcrefs_lock.py --remap   # after a Lean change: re-point references whose text moved, then
                                          # rewrite the prose and the lock

Run it in a built site directory (build/<slug>/ in a hub, after engine/build.sh <slug>, with LEARN_SRC_ROOT set
to the project checkout as build.sh does), or in a standalone site folder.

File names are resolved exactly as the build links them (tools/srcrefs.mjs): a name may be a full repo path
(Foo/Bar.lean) or any unique path suffix (Bar.lean, B4/Asm.lean when the file is imp/lean/B4/Asm.lean). A name
that matches no file or several files is not linked by the build, so it is skipped here too. The lock records
the resolved repo path, so a short name and a full name for the same file share one entry.

Where things live:
  * hub: the lock is sites/<slug>/srcrefs.lock.json, references are read from sites/<slug>/nodes_src/*.py and
    pages/*.md (the sources --remap rewrites); the site dir comes from "siteDir" in scan.config.json (gen.py).
  * standalone: the lock is data/srcrefs.lock.json; references are read from nodes/, pages/ and assets/app.js.

--remap looks for the locked text, line for line (whitespace-trimmed), first in the same file and then in every
.lean file. If the text is gone, a reference that covered a whole declaration follows that declaration (by name)
and is listed for a human to re-read; any other reference is reported as unresolved.
"""
import json, os, re, sys

LEARN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.abspath(os.environ["LEARN_SRC_ROOT"]) if os.environ.get("LEARN_SRC_ROOT") else os.path.dirname(LEARN)
_cfg_path = os.path.join(LEARN, "scan.config.json")
CFG = json.load(open(_cfg_path, encoding="utf-8")) if os.path.exists(_cfg_path) else {}
SITE_DIR = CFG.get("siteDir")
if SITE_DIR:  # hub build: the sources of truth are in sites/<slug>/
    LOCK = os.path.join(SITE_DIR, "srcrefs.lock.json")
    SOURCES = [os.path.join(SITE_DIR, "nodes_src"), os.path.join(SITE_DIR, "pages")]
else:         # standalone site folder
    LOCK = os.path.join(LEARN, "data", "srcrefs.lock.json")
    SOURCES = [os.path.join(LEARN, t) for t in ("nodes", "pages", "assets/app.js")]
# Same pattern as tools/srcrefs.mjs, restricted to references that carry line numbers.
REF = re.compile(r"\b((?:[A-Za-z0-9_-]+/)*[A-Z][A-Za-z0-9_]*\.lean)((?:</code>|`)?,?\s+lines?\s+)(\d+)(?:(\s*(?:-|–|—|to)\s*)(\d+))?")


def files_in(tops):
    for p in tops:
        if os.path.isfile(p): yield p
        elif os.path.isdir(p):
            for f in sorted(os.listdir(p)):
                if f.endswith((".py", ".md")): yield os.path.join(p, f)


def lean_files():
    """Every .lean file the site renders (sourceRoots, else roots, else the whole repo), as repo paths."""
    out = set()
    for top in CFG.get("sourceRoots") or CFG.get("roots") or ["."]:
        p = os.path.join(ROOT, top)
        if os.path.isfile(p) and p.endswith(".lean"): out.add(os.path.relpath(p, ROOT).replace(os.sep, "/"))
        for d, dns, fs in os.walk(p):
            dns[:] = [x for x in dns if not x.startswith(".") and x not in ("node_modules", ".lake")]
            out |= {os.path.relpath(os.path.join(d, f), ROOT).replace(os.sep, "/") for f in fs if f.endswith(".lean")}
    return sorted(out)


FILES = lean_files()


def resolve(name):
    """The repo path a cited name means, or None (no match or ambiguous), exactly as srcrefs.mjs resolveLeanFile."""
    hits = [f for f in FILES if f == name or f.endswith("/" + name)]
    return hits[0] if len(hits) == 1 else None


def short_name(path, like):
    """How to write `path` in prose: keep the full path if the prose used one, else the shortest unique suffix."""
    if "/" in like and resolve(like) and like == resolve(like): return path
    parts = path.split("/")
    for k in range(1, len(parts) + 1):
        cand = "/".join(parts[-k:])
        if resolve(cand) == path: return cand
    return path


_cache = {}
def lines(f):
    if f not in _cache:
        p = os.path.join(ROOT, f)
        _cache[f] = open(p, encoding="utf-8").read().split("\n") if os.path.exists(p) else None
    return _cache[f]


def text(f, a, b):
    ls = lines(f)
    if ls is None or a < 1 or b > len(ls) or b < a: return None
    return [x.strip() for x in ls[a - 1:b]]


def refs(path):
    src = open(path, encoding="utf-8").read()
    if path.endswith(".js"): src = re.sub(r"(?m)^\s*//.*$", "", src)  # code comments give examples, not references
    for m in REF.finditer(src):
        f = resolve(m.group(1))
        if not f: continue  # the build leaves it unlinked too
        a = int(m.group(3)); b = int(m.group(5)) if m.group(5) else a
        yield f, a, b


key = lambda f, a, b: f"{f}:{a}-{b}"
rel = lambda p: os.path.relpath(p, SITE_DIR or LEARN)


def load():
    return json.load(open(LOCK, encoding="utf-8")) if os.path.exists(LOCK) else {}


def save(lock):
    json.dump(dict(sorted(lock.items())), open(LOCK, "w", encoding="utf-8"), indent=1, ensure_ascii=False)


def decls():
    p = os.path.join(LEARN, "data", "decls.json")
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else []


def decl_at(f, a, b, ds):
    """The declaration whose range is exactly [a, b], or which starts at a (a statement sub-range)."""
    for d in ds:
        if d.get("file") == f and d.get("line") == a and b <= d["endLine"]: return d["name"], d["endLine"] == b
    return None, None


def lock_all():
    lock, ds, bad = {}, decls(), []
    for p in files_in(SOURCES):
        for f, a, b in refs(p):
            t = text(f, a, b)
            if t is None: bad.append(f"{rel(p)}: {f} lines {a}-{b} is outside the file"); continue
            name, whole = decl_at(f, a, b, ds)
            lock[key(f, a, b)] = {"text": t, **({"decl": name, "whole": whole} if name else {})}
    if bad: print("FAIL\n" + "\n".join(sorted(set(bad)))); sys.exit(1)
    save(lock)
    print(f"locked {len(lock)} references ({rel(LOCK)})")


def check():
    if not os.path.exists(LOCK): sys.exit(f"no lock file at {LOCK}: run tools/srcrefs_lock.py --lock first")
    lock, bad, n = load(), [], 0
    for p in files_in(SOURCES):
        for f, a, b in refs(p):
            n += 1
            k = key(f, a, b)
            if k not in lock: bad.append(f"{rel(p)}: {f} lines {a}-{b} is not in the lock (run tools/srcrefs_lock.py --lock after checking it)")
            elif text(f, a, b) != lock[k]["text"]: bad.append(f"{rel(p)}: {f} lines {a}-{b} no longer reads as when it was written (run tools/srcrefs_lock.py --remap)")
    if bad: print("FAIL\n" + "\n".join(sorted(set(bad)))); sys.exit(1)
    print(f"srcrefs_lock: ok ({n} references, {len(lock)} locked)")


def find(t, prefer, near):
    hits = []
    for f in [prefer] + [x for x in FILES if x != prefer]:
        ls = lines(f)
        if ls is None: continue
        s = [x.strip() for x in ls]
        for i in range(len(s) - len(t) + 1):
            if s[i:i + len(t)] == t: hits.append((f, i + 1))
        if hits and f == prefer: break
    if not hits: return None
    same = [h for h in hits if h[0] == prefer]
    if same: return min(same, key=lambda h: abs(h[1] - near))
    return hits[0] if len(hits) == 1 else None


def remap():
    lock, new, moved, review, lost = load(), {}, {}, [], []
    by_name = {d["name"]: d for d in decls()}
    for k, e in lock.items():
        f, rng = k.rsplit(":", 1); a, b = map(int, rng.split("-"))
        if text(f, a, b) == e["text"]: new[k] = e; continue
        hit = find(e["text"], f, a)
        if hit:
            nf, na = hit; nb = na + b - a
        elif e.get("decl") in by_name:
            d = by_name[e["decl"]]; nf, na = d["file"], d["line"]
            nb = d["endLine"] if e["whole"] else na + b - a
            review.append(f"{k} -> {nf}:{na}-{nb} (followed {e['decl']}; its text changed, re-read the prose)")
        else:
            lost.append(k); continue
        moved[k] = (nf, na, nb)
        new[key(nf, na, nb)] = {**e, "text": text(nf, na, nb)}
    def sub(m):
        f = resolve(m.group(1))
        if not f: return m.group(0)
        a = int(m.group(3)); b = int(m.group(5)) if m.group(5) else a
        if key(f, a, b) not in moved: return m.group(0)
        nf, na, nb = moved[key(f, a, b)]
        name = m.group(1) if nf == f else short_name(nf, m.group(1))
        if m.group(5): return f"{name}{m.group(2)}{na}{m.group(4)}{nb}"
        return f"{name}{m.group(2)}{na}" + (f"–{nb}" if nb != na else "")
    for p in files_in(SOURCES):
        s = open(p, encoding="utf-8").read(); s2 = REF.sub(sub, s)
        if s2 != s: open(p, "w", encoding="utf-8").write(s2)
    save(new)
    print(f"remapped {len(moved)} of {len(lock)} locked references")
    for r in review: print("review:", r)
    for k in lost: print("UNRESOLVED (text gone; rewrite the prose, then --lock):", k)
    if lost: sys.exit(2)


if __name__ == "__main__":
    {"--check": check, "--remap": remap, "--lock": lock_all}[sys.argv[1] if len(sys.argv) > 1 else "--check"]()
