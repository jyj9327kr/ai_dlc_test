# AEGIS — User Stories

작성일: 2026-09-07 | 단계: INCEPTION → User Stories (Part 2) | 출처: `requirements/requirements.md` v4.0 §4.2, §5, §8
승인된 방법론(전부 A): Unit 중심+페르소나 태그(Q1) · Epic→하위 스토리(Q2) · Given/When/Then 3경로(Q3) · MVP/유예 태그(Q4) · P1/P2 스텁(Q5).

## 읽는 법
- **조직**: US-1~US-6을 Epic으로 두고, 구현 의존성 순서(Q2=A: contracts+U-4/U-5 → U-3 → U-2 → U-1)로 정렬. 스토리 ID = `S-<Unit>-<n>`.
- **페르소나**: P-A 개발자 · P-B 정책 관리자 · P-C 검증 동료 (`personas.md`).
- **태그**: `[MVP:P0-core]` = 핵심 보안 기능 경로 + 보안 집행형 NFR(NFR-3/4/5/8/9/10) 포함(MVP 필수). `[Deferred:perf-NFR]`·`[Deferred:usability-NFR]`·`[Deferred:P1]`·`[Deferred:P2]` = MVP 이후.
- **3경로**: 정상(Normal) / 거부(Reject·차단) / 장애(Failure·fail-closed). C-SCOPE-1에 따라 거부·fail-closed 경로는 1급 수용 기준이며 경고/통과로 대체하지 않는다.
- **추적**: 각 스토리에 FR·검증 ID(D-1~D-3, S/B 코퍼스, T-*) 연결.

---

# Epic US-5 → Unit U-4 PolicyCore
*정책 관리자(P-B)로서 검증된 정책과 신뢰키만으로 안전하게 운영하고 싶다.* 방어 Unit이 참조하는 신뢰 앵커이므로 **가장 먼저 확립**.

## S-U4-1 공통/정책 스키마 검증 `[MVP:P0-core]`
개발/관리자(P-B)로서 잘못된 설정이 로드되지 않도록 두 스키마를 분리 검증하고 싶다. (FR-4.1)
- **Normal** — Given 유효한 공통 설정(schema_version=1)과 OpenShell policy(version=1), When 로드, Then 두 스키마를 혼동 없이 검증·수용한다.
- **Reject** — Given 필수값 부재·잘못된 타입·미지원 버전·중복 YAML 키·알 수 없는 보안 설정, When 로드, Then 로드를 거부한다.
- **Failure** — Given 부분 파싱만 성공, When 활성화 시도, Then 부분 결과를 활성화하지 않는다(FR-4.4).
- INVEST: 순수 검증 로직·독립 테스트 가능. 추적: FR-4.1, T-SIGN.

## S-U4-2 ML-DSA-65 원본 bytes 서명/검증 `[MVP:P0-core]`
관리자(P-B)로서 policy.yaml 원본 bytes의 진위를 양자내성 서명으로 검증하고 싶다. (FR-4.2, NFR-3)
- **Normal** — Given 오프라인 도구가 만든 정상 서명, When 검증, Then 통과한다. 서명 메시지 = `ASCII("AEGIS-OPENSHELL-POLICY-v1") + 0x00 + policy.yaml raw bytes`.
- **Reject** — Given 공백·개행 포함 한 바이트라도 변경된 정책, When 검증, Then 실패한다.
- **Failure** — Given 실행 환경, When 서명 시도, Then 공개키만 존재해 서명 불가하며, 대체 HMAC·가짜 검증 성공을 사용하지 않는다.
- INVEST: 직렬화 왕복·bytes 무결성 → PBT 대상(PBT-02/03/07/08/09). 추적: FR-4.2, NFR-3, T-SIGN.

## S-U4-3 신뢰키 교체·폐기 `[MVP:P0-core]`
관리자(P-B)로서 신뢰키를 수동 교체·폐기하고 안전하게 재시작하고 싶다. (US-5, FR-4.3)
- **Normal** — Given 재서명된 정책 + 신규 신뢰키, When 재시작, Then 정상 기동한다.
- **Reject** — Given 신뢰 저장소에 없는 pubkey_id·제거된 키·서명 옆에 놓인 임의 공개키, When 다음 실행, Then 거부하며 자동 신뢰하지 않는다.
- **Failure** — Given 키 폐기 운영, When 실행, Then 폐기 키의 기존 관련 실행을 종료한다.
- INVEST: 신뢰목록 상태 관리·독립 테스트. 추적: FR-4.3, T-KEY.

