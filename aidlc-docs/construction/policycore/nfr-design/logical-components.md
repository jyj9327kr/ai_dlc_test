# PolicyCore (U-4) — Logical Components

유닛: UOW-1 PolicyCore (`src/aegis/policy/`) | 단계: NFR Design | 작성일: 2026-09-07
결정: Q4=A(책임 분리 모듈, 순환 없음). 외부 의존: `aegis.contracts`만 + liboqs/PyYAML(어댑터·스키마 모듈 내부).

## 1. 모듈 구성

| 모듈 | 책임 | 외부 의존 |
|---|---|---|
| `verifier.py` | ML-DSA-65 검증 어댑터(P1). `verify(pub, msg, sig)->bool`, `build_signing_message(raw)->bytes`(C-PQC-1) | `oqs` |
| `keystore.py` | `config/trusted-keys/` 읽기 전용 로드 → 불변 `KeyStore`; `lookup(pubkey_id)->TrustedKey|None`; 상태·유효기간 판정(now 주입, P3) | `PyYAML`(매니페스트) |
| `schema.py` | `safe_load`+크기 상한 파싱, 공통/정책 섹션 **분리 검증**(P4), `PolicyDocument` 구성 | `PyYAML` |
| `evaluator.py` | 우선순위 판정 오케스트레이션(FD business-logic-model §2) → contracts `Judgment`. fail-closed 래퍼(P2) | `aegis.contracts` |
| `errors.py` | PolicyCore 내부 예외(검증 불가 등). 메시지 비민감 | — |
| `__init__.py` | 공개 API: `verify_policy`, `load_keystore`, 주요 타입 re-export | — |

## 2. 모듈 의존 그래프 (순환 없음, NFR-PC-3)

```
__init__  →  evaluator  →  verifier   → (oqs)
                     │  →  keystore   → (PyYAML)
                     │  →  schema     → (PyYAML)
                     └  →  errors
evaluator, keystore, schema, verifier  →  aegis.contracts   (하위, 단방향)
```
- `aegis.contracts`로 향하는 간선만 존재(역방향 없음). PolicyCore는 다른 방어 UOW(guard/cage/web)를 import하지 않는다.
- liboqs/PyYAML 의존은 `verifier`/`keystore`/`schema` **내부에 격리**(`evaluator`는 라이브러리 비의존).

## 3. 공개 API (기술 스케치, 확정은 Code Gen)

```
load_keystore(dir="config/trusted-keys") -> KeyStore        # 읽기 전용, 로드 실패→fail-closed
verify_policy(policy_bytes, signature, keystore, now,
              supported_versions) -> Judgment               # 순수, fail-closed 래퍼
```
- `signature`: `DetachedSignature{pubkey_id, signature}`.
- 반환: contracts `Judgment` (§FD domain-entities §2.7 매핑).

## 4. contracts 사용 지점
- `evaluator`가 `Verdict`·`ReasonCode.POLICY_*`/`COMMON_INTERNAL_ERROR`·`Judgment`·`PolicySnapshot`(digest) 사용.
- `Judgment` 필드만으로 결과 표현 — 원문·키 비노출(P5).

## 5. C-PQC-1 서명 메시지 구성 위치
- `verifier.build_signing_message(raw)` 단일 함수에 구성 규칙 집중: `b"AEGIS-OPENSHELL-POLICY-v1" + b"\x00" + raw`. `evaluator`는 이 함수만 호출(규칙 중복·표류 방지).

## 6. 테스트 배치 (`tests/policy/`)
- `test_verifier.py`(실검증·1비트 변조·도메인 분리, PBT), `test_keystore.py`(로드·폐기·만료·미등록, now 주입), `test_schema.py`(분리 검증·크기 상한·safe_load), `test_evaluator.py`(우선순위 단락·fail-closed·결정성, PBT).
- **합성/절대 무효 키만**. V-2(liboqs) 통과 전 관련 P0 완료 표시 금지.
- 픽스처: `tests/fixtures/`(합성 키쌍·정책 샘플), 개인키·실제 키 반입 금지.
