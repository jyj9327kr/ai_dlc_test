# UOW-0 Contracts — NFR Design Patterns

작성일: 2026-09-07 | 페이즈: CONSTRUCTION → NFR Design | 유닛: UOW-0 Contracts
결정: Q1~Q3 = A(권장). 근거: nfr-requirements.md(NFR-CT-1~5).

## 1. 적용 패턴

### P1 · Immutable Value Object (NFR-CT-4)
- 모든 계약 타입은 `@dataclass(frozen=True, slots=True)` — 생성 후 변경 불가. 공유·전달 시 부작용 없음.
- 동등성은 값 기반. 해시 안정.

### P2 · Strict Boundary Parsing (NFR-CT-4)
- 역직렬화는 **엄격 게이트**: 미지원 `schema_version`, 미정의 enum, 알 수 없는 필드를 거부(부분 해석 금지, FR-4.4 정렬).
- "관용적 파싱" 금지 — 계약 드리프트·조용한 오해석 차단.

### P3 · Canonical Serialization (NFR-CT-3)
- 단일 `serialize()`가 키 정렬·최소 구분자·UTF-8·부동소수 배제로 결정적 bytes 생성.
- evidence_hash·감사 행·loopback 메시지의 재현성 기반. 같은 값 → 같은 bytes → 같은 SHA-256.

### P4 · Secret-Exclusion by Construction (NFR-CT-1) **[Security 집행 — 이중 방어]**
- **1층(타입)**: 원시 본문·헤더·키·인자·env를 담을 필드가 타입에 없음(구조적 불가).
- **2층(게이트)**: `EvidenceDescriptor`는 `evidence.build()` 단일 게이트로만 생성 — 허용 필드·타입·최대 길이 검증, 자유 텍스트/비밀 의심 시 `EvidenceRejectedError`.
- `AuditEvent.create`는 완성된 `evidence_hash`(문자열)만 수용 → 원문이 이벤트 경로에 진입할 표면이 없음.

### P5 · Fail-Closed Signaling (R5, C-SCOPE-1) **[Security 집행]**
- 계약 위반·증거 거부는 **전용 예외**(`ContractError` 계층)로 신호. 반환값 무시로 인한 조용한 통과 불가(Q2=A).
- 소비 Unit은 예외를 잡아 `verdict=ERROR` + `*_UNAVAILABLE`/`*_INVALID` reason_code로 fail-closed 전환.
- 예외 메시지에 원문·비밀 미포함(NFR-CT-1 유지).

### P6 · Code/Message Separation (NFR-CT-5)
- reason_code(식별자)는 계약, 한글 표시 문구는 표시계층(`reason-messages`) 매핑. 국제화·문구 변경이 계약을 깨지 않음.

## 2. 비적용 패턴 (근거)
| 카테고리 | 상태 | 근거 |
|---|---|---|
| Resilience(재시도·서킷브레이커·failover) | **N/A** | 라이브러리 — 네트워크·프로세스 장애 개념 없음. 실패는 P5 예외로 표현. |
| Scalability(샤딩·풀·오토스케일) | **N/A** | 부하·프로세스 개념 없음. |
| Performance(캐시·배치·비동기) | **N/A(유예)** | NFR-1/2 유예. 직렬화 병목 아님. |
| Availability(HA·복제) | **N/A** | 인메모리 값 계층. |

## 3. PBT로 검증되는 패턴 불변식 (PBT-02/03/07/08/09)
- P1: 불변성 — 생성 후 setattr 시도 실패.
- P2: 오염 입력(버전/enum/필드) 거부.
- P3: `deserialize(serialize(x)) == x`, 반복·플랫폼 무관 동일 해시.
- P4: 임의 비밀 문자열 주입 → 게이트 거부 또는 필드 부재로 미반영.

## 4. 제약 준수
- Security(Full) 집행 지점: P4(원문 비노출), P5(fail-closed). Resiliency=N/A.
- zero 3rd-party: 모든 패턴을 stdlib(dataclasses/enum/json/hashlib/uuid)로 구현.