## S-U4-4 공통 판정 식별자 계약 `[MVP:P0-core]`
모든 Unit이 동일 의미의 정책 판정 식별자를 쓰도록 계약을 제공하고 싶다. (FR-4.4)
- **Normal** — Given 정책 판정, When 결과 제공, Then `policy_id, policy_version, policy_digest, rule_id, verdict, reason_code`를 모든 Unit이 동일 의미로 사용한다.
- **Reject** — Given 공통 설정 갱신, When 적용, Then 검증 후 재시작으로만 적용한다.
- **Failure** — Given 검증 미완료, When 활성화, Then 부분 파싱 결과를 활성화하지 않는다.
- INVEST: `contracts` 모듈의 공통 타입·reason code. 추적: FR-4.4, T-FLOW.

---

# Epic US-4 → Unit U-5 AuditTrail + 공통 상태
*개발자(P-A)로서 어떤 보호가 켜져 있고 왜 차단됐는지 알고 싶다.* U-4와 함께 기반 확립.

## S-U5-1 단일 writer JSONL 순차 기록·조회 `[MVP:P0-core]`
개발자(P-A)로서 동시 기록에도 무결한 이벤트 로그를 남기고 조회하고 싶다. (FR-5.1)
- **Normal** — Given 여러 Unit 동시 기록, When append, Then 각 행이 유효 JSON·event_id 중복 없음, 조회 가능.
- **Reject** — Given 제품 API, When 수정·삭제 요청, Then 그런 기능이 없고 기존 이벤트를 다시 쓰지 않는다(호스트 관리자 파일 변경을 막는 WORM이라 주장하지 않음).
- **Failure** — Given 동시 쓰기 경합, When append, Then 직렬화되어 손상 행이 발생하지 않는다.
- INVEST: 직렬화·동시성 → PBT 대상. 추적: FR-5.1, T-AUDIT.

## S-U5-2 원문 없는 증거·evidence_hash `[MVP:P0-core]`
개발자(P-A)로서 로그에 비밀·원문이 남지 않는다고 신뢰하고 싶다. (FR-5.2, NFR-4)
- **Normal** — Given 이벤트 기록, When 저장, Then evidence_hash를 안전한 메타데이터로 계산하고 검증 도구를 제공한다.
- **Reject** — Given 요청 본문·전체 URL query·원시 헤더·키·PQC/CA 개인키·명령 인자, When 로그/stdout/stderr/UI 오류/내보내기 검색, Then 0건이어야 한다.
- **Failure** — Given 증거 계산 불가, When 기록, Then fail-closed로 이어진다(S-U5-4 연계).
- INVEST: 해시·직렬화 순수 로직 → PBT 대상. 추적: FR-5.2, NFR-4, T-PRIVACY.

## S-U5-3 통합 상태 UI (3 카드·최근 이벤트) `[MVP:P0-core]` / 화질·집계 `[Deferred:P1]`
개발자(P-A)로서 세 보호 상태와 최근 판정을 한 화면에서 확인하고 싶다. (US-4, FR-5.3, §6)
- **Normal** — Given 실행 중, When 대시보드 열기, Then 3 카드(이름·상태·정책 버전)와 시간순 최근 이벤트, workflow_id·Unit·verdict 필터, 상세(사유·host 또는 command_label·event_id·권장 행동)를 보여주고 새 이벤트가 3초 내 표시된다. 색상만으로 전달하지 않고 키보드 Tab·포커스·접근 가능 알림 제공.
- **Reject** — Given 목적지·오류 메시지, When 렌더링, Then HTML로 해석하지 않는다. 비밀값 보기·보호 예외 버튼은 P0에 없다.
- **Failure** — Given 화면 상태와 실제 집행 결과 충돌, When 표시, Then 보호 활성 표시를 내린다.
- 집계 지표는 `[Deferred:P1]`. INVEST: UI 컴포넌트·독립 테스트. 추적: FR-5.3, T-UX, NFR-12.

