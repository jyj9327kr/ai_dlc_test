# UOW-0 Contracts — NFR Requirements

작성일: 2026-09-07 | 페이즈: CONSTRUCTION → NFR Requirements | 유닛: UOW-0 Contracts
결정: Q1~Q4 = A(권장). 스택은 C-DEP-1로 Python 잠금.

## 1. 적용 NFR과 수용 기준(테스트 가능)

### NFR-CT-1 · 원문·비밀 비노출 (NFR-4, FR-5.2) — **MVP 필수 · Security 집행**
- **요구**: 계약 타입·직렬화·해시 어디에도 요청 본문·전체 URL query·원시 헤더·키·개인키·명령 인자·환경변수가 담기지 않는다.
- **수용 기준**:
  - 금지 필드가 타입에 존재하지 않음(정적 확인 + 속성 테스트).
  - 임의 비밀 문자열을 evidence 입력에 주입해도 `EvidenceDescriptor` 검증이 자유 텍스트/과대 크기를 거부한다.
  - 직렬화 출력(JSON) 스캔 시 금지 항목 0건(T-PRIVACY 전제).

### NFR-CT-2 · 순환 없음 · 독립 테스트 (NFR-6) — **MVP 필수**
- **요구**: contracts는 다른 aegis Unit을 import하지 않는다. 단독으로 테스트 가능.
- **수용 기준**: import 그래프에 `aegis.contracts → aegis.*` 간선 0개(정적 검사). 계약 단위·PBT가 타 Unit 없이 통과.

### NFR-CT-3 · 결정적 직렬화 · 서명/해시 재현성 (NFR-3 간접, NFR-7/11) — **MVP 필수**
- **요구**: 같은 값은 항상 같은 canonical bytes로 직렬화되어 evidence_hash·행 재현이 결정적이다.
- **수용 기준**:
  - `serialize(x)`가 키 정렬·최소 구분자·UTF-8·부동소수 배제로 안정적(Q3=A).
  - `deserialize(serialize(x)) == x` (직렬화 왕복 항등, PBT).
  - 동일 입력 → 동일 SHA-256 evidence_hash(반복 실행·플랫폼 무관).

### NFR-CT-4 · 계약 무결성 · 엄격 파싱 — **MVP 필수**
- **요구**: 미지원 `schema_version`, 미정의 enum, 알 수 없는 필드는 명시적으로 거부(부분 해석 금지, FR-4.4 정렬).
- **수용 기준**: 위 오염 입력 각각에 대해 역직렬화가 예외/거부. 값 객체 불변(생성 후 변경 시도 실패).

### NFR-CT-5 · 유지보수성 · 표시계층 분리 — 표준
- **요구**: reason_code(식별자)와 사람이 읽는 한글 메시지를 분리. 신규 코드는 계약 개정으로만.
- **수용 기준**: 코드↔메시지 매핑이 계약 밖(`reason-messages`)에 있고, 코드 변경 없이 메시지 교체 가능.

## 2. 유예/비적용 NFR (근거)
| NFR | 상태 | 근거 |
|---|---|---|
| NFR-1/2 성능(지연·처리량) | `[Deferred:perf-NFR]` | 계약 직렬화는 마이크로 단위, MVP는 동작·정확성 우선(Q1=A). 목표치·최적화 없음. |
| NFR-12 사용성 측정 | N/A | UI 없음. 표시계층 분리로 지원만. |
| 가용성·확장성·failover | N/A | 라이브러리(프로세스 아님), 단일 장비. |
| Resiliency Baseline | N/A | opt-out. |

## 3. PBT 강제 대상 (Partial: PBT-02/03/07/08/09)
- **왕복 항등**: 모든 값 객체 `deserialize(serialize(x)) == x`.
- **닫힌 집합**: Verdict/ReasonCode 밖 값 역직렬화 거부.
- **비밀 배제 속성**: 임의 문자열을 evidence 서술자에 넣어도 금지 필드/과대 자유 텍스트가 계약에 실리지 않음.
- **해시 결정성**: 같은 서술자 → 같은 해시, 다른 서술자 → 다른 해시(충돌 무시 가능 수준).

## 4. 검증 매핑
- NFR-CT-1 → T-PRIVACY, 비밀 배제 PBT.
- NFR-CT-2 → import 그래프 정적 검사, 계약 단위 테스트.
- NFR-CT-3 → 왕복/해시 PBT, 재현성 테스트.
- NFR-CT-4 → 오염 입력 거부 테스트, 불변성 테스트.
- NFR-CT-5 → 코드/메시지 분리 테스트.
