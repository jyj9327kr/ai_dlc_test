# UOW-0 Contracts — Logical Components

작성일: 2026-09-07 | 페이즈: CONSTRUCTION → NFR Design | 유닛: UOW-0 Contracts
결정: Q1=A(관심사별 모듈 분리). 인프라 런타임 컴포넌트(큐·캐시·서킷브레이커) 없음 — 라이브러리.

## 1. 모듈 구성 (`src/aegis/contracts/`)
| 모듈 | 책임 | 주요 심볼 | 패턴 |
|---|---|---|---|
| `enums.py` | 닫힌 집합 | `Verdict`, `ReasonCode`, `Unit`, `ComponentStatus`, `NavDecision`, `ProxyDecision`, `CageDecision` | P2 |
| `models.py` | 불변 값 객체 | `PolicySnapshot`, `Judgment`, `SafeLocation`, `RecommendedAction`, `AuditEvent`, `BlockResponse` | P1 |
| `serialization.py` | canonical 직렬화·엄격 파싱 | `serialize()`, `deserialize()` | P2, P3 |
| `evidence.py` | 증거 서술자·해시 게이트 | `EvidenceDescriptor`, `build()`(단일 게이트), `evidence_hash()` | P4 |
| `ids.py` | 식별자 생성 | `new_event_id()`(시간 정렬형), `new_workflow_id()` | — |
| `errors.py` | 계약 예외 계층 | `ContractError`, `SchemaVersionError`, `UnknownFieldError`, `InvalidEnumError`, `EvidenceRejectedError` | P5 |
| `mapping.py` | 경계 결정 → Verdict | `map_nav()`, `map_proxy()`, `map_cage()` | — |
| `__init__.py` | 공개 API 재노출 | 위 심볼 export | — |

- `models.AuditEvent`는 `evidence.py`의 완성 해시만 수용(원문 미진입, P4).
- `serialization.py`는 `errors.py` 예외로 위반 신호(P5). 다른 aegis Unit import 없음(NFR-6).

## 2. 컴포넌트 상호작용 (모듈 내부, 텍스트)
- `deserialize(bytes)` → `serialization`이 schema_version·필드·enum 검증(`enums`, `errors`) → `models` 값 객체 반환.
- `AuditEvent.create(...)` → `ids.new_event_id()` + 현재 ts + `evidence_hash`(호출자 사전 계산) → 불변 이벤트.
- `evidence.build(descriptor_fields)` → 비민감 검증 → `EvidenceDescriptor` → `serialize` canonical → `evidence_hash()`(sha256). 위반 시 `EvidenceRejectedError`.
- 경계 결정 매핑은 `mapping`이 순수 함수로 제공(감사/UI 통합 Verdict).

## 3. 의존 그래프 (모듈 수준, 순환 없음)
```
errors  enums
   \\     |
    \\    v
     > models <---- ids
        ^   ^
        |   |
 serialization  evidence   mapping
```
- 상위(serialization/evidence/mapping)만 하위(models/enums/ids/errors)에 의존. 순환 없음(NFR-6를 모듈 수준에서도 유지).
- 외부(aegis 타 Unit·서드파티) 의존 0.

## 4. 테스트 배치 (Q4=A, 유닛별 하위)
- `tests/contracts/test_serialization.py`(P2/P3 PBT), `test_models.py`(P1 불변), `test_evidence.py`(P4 비밀 배제 PBT), `test_mapping.py`, `test_errors.py`, `test_ids.py`.
- 공유 코퍼스·e2e는 UOW-3/전체 단계에서. contracts는 자립 테스트.

## 5. 인프라 컴포넌트
- **없음**(N/A). contracts는 프로세스·큐·저장소를 소유하지 않는다. 감사 영속화는 UOW-2 writer, 서명 검증 실행은 UOW-1.

## 6. 제약 준수
- 관심사 분리로 PBT 초점 명확(PBT-02/03/07/08/09). Security 게이트(evidence.build) 단일화.
- zero 3rd-party. 모듈 수준 순환 없음.
