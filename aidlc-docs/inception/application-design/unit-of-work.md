# AEGIS — Units of Work

작성일: 2026-09-07 | 단계: INCEPTION → Units Generation (Part 2) | 출처: application-design.md, stories.md, unit-of-work-plan.md
분해 결정(전부 A): contracts 독립 기반 UOW(Q1) · U-1 단일 UOW/두 코드 위치(Q2) · 공통 실행·제어 서버/UI를 U-5에 포함(Q3) · 공유 `tests/` + 유닛별 하위(Q4).

## 0. 개요
AEGIS를 **6개 작업 단위(Unit of Work, UOW)** 로 분해한다. UOW는 개발·테스트·완료를 함께 관리하는 경계이며, 배포 프로세스 수와 1:1이 아니다(단일 장비, "5 Unit ≠ 5 서비스", §4.1). 구현 순서는 Q2=A: **contracts → U-4 → U-5 → U-3 → U-2 → U-1**. 각 UOW는 Construction per-unit loop(Functional Design → NFR Req → NFR Design → Infra Design → Code Gen)를 순차 통과한다.

## 1. UOW 목록

| UOW | 이름 | 유닛 | 형태 | 언어 | 코드 위치 | 선행 검증 | 스토리 수(P0) |
|---|---|---|---|---|---|---|---|
| **UOW-0** | Contracts | `contracts` | 공유 lib | Py | `src/aegis/contracts/` | — | 1 (S-U4-4) |
| **UOW-1** | PolicyCore | U-4 | 공유 lib | Py | `src/aegis/policy/` | V-2 | 3 |
| **UOW-2** | AuditTrail & Control | U-5 (+제어 서버·UI·FR-0.x) | writer 프로세스 + lib + FastAPI + 정적 UI | Py + 정적 HTML/CSS/TS | `src/aegis/audit/`, `src/aegis/control/`, `apps/ui/`, `scripts/aegis` | — | 8 |
| **UOW-3** | SecretGuard | U-3 | mitmproxy addon 프로세스 | Py | `src/aegis/guard/` | V-3 | 6 |
| **UOW-4** | AgentCage | U-2 | CLI 실행기 | Py | `src/aegis/cage/` | V-1 | 5 |
| **UOW-5** | WebIsolate | U-1 | MV3 확장 + RBI 서버(2 코드 위치) | TS + Py | `apps/extension/`(TS), `src/aegis/web/`(Py) | V-4 | 6 |

합계 P0 스토리 = 1+3+8+6+5+6 = **29 배정 슬롯** (S-U4-4는 UOW-0 primary + UOW-1 shared로 2회 계수). 고유 P0 스토리 25개 전부 배정(§story-map).

## 2. UOW 상세

### UOW-0 · Contracts (기반, 최우선)
- **책임**: 모든 Unit이 공유하는 데이터 타입·판정 계약을 단일 정의. `verdict`, `reason_code`, `Judgment{policy_id, policy_version, policy_digest, pubkey_id, rule_id, verdict, reason_code}`, `AuditEvent`(원문·비밀·인자·개인키 필드 없음), `safe_location`, `recommended_action`, 차단 응답 코드(`AEGIS_SECRET_BLOCKED`, `AUDIT_UNAVAILABLE` 등).
- **왜 먼저**: 이후 모든 UOW가 안정된 계약에 의존(NFR-6 순환 없음). 직렬화 왕복 PBT(PBT-02/03/07/08/09)를 여기서 확립.
- **스토리**: S-U4-4(공통 판정 식별자 계약, primary).
- **완료 정의(DoD)**: 계약 타입 직렬화 왕복 PBT 통과, 다른 UOW가 import만으로 사용 가능, 원문/비밀 필드 부재 정적 확인.