## S-U5-4 필수 감사 실패 → fail-closed `[MVP:P0-core]`
개발자(P-A)로서 감사 기록이 불가하면 보호되지 않은 동작이 진행되지 않길 바란다. (FR-5.4, NFR-8/9)
- **Normal** — Given 감사 저장소 정상, When 보호 동작, Then 정상 기록·진행.
- **Reject** — Given 디스크 쓰기 실패·writer 중단, When 새 격리 입력·에이전트 실행·LLM 전송 시도, Then 허용하지 않고 `AUDIT_UNAVAILABLE`을 표시한다. 이미 차단한 동작은 계속 차단.
- **Failure** — Given 기록 실패, When 상태 판단, Then 정상 감사 완료로 표시하지 않는다.
- INVEST: fail-closed 상태 전이·독립 테스트. 추적: FR-5.4, T-AUDIT, NFR-8, NFR-9.

---

# Epic US-3 → Unit U-3 SecretGuard  (D-3 전송 보호)
*개발자(P-A)로서 프롬프트에 섞인 키가 외부에 나가지 않게 하고 싶다.* 통합 순서 1번째 방어(U-3).

## S-U3-1 프록시 강제 경유 `[MVP:P0-core]`
개발자(P-A)로서 보호 클라이언트의 LLM 요청이 반드시 프록시를 거치게 하고 싶다. (FR-3.1)
- **Normal** — Given AgentCage 내 보호 HTTP 클라이언트, When 정상 요청, Then SecretGuard를 통해 전송된다.
- **Reject** — Given 프록시 종료 또는 프록시 설정 제거한 직접 연결, When 요청, Then 모두 실패한다. 환경변수만 설정한 상태는 강제 경유로 인정하지 않는다.
- **Failure** — Given 프록시 중단 후, When 직접 fallback 시도, Then fallback이 없어야 한다.
- 추적: FR-3.1, T-PROXY, D-3.

## S-U3-2 요청 정규화 + 시크릿 8종 탐지 `[MVP:P0-core]`
개발자(P-A)로서 본문·헤더의 시크릿을 escape·청크 경계까지 복원해 탐지하고 싶다. (FR-3.2, NFR-10)
- **Normal** — Given 무해한 JSON(escape·배열·다청크 포함, B-08), When 검사, Then 원본 본문을 보존하며 통과한다.
- **Reject** — Given §8.2 고정 코퍼스 S-01~S-08, When 검사, Then 8개 모두 BLOCK(정규식+문맥 엔트로피, LLM 판정 호출 없음). 인증 예외 외 헤더(S-07)·JSON unicode escape·청크 분할(S-08)도 검출.
- **Failure** — Given 코퍼스, When 측정, Then TP=8, FN=0, FP=0, TN=8 (B-01~B-08 ALLOW). 시험 문자열을 탐지기에 하드코딩하지 않는다.
- INVEST: 정규식·엔트로피·escape 복원·청크 병합 = 순수/직렬화 → **PBT 강제 대상**. 추적: FR-3.2, NFR-10, S-01~08/B-01~08.

## S-U3-3 탐지 시 요청 전체 전송 전 차단(403) `[MVP:P0-core]`
개발자(P-A)로서 시크릿 탐지 시 업스트림 도달 전에 차단되고 사유를 받고 싶다. (US-3, FR-3.3)
- **Normal** — Given 키 제거 후 재시도, When 전송, Then 새 요청으로 정상 처리된다.
- **Reject** — Given 시크릿 포함 요청, When 전송 전, Then 403에 `AEGIS_SECRET_BLOCKED`·event_id·rule_id·안전한 위치 식별자를 포함해 차단하고 업스트림에 본문·헤더가 전달되지 않는다. UI에는 위치·`[REDACTED]`·업스트림 미전송 표시.
- **Failure** — Given 차단, When 처리, Then 경고 후 통과로 바꾸지 않는다(C-SCOPE-1).
- 추적: FR-3.3, D-3, §6.

## S-U3-4 정상 인증·콘텐츠 무손상 전달 `[MVP:P0-core]`
개발자(P-A)로서 정상 요청의 인증·본문·응답이 변형 없이 전달되길 바란다. (FR-3.4)
- **Normal** — Given 정확한 제공자 host의 규정된 인증 헤더(B-07), When 전송, Then 전송용 자격증명으로 처리하고 로깅하지 않으며 본문 bytes·응답·SSE 의미를 변경하지 않는다.
- **Reject** — Given 동일 키가 본문이나 다른 헤더에 존재, When 검사, Then 차단한다.
- **Failure** — Given 정상 SSE 스트림, When 전달, Then 의미 손상 없이 전달한다.
- 추적: FR-3.4, B-07, T-PROXY.

