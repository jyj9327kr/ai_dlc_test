# AEGIS — Components

작성일: 2026-09-07 | 단계: INCEPTION → Application Design | 승인 결정: Q1~Q5=A
고수준 컴포넌트 정의(목적·책임·인터페이스). 상세 비즈니스 로직은 Functional Design(per-unit)에서 정의.

## 토폴로지 요약 (Q1=A 하이브리드)
- **in-process 공유 라이브러리**: `contracts`, U-4 PolicyCore, U-5 클라이언트 계약 → 각 Unit이 import.
- **별도 프로세스 (loopback 통신만)**: 감사 writer(U-5), mitmproxy 애드온(U-3), Playwright Chromium RBI 서버(U-1), FastAPI 제어 서버, Chrome MV3 확장.
- 프로세스 간은 loopback(UDS 또는 127.0.0.1)로만. 토큰·Origin·Host 검증(C-SEC).

---

## C0. contracts (공통 계약) — `src/aegis/contracts/`  [공유 라이브러리]
- **목적**: 모든 Unit·UI·CLI가 공유하는 데이터 타입·판정/오류 모델(Q4=A).
- **책임**:
  - 공통 판정 타입: `Verdict`(ALLOW/BLOCK/ERROR), `ReasonCode`(예: `POLICY_SIGNATURE_INVALID`, `AEGIS_SECRET_BLOCKED`, `AUDIT_UNAVAILABLE`, `SSRF_BLOCKED`, `RISKY_ACTION_BLOCKED`, `POLICY_SCHEMA_INVALID`, `UNTRUSTED_KEY` …).
  - 정책 식별자: `policy_id`, `policy_version`, `policy_digest`, `pubkey_id`, `rule_id`.
  - 감사 이벤트 스키마: `AuditEvent`(event_id, workflow_id, unit, verdict, reason_code, safe_location, target(host/command_label), recommended_action, ts, evidence_hash — **원문·비밀 없음**).
  - workflow_id/event_id 생성 규약, 안전한 위치 식별자 타입(배열 인덱스·헤더명 등).
- **인터페이스(고수준)**: 순수 데이터 타입 + 직렬화/역직렬화 함수(PBT 대상). 부수효과 없음.
- **의존**: 없음(최하위). **PBT**: 직렬화 왕복(PBT-02/03/07/08/09).

## C1. U-4 PolicyCore — `src/aegis/policy/`  [공유 라이브러리]
- **목적**: 공통 설정·OpenShell 정책의 스키마 검증과 ML-DSA-65 서명 검증, 신뢰키 관리(신뢰 앵커).
- **책임**:
  - 공통 설정(schema_version=1)·OpenShell policy(version=1) 스키마 검증(FR-4.1).
  - ML-DSA-65로 `policy.yaml` **원본 bytes** 서명 검증(FR-4.2). 서명 메시지 = `ASCII("AEGIS-OPENSHELL-POLICY-v1") + 0x00 + policy.yaml raw bytes`. 실행 환경엔 **공개키만**. HMAC 대체·가짜 성공 금지.
  - 신뢰키 목록(pubkey_id) 로드·수동 교체·폐기(FR-4.3). 서명 옆 임의 공개키 자동 신뢰 금지.
  - 검증된 **정책 스냅샷** 제공(TOCTOU 방지 입력, FR-2.2).
  - 공통 판정 결과(policy_id/version/digest/rule_id/verdict/reason_code) 제공(FR-4.4).
- **인터페이스(고수준, Q3=A in-process)**: `verify_policy(bytes, sig, trust_store) -> VerifyResult`, `load_common_config(path) -> Config`, `snapshot(policy_path) -> PolicySnapshot`, `trust_store(config) -> TrustStore`.
- **의존**: `contracts`만. 방어 Unit 미참조. **PBT**: bytes 무결성·직렬화(PBT 강제). **선행 검증**: V-2(liboqs ML-DSA-65 smoke test).

## C2. U-5 AuditTrail — `src/aegis/audit/`  [writer=별도 프로세스 + 클라이언트 라이브러리]
- **목적**: 구조화 이벤트의 단일 writer 순차 기록·조회, 통합 상태, 감사 실패의 fail-closed 반영.
- **책임**:
  - **단일 writer 프로세스**(Q2=A): loopback 수신 후 JSONL(ext4) append. 각 행 유효 JSON·event_id 유일·기존 이벤트 미수정(FR-5.1).
  - 원문 없는 증거·`evidence_hash` 계산 및 검증 도구(FR-5.2, NFR-4).
  - 조회 API(workflow_id/unit/verdict 필터)와 최근 이벤트(FR-5.3).
  - 감사 불가(디스크 실패·writer 중단) 시 `AUDIT_UNAVAILABLE` 신호 → 새 보호 동작 금지(FR-5.4, fail-closed).
- **인터페이스(고수준)**:
  - 클라이언트(라이브러리): `emit(event: AuditEvent) -> Ack|AuditUnavailable`(loopback로 writer에 송신).
  - writer(프로세스): loopback 수신 → append; health 상태 노출.
  - 조회: `query(filter) -> list[AuditEvent]`, `verify_hash(event) -> bool`.
- **의존**: `contracts`만. 방어 Unit 미참조. **PBT**: evidence_hash·직렬화·동시성(PBT 강제).

