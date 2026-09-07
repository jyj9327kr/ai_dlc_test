# PolicyCore (U-4) — Domain Entities

유닛: UOW-1 PolicyCore | 단계: Functional Design (기술 비의존) | 작성일: 2026-09-07
결정: Q1=A(최소 필드+확장 여지), Q2=A(인증 우선), Q3=A(상태형 키 저장소), Q5=A(순수 판정 함수), Q6=A(버전 fail-closed)

> 이 문서는 도메인 개념만 정의한다. 라이브러리·자료형 구현은 NFR/Code 단계. contracts(UOW-0)의 `Judgment`·`Verdict`·`ReasonCode.POLICY_*`·`PolicySnapshot`을 재사용한다.

## 1. 엔티티 개요

| 엔티티 | 역할 | 비고 |
|---|---|---|
| `PolicyBytes` | 검증 대상 원본 바이트열(policy.yaml raw) | 서명 검증의 유일한 입력(파싱 전) |
| `DetachedSignature` | 정책에 부착된 ML-DSA-65 서명 + 서명자 `pubkey_id` | 원본 bytes에 대한 detached 서명 |
| `SigningMessage` | 서명 검증 메시지(도메인 분리) | C-PQC-1 규칙으로 **구성**만, 저장 안 함 |
| `TrustedKey` | 신뢰 공개키 1개의 상태·유효기간 | **공개키만**(개인키 부재) |
| `KeyStore` | `pubkey_id → TrustedKey` 매핑 | 다중 active·폐기 지원(Q3) |
| `PolicyDocument` | 서명 검증 성공 후 파싱된 정책 내용 | 공통/정책 섹션 분리(Q1) |
| `VerificationOutcome` | 단계별 검증 결과의 내부 표현 | 최종적으로 contracts `Judgment`로 사상 |

## 2. 엔티티 상세

### 2.1 PolicyBytes
- **필드**: `raw: bytes`.
- **규칙**: 파싱하지 않은 상태로 서명 검증에 사용. contracts `PolicySnapshot.of(raw)`로 digest 산출(감사엔 digest만 남김, 원본 bytes는 정책 설정값이며 비밀 아님).
- **금지**: 개인키·자격증명을 담지 않음(정책 설정 파일일 뿐).

### 2.2 DetachedSignature
- **필드**: `pubkey_id: str`(서명자 식별), `signature: bytes`(ML-DSA-65 서명값).
- **규칙**: `pubkey_id`로 KeyStore를 조회해 검증에 쓸 공개키를 결정. 서명값 자체는 원본 bytes + 공개키로만 검증(HMAC/대칭키 대체 금지).

### 2.3 SigningMessage (C-PQC-1, 구성 규칙)
- **구성**: `ASCII("AEGIS-OPENSHELL-POLICY-v1") + 0x00 + PolicyBytes.raw`.
  - 고정 도메인 문자열 + **도메인 분리 바이트 `0x00`** + 원본 정책 바이트열.
- **규칙**: 검증 시점에 결정적으로 재구성. 도메인 분리 바이트로 다른 용도 서명과 혼용 불가.
- **저장 안 함**: 파생값이므로 영속화하지 않는다.

### 2.4 TrustedKey (Q3)
- **필드**: `pubkey_id: str`, `public_key: bytes`(ML-DSA-65 공개키), `status: KeyStatus{ACTIVE, REVOKED}`, `not_before`/`not_after`(유효기간, UTC), (선택) `label`(비민감).
- **규칙**:
  - **공개키만** 보유(개인키 필드 구조적 부재).
  - `ACTIVE`이고 검증 시각이 `[not_before, not_after]` 내일 때만 유효.
  - `REVOKED`는 즉시 효력(폐기 후 서명 정책 거부).

### 2.5 KeyStore (Q3)
- **필드**: `keys: Map<pubkey_id, TrustedKey>`.
- **규칙**:
  - **다중 active 허용**(키 교체 중첩기: 신·구 키 동시 신뢰).
  - `lookup(pubkey_id) -> TrustedKey | None`. 미등록 id는 `None`(→ 미신뢰).
  - 폐기·만료 판정은 조회 시점 상태·시각으로 결정(TOCTOU는 U-2 policy_digest가 별도 방어).

### 2.6 PolicyDocument (Q1 — 최소 필드 + 확장 여지)
- **필드(핵심만 모델링)**:
  - `schema_version: int` (지원 집합 밖이면 거부, Q6).
  - `policy_id: str`.
  - `policy_version: int`.
  - `common: CommonSection` — 공통(전 경계 공유) 설정의 추상 표현.
  - `policy: PolicySection` — 경계별 규칙 집합의 추상 표현(규칙 식별자 목록 수준).
  - `extra: opaque` — 알려지지 않은 필드는 불투명 통과(엄격 거부는 하되, 상세 모델링은 안 함).
- **분리 검증(FR-4.1)**: `common`과 `policy` 섹션을 **분리**해 각기 스키마 검증. 한 섹션 오류가 다른 섹션 판정을 오염시키지 않음.
- **주의**: 파싱은 **서명 검증 성공 이후에만** 수행(Q2, authenticate-before-parse).

### 2.7 VerificationOutcome → Judgment
- **내부 표현**: `{stage, ok, reason_code, rule_id?}`.
- **최종 사상**: contracts `Judgment{policy_id, policy_version, policy_digest, pubkey_id, verdict, reason_code, rule_id?}`.
  - 성공: `verdict=ALLOW`(정책 신뢰됨), `reason_code=POLICY_OK`.
  - 예상된 검증 실패: `verdict=BLOCK`, `reason_code=POLICY_UNTRUSTED_KEY | POLICY_SIGNATURE_INVALID | POLICY_SCHEMA_INVALID | POLICY_VERSION_UNSUPPORTED`.
  - 내부 오류(검증 자체 불가): `verdict=ERROR`, `reason_code=COMMON_INTERNAL_ERROR`(fail-closed).

## 3. 금지·비노출 (보안, 집행)
- 어떤 엔티티도 **개인키**를 담지 않는다(공개키 전용).
- `Judgment`·감사 경로에는 `policy_digest`·`pubkey_id`·`reason_code`만(원문 정책 바이트·키 원문 미노출은 감사 계층 책임, 여기선 digest만 전달).
- 서명 검증은 실제 ML-DSA-65로만 성립 — mock 성공·HMAC 대체·검증 우회 표현을 도메인에 두지 않는다.

## 4. 관계 (텍스트)
- `KeyStore` 1 — * `TrustedKey`.
- `DetachedSignature.pubkey_id` → `KeyStore.lookup` → `TrustedKey.public_key`.
- (`PolicyBytes` + `SigningMessage` + `TrustedKey.public_key`) → 서명 검증 → 성공 시 `PolicyBytes` 파싱 → `PolicyDocument`.
- 각 단계 결과 → `VerificationOutcome` → `Judgment`(contracts).
