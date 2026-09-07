# Story Generation Plan — AEGIS

역할: Product Owner | 단계: INCEPTION → User Stories (Part 1: Planning) | 작성일: 2026-09-07
상태: ✅ 승인됨 (2026-09-07T07:52:00Z, Q1~Q5 = 전부 A). Part 2 Generation 실행 중.

이 문서는 요구사항(`requirements/requirements.md` v4.0 §2.1 페르소나, §4.2 US-1~US-6, §5 FR)을 **사용자 중심 스토리 + 페르소나**로 변환하는 방법론과 실행 체크리스트다. 제품 기본값(격리/차단/서명/프록시 동작 등)은 기준안에 이미 잠겨 있어 재질문하지 않는다(C-AIDLC-2). MVP 범위(Q1=A: 핵심 보안 기능 경로 우선, 보안 집행형 NFR 포함·성능/사용성 NFR 유예)와 구현 순서(Q2=A: contracts+U-4/U-5 → U-3 → U-2 → U-1)를 반영한다.

---

## A. 입력 (재사용)
- **페르소나 초안** (§2.1): 주 사용자(개발자), 정책 관리자, 검증 사용자(동료).
- **스토리 초안** (§4.2): US-1(웹 격리 읽기), US-2(검증 제한 내 에이전트), US-3(키 유출 차단), US-4(보호 상태·차단 사유 확인), US-5(정책·키 교체·안전 재시작), US-6(README 재현).
- **수용 기준 원천** (§5): FR-0.x 공통, FR-1.x WebIsolate, FR-2.x AgentCage, FR-3.x SecretGuard, FR-4.x PolicyCore, FR-5.x AuditTrail.
- **검증 매핑**: D-1~D-3, S-01~S-08/B-01~B-08, T-*.

---

## B. 실행 방법론 질문 (Step 3)

각 질문의 `[Answer]:` 뒤에 알파벳을 적어 주세요. 해당 옵션이 없으면 `X) Other`를 고르고 설명을 적어 주세요. 각 질문에는 이 프로젝트 맥락의 **권장 답변**을 표시했습니다. 모두 작성 후 "완료" 또는 "승인"이라고 알려 주세요.

### Question 1: 스토리 분해 접근 (Breakdown Approach)
US-1~US-6을 어떤 축으로 조직·분해할까요? (구현 순서는 Q2=A로 Unit 의존성 순서가 이미 확정됨)

A) **Unit 중심 + 페르소나 태그 (권장)** — 스토리를 5개 Unit(U-4/U-5 → U-3 → U-2 → U-1)로 그룹화하고, 각 스토리에 관련 페르소나를 태그. 의존성 구현 순서(Q2=A)와 정렬돼 Workflow Planning으로 바로 이어짐. [권장]

B) **페르소나 중심** — 주 사용자/정책 관리자/검증 사용자별로 스토리를 묶는다.

C) **사용자 여정 중심** — 웹 확인 → 에이전트 실행 → LLM 요청의 연속 작업 흐름으로 묶는다.

X) Other (아래 [Answer]: 뒤에 설명해 주세요. 예: Unit·여정 하이브리드)

[Answer]: A

### Question 2: 스토리 세분화 수준 (Granularity)
§4.2의 US-1~US-6을 어느 정도로 쪼갤까요?

A) **Epic → 구현 가능한 하위 스토리 (권장)** — US-1~US-6을 Epic으로 두고, FR 그룹 단위로 INVEST를 만족하는 하위 스토리로 분해(예: US-1 → 판정/픽셀중계/위험액션차단/세션수명/격리실패복구/SSRF제한). 각 하위 스토리가 독립 테스트·구현 단위. [권장]

B) **US-1~US-6 그대로 6개** — 원본 6개를 그대로 스토리로 유지하고 세부는 acceptance criteria로만 표현.

X) Other (아래 [Answer]: 뒤에 설명해 주세요)

[Answer]: A

### Question 3: 수용 기준 형식 (Acceptance Criteria Format)
스토리의 수용 기준을 어떤 형식으로 쓸까요? (§5 원문은 '전제 → 행동 → 결과' 구조)

A) **Given/When/Then + 정상·거부·장애 3경로 (권장)** — 각 스토리에 정상 경로, 거부(차단) 경로, 장애(fail-closed) 경로를 Given/When/Then으로 명시하고 D-1~D-3·T-* ID로 추적 연결. C-SCOPE-1(안전한 차단 유지)·fail-closed 요구를 스토리에 고정. [권장]

B) **평문 체크리스트** — §5 스타일의 서술형 수용 기준만 유지.

X) Other (아래 [Answer]: 뒤에 설명해 주세요)

[Answer]: A

### Question 4: MVP 범위 태깅 (Scope Tagging)
MVP 우선순위(Q1=A)를 스토리에 어떻게 표시할까요?

A) **스토리별 MVP/유예 태그 (권장)** — 각 스토리·하위 스토리에 `[MVP:P0-core]`(핵심 보안 기능 경로 + 보안 집행형 NFR) 또는 `[Deferred:P1/P2]`·`[Deferred:perf/usability NFR]` 태그를 부여해 Workflow Planning 순서의 근거로 사용. [권장]

