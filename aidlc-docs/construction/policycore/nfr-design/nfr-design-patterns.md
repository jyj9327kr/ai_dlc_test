# PolicyCore (U-4) — NFR Design Patterns

유닛: UOW-1 PolicyCore | 단계: NFR Design | 작성일: 2026-09-07
결정: Q1~Q5 = A. 집행: Security(Full), C-PQC-1, C-SCOPE-1. [Security]는 완화 불가.

## P1 — Verifier 포트-어댑터 (라이브러리 격리) [Security] (Q1)
- **의도**: liboqs(`oqs`) 호출을 얇은 `verifier` 어댑터 **단일 지점**에 캡슐화. 판정 로직(`evaluator`)은 라이브러리에 직접 의존하지 않고 인터페이스로만 호출.
- **인터페이스**: `verify(public_key: bytes, message: bytes, signature: bytes) -> bool`.
- **불변**: 실제 ML-DSA-65 검증만 성립. mock/스텁 성공·HMAC 대체 금지. `oqs`/liboqs 부재·초기화 실패 시 어댑터는 예외를 던지고, 상위 fail-closed 래퍼(P2)가 `ERROR`로 사상(성공 강등 없음).
- **테스트 정책**: 어댑터 경계에서 **실제 검증**으로 테스트(합성/무효 키). 검증 성공을 가짜로 만들지 않는다. V-2 smoke가 환경 가용성 사전 진단.

## P2 — Fail-Closed 판정 래퍼 [Security] (Q2, NFR-PC-4)
- **의도**: 판정 진입점(`verify_policy`)을 감싸, 내부 예외·라이브러리 오류를 `Judgment(verdict=ERROR, reason_code=COMMON_INTERNAL_ERROR)`로 사상.
- **구분**: 예상된 검증 실패(미신뢰키·서명 무효·스키마·버전)는 예외가 아니라 `Judgment(verdict=BLOCK, POLICY_*)`. 예외는 **내부 오류에 한정**.
- **불변**: 어떤 예외도 성공(`ALLOW`)으로 강등되지 않는다. 결과 미확정 시 거부.

## P3 — 불변 KeyStore + 시각 주입 (결정성) (Q3, FR-4.3)
- **의도**: 부팅/정책 갱신 시 `config/trusted-keys/`를 **읽기 전용 로드**해 불변 KeyStore를 만든다. `lookup(pubkey_id)`은 순수.
- **결정성**: 폐기·만료 판정에 쓰는 시각을 판정 함수 인자(`now`)로 **주입**한다(전역 시계 직접 참조 금지) → 동일 입력·동일 now → 동일 Judgment(NFR-PC-5).
- **불변**: 로드 실패·형식 오류는 fail-closed(신뢰키 없음 → 모든 정책 `POLICY_UNTRUSTED_KEY`). 개인키 미보관.

## P4 — 인증-우선 파싱 강건화 (Q2 tech, R3) [Security]
- **의도**: 파싱은 **서명 검증 성공 이후에만**(authenticate-before-parse). `schema` 모듈이 `yaml.safe_load` + **입력 크기 상한**으로 파서 남용을 제한.
- **불변**: `safe_load`만 사용(임의 객체 생성 금지). 미인증 입력을 파서에 노출하지 않는다. 파싱·스키마 오류는 `POLICY_SCHEMA_INVALID`(인증된 정책에 대해서만 발생).

## P5 — 비노출 (NFR-PC-2) [Security]
- **의도**: 판정 결과·오류에 `policy_digest`·`pubkey_id`·`reason_code`만 노출. 정책 원문·키 원문·개인키를 `Judgment`·예외·로그에 담지 않는다.
- **불변**: contracts `Judgment`의 잠긴 필드만 사용(원문·비밀 필드 구조적 부재).

## 비적용/축소 패턴 (Q5)
| 영역 | 적용 | 근거 |
|---|---|---|
| Resilience | **fail-closed만** | 검증 재시도·서킷 브레이커는 무의미·위험(변조 입력 재시도해도 실패). 재시도/백오프 미도입 |
| Scalability | N/A | 단일 사용자·단일 장비 |
| Performance | `[Deferred:perf-NFR]` | 측정 훅 미추가, 동작만. **결과 캐시로 재검증 생략 금지**(C-SCOPE-1 — 보안 완화 위험) |
| Availability(HA) | N/A | 단일 장비. fail-closed로 대체 |

## 패턴 ↔ NFR 매핑
| 패턴 | NFR | 스토리 |
|---|---|---|
| P1 Verifier 어댑터 | NFR-PC-1 | S-U4-2 |
| P2 Fail-Closed 래퍼 | NFR-PC-4 | S-U4-1/3 |
| P3 불변 KeyStore | NFR-PC-5, FR-4.3 | S-U4-3 |
| P4 인증-우선 파싱 | NFR-PC-1 | S-U4-1 |
| P5 비노출 | NFR-PC-2 | S-U4-4 |