## S-U3-5 검사 불가 요청 명시적 거부 `[MVP:P0-core]`
개발자(P-A)로서 검사할 수 없는 요청이 조용히 통과하지 않길 바란다. (FR-3.5, NFR-13)
- **Normal** — Given 상한 내 chunked 요청, When 수신, Then 끝까지 수신·검사 후 전달한다.
- **Reject** — Given 크기 초과/미지원 본문·압축/잘못된 JSON/내부 검사·감사 장애, When 처리, Then 각각 413/415/400/503으로 거부한다(이미지 등은 415).
- **Failure** — Given 초과·시간 초과, When 처리, Then 경고 후 통과로 바꾸지 않는다.
- 추적: FR-3.5, T-BODY, NFR-13.

## S-U3-6 TLS·지원 제공자 한정 `[MVP:P0-core]`
개발자(P-A)로서 프록시가 지원 제공자로만 복호화·전송하길 바란다. (FR-3.6, NFR-5)
- **Normal** — Given 정확한 host·port·path·method, When 요청, Then 수용한다. 로컬 CA 신뢰는 보호 클라이언트에만 설정.
- **Reject** — Given 다른 목적지의 CONNECT·요청, When 처리, Then 거부한다.
- **Failure** — Given 업스트림 인증서, When 연결, Then 검증을 끄지 않는다.
- 추적: FR-3.6, T-TRANSPORT, NFR-5.

---

# Epic US-2 → Unit U-2 AgentCage  (D-2 정책·샌드박스)
*개발자(P-A)로서 검증된 제한 안에서 에이전트에 작업을 맡기고 싶다.* 통합 순서 2번째 방어(U-2).

## S-U2-1 검증 후 실제 OpenShell 실행 `[MVP:P0-core]`
개발자(P-A)로서 서명 검증을 통과한 정책으로만 실제 샌드박스가 실행되길 바란다. (US-2, FR-2.1)
- **Normal** — Given 유효 정책, When `aegis-cage run --policy <path> -- <command>`, Then 샌드박스 안에서 결정적 작업 명령을 실행한다.
- **Reject** — Given 미서명·변조·미신뢰 키·미지원 버전·검증기 예외, When run, Then 명령 시작 전 거부하며 OpenShell 생성 호출·자식 명령 실행이 각각 0회.
- **Failure** — Given V-1(OpenShell/Landlock/컨테이너) 미검증 환경, When 실행, Then 관련 P0 완료로 표시하지 않는다(WSL2 smoke test 게이팅).
- 추적: FR-2.1, T-SIGN, D-2. **선행: V-1**.

## S-U2-2 검증본=적용본 (TOCTOU) `[MVP:P0-core]`
개발자(P-A)로서 검증한 정책과 실제 적용 정책이 동일하길 바란다. (FR-2.2)
- **Normal** — Given 검증된 스냅샷, When 적용, Then 그 스냅샷이 적용되고 policy_digest를 결과·감사에 남긴다.
- **Reject** — Given 검증 후 원본 파일 변경, When 실행, Then 변경 bytes가 적용되지 않거나 실행이 거부된다.
- **Failure** — Given 변경된 원본, When 검증 없이 사용 시도, Then 사용되지 않는다.
- INVEST: 스냅샷 무결성 → PBT 유용. 추적: FR-2.2, T-TOCTOU.

## S-U2-3 최소 워크스페이스·통신 권한 `[MVP:P0-core]`
개발자(P-A)로서 에이전트가 허용된 자원만 접근하길 바란다. (FR-2.3)
- **Normal** — Given 준비한 프로젝트 복사본, When 실행, Then 파일 읽기·수정 성공하며 런타임 필요한 샌드박스 내부 파일 접근은 허용한다.
- **Reject** — Given 호스트 홈 시험 표식·SSH 설정·Docker 소켓·비허용 외부 통신, When 접근, Then 실패한다(‘모든 FS 금지’로 과잉 해석하지 않음).
- **Failure** — Given 경계 미확인, When 실행, Then 보호 활성으로 표시하지 않는다.
- 추적: FR-2.3, T-CAGE, D-2.