B) **태그 없이 전량 동일 취급** — 우선순위 구분 없이 모든 스토리를 같은 수준으로 나열.

X) Other (아래 [Answer]: 뒤에 설명해 주세요)

[Answer]: A

### Question 5: 비-P0 스토리 처리 (P1/P2 Coverage)
§3의 P1(동적 정책 갱신, gzip, 탐지 예외목록, RBI 최적화, 집계지표)·P2 항목을 이번 스토리 문서에 어떻게 포함할까요?

A) **P1/P2를 별도 섹션에 스텁으로 기재 (권장)** — 지금은 제목·페르소나·유예 사유만 남기는 placeholder 스토리로 두고, acceptance criteria 상세화는 MVP(P0) 검증 후로 미룬다. 범위 추적성은 유지하되 MVP에 집중. [권장]

B) **P0만 작성** — P1/P2는 이번 스토리 문서에서 완전히 제외(§3 참조로만 남김).

C) **P0·P1·P2 전부 상세 작성** — 모든 우선순위를 동일 상세도로 작성(MVP 우선 지시와 상충 소지).

X) Other (아래 [Answer]: 뒤에 설명해 주세요)

[Answer]: A 

---

## C. 스토리 분해 접근 옵션 설명 (Step 5, 참고)
| 접근 | 장점 | 단점 | AEGIS 적합성 |
|---|---|---|---|
| Unit 중심 + 페르소나 태그 | 의존성 구현순서(Q2=A)와 정렬, Unit 경계=개발/테스트 경계 | 여정 연속성은 태그로만 표현 | ★ 높음 (Q2=A와 정렬) |
| 페르소나 중심 | 이해관계자별 가치 명확 | Unit 경계와 어긋나 구현순서 매핑 추가 필요 | 중 |
| 사용자 여정 중심 | 3경계 연속작업(P-1~P-4) 서사 명확 | 하나의 여정이 여러 Unit 횡단 → 구현 단위 분해 필요 | 중 |
| 도메인/에픽 중심 | 계층 구조 명확 | 본질적으로 Unit=도메인이라 A와 수렴 | 중 |
하이브리드 허용: 기본 Unit 그룹 + 페르소나 태그 + 여정 참조(권장 조합 = Q1=A).

---

## D. 실행 체크리스트 (Part 2: Generation — 승인 후 수행)

- [x] **G-1**: 승인된 답변(Q1~Q5) 반영 방침 확정, 본 계획 상단 상태를 "승인됨"으로 갱신
- [x] **G-2**: `personas.md` 생성 — 주 사용자/정책 관리자/검증 사용자 3 페르소나(목표·동기·기술수준·좌절점·성공기준). 비전문가 이해 요구(§2.1) 반영
- [x] **G-3**: `stories.md` 생성 — INVEST 스토리
  - [x] G-3.1: U-4 PolicyCore 스토리 (S-U4-1~4 — US-5 관련, FR-4.x)
  - [x] G-3.2: U-5 AuditTrail 스토리 (S-U5-1~4 — US-4 관련, FR-5.x, FR-0.x)
  - [x] G-3.3: U-3 SecretGuard 스토리 (S-U3-1~6 — US-3, FR-3.x, D-3, S/B 코퍼스)
  - [x] G-3.4: U-2 AgentCage 스토리 (S-U2-1~5 — US-2, FR-2.x, D-2)
  - [x] G-3.5: U-1 WebIsolate 스토리 (S-U1-1~6 — US-1, FR-1.x, D-1)
  - [x] G-3.6: 공통 실행 경험 스토리 (S-C-1~4 — US-6, FR-0.x, T-BOOT)
- [x] **G-4**: 각 스토리에 acceptance criteria(Given/When/Then) + 정상/거부/장애 경로 + 검증 ID(D/T/S/B) 매핑
- [x] **G-5**: 각 스토리에 MVP/유예 태그 부여
- [x] **G-6**: P1/P2 스토리 처리 — 유예 스텁 섹션(S-P1-*, S-P2-*)
- [x] **G-7**: 페르소나 ↔ 스토리 매핑표 작성 (personas.md + stories.md 하단)
- [x] **G-8**: INVEST 준수 셀프체크 (stories.md 하단)
- [x] **G-9**: `aidlc-state.md` 갱신, audit.md 기록, 완료 메시지 + 승인 게이트 제시

---

## E. 제약 준수 확인 (작성 중 상시 적용)
- C-AIDLC-1: 기준안의 US·페르소나를 입력 재사용, 무의미한 재선택 금지.
- C-AIDLC-2: 시제품 범위를 이유로 P0 완화 금지 — MVP 태그는 "우선순위"일 뿐 P0 보안 집행 축소가 아님.
- C-SCOPE-1: 안전한 차단을 경고/통과로 바꾸는 acceptance criteria 금지. 거부·fail-closed 경로를 1급 수용 기준으로 유지.
- 이 단계는 방법론·구조만 다룸 — 기술 구현·스프린트 계획·타임라인 미포함(Step 11).
