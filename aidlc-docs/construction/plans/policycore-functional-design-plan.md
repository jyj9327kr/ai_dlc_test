# Functional Design Plan — UOW-1 PolicyCore (U-4)

역할: Functional Design Lead | 페이즈: CONSTRUCTION → Functional Design | 유닛: UOW-1 PolicyCore (U-4) | 작성일: 2026-09-07
상태: ✅ 답변 완료 (Q1~Q6 = A, 사용자 '모두 권장대로') — 산출물 생성

## 유닛 컨텍스트
- **유닛**: UOW-1 PolicyCore (U-4, `src/aegis/policy/`). Q2=A 순서 두 번째 유닛(신뢰 앵커).
- **책임**: 공통/정책 스키마 분리 검증(FR-4.1), **ML-DSA-65 원본 bytes 서명 검증**(FR-4.2, 서명 메시지 = `ASCII("AEGIS-OPENSHELL-POLICY-v1") + 0x00 + policy.yaml raw bytes`), 신뢰키 교체·폐기(FR-4.3), 판정 산출(FR-4.4).
- **스토리**: S-U4-1(스키마 분리 검증), S-U4-2(ML-DSA-65 서명 검증), S-U4-3(신뢰키 교체·폐기), S-U4-4(판정 산출·계약 소비, shared).
- **의존**: `contracts`(UOW-0, 완료). 소비자: U-2/U-3/U-1이 `Judgment`를 받아 fail-closed 분기.
- **선행 검증**: **V-2**(liboqs ML-DSA-65) — 통과 전 관련 P0 완료 표시 금지.
- **보안 불변(집행, 완화 없음)**: 실행 환경엔 **공개키만**. HMAC 대체·mock 성공·서명 검증 우회 금지. 1비트 변조 시 검증 실패. 미지원 버전·미신뢰 키·무효 서명은 fail-closed 거부(C-SCOPE-1, C-PQC-1).
- **이 단계는 기술 비의존**: liboqs·라이브러리 선택은 NFR Requirements 단계에서 결정. 여기서는 도메인·비즈니스 로직만.

## 설계 입력 (확정)
- unit-of-work.md §UOW-1, story-map §UOW-1, contracts(`Judgment`, `PolicySnapshot`, `Verdict`, `ReasonCode.POLICY_*`, `ContractError`), C-PQC-1(서명 메시지·ML-DSA-65 NIST cat 3).

---

## 컨텍스트 질문 (A/B/C + 기타, `[Answer]: A` 태그에 답변)

권장안은 각 질문의 A입니다. "모두 권장대로"로 일괄 승인하실 수 있습니다.

### Q1. 정책 문서 도메인 모델의 상세도 (FR-4.1 공통/정책 스키마 분리)

A) **최소 필드 집합 모델링 + 확장 여지** — 검증·판정에 필요한 핵심 필드(`policy_id`, `policy_version`, 공통 섹션·정책 섹션 구분, 규칙 집합의 추상 식별자)만 도메인 엔티티로 정의하고, 나머지는 불투명하게 통과. MVP 핵심 검증 경로에 집중. (권장)

B) 전체 policy.yaml 스키마를 상세 모델링 — 모든 규칙 타입·필드를 엔티티로 정의.

C) 정책 내용을 불투명 bytes로만 취급 — 구조 검증 최소화, 서명·버전만.

X) 기타: 자유 기술

[Answer]: A

### Q2. 검증 순서 — 서명 검증 vs 스키마 검증 (보안 신뢰 경계)

A) **인증 우선(authenticate-before-parse)** — 원본 bytes에 대해 신뢰키·ML-DSA-65 서명을 먼저 검증하고, **성공한 경우에만** 파싱·스키마 검증 수행. 신뢰되지 않은 입력을 파서에 최소 노출(공격면 축소). (권장)

B) 스키마 검증 먼저 → 서명 검증.

C) 서명·스키마를 독립 수행 후 모두 통과 요구(순서 무의미).

X) 기타: 자유 기술

[Answer]: A

### Q3. 신뢰키 저장소 모델 (FR-4.3 교체·폐기)

A) **`pubkey_id → {공개키, 상태(active/revoked), 유효기간}` 매핑** — 다중 active 허용(교체 중첩기), revoked·만료 키로 서명된 정책은 거부. 폐기는 상태 전이로 표현(즉시 효력). (권장)

B) 단일 active 키만 — 교체 시 즉시 치환, 이전 키 무효.

