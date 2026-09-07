# NFR Design Plan — UOW-1 PolicyCore (U-4)

역할: NFR Design Lead | 페이즈: CONSTRUCTION → NFR Design | 유닛: UOW-1 PolicyCore (U-4) | 작성일: 2026-09-07
상태: ✅ 답변 완료 (Q1~Q5 = A, 사용자 '모두 권장대로') — 산출물 생성

## 유닛 컨텍스트
- **유닛**: UOW-1 PolicyCore (`src/aegis/policy/`). NFR Requirements 완료(NFR-PC-1~5).
- **NFR 동인**: 암호 정확성·비노출·순환없음·fail-closed·결정성. 성능·확장은 deferred/N/A.
- **기술**: liboqs(`oqs-python`) 검증, PyYAML `safe_load` 파싱, `config/trusted-keys/` 공개키.
- **목적**: 위 NFR을 **패턴·논리 컴포넌트(모듈)**로 구체화. 순환 없는 import 그래프, 라이브러리 경계 격리.

## 설계 입력 (확정)
- nfr-requirements/{nfr-requirements, tech-stack-decisions}.md, functional-design/*, contracts(UOW-0), C-PQC-1.

---

## 컨텍스트 질문 (A/B/C + 기타, `[Answer]: A` 태그에 답변)

권장안은 각 질문의 A입니다.

### Q1. 서명 검증 라이브러리 경계 격리 패턴 [Security]

A) **포트-어댑터로 Verifier 격리** — liboqs(`oqs`) 호출을 얇은 `verifier` 어댑터 단일 지점에 캡슐화. 판정 로직은 라이브러리 비의존(인터페이스로만 호출). 테스트는 어댑터 경계에서 **실제 검증**(mock 금지). liboqs 부재 시 어댑터가 fail-closed 신호. (권장)

B) 판정 로직 곳곳에서 `oqs`를 직접 호출.

C) 검증을 별도 프로세스로 분리해 IPC.

X) 기타: 자유 기술

[Answer]: A

### Q2. Fail-Closed 신호 패턴 (NFR-PC-4) [Security]

A) **판정 진입점을 fail-closed 래퍼로 감싼다** — 내부 예외·라이브러리 오류를 `Judgment(ERROR, COMMON_INTERNAL_ERROR)`로 사상, 예상된 검증 실패는 `Judgment(BLOCK, POLICY_*)`. 예외를 성공으로 강등하는 경로 없음. (권장)

B) 호출자가 예외를 잡아 처리(래퍼 없음).

C) 실패 시 전부 예외 raise(Judgment 미반환).

X) 기타: 자유 기술

[Answer]: A

### Q3. KeyStore 컴포넌트 설계 (Q4 tech, FR-4.3)

A) **불변 로드 + 순수 조회** — 부팅/정책 갱신 시 `config/trusted-keys/`를 읽기 전용 로드해 불변 KeyStore 구성. `lookup`은 순수 함수, 폐기·만료 판정은 **검증 시각을 주입**(now 파라미터)해 결정성 확보. 로드 실패는 fail-closed(신뢰키 없음). (권장)

B) 조회 시마다 파일 재읽기(디스크 I/O 매 호출).

C) 가변 캐시 + 백그라운드 갱신 스레드.

X) 기타: 자유 기술

[Answer]: A

### Q4. 논리 컴포넌트(모듈) 구성 (NFR-PC-3, 순환 없음)

A) **책임 분리 모듈** — `verifier`(oqs 어댑터), `keystore`(로드·조회), `schema`(공통/정책 분리 검증 + safe_load + 입력 크기 상한), `evaluator`(우선순위 판정→Judgment), `errors`, `__init__`(공개 API). import 그래프: `evaluator → {verifier, keystore, schema}`, 전부 `→ contracts`만 외부 의존, 순환 0. (권장)

B) 단일 모듈(`policy.py`)에 전부.

C) 더 세분(각 검사 단계별 개별 모듈).

X) 기타: 자유 기술

[Answer]: A

### Q5. Resilience / Scalability / Performance 패턴

A) **Resilience = fail-closed만**(재시도·서킷 브레이커 없음 — 검증 재시도는 무의미·위험). Scalability = N/A(단일 사용자). Performance = `[Deferred:perf-NFR]`(측정 훅 미추가, 동작만). (권장)

B) 검증 재시도·백오프 도입.

C) 결과 캐시로 성능 최적화(동일 정책 재검증 생략).

X) 기타: 자유 기술

[Answer]: A

---

## 생성 단계 (승인·답변 후 실행, 체크박스)

- [x] **Step ND-1 — NFR 설계 패턴**: `nfr-design-patterns.md` — P1 Verifier 포트-어댑터(라이브러리 격리, 실검증) [Security], P2 Fail-Closed 래퍼 [Security], P3 불변 KeyStore·시각 주입(결정성), P4 인증-우선 파싱 강건화(safe_load+크기 상한), P5 비노출(digest/식별자만). Resilience(fail-closed만)/Scalability(N/A)/Performance(deferred) 명시.
- [x] **Step ND-2 — 논리 컴포넌트**: `logical-components.md` — 모듈 `verifier`/`keystore`/`schema`/`evaluator`/`errors`/`__init__` 책임·인터페이스, 모듈 의존 그래프(순환 없음), contracts 사용 지점, 테스트 배치(`tests/policy/`), C-PQC-1 서명 메시지 구성 위치.

## 스토리 추적성
| Step | 스토리 | NFR | 패턴 |
|---|---|---|---|
| ND-1/2 | S-U4-2 | NFR-PC-1 | P1 Verifier 어댑터 |
| ND-1 | S-U4-1/3 | NFR-PC-4 | P2 Fail-Closed |
| ND-2 | S-U4-3 | FR-4.3 | P3 불변 KeyStore |
| ND-1/2 | S-U4-4 | NFR-PC-2/3/5 | P4/P5 |

## 범위·제약 (상시)
- 보안 완화 없음(실검증·mock/HMAC 금지·공개키 전용). 순환 없는 import 그래프. 성능 최적화(캐시·전송 전 검증 생략 등) 도입으로 보안 완화 금지(C-SCOPE-1).
- 문서는 `aidlc-docs/construction/policycore/nfr-design/`에만.
