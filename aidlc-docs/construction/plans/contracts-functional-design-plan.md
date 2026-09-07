# Functional Design Plan — UOW-0 Contracts

역할: Domain Designer | 페이즈: CONSTRUCTION | 유닛: UOW-0 Contracts (`src/aegis/contracts/`) | 작성일: 2026-09-07
상태: ✅ 승인 완료 (2026-09-07T09:14:00Z — 전 질문 A/권장 채택, 산출물 생성 완료)

## 목적
모든 Unit이 공유하는 공통 데이터 계약의 **기술 비의존 도메인 모델·비즈니스 규칙**을 확정한다. 인프라·언어 세부는 다루지 않는다(Python dataclass 구현은 Code Generation). 이 계약은 이후 5개 UOW가 의존하므로(NFR-6), 여기서 안정화한다.

## 스코프 (배정 스토리)
- **S-U4-4** 공통 판정 식별자 계약 (primary). 소비: 전 Unit·UI·CLI.
- 산출 대상 타입: `Verdict`, `ReasonCode`, `Judgment`, `AuditEvent`, `SafeLocation`, `RecommendedAction`, 차단/오류 응답 코드(`AEGIS_SECRET_BLOCKED`, `AUDIT_UNAVAILABLE` 등).

## 이미 잠긴 입력 (재질문 안 함 — C-AIDLC-2)
- `Judgment{policy_id, policy_version, policy_digest, pubkey_id, rule_id, verdict, reason_code}` (component-dependency.md §4).
- `AuditEvent`에 **원문·비밀·요청 본문·전체 URL query·원시 헤더·키·개인키·명령 인자 없음**(FR-5.2, NFR-4).
- 차단 응답: HTTP 403 `AEGIS_SECRET_BLOCKED` + event_id + rule_id + safe_location.
- 언어=Python, 직렬화=JSON(감사 JSONL + loopback IPC), snake_case.

## Part 1 — 계획 체크리스트
- [x] Step 1: 유닛 컨텍스트·스토리 분석 (완료)
- [x] Step 2: 도메인 모델·규칙 설계 범위 확정
- [x] Step 3: 아래 질문 답변 수집 (Q1~Q6 = A/권장)
- [x] Step 4: 모호성 검사 (6개 답변 단일 옵션 A, 모호·모순 없음)
- [x] Step 5: 산출물 생성 (`business-logic-model.md`, `business-rules.md`, `domain-entities.md`)

---

## 질문 (각 `[Answer]:` 에 알파벳. 권장안 표시. 없으면 `X) Other`)

### Q1: `Verdict`(판정) 값 모델
세 경계의 판정을 어떻게 표현할까요? (웹: 직접/격리/차단, 프록시: 허용/차단, cage: 실행/거부)

A) **공통 핵심 verdict enum + 경계별 세부 결정 타입 (권장)** — 공통 `Verdict = {ALLOW, BLOCK, ISOLATE, ERROR}`(닫힌 집합)를 두고, 각 경계 결정(예: 웹 `NavDecision=DIRECT|ISOLATE|BLOCK`)을 공통 verdict로 매핑. 감사·UI는 공통 verdict로 통일 조회, 경계 의미는 reason_code로 세분. [권장]

B) 경계별 완전 독립 enum — 웹/프록시/cage 각각 별도 verdict. 통일 조회 시 매핑 테이블 필요.

C) 단일 boolean(allowed) + 사유 문자열 — 최소. 격리(ISOLATE) 같은 3상태 표현 손실.

X) Other

[Answer]: A

### Q2: `ReasonCode`(사유 코드) 체계
차단·거부·오류 사유를 어떻게 식별할까요?

A) **닫힌 enum + Unit 네임스페이스 접두 (권장)** — 예: `WEB_RISKY_ACTION_BLOCKED`, `GUARD_SECRET_DETECTED`, `CAGE_SIGNATURE_INVALID`, `AUDIT_UNAVAILABLE`. 코드=식별자, 사람이 읽는 한글 메시지는 별도 매핑(UI 표시용). 신규 사유는 계약 개정으로만 추가. [권장]

