# AEGIS — Inception Requirements (승인된 요구 입력)

상태: Requirements Analysis 완료 후보 (사용자 승인 대기) | 깊이: Comprehensive | 작성일: 2026-09-07

이 문서는 AI-DLC Inception 단계의 **승인된 요구 입력**이다. 사용자 답변(Q5=A)에 따라 아래 두 기준안을 이번 프로젝트의 권위 있는 요구·제약 원본으로 채택한다. 내용 중복·드리프트를 막기 위해 전문을 복사하지 않고 원본을 연결한다. (근거: constraints.md C-AIDLC-3, C-AIDLC-4)

## 0. 권위 있는 원본 (채택)

| 문서 | 경로 | 버전 | 역할 |
|---|---|---|---|
| 제품 요구사항 | [`requirements/requirements.md`](../../../requirements/requirements.md) | v4.0 (2026-09-07) | 제품 동작·수용 기준(FR/NFR)·시나리오 |
| 개발·보안 제약 | [`requirements/constraints.md`](../../../requirements/constraints.md) | v4.0 (2026-09-07) | 기술 경계·프로토콜·기본값·검증·AI-DLC 절차 |

**채택 의미**: 위 문서의 모든 P0 FR/NFR·수용 기준·제약(C-*)이 이번 개발의 기준이다. 이 채택은 요구 입력 승인이며, 이후 설계·코드 생성 단계의 개별 승인과는 구분한다. (근거: constraints.md C-AIDLC-1)

## 1. Intent Analysis (Requirements Analysis Step 2)

| 항목 | 값 |
|---|---|
| 사용자 요청 (원문) | "AEGIS 시스템을 만들고 싶습니다. requirements 디렉토리에 있는 md 문서를 읽고 AI-DLC 워크플로우를 시작해봅시다." |
| 제품 의도 요약 | 개발자가 ① 외부 웹 확인, ② 로컬 AI 에이전트 실행, ③ 클라우드 LLM 요청을 하는 3개 신뢰 경계를 통제하는 보안 워크스페이스 (requirements.md §1.1) |
| 요청 유형 | New Project (Greenfield) |
| 요청 명확성 | Clear — 상세 기준안 2종이 제공됨 |
| 범위 | Cross-system (Chrome 확장, 격리 브라우저, 에이전트 실행 게이트, LLM 전송 프록시, 공통 정책·감사) |
| 복잡도 | Complex |
| 요구 분석 깊이 | Comprehensive |

## 2. 핵심 문제 → 보장 결과 (요약)

| 문제 | 보장 결과 | 증거 |
|---|---|---|
| P-1 불명확한 링크의 로컬 스크립트 실행 위험 | 미분류/위험 웹은 서버 브라우저에서 격리, 로컬엔 픽셀만 | D-1 |
| P-2 에이전트 샌드박스 정책 변조 위험 | 서명(ML-DSA-65) 검증된 정책만 실행, OpenShell이 자원 제한 집행 | D-2 |
| P-3 프롬프트에 섞인 API 키의 LLM 유출 | 전송 전 시크릿 탐지 시 요청 전체 차단 | D-3 |
| P-4 도구별 정책·로그 분산 | 공통 policy_id·workflow_id로 세 방어 결과 통합 조회 | T-FLOW, T-AUDIT |

## 3. Units of Work (5) — 상세는 원본 §4 / C-DEP-2

- **U-1 WebIsolate** — URL 분류·Chrome 보호 탐색·RBI 픽셀 중계·위험 액션 UI
- **U-2 AgentCage** — 검증된 정책으로 OpenShell 실행·워크스페이스/통신 경계
- **U-3 SecretGuard** — LLM 요청 정규화·시크릿 탐지·전송/거부 프록시
- **U-4 PolicyCore** — 공통 설정·ML-DSA 서명/검증·신뢰키
- **U-5 AuditTrail** — 구조화 이벤트 순차 기록·조회·통합 상태 UI
- 공통 `contracts` 모듈 (데이터 타입·reason code)

의존: `U-1/U-2/U-3 → U-4, U-5`. 통합 순서: 공통 계약 + U-4/U-5 확립 → `U-3 → U-2 → U-1`.