## S-U2-4 실행 시작·거부·종료 기록 `[MVP:P0-core]`
개발자(P-A)로서 실행 판정과 결과가 안전하게 기록되길 바란다. (FR-2.4)
- **Normal** — Given 각 실행, When 완료, Then command_label·policy digest·pubkey_id·판정·종료 상태가 연결된다.
- **Reject** — Given 명령 인자·환경변수 전체, When 기록, Then 저장하지 않는다.
- **Failure** — Given 검증 실패, When 종료, Then CLI 비정상 종료와 이해 가능한 사유로 전달한다.
- 추적: FR-2.4, T-CAGE, T-PRIVACY.

## S-U2-5 실행 중 정책 고정·재검증 `[MVP:P0-core]`
관리자(P-B)로서 실행 중 정책이 몰래 바뀌지 않길 바란다. (FR-2.5)
- **Normal** — Given 실행 중, When 원본 정책 편집, Then 실행 중 권한이 자동으로 바뀌지 않는다.
- **Reject** — Given 정책 적용 미확인, When 상태, Then 보호 활성이 되지 않는다.
- **Failure** — Given 운영자 재적용, When 처리, Then 기존 실행 종료 후 서명·스키마·신뢰키를 재검증·재생성한다.
- 추적: FR-2.5, T-CAGE.

---

# Epic US-1 → Unit U-1 WebIsolate  (D-1 웹 격리)
*개발자(P-A)로서 의심 링크를 로컬 실행 없이 읽고 싶다.* 통합 순서 마지막 방어(U-1).

## S-U1-1 탐색 판정: 직접/격리/차단 `[MVP:P0-core]`
개발자(P-A)로서 미분류·위험 웹이 로컬에서 먼저 실행되지 않길 바란다. (US-1, FR-1.1)
- **Normal** — Given 명시한 신뢰 origin, When 탐색, Then 직접 열린다.
- **Reject** — Given 지정 위험 도메인·미분류 외부 origin, When 최초 요청·주소창 입력·링크 클릭·새 탭·서버 리다이렉트, Then 원격 격리되고 대상 페이지가 로컬에 먼저 실행되지 않는다.
- **Failure** — Given 정책 부재, When 탐색, Then 직접 접속하지 않는다.
- 추적: FR-1.1, T-WEB, D-1.

## S-U1-2 픽셀 중계·로컬 HTML 부재 `[MVP:P0-core]` / RBI 화질·지연 `[Deferred:perf-NFR]`
개발자(P-A)로서 원격 페이지의 픽셀만 받고 코드는 로컬에 오지 않길 바란다. (FR-1.2)
- **Normal** — Given 시험 페이지, When 격리 표시, Then 버튼·스크롤이 원격에서 동작하고 viewer에는 이미지 프레임·허용된 구조화 제어 메시지만 도착한다.
- **Reject** — Given 원격 HTML, When 표시, Then iframe·innerHTML로 삽입하지 않는다.
- **Failure** — Given 로컬 네트워크 기록, When 검사, Then 대상 페이지 HTML/JS/DOM 다운로드가 0건.
- NFR-1(입력→화면 P95≤300ms, 첫 프레임≤5s)의 **수치 목표 달성·최적화는 `[Deferred:perf-NFR]`**(T-PERF, MVP는 동작만 확인). 추적: FR-1.2, D-1.

## S-U1-3 위험 액션 차단·한글 사유 `[MVP:P0-core]`
개발자(P-A)로서 격리 페이지의 위험 액션이 실제로 차단되고 이유를 알고 싶다. (FR-1.3, §3)
- **Normal** — Given `mailto:` 클릭, When 처리, Then ‘외부 메일 앱을 열지 않았습니다’ 경고 + 계속 읽기·세션 닫기 제공(외부 앱 미실행).
- **Reject** — Given 다운로드·업로드·클립보드 전달·`type=password` 입력, When 시도, Then 원격 집행 지점에서 차단한다.
- **Failure** — Given 페이지가 직접 다운로드 시작, When 처리, Then 로컬 파일이 생성되지 않는다.
- 추적: FR-1.3, D-1, §3(P0 차단 유지, 경고/통과로 축소 금지).

