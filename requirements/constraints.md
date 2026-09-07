# AEGIS 개발·보안 제약조건

버전: 4.0 | 작성일: 2026-09-07 | 상태: 개발 착수용 기준안, 사람의 단계 승인 전

같은 디렉토리의 [requirements.md](requirements.md)를 구현할 때 적용한다. 제품 동작·수용 기준은 requirements.md, 기술 경계·프로토콜·기본값·검증·AI-DLC 절차는 이 문서가 정한다. 문서에 기록한 새 기본값을 과거 사용자의 확정 답변으로 해석하지 않는다.

## 1. 적용 원칙과 실행 범위

### C-SCOPE-1 — 범위와 변경 통제

- 최초 제공 범위는 requirements.md의 P0 전체다. P1/P2는 P0의 보안 집행·정상 경로·검증을 완료한 뒤 추가한다.
- 우선순위는 **보호 경계 유지 → 데이터 비노출·정책 무결성 → 실제 기능 완성 → 재현성·사용성 → 성능 최적화 → 확장 기능**이다. 성능을 맞추려고 검사 전 전송, TLS 검증 해제, 검증 실패 허용을 도입하지 않는다.
- 변경 시 영향받는 FR/NFR, 이유, 새 동작, 검증 방법을 함께 갱신한다. 같은 요구를 여러 파일에서 서로 다른 기본값으로 정의하지 않는다.
- 이 작업의 산출물은 `new/requirements.md`, `new/constraints.md` 두 기준 문서다. 앞으로 수행할 설계·테스트·승인·구현을 이번 문서 작성으로 완료한 것으로 기록하지 않는다.

### C-SCOPE-2 — 최소 배포 형태

단일 저장소, 단일 사용자, 단일 Linux 실행 호스트를 기준으로 한다. Chrome 클라이언트는 해당 호스트 또는 같은 개발 장비의 호스트 OS에서 실행한다. 기준 서버는 Ubuntu 24.04 Linux VM이며 WSL2는 실제 OpenShell 격리 시험을 통과한 경우에만 지원 조합으로 기록한다. GPU, Kubernetes 클러스터, 외부 DB, 클라우드 계정, 실제 LLM 과금은 기본 검증에 요구하지 않는다.

권장 실행 환경은 4 vCPU·8GiB RAM 이상이다. 이 값은 보장된 최소 사양이 아니라 검증 시작 기준이며 실제 사용 환경과 사용량을 기록한다. Chrome 세션 1개, OpenShell 실행 1개, 프록시 동시 요청 1개를 검증 범위로 고정한다. 초과 작업은 유한 큐나 429로 거부하며 무제한 대기열을 만들지 않는다.

## 2. 스택, 의존성, 소스 구성

### C-DEP-1 — 스택과 버전 고정

| 영역 | 기준 선택 | 강제 조건 |
|---|---|---|
| 클라이언트 | Chrome Manifest V3, TypeScript | 전용 보호 프로필. DNR로 탐색 전 집행, viewer·팝업은 패키지에 포함한 정적 자원. |
| UI·제어 서버 | Python, FastAPI, 정적 HTML/CSS/TypeScript | 최소 상태 화면만 제공. 별도 프런트엔드 프레임워크·DB·메시지 브로커를 필수 의존성으로 추가하지 않음. |
| RBI | Playwright Python + 해당 버전에 묶인 Chromium | 격리 컨테이너의 실제 브라우저. JPEG 프레임을 WebSocket으로 전달하는 방식을 P0로 고정. WebRTC는 P2. |
| 실행 게이트 | Python 래퍼 + NVIDIA OpenShell CLI | 실제 설치 버전의 계약을 확인. OpenShell 자체를 재구현하지 않음. |
| 전송 보호 | mitmproxy/mitmdump Python addon, 명시적 HTTPS forward proxy | 검사 요청의 body streaming 금지. 자체 범용 TLS 프록시 구현을 새로 시작하지 않음. |
| 정책 서명 | liboqs + 공식 Python 바인딩 liboqs-python | ML-DSA-65 활성화 여부와 정상·변조 검증을 확인. 이름이 비슷한 다른 `oqs` 패키지를 설치하지 않음. |
| 감사 | 단일 writer, UTF-8 JSONL, 로컬 ext4 등 Linux 파일시스템 | 외부 저장소·검색 엔진 없이 조회·내보내기 지원. |
| 검증 | pytest, 필요한 Chrome/Playwright 통합 시험 | 기존 도구의 실동작 계약과 경계 검증에 집중. 전체 커버리지 비율을 임의의 합격 기준으로 추가하지 않음. |

직접 작성하는 애플리케이션 코드는 TypeScript와 Python으로 제한한다. HTML/CSS, YAML/JSON, Dockerfile, 실행용 shell은 설정·진입점 용도로 허용하고 OpenShell/liboqs의 내부 구현 언어는 이 제한의 대상이 아니다.

패키지 lockfile과 이미지 digest로 실행 조합을 재현한다. 배포·기동 명령에 `latest`나 범위 버전만 남기지 않는다. 정확한 패치 버전·digest는 V-1~V-4 smoke test를 통과한 값으로 잠근다. 이 문서만으로 아직 시험하지 않은 버전 번호를 ‘검증 완료’라고 고정하지 않는다. `doctor`는 실제 버전이 잠금 목록과 다르면 해당 Unit을 시작하지 않는다.

### C-DEP-2 — 구조와 책임

애플리케이션 코드는 저장소 루트 아래 `apps/extension/`, `src/aegis/{web,cage,guard,policy,audit,contracts}/`, `tests/`, `scripts/`, `config/`로 구성한다. AI-DLC 문서는 `aidlc-docs/`에 둔다. U-5의 정식 이름은 AuditTrail이며 기존 AuditFabric은 같은 책임의 옛 이름이다.

`contracts`는 데이터 타입·reason code를 정의하며 런타임 구현을 import하지 않는다. U-4/U-5가 U-1/U-2/U-3을 import하지 않게 한다. 공통 정책·감사·탐지 룰을 방어 Unit마다 복제하지 않는다. U-5가 U-3 탐지기를 호출해서 원문을 뒤늦게 마스킹하는 구조 대신 이벤트 생성 단계부터 원문 없는 허용 필드만 받는다.

### C-DEP-3 — 통합 가능성 확인

Construction의 본 구현 전에 다음 결과를 남긴다. 문서 조사와 실행 결과를 구분한다.

1. OpenShell 실제 버전·도움말·지원 kernel 기능 확인, 최소 sandbox 생성, 허용/금지 파일 및 네트워크 접근 시험.
2. ML-DSA-65 키 생성·서명·검증 성공, bytes 변경 검증 실패. 빌드가 어려우면 검증된 이미지를 만들거나 사용하되 출처·digest·라이선스를 기록한다.
3. 보호 네트워크에서 프록시 통과 성공, 프록시 종료·환경변수 제거 후 직접 외부 연결 실패, CA 신뢰 검증.
4. Chrome의 탐색 전 차단·격리 전환과 원격 Chromium의 픽셀 표시 성공.

이 중 실패한 외부 의존성을 가짜 보안 기능으로 대체하지 않는다. 지원 VM·잠근 빌드로 환경을 수정하고 재검증한다. 해결하지 못하면 영향받는 P0를 미완료로 표시한다. 실제 OpenShell 없이 wrapper mock만 통과시킨 결과로 D-2를 완료하지 않는다.

## 3. 공통 정책과 인터페이스 계약

### C-CONTRACT-1 — 정책 두 종류의 분리

| 파일·객체 | 역할·필수 필드 | 검증·갱신 |
|---|---|---|
| `aegis-policy.json` | `schema_version`=1, `policy_id`, `policy_version`(양의 정수), `web`, `guard`, `audit`. 제품 공통 동작·룰 설정. | 신뢰 운영자가 소유한 로컬 설정. 전체 스키마 검증 후 적용, P0는 전체 재시작. 이 파일이 PQC 서명된 것으로 표시하지 않음. |
| `policy.yaml` | OpenShell 고유 스키마. `version`=1과 해당 버전의 filesystem/network/process 등 필드. | 원본 bytes를 ML-DSA로 검증한 뒤 OpenShell 스키마·의도한 최소권한을 확인. AEGIS 전용 필드를 주입하지 않음. |
| `policy.yaml.sig.json` | `schema_version`=1, `alg`=`ML-DSA-65`, `pubkey_id`, `signature_b64`. | 정확한 알고리즘·base64·길이·신뢰키를 확인. 서명 옆의 공개키를 자동 신뢰하지 않음. |
| `trusted-keys.json` | `schema_version`=1, 허용된 pubkey_id와 공개키 파일의 명시적 매핑. | 에이전트·원격 브라우저에서 읽기/쓰기 접근 불가. 운영자만 교체. |

