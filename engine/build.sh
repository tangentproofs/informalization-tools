#!/usr/bin/env bash
# Build one explainer: engine/build.sh <slug>   ->  build/<slug>/dist  and  _site/<slug>/
# No Lean build: declarations are scanned from the submodule's source text (tools/scan_decls.py).
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
slug=$1; S=$ROOT/sites/$slug; B=$ROOT/build/$slug
[ -f "$S/site.json" ] || { echo "no $S/site.json"; exit 1; }
src=$(python3 -c "import json;print(json.load(open('$S/site.json'))['submodule'])")
export LEARN_SRC_ROOT=$ROOT/$src
want=$(python3 -c "import json;print(json.load(open('$S/site.json'))['sha'])")
have=$(git -C "$LEARN_SRC_ROOT" rev-parse HEAD 2>/dev/null || echo none)
snap=$(python3 -c "import json;print(1 if json.load(open('$S/site.json')).get('snapshot') else '')")
[ -n "$snap" ] || [ "$want" = "$have" ] || { echo "site.json sha $want != submodule $src HEAD $have"; exit 1; }
rm -rf "$B"; mkdir -p "$B/data"
cp -r "$ROOT/engine/assets" "$ROOT/engine/tools" "$ROOT/engine/schema" "$ROOT/engine/package.json" "$B/"
ln -s "$ROOT/engine/node_modules" "$B/node_modules"
cp -r "$S/nodes_src" "$B/"; mkdir -p "$B/nodes" "$B/pages"
[ -d "$S/pages" ] && cp "$S"/pages/*.md "$B/pages/" 2>/dev/null || true
python3 "$ROOT/engine/gen.py" "$B" "$S"
cd "$B"
python3 tools/scan_decls.py
python3 tools/write_nodes.py
node tools/test_progress.mjs >/dev/null && node tools/test_leanlines.mjs >/dev/null && node tools/test_statement.mjs >/dev/null
node tools/build_site.mjs
mkdir -p "$ROOT/_site/$slug"; rm -rf "$ROOT/_site/$slug"; cp -r dist "$ROOT/_site/$slug"
echo "built _site/$slug"
