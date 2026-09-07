# UOW-0 Contracts — Domain Entities

작성일: 2026-09-07 | 페이즈: CONSTRUCTION → Functional Design | 유닛: UOW-0 Contracts
기술 비의존 도메인 모델. Python 구현·직렬화 라이브러리 선택은 Code Generation에서. 결정: Q1~Q6 = A(권장).

## 0. 원칙
- `contracts`는 **최하위 공유 계약**(NFR-6): 다른 어떤 Unit도 참조하지 않는다.
- 모든 엔티티는 **불변(값 객체)**, JSON 직렬화 가능(snake_case), 직렬화 왕복 항등(PBT-02/03/07/08/09).
- **원문·비밀 비노출**(NFR-4, FR-5.2, T-PRIVACY): 어떤 엔티티도 요청 본문·전체 URL query·원시 헤더·키·개인키·명령 인자를 담는 필드를 두지 않는다(구조적 불가능, Q5=A).

## 1. 열거형 (닫힌 집합)

### 1.1 Verdict (공통 판정 — Q1=A)
| 값 | 의미 | 사용 경계 |
|---|---|---|
| `ALLOW` | 허용/정상 진행 | 프록시 전달, cage 실행, 웹 직접 |
| `BLOCK` | 차단(전송·실행·행동 금지) | 프록시 403, cage 거부, 웹 위험 액션·탐색 차단 |
| `ISOLATE` | 원격 격리로 전환(로컬 직접 실행 금지) | 웹 탐색 |
| `ERROR` | 검사·판정 불가 → fail-closed | 전 경계 (감사/검증 실패 등) |

- 경계별 세부 결정은 별도 값 타입으로 두고 **공통 Verdict로 매핑**한다:
  - `NavDecision = DIRECT | ISOLATE | BLOCK` → Verdict: DIRECT→ALLOW, ISOLATE→ISOLATE, BLOCK→BLOCK.
  - `ProxyDecision = FORWARD | BLOCK | REJECT` → FORWARD→ALLOW, BLOCK→BLOCK, REJECT→BLOCK(사유 코드로 413/415/400/503 구분).
  - `CageDecision = RUN | DENY` → RUN→ALLOW, DENY→BLOCK.
- 감사·UI 통합 조회는 공통 Verdict 기준, 세부 의미는 `reason_code`로 구분.

### 1.2 ReasonCode (사유 코드 — Q2=A, 닫힌 enum + Unit 네임스페이스)
식별자만 계약에 고정. 사람이 읽는 한글 메시지는 UI 표시용 별도 매핑(`reason-messages`, 계약 아님). 신규 사유는 계약 개정으로만 추가.

| 네임스페이스 | 예시 코드 | 연결 |
|---|---|---|
| `COMMON_` | `COMMON_OK`, `COMMON_INTERNAL_ERROR` | 전체 |
| `POLICY_` | `POLICY_SIGNATURE_INVALID`, `POLICY_SCHEMA_INVALID`, `POLICY_UNTRUSTED_KEY`, `POLICY_VERSION_UNSUPPORTED` | U-4 |
| `AUDIT_` | `AUDIT_UNAVAILABLE`, `AUDIT_EVIDENCE_UNCOMPUTABLE` | U-5 |
| `GUARD_` | `GUARD_SECRET_DETECTED`, `GUARD_PROXY_BYPASS`, `GUARD_BODY_TOO_LARGE`(413), `GUARD_UNSUPPORTED_MEDIA`(415), `GUARD_MALFORMED_BODY`(400), `GUARD_INSPECTION_UNAVAILABLE`(503), `GUARD_UNSUPPORTED_DESTINATION` | U-3 |
| `CAGE_` | `CAGE_SIGNATURE_INVALID`, `CAGE_POLICY_MUTATED`(TOCTOU), `CAGE_PERMISSION_DENIED`, `CAGE_UNVERIFIED_ENV` | U-2 |
| `WEB_` | `WEB_RISKY_ACTION_BLOCKED`, `WEB_SSRF_BLOCKED`, `WEB_ISOLATION_FAILED`, `WEB_SESSION_INVALID` | U-1 |

- `AEGIS_SECRET_BLOCKED`는 U-3 차단 응답의 **와이어 코드**(HTTP 403 body)이며, 내부 reason_code는 `GUARD_SECRET_DETECTED`로 대응.

### 1.3 Unit (출처 식별)
`CONTRACTS | POLICY | AUDIT | GUARD | CAGE | WEB | CONTROL` — AuditEvent의 `unit` 필드.

### 1.4 ComponentStatus (FR-0.2, S-C-2 — 4구분)
`PREPARING | PROTECTING | BLOCKED | DISABLED`.

## 2. 값 객체 (엔티티)

### 2.1 PolicySnapshot
검증 대상이 된 정책의 불변 스냅샷(TOCTOU 방지, S-U2-2).
| 필드 | 타입 | 설명 |
|---|---|---|
| `raw_bytes` | bytes | policy.yaml 원본 바이트(정책 본문 — 비밀 아님, 검증 대상) |
| `digest` | str | `sha256(raw_bytes)` hex |
> raw_bytes는 정책 설정값이며 비밀·자격증명이 아니다. 서명 검증 메시지 구성에만 사용, 감사엔 `digest`만 남긴다.

