#!/usr/bin/env python3
"""Generate a site's assets/config.js, index.html and scan.config.json from sites/<slug>/site.json.
Usage: python3 engine/gen.py <build-dir> <site-dir>"""
import json, os, sys, html
B, S = sys.argv[1], sys.argv[2]
# Hub-wide settings (name, URLs, credit line, comments) come from hub.json next to engine/ (see templates/hub.json).
HUB_FILE = os.environ.get("HUB_CONFIG") or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "hub.json")
HUB = {"name": "Lean projects, explained (unofficial)", "baseUrl": "", "repo": "", "indexLabel": "Index",
       "indexBlurb": "the project index", "storagePrefix": "informal", "credit": "written by Claude (AI)",
       "giscus": {"repoId": "", "category": "Announcements", "categoryId": ""}}
if os.path.exists(HUB_FILE): HUB.update(json.load(open(HUB_FILE, encoding="utf-8")))
C = json.load(open(os.path.join(S, "site.json"), encoding="utf-8"))
OK = {"Apache-2.0", "MIT", "BSD-2-Clause", "BSD-3-Clause", "GPL-3.0", "LGPL-2.1", "MPL-2.0"}
lic = C["license"]
perm = bool(lic.get("authorPermission"))  # no licence file, but the author asked for his code to be shown (b4)
allow = lic.get("spdx") in OK or perm
repo, sha = C["repo"], C["sha"]
gh = f"https://github.com/{repo}"
e = html.escape
lic_url = f"{gh}/blob/{sha}/{lic['file']}" if lic.get("file") else None
lic_link = f'<a href="{lic_url}" target="_blank" rel="noopener">{e(lic["name"])}</a>' if lic_url else ("no licence file; source shown with the author's permission" if perm else "none found in the repository")
lic["short"] = ("is published under " + lic["name"] + ", but this site does not reproduce its source") if not allow and lic_url else "has no licence file, so this site does not copy its source"
handling = ("The author asked for his source to be shown here; all rights remain with him." if perm
            else "Source reproduced on this site under that licence, with its notice." if allow
            else "So this site reproduces none of its source: it explains in prose and links to the exact lines on GitHub.")
author = f'<a href="{e(C["authorUrl"])}" target="_blank" rel="noopener">{e(C["authors"])}</a>' if C.get("authorUrl") else e(C["authors"])
banner = f'''<div class="disclaimer" role="note"><b>Unofficial explainer.</b> This is not official documentation for <a href="{gh}" target="_blank" rel="noopener">{e(repo)}</a>. It was written independently (AI-assisted) from the public source at commit <a href="{gh}/tree/{sha}" target="_blank" rel="noopener"><code>{sha[:7]}</code></a>, and may contain errors. See the original repository by {author}.<span class="lic">Licence: {lic_link}. {handling}</span></div>'''
own = C.get("ownProject")  # the hub owner's own repo (b4): same banner, worded for a project he wrote and asked to have explained
if own:
    banner = f'''<div class="disclaimer" role="note"><b>Unofficial explainer.</b> This is not official documentation for <a href="{gh}" target="_blank" rel="noopener">{e(repo)}</a>. It is an AI-assisted tour of {author}'s own project, written at his request from the public source at commit <a href="{gh}/tree/{sha}" target="_blank" rel="noopener"><code>{sha[:7]}</code></a>. He has not reviewed it line by line, and it may contain errors: the repository is the ground truth.<span class="lic">Licence: {lic_link}. {handling}</span></div>'''
snap = C.get("snapshot")  # explainer of a public website snapshot rather than a git repository (prove2me)
if snap:
    gh = snap["url"]; sha = snap["fetched"]
    lic_url = lic.get("url"); lic_link = f'<a href="{lic_url}" target="_blank" rel="noopener">{e(lic["name"])}</a>'
    handling = "This site quotes only short attributed phrases from " + e(snap["name"]) + " and links to its pages."
    banner = f'''<div class="disclaimer" role="note"><b>Unofficial explainer.</b> This is not official documentation for <a href="{gh}" target="_blank" rel="noopener">{e(snap["name"])}</a>. It was written independently (AI-assisted) from the public site as fetched on {e(sha)}, and may contain errors. See the original site by {author}.<span class="lic">Licence: {lic_link}. {handling}</span></div>'''
lang = C.get("lang", "Lean")
credit = f'The {lang} project <a href="{gh}" target="_blank" rel="noopener">{e(repo)}</a> is by {author}.'
if snap: credit = f'<a href="{gh}" target="_blank" rel="noopener">{e(snap["name"])}</a> is by {author}; each mission belongs to its captain and contributors.'
footer = (f'{credit} Licence: {lic_link}. This explainer is unofficial and AI-assisted ({HUB["credit"]}), '
          + (f'from the public site as fetched on {e(sha)}; it is not' if snap else f'from commit <code>{sha[:7]}</code>; it is not') + f' reviewed by the project\'s authors and may be wrong. {"The Lean is the ground truth" if lang == "Lean" else "The source is the ground truth"}. ' +
          f'Part of <a href="../">{HUB["indexBlurb"]}</a>. Progress is stored only in this browser.')
