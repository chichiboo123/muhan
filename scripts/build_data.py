#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
한국사 × 한국뮤지컬 웹앱 — 데이터 빌드 스크립트
  한국사_한국뮤지컬_웹앱_최종DB_v1.xlsx  →  data/*.json
빌드 단계에서만 실행한다. 브라우저는 생성된 JSON만 읽는다.
"""
import json, re, sys, os
from openpyxl import load_workbook

SRC = os.environ.get("SRC_XLSX", "/mnt/user-data/uploads/한국사_한국뮤지컬_웹앱_최종DB_v2_포스터반영_1_.xlsx")
POSTER = os.environ.get("POSTER_JSON", "/mnt/user-data/uploads/한국사_한국뮤지컬_poster_mapping_v2.json")
OUT = os.environ.get("OUT_DIR", "/home/claude/site/data")

ARRAY_FIELDS = {"h_ids", "h_topics", "tags", "relation_basis"}
NUM_FIELDS = {"sort_order", "h_sort"}
BOOL_FIELDS = {"display"}

# 공개 화면에 노출하면 안 되는 내부 검증 표현 (프롬프트 12항)
BANNED = [
    r"추가\s*확인\s*필요", r"기존\s*DB\s*후보", r"재검증", r"내부\s*검증",
    r"미확인[-–]\S*", r"사용자\s*지정[-–]\S*", r"신뢰\s*등급\s*[A-C][+\-]?",
    r"\bSRC\d{3}\b",
]
BANNED_RE = re.compile("|".join(BANNED))

# 사용자에게 그대로 보여주는 텍스트 필드
PUBLIC_TEXT = {
    "synopsis", "fact_fiction_note", "curriculum_connection", "number_context",
    "number_history_connection", "lesson_activity", "lesson_question", "caution",
    "connection_summary", "context", "history_connection",
}


def sanitize(text):
    """내부 검증 문구가 들어간 문장만 제거하고 나머지는 원문 그대로 둔다."""
    if not text or not BANNED_RE.search(text):
        return text, False
    parts = re.split(r"(?<=[.!?])\s+", text)
    kept = [p for p in parts if p.strip() and not BANNED_RE.search(p)]
    out = " ".join(kept).strip()
    return (out or None), (out != text.strip())


def norm(key, val):
    if val is None:
        return None
    if isinstance(val, str):
        val = val.strip()
        if val == "":
            return None
    if key in BOOL_FIELDS:
        return str(val).upper() == "Y"
    if key in NUM_FIELDS:
        try:
            return int(val)
        except (TypeError, ValueError):
            return None
    if key in ARRAY_FIELDS and isinstance(val, str):
        return [p.strip() for p in re.split(r"[|/]", val) if p.strip()]
    return val


def read_sheet(wb, name, header_row):
    ws = wb[name]
    hdr = [ws.cell(row=header_row, column=c).value for c in range(1, ws.max_column + 1)]
    rows = []
    for r in range(header_row + 1, ws.max_row + 1):
        rec = {}
        for i, h in enumerate(hdr):
            if not h:
                continue
            rec[h] = norm(h, ws.cell(row=r, column=i + 1).value)
        if rec.get(hdr[0]):
            rows.append(rec)
    return rows


def main():
    wb = load_workbook(SRC, data_only=True)
    stripped = []

    h_rows = read_sheet(wb, "H", 4)
    works = read_sheet(wb, "작품", 4)
    rels = read_sheet(wb, "관계", 4)
    nums = read_sheet(wb, "대표넘버", 4)
    srcs = read_sheet(wb, "출처", 4)

    # display=Y 만 공개
    works = [w for w in works if w.get("display") is True]

    # 내부 검증 문구 제거
    for coll, label in ((works, "작품"), (rels, "관계"), (nums, "대표넘버")):
        for rec in coll:
            for k in list(rec.keys()):
                if k in PUBLIC_TEXT and isinstance(rec[k], str):
                    new, changed = sanitize(rec[k])
                    if changed:
                        stripped.append(f"{label} {rec.get('work_id') or rec.get('relation_id')} · {k}")
                    rec[k] = new

    # ---------- 포스터 매핑 병합 ----------
    poster_mismatch, poster_extra = [], []
    if os.path.exists(POSTER):
        pmap = {p["work_id"]: p for p in json.load(open(POSTER, encoding="utf-8"))}
        wids = {w["work_id"] for w in works}
        poster_extra = [k for k in pmap if k not in wids]
        for w in works:
            pm = pmap.get(w["work_id"])
            if not pm:
                continue
            purl = pm.get("poster_url") or None
            if purl and w.get("poster_url") and purl != w["poster_url"]:
                poster_mismatch.append(w["work_id"])
            # 이미지 URL은 XLSX 값을 유지하고, 매핑에만 있는 출처 정보를 덧붙인다
            if purl and not w.get("poster_url"):
                w["poster_url"] = purl
            if pm.get("poster_alt") and not w.get("poster_alt"):
                w["poster_alt"] = pm["poster_alt"]
            w["poster_source"] = pm.get("poster_source") or None
            w["poster_source_url"] = pm.get("poster_source_url") or None

    # 출처는 내부 관리용 필드(reliability, memo)를 공개 파일에서 제외
    srcs_pub = [{k: v for k, v in s.items() if k not in ("reliability", "memo", "checked_date")} for s in srcs]

    os.makedirs(OUT, exist_ok=True)
    files = {
        "h.json": h_rows,
        "works.json": works,
        "relations.json": rels,
        "numbers.json": nums,
        "sources.json": srcs_pub,
    }
    for fn, data in files.items():
        with open(os.path.join(OUT, fn), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1)

    # ---------- 검증 ----------
    EXCLUDED = {"M19", "M30", "M39", "M43", "M46"}
    NUM_FIX = {"M28": "당신이 사는 세상", "M29": "왕비를 정하소서",
               "M38": "나를 태워라", "M40": "내가 가겠소"}
    wid = {w["work_id"] for w in works}
    checks = []

    def ck(name, actual, expect):
        ok = actual == expect
        checks.append((name, expect, actual, "통과" if ok else "실패"))
        return ok

    ck("H 수", len(h_rows), 7)
    ck("작품 수", len(works), 42)
    ck("관계 수", len(rels), 44)
    ck("대표 넘버 수", len(nums), 29)
    ck("work_id 중복", len(works) - len(wid), 0)
    ck("제외 작품 포함", len(wid & EXCLUDED), 0)
    ck("H08/H09 노출", sum(1 for w in works for h in (w.get("h_ids") or []) if h in ("H08", "H09")), 0)
    ck("관계 → 작품 참조 오류", sum(1 for r in rels if r["work_id"] not in wid), 0)
    hid = {h["h_id"] for h in h_rows}
    ck("관계 → H 참조 오류", sum(1 for r in rels if r["h_id"] not in hid), 0)
    ck("넘버 → 작품 참조 오류", sum(1 for n in nums if n["work_id"] not in wid), 0)
    ck("포스터 이미지 수", sum(1 for w in works if w.get("poster_url")), 38)
    ck("포스터 fallback 수", sum(1 for w in works if not w.get("poster_url")), 4)
    ck("포스터 대체 텍스트 누락", sum(1 for w in works if not w.get("poster_alt")), 0)
    ck("포스터 URL 불일치", len(poster_mismatch), 0)
    ck("매핑에만 있는 work_id", len(poster_extra), 0)
    ck("포스터 출처 링크 누락", sum(1 for w in works if w.get("poster_url") and not w.get("poster_source_url")), 0)
    ck("http 포스터(비 https)", sum(1 for w in works if (w.get("poster_url") or "").startswith("http://")), 0)

    wmap = {w["work_id"]: w for w in works}
    for k, v in NUM_FIX.items():
        ck(f"{k} 대표 넘버", (wmap.get(k) or {}).get("representative_number"), v)

    print("=" * 62)
    print(f"{'검사':<26}{'기대':>12}{'실제':>12}{'결과':>8}")
    print("-" * 62)
    for n, e, a, r in checks:
        print(f"{n:<26}{str(e):>12}{str(a):>12}{r:>8}")
    print("=" * 62)
    for fn, data in files.items():
        print(f"  data/{fn:<16} {len(data):>3}건")
    if stripped:
        print("\n내부 검증 문구를 제거한 필드:")
        for s in stripped:
            print("  -", s)

    failed = [c for c in checks if c[3] == "실패"]
    if failed:
        print("\n검증 실패:", [c[0] for c in failed])
        sys.exit(1)
    print("\n전체 검증 통과")


if __name__ == "__main__":
    main()
