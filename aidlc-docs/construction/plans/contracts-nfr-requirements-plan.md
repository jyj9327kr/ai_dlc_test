# NFR Requirements Plan — UOW-0 Contracts

역할: NFR Analyst | 페이즈: CONSTRUCTION | 유닛: UOW-0 Contracts | 작성일: 2026-09-07
상태: ✅ 승인 완료 (2026-09-07T09:30:00Z — Q1~Q4 = A/권장, 산출물 생성 완료)

## 목적
UOW-0 Contracts에 적용되는 NFR과 스택 하위 선택을 확정한다. contracts는 순수 계약 계층이라 성능·확장성 부담이 낮고, **보안 집행형 NFR(NFR-4, NFR-6)** 과 **PBT(Partial 강제)** 가 핵심이다.

## 적용 NFR (분석 결과)
| NFR | 적용성 | contracts에서의 의미 |
|---|---|---|
| **NFR-4 원문·비밀 비노출** | ✅ 핵심(MVP) | 금지 필드 구조적 부재, evidence 해시 입력 검증(R2) |
| **NFR-6 순환 없음·독립 테스트** | ✅ 핵심(MVP) | 타 Unit 미참조, 계약 단독 테스트·PBT |
| **NFR-3 서명 대상 무결성** | ✅(간접) | 직렬화 왕복 항등이 서명 bytes 재현성의 전제 |
| NFR-1/2 성능(지연·처리량) | ⚠️ 경미 | 계약 직렬화는 마이크로 단위 — 목표치 없음, `[Deferred:perf-NFR]` |
| NFR-7/11 재현성 | ✅ | 결정적 직렬화(canonical JSON) |
| NFR-12 사용성 | N/A | UI 없음(코드/메시지 분리로 표시계층 지원) |
| 가용성·확장성 | N/A | 단일 장비·라이브러리(프로세스 아님) |
| Resiliency | N/A | opt-out |

## PBT 강제 대상 (Partial: PBT-02/03/07/08/09)
- 직렬화 왕복 항등, 닫힌 집합 거부, evidence 서술자 비밀 배제 속성 → contracts에서 **강제**.

## 이미 잠긴 입력 (재질문 안 함 — C-DEP-1, C-AIDLC-2)
- 언어 = **Python**. 직렬화 표현 = JSON(감사 JSONL·loopback·403 body), snake_case.
- 성능 최적화·수치 목표는 MVP 유예(Q1=A). 차단/거부/오류를 경고·통과로 바꾸지 않음(C-SCOPE-1).

---

## 질문 (각 `[Answer]:` 에 알파벳. 권장안 표시. 없으면 `X) Other`)

### Q1: contracts 계층의 의존성 정책
기반 계약 계층이므로 외부 라이브러리 의존을 어떻게 둘까요?

A) **표준 라이브러리만(zero 3rd-party) (권장)** — `dataclasses` + `json` + `hashlib` + `uuid`만 사용. 모든 Unit이 부담 없이 import, 공급망 표면 최소(Security), 순환·버전 충돌 위험 제거. 검증 로직은 직접 구현. [권장]

B) pydantic v2 채택 — 검증·직렬화 편의, 그러나 무거운 의존을 최하위 계약에 도입(모든 Unit이 상속), 공급망 표면 증가.

C) msgspec 등 고성능 직렬화 — 성능 이점이나 MVP에 불필요하고 의존 추가.

X) Other

[Answer]: A

### Q2: 불변성·검증 구현 방식
값 객체 불변성과 닫힌 집합·필드 검증을 어떻게 강제할까요?

A) **`@dataclass(frozen=True)` + `Enum` + 명시적 검증 함수 (권장)** — frozen dataclass로 불변, `enum.Enum`으로 Verdict/ReasonCode 닫힌 집합, 팩토리·역직렬화에서 명시적 검증(엄격 파싱, 미지원 버전·미정의 코드·알 수 없는 필드 거부). 표준 라이브러리만으로 충족. [권장]

B) 일반 class + 런타임 setter 차단 — 장황·실수 여지.

X) Other

[Answer]: A

### Q3: Canonical JSON(결정적 직렬화) 규약
evidence_hash·행 재현성을 위한 정규 직렬화 규칙은?

A) **키 정렬 + 최소 구분자 + UTF-8(ensure_ascii=false) + 부동소수 미사용 (권장)** — `json.dumps(sort_keys=True, separators=(",",":"), ensure_ascii=False)`. 정수·문자열·불리언만 사용(부동소수 배제로 플랫폼 차이 제거). 같은 값 → 같은 bytes → 같은 SHA-256. [권장]

B) 기본 json.dumps(정렬·구분자 미지정) — 해시 재현성 취약.

X) Other

[Answer]: A

### Q4: 계약 버전 호환 정책
`schema_version` 진화 규칙은?

A) **엄격 단일 버전 + 미지원 버전 명시적 거부 (권장, MVP)** — MVP는 `schema_version=1`만 지원, 다른 버전은 역직렬화 거부(부분 해석 금지, FR-4.4 정렬). 하위호환 매핑은 P1 이후. [권장]

B) 관용적 다중 버전 파서 지금 구현 — MVP 과설계.

X) Other

[Answer]: A

---

## 산출물 (승인 후 생성)
- [x] `aidlc-docs/construction/contracts/nfr-requirements/nfr-requirements.md`
- [x] `aidlc-docs/construction/contracts/nfr-requirements/tech-stack-decisions.md`

## 제약 준수 (상시)
- NFR-4/NFR-6는 MVP 필수(유예 불가). NFR-1/2 수치·최적화만 유예.
- C-DEP-1(Python) 준수, 계약 계층은 공급망 표면 최소화(Security).
- PBT-02/03/07/08/09 강제 대상 표기.