B) 자유 문자열 — 유연하나 오타·불일치·조회 불가 위험, 계약 안정성 저하.

C) 숫자 코드(HTTP 유사) — 간결하나 가독성 낮고 의미 파악 어려움.

X) Other

[Answer]: A

### Q3: 식별자(`event_id`, `workflow_id`) 형식
감사 이벤트·워크플로우 식별자 형식은?

A) **event_id = 시간 정렬형(UUIDv7/ULID), workflow_id = UUIDv4 또는 호출자 제공 (권장)** — event_id는 생성 시각순 정렬 가능해 JSONL append·조회에 유리. workflow_id는 한 작업(D-1~D-3)을 묶는 상위 ID. 둘 다 전역 유일. [권장]

B) 둘 다 UUIDv4 — 유일하나 시간 정렬 불가(조회 정렬은 ts 필드로).

C) 단조 증가 정수 시퀀스 — 단일 writer면 가능하나 분산·재시작 시 취약.

X) Other

[Answer]: A

### Q4: `evidence_hash` 정의 (원문 비노출 핵심)
증거 해시를 무엇으로·어떻게 계산할까요? (FR-5.2, NFR-4)

A) **SHA-256(정규화된 비밀 없는 증거 서술자) (권장)** — 원문·비밀을 절대 입력하지 않고, 판정을 재현·대조할 수 있는 비민감 메타(예: rule_id, 탐지 위치 라벨, 정규화 방식 id, 길이/오프셋 등 비복원 정보)만 정규 직렬화 후 SHA-256. 해시로 원문 복원 불가. 검증 도구 제공. [권장]

B) SHA-256(원문) — **금지**(원문을 해시 입력으로도 다루지 않음 — 유출·오용 위험, NFR-4 위반 소지). 채택 불가.

C) 해시 생략, event_id만 — 증거 대조 불가.

X) Other

[Answer]: A

### Q5: 원문·비밀 비노출을 계약 타입 차원에서 강제하는 방식
"로그/UI에 원문·비밀 0건"(T-PRIVACY)을 어떻게 구조적으로 보장할까요?

A) **닫힌 필드 타입 + 안전 생성자만 (권장)** — `AuditEvent`를 자유 dict 없이 고정 필드(불변)로 정의하고, 생성은 해시·라벨·식별자만 받는 팩토리로 제한. 원시 본문·헤더·인자·키를 담을 필드를 아예 두지 않음(구조적으로 불가능). `target`은 `host` 또는 `command_label`만. [권장]

B) 자유 dict 허용 + 런타임 redaction 필터 — 유연하나 누락 위험, 구조적 보장 아님.

X) Other

[Answer]: A

### Q6: 스키마 버전·타임스탬프 규약
계약 진화·시간 표기 규약은?

A) **필드 `schema_version`(정수) + `ts`=RFC3339 UTC 문자열 (권장)** — 계약에 버전 필드를 넣어 이후 개정 호환 관리. 시각은 UTC RFC3339(예: `2026-09-07T09:00:00Z`). 직렬화 왕복 PBT(PBT-02/03/07/08/09) 대상. [권장]

B) 버전 없음 + epoch 정수 ts — 최소하지만 계약 진화 추적 어려움.

X) Other

[Answer]: A

---

## 제약 준수 (상시)
- NFR-6: contracts는 최하위, 어떤 Unit도 참조하지 않음. 직렬화 왕복 PBT 확립.
- NFR-4 / FR-5.2 / T-PRIVACY: 원문·비밀·인자·개인키를 타입·해시·직렬화 어디에도 담지 않음.
- C-SCOPE-1: 계약이 차단/거부/오류를 1급으로 표현(경고/통과로 대체 표현 금지).
- 이 단계는 기술 비의존 도메인 설계 — Python 구현·패키징은 Code Generation.