### UOW-1 · U-4 PolicyCore (신뢰 앵커)
- **책임**: 공통/정책 스키마 검증(FR-4.1), ML-DSA-65 원본 bytes 서명 검증(FR-4.2, 서명 메시지 = `ASCII("AEGIS-OPENSHELL-POLICY-v1") + 0x00 + policy.yaml raw bytes`), 신뢰키 교체·폐기(FR-4.3), 판정 산출(FR-4.4). 실행 환경엔 **공개키만** — HMAC 대체·가짜 성공 금지.
- **의존**: `contracts`.
- **스토리**: S-U4-1, S-U4-2, S-U4-3 + S-U4-4(계약 소비자, shared).
- **선행 검증**: **V-2**(liboqs ML-DSA-65) 통과 전 관련 P0 완료 표시 금지.
- **DoD**: T-SIGN·T-KEY 통과, 1 bit 변조 검증 실패, 서명 bytes PBT 통과, V-2 통과.

### UOW-2 · U-5 AuditTrail & Control (기록 + 제어 평면)
- **책임**: 단일 writer JSONL 순차 기록·조회(FR-5.1), 원문 없는 evidence_hash(FR-5.2, NFR-4), 통합 상태 UI 3카드·최근 이벤트(FR-5.3), 필수 감사 실패 시 fail-closed(FR-5.4, NFR-8/9). **Q3=A 포함**: 단일 실행 진입점 `scripts/aegis`(doctor/up/down/demo/test, FR-0.1), 컴포넌트 상태 구분(FR-0.2), workflow_id 전파(FR-0.3), FastAPI 제어 서버 loopback 집약(Q5=A, 토큰/Origin/Host 검증).
- **구성**: 전용 **감사 writer 프로세스**(단일 writer, loopback 수신) + `AuditClient` 라이브러리(각 Unit이 import) + FastAPI 제어 서버 + 정적 UI(`apps/ui/`).
- **의존**: `contracts`. (제어 서버는 U-5 조회 + 각 서비스 상태 loopback.)
- **스토리**: S-U5-1, S-U5-2, S-U5-3, S-U5-4, S-C-1, S-C-2, S-C-3, S-C-4.
- **DoD**: T-AUDIT·T-PRIVACY(로그/stdout/UI에 원문·비밀 0건)·T-UX·T-BOOT 통과, 동시성 PBT 통과, fail-closed 전이(감사 불가 시 새 보호 동작 금지) 검증.

### UOW-3 · U-3 SecretGuard (D-3 전송 보호)
- **책임**: 프록시 강제 경유(FR-3.1), 요청 정규화+시크릿 8종 탐지(FR-3.2, NFR-10, escape·청크 복원, LLM 판정 호출 없음), 전송 전 403 차단(FR-3.3, `AEGIS_SECRET_BLOCKED`), 정상 인증·콘텐츠 무손상 전달(FR-3.4), 검사 불가 요청 명시적 거부(FR-3.5, 413/415/400/503), TLS·지원 제공자 한정(FR-3.6, NFR-5, 업스트림 TLS 검증 유지).
- **의존**: `contracts`, U-4(검증 호출), U-5(기록). U-2와는 런타임 트래픽 경유(코드 의존 아님).
- **선행 검증**: **V-3**(프록시 CA/egress).
- **스토리**: S-U3-1 ~ S-U3-6.
- **DoD**: 고정 코퍼스 S-01~08 BLOCK / B-01~08 ALLOW → TP=8/FN=0/FP=0/TN=8, 탐지·escape 복원·청크 병합 PBT 통과, T-PROXY·T-BODY·T-TRANSPORT 통과, C-SCOPE-1(경고/통과 대체 없음) 준수.

### UOW-4 · U-2 AgentCage (D-2 정책·샌드박스)
- **책임**: 검증 후 실제 OpenShell 실행(FR-2.1, `aegis-cage run`), 검증본=적용본 TOCTOU(FR-2.2, policy_digest), 최소 워크스페이스·통신 권한(FR-2.3), 실행 시작·거부·종료 기록(FR-2.4, 인자·환경변수 미저장), 실행 중 정책 고정·재검증(FR-2.5).
- **의존**: `contracts`, U-4(서명·스키마 검증, 공개키만), U-5(기록).
- **선행 검증**: **V-1**(OpenShell/Landlock/컨테이너 격리) — 통과 전 D-2 관련 P0 완료 표시 금지(WSL2 게이팅).
- **스토리**: S-U2-1 ~ S-U2-5.
- **DoD**: 미서명/변조/미신뢰 키 시 OpenShell 생성·자식 명령 0회, T-SIGN·T-TOCTOU·T-CAGE·T-PRIVACY 통과, D-2 종단 통과, V-1 통과.

