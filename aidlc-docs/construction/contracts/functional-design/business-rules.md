# UOW-0 Contracts — Business Rules

작성일: 2026-09-07 | 페이즈: CONSTRUCTION → Functional Design | 유닛: UOW-0 Contracts
계약이 스스로 강제하는 규칙(검증·직렬화·불변식). 소비 Unit의 비즈니스 로직 규칙은 각 Unit Functional Design에서.

## R1. 닫힌 집합 강제 (Q1/Q2=A)
- **R1.1** `verdict`는 `{ALLOW, BLOCK, ISOLATE, ERROR}` 중 하나여야 한다. 그 외 값 역직렬화 시 거부(`COMMON_INTERNAL_ERROR` 아님 — 파싱 예외).
- **R1.2** `reason_code`는 정의된 네임스페이스 코드 집합에 속해야 한다. 미정의 코드는 거부. 신규 코드는 계약 개정(schema_version 증가 검토)으로만 추가.
- **R1.3** 경계별 결정→공통 Verdict 매핑은 계약이 제공하며 1:1 결정적이다(NavDecision/ProxyDecision/CageDecision → Verdict).

## R2. 원문·비밀 비노출 (NFR-4, FR-5.2, T-PRIVACY — Q4/Q5=A) **[Security 집행]**
- **R2.1** `AuditEvent`·`BlockResponse`·`Judgment`·`SafeLocation`·`RecommendedAction`에는 요청 본문·전체 URL query·원시 헤더·키·개인키·명령 인자·환경변수를 담는 필드가 **존재하지 않는다**(구조적 불가능).
- **R2.2** `evidence_hash`의 입력(`EvidenceDescriptor`)은 비밀·원문을 포함할 수 없다. 팩토리는 `extra` 맵의 각 값이 비민감 메타(길이·오프셋·라벨·id)임을 검증하고, 값 복원이 가능한 크기의 자유 텍스트를 거부한다.
- **R2.3** `SafeLocation.label`·`command_label`은 **라벨**이며 원문·인자가 아니다. host명·논리 명령 이름만 허용.
- **R2.4** 해시는 SHA-256이며 **원문을 해시 입력으로도 사용하지 않는다**(Q4-B 금지). 해시로 원문을 복원할 수 없어야 한다.
- **R2.5** 계약 직렬화 결과(JSON)에 위 금지 항목이 없음을 보장하는 것이 계약의 책임이다(소비 Unit이 우회 필드를 추가하면 계약 위반).

## R3. 식별자 규칙 (Q3=A)
- **R3.1** `event_id`는 전역 유일·시간 정렬 가능(UUIDv7/ULID). 단일 writer가 append 순서와 event_id 정렬을 일치시킬 수 있어야 한다(S-U5-1).
- **R3.2** `workflow_id`는 한 작업(D-1~D-3)의 세 판정을 묶는다. 서로 다른 실행은 서로 다른 workflow_id(S-C-3). 임의 다른 id로는 이벤트·세션 접근 불가(소비 측 강제, 계약은 형식만 규정).
- **R3.3** 같은 workflow_id + 서로 다른 event_id로 D-1~D-3 결과를 조회할 수 있다.

## R4. 무결성·불변식
- **R4.1** 모든 값 객체는 불변. 생성 후 필드 변경 불가.
- **R4.2** 직렬화 왕복 항등: `deserialize(serialize(x)) == x` (PBT-02/03/07/08/09). 알 수 없는 필드는 거부(엄격 파싱)해 계약 드리프트를 막는다.
- **R4.3** `schema_version`은 필수 정수. 파서는 지원하지 않는 버전을 명시적으로 거부한다(부분 해석 금지, FR-4.4의 "부분 파싱 결과 활성화 금지"와 정렬).
- **R4.4** `PolicySnapshot.digest == sha256(raw_bytes)` 여야 한다(생성 시 검증).

## R5. fail-closed 표현 (C-SCOPE-1) **[Security 집행]**
- **R5.1** 검사·판정·기록 불가 상태는 `verdict=ERROR` + 해당 `*_UNAVAILABLE` reason_code로 표현한다. 계약에는 "경고 후 통과"를 뜻하는 값이 없다(차단/거부/오류만 1급 표현).
- **R5.2** `AUDIT_UNAVAILABLE`, `GUARD_INSPECTION_UNAVAILABLE`, `CAGE_UNVERIFIED_ENV` 등은 소비 Unit이 보호 동작을 진행하지 않는 근거로 쓴다(계약은 코드 제공).

## R6. 계약 안정성
- **R6.1** contracts는 다른 Unit을 import하지 않는다(NFR-6, 순환 없음). 순수 값·열거·직렬화만.
- **R6.2** 사람이 읽는 메시지(한글)는 계약이 아닌 표시 계층 매핑(`reason-messages`)에 둔다 — 코드/메시지 분리로 국제화·변경이 계약을 깨지 않게 한다.

## 검증 매핑
- R1/R4 → PBT(직렬화·닫힌 집합), 계약 단위 테스트.
- R2 → T-PRIVACY(원문·비밀 0건), 금지 필드 부재 정적/속성 테스트.
- R3 → T-FLOW(workflow_id 통합 조회), T-AUDIT(event_id 유일·정렬).
- R5 → fail-closed 경로(T-AUDIT, D-2/D-3 거부 경로) 소비 Unit 테스트의 전제.