## S-U1-4 세션 인증·만료·데이터 폐기 `[MVP:P0-core]`
개발자(P-A)로서 격리 세션이 안전하게 인증·종료되길 바란다. (FR-1.4)
- **Normal** — Given 유효 토큰, When 세션, Then 정상 동작한다.
- **Reject** — Given 잘못된 토큰·다른 세션 토큰, When 접근, Then 거부한다.
- **Failure** — Given 탭 닫기·명시적 종료·유휴 만료·연결 끊김, When 처리, Then 원격 컨텍스트·임시 데이터를 삭제하고 끊긴 세션은 닫아 새 인증으로 다시 연다.
- 추적: FR-1.4, T-WEB, NFR-13(TTL).

## S-U1-5 격리 실패 시 안전한 재시도(우회 없음) `[MVP:P0-core]`
개발자(P-A)로서 격리가 실패해도 로컬 직접 접속으로 떨어지지 않길 바란다. (FR-1.5, NFR-8)
- **Normal** — Given 서버 복구, When ‘격리 다시 열기’, Then 새 세션을 만든다.
- **Reject** — Given ‘로컬에서 계속’ 우회, When UI, Then 그런 버튼이 없다.
- **Failure** — Given RBI 중단·인증 만료·잘못된 URL·차단 목적지, When 처리, Then viewer가 입력을 중단하고 사유를 표시한다.
- 추적: FR-1.5, D-1, NFR-8.

## S-U1-6 원격 브라우저 SSRF 제한 `[MVP:P0-core]`
개발자(P-A)로서 원격 브라우저가 내부망·메타데이터로 접근하지 않길 바란다. (FR-1.6)
- **Normal** — Given test 프로필의 정확한 내부 fixture 목적지, When 접근, Then 지정 예외만 허용된다.
- **Reject** — Given loopback·사설/link-local IPv4/IPv6·클라우드 메타데이터·비HTTP(S)·리다이렉트·하위 요청·DNS 변경, When 접근, Then 실제 연결 경계에서 모두 거부한다.
- **Failure** — Given 시험 예외, When 적용, Then 다른 목적지로 확대되지 않는다.
- INVEST: URL 정규화·SSRF 판정 = 순수 로직 → PBT 유용. 추적: FR-1.6, T-SSRF.

---

# Epic US-6 → 공통 실행 경험 (FR-0.x)
*검증 동료(P-C)로서 README만으로 설치·검증을 반복하고 싶다.* 세 방어를 묶는 실행 표면.

## S-C-1 단일 실행 진입점 `[MVP:P0-core]`
검증자(P-C)로서 `doctor/up/down/demo/test` 하나로 환경을 다루고 싶다. (FR-0.1)
- **Normal** — Given 의존성 준비, When `up` 1회, Then 제어 UI·프록시·감사 저장소·RBI 준비 상태가 표시된다(OpenShell 실행은 `run` 요청 때).
- **Reject** — Given 미준비 항목, When `up`, Then 이름·복구 절차를 출력하고 성공 종료코드를 반환하지 않는다.
- **Failure** — Given 반복 기동·서비스 복구, When 처리, Then 성공/실패 종료코드가 정확하고 복구 시 재검증한다.
- 추적: FR-0.1, T-BOOT, NFR-7, NFR-11.

## S-C-2 컴포넌트 상태 구분 `[MVP:P0-core]`
검증자(P-C)로서 각 컴포넌트가 준비 중·보호 활성·차단·사용 안 함으로 구분되길 바란다. (FR-0.2)
- **Normal** — Given 정상, When 상태 표시, Then 4개 상태로 구분한다.
- **Reject** — Given 보호되지 않는 요청·비활성 Unit, When 표시, Then ‘보호됨’으로 표시하지 않는다.
- **Failure** — Given 프록시·RBI·감사 저장소 하나 중지, When 3초 경과, Then 해당 카드가 활성 상태를 잃는다.
- 추적: FR-0.2, T-UX.

## S-C-3 workflow_id 전파 `[MVP:P0-core]`
검증자(P-C)로서 한 작업의 세 방어 결과를 같은 workflow_id로 조회하고 싶다. (US-4, FR-0.3)
- **Normal** — Given 실행, When D-1~D-3를 같은 작업으로 실행, Then 동일 workflow_id·서로 다른 event_id로 조회된다.
- **Reject** — Given 임의 다른 세션 ID, When 접근, Then 이벤트·격리 세션에 접근할 수 없다.
- **Failure** — Given 재실행, When 처리, Then 이전 실행의 이벤트·카운터와 섞이지 않는다.
- 추적: FR-0.3, T-FLOW.

