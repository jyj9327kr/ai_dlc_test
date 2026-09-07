# Application Design Plan — AEGIS

역할: Application Architect | 단계: INCEPTION → Application Design | 작성일: 2026-09-07
상태: ✅ 승인됨 (2026-09-07T08:30:00Z, Q1~Q5 = 전부 A). 설계 산출물 생성 완료.

이 문서는 5 Unit + 공통 `contracts`의 **고수준 컴포넌트·인터페이스·서비스 계층·의존 관계**를 정의하기 위한 계획이다. 상세 비즈니스 로직은 이후 Functional Design(per-unit)에서 다룬다. 컴포넌트 경계·디렉토리(C-DEP-2)·기술 스택(C-DEP-1)·제품 동작은 기준안에 잠겨 있어 재질문하지 않는다(C-AIDLC-2). 구현 순서 Q2=A·MVP 범위 Q1=A·확장(Security Full/PBT Partial)을 반영한다.

---

## A. 확정된 입력 (재질문 안 함)
- **컴포넌트**: U-1 WebIsolate, U-2 AgentCage, U-3 SecretGuard, U-4 PolicyCore, U-5 AuditTrail + 공통 `contracts`.
- **의존 방향**: `U-1/U-2/U-3 → U-4, U-5`; U-4·U-5는 서로/방어 Unit 미참조.
- **디렉토리(C-DEP-2)**: `apps/extension/`(TS), `src/aegis/{web,cage,guard,policy,audit,contracts}/`(Py), `tests/`, `scripts/`, `config/`.
- **기술 스택(C-DEP-1)**: Chrome MV3+TS 확장, Python+FastAPI+정적 HTML/CSS/TS 제어 UI, Playwright Python+고정 Chromium(RBI), Python wrapper+OpenShell CLI(cage), mitmproxy/mitmdump addon(proxy), liboqs-python ML-DSA-65(서명), 단일 writer JSONL/ext4(audit), pytest.
- **배포**: "5 Unit ≠ 5 서비스". 단일 장비·단일 사용자·동시 세션 1개(§2.2).

---

## B. 설계 결정 질문 (Step 4)

각 질문의 `[Answer]:` 뒤에 알파벳을 적어 주세요. 없으면 `X) Other`. 권장안을 표시했습니다. 모두 작성 후 "완료" 또는 "승인"이라고 알려 주세요.

### Question 1: 컴포넌트 실행·통신 형태 (Runtime Topology)
5 Unit은 서로 다른 성격(라이브러리 vs 프로세스)입니다. 어떤 토폴로지로 구성할까요?

A) **하이브리드 (권장)** — U-4 PolicyCore·U-5 계약 타입·`contracts`는 **in-process 공유 라이브러리**로 각 Unit이 import. 본질적으로 프로세스인 요소만 별도 프로세스: mitmproxy(U-3 전송), Playwright Chromium(U-1 RBI 서버), FastAPI 제어 UI, Chrome 확장. U-5 감사는 **단일 writer 프로세스**(Q2 참조). 프로세스 간은 loopback로만 통신. 단일 장비 범위에 부합하고 서비스 남발을 피함. [권장]

B) **로컬 마이크로서비스** — 모든 Unit을 loopback HTTP 서비스로 분리. 경계는 뚜렷하나 단일 사용자·단일 세션 범위에 과도, 기동·지연·복잡도 증가.

C) **단일 모놀리식 프로세스** — 확장·mitmproxy·Chromium 외 전부 한 프로세스. 단순하나 단일 writer 감사·fail-closed 격리·프록시 강제 경유 검증이 어려워짐.

X) Other (아래 [Answer]: 설명)

[Answer]: A 

### Question 2: 단일 writer 감사(U-5) 실현 방식
FR-5.1은 "단일 writer가 JSONL을 순차 추가"를 요구합니다. 여러 Unit(다른 프로세스 포함)이 이벤트를 남길 때 어떻게 단일 writer를 보장할까요?

A) **전용 감사 writer(단일 프로세스) + loopback 수신 (권장)** — 모든 Unit이 이벤트를 loopback(UDS 또는 127.0.0.1)로 전용 writer에 보내고, writer만 파일에 append. writer 중단·쓰기 실패 시 `AUDIT_UNAVAILABLE`로 fail-closed(FR-5.4). event_id 유일·순차 보장 용이. [권장]

B) **파일 락 append** — 각 프로세스가 advisory lock으로 직접 append. 단순하나 "단일 writer" 의미가 약하고 부분 쓰기·경합 위험, fail-closed 신호 전파가 어려움.

