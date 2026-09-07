# UOW-0 Contracts — Business Logic Model

작성일: 2026-09-07 | 페이즈: CONSTRUCTION → Functional Design | 유닛: UOW-0 Contracts
계약 모듈의 기술 비의존 로직(직렬화·검증·매핑·해시 서술). 무거운 비즈니스 판정 로직은 소비 Unit에.

## 1. 모듈 책임 요약
`contracts`는 **행동이 거의 없는 계약 계층**이다. 제공 기능은:
1. 값 객체 정의(domain-entities.md)와 **엄격 직렬화/역직렬화**(JSON, snake_case).
2. **닫힌 집합 검증**(Verdict/ReasonCode).
3. 경계 결정 → 공통 `Verdict` **매핑** 함수.
4. **evidence_hash 계산**(비밀 없는 `EvidenceDescriptor` → SHA-256), 검증 도구.
5. **AuditEvent 안전 팩토리**(금지 값 인자 부재).

## 2. 핵심 흐름 (기술 비의존)

### 2.1 직렬화 왕복 (R4.2 / PBT)
```
serialize(x)      : 값 객체 → canonical JSON(정렬된 키, UTF-8)
deserialize(bytes): JSON → 값 객체 (엄격: 미지원 schema_version·미정의 enum·알 수 없는 필드 거부)
불변식            : deserialize(serialize(x)) == x
```
- canonical JSON은 감사 evidence_hash·행 무손상(S-U5-1)·비교 재현성의 기반.

### 2.2 경계 결정 → 공통 Verdict 매핑 (R1.3)
```
map_nav(DIRECT|ISOLATE|BLOCK)        -> ALLOW|ISOLATE|BLOCK
map_proxy(FORWARD|BLOCK|REJECT)      -> ALLOW|BLOCK|BLOCK   (REJECT는 reason_code로 413/415/400/503 구분)
map_cage(RUN|DENY)                   -> ALLOW|BLOCK
```
- 결정적·전역 함수. 감사·UI가 공통 Verdict로 통일 조회.

### 2.3 evidence_hash 계산 (Q4=A / R2.2 / R2.4)
```
build_evidence(descriptor): 
   1) descriptor의 각 필드가 비민감(길이·오프셋·라벨·id·정규화방식)인지 검증
   2) 자유 텍스트 값·비밀 패턴·과대 크기 거부 → 거부 시 verdict=ERROR / AUDIT_EVIDENCE_UNCOMPUTABLE 신호
   3) canonical_json(descriptor) → sha256 → hex
불변식: 원문·비밀은 입력에 들어갈 수 없음. 해시로 원문 복원 불가.
```

### 2.4 AuditEvent 안전 생성 (Q5=A / R2.1)
```
AuditEvent.create(
   workflow_id, unit, verdict, reason_code,
   target: SafeLocation, recommended_action, evidence_hash,
   policy_digest?=None, pubkey_id?=None
) -> AuditEvent
   - event_id: 시간 정렬형 자동 생성(R3.1)
   - ts: 현재 UTC RFC3339
   - schema_version: 현재 계약 버전
   - 금지 값(본문/헤더/키/인자)을 받는 매개변수가 아예 없음
```

## 3. 상태·전이
- 계약 값 객체는 **불변**이라 내부 상태 전이가 없다.
- 유일한 "상태" 개념은 `ComponentStatus`(PREPARING→PROTECTING→BLOCKED/DISABLED)이나, 전이 로직은 제어 서버(UOW-2)에 있고 계약은 값만 제공.

## 4. 데이터 입·출력
- **입력**: 소비 Unit이 만든 판정·탐지·세션 메타(비민감).
- **출력**: 직렬화된 JSON(감사 JSONL 1행, loopback IPC 메시지, HTTP 403 body).
- **영속화**: 계약 자체는 저장하지 않음. 저장은 UOW-2 writer.

## 5. 오류 처리
| 상황 | 계약 동작 |
|---|---|
| 미지원 schema_version | 역직렬화 예외(부분 해석 금지, R4.3) |
| 미정의 verdict/reason_code | 역직렬화 거부(R1) |
| evidence descriptor에 비밀/과대 텍스트 | build 거부 → 소비 측 fail-closed 신호(R2.2/R5.1) |
| 알 수 없는 필드 | 엄격 파싱 거부(R4.2, 계약 드리프트 방지) |

## 6. 통합 지점
- **U-4**: `Judgment` 생성·직렬화.
- **U-5**: `AuditEvent.create`·직렬화·역직렬화(조회), `EvidenceDescriptor` 검증.
- **U-3**: `BlockResponse`(403 body), map_proxy.
- **U-2**: map_cage, `Judgment`·`AuditEvent`.
- **U-1**: map_nav, `AuditEvent`.
- **제어 서버(UOW-2)**: 조회·상태(`ComponentStatus`), workflow_id 필터.

## 7. MVP·검증
- MVP 필수(S-U4-4 [MVP:P0-core]): 이 계약 없이는 어떤 Unit도 판정·기록을 통일 표현할 수 없음 → 최우선.
- 검증: 직렬화 왕복 PBT, 닫힌 집합 PBT, 금지 필드 부재(T-PRIVACY 전제), map_* 결정성 단위 테스트.
- 비의존 설계: 여기서 Python dataclass/pydantic/직렬화 라이브러리 선택은 하지 않음 → Code Generation.
