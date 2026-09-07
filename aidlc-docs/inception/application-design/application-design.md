# AEGIS — Application Design (통합)

작성일: 2026-09-07 | 단계: INCEPTION → Application Design | 상태: 사용자 승인 대기
승인 결정(전부 A): Q1 하이브리드 토폴로지 · Q2 전용 감사 writer + loopback · Q3 in-process 검증 라이브러리 · Q4 공통 오류/판정 계약 · Q5 FastAPI 제어 서버 집약.

이 문서는 아래 세부 산출물을 통합한다:
- [components.md](components.md) — 컴포넌트 정의·책임·인터페이스
- [component-methods.md](component-methods.md) — 메서드 시그니처(고수준)
- [services.md](services.md) — 런타임 서비스·오케스트레이션
- [component-dependency.md](component-dependency.md) — 의존 매트릭스·통신·데이터 흐름

상세 비즈니스 로직·스키마·알고리즘은 Construction 단계 Functional Design(per-unit)에서 확정한다.

## 1. 아키텍처 개요
AEGIS는 단일 장비·단일 사용자에서 3개 신뢰 경계를 통제한다. 6개 컴포넌트(U-1~U-5 + `contracts`)를 **하이브리드 토폴로지**로 구성한다:
- **공유 라이브러리(in-process)**: `contracts`, U-4 PolicyCore, U-5 AuditClient — 각 서비스가 import.
- **런타임 프로세스(loopback 통신)**: 제어 서버(FastAPI), 감사 writer(단일), 전송 프록시(mitmproxy), RBI 서버(Playwright/Chromium), Chrome 확장(MV3), cage 실행기(on-demand).

의존은 `U-1/U-2/U-3 → U-4, U-5` 단방향이며 순환이 없다(NFR-6). U-2→U-3는 코드 참조가 아닌 런타임 트래픽 경유다.

## 2. 핵심 설계 원칙 (제약 반영)
- **fail-closed**(FR-5.4, NFR-8): 정책·감사·집행 지점 준비가 확인되지 않으면 보호 동작을 허용하지 않는다. 감사 writer 불가 시 새 보호 동작 금지.
- **검증 단일 소스**(Q3=A): ML-DSA-65 검증은 U-4 라이브러리 하나로. 실행 환경엔 공개키만, HMAC 대체·가짜 성공 금지(FR-4.2).
- **단일 writer 감사**(Q2=A): 전용 writer 프로세스가 loopback 수신 후 JSONL append. event_id 유일·행 무손상.
- **공통 판정/오류 계약**(Q4=A): `verdict`·`reason_code`·safe_location·recommended_action을 `contracts`에 정의, 모든 Unit·UI·CLI 공유. workflow_id로 통합 조회.
- **제어 평면 집약**(Q5=A): FastAPI 제어 서버가 상태·이벤트를 loopback로 노출, 토큰/Origin/Host 검증. 최소 상태 화면(§6).
- **C-SCOPE-1**: 성능·편의를 위해 검사 전 전송·TLS 해제·검증 실패 허용을 도입하지 않는다.

## 3. 컴포넌트 요약
| ID | 컴포넌트 | 형태 | 언어 | 의존 | 주요 FR | 선행 검증 |
|---|---|---|---|---|---|---|
| C0 | contracts | 공유 lib | Py | — | 공통 타입 | — |
| C1 | U-4 PolicyCore | 공유 lib | Py | contracts | FR-4.1~4.4 | V-2 |
| C2 | U-5 AuditTrail | writer+lib | Py | contracts | FR-5.1~5.4, FR-0.x | — |
| C3 | U-3 SecretGuard | mitmproxy | Py | U-4,U-5 | FR-3.1~3.6 | V-3 |
| C4 | U-2 AgentCage | CLI | Py | U-4,U-5 | FR-2.1~2.5 | V-1 |
| C5 | U-1 WebIsolate | MV3+RBI | TS+Py | U-4,U-5 | FR-1.1~1.6 | V-4 |
| — | 제어 서버 | FastAPI | Py | U-5,상태 | FR-0.1~0.3, FR-5.3 | — |

## 4. 구현 순서 (Q2=A)
`contracts → U-4 PolicyCore → U-5 AuditTrail → U-3 SecretGuard → U-2 AgentCage → U-1 WebIsolate`. Construction per-unit loop가 이 순서를 따른다.

## 5. 검증·품질 게이트 매핑
- **종단**: D-1(U-1), D-2(U-2+U-4), D-3(U-3), T-FLOW(통합).
- **경계/실패**: T-SIGN·T-KEY·T-TOCTOU(U-4/U-2), T-CAGE(U-2), T-SSRF·T-WEB(U-1), T-PROXY·T-BODY·T-TRANSPORT(U-3), T-AUDIT·T-PRIVACY(U-5), T-UX·T-BOOT(제어).
- **탐지 코퍼스**: S-01~08 BLOCK / B-01~08 ALLOW (NFR-10: TP=8/FN=0/FP=0/TN=8).
- **PBT(Partial 강제 PBT-02/03/07/08/09)**: contracts 직렬화, U-4 서명 bytes, U-3 탐지·escape 복원·청크 병합, U-5 hash·동시성, U-1 URL 정규화·SSRF 판정.
- **Security(Full)**: 프록시 강제경유·업스트림 TLS·SSRF·서명검증·fail-closed 감사·loopback 인증 등 집행 지점. 비해당 규칙은 이후 단계에서 N/A 표기.
- **Resiliency**: N/A(단일 장비, opt-out).

## 6. MVP 범위 반영 (Q1=A)
- MVP: D-1/D-2/D-3 정상+차단 경로 실동작 + 보안 집행형 NFR(NFR-3/4/5/8/9/10). 이 설계의 모든 컴포넌트가 MVP 핵심.
- 유예: 성능 목표(NFR-1/2 수치·최적화), 사용성 세부(NFR-12 측정), P1/P2 기능. 설계는 이를 수용하되 MVP에선 "동작 확인"에 집중.

## 7. 미해결/추적
- 상세 스키마(policy.yaml 필드, 이벤트 필드), 탐지 룰 세부, RBI 제어 메시지 스펙 → Functional Design.
- 버전·digest 잠금(C-DEP-1) → smoke test 통과 값으로 확정.
- V-1~V-4 → NFR/Infrastructure Design·Build&Test에서 실행.
