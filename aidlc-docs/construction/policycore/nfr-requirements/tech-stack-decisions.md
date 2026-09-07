# PolicyCore (U-4) — Tech Stack Decisions

유닛: UOW-1 PolicyCore | 단계: NFR Requirements | 작성일: 2026-09-07
결정: Q1~Q6 = A. 원칙: 최소 의존, 공개키 전용, 실제 PQC 검증(mock/HMAC 금지).

## 1. 결정 요약

| # | 항목 | 결정 | 근거 |
|---|---|---|---|
| Q1 | ML-DSA-65 검증 라이브러리 | **liboqs (OQS) via `oqs-python`** | V-2 게이트 명시 구현, NIST 표준 ML-DSA, 실제 PQC |
| Q2 | 정책 파서 | **PyYAML `yaml.safe_load`** | 안전 로더(임의 객체 생성 없음), 인증 후에만 파싱 |
| Q3 | 성능 NFR | `[Deferred:perf-NFR]` | MVP 동작 확인, 수치 목표 미설정 |
| Q4 | 신뢰키 저장소 | `config/trusted-keys/`(공개키+매니페스트) | 공개키 전용, 읽기 전용 로드 |
| Q5 | 의존성 정책 | 최소 3rd-party(`oqs-python`+`PyYAML`) | 검증에 필수, 그 외 stdlib |
| Q6 | PBT | 서명 검증군 blocking | PBT Partial 집행 |

## 2. 런타임 의존성 (최소, Q5=A)

| 패키지 | 용도 | 검증 목적 | 비고 |
|---|---|---|---|
| `oqs-python` (liboqs) | ML-DSA-65 서명 검증 | NFR-PC-1, S-U4-2 | 검증 전용, 공개키만 사용. 네이티브 liboqs 필요(V-2 smoke로 확인) |
| `PyYAML` | policy.yaml 파싱(`safe_load`) | FR-4.1, S-U4-1 | 서명 검증 성공 후에만 호출 |
| (stdlib) `hashlib` | policy_digest(sha256) | NFR-PC-2 | contracts와 동일 |
| (stdlib) `datetime` | 키 유효기간 판정(UTC) | FR-4.3 | — |

- **개인키 라이브러리·서명 생성 경로 없음**(공개키 검증만).
- contracts(UOW-0)는 zero 3rd-party 유지. PolicyCore만 위 2개 의존을 추가하며, 이는 실제 PQC 검증·정책 파싱에 불가피.
- 개발 의존: 기존 `pytest`·`hypothesis` 재사용(PBT).

## 3. 패키징 반영
- `pyproject.toml`에 PolicyCore 의존 추가: `pyyaml`, `oqs`(설치명은 배포 시점 확정 — `oqs-python`/liboqs 바인딩). 네이티브 liboqs 부재 시 import 실패는 fail-closed(검증 불가 → `COMMON_INTERNAL_ERROR`)로 처리하고 V-2 smoke가 사전 진단.
- 선택적 extras로 분리 검토(`aegis[policy]`) — 확정은 Code Generation 계획에서.

## 4. 신뢰키 저장소 (Q4=A)
- 위치: `config/trusted-keys/`.
- 구성: 공개키 자료 + 매니페스트(`pubkey_id`, `status: active|revoked`, `not_before`, `not_after`). 매니페스트는 YAML(Q2 파서 재사용).
- 개인키는 저장소·실행 환경에 부재. 서명 생성은 오프라인 관리(AEGIS 범위 밖).
- 로드는 읽기 전용. 로드 실패·형식 오류는 fail-closed(신뢰키 없음 → 모든 정책 `POLICY_UNTRUSTED_KEY`).

## 5. 보안·게이팅 연계
- **V-2**(liboqs ML-DSA-65) smoke test 통과 전 S-U4-2 등 P0 완료 표시 금지(WSL2 환경 게이팅).
- 실제 키·개인키를 저장소·문서·테스트에 반입 금지 — **합성/절대 무효 키만**.
- mock 검증 성공·HMAC 대체·TLS 무관(PolicyCore는 로컬 검증) — 서명 우회 경로 없음(C-PQC-1, C-SCOPE-1).
