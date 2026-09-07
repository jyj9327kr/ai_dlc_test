# NFR Design Plan — UOW-0 Contracts

역할: NFR Designer | 페이즈: CONSTRUCTION | 유닛: UOW-0 Contracts | 작성일: 2026-09-07
상태: ✅ 승인 완료 (2026-09-07T09:40:00Z — Q1~Q3 = A/권장, 산출물 생성 완료)

## 목적
NFR Requirements(NFR-CT-1~5)를 계약 모듈의 **설계 패턴·논리 컴포넌트**로 구체화한다. contracts는 순수 라이브러리이므로 런타임 인프라 컴포넌트(큐·캐시·서킷브레이커)는 없다.

## 카테고리 적용성 (근거 명시)
| 카테고리 | 적용 | 근거 |
|---|---|---|
| Resilience 패턴 | **N/A** | 라이브러리 — 네트워크·프로세스 장애 없음. "실패"는 파싱 거부(엄격, NFR-CT-4)로 표현. |
| Scalability 패턴 | **N/A** | 프로세스·부하 개념 없음. |
| Performance 패턴 | **N/A(유예)** | NFR-1/2 유예, 계약 직렬화는 병목 아님. |
| **Security 패턴** | ✅ | NFR-CT-1(원문 비노출) 구조적 강제 = 핵심 설계 결정. |
| **Logical Components** | ✅ | 계약 모듈 내부 구성(타입/열거/직렬화/증거/식별자/검증). |

## 확정 입력 (재질문 안 함)
- 값 객체 불변(frozen dataclass), 닫힌 집합(Enum), canonical JSON, sha256, zero 3rd-party, schema_version=1 엄격.
- 금지 필드 구조적 부재 + 안전 팩토리(Functional Q5=A, NFR-CT-1).

---

## 질문 (각 `[Answer]:` 에 알파벳. 권장안 표시. 없으면 `X) Other`)

### Q1: contracts 패키지 내부 논리 컴포넌트 구성
`src/aegis/contracts/` 내부를 어떻게 나눌까요?

A) **관심사별 모듈 분리 (권장)** — `enums.py`(Verdict/ReasonCode/Unit/ComponentStatus), `models.py`(값 객체), `serialization.py`(canonical dump/strict load), `evidence.py`(EvidenceDescriptor 검증·해시), `ids.py`(event_id/workflow_id 생성), `errors.py`(계약 예외). 응집도 높고 PBT 대상이 모듈별로 명확. [권장]

B) 단일 모듈(`__init__.py`에 전부) — 작지만 성장 시 비대·테스트 초점 흐림.

X) Other

[Answer]: A

### Q2: 계약 위반(엄격 파싱 실패) 표현 방식
미지원 버전·미정의 enum·알 수 없는 필드·비밀 혼입 시 어떻게 신호할까요?

A) **전용 예외 계층 (권장)** — `ContractError`(기반) 하위 `SchemaVersionError`, `UnknownFieldError`, `InvalidEnumError`, `EvidenceRejectedError`. 소비 Unit은 이를 잡아 `verdict=ERROR` + 적절한 `*_UNAVAILABLE`/`*_INVALID` reason_code로 fail-closed 전환(R5). 예외 메시지에 원문·비밀 미포함. [권장]

B) 반환값(None/에러코드) 방식 — 소비 측 검사 누락 시 조용한 통과 위험(C-SCOPE-1 저해).

X) Other

[Answer]: A

### Q3: Security 패턴 — evidence 비밀 배제 강제 지점
원문·비밀이 evidence에 실리지 않도록 어디서 강제할까요?

A) **생성 경계 단일 게이트 (권장)** — `EvidenceDescriptor`는 오직 `evidence.build()` 게이트로만 생성. 게이트가 (1) 허용된 비민감 필드만 수용, (2) 각 값의 타입·최대 길이 검증, (3) 자유 텍스트/비밀 패턴 의심 시 `EvidenceRejectedError`. `AuditEvent.create`는 완성된 hash만 받음. 이중 방어(생성 게이트 + 타입에 원시 필드 부재). [권장]

B) 호출 측 각자 검증 — 누락·불일치 위험, 단일 소스 아님.

X) Other

[Answer]: A

---

## 산출물 (승인 후 생성)
- [x] `aidlc-docs/construction/contracts/nfr-design/nfr-design-patterns.md`
- [x] `aidlc-docs/construction/contracts/nfr-design/logical-components.md`

## 제약 준수 (상시)
- NFR-CT-1(Security)·CT-4를 패턴으로 구체화. Resilience/Scalability/Performance = N/A(근거 명시).
- fail-closed 표현(R5, C-SCOPE-1): 실패는 예외→ERROR, 조용한 통과 없음.
- zero 3rd-party 유지(stdlib 예외/직렬화만).