### 2.2 Judgment (S-U4-4 — 잠긴 필드)
정책 판정 결과. 모든 Unit이 동일 의미로 사용.
| 필드 | 타입 | 설명 |
|---|---|---|
| `policy_id` | str | 정책 논리 식별자 |
| `policy_version` | int | 정책 버전 |
| `policy_digest` | str | 적용된 스냅샷 digest(검증본=적용본 증거) |
| `pubkey_id` | str | 검증에 쓰인 신뢰 공개키 id |
| `rule_id` | str \| null | 판정 근거 규칙 id(해당 시) |
| `verdict` | Verdict | 공통 판정 |
| `reason_code` | ReasonCode | 사유 |

### 2.3 SafeLocation
차단·격리 시 사용자가 안전하게 이동/확인할 위치의 **비민감 식별자**.
| 필드 | 타입 | 설명 |
|---|---|---|
| `kind` | `HOST \| COMMAND_LABEL \| SESSION \| FIELD_LABEL` | 위치 종류 |
| `label` | str | 비민감 라벨(host명, command_label 등 — 원문·인자 아님) |

### 2.4 RecommendedAction
| 필드 | 타입 | 설명 |
|---|---|---|
| `action_code` | `RETRY_ISOLATED \| REMOVE_SECRET_RETRY \| REOPEN_SESSION \| CONTACT_ADMIN \| NONE` | 권장 행동 코드 |
> UI 한글 문구는 별도 매핑. 계약엔 코드만.

### 2.5 AuditEvent (S-U5-1/2 — Q5=A 닫힌 필드, 안전 생성자만)
| 필드 | 타입 | 설명 |
|---|---|---|
| `schema_version` | int | 계약 버전(Q6=A) |
| `event_id` | str | 시간 정렬형 유일 id(UUIDv7/ULID, Q3=A) |
| `workflow_id` | str | 상위 작업 id(D-1~D-3 묶음) |
| `unit` | Unit | 출처 |
| `ts` | str | RFC3339 UTC(Q6=A) |
| `verdict` | Verdict | 공통 판정 |
| `reason_code` | ReasonCode | 사유 |
| `target` | SafeLocation | `host` 또는 `command_label`만(원문 없음) |
| `recommended_action` | RecommendedAction | 권장 행동 |
| `evidence_hash` | str | SHA-256(비밀 없는 증거 서술자), Q4=A |
| `policy_digest` | str \| null | 관련 정책 스냅샷 digest(해당 시) |
| `pubkey_id` | str \| null | 관련 신뢰키 id(해당 시) |

**금지 필드(구조적으로 없음)**: request_body, url_query, raw_headers, secret_value, private_key, command_args, env. 생성은 팩토리(`AuditEvent.create(...)`)로만 하며 위 값을 받는 인자를 두지 않는다.

### 2.6 EvidenceDescriptor (evidence_hash 입력 — Q4=A)
`evidence_hash = sha256(canonical_json(EvidenceDescriptor))`. **비밀·원문 미포함.**
| 필드 | 타입 | 설명 |
|---|---|---|
| `rule_id` | str \| null | 근거 규칙 |
| `location_label` | str \| null | 탐지 위치 라벨(예: `body.json.$.messages[2]`, 값 아님) |
| `normalization_id` | str \| null | 적용 정규화 방식 식별자 |
| `match_length` | int \| null | 매칭 길이(값 복원 불가) |
| `match_offset` | int \| null | 오프셋(값 복원 불가) |
| `extra` | map<str,str/int> | 비민감 메타만(생성 시 검증) |

### 2.7 BlockResponse (U-3 와이어 — S-U3-3)
HTTP 403 body 계약.
| 필드 | 타입 | 설명 |
|---|---|---|
| `code` | str | `AEGIS_SECRET_BLOCKED` |
| `event_id` | str | 대응 AuditEvent |
| `rule_id` | str | 근거 규칙 |
| `safe_location` | SafeLocation | 안전 위치 |

## 3. 관계 (텍스트)
- `AuditEvent` → 참조: `EvidenceDescriptor`(해시로만), `SafeLocation`, `RecommendedAction`, `Verdict`, `ReasonCode`, `Unit`.
- `Judgment` → `Verdict`, `ReasonCode`; 근거 `PolicySnapshot.digest`.
- `BlockResponse` → `SafeLocation`, `event_id`(AuditEvent).
- 계약은 **행동·로직 없음**(순수 값). 검증·판정·기록 로직은 소비 Unit(U-4/U-5/...)에 있음.

## 4. PBT 대상 (Partial 강제)
- 모든 값 객체: `deserialize(serialize(x)) == x` (직렬화 왕복 항등, PBT-02/03/07/08/09).
- ReasonCode/Verdict: 닫힌 집합 밖 값 역직렬화 시 거부.
- EvidenceDescriptor: 임의 비밀 문자열을 넣어도 필드 구조상 담기지 않음(속성: 금지 필드 부재).
