# Unit of Work Plan — AEGIS

역할: Decomposition Lead | 단계: INCEPTION → Units Generation (Part 1: Planning) | 작성일: 2026-09-07
상태: ✅ 승인 완료 (2026-09-07T08:52:00Z — 전 질문 A/권장 채택, Part 2 Generation 실행)

이 문서는 시스템을 개발·테스트 단위(Unit of Work)로 분해하는 계획이다. 유닛 경계(5 Unit + `contracts`)·의존 방향·디렉토리(C-DEP-2)·구현 순서(Q2=A)는 기준안·Application Design에 잠겨 있어 재질문하지 않는다(C-AIDLC-2). 배포는 단일 장비, "5 Unit ≠ 5 서비스"(§4.1). 아래는 경계가 **걸치는** 열린 결정만 묻는다.

---

## A. 확정된 입력 (재질문 안 함)
- **유닛**: `contracts`(공통 타입), U-4 PolicyCore, U-5 AuditTrail, U-3 SecretGuard, U-2 AgentCage, U-1 WebIsolate.
- **의존**: `U-1/U-2/U-3 → U-4, U-5`; contracts 최하위; 순환 없음(NFR-6).
- **구현 순서(Q2=A)**: contracts → U-4 → U-5 → U-3 → U-2 → U-1.
- **디렉토리(C-DEP-2)**: `src/aegis/{contracts,policy,audit,guard,cage,web}/`, `apps/extension/`(TS), `tests/`, `scripts/`, `config/`.
- **배포 모델**: 단일 장비 · monorepo · 서비스 강제 분리 없음(§2.2, §4.1).
- **스토리 매핑**: stories.md에서 이미 Unit별로 정렬(S-U4-*, S-U5-*, S-U3-*, S-U2-*, S-U1-*, S-C-*).

---

## B. 분해 결정 질문 (Step 3)

각 질문의 `[Answer]:` 뒤에 알파벳. 없으면 `X) Other`. 권장안 표시. 모두 작성 후 "완료" 또는 "승인".

### Question 1: `contracts`를 별도 UOW로 둘까?
공통 타입 모듈을 개발·테스트 단위로 어떻게 취급할까요?

A) **독립 기반 UOW로 (권장)** — `contracts`를 UOW-0(기반)로 두고 가장 먼저 완성. 이후 모든 유닛이 안정된 계약에 의존. 직렬화 PBT를 여기서 확립. [권장]

B) **U-4/U-5에 흡수** — 별도 UOW 없이 U-4·U-5 작업에 포함. 문서상 별도 모듈로만 유지.

X) Other (아래 [Answer]: 설명)

[Answer]: A

### Question 2: U-1 WebIsolate의 두 코드 위치(확장 TS + RBI 서버 Py)
U-1은 `apps/extension/`(MV3 TS)과 `src/aegis/web/`(Playwright RBI 서버, Py)에 걸칩니다. UOW 경계를 어떻게 둘까요?

A) **단일 UOW, 두 코드 위치 (권장)** — 확장과 RBI 서버를 하나의 UOW(U-1 WebIsolate)로 묶고 두 코드 위치를 함께 관리. 둘은 제어 메시지 프로토콜로 강결합(로컬 선실행 방지·픽셀 릴레이가 한 기능)이므로 함께 설계·테스트. [권장]

B) **두 UOW로 분리** — 확장(UI)과 RBI 서버(백엔드)를 별도 UOW로. 인터페이스 계약을 UOW 간 계약으로 관리(오버헤드 증가).

X) Other (아래 [Answer]: 설명)

[Answer]: A

### Question 3: 공통 실행 경험(FR-0.x) + 제어 서버/UI의 소속
단일 진입점(`scripts/aegis`), 제어 서버(FastAPI), 통합 상태 UI(FR-5.3), workflow_id 전파(FR-0.3)를 어느 UOW에 둘까요?

A) **U-5 AuditTrail에 포함 (권장)** — 통합 상태 화면(FR-5.3)이 이미 U-5 책임이고 UI는 감사 조회 중심이므로, 제어 서버·UI·FR-0.x 공통 실행을 U-5 UOW에 포함(얇은 `scripts/aegis` 부트스트랩 포함). 유닛 수를 늘리지 않음. [권장]

B) **별도 "Bootstrap/Control" UOW로 분리** — FR-0.x·제어 서버·UI를 독립 UOW(UOW-6)로. 경계는 뚜렷하나 유닛이 하나 늘고 U-5와 UI 결합을 계약으로 관리해야 함.

X) Other (아래 [Answer]: 설명)

[Answer]: A

### Question 4: 유닛별 테스트 자산(코퍼스·fixture) 배치
고정 코퍼스(S/B), 시나리오 fixture, 환경 smoke test(V-1~V-4)를 어떻게 배치할까요?

A) **공유 `tests/` + 유닛별 하위 디렉토리 (권장)** — `tests/`에 유닛별(예: `tests/guard/`, `tests/policy/`)과 공유 코퍼스·fixture(`tests/corpus/`, `tests/fixtures/`)를 두고, 종단(D-1~3)·통합(T-FLOW)은 `tests/e2e/`. 코퍼스·기대결과는 구현 전 고정(§8.2). [권장]

B) **각 유닛 디렉토리 내부에 테스트 동거** — `src/aegis/<unit>/tests/`. 유닛 캡슐화는 좋으나 공유 코퍼스·e2e 배치가 애매.

X) Other (아래 [Answer]: 설명)

[Answer]: A

**모호성 검사 결과**: 4개 답변 모두 단일 옵션(A/권장). 모호·모순 없음 → 계획 승인, Part 2 실행.

---

## C. 유닛 산출물 체크리스트 (Part 2 — 승인 후 생성)
- [x] **U-1(art)**: `aidlc-docs/inception/application-design/unit-of-work.md` — 유닛 정의·책임·코드 조직 전략(Greenfield)
- [x] **U-2(art)**: `unit-of-work-dependency.md` — 유닛 의존 매트릭스·통신·빌드 순서(Q2=A)
- [x] **U-3(art)**: `unit-of-work-story-map.md` — 스토리 → 유닛 매핑(전 스토리 배정 확인)
- [x] **U-4(art)**: 유닛 경계·의존 검증(순환 없음, 전 스토리 배정, 선행 검증 게이팅 표기)

## D. 제약 준수 (상시)
- C-AIDLC-2: 시제품 범위로 유닛 경계·P0 완화 금지.
- NFR-6: 순환 의존 없음, 계약 독립 테스트.
- Q2=A 구현 순서 유지. 이 단계는 분해·경계만 — 상세 설계는 Construction Functional Design.
