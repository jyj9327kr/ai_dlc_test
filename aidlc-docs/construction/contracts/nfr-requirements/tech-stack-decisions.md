# UOW-0 Contracts — Tech Stack Decisions

작성일: 2026-09-07 | 페이즈: CONSTRUCTION → NFR Requirements | 유닛: UOW-0 Contracts
상위 제약: C-DEP-1(언어 Python), C-DEP-2(위치 `src/aegis/contracts/`).

## 1. 결정 요약
| 항목 | 결정 | 근거 |
|---|---|---|
| 언어 | Python (3.11+ 권장) | C-DEP-1 잠금. `dataclass(slots)`·UUIDv7 등 활용 |
| 의존성 | **표준 라이브러리만 (zero 3rd-party)** — `dataclasses`, `enum`, `json`, `hashlib`, `uuid`, `typing` | Q1=A. 최하위 계약, 공급망 표면 최소(Security), 순환·버전 충돌 제거 |
| 값 객체 | `@dataclass(frozen=True)` (가능 시 `slots=True`) | Q2=A. 불변·경량 |
| 닫힌 집합 | `enum.Enum` (Verdict, ReasonCode, Unit, ComponentStatus 등) | Q2=A. 미정의 값 거부 용이 |
| 검증 | 명시적 검증 함수 + 엄격 파서(미지원 버전·미정의 코드·알 수 없는 필드 거부) | Q2/Q4=A. FR-4.4 부분 해석 금지 정렬 |
| 직렬화 | `json.dumps(sort_keys=True, separators=(",",":"), ensure_ascii=False)` | Q3=A. 결정적 canonical JSON |
| 수치 타입 | 정수·문자열·불리언만(부동소수 배제) | Q3=A. 플랫폼 차이 제거, 해시 재현성 |
| 해시 | `hashlib.sha256` over canonical JSON of `EvidenceDescriptor` | Q4(Functional)=A. 원문 미입력 |
| 식별자 | `event_id`=UUIDv7(또는 ULID 대체, 표준 uuid로 v7)·`workflow_id`=UUIDv4/호출자 제공 | Functional Q3=A. 시간 정렬 |
| 스키마 버전 | `schema_version=1`만 지원, 그 외 거부 | Q4=A. MVP, 다중 버전은 P1+ |
| 테스트 | pytest + hypothesis(PBT) | 전역 스택, PBT-02/03/07/08/09 강제 |

## 2. 채택하지 않은 대안
- **pydantic v2 (Q1-B)**: 검증 편의는 크나 무거운 서드파티를 **모든 Unit이 상속하는 최하위 계약**에 도입 → 공급망 표면·버전 결합 증가. 계약 계층엔 부적합.
- **msgspec/orjson (Q1-C)**: 성능 이점이 MVP에 불필요(계약 직렬화는 병목 아님). 의존 추가만 남음.
- **다중 버전 관용 파서 (Q4-B)**: MVP 과설계. 엄격 단일 버전으로 부분 해석 위험 차단.

## 3. UUIDv7 주의
- Python 표준 `uuid`의 v7 가용성은 런타임 버전에 따름. **없으면 ULID(경량 자체 구현, 표준 라이브러리 `os.urandom`+time 기반) 또는 time-prefixed UUID로 대체**하되, "시간 정렬 가능·전역 유일" 속성을 유지한다. 이 대체 여부는 Code Generation에서 런타임 버전 확인 후 확정(zero 3rd-party 유지).

## 4. 제약 준수
- C-DEP-1/2 준수. Resiliency=N/A(opt-out). 성능 NFR 유예(NFR-1/2).
- Security: 서드파티 0 → 계약 계층 공급망 위험 최소. 원문·비밀 미보관(NFR-4).
- 이 결정은 UOW-0에 한정. 상위 Unit(U-4 등)의 liboqs·mitmproxy·FastAPI 등은 각 UOW tech-stack에서.