## S-C-4 README 기반 재현 `[MVP:P0-core]` / 사용성 세부 측정 `[Deferred:usability-NFR]`
검증자(P-C)로서 숨은 수작업 없이 3 시나리오·장애·정리를 재현하고 싶다. (US-6, NFR-7/11/12)
- **Normal** — Given README, When 사전 준비→기동→D-1~D-3→장애 복구→정리 수행, Then 결과 파일을 workflow_id로 찾는다. README 외 미기록 수작업 0개.
- **Reject** — Given 검증하지 않은 OpenShell 버전, When 기동, Then 거부한다(NFR-11).
- **Failure** — Given 실행 환경·라이브러리·이미지 digest, When 기록, Then 버전·digest를 남긴다.
- NFR-12(다른 사용자 1명 재현·인지·복구 성공) 측정은 **`[Deferred:usability-NFR]`**(테스트 가능자 없으면 미수행으로 남김). 추적: FR-0.1, US-6, T-BOOT, NFR-7/11/12.

---

# 유예 스토리 스텁 (P1 / P2) `[Deferred:P1]` `[Deferred:P2]`
MVP(P0) 검증 후 상세화. 지금은 범위 추적을 위한 placeholder만 둔다(§3, §11). acceptance criteria는 MVP 완료 후 작성.

| ID | 스토리(요약) | 페르소나 | 우선순위 | 유예 사유 |
|---|---|---|---|---|
| S-P1-1 | SHA-256 기반 탐지 예외 목록 | P-B | P1 | MVP는 고정 코퍼스 정탐 우선 |
| S-P1-2 | 서명된 정책의 동적 갱신 | P-B | P1 | MVP는 재시작 기반 적용(FR-2.5) 우선 |
| S-P1-3 | gzip 텍스트 요청 지원 | P-A | P1 | MVP는 비압축 텍스트 JSON 우선(FR-3.5는 압축 415 거부) |
| S-P1-4 | RBI 품질·지연 최적화(1080p/15fps, <150ms) | P-A | P1 | MVP는 동작·안전 우선, 수치 목표 유예(NFR-1) |
| S-P1-5 | 집계 지표 대시보드 | P-A | P1 | MVP는 최소 상태·최근 이벤트 우선 |
| S-P2-1 | 요청 자동 redact | P-A | P2 | 후속 확장 |
| S-P2-2 | 정책 편집 GUI | P-B | P2 | 후속 확장 |
| S-P2-3 | 감사 로그 해시체인·외부 서명 보관 | P-B | P2 | 후속 확장 |
| S-P2-4 | WebRTC / 다중 세션·브라우저 | P-A | P2 | 단일 세션 P0 범위(§2.2) |
| S-P2-5 | ML-DSA-87 / 자동 키 회전·HSM·KMS | P-B | P2 | MVP는 ML-DSA-65·수동 교체 |
| S-P2-6 | 외부 위협 피드 | P-B | P2 | 후속 확장 |

---

# INVEST 셀프체크 요약
- **Independent**: 스토리를 Unit 경계로 분리, U-4/U-5는 방어 Unit 구현 미참조(FR-4/5 계약만).
- **Negotiable**: acceptance criteria는 '무엇'을 고정하고 '어떻게'(구현)는 Construction 단계로 남김.
- **Valuable**: 각 스토리가 P-A/P-B/P-C 중 하나 이상에 직접 가치.
- **Estimable**: FR 단위로 분해해 크기 추정 가능.
- **Small**: 각 하위 스토리 = 1개 FR 그룹, 독립 테스트 단위.
- **Testable**: 모든 스토리에 D-1~D-3·S/B 코퍼스·T-* 검증 ID 연결, Given/When/Then로 표현.

# 페르소나 ↔ 스토리 매핑 (상세)
| 페르소나 | 주(★) 스토리 | 부(○) 스토리 |
|---|---|---|
| P-A 개발자 | S-U5-3, S-U3-1~6, S-U2-1/3/4, S-U1-1~6, S-C-3 | S-U5-1/2/4, S-C-1/2/4 |
| P-B 정책 관리자 | S-U4-1~4, S-U2-5 | S-U2-1(정책 발급), S-U3-2(탐지 정책), S-C-1 |
| P-C 검증 동료 | S-C-1/2/4 | 전 스토리 재현 경로 |
