# 한국사 × 한국뮤지컬 — 초등 한국사 수업 교사용 아카이브

2022 개정 사회과 한국사 성취기준(H01~H07)에 연결한 한국 창작뮤지컬 아카이브입니다.
서버·데이터베이스·로그인 없이 정적 파일만으로 동작합니다.

## 구조

```
index.html              앱 본체 (data/*.json 을 fetch)
standalone.html         데이터를 인라인한 단일 파일 (로컬에서 바로 열람용)
data/
  h.json                7건   시대·역사 주제
  works.json            42건  공개 작품
  relations.json        44건  H–작품 관계
  numbers.json          29건  확인된 대표 넘버
  sources.json          69건  출처 (내부 관리 필드 제외)
scripts/
  build_data.py         XLSX → JSON 변환 + 검증
  build_standalone.py   index.html + JSON → standalone.html
```

## 데이터 갱신

`한국사_한국뮤지컬_웹앱_최종DB_v2_포스터반영_1_.xlsx` 가 단일 원천입니다.

포스터는 `한국사_한국뮤지컬_poster_mapping_v2.json` 에서 출처 정보를 가져와 병합합니다.

```bash
SRC_XLSX=./한국사_한국뮤지컬_웹앱_최종DB_v2_포스터반영_1_.xlsx \
POSTER_JSON=./한국사_한국뮤지컬_poster_mapping_v2.json \
OUT_DIR=./data \
python3 scripts/build_data.py      # 검증 실패 시 exit 1
python3 scripts/build_standalone.py
```

`build_data.py` 가 자동 검증하는 항목:

- H 7 / 작품 42 / 관계 44 / 대표 넘버 29
- work_id 중복 0, 제외작(M19·M30·M39·M43·M46) 0
- H08·H09 노출 0
- 포스터 이미지 38 / 대체 이미지 4 / 대체 텍스트 누락 0
- 포스터 URL 불일치 0, 출처 링크 누락 0, 비 https 0
- 관계·넘버의 ID 참조 무결성
- 대표 넘버 회귀 확인 — M28 당신이 사는 세상 / M29 왕비를 정하소서 / M38 나를 태워라 / M40 내가 가겠소

빈 값은 추정해서 채우지 않습니다. 값이 없으면 UI에서 해당 섹션을 숨깁니다.

## 로컬 실행

```bash
python3 -m http.server 8000    # http://localhost:8000
```

`file://` 로 직접 열면 브라우저 보안 정책 때문에 JSON을 읽지 못합니다.
이 경우 `standalone.html` 을 사용하세요.

## 배포

정적 호스팅이면 어디든 그대로 올라갑니다 (GitHub Pages, Cloudflare Pages, Netlify 등).
빌드 단계가 필요 없으며, 저장소 루트를 그대로 게시하면 됩니다.

## 데이터 원칙

- 존재하지 않는 작품·넘버·인물·출처를 생성하지 않습니다.
- 포스터는 원 출처 서버의 이미지를 직접 참조합니다. 공개 운영 전에는 각 출처의 이용 조건을 확인하고,
  허용되는 범위에서 `assets/` 등에 직접 보관해 사용하기를 권합니다.
- 이미지 로딩에 실패하면 시대별 구분색 대체 이미지로 자동 전환되므로 화면이 비지 않습니다.
- 내부 검증 문구(추가 확인 필요, 신뢰 등급, SRC 코드 등)는 빌드 단계에서 공개 필드에서 제거됩니다.
