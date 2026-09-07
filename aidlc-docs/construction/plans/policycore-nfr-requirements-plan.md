# NFR Requirements Plan — UOW-1 PolicyCore (U-4)

역할: NFR Requirements Lead | 페이즈: CONSTRUCTION → NFR Requirements | 유닛: UOW-1 PolicyCore (U-4) | 작성일: 2026-09-07
상태: ✅ 답변 완료 (Q1~Q6 = A, 사용자 '모두 권장대로') — 산출물 생성

## 유닛 컨텍스트
- **유닛**: UOW-1 PolicyCore (`src/aegis/policy/`), 신뢰 앵커. Functional Design 완료(순수 판정 `verify_policy`).
- **핵심 NFR 동인**: 암호 정확성(ML-DSA-65 실검증, NFR-3), 원문·키 비노출(NFR-4), 순환 없음(NFR-6), fail-closed(NFR-8/9). 성능·확장은 MVP에서 동작 확인만.
- **선행 검증**: **V-2**(liboqs ML-DSA-65) 통과 전 관련 P0 완료 표시 금지.
- **보안 불변**: 공개키 전용, HMAC/mock/우회 금지(C-PQC-1, C-SCOPE-1). contracts와 달리 PolicyCore는 **실제 PQC 라이브러리 의존이 불가피** — 단, 의존은 최소로.

## 설계 입력 (확정)
- functional-design/{domain-entities, business-rules, business-logic-model}.md, contracts(UOW-0), C-PQC-1, MVP 우선순위(성능 NFR-1/2 deferred).

---

## 컨텍스트 질문 (A/B/C + 기타, `[Answer]: A` 태그에 답변)

권장안은 각 질문의 A입니다. **Q1(암호 라이브러리)은 보안 임계 결정**이므로 옵션을 확인해 주세요.

### Q1. ML-DSA-65 서명 검증 라이브러리 (tech-stack, 보안 임계) [Security]

A) **liboqs (Open Quantum Safe) via `oqs-python` 바인딩** — V-2 게이트가 명시한 구현. NIST 표준 ML-DSA(Dilithium) 지원, 실제 PQC 검증. 검증 전용(공개키만) 사용. (권장)

B) 순수 파이썬 ML-DSA 구현(예: `dilithium-py`) — 네이티브 의존 없음, 단 성능·성숙도·유지보수 리스크.

C) 시스템 `liboqs` C 라이브러리 직접 FFI(ctypes/cffi) — 바인딩 없이 직접 연동.

X) 기타: 자유 기술

[Answer]: A

### Q2. 정책 파서 (policy.yaml) [Security]

A) **PyYAML `yaml.safe_load`** — 임의 객체 생성 없는 안전 로더. 파싱은 **서명 검증 성공 후에만**(R3 인증-우선)이라 노출 최소. (권장)

B) `ruamel.yaml`(round-trip) — 주석·순서 보존, 의존 증가.

C) 정책을 JSON으로 한정하고 stdlib `json` 사용(YAML 불가).

X) 기타: 자유 기술

[Answer]: A

### Q3. NFR 범위 — 성능·확장 목표 처리 (MVP 우선순위)

A) **정확성·보안 NFR만 필수**(NFR-3 암호정확성, NFR-4 비노출, NFR-6 순환없음, NFR-8/9 fail-closed). 검증 지연/처리량 수치 목표는 `[Deferred:perf-NFR]`(동작만 확인, 수치 미설정). (권장)

B) 검증 지연 상한(예: p95) 수치 목표를 지금 설정.

C) 성능 NFR 전면 제외(측정도 안 함).

X) 기타: 자유 기술

[Answer]: A

### Q4. 신뢰키 저장소 형식·위치 (FR-4.3, 공개키 전용)

A) **`config/trusted-keys/`에 공개키 자료 + 매니페스트**(`pubkey_id`, `status`, `not_before`/`not_after`)를 읽기 전용 로드. 개인키는 저장소·실행 환경에 부재. 매니페스트 형식은 Q2 파서 재사용. (권장)

B) 단일 매니페스트 파일에 공개키를 인라인(base64) + 메타.

C) 환경변수·외부 비밀 저장소에서 로드.

X) 기타: 자유 기술

[Answer]: A

### Q5. 의존성 정책 (PolicyCore)

A) **최소 3rd-party만 허용** — `oqs-python`(또는 Q1 선택) + `PyYAML`(또는 Q2 선택)로 한정. 그 외는 stdlib. 각 의존은 검증 목적에 필수임을 문서화. (권장)

B) 편의 라이브러리 추가 허용(예: pydantic로 스키마 검증).

C) contracts처럼 zero 3rd-party 강제(→ 순수 파이썬 PQC·수동 YAML 필요).

X) 기타: 자유 기술

[Answer]: A

### Q6. 속성 기반 테스트(PBT) 강제 대상 (PBT Partial, blocking)

A) **서명 검증 관련 PBT를 blocking으로 강제** — 서명 왕복(유효키→ALLOW), 1비트 변조→SIGNATURE_INVALID, 도메인분리 바이트 누락→실패, 키 상태(폐기/만료/미등록)→UNTRUSTED_KEY, 판정 결정성. 합성/절대 무효 키만. (권장)

B) PBT를 권고로만(비강제).

C) 예제 기반 단위 테스트만.

X) 기타: 자유 기술

[Answer]: A

---

## 생성 단계 (승인·답변 후 실행, 체크박스)

- [x] **Step NR-1 — NFR 요구사항 문서**: `nfr-requirements.md` — 적용 NFR(NFR-3/4/6/8/9)·근거, deferred/N/A 표(성능·확장·가용성), PBT 강제 대상, 보안 집행 지점(공개키 전용·1비트 변조·fail-closed).
- [x] **Step NR-2 — 기술 스택 결정 문서**: `tech-stack-decisions.md` — Q1~Q6 결정 확정, 각 의존의 필요성·검증 목적·버전 제약, 공개키 전용·개인키 부재 원칙, V-2 게이트 연계.

## 스토리 추적성
| Step | 스토리 | NFR | 검증 |
|---|---|---|---|
| NR-1 | S-U4-2 | NFR-3 | T-SIGN, V-2 |
| NR-1 | S-U4-4 | NFR-4/6 | T-PRIVACY(전제), T-FLOW |
| NR-1/2 | S-U4-1/3 | NFR-8/9 | T-KEY, fail-closed |

## 범위·제약 (상시)
- 보안 완화 없음(공개키 전용·서명 우회/mock/HMAC 금지). 의존 최소화. 실제 키·개인키를 저장소·문서·테스트에 반입 금지(합성/무효만).
- 문서는 `aidlc-docs/construction/policycore/nfr-requirements/`에만.
