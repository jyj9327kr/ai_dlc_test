# Code Generation Plan — UOW-0 Contracts

역할: Code Gen Lead | 페이즈: CONSTRUCTION → Code Generation (Part 1 Planning) | 유닛: UOW-0 Contracts | 작성일: 2026-09-07
상태: ✅ 완료 (Part 2 실행 완료 — 9/9 Step, `35 passed`)

## 유닛 컨텍스트
- **유닛**: UOW-0 Contracts (`src/aegis/contracts/`), Q2=A 순서 첫 유닛(기반).
- **구현 스토리**: S-U4-4 공통 판정 식별자 계약(primary). 이후 전 Unit이 소비.
- **의존**: 없음(최하위, NFR-6). 외부 서드파티 0(zero 3rd-party, tech-stack Q1=A).
- **인터페이스**: `enums`·`models`·`serialization`·`evidence`·`ids`·`errors`·`mapping` 공개 API(logical-components.md).
- **프로젝트 타입**: Greenfield · monorepo · 단일 장비. 코드=워크스페이스 루트, 문서=aidlc-docs/만.
- **적용 없음(N/A)**: API 레이어·Repository 레이어·Frontend·DB 마이그레이션 — 계약은 순수 값 라이브러리(영속화·서버 없음).

## 설계 입력 (확정)
- domain-entities.md(값 객체·enum·금지 필드), business-rules.md(R1~R6), business-logic-model.md(직렬화·매핑·해시·팩토리), nfr-design-patterns.md(P1~P6), logical-components.md(모듈 구성).
- Python 3.11+, stdlib만(dataclasses/enum/json/hashlib/uuid/typing), frozen dataclass, canonical JSON, sha256, schema_version=1 엄격.

---

## 생성 단계 (번호순, 체크박스)

- [x] **Step 1 — 프로젝트 구조 설정(Greenfield)**
  - `pyproject.toml`(PEP 517, 패키지명 `aegis`, src 레이아웃, Python≥3.11, 서드파티 런타임 의존 0; dev 의존 pytest·hypothesis), `src/aegis/__init__.py`, `src/aegis/contracts/__init__.py`, `tests/__init__.py`·`tests/contracts/__init__.py`, `.gitignore`(있으면 유지). 위치: 워크스페이스 루트.

- [x] **Step 2 — 비즈니스 로직 생성: enums + errors**
  - `src/aegis/contracts/enums.py`: `Verdict`, `ReasonCode`(Unit 네임스페이스), `Unit`, `ComponentStatus`, `NavDecision`, `ProxyDecision`, `CageDecision`.
  - `src/aegis/contracts/errors.py`: `ContractError` 및 하위 `SchemaVersionError`·`UnknownFieldError`·`InvalidEnumError`·`EvidenceRejectedError`(원문·비밀 미포함 메시지). (S-U4-4)

- [x] **Step 3 — 비즈니스 로직 생성: ids + mapping**
  - `ids.py`: `new_event_id()`(시간 정렬형 — UUIDv7 가용 시 사용, 아니면 time-prefixed 대체, zero 3rd-party), `new_workflow_id()`(UUIDv4).
  - `mapping.py`: `map_nav`/`map_proxy`/`map_cage` → 공통 `Verdict`(결정적). (S-U4-4)

- [x] **Step 4 — 비즈니스 로직 생성: models**
  - `models.py`: `PolicySnapshot`, `Judgment`, `SafeLocation`, `RecommendedAction`, `AuditEvent`(안전 팩토리 `create`, 금지 필드 없음), `BlockResponse`. 전부 `@dataclass(frozen=True, slots=True)`. (S-U4-4, P1/P4)

- [x] **Step 5 — 비즈니스 로직 생성: evidence + serialization**
  - `evidence.py`: `EvidenceDescriptor`, `build()` 단일 게이트(비민감 필드·타입·최대 길이 검증, 위반 시 `EvidenceRejectedError`), `evidence_hash()`(canonical JSON→sha256, 원문 미입력).
  - `serialization.py`: `serialize()`(sort_keys+최소 구분자+ensure_ascii=False+부동소수 배제), `deserialize()`(엄격: 미지원 schema_version·미정의 enum·알 수 없는 필드 거부). (P2/P3/P4)

- [x] **Step 6 — 공개 API 노출**
  - `contracts/__init__.py`에서 공개 심볼 re-export. import 그래프에 `aegis.contracts → aegis.*` 간선 0 유지(NFR-6).

- [x] **Step 7 — 단위·속성 테스트 생성(PBT 포함)**
  - `tests/contracts/`: `test_serialization.py`(왕복 항등·오염 입력 거부 — hypothesis), `test_models.py`(불변성·안전 팩토리), `test_evidence.py`(비밀 배제 속성 — 임의 문자열 주입 거부/미반영, hypothesis), `test_mapping.py`(결정성), `test_errors.py`, `test_ids.py`(유일·시간정렬). PBT-02/03/07/08/09 대상 명시. **합성/절대 무효 값만 사용**(실제 키 금지).
  - 주: 테스트 실행은 Build & Test 단계. 여기서는 생성만.

- [x] **Step 8 — 문서 요약 생성**
  - `aidlc-docs/construction/contracts/code/` 에 markdown 요약(모듈별 책임·공개 API·PBT 매핑). 애플리케이션 코드 아님.

- [x] **Step 9 — 배포/패키징 아티팩트**
  - `pyproject.toml` 패키징 메타 확정(라이브러리이므로 별도 배포 대상 없음 — 다른 UOW가 import). README에 contracts 위치·zero 3rd-party 원칙 1줄 기록(있으면 append).

## 스토리 추적성
| Step | 스토리 | FR | 검증 |
|---|---|---|---|
| 2~6 | S-U4-4 | FR-4.4 | T-FLOW(계약), PBT |
| 7 | S-U4-4 | NFR-4/6, NFR-CT-1~4 | T-PRIVACY(전제), PBT-02/03/07/08/09 |

## 범위·제약 (상시)
- NO HARDCODED LOGIC: 이 계획대로만 생성. 원문·비밀·실제 키를 코드·테스트·문서에 두지 않음(NFR-4, 합성값만).
- fail-closed 표현 유지(예외→ERROR, 조용한 통과 없음, C-SCOPE-1).
- 애플리케이션 코드는 워크스페이스 루트만, 문서는 aidlc-docs/만.
- 예상 규모: 신규 파일 약 8 소스 + 6 테스트 + pyproject/README + 문서 요약.