정책 입력은 중복 키, 알 수 없는 필드, 미지원 버전, 경로 이탈, 유효하지 않은 enum·범위를 거부한다. 공통 JSON은 객체 타입별 허용 필드를 닫힌 스키마로 정의한다. OpenShell YAML은 안전한 loader를 사용하고 custom tag·외부 참조를 허용하지 않는다. OpenShell에 존재하지 않는 임의의 ‘명령 allowlist’ 필드를 만들지 않는다.

공통 정책의 digest는 정렬된 키·고정 JSON 직렬화 bytes의 SHA-256이다. 에이전트 실행 정책의 digest는 `policy.yaml` 원본 bytes의 SHA-256이다. 이벤트에 `policy_kind`를 넣어 둘을 구분한다. 실행 이벤트에는 필요하면 별도 `workspace_policy_digest`로 공통 설정 digest를 함께 남긴다. `policy_version`은 관리 버전이고 `schema_version`은 데이터 계약 버전이다.

| 설정 항목 | 기본값·범위 |
|---|---|
| 웹 판정 | 명시적 차단 origin → 지정 격리 host → 신뢰 origin → 나머지 격리. 정확한 origin/host 비교, 서브도메인 암묵 허용 없음. |
| 신뢰 origin | 설치 시 생성한 AEGIS UI origin 및 명시적으로 등록한 신뢰 사이트만. 빈 신뢰 사이트 목록이 기본. |
| 웹 위험 액션 | 메일 앱 실행·파일 입출력·클립보드 전달·`type=password` 필드 입력 모두 차단. |
| 제공자 | `api.anthropic.com:443`, `api.openai.com:443`만. P0에서 임의 host 추가 UI 없음. |
| 탐지 판정 | 일치 1개 이상이면 BLOCK. warn-only·자동 redact 없음. |
| 엔트로피 | Shannon entropy 4.0 bits/char 이상, 정해진 길이·secret 문맥 조건을 동시에 만족해야 적용. |
| 정책 갱신 | P0는 검증 후 재시작. 실패한 설정으로 부분 시작하지 않음. |

### C-CONTRACT-2 — 공통 판정·식별자

공통 판정은 `ALLOW`, `ISOLATE`, `BLOCK`, `ERROR`이다. `ERROR`는 보호 동작 허용을 의미하지 않는다. HTTP·CLI 결과와 UI 상태는 같은 reason_code에 매핑한다. 필수 코드에는 `WEB_ISOLATED`, `WEB_ACTION_BLOCKED`, `WEB_TARGET_DENIED`, `RBI_UNAVAILABLE`, `SESSION_EXPIRED`, `POLICY_SIGNATURE_INVALID`, `POLICY_SCHEMA_INVALID`, `POLICY_KEY_UNTRUSTED`, `POLICY_VERSION_UNSUPPORTED`, `SANDBOX_UNAVAILABLE`, `AEGIS_SECRET_BLOCKED`, `REQUEST_TOO_LARGE`, `REQUEST_UNSUPPORTED`, `REQUEST_INVALID`, `REQUEST_TIMEOUT`, `UPSTREAM_UNAVAILABLE`, `AUDIT_UNAVAILABLE`을 포함한다.

`workflow_id`, `session_id`, `request_id`, `event_id`는 서버에서 생성한 UUID v4 또는 동등한 충돌 저항 식별자다. 식별자는 인증 수단이 아니다. UI·CLI가 식별자를 전달하더라도 인증된 작업과 일치하는지 확인한다. 웹의 URL·페이지 제목·요청의 JSON 키에 시크릿이 있을 수 있으므로 원시 값을 식별자로 재사용하지 않는다.

### C-CONTRACT-3 — 최소 API와 CLI

| 인터페이스 | 계약 |
|---|---|
| `GET /api/health` | 인증된 상태 조회. 공통 정책 검증 결과, Unit별 상태·의존성 오류를 반환. 민감한 경로·환경값 제외. |
| `POST /api/web/sessions` | `{url, workflow_id}` 입력. URL은 메모리에서만 사용. 성공 시 session_id·만료시각을 반환하고 인증된 채널로 viewer 연결. |
| `DELETE /api/web/sessions/{id}` | 소유 세션 종료. 이미 종료돼도 안전하고 반복 가능. |
| `WS /api/web/sessions/{id}/stream` | 인증·Origin·세션 소유 검증 후 픽셀 binary와 제한된 input/action/status JSON만 교환. |
| `GET /api/events?workflow_id=...&unit=...&verdict=...` | 소유 작업의 안전한 이벤트만 반환. 기본 50개, 최대 200개, cursor 기반 페이지. |
| `aegis-policy keygen / sign / verify` | 키 생성은 명시적 관리 명령. sign은 오프라인 동작, verify는 읽기 전용. 실패는 0이 아닌 종료코드. |
| `aegis-cage run --policy <path> -- <command>` | 내부적으로 서명·스키마·감사·런타임 준비 확인 후 실행. 성공은 자식 종료코드, 정책/의존성 실패는 문서화한 0이 아닌 코드. |
| `scripts/aegis demo web / cage / guard / all` | 지정 시나리오와 안전한 결과 파일을 생성. `all`은 공통 workflow_id를 생성. |

임의 셸 명령을 실행하는 HTTP API는 제공하지 않는다. 명령은 로컬 CLI에서 argv 배열로 OpenShell에 전달하며 문자열 셸 결합을 하지 않는다. 오류 응답의 고정 구조는 `error.code`, `error.message`, `error.event_id`, `error.findings`이며 findings는 최대 5개, 각 항목에 rule_id·안전한 위치·`[REDACTED]`만 포함한다. JSON 키 이름 대신 허용된 키 이름 또는 객체 내 순번·배열 인덱스를 써서 위치 자체의 누출을 막는다.

## 4. WebIsolate 집행 제약

### C-WEB-1 — Chrome 경계

MV3 `declarativeNetRequest` 규칙으로 대상 네트워크 탐색 전에 차단·격리 viewer로 전환한다. 페이지가 로컬에서 로드된 뒤 content script로 가리는 구현은 금지한다. URL 분류는 URL parser를 사용하고 소문자 host·IDNA·기본 port를 정규화한다. `example.com.evil.test`, userinfo, 인코딩된 host, 비HTTP(S) scheme을 단순 문자열 접두사로 신뢰하지 않는다.

규칙은 보호 프로필에 한정한다. service worker가 종료·재시작해도 마지막으로 검증된 차단 규칙이 유지되어야 한다. 정책·규칙 갱신은 원자적으로 수행하고, 실패하면 기존 보호 규칙을 유지하거나 탐색을 차단한다. keepalive 메시지만으로 service worker가 영구 실행된다고 가정하지 않는다. 저장소에는 정책 revision·비민감 상태만 보관하고 대상 URL·세션 토큰은 영속 저장하지 않는다.

보호 전용 프로필에는 기존 외부 사이트 service worker·캐시가 없어야 한다. 외부 페이지의 로컬 하위 frame 삽입 경로를 차단하고, 로컬 신뢰 사이트의 script/API 트래픽에 대한 범용 DLP는 주장하지 않는다. 직접 허용 사이트는 최소화하며 사용자에게 그 범위를 표시한다. 확장 제거·다른 프로필로 이탈한 경우 제품 보호 밖임을 명시한다.