cfg = {"slug": C["slug"], "repo": repo, "sha": sha, "title": C["title"], "brand": C["brand"], "h1": C["h1"], "lead": C["lead"],
       "creditHtml": credit, "sizeNote": C.get("sizeNote", ""), "startNote": C.get("startNote", ""), "agentCtx": C.get("agentCtx", C["desc"]),
       "headlines": C["headlines"], "gloss": C.get("gloss", {}), "allowSource": allow, "roots": C["roots"], "ns": C.get("ns", ""),
       "headlineFiles": C.get("headlineFiles", []), "sourceRoots": C.get("sourceRoots"), "sourceExts": C.get("sourceExts"), "license": {**lic, "url": lic_url}, "bannerHtml": banner, "snapshot": snap, "footerHtml": footer, "hub": {k: HUB[k] for k in ("name", "repo", "indexLabel", "storagePrefix", "giscus")}}
if snap: cfg["sha"] = f"main/sites/{C['slug']}/snapshot"  # GitHub line links point at the quoted snapshot in the hub repo
open(os.path.join(B, "assets", "config.js"), "w", encoding="utf-8").write("// generated by engine/gen.py from site.json\nexport default " + json.dumps(cfg, ensure_ascii=False, indent=1) + ";\n")
json.dump({k: C[k] for k in ("roots", "ns", "headlines", "mathlibNamespaces", "mathlibNames", "concepts") if k in C},
          open(os.path.join(B, "scan.config.json"), "w"), indent=1)
url = f"{HUB['baseUrl']}{C['slug']}/"
src_nav = '<a href="src/index.html">Quoted statements</a>' if snap else '<a href="src/index.html">Source</a>' if allow else f'<a href="{gh}/tree/{sha}" target="_blank" rel="noopener">Source (GitHub) ↗</a>'
idx = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(C["title"])} (unofficial explainer)</title>
<meta name="description" content="{e(C["desc"])}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{e(HUB["name"])}">
<meta property="og:title" content="{e(C["title"])} (unofficial explainer)">
<meta property="og:description" content="{e(C["desc"])}">
<meta property="og:url" content="{url}">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="{e(C["title"])} (unofficial explainer)">
<meta name="twitter:description" content="{e(C["desc"])}">
<link rel="stylesheet" href="assets/style.css">
<script src="https://cdn.jsdelivr.net/npm/cytoscape@3.30.2/dist/cytoscape.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/dagre@0.8.5/dist/dagre.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/cytoscape-dagre@2.5.0/cytoscape-dagre.js"></script>
</head>
<body>
<header class="top">
  <a class="brand" href="#/">{C["brand"]}</a>
  <nav>
    <a href="#/start">Start here</a>
    <a href="#/">Proof graph</a>
    <a href="#/nodes">Nodes</a>
    {src_nav}
    {'<a href="#/roadmap">Roadmap</a>' if os.path.exists(os.path.join(S, "pages", "roadmap.md")) else ""}
    <a href="#/review">Review</a>
    <a href="#/trust">Trust</a>
    <a href="#/about">About</a>
    <a href="../">{e(HUB["indexLabel"])}</a>
    <a href="{gh}" target="_blank" rel="noopener">{"Original site" if snap else "Original repo"} ↗</a>
  </nav>
</header>
{banner}
<main id="app"><p class="loading">Loading…</p></main>
<footer>
  {footer}
</footer>
<script type="module" src="assets/app.js"></script>
</body>
</html>
'''
open(os.path.join(B, "index.html"), "w", encoding="utf-8").write(idx)
# Standard credit + licence section at the end of the About page.
ab = os.path.join(B, "pages", "about.md")
os.makedirs(os.path.dirname(ab), exist_ok=True)
txt = open(ab, encoding="utf-8").read() if os.path.exists(ab) else "# About this site\n"
txt += f'''

## Credit, licence and status

- **The project:** [{snap["name"] if snap else repo}]({gh}) by {C["authors"]}{f" ({C['authorUrl']})" if C.get("authorUrl") else ""}. Everything mathematical and every line of {lang} is theirs.
- **This explainer:** unofficial and independent. Written by Claude (AI) {f"from the public site as fetched on {sha}" if snap else f"from the public source at commit [`{sha[:7]}`]({gh}/tree/{sha})"}, {HUB.get("aboutCredit", "for [" + HUB["indexBlurb"] + "](../)")}. {"Requested by the author, but not reviewed by him line by line" if own else "Not reviewed or endorsed by the project's authors"}, and it may contain errors. Every node is `review: draft`.
- **Licence:** {f"[{lic['name']}]({lic_url})" if lic_url else lic["name"]}. {handling}
- **Corrections:** open an issue or pull request on [{HUB["repo"]}](https://github.com/{HUB["repo"]}). Authors who would like this page changed or taken down: say so there and it will be done.
'''
open(ab, "w", encoding="utf-8").write(txt)
print(f"gen: {C['slug']} allowSource={allow} licence={lic['name']}")