## C3. U-3 SecretGuard — `src/aegis/guard/`  [mitmproxy 애드온 프로세스]
- **목적**: 보호 클라이언트의 지원 LLM 요청을 전송 전 검사, 시크릿 탐지 시 전체 차단.
- **책임**:
  - 프록시 강제 경유(FR-3.1) — 환경변수만으론 불인정; 프록시 종료 시 직접 fallback 없음.
  - 요청 정규화(JSON 문자열·배열·중첩·escape 복원·청크 병합)와 탐지(정규식+문맥 엔트로피, LLM 판정 없음)(FR-3.2). 고정 코퍼스 S-01~08 전부 BLOCK.
  - 탐지 시 403 + `AEGIS_SECRET_BLOCKED`·event_id·rule_id·안전한 위치, 업스트림 미전송(FR-3.3).
  - 정상 인증·본문·SSE 무손상 전달, 인증값 미로깅(FR-3.4).
  - 검사 불가 명시적 거부(413/415/400/503)(FR-3.5). 경고 후 통과 금지.
  - TLS·지원 제공자 host/port/path/method 한정, 업스트림 인증서 검증 유지(FR-3.6).
- **인터페이스(고수준)**: mitmproxy addon hook(`request`/`responseheaders`) → `inspect(request) -> Verdict`; 로컬 CA는 보호 클라이언트에만 신뢰 설정.
- **의존**: U-4(탐지 정책), U-5(감사). **PBT 강제**: 탐지·escape 복원·청크 병합·직렬화(PBT-02/03/07/08/09).

## C4. U-2 AgentCage — `src/aegis/cage/`  [Python wrapper + OpenShell CLI]
- **목적**: 검증된 정책으로만 실제 OpenShell 샌드박스를 실행하고 자원 경계를 집행.
- **책임**:
  - `aegis-cage run --policy <path> -- <command>`: U-4 검증 통과 후에만 OpenShell 호출(FR-2.1). 실패 시 OpenShell 생성·자식 명령 0회.
  - 검증본=적용본(TOCTOU): 검증된 스냅샷 적용, 변경 원본 미사용, policy_digest 기록(FR-2.2).
  - 최소 워크스페이스·통신 권한, 금지 자원(호스트 홈 표식·SSH·Docker 소켓·비허용 통신) 실패(FR-2.3).
  - 실행 시작·거부·종료 기록(command_label·digest·pubkey_id·판정·종료), 인자·환경 전체 미저장(FR-2.4).
  - 실행 중 정책 고정, 재적용 시 종료·재검증·재생성(FR-2.5).
- **인터페이스(고수준)**: CLI 진입점 + `run(policy_path, command) -> RunResult`. U-3 프록시 강제 경유 대상 클라이언트를 샌드박스 내에 둠(T-FLOW).
- **의존**: U-4(서명 검증), U-5(감사). **선행 검증**: V-1(OpenShell/Landlock/컨테이너). **PBT**: 스냅샷 무결성.

## C5. U-1 WebIsolate — `apps/extension/`(MV3 TS) + `src/aegis/web/`(RBI 서버, Playwright)  [확장 + RBI 프로세스]
- **목적**: 미분류·위험 웹을 서버 브라우저에서 격리 실행하고 로컬에는 픽셀만 전달, 위험 액션 차단.
- **책임**:
  - 확장(MV3): DNR 기반 사전 판정(직접/격리/차단), 로컬 선실행 방지, 뷰어 UI(FR-1.1, FR-1.3 UI).
  - RBI 서버(Playwright+고정 Chromium): 픽셀·허용 입력 릴레이, HTML/DOM 로컬 미전달(FR-1.2).
  - 위험 액션(다운로드·업로드·클립보드·`type=password`·mailto) 원격 집행 차단·한글 사유(FR-1.3).
  - 세션 인증·만료·데이터 폐기(FR-1.4), 격리 실패 시 안전 재시도·로컬 fallback 없음(FR-1.5).
  - 원격 브라우저 SSRF 제한(loopback·사설·메타데이터·비HTTP(S)·리다이렉트·하위요청)(FR-1.6).
- **인터페이스(고수준)**: 확장↔RBI 제어 메시지(구조화, HTML 삽입 금지); RBI 서버 세션 API(인증 토큰). 정책은 U-4, 이벤트는 U-5.
- **의존**: U-4(정책), U-5(이벤트). **선행 검증**: V-4(브라우저-RBI 지연·가로채기). **PBT**: URL 정규화·SSRF 판정.

---

## 컴포넌트 요약표
| ID | 컴포넌트 | 형태 | 언어 | 의존 | 주요 검증 | MVP |
|---|---|---|---|---|---|---|
| C0 | contracts | 공유 라이브러리 | Py | — | 직렬화 PBT | 핵심 |
| C1 | U-4 PolicyCore | 공유 라이브러리 | Py | contracts | T-SIGN,T-KEY,T-TOCTOU / V-2 | 핵심 |
| C2 | U-5 AuditTrail | writer 프로세스+lib | Py | contracts | T-AUDIT,T-PRIVACY | 핵심 |
| C3 | U-3 SecretGuard | mitmproxy 애드온 | Py | U-4,U-5 | D-3,S/B,T-PROXY,T-BODY,T-TRANSPORT | 핵심 |
| C4 | U-2 AgentCage | CLI+wrapper | Py | U-4,U-5 | D-2,T-SIGN,T-CAGE / V-1 | 핵심 |
| C5 | U-1 WebIsolate | MV3 확장+RBI 서버 | TS+Py | U-4,U-5 | D-1,T-WEB,T-SSRF / V-4 | 핵심 |
| — | 제어 서버 | FastAPI 프로세스 | Py | U-5 조회, 각 Unit 상태 | T-UX,T-BOOT,T-TRANSPORT | 핵심 |

순환 의존 없음(NFR-6): 방어 Unit → U-4/U-5 단방향, contracts는 최하위.