## 4. 기능/비기능 요구사항 (요약, 전문은 원본)

- **기능 요구**: FR-0.1~0.3(공통 실행), FR-1.1~1.6(WebIsolate), FR-2.1~2.5(AgentCage), FR-3.1~3.6(SecretGuard), FR-4.1~4.4(PolicyCore), FR-5.1~5.4(AuditTrail+UI). → requirements.md §5
- **비기능 요구**: NFR-1~NFR-13 (RBI 지연, 프록시 지연, 정책 무결성, 데이터 최소화, TLS, 유지보수성, 재현 기동, 장애 안전성, 감사 일관성, 탐지 정확도, 호환성, 사용성, 자원 상한). → requirements.md §7
- **검증**: 종단 시나리오 D-1~D-3, 시크릿 고정 코퍼스 S-01~S-08 / B-01~B-08, 경계·실패·통합 시험 T-* → requirements.md §8

## 5. Extension Decisions (Requirements Analysis Step 5.1)

opt-in 질문·답변은 [`requirement-verification-questions.md`](requirement-verification-questions.md)에 기록. 확정 결과:

| Extension | 결정 | 모드 | 적용 |
|---|---|---|---|
| **Security Baseline** | ✅ Enabled (Q1=A) | Full / blocking | SECURITY-01~15를 단계별 해당 시 차단성 제약으로 적용, 비해당은 N/A 표시 |
| **Resiliency Baseline** | ❌ Disabled (Q2=A) | — | 미적용 (단일 장비 P0 범위, HA/DR은 §3 명시적 제외). full rules 미로드 |
| **Property-Based Testing** | ✅ Enabled — **Partial** (Q3=B) | Partial / blocking | **PBT-02, PBT-03, PBT-07, PBT-08, PBT-09** 강제. 나머지(PBT-01/04/05/06/10) 권고 |

- 제품 P0 보안 제약은 확장 선택과 무관하게 적용한다. 선택하지 않은 Resiliency로 HA/DR·전사 인증을 자동 추가하지 않는다. (근거: constraints.md C-AIDLC-2)

## 6. 실행·검증 환경 결정 (Q4=B)

- **선택**: WSL2 선진행 + 조기 smoke test 게이팅. 실패 시 Ubuntu 24.04 VM 전환.
- **현재 장비**: WSL2 (Linux 6.18 microsoft-standard-WSL2).
- **필수 선행 기술 검증**(요구 질문 아님, 실행 작업): 
  - **V-1** — OpenShell / Landlock / 컨테이너 격리 실동작
  - **V-2** — liboqs ML-DSA-65 키 생성→서명→정상/변조 검증 smoke test
- V-1/V-2 통과 전 관련 P0(특히 D-2)를 완료로 표시하지 않는다. (근거: requirements.md §10.2, constraints.md C-SCOPE-2, C-DEP-3)

## 7. 우선순위·범위·완료 정의

- **P0 = 최초 제공 범위** (모든 P0 수용 기준 충족 시 완료). P1은 P0 검증 후, P2는 후속. 안전한 차단을 경고/통과로 바꿔 P0를 축소하지 않는다. (requirements.md §3)
- **Definition of Done**: requirements.md §9.3 및 constraints.md §12·§13 적용.

## 8. 다음 단계 제안

Greenfield · Complex 이므로 Inception 후속 단계로 **User Stories → Workflow Planning → Application Design → Units Generation**을 제안한다. 사용자 스토리(US-1~US-6)와 5 Unit·기본값은 원본에 이미 존재하므로 입력으로 재사용하고 무의미하게 다시 선택시키지 않는다. (근거: constraints.md C-AIDLC-1)

## 부록: 미해결/추적 항목
- V-1/V-2 환경 smoke test (WSL2) — Inception 초기 실행 예정
- V-3(프록시 CA·egress 차단), V-4(브라우저-RBI 지연·탐색 가로채기) — Application/Infrastructure Design 단계 검증
- 상세 버전·digest 잠금은 smoke test 통과 값으로 확정 (C-DEP-1)