근거: 탐색·요청 차단과 리다이렉트는 [Chrome DNR 공식 API](https://developer.chrome.com/docs/extensions/reference/api/declarativeNetRequest)의 지원 범위에서 구현하고 테스트한다. 실제 사용한 API·Chrome 버전과 규칙 우선순위를 고정한다.

### C-WEB-2 — 원격 렌더링과 통로 제한

원격 브라우저는 전용 컨테이너 안의 별도 Chromium 프로세스·임시 프로필로 실행한다. 호스트 홈·Docker 소켓·서명키·CA키·다른 사용자 데이터는 마운트하지 않는다. 비특권 사용자로 실행하고 Chromium sandbox를 활성화한다. `--no-sandbox`, privileged 컨테이너로 동작시키며 보호를 주장하지 않는다. 컨테이너는 호스트 VM의 kernel을 공유하므로 별도 하이퍼바이저 격리라고 표현하지 않는다.

기본 프레임은 JPEG, 1280×720, 목표 10fps, quality 60이다. 프레임 메시지 상한은 1MiB, 전송 대기 프레임은 최신 1개다. 느린 클라이언트는 오래된 프레임을 버리고 무한 버퍼링하지 않는다. 제어 메시지는 4KiB 이하이며 좌표·키 enum·event sequence를 검증한다. 최대 입력률은 세션당 초당 60건이고 초과는 제한한다.

로컬 viewer는 신뢰한 AEGIS 자원만 실행한다. 원격 HTML·DOM·JS·파일 bytes·원시 브라우저 프로토콜을 전달하지 않는다. 경고 문자열은 서버의 고정 메시지 템플릿을 사용한다. `mailto:`, 외부 앱 scheme, 다운로드·업로드·clipboard는 브라우저 이벤트와 컨테이너 통로에서 차단한다. `type=password` 필드의 키 입력은 원격 입력 중계 전에 거부한다. 일반 텍스트 필드로 위장한 비밀번호 수집이나 자유 입력까지 비밀이 없다고 보장하지 않는다.

### C-WEB-3 — 목적지 검증과 SSRF

허용 scheme은 http/https, 일반 목적지 port는 80/443이다. URL 길이 상한 2,048자, userinfo 포함 URL은 거부한다. loopback, 사설 IPv4/IPv6, link-local, multicast, unspecified 주소, IPv4-mapped IPv6의 금지 주소를 차단한다. 특히 메타데이터 주소와 AEGIS 관리·감사·프록시 목적지는 금지한다.

DNS 결과·리다이렉트·새 창·하위 요청에도 검사하며 DNS 결과가 바뀌어 내부 IP로 연결되는 것을 네트워크 egress 규칙으로 막는다. URL 문자열 검사만으로 완료하지 않는다. 시험 fixture는 격리된 test 네트워크의 정확한 host·IP·port만 예외로 지정하고 운영 설정에서는 이 예외를 로드하지 않는다. 모든 사설망을 허용하는 시험 예외는 금지한다.

### C-WEB-4 — 세션 수명

세션 인증 토큰은 CSPRNG 256bit 이상, 유휴 TTL 10분, 최대 수명 30분이다. 브라우저 URL query·로그에 넣지 않는다. 연결 초기 인증 메시지 또는 헤더 등 로그에 남지 않는 방법을 사용한다. handshake Origin·세션 소유자를 확인하고 인증 전 프레임과 입력을 교환하지 않는다.

명시적 종료·탭 종료는 즉시 폐기 요청을 보낸다. 종료 이벤트가 전달되지 않으면 연결 끊김·heartbeat 부재 30초 안에 폐기한다. 만료·장애 뒤 재연결은 새 세션으로 처리하고 이전 토큰을 재사용하지 않는다. 원격 쿠키·다운로드 임시파일·브라우저 프로필은 세션 종료 시 삭제한다.

## 5. AgentCage·PQC 제약

### C-CAGE-1 — OpenShell 책임과 실제 계약

OpenShell은 runtime filesystem/network/process 정책을 집행하고 AEGIS는 정책의 출처·bytes와 실행 전 조건을 확인한다. OpenShell 전체 동작을 AEGIS의 자체 구현으로 표시하지 않는다. `sandbox create --policy ...`의 실제 옵션·정책 조회·종료 명령은 잠근 버전의 `--help`와 통합 시험으로 확정한다.

샌드박스에는 프로젝트 복사본 또는 명시적으로 전달한 최소 디렉토리만 제공한다. 호스트 전체 FS, 홈, SSH·클라우드 자격증명, 제어 API, Docker 소켓을 노출하지 않는다. 실행에 필요한 샌드박스 내부 runtime 파일은 read-only, 작업·임시 경로는 제한된 read-write로 허용한다. 비특권 사용자와 런타임 기본 syscall 제한을 사용한다. Landlock은 `hard_requirement`로 설정하고 kernel 기능 부재를 경고만 하고 통과시키지 않는다.

공식 스키마는 filesystem/process 등 정적 항목과 network 등 동적 항목을 구분한다. 정적 정책을 실행 중 변경할 수 있다고 가정하지 않는다. [OpenShell 정책 스키마](https://docs.nvidia.com/openshell/reference/policy-schema)와 [정책 적용 안내](https://docs.nvidia.com/openshell/sandboxes/policies)를 근거로 실제 사용 필드만 기록한다.

### C-CAGE-2 — 네트워크·실행 자원

샌드박스의 임의 외부 연결은 기본 거부한다. LLM 사용 프로필에서만 SecretGuard의 정확한 서비스 주소·port로 연결을 허용하고, 외부 LLM host로 직접 연결하는 경로는 열지 않는다. OpenShell의 다른 inference route·자동 provider route가 프록시를 우회하지 않는지 시험한다. 프록시가 다른 격리 네트워크에 있으면 loopback 대신 그 전용 주소를 사용하며 일반 호스트 서비스 접근을 허용하지 않는다.

자원 목표는 에이전트 2 CPU·2GiB RAM·PID 256, RBI 2 CPU·2GiB RAM이다. 검증한 컨테이너/compute driver의 실제 자원 제한 설정으로 적용하고 효과를 확인한다. OpenShell YAML에 지원하지 않는 자원 필드를 만들어 넣지 않는다. 기본 결정적 작업은 60초 안에 종료하며 무응답 실행을 종료할 수 있어야 한다. 임의 명령 문자열·환경변수는 감사에 저장하지 않는다.

### C-CAGE-3 — 적용 순서와 갱신

실행 순서는 `입력 파일 읽기 → 신뢰키·서명 확인 → 스키마·최소권한 검증 → 안전한 정책 스냅샷 작성 → 필수 감사 기록 → OpenShell 생성·적용 확인 → 사용자 명령 실행`이다. 정책 검증 실패 시 OpenShell 생성 호출 자체가 발생하지 않아야 한다. 생성은 됐으나 적용 상태 확인이 실패하면 명령을 시작하지 않고 생성된 자원을 정리한다.

검증할 원본을 한 번 읽은 동일 bytes로 서명 검증·digest 계산·스냅샷 생성을 수행한다. symlink·비정규 파일·허용 경로 밖 입력은 거부한다. 스냅샷은 실행별 신뢰 runtime 디렉토리에 두고 에이전트에 노출하지 않으며, OpenShell에는 그 경로만 전달한다. 원본 경로를 다시 열어 실행하는 TOCTOU를 금지한다. 호스트의 악성 관리자에 대한 파일 불변성까지 주장하지 않는다.

P0에서는 자동 파일 감시·hot-reload를 사용하지 않는다. 정책 변경은 기존 실행 종료 후 재검증·재생성한다. OpenShell 관리 CLI·TUI·직접 API는 신뢰 운영자만 사용하며 에이전트에서 접근할 수 없어야 한다. P1의 동적 갱신은 AEGIS 경로로 제한하고 재검증→실제 적용 완료 확인→감사까지 제공한다. 확인되지 않은 ‘모든 OpenShell hot-reload 이벤트 훅’을 전제로 구현하지 않는다.

### C-PQC-1 — 암호 계약

서명 알고리즘은 **ML-DSA-65** 하나로 고정한다. 이는 NIST 보안 category 3이며 기존 문서의 ‘128b급’ 설명은 사용하지 않는다. 명세는 [NIST FIPS 204](https://csrc.nist.gov/pubs/fips/204/final), 라이브러리 지원·파라미터는 [Open Quantum Safe ML-DSA](https://openquantumsafe.org/liboqs/algorithms/sig/ml-dsa.html)를 확인한다. ‘FIPS 204 알고리즘 사용’과 ‘FIPS 검증 암호 모듈’은 다르다.

서명 메시지는 `ASCII("AEGIS-OPENSHELL-POLICY-v1") + 0x00 + policy.yaml 원본 bytes`이다. UTF-8 정책 입력 크기 상한은 64KiB이며 BOM·개행을 서명 전에 자동 변환하지 않는다. 키·서명 sidecar를 읽어 알고리즘·타입·길이를 검증하고, `alg`가 다르면 협상·폴백 없이 거부한다. 직접 작성한 암호 구현, HMAC 대체, mock 검증 성공은 금지한다. SHA-256은 정책 식별·증거 digest 용도이며 ML-DSA 서명 자체를 대체하지 않는다.

### C-PQC-2 — 키 보관과 신뢰

- 서명 도구는 외부 네트워크 연결 없이 실행한다. 개인키는 runtime·컨테이너·저장소·이미지·브라우저 확장에 포함하지 않는다. `up` 과정에서 자동 서명하거나 검증 실패 정책을 다시 서명하지 않는다.
- Linux 개인키 파일은 0600, 상위 디렉토리는 0700으로 제한한다. Windows 파일을 직접 쓰는 지원 구성이라면 이에 대응하는 사용자 전용 ACL을 확인한다. 관리자가 실행하는 별도 `keygen/sign` 명령으로만 생성·사용한다.
- `pubkey_id`는 공개키 bytes의 SHA-256 hex로 정의하고 신뢰 저장소에 명시적으로 등록한다. 배포 대상은 공개키뿐이다. 신뢰키 등록은 정책 파일이 아니라 설치·운영 설정에서 관리한다.
- 키 회전은 새 키 생성→공개키 신뢰 등록→정책 재서명→기존 관련 실행 종료→새 검증 실행→옛 키 제거 순으로 문서화한다. 손상 키는 먼저 실행 종료·신뢰 제거하고 재발급한다.

### C-PQC-3 — 보장 한계

미서명·변조·미신뢰 키 정책을 시작 전에 거부하는 것이 보장이다. 적법하게 서명한 위험 정책의 안전성, 과거 정상 서명 정책의 롤백 방지, 모든 프로세스의 정책 직접 변경 감시는 P0의 보장이 아니다. 이 한계는 제품 문서와 데모 설명에서 숨기지 않는다. 양자내성 설명은 정책 서명에만 적용하며 TLS까지 PQC로 바뀌었다고 설명하지 않는다.

## 6. SecretGuard 제약

### C-PROXY-1 — 명시적 프록시와 강제 경유

프록시는 등록한 제공자만 처리하는 전용 forward proxy다. 보호 클라이언트는 격리 네트워크에서 프록시 주소로만 통신할 수 있고, 프록시만 허용 제공자의 외부 TLS 목적지로 나갈 수 있다. 테스트 클라이언트의 격리 컨테이너 또는 AgentCage의 실제 집행 정책으로 이를 확인한다. host의 전체 네트워크 설정을 임의로 바꾸지 않는다.

`HTTPS_PROXY` 등 환경변수 설정만으로 fail-closed라고 주장하지 않는다. 프록시 종료, 환경변수 제거, 직접 IP 접속, 대체 host, 다른 port, 다른 inference route를 통한 우회를 시험한다. LLM 제공자 이외 목적지는 CONNECT 단계에서 거부한다. 일반 호스트 애플리케이션은 이 프록시를 사용하지 않으므로 평소 트래픽을 건드리지 않는다. 기존 문서의 ‘비대상 host는 터널 통과’ 정책을 보호 프록시의 기본값으로 사용하지 않는다.

### C-PROXY-2 — 제공자·본문 계약

| 제공자 | 허용 method·path | 인증값 취급 |
|---|---|---|
| Anthropic | `POST https://api.anthropic.com/v1/messages` | `x-api-key` 1개를 해당 host의 전송 인증값으로 취급. `anthropic-version` 등 정상 프로토콜 헤더는 보존. |
| OpenAI | `POST https://api.openai.com/v1/responses`, `POST https://api.openai.com/v1/chat/completions` | `Authorization: Bearer ...` 1개를 해당 host의 전송 인증값으로 취급. |

port는 443만 허용한다. URL query의 자격증명 전송을 막기 위해 P0에서 query가 있는 제공자 요청은 거부한다. 임의의 host 접미사·추가 path·redirect 목적지를 허용하지 않는다. 업스트림 redirect는 자동 추종하지 않고 안전한 오류로 반환하여 재검사 없는 재전송을 방지한다.

P0 본문은 `application/json`의 UTF-8 텍스트 입력이며 Content-Encoding은 없거나 identity다. 문자열·중첩 배열·객체를 검사한다. 지원하는 텍스트 콘텐츠 타입만 허용하고 이미지·audio·file 참조·multipart·압축·WebSocket/Realtime 요청은 415로 거부한다. SDK의 `stream=true`는 **응답 SSE 요청**이므로 허용할 수 있으나 전송하는 요청 본문은 여전히 끝까지 검사한다.

인증 헤더 예외는 해당 host의 해당 필드에서만 적용한다. 같은 값이 본문·다른 헤더에 있으면 탐지하며, 인증 필드 값도 UI·로그에서 항상 제거한다. 중복·충돌하는 인증 헤더, Host와 CONNECT 목적지 불일치, 비정상 메시지 framing은 거부한다. 지원 프로토콜을 악용해 인증 헤더를 일반 데이터 유출 채널로 사용하는 모든 경우를 방지한다고 주장하지 않는다.

### C-PROXY-3 — 검사 완료 전 전송 금지

요청 본문 상한은 **1MiB(1,048,576 bytes)**, 헤더 총합은 16KiB, JSON 최대 깊이는 32다. 요청 body 수신 timeout은 10초, 검사·필수 감사의 hard timeout은 1초다. 본문은 메모리에서 전부 받은 뒤 검사·감사를 마쳐야 외부 요청 헤더와 본문을 보낼 수 있다. TLS 연결 사전 준비와 데이터 전송은 구분한다.

Content-Length가 있으면 먼저 상한 검사하고 실제 수신 bytes도 확인한다. chunked 입력도 실제 합계 크기·시간을 제한한다. 요청 body streaming과 `stream_large_bodies`를 통한 검사 우회는 끈다. 청크 앞부분을 먼저 보내고 뒤에서 시크릿을 발견하는 누적 윈도우 방식은 금지한다. mitmproxy의 buffering/streaming 의미는 [공식 기능 문서](https://docs.mitmproxy.org/stable/overview/features/#streaming)를 따른다.

허용 요청은 본문을 원본 그대로 전송하며 프로토콜상 필요한 hop-by-hop header 처리를 제외하면 의미를 바꾸지 않는다. 정상 응답 SSE는 지연 없이 relay할 수 있다. 응답 내용 탐지·보관은 범위 밖이며 무제한 response buffering을 하지 않는다. upstream connect timeout 5초, 응답 유휴 timeout 30초, 전체 요청 최대 120초다.

| 상태 | 외부 동작·응답 |
|---|---|
| 시크릿 일치 | 외부 헤더·본문 전송 0, HTTP 403 `AEGIS_SECRET_BLOCKED` |
| JSON/헤더/framing 무효 | 외부 전송 0, HTTP 400 `REQUEST_INVALID` |
| 크기 초과 | 외부 전송 0, HTTP 413 `REQUEST_TOO_LARGE` |
| 미지원 타입·압축·path | 외부 전송 0, HTTP 415 `REQUEST_UNSUPPORTED`; CONNECT의 비허용 목적지는 403 |
| 입력 수신 timeout | 외부 전송 0, HTTP 408 `REQUEST_TIMEOUT` |
| 탐지기·정책·필수 감사 오류/timeout | 외부 전송 0, HTTP 503 및 해당 reason code |
| 업스트림 접속 실패·timeout | 502 또는 504 `UPSTREAM_UNAVAILABLE`, 자동 재전송 없음 |
| 프록시 프로세스 종료 | 클라이언트 연결 실패. 프로세스가 없는데 JSON 오류를 돌려준다고 요구하지 않음. 직접 fallback은 네트워크에서 차단. |

### C-PROXY-4 — 시험·확장 경계

시험용 업스트림은 test 프로필에서 제공자 호환 URL을 사설 fixture로 명시적으로 매핑한다. 운영 프로필은 이를 거부하고 UI에는 `TEST / SYNTHETIC DATA`를 표시한다. fixture는 request_id별 수신 수·bytes 수와 고정된 안전한 응답만 저장하며 본문·헤더 원문은 저장하지 않는다. 이것으로 차단 요청이 실제 전송되지 않았음을 독립적으로 확인한다.

P1 gzip 지원 시 압축 bytes ≤1MiB, 해제 bytes ≤1MiB, 팽창률 ≤20배, timeout은 기존 상한을 유지한다. 초과·오류는 거부하고 미검사 bytes를 전달하지 않는다. brotli·multipart·바이너리·자유로운 요청 스트리밍 지원은 별도 요구 승인 없이 추가하지 않는다.

### C-DETECT-1 — 탐지와 예외 규칙

룰 우선순위는 `알려진 키/개인키 포맷 → 문맥+엔트로피 → 허용`이다. 정규식은 미리 compile하고 무제한 backtracking 패턴을 피한다. 포맷 룰은 접두사와 길이·문자 집합을 함께 검사한다. 최소 룰 ID를 아래처럼 고정하고 테스트 코퍼스와 연결한다.

| rule_id | 탐지 조건 |
|---|---|
| `OPENAI_KEY` | 독립 토큰 경계의 `sk-proj-` 뒤 영숫자·`_`·`-` 20~256자. 실제 유효키 판정이 아닌 후보 탐지. |
| `ANTHROPIC_KEY` | 독립 토큰 경계의 `sk-ant-` 뒤 영숫자·`_`·`-` 20~256자. |
| `AWS_ACCESS_KEY` | 독립 토큰 경계의 `AKIA` 뒤 대문자·숫자 정확히 16자. |
| `GITHUB_PAT` | 독립 토큰 경계의 `ghp_` 뒤 영숫자 정확히 36자. 다른 GitHub 토큰 형식은 별도 룰로 추가해야 지원을 주장할 수 있음. |
| `PRIVATE_KEY` | `BEGIN PRIVATE KEY`, `BEGIN RSA PRIVATE KEY`, `BEGIN EC PRIVATE KEY`, `BEGIN OPENSSH PRIVATE KEY` 중 하나의 PEM 시작 표식. |
| `CONTEXT_ENTROPY` | 영숫자 및 `+ / = _ -`의 연속 후보 20~128자, 문자 분포 Shannon entropy ≥4.0, 아래 secret 문맥에 해당. |

secret 문맥은 JSON key가 `api_key`, `apikey`, `secret`, `token`, `password`, `client_secret`, `access_token` 중 하나이거나, 문자열 안 같은 이름의 대입·콜론 뒤 32자 이내에 후보가 오는 경우다. 대소문자를 정규화한다. 엔트로피만 높은 일반 문자열은 차단하지 않는다. UUID·checksum·명백한 플레이스홀더 예외는 **엔트로피 룰에만** 적용하며 알려진 키 포맷 탐지를 우회하지 못한다. 이미지 base64를 건너뛰고 정상 처리하지 말고 미지원으로 거부한다.

Unicode escape는 JSON parser로 해제해 검사하고, 모든 nested 문자열을 스캔한다. 여러 네트워크 청크에 나뉜 키는 합친 뒤 검사한다. 임의의 base64·암호화·조각난 별도 JSON 필드를 모두 복원하는 탐지는 범위 밖이다. 정규식·문맥·entropy의 입력 상한을 공유하여 대용량 입력에서 검사가 무한 지연되지 않게 한다.

P0 예외 목록은 비어 있다. P1 예외 레코드는 `{rule_id, provider_host, value_sha256, expires_at, reason}`으로 정확한 일치만 허용하며 만료 상한은 24시간이다. key 값 원문을 저장하지 않는다. SHA-256은 비밀 보관 수단이 아니므로 낮은 엔트로피 값의 예외 등록은 허용하지 않고, 예외 추가는 신뢰 운영자의 파일 변경·재시작으로만 적용한다. 다른 탐지가 함께 존재하면 전체 요청을 계속 차단한다.

## 7. 전송·로컬 접근·장애 정책

### C-SEC-1 — TLS와 제한된 로컬 예외

외부 HTTPS는 TLS 1.3을 우선 사용하고 peer·라이브러리가 지원하지 않는 경우 검증된 TLS 1.2 이상만 허용한다. 이 경우 실제 협상 버전을 기록하며 ‘전 구간 TLS 1.3’이라고 표시하지 않는다. TLS 1.1 이하·인증서 검증 해제·hostname 검증 해제는 허용하지 않는다. 로컬 개발 CA를 썼다는 이유로 업스트림 인증서 검증을 생략하지 않는다.

같은 장비의 loopback 제어 UI·WebSocket·상태 API와 단일 호스트의 격리된 컨테이너 내부 제어 채널은 HTTP/WS를 허용한다. 이 예외는 호스트로 범위가 제한되고 외부 NIC로 노출되지 않으며 토큰·Origin 검증이 적용된 경우에만 유효하다. 장비 간 통신이나 공유 LAN 노출은 HTTPS/WSS로 바꾼다. 시험 fixture의 HTTP는 test 네트워크에서만 허용한다.

### C-SEC-2 — CA·토큰·접근 제한

CA는 설치 장비별로 생성하고 개인키 파일 0600·디렉토리 0700으로 보호한다. CA키는 프록시 전용 runtime에만 둔다. 신뢰는 보호 컨테이너 또는 선택한 클라이언트의 CA bundle에 한정하며 시스템 전역 root store·일반 브라우저 프로필을 변경하지 않는다. 지원되지 않는 클라이언트에서 `verify=false`로 우회하지 않는다. README에 적용·해제 방법을 기록한다.

로컬 API는 loopback에 bind하고 서버가 생성한 CSPRNG 256bit 이상의 토큰을 요구한다. 외부 NIC의 `0.0.0.0`으로 기본 노출하지 않는다. 컨테이너 내부 listener는 분리된 네트워크에 두고 호스트로 공개하는 port는 loopback에만 publish한다. 기본 host port는 UI 8787, 프록시 8080이며 충돌은 명확히 알리고 명시적 설정으로 변경한다.

Origin은 설치 시 확인한 extension origin 및 UI origin으로 한정한다. WebSocket도 Origin·인증을 검증한다. Host allowlist로 DNS rebinding을 방어하고, credential과 결합된 `Access-Control-Allow-Origin: *`는 금지한다. 원격 페이지·RBI 네트워크는 제어 API에 접근할 수 없다. 세션 인증값을 URL·로그·페이지 DOM의 공개 영역에 넣지 않는다.

### C-SEC-3 — 최소 위협 모델

NFR Design에는 아래 자산·위협·통제·검증·잔여 위험을 최소 기준으로 포함한다. 표의 통제는 개발할 요구이며 현재 구현됐다는 주장이 아니다.

| 위협 | 필수 통제 | 주요 검증·잔여 범위 |
|---|---|---|
| 원격 웹 활성 콘텐츠의 로컬 실행 | 탐색 전 가로채기, 픽셀 전달, 신뢰 viewer | T-WEB·D-1; 브라우저 자체 취약점은 별도 |
| 위험 액션의 파일·클립보드·메일 앱 유출 | 원격 이벤트와 통로 차단 | D-1; 일반 텍스트 수동 입력은 범위 한계 |
| RBI를 통한 내부망 접근·DNS rebinding | 목적지 검사와 실제 egress 제한 | T-SSRF |
| 격리 세션 탈취·교차 접근 | 토큰·Origin·소유 검증·TTL | T-WEB·T-TRANSPORT |
| 미서명·변조 정책 실행 | ML-DSA, 닫힌 스키마, 생성 전 검증 | T-SIGN |
| 검증 후 정책 바꿔치기 | 같은 bytes의 검증·스냅샷·실행 | T-TOCTOU |
| 샌드박스 자격증명·관리 소켓 접근 | 최소 mount·비특권 실행·Landlock 강제 | T-CAGE |
| 프록시 종료·대체 라우트 우회 | 클라이언트 egress 제한 | T-PROXY |
| 청크·압축·대용량을 통한 검사 우회 | 전체 버퍼·상한·미지원 거부 | S-08·T-BODY |
| 로그·오류·UI의 시크릿 노출 | 원문 없는 이벤트, 고정 오류, 출력 검사 | T-PRIVACY |
| CA키·서명키·신뢰키 손상 | 역할 분리·권한·runtime 미배포·수동 폐기 | T-KEY; 신뢰 관리자 손상은 범위 한계 |
| 로그 파일 재작성·삭제 | API 추가 기록, 제한 권한·hash 검증 | T-AUDIT; 악성 관리자에 대한 무결성 증명은 P2 |

### C-FAIL-1 — 장애별 집행

| 상황 | 필수 동작 | 복구 |
|---|---|---|
| RBI 미가용·프레임 연결 종료 | 새 격리 탐색·원격 입력 차단. 로컬 원본 URL로 전환하지 않음. 명시 신뢰 사이트는 기존 유효 규칙 범위에서만 계속 허용. | 새 인증·새 원격 세션 |
| 웹 정책 무효·DNR 갱신 실패 | 새 보호 탐색 차단 또는 이전 검증 규칙 유지. 분류 실패를 직접 허용으로 처리하지 않음. | 설정 재검증·규칙 원자 적용 |
| 서명·스키마·신뢰키·OpenShell 버전 실패 | 샌드박스 생성 및 명령 실행 거부 | 유효 정책·검증 환경으로 다시 run |
| OpenShell 생성·정책 적용 확인 실패 | 명령 미실행, 생성된 자원 정리 | 준비 검사 후 새 생성 |
| 프록시 종료 | 보호 클라이언트의 업스트림 연결 불가 | 프록시 준비 확인 후 새 요청. 미확정 요청 자동 재전송 금지 |
| 검사기 예외·본문 상한·미지원 형식 | 요청 헤더·본문 미전송, 명시적 오류 | 입력 수정 후 새 요청 |
| 감사 writer·저장소 오류 | 새 웹 세션/경계 동작·에이전트 실행·LLM 전송 거부. 이미 거부할 작업은 계속 거부. | 저장소 복구 확인, 정책 재검증, 새 작업 |
| UI만 중단·조회 실패 | 집행 Unit과 writer가 정상이면 보호 동작은 유지. UI는 연결 오류 표시. | 조회 재연결 |
| 프로세스 재시작 | 이전 작업의 성공을 추측하지 않고 정책·키·의존성을 재검증 | 진행 중 세션 종료·새 작업 식별자 |

필수 감사는 세션 생성·탐색 판정·위험 액션·정책 실행 허용/거부·LLM 허용/거부·실행 종료다. 동작 허용 전 이벤트를 기록하고 writer acknowledgement를 확인한다. 매 프레임을 로그로 남길 필요는 없다. 기존 세션의 일반 입력은 writer 준비 확인을 거쳐 처리하고 writer와 연결이 끊겼으면 릴레이를 중단한다. 외부 동작이 이미 발생한 뒤 종료 이벤트 기록이 실패하면 이를 되돌렸다고 주장하지 말고 새 작업을 차단한다.

## 8. 데이터·감사 제약

### C-DATA-1 — 이벤트 스키마

이벤트는 허용 필드만 직렬화한다. 최소 필드는 `schema_version`=1, event_id, ts(UTC ISO 8601), workflow_id, session_id(해당 시), request_id(해당 시), unit, actor(`local-user` 등 고정 역할), action, verdict, reason_code, rule_id(해당 시), policy_kind, policy_id, policy_version, policy_digest, evidence_hash이다.

추가 허용 필드는 검증된 대상 host·port, command_label, pubkey_id, counts, duration_ms, exit_code다. 입력이 정책 검증에 실패해서 metadata를 신뢰할 수 없으면 해당 필드는 null로 두고 미확인 상태를 표시한다. 임의 URL·오류 객체·HTTP body·원시 명령을 그대로 직렬화하는 `details` 필드는 금지한다.

evidence_hash는 **해당 이벤트에서 evidence_hash 필드를 제외한 안전한 필드 전체**를 `UTF-8 + JSON 키 정렬 + 불필요한 공백 없음 + Unicode 직접 출력 + 정수 기반 수치`로 직렬화한 bytes의 SHA-256 hex이다. timestamp는 문자열, duration은 정수 밀리초로 기록한다. float·NaN·Infinity를 허용하지 않는다. 개별 hash는 우발적 불일치 검출용이며 공격자가 전체 파일과 hash를 다시 쓰는 것을 막지 않는다. 원본 시크릿을 evidence_hash의 입력으로 사용하지 않는다.

### C-DATA-2 — 저장·보존·제거

| 데이터 | 위치·보존 | 제약 |
|---|---|---|
| 요청 원문·인증 헤더 | 프록시 메모리에서 요청 처리 동안만 | flow dump·HAR·일반 access log·trace body·core dump·디스크 임시 spool을 끈다. Python 메모리의 완전한 암호학적 소거까지 보장하지 않음. |
| 원격 페이지·쿠키·프레임 | 원격 브라우저 임시 영역·bounded memory | 세션 종료/만료 시 폐기. 프레임 녹화 기본 비활성. |
| 감사 이벤트 | `.aegis/audit/<workflow_id>.jsonl` | 디렉토리 0700·파일 0600. 세션별 파일, 기본 7일 보존, 제품 API에서 수정·삭제 없음. |
| 개인키·CA키 | 역할별 `.aegis/keys/` 또는 별도 관리 경로 | 0700/0600, git·이미지·일반 실행 mount 제외. |
| 테스트 fixture·안전한 결과 | `tests/fixtures/`, `evidence/` | 비활성 합성 입력만. fixture와 런타임 출력 구분. |

감사 저장 용량 상한은 100MiB다. 상한 도달 시 새 보호 동작을 차단하고 운영자에게 보관·정리 필요를 표시한다. 실행 중 writer가 기존 로그를 truncate/rotate-delete하지 않는다. 7일 경과 파일 정리는 별도 관리 명령이 종료된 세션에만 수행하고, append-only API와 운영 보존기간 삭제를 구분해 문서화한다. `down`은 서비스를 정리하되 감사 파일을 삭제하지 않는다.

`.gitignore`에 `.env`, `.aegis/`, 키·인증서 개인키·flow dump·브라우저 프로필을 포함한다. 공개 fixture는 실제 서비스에 유효하지 않은 합성값만 저장한다. 사용자 홈·기존 인증서 저장소·기존 프로젝트 파일을 정리 대상에 포함하지 않는다.

### C-DATA-3 — 기록 일관성과 출력 검증

단일 writer가 큐를 받아 JSONL 한 행씩 append하고 필수 이벤트는 flush·fsync 후 성공을 알린다. 대기열 상한은 1,000 이벤트이며 초과나 1초 내 acknowledgement 실패는 감사 장애로 취급한다. 런타임 로그의 수정·삭제 API를 만들지 않는다. 동시 기록 시험으로 행 손상·ID 중복·누락을 확인한다.

합성 시크릿 전체와 원문 패턴을 애플리케이션 로그·mitmproxy 출력·오류·UI export·시험 결과에 검색한다. 검증 fixture 원본·격리된 합성 요청 입력은 명시한 제외 대상이며, ‘저장된 파일 모두에 시크릿 0건’처럼 fixture 존재와 모순되는 표현을 쓰지 않는다. 디버그 출력에서도 같은 기준을 적용한다.

## 9. 사용성·실행 스크립트

### C-UX-1 — 최소 화면과 온보딩

상태 카드 3개, 정책 요약, 이벤트 목록·상세만 만든다. 보안 용어만 표시하지 말고 ‘전송하지 않았습니다’, ‘검증 실패로 실행하지 않았습니다’처럼 결과를 설명한다. 활성·중단·미설정을 다른 상태로 표시하고 색 외 텍스트·아이콘을 사용한다. 비밀의 일부 문자 노출 대신 값 전체를 `[REDACTED]`로 표시한다.

온보딩 순서는 `사전 조건 확인 → doctor → 선택한 클라이언트 CA 설정·확장 수동 설치 → up → guard/cage/web 순으로 정상 경로 확인 → D-1~D-3`다. 확장 개발자 모드 로드와 CA 설정은 최초 준비 단계로 README에 명시한다. ‘단일 기동’이 최초 OS 설치·확장 설치·인증서 설정까지 자동화한다는 뜻은 아니다.

설치·기동은 기존 브라우저 프로필과 시스템 CA를 변경하지 않고 전용 디렉토리를 사용한다. `doctor`가 정상 기능과 우회 차단을 검증한 Unit만 활성으로 표시한다. 포트 충돌·버전 불일치·OpenShell 미가용·PQC import 실패·CA 미신뢰·writer 오류에 각각 실행 가능한 복구 안내를 제공한다.

## 10. 성능·검증 측정

### C-PERF-1 — 측정 계약

| 항목 | 방법·표본 | P0 합격 |
|---|---|---|
| RBI 입력 지연 | 준비된 로컬 VM의 1280×720·10fps 시험 페이지. 클릭 후 화면 색/카운터 변화가 viewer에 표시되는 시점을 측정. warm-up 10회 후 입력 100회, 외부 사이트 응답 대기 제외. | P95 ≤300ms, 첫 프레임 ≤5초 |
| 프록시 지연 | 연결 준비·warm-up 20회 후 무해한 1KiB·16KiB·64KiB JSON 각 200회, 동시성 1. 전체 body 수신 완료부터 검사+필수 fsync acknowledgement 완료까지 측정. | 각 크기 그룹 P95 ≤30ms |
| 큰 입력 안전성 | 1MiB 이하 경계 입력과 초과 입력, 검사 최대 1초·수신 최대 10초 확인 | 제한 시간·크기 준수, 미검사 전송 0 |
| 기동 | 의존성·이미지가 준비된 상태에서 up→모든 필수 준비 검사 종료 | ≤60초. 최초 다운로드 시간 별도 |
| 이벤트 UI | 이벤트 append acknowledgement→화면 노출 | ≤3초, 기본 polling 1초 |

P95는 정렬된 n개 표본의 `ceil(0.95×n)`번째 값으로 계산한다. CPU·RAM·OS·가상화·파일시스템·네트워크 조건·브라우저·의존성 버전과 P50/P95/최대값을 기록한다. 프록시 내부 처리 지표를 전체 LLM 응답 지연이나 네트워크 추가 왕복 지연으로 표현하지 않는다. 실제 종단 시간도 참고값으로 따로 기록한다.

측정치 미달은 실패 또는 미충족으로 기록하고 원인을 설명한다. P0 수치를 사후에 몰래 바꾸거나 fsync·탐지를 꺼서 통과시키지 않는다. 성능 목표 변경이 필요하면 FR/NFR과 이유·측정 결과를 함께 갱신한다.

## 11. 외부 근거·라이선스·기존 문서 정정

### C-EVIDENCE-1 — 근거와 주장

기술 확인 기준일은 2026-09-07이다. 이 문서에서 인용한 공식 자료는 API·스키마·알고리즘 설명의 근거이며, 현재 장비에서 해당 구성의 설치·성능·보안을 시험했다는 증거는 아니다. 잠근 실제 버전의 공식 문서와 실행 결과가 다르면 차이를 기록하고 계약을 갱신한다.

로컬 입력 출처는 [기존 requirements](../requirements/requirements.md), [기존 상세 요구사항](../requirements/requirements_new.md), [기존 constraints](../requirements/constraints.md), [검증 질문·제안 답변](../requirements/requirement-verification-questions.md), [평가 기준](../assessment.md), [AI-DLC 워크플로](../CLAUDE.md)와 `.aidlc-rule-details/`의 공통·요구 분석·Unit·검증·opt-in 안내다. 과거 문서는 수정하지 않고 변경 의미를 아래 표에 기록한다.

직접·전이 의존성의 라이선스를 버전별로 확인하고 `THIRD_PARTY_NOTICES.md`에 이름·버전·출처·라이선스를 적는다. 각 라이선스가 요구하는 NOTICE·저작권 표기를 포함한다. 모든 구성요소를 일괄 Apache-2.0이라고 추정하지 않는다.

FIPS 204, OWASP ASVS, OWASP Secrets Management는 관련 설계 항목을 연결하는 참고 기준이다. 전체 표준 준수·인증을 받았다고 주장하지 않는다. 표준 매핑을 작성할 때는 확인한 공식 문서·버전·적용 항목·테스트와 미적용 범위를 함께 기록한다.

### C-CHANGE-1 — 이전 자료에서 정리한 차이

| 이전 표현·충돌 | 이번 기준안 | 이유·영향 |
|---|---|---|
| 질문은 제안 상태인데 Approved·locked 표시 | 새 문서는 기준안이며 실제 승인 별도 | AI-DLC 승인 증거의 진실성 유지 |
| U-5 AuditFabric/AuditTrail 혼용 | AuditTrail로 통일 | Unit·코드·증거 추적 일치 |
| 다운로드 확인 후 허용 vs 기본 차단 | P0 파일·클립보드·비밀번호 통로 차단 | 검사 없는 파일 반출과 과도한 구현 범위 제거 |
| 모든 OpenShell hot-reload 이벤트 재검증 | P0 종료·재검증·재생성, P1 통제된 동적 갱신 | 미확인 훅에 의존하지 않고 정적/동적 정책 구분 |
| 모든 FS/network 금지 | 필요한 샌드박스 runtime·작업 경로 및 선택된 프록시만 허용 | 정상 에이전트 작업 가능성과 최소권한 양립 |
| 전 클라이언트의 아웃바운드 자동 가로채기 | 보호 네트워크의 지원 클라이언트로 한정 | 실제 집행 경계와 호환 범위를 입증 가능하게 함 |
| 비대상 host는 프록시에서 터널 통과 | 제공자 전용 프록시는 비허용 목적지 거부 | 보호 환경에서 우회 유출 통로 제거 |
| 청크 누적 검사, 압축·파일 폭넓은 지원 | P0 전체 본문 검사, 미지원 형식 거부 | 검사 완료 전 부분 유출 방지 |
| 요청 헤더의 모든 키 차단 | 정확한 제공자 인증 필드만 예외, 본문·다른 헤더는 탐지 | 정상 인증과 유출 탐지의 충돌 해소 |
| ML-DSA-65 128b급 | NIST category 3 | 암호 설명 정정 |
| 모든 채널 TLS 1.3 | 외부 검증 TLS, 제한된 로컬 예외 명시 | 로컬 개발 통신의 실제 구성과 주장 일치 |
| 1080p/15fps·150ms 모두 필수 | P0 720p/10fps·P95 300ms, 향상 목표 P1 | 실제 픽셀 격리와 조작 가능한 기능 완성 우선 |
| SHA-256·append-only로 수정/삭제 불가능 | 앱 추가 기록·metadata hash, 관리자 재작성 한계 명시 | 암호학적 불변성·WORM 과장 제거 |

이 표는 이번 문서의 범위 조정 근거다. 이전 요구 ID는 가능한 한 역할을 유지했으나 의미가 바뀐 항목은 새 AC와 이 표를 기준으로 재추적한다.

## 12. AI-DLC 수행·산출물·평가 근거

### C-AIDLC-1 — 실제 절차와 승인

본 기준안 작성은 향후 AI-DLC 실행의 입력 준비다. 실제 개발 착수 시 `CLAUDE.md`와 `.aidlc-rule-details/`의 관련 단계 규칙을 읽고 workspace/state를 확인한다. 기존 코드가 없다면 Greenfield이며 Reverse Engineering은 생략 이유를 기록한다. 복잡도는 Complex, Requirements Analysis 깊이는 Comprehensive로 제안한다.

Inception에서는 요구 확인, User Stories, Workflow Planning, Application Design, Units Generation을 수행한다. 사용자 스토리·5 Unit·명시된 기본값을 입력으로 재사용하고 무의미하게 다시 선택시키지 않는다. 이번 문서에 대한 승인과 이후의 설계·코드 생성 승인을 구분한다. 실제 단계에서 사용자에게 받은 결정·승인 문구와 시각만 기록하고, AI의 제안이나 ‘문서 작성 요청’을 모든 후속 단계 승인으로 간주하지 않는다.

Construction에서는 Unit별 기능 설계·NFR·인프라 필요성을 판단해 수행/생략과 이유를 기록하고, 코드 생성 후 Build and Test를 수행한다. 선택한 단계의 필수 산출물은 빠뜨리지 않되 깊이는 실제 복잡도에 맞춘다. Operations는 현재 로컬 가이드에서 placeholder이며 자동 운영·배포를 완료했다고 쓰지 않는다.

`aidlc-docs/aidlc-state.md`에는 현재 단계, 실제 완료·생략 상태, 복잡도·근거, 산출물 경로, 미해결 사항을 유지한다. `aidlc-docs/audit.md`는 개발 대화·결정·승인의 과정 기록이며 U-5의 런타임 보안 이벤트 파일과 분리한다. 사용자 원문을 기록하는 절차에서도 실제 키를 수집하지 않고 합성값·자리표시자를 사용한다. 상태와 계획 checkbox는 실제 작업이 끝날 때 갱신한다.

### C-AIDLC-2 — 질문과 확장 규칙

질문은 이 문서로 해결되지 않은 제품 범위·권한·외부 접근 결정에만 집중한다. V-1~V-4는 실행 검증으로 해결할 기술 작업이다. 과거 검증 질문 파일의 `(제안)` 답변을 실제 사람 답변으로 옮기지 않는다. 새 답변은 출처·날짜와 함께 기록한다.

현재 workspace에는 Security Baseline, Resiliency Baseline, Property-Based Testing의 opt-in 안내가 있다. 이번 입력 문서 작성만으로 어느 확장도 사용자가 선택했다고 기록하지 않는다. 실제 Requirements Analysis에서 opt-in 질문과 답변을 처리하고 `aidlc-state.md`의 Extension Configuration에 결과를 명시한다. 로컬 규칙의 ‘설정 부재 시 기본 적용’과 혼동되지 않게 **아직 미결정인 상태를 완료 상태로 남기지 않는다**. 활성화된 확장의 전체 규칙을 그때 읽고 단계별 적용·N/A·위반을 기록한다.

제품의 P0 보안 제약은 확장 선택과 무관하게 적용한다. 일반적인 단일 사용자 시제품 범위를 이유로 P0를 완화하거나, 선택하지 않은 운영 확장으로 고가용성·재해복구·전사 인증 같은 범위를 자동 추가하지 않는다. 필요한 추가 질문은 로컬 question-format-guide의 전용 파일 형식으로 작성한다.

### C-AIDLC-3 — Unit 실행과 변경 기록

5 Unit의 책임·공통 계약·요구 매핑을 Units Generation 산출물에 반영한다. 단일 실행자는 로컬 가이드의 Unit별 설계→구현 순서를 따른다. 여러 담당자가 작업할 경우 공통 계약·소유 파일·통합 지점을 먼저 정하고, 실제로 동시에 수행한 기록이 있을 때만 병렬 개발했다고 설명한다. 5 Unit으로 나누었다는 사실만으로 병렬 실행 증거가 되지는 않는다.

단계·Unit별로 리뷰 가능한 변경을 묶고 실제 커밋이 있으면 hash와 대응 산출물을 기록한다. 이후 평가를 위해 과거 승인·커밋 시각·진행 기록을 소급해서 만들지 않는다. 동일한 사실을 여러 문서에 복사하기보다 권위 있는 원본을 연결한다.

### C-AIDLC-4 — 후속 산출물의 실제 경로

아래는 **앞으로 생성할 산출물 목록**이며 현재 존재한다고 주장하는 목록이 아니다. 실제 단계 규칙이 요구하는 세부 파일은 추가로 생성한다.

| 목적 | 후속 산출물 위치 |
|---|---|
| 상태·대화·승인 | `aidlc-docs/aidlc-state.md`, `aidlc-docs/audit.md` |
| 승인된 요구·질문 | `aidlc-docs/inception/requirements/requirements.md`, `constraints.md`, 필요 시 `requirement-verification-questions.md` |
| 사용자 스토리·페르소나 | `aidlc-docs/inception/user-stories/`의 해당 단계 필수 파일 |
| 워크플로·분해 계획 | `aidlc-docs/inception/plans/`의 실제 실행 계획 |
| 설계·5 Unit·의존·스토리 매핑 | `aidlc-docs/inception/application-design/`의 `unit-of-work.md`, `unit-of-work-dependency.md`, `unit-of-work-story-map.md` 및 설계 파일 |
| Unit별 기능·NFR·인프라 | `aidlc-docs/construction/<unit-name>/` 아래 수행한 단계의 필수 파일 |
| 빌드·테스트 | `aidlc-docs/construction/build-and-test/`의 build/unit/integration/performance 지침·summary와 필요한 security/e2e 지침 |
| 요구→코드→검증 추적 | `aidlc-docs/traceability-matrix.md` |
| 도입·차별화·잔여 위험 | `aidlc-docs/differentiation-and-adoption.md` |
| 검증 원본 | `evidence/`의 실행 명령·환경·안전한 결과·스크린샷·표본. 생성된 파일만 링크. |
| 방법론 검토 | `evaluation/ai-dlc-compliance-log.md` |
| 사용 안내·설정·권리 | `README.md`, `.env.example`, `THIRD_PARTY_NOTICES.md`, lockfile |

실제 개발에서 `new/` 입력을 승인된 Inception 경로로 반영한 이후에는 그 승인본을 기준으로 삼는다. 두 곳을 서로 독립적인 최신본으로 관리하지 않는다. 문서 이동·승인 시 버전과 원본 출처를 기록한다.

### C-EVAL-1 — assessment.md와 연결할 증거

제공된 `assessment.md`는 배점과 동시에 기존 자기평가 문구·예시 파일명을 담고 있다. 거기에 적힌 ‘동작 완료’, ‘오탐 0’, ‘병렬 개발’, ‘보안 충족’은 현재 구현 증거가 아니며 실제 개발 후 확인해야 한다. 다음 연결표는 높은 평가를 받을 수 있도록 **구현과 검증의 우선순위를 정하는 기준**이며 점수를 미리 보장하지 않는다.

| 평가 항목·배점 | 실제로 남길 근거 | 이 기준안의 대응 |
|---|---|---|
| AI-DLC 사용 충실성 25 | 복잡도·단계 선택 이유, 실제 사람 승인, 상태·감사, 5 Unit·의존·스토리 매핑, 실제 단계별 변경 기록 | C-AIDLC-1~C-AIDLC-4, requirements §4·§9 |
| 문제 정의 및 해결 20 | 3대 경계의 문제→스토리→FR/NFR→코드→검증 추적, 정상·공격·장애 결과 | requirements §1·§5·§8·§9 |
| 창의성 15 | 범주별 경쟁/대안 비교, 재사용과 자체 통합 구분, HMAC·일반 비대칭 서명·PQC 선택 근거와 한계 | 공통 정책·workflow_id·이벤트 통합, C-PQC-1~C-PQC-3 |
| 완성도 15 | 실제 D-1~D-3, 8개 양성+8개 음성, 우회·TOCTOU·인증 예외·로그 비노출 시험, 재현 명령 | requirements §8, C-DEP-3, C-PERF-1 |
| 사용성 15 | 단일 기동, 단계별 온보딩, 정상 작업 지속, 상태·사유·재시도 UX, 다른 사용자 재현 기록 | requirements §6, NFR-7·NFR-12, C-UX-1 |
| 유지보수성 및 보안 10 | 최소 위협 모델, 버전·키·정책 경계, fail-closed 집행, 원문 없는 감사, 설정·라이선스 | C-DEP-1~C-DEP-2, C-SEC-3, C-FAIL-1, C-DATA-1~C-DATA-3 |

경쟁 비교는 ‘다른 제품은 AI 워크플로우를 지원하지 않는다’는 일괄 단정 대신 RBI 도구·OpenShell 단독·시크릿 검사 도구·AEGIS 조합이 어느 경계를 어떻게 다루는지 공식 근거로 비교한다. 평가 문서에서 파일명은 위 실제 경로로 연결하고, 존재하지 않는 파일이나 캡처만으로 보안 동작을 입증하지 않는다. UI 화면·집행 결과·수신 관측·테스트 결과가 일치해야 한다.

## 13. 문서 정합성 점검

후속 변경마다 다음을 확인한다.

1. P0/P1/P2와 FR/NFR·시나리오·기술 기본값이 일치한다.
2. 정상 인증과 시크릿 탐지, 원격 픽셀과 로컬 경고, 샌드박스 최소권한과 정상 작업, 감사 보존과 append-only의 의미가 충돌하지 않는다.
3. 실패 조건마다 실제 거부 집행 위치가 있고 UI 표현과 일치한다.
4. 측정 수치에는 환경·표본·구간이 있으며 아직 측정하지 않은 목표를 성과로 표현하지 않는다.
5. 승인·구현·시험·병렬 실행·표준 준수 주장은 실제 근거가 있는 범위에 한정한다.
