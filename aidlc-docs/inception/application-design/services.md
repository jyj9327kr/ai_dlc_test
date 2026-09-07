# AEGIS — Services & Orchestration

작성일: 2026-09-07 | 단계: INCEPTION → Application Design | 토폴로지: Q1=A 하이브리드
"5 Unit ≠ 5 서비스"(§4.1). 아래 "서비스"는 런타임 프로세스 경계이며, 공유 라이브러리(contracts/U-4/U-5 client)는 프로세스 내부에서 import된다.

## 1. 런타임 프로세스(서비스) 목록
| 서비스 | 프로세스 | 담당 Unit | 통신 | 기동 |
|---|---|---|---|---|
| **제어 서버** | FastAPI(Py) | 제어 평면 | loopback API(토큰/Origin/Host 검증) | `aegis up` |
| **감사 writer** | 단일 writer(Py) | U-5 | loopback 수신(UDS/127.0.0.1) → JSONL append | `aegis up` |
| **전송 프록시** | mitmdump + addon(Py) | U-3 | 보호 클라이언트 강제 경유, 업스트림 TLS | `aegis up` |
| **RBI 서버** | Playwright + 고정 Chromium(Py) | U-1 | 확장↔서버 제어 메시지, 픽셀 릴레이 | `aegis up`(준비), 세션은 요청 시 |
| **Chrome 확장** | MV3(TS) | U-1 | DNR 사전판정 + 뷰어, 서버와 제어 메시지 | 사용자 설치 |
| **cage 실행기** | CLI+wrapper(Py) | U-2 | 사용자 `aegis-cage run` 시 기동, OpenShell 호출 | on-demand(`run`) |

- **공유 라이브러리(프로세스 내 import)**: `contracts`(C0), `U-4 PolicyCore`(C1, 검증), `U-5 AuditClient`(C2 emit). 각 서비스가 필요 시 import(Q3=A in-process 검증).

## 2. 오케스트레이션 패턴
- **단일 진입점**(FR-0.1): `scripts/aegis {doctor|up|down|demo|test}`. `up`은 제어 서버·프록시·감사 writer·RBI 준비 상태 표시. OpenShell 실행은 `run` 요청 시.
- **fail-closed 조정**(FR-5.4): 감사 writer health가 unavailable이면 제어 서버가 새 격리 입력·에이전트 실행·LLM 전송을 허용하지 않도록 신호. 이미 차단된 동작은 계속 차단. (독립 컴포넌트의 정상 작업을 일괄 중단하는 의미는 아님 — §2.2 fail-closed 정의)
- **정책 검증 흐름**(Q3=A): 각 방어 서비스가 U-4 라이브러리로 직접 검증(신뢰키=공개키만). cage는 CLI 내부에서 verify_then_run.
- **상태 집약**(Q5=A): 제어 서버가 각 서비스 상태를 loopback로 폴링/구독하여 3개 상태 카드로 노출(FR-0.2/5.3). 3초 내 상태 변화 반영.

## 3. workflow_id 전파 (FR-0.3)
- 실행 시작 시 `new_workflow_id()` 생성 → 제어 서버·CLI·시나리오 실행기·각 서비스에 전달.
- 각 서비스가 이벤트 emit 시 동일 workflow_id + 서로 다른 event_id 부여.
- 재실행은 새 workflow_id로 이전 실행의 이벤트·카운터와 분리(§8.1). 임의 다른 세션 ID로 이벤트·격리 세션 접근 불가.

## 4. 종단 시나리오 오케스트레이션
- **D-1(웹 격리)**: 확장 classify→ISOLATE → RBI open_session → relay/픽셀, 위험 액션 block → U-5 emit. 로컬 직접 요청 0건.
- **D-2(정책·샌드박스)**: `aegis-cage run` → U-4 verify_signature(스냅샷) → 통과 시 invoke_openshell, 실패 시 미호출 → U-5 record. 보호 HTTP 클라이언트는 U-3 경유(T-FLOW).
- **D-3(전송 보호)**: cage 내 보호 클라이언트 → 프록시 강제 경유 → normalize→detect → BLOCK 시 403·업스트림 미전송, ALLOW 시 무손상 전달 → U-5 emit.
- **T-FLOW**: 같은 workflow_id로 U-1 격리, U-2 검증·실행, U-2→U-3 실제 요청 경유·차단, U-5 조회가 연결됨.

## 5. 보안·검증 표기
- 모든 loopback 엔드포인트: 토큰·Origin·Host 검증(C-SEC-1~3, NFR-5, T-TRANSPORT).
- 업스트림 TLS 인증서 검증 유지(FR-3.6). 로컬 CA는 보호 클라이언트에만.
- **선행 환경 검증**: V-1(cage/OpenShell), V-2(U-4/liboqs), V-3(프록시 CA·egress), V-4(RBI 지연·가로채기).
