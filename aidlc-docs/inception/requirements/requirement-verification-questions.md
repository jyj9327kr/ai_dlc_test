# 요구사항 확인 질문 (Requirements Verification)

AEGIS 요구사항(`requirements/requirements.md` v4.0)과 제약(`requirements/constraints.md` v4.0)은 매우 상세하며 대부분의 제품 기본값(웹 미분류=격리, 위험 액션=차단, 시크릿=요청 차단, ML-DSA-65 서명, 지원 제공자 전용 프록시, 최소 통합 UI, 로컬 추가 감사 기록 등)을 이미 결정했습니다. 이 결정들은 반복해서 묻지 않습니다. (근거: requirements.md §10.1, constraints.md C-AIDLC-2)

아래는 문서로 확정되지 않았고 **실제 사람의 결정이 필요한 항목**입니다. 각 질문의 `[Answer]:` 뒤에 알파벳을 적어 주세요. 해당 옵션이 없으면 마지막 `X) Other`를 고르고 설명을 적어 주세요. 모두 작성하신 후 "완료" 또는 "done"이라고 알려 주세요.

각 질문에는 이 프로젝트 맥락에 맞는 **권장 답변**을 표시해 두었습니다.

---

## Question 1: Security Extensions (보안 확장)
이 프로젝트에 Security 확장 규칙을 강제 적용할까요?

AEGIS는 3개 신뢰 경계를 통제하는 보안 제품이며, P0 자체가 다수의 보안 집행 요구(FR-1~FR-5, C-SEC/C-PQC/C-PROXY 계열)를 포함합니다. Security Baseline을 켜면 요구·설계·코드 단계에서 보안 규칙이 차단성 제약(blocking constraint)으로 적용됩니다.

A) 예 — 모든 SECURITY 규칙을 차단성 제약으로 강제한다 (production 성격의 보안 제품에 권장) [권장]

B) 아니오 — 모든 SECURITY 규칙을 생략한다 (PoC·프로토타입·실험 프로젝트에 적합)

X) Other (아래 [Answer]: 뒤에 설명해 주세요)

[Answer]: A

---

## Question 2: Resiliency Extensions (복원력 확장)
이 프로젝트에 Resiliency Baseline을 적용할까요?

이 확장은 AWS Well-Architected(신뢰성 원칙) 기반의 **설계 시점 방향성 모범사례**(내결함성, 고가용성, 관측성, 복구성 15개 실천 영역)를 요구·설계·코드에 반영하도록 안내합니다. 다만 AEGIS의 P0 범위는 **단일 장비·단일 사용자·단일 세션**을 명시적 기준으로 하며(requirements.md §2.2, constraints.md C-SCOPE-2), 고가용성·재해복구는 §3에서 **명시적 제외** 항목입니다. 선택하지 않은 운영 확장으로 HA/DR 범위를 자동 추가하지 않습니다(constraints.md C-AIDLC-2).

A) 아니오 — Resiliency Baseline을 생략한다 (단일 장비 시제품 범위, 빠른 반복 우선 — 현재 P0 범위에 부합) [권장]

B) 예 — Resiliency Baseline을 설계 시점 방향성 지침으로 적용한다 (비즈니스 크리티컬 워크로드용, go-live 전 검증·강화 전제)

X) Other (아래 [Answer]: 뒤에 설명해 주세요)

[Answer]: A

---

## Question 3: Property-Based Testing Extension (속성 기반 테스트 확장)
이 프로젝트에 Property-Based Testing(PBT) 규칙을 강제 적용할까요?

AEGIS에는 시크릿 탐지(정규식·엔트로피·JSON escape 복원·청크 병합), 정책 서명 검증(bytes 무결성), 이벤트 직렬화/evidence_hash, URL 정규화·SSRF 판정 등 **순수 로직·데이터 변환·직렬화 왕복**이 다수 존재하여 PBT의 이점이 큽니다.

A) 예 — 모든 PBT 규칙을 차단성 제약으로 강제한다 (비즈니스 로직·데이터 변환·직렬화·상태 컴포넌트가 있는 프로젝트에 권장) [권장]

B) 부분 — 순수 함수와 직렬화 왕복에만 PBT 규칙을 강제한다 (알고리즘 복잡도가 제한적인 프로젝트에 적합)

C) 아니오 — 모든 PBT 규칙을 생략한다 (단순 CRUD·UI 전용·얇은 통합 계층에 적합)

X) Other (아래 [Answer]: 뒤에 설명해 주세요)

[Answer]: B

---

## Question 4: 실행·검증 기준 환경 (Execution / Verification Environment)
constraints.md C-SCOPE-2는 기준 서버를 **Ubuntu 24.04 Linux VM**으로 정하고, **WSL2는 실제 OpenShell 격리 시험을 통과한 경우에만** 지원 조합으로 기록하도록 규정합니다. 그런데 현재 개발 장비는 **WSL2**(Linux 6.18 microsoft-standard-WSL2)입니다. OpenShell(NVIDIA)·Landlock·컨테이너 격리·liboqs(ML-DSA-65)의 실동작(V-1, V-2)은 커널·런타임 지원에 민감합니다. 어느 환경을 이번 개발·검증의 기준으로 삼을까요?

A) Ubuntu 24.04 Linux VM을 기준 환경으로 준비해 그 위에서 개발·검증한다 (constraints.md 기본값, V-1/V-2 위험 최소화) [권장]

B) 현재 WSL2에서 먼저 진행하되, Inception 초기에 V-1(OpenShell/Landlock/컨테이너)·V-2(liboqs ML-DSA-65) smoke test로 실제 격리 가능 여부를 확인하고 실패 시 Ubuntu VM으로 전환한다

C) 실행 환경은 아직 확정하지 않고, 코드·설계는 환경 독립적으로 진행하며 통합 검증 시점에 결정한다

X) Other (아래 [Answer]: 뒤에 설명해 주세요)

[Answer]: B

---

## Question 5: 이번 기준안(requirements/constraints)의 처리
`requirements/requirements.md`와 `requirements/constraints.md`는 "개발 착수용 기준안"이며 문서 자체로는 사람의 승인이 아닙니다(constraints.md C-AIDLC-1, C-CHANGE-1). 이 기준안을 이번 AI-DLC Inception의 승인된 요구사항 입력으로 채택할까요?

A) 예 — 두 문서를 그대로 승인된 요구 입력으로 채택하고, `aidlc-docs/inception/requirements/`에 반영한다 [권장]

B) 예, 단 일부 수정 후 채택한다 (아래 [Answer]: 뒤에 수정할 항목을 적어 주세요)

C) 아니오 — 채택 전 추가 논의가 필요하다

X) Other (아래 [Answer]: 뒤에 설명해 주세요)

[Answer]: A