### UOW-5 · U-1 WebIsolate (D-1 웹 격리, 두 코드 위치)
- **책임**: 탐색 판정 직접/격리/차단(FR-1.1), 픽셀 중계·로컬 HTML 부재(FR-1.2), 위험 액션 차단·한글 사유(FR-1.3, §3 P0 차단 유지), 세션 인증·만료·데이터 폐기(FR-1.4), 격리 실패 시 안전한 재시도·우회 없음(FR-1.5, NFR-8), 원격 브라우저 SSRF 제한(FR-1.6).
- **구성(단일 UOW, 두 코드 위치, Q2=A)**: `apps/extension/`(Chrome MV3, TS — DNR 선-네비 차단·픽셀 viewer) + `src/aegis/web/`(Playwright/Chromium RBI 서버, Py). 둘은 loopback 제어 메시지+픽셀로 강결합 → 함께 설계·테스트.
- **의존**: `contracts`, U-4(검증), U-5(기록).
- **선행 검증**: **V-4**(브라우저-RBI 지연).
- **스토리**: S-U1-1 ~ S-U1-6.
- **DoD**: 로컬 HTML/JS/DOM 다운로드 0건, P0 위험 액션(다운로드/업로드/클립보드/password) 실제 차단, SSRF(loopback·사설·메타데이터·리다이렉트·DNS 변경) 거부, T-WEB·T-SSRF 통과. NFR-1 수치 목표는 `[Deferred:perf-NFR]`(동작만 확인).

## 3. 코드 조직 전략 (Greenfield)
- **monorepo, 단일 장비**. Python 패키지 `src/aegis/`(PEP 517), Chrome 확장 `apps/extension/`(TS 빌드), 제어 UI `apps/ui/`(정적 HTML/CSS/TS).
- **애플리케이션 코드는 워크스페이스 루트**(C-DEP-2). `aidlc-docs/`에는 코드 금지.
- **테스트(Q4=A)**: 공유 `tests/` + 유닛별 하위 디렉토리 —
  - `tests/contracts/`, `tests/policy/`, `tests/audit/`, `tests/guard/`, `tests/cage/`, `tests/web/`
  - `tests/corpus/`(S-01~08 / B-01~08 고정 코퍼스·기대결과, 구현 전 고정 §8.2, **합성/절대 무효 키만**)
  - `tests/fixtures/`(정책·인증서·시나리오), `tests/e2e/`(D-1~D-3 종단·T-FLOW 통합)
  - `tests/smoke/`(V-1~V-4 환경 smoke test)
- **설정**: `config/`(policy.yaml 예시·신뢰키(공개)·제공자 목록). 개인키는 저장소·실행 환경에 두지 않음.
- **진입점**: `scripts/aegis`(UOW-2 소유, doctor/up/down/demo/test).

## 4. 제약·게이팅 요약
- 순환 의존 없음(NFR-6): 방어 UOW(3/4/5) → UOW-1/UOW-2 단방향, UOW-0 최하위.
- 환경 게이팅: V-1(UOW-4), V-2(UOW-1), V-3(UOW-3), V-4(UOW-5). 미통과 시 관련 P0 완료 표시 금지.
- C-SCOPE-1/C-AIDLC-2: 성능·시제품 범위를 이유로 차단을 경고/통과로 완화하거나 P0를 축소하지 않는다.
- Security(Full) 집행 지점은 각 UOW DoD에 반영. Resiliency=N/A(단일 장비). PBT(Partial) 강제 대상은 UOW-0/1/3/5에 표기.