C) active 공개키 목록만 — 폐기 개념 없이 목록에서 제거.

X) 기타: 자유 기술

[Answer]: A

### Q4. 판정 산출 — 다중 실패 시 평가 순서·reason_code (FR-4.4)

A) **결정적 우선순위로 첫 실패에서 단락(short-circuit)**, 해당 단계의 `POLICY_*` reason_code 부여. Q2=A와 정합하는 순서: 미신뢰/폐기 키(`POLICY_UNTRUSTED_KEY`) → 서명 무효(`POLICY_SIGNATURE_INVALID`) → 스키마 무효(`POLICY_SCHEMA_INVALID`) → 버전 미지원(`POLICY_VERSION_UNSUPPORTED`). 전부 통과 시 `POLICY_OK`. (권장)

B) 모든 검사를 수행한 뒤 실패 목록을 집계, 대표 코드 선택.

C) 첫 실패 단락하되 순서를 스키마 → 서명 → 키로.

X) 기타: 자유 기술

[Answer]: A

### Q5. PolicyCore 인터페이스·부수효과 (S-U4-4 계약 소비)

A) **순수 판정 함수** — `verify_policy(raw_bytes, keystore) -> Judgment` 반환, 부수효과 없음. 감사 기록은 호출자(U-2/U-3/U-1)가 수행. 예상된 실패(미신뢰키·무효 서명 등)는 예외가 아니라 `Judgment(verdict=BLOCK/ERROR, reason_code=...)`로 신호. 내부 오류(검증 자체 불가)만 fail-closed로 `verdict=ERROR`. (권장)

B) PolicyCore가 판정 후 감사 기록까지 직접 수행.

C) 실패 시 예외 raise, 성공 시 `Judgment` 반환.

X) 기타: 자유 기술

[Answer]: A

### Q6. 버전 호환성 정책 (FR-4.4 / 부분 해석 금지)

A) **지원 version 집합 명시, 미지원 version은 `POLICY_VERSION_UNSUPPORTED`로 fail-closed 거부** — 부분 해석·상위 호환 추정 금지. (권장)

B) 상위 호환 — 미지원 버전도 알려진 필드만 해석.

C) 버전 무시.

X) 기타: 자유 기술

[Answer]: A

---

## 생성 단계 (승인·답변 후 실행, 체크박스)

- [x] **Step FD-1 — 도메인 엔티티**: `domain-entities.md` — `PolicyDocument`(공통/정책 섹션 구분, Q1), `TrustedKey`/`KeyStore`(상태·유효기간, Q3), `SigningMessage`(C-PQC-1 구성 규칙), `VerificationOutcome`→`Judgment`(계약 재사용). 금지: 개인키·원문 비밀 필드 부재 확인.
- [x] **Step FD-2 — 비즈니스 규칙**: `business-rules.md` — R: 서명 메시지 구성(도메인 분리 바이트 `0x00`), 1비트 변조 실패, 인증-우선 순서(Q2), 키 상태 전이·폐기(Q3), 평가 우선순위·reason_code 매핑(Q4), 버전 fail-closed(Q6), 공개키 전용·HMAC/mock 금지(보안 집행).
- [x] **Step FD-3 — 비즈니스 로직 모델**: `business-logic-model.md` — `verify_policy` 판정 플로우(입력→키 조회→서명 검증→파싱→스키마→버전→Judgment), 오류→fail-closed 매핑, 소비자 통합 지점(U-2/U-3/U-1), PBT 대상(서명 bytes 왕복·1비트 변조·경계값).

## 스토리 추적성
| Step | 스토리 | FR | 검증 |
|---|---|---|---|
| FD-1~3 | S-U4-1 | FR-4.1 | T-SIGN |
| FD-2~3 | S-U4-2 | FR-4.2, NFR-3 | T-SIGN(+PBT) |
| FD-1~2 | S-U4-3 | FR-4.3 | T-KEY |
| FD-3 | S-U4-4 | FR-4.4 | T-FLOW |

## 범위·제약 (상시)
- 기술 비의존(라이브러리 결정은 NFR Requirements). 보안 완화 없음(공개키 전용·서명 우회/mock/HMAC 금지, C-SCOPE-1/C-PQC-1).
- 문서는 `aidlc-docs/construction/policycore/functional-design/`에만. 실제 키·개인키·원문 비밀을 문서에 두지 않음(합성/설명만).
