# AI-DLC State Tracking — AEGIS

## Project Information
- **Project Name**: AEGIS (개발자 워크스페이스 3-경계 보안 시스템)
- **Project Type**: Greenfield
- **Start Date**: 2026-09-07T07:15:41Z
- **Current Phase**: CONSTRUCTION
- **Current Stage**: UOW-0 Contracts — Code Generation 완료, 완료 승인 대기 (다음: UOW-1 U-4 PolicyCore)
- **Complexity**: Complex (근거: requirements.md §1.1, constraints.md C-AIDLC-1)
- **Requirements Depth**: Comprehensive

## Workspace State
- **Existing Code**: No (애플리케이션 소스코드·빌드파일 없음)
- **Reverse Engineering Needed**: No (Greenfield — 생략)
- **Workspace Root**: /home/jyj/aidlc-workshop/aegis

## Code Location Rules
- **Application Code**: Workspace root (`apps/extension/`, `src/aegis/{web,cage,guard,policy,audit,contracts}/`, `tests/`, `scripts/`, `config/`) — NEVER in aidlc-docs/ (근거: constraints.md C-DEP-2)
- **Documentation**: aidlc-docs/ only
- **Structure patterns**: See construction/code-generation.md

## Input Documents (개발 착수 기준안)
- `requirements/requirements.md` (v4.0) — 제품 요구사항
- `requirements/constraints.md` (v4.0) — 기술·보안·AI-DLC 절차 제약
- 위 문서는 "기준안"이며 이전 사람의 승인으로 간주하지 않는다. (근거: constraints.md C-AIDLC-1, C-CHANGE-1)

## Extension Configuration
| Extension | Enabled | Mode | Decided At | Enforced Rules |
|---|---|---|---|---|
| Security Baseline | Yes | Full (blocking) | 2026-09-07T07:26:01Z (사용자 답변 Q1=A) | SECURITY-01 ~ SECURITY-15 (해당 시 적용, N/A 표시) |
| Resiliency Baseline | No | — | 2026-09-07T07:26:01Z (사용자 답변 Q2=A) | 없음 (opt-out — 전체 규칙 미로드) |
| Property-Based Testing | Yes | **Partial (blocking)** | 2026-09-07T07:26:01Z (사용자 답변 Q3=B) | PBT-02, PBT-03, PBT-07, PBT-08, PBT-09 강제 / 나머지 권고 |

**결정 근거**: Requirements Analysis Step 5.1 opt-in 처리 완료. 답변 출처는 `requirement-verification-questions.md`, 날짜 2026-09-07. Resiliency는 opt-out이므로 full rules 미로드. Security/PBT full rules 로드 완료.

## Environment Decision (Q4)
- **선택**: B — WSL2 선진행 + V-1/V-2 smoke test 게이팅, 실패 시 Ubuntu 24.04 VM 전환.
- **현재 장비**: WSL2 (Linux 6.18 microsoft-standard-WSL2).
- **필수 선행 검증**: V-1(OpenShell/Landlock/컨테이너 격리), V-2(liboqs ML-DSA-65). 통과 전 관련 P0(D-2 등) 완료 표시 금지. (근거: constraints.md C-SCOPE-2, C-DEP-3, requirements.md §10.2)

## Baseline Adoption (Q5)
- **선택**: A — `requirements/requirements.md` v4.0, `requirements/constraints.md` v4.0을 승인된 요구 입력으로 채택. `aidlc-docs/inception/requirements/`에 반영.

## Stage Progress
### 🔵 INCEPTION PHASE
- [x] Workspace Detection (Greenfield 확정)
- [~] Reverse Engineering — SKIPPED (Greenfield, 기존 코드 없음)
- [x] Requirements Analysis (승인 완료 2026-09-07T07:30:50Z — Comprehensive)
- [x] User Stories (승인 완료 2026-09-07T08:05:00Z — stories.md 25개 P0 스토리 + P1/P2 스텁, personas.md 3 페르소나)
- [x] Workflow Planning (승인 완료 2026-09-07T08:18:00Z — execution-plan.md)
- [x] Application Design — 승인 완료 2026-09-07T08:38:00Z (components/component-methods/services/component-dependency/application-design.md, 결정 Q1~Q5=A)
- [x] Units Generation — 승인 완료 2026-09-07T08:58:00Z (6 UOW 분해: contracts/U-4/U-5+제어/U-3/U-2/U-1, Q2=A 순서. unit-of-work.md / unit-of-work-dependency.md / unit-of-work-story-map.md. 25개 P0 스토리 100% 배정, 순환 없음)

### 🟢 CONSTRUCTION PHASE (Unit별 순차 — Q2=A: contracts → U-4 → U-5 → U-3 → U-2 → U-1)
**UOW-0 Contracts** (Code Generation 완료 — 승인 대기)
- [x] Functional Design — 승인 완료 2026-09-07T09:20:00Z (domain-entities/business-rules/business-logic-model, 결정 Q1~Q6=A)
- [x] NFR Requirements — 승인 완료 2026-09-07T09:34:00Z (nfr-requirements/tech-stack-decisions, 결정 Q1~Q4=A, zero 3rd-party)
- [x] NFR Design — 승인 완료 2026-09-07T09:44:00Z (nfr-design-patterns/logical-components, 결정 Q1~Q3=A)
- [~] Infrastructure Design — SKIPPED (stdlib 전용 라이브러리, 인프라·배포·클라우드 자원 없음)
- [x] Code Generation — Part 2 실행 완료 2026-09-07T10:10:00Z (9/9 Step, 8 소스 + 6 테스트, `35 passed`, zero 3rd-party) — 완료 승인 대기
**UOW-1 PolicyCore (U-4)** (진행 중 — 선행 V-2)
- [x] Functional Design — 승인 완료 2026-09-07T10:32:00Z (domain-entities/business-rules/business-logic-model, Q1~Q6=A)
- [x] NFR Requirements — 승인 완료 2026-09-07T10:46:00Z (nfr-requirements/tech-stack-decisions, Q1~Q6=A, liboqs+PyYAML 최소 의존)
- [~] NFR Design — 산출물 생성 완료 (nfr-design-patterns/logical-components, Q1~Q5=A, P1~P5 + verifier/keystore/schema/evaluator 모듈) — 완료 승인 대기
- [ ] Infrastructure Design
- [ ] Code Generation
**UOW-2~5**: 대기 (순차)
- [ ] Build and Test — EXECUTE (전 Unit 완료 후)

### 🟡 OPERATIONS PHASE
- [ ] Operations (placeholder)

## Open Items
- [x] Extension opt-in 3건 결정 완료 (Security=Full, Resiliency=off, PBT=Partial)
- [x] 요구 확인 질문 응답·정합성 검사 완료 (모순 없음)
- [x] Requirements Analysis 사용자 승인 완료 (2026-09-07T07:30:50Z)
- [x] MVP 범위 clarification 확정 (Q1=A 핵심 보안 기능 경로 우선 / Q2=A 문서 기본 순서, 2026-09-07T07:41:00Z)
- [ ] V-1/V-2 환경 smoke test (WSL2) — Inception 초기 실행 예정
- [ ] V-3/V-4 검증 — Application/Infrastructure Design 단계 (근거: requirements.md §10.2)