C) **SQLite(WAL) 후 JSONL export** — DB로 직렬화. 요구의 JSONL·ext4·단일 writer 기본값과 어긋나 채택 시 C-DATA 계열 제약 수정 필요.

X) Other (아래 [Answer]: 설명)

[Answer]: A

### Question 3: 정책 검증(U-4) 호출 형태
방어 Unit(U-1/U-2/U-3)이 정책 서명·스키마 검증을 어떻게 사용할까요?

A) **in-process 공유 검증 라이브러리 (권장)** — `src/aegis/policy`가 검증 함수·신뢰키 로더를 제공하고 각 Unit이 직접 호출(cage는 CLI 내에서 호출). 실행 환경엔 공개키만. 검증 로직 단일 소스로 일관성·PBT 용이. HMAC 대체·가짜 성공 없음(FR-4.2). [권장]

B) **검증 서비스(loopback)** — 별도 검증 데몬에 요청. 네트워크 표면·추가 신뢰 경계가 생겨 단일 장비 범위에 과도.

X) Other (아래 [Answer]: 설명)

[Answer]: A

### Question 4: 오류·판정 모델 일관성 (Cross-Unit Error Model)
세 방어의 차단·오류를 어떻게 표준화할까요? (§6 UI는 사유·event_id·다음 행동 표시 요구)

A) **공통 판정/오류 계약을 `contracts`에 정의 (권장)** — `verdict`(ALLOW/BLOCK/ERROR), `reason_code`(예: `POLICY_SIGNATURE_INVALID`, `AEGIS_SECRET_BLOCKED`, `AUDIT_UNAVAILABLE`), 안전한 위치 식별자, 권장 행동을 공통 타입으로 두고 모든 Unit·UI·CLI가 공유. fail-closed 상태도 공통 표현. [권장]

B) **Unit별 개별 오류 모델** — 각 Unit이 자체 코드 정의. 통합 UI·workflow_id 조회(FR-0.3/5.3) 매핑 비용 증가.

X) Other (아래 [Answer]: 설명)

[Answer]: A

### Question 5: 제어 평면(UI/CLI) 경계
제어 UI·CLI가 각 Unit 상태·이벤트를 어떻게 얻을까요?

A) **FastAPI 제어 서버가 loopback 집약 (권장)** — 제어 서버가 각 Unit 상태(준비/보호활성/차단/사용안함)와 감사 조회를 loopback API로 노출하고, 정적 UI(HTML/CSS/TS)·`scripts/aegis` CLI가 이를 사용. 토큰·Origin·Host 검증(C-SEC). 최소 상태 화면만(§6). [권장]

B) **UI가 각 Unit에 직접 접근** — 제어 서버 없이 UI가 프록시·RBI·감사에 각각 연결. 표면·검증 지점 분산.

X) Other (아래 [Answer]: 설명)

[Answer]: A

---

## C. 설계 산출물 체크리스트 (Step 10 — 승인 후 생성)
- [x] **D-1**: `components.md` — 6 컴포넌트(U-1~U-5 + contracts) 목적·책임·인터페이스(고수준)
- [x] **D-2**: `component-methods.md` — 컴포넌트별 메서드 시그니처·입출력 타입·고수준 목적(상세 규칙은 Functional Design)
- [x] **D-3**: `services.md` — 서비스 정의(제어 서버, RBI 서버, 프록시, cage 실행기, 감사 writer)·오케스트레이션·workflow_id 전파
- [x] **D-4**: `component-dependency.md` — 의존 매트릭스·통신 패턴(in-process/loopback)·데이터 흐름(D-1~D-3, T-FLOW)
- [x] **D-5**: `application-design.md` — 위 문서 통합
- [x] **D-6**: 설계 완전성·일관성 검증(순환 의존 부재 NFR-6, Security/PBT 적용 지점 표기)

## D. 제약 준수 (상시)
- C-AIDLC-2: 시제품 범위로 P0·컴포넌트 경계 완화 금지.
- NFR-6: 순환 의존 없음, 계약(프록시·서명·감사) 독립 테스트 가능하게 설계.
- Security(Full)·PBT(Partial): 각 컴포넌트 인터페이스에 보안 집행·PBT 대상 지점을 표기(상세는 NFR/Functional 단계).
- 이 단계는 고수준 컴포넌트·인터페이스만 — 상세 비즈니스 로직은 Functional Design(per-unit).
