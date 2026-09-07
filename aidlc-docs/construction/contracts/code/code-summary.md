# UOW-0 Contracts — Code Generation Summary

**Unit**: UOW-0 (공유 계약 라이브러리)
**Verification**: `35 passed` (pytest + hypothesis), zero 3rd-party runtime deps.
**Story traceability**: S-U4-4 (Judgment 정의) — 이 UOW에서 **정의**, UOW-1 U-4에서 **소비**.

## 생성 산출물 (application code = workspace root)

| 파일 | 책임 | NFR/규칙 |
|---|---|---|
| `src/aegis/contracts/enums.py` | 닫힌 집합: `Verdict`, `Unit`, `ComponentStatus`, `NavDecision`/`ProxyDecision`/`CageDecision`, `ReasonCode`(Unit 네임스페이스), `SECRET_BLOCKED_WIRE_CODE` | P2, R1, R6 |
| `src/aegis/contracts/errors.py` | `ContractError` + `SchemaVersionError`/`UnknownFieldError`/`InvalidEnumError`/`EvidenceRejectedError`. 메시지 비민감 | P5, NFR-4 |
| `src/aegis/contracts/ids.py` | `new_event_id()`(시간 정렬), `new_workflow_id()`. UUIDv7 부재 시 time-prefixed 대체 | Functional Q3=A |
| `src/aegis/contracts/mapping.py` | 경계 결정 → 공통 `Verdict` 결정적 매핑. `ProxyDecision.REJECT`→`BLOCK` | R1.3, C-SCOPE-1 |
| `src/aegis/contracts/models.py` | 불변 값 객체: `PolicySnapshot`(digest 자기검증), `Judgment`, `SafeLocation`, `RecommendedAction`, `AuditEvent`(`create` 안전 팩토리), `BlockResponse` | P1, P4, NFR-4 |
| `src/aegis/contracts/evidence.py` | `EvidenceDescriptor` + `build()` 단일 게이트 + `evidence_hash()`(canonical JSON→sha256, 원문 미입력) | P4(이중 방어), Q4=A |
| `src/aegis/contracts/serialization.py` | `canonical_dumps`(결정적), `serialize`/`deserialize`(엄격 파싱) | P2, P3, NFR-CT-3 |
| `src/aegis/contracts/__init__.py` | 공개 API 재노출. `aegis` 내 타 패키지 import 0 (순환 없음) | NFR-6 |

## 테스트 (`tests/contracts/`, 합성값만)
- `test_serialization.py`: 라운드트립·결정성·부동소수 배제·엄격 파싱(미지원 버전/미지의 필드/미정의 enum 거부) — PBT-02/03
- `test_evidence.py`: 비밀 배제 속성, 과대 길이/항목/bool 거부 — PBT-07/08/09
- `test_models.py`: 불변성, 안전 팩토리, 금지 필드 부재, PolicySnapshot digest
- `test_mapping.py`: 전수 매핑, REJECT→BLOCK
- `test_ids.py`: 유일성·시간 정렬성·UUID 형태
- `test_errors.py`: 예외 계층

## 보안 집행 확인 (blocking, 완화 없음)
- **구조적 비노출**: `AuditEvent`에 body/headers/url/key/args/env 필드 부재 — `test_audit_event_has_no_forbidden_fields`로 회귀 방지.
- **증거 해시 원문 미입력**: `evidence_hash`는 검증된 비민감 서술자만 입력.
- **fail-closed 파싱**: 미지원 스키마/미정의 enum/알 수 없는 필드를 예외로 거부(조용한 통과 없음).
- **안전 차단 불변**: `ProxyDecision.REJECT`(검사 불가)도 `BLOCK`으로 매핑(경고·통과 완화 금지, C-SCOPE-1).

## 비고
- Python 3.12.3 환경: stdlib UUIDv7 부재 → time-prefixed 정렬 식별자로 대체(서드파티 미추가).
- 실행/테스트는 `.venv`(PEP 668 externally-managed 회피). 런타임 의존 0, dev 의존 pytest/hypothesis.
