#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""index.html + data/*.json  →  단일 HTML 파일 (오프라인·로컬 열람용)"""
import json, os, re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILES = ["h", "works", "relations", "numbers", "sources"]

html = open(os.path.join(BASE, "index.html"), encoding="utf-8").read()
data = {f: json.load(open(os.path.join(BASE, "data", f + ".json"), encoding="utf-8")) for f in FILES}
inline = "<script>window.INLINE_DATA=" + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";</script>\n"

out = html.replace("<script>\n/* ================================================================\n   데이터 로드",
                   inline + "<script>\n/* ================================================================\n   데이터 로드", 1)
assert inline in out, "삽입 지점을 찾지 못했습니다."

dst = os.environ.get("STANDALONE_OUT", os.path.join(BASE, "standalone.html"))
open(dst, "w", encoding="utf-8").write(out)
print(f"생성: {dst}  ({len(out):,} bytes)")
for f in FILES:
    print(f"  {f}: {len(data[f])}건")
