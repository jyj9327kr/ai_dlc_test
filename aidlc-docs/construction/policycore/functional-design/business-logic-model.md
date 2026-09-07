# PolicyCore (U-4) — Business Logic Model

유닛: UOW-1 PolicyCore | 단계: Functional Design | 작성일: 2026-09-07
결정: Q2=A(인증 우선), Q4=A(우선순위 단락), Q5=A(순수 함수), Q6=A(버전 fail-closed)

## 1. 공개 판정 함수 (Q5=A)

```
verify_policy(policy_bytes, signature, keystore, now, supported_versions) -> Judgment
```

- **입력**: `policy_bytes: bytes`(원본), `signature: DetachedSignature{pubkey_id, signature}`, `keystore: KeyStore`, `now: UTC`(유효기간 판정), `supported_versions: set[int]`.
- **출력**: contracts `Judgment`. 부수효과 없음.
- **성질**: 결정적(동일 입력·동일 `now`·동일 keystore → 동일 Judgment).

## 2. 판정 플로우 (인증 우선, 첫 실패 단락)

```
1) policy_digest = sha256(policy_bytes)            # 감사·소비자에 항상 제공(성공/실패 무관)

2) 신뢰키 조회·상태 (R4)                            # 순위 1
   key = keystore.lookup(signature.pubkey_id)
   if key is None or key.status != ACTIVE
        or not (key.not_before <= now <= key.not_after):
       return Judgment(BLOCK, POLICY_UNTRUSTED_KEY, policy_digest, pubkey_id=signature.pubkey_id)

3) 서명 메시지 구성 (R1)                             # C-PQC-1
   msg = b"AEGIS-OPENSHELL-POLICY-v1" + b"\x00" + policy_bytes

4) ML-DSA-65 서명 검증 (R2)                          # 순위 2, [Security]
   if not mldsa65_verify(key.public_key, msg, signature.signature):
       return Judgment(BLOCK, POLICY_SIGNATURE_INVALID, policy_digest, pubkey_id)
   # 여기부터 내용은 "인증됨"

5) 파싱 (인증 성공 후에만, R3)
   doc = parse(policy_bytes)          # 파싱 실패 → POLICY_SCHEMA_INVALID

6) 스키마 분리 검증 (R5)                              # 순위 3
   validate_common(doc.common); validate_policy(doc.policy)
   if invalid: return Judgment(BLOCK, POLICY_SCHEMA_INVALID, policy_digest, pubkey_id)

7) 버전 지원 (R6)                                    # 순위 4
   if doc.schema_version not in supported_versions:
       return Judgment(BLOCK, POLICY_VERSION_UNSUPPORTED, policy_digest, pubkey_id)

8) 성공
   return Judgment(ALLOW, POLICY_OK, policy_digest, pubkey_id,
                   policy_id=doc.policy_id, policy_version=doc.policy_version)
```

**Fail-closed 래핑 (R7)**: 위 전 과정을 감싸, 예기치 못한 내부 오류(라이브러리 부재·예외)는
`Judgment(ERROR, COMMON_INTERNAL_ERROR, policy_digest?, pubkey_id?)`로 반환한다. 예외를 성공으로
강등하지 않는다.

> 주의: 스텝 5(파싱)를 스텝 4(서명 검증) **이후**에 두는 것이 R3(authenticate-before-parse)의 핵심.
> 미인증 입력이 파서에 도달하지 않는다.

## 3. 오류 → 판정 매핑 (요약)

| 상황 | verdict | reason_code |
|---|---|---|
| 미등록/폐기/만료 키 | BLOCK | POLICY_UNTRUSTED_KEY |
| 서명 검증 실패(1비트 변조 포함) | BLOCK | POLICY_SIGNATURE_INVALID |
| 파싱/스키마 오류(인증 후) | BLOCK | POLICY_SCHEMA_INVALID |
| 미지원 schema_version | BLOCK | POLICY_VERSION_UNSUPPORTED |
| 전부 통과 | ALLOW | POLICY_OK |
| 내부 검증 불가 | ERROR | COMMON_INTERNAL_ERROR |

## 4. 소비자 통합 지점

- **U-2 AgentCage**: 실행 전 `verify_policy` 호출 → `ALLOW`+`POLICY_OK`일 때만 진행. TOCTOU는 U-2가 `Judgment.policy_digest`를 실행 시점 정책과 재대조(검증본=적용본, FR-2.2). PolicyCore는 digest 제공까지.
- **U-3 SecretGuard / U-1 WebIsolate**: 정책 갱신·부팅 시 신뢰성 확인에 사용. `ALLOW`가 아니면 이전 신뢰 정책 유지 또는 fail-closed(보호 유지).
- 세 소비자 모두 `BLOCK`/`ERROR`를 **보호 동작 차단**으로 해석(경고·통과 없음, C-SCOPE-1).
- **감사**: 소비자가 `Judgment`(+ 자신의 unit·workflow_id·evidence_hash)를 U-5에 기록. PolicyCore 자신은 기록하지 않음(R9).

## 5. 키 교체·폐기 운영 모델 (FR-4.3, S-U4-3)

- 교체: 새 `TrustedKey(ACTIVE)`를 KeyStore에 추가(구 키도 유효기간 동안 ACTIVE 유지 → 무중단 교체).
- 폐기: 대상 키 `status=REVOKED` 전이(즉시). 이후 해당 키 서명 정책은 순위 1에서 거부.
- 개인키 미보관(공개키만). 서명 생성(개인키 사용)은 AEGIS 실행 범위 밖(오프라인 관리).

## 6. PBT·검증 대상 (PBT partial, T-SIGN/T-KEY)

- **PBT-서명 왕복**: 유효 키쌍으로 서명한 임의 policy_bytes → `verify_policy` = ALLOW/POLICY_OK.
- **PBT-1비트 변조**: policy_bytes 또는 signature의 임의 1비트 뒤집기 → 반드시 BLOCK/POLICY_SIGNATURE_INVALID (R2.2).
- **PBT-도메인 분리**: `0x00` 누락·문자열 변경 시 검증 실패(R1.2).
- **PBT-키 상태**: REVOKED/만료/미등록 키 → POLICY_UNTRUSTED_KEY (임의 시각·상태 조합).
- **경계값**: 미지원 버전 집합 → POLICY_VERSION_UNSUPPORTED. 빈 bytes·과대 bytes 처리.
- **결정성**: 동일 입력 반복 → 동일 Judgment.
- 모든 테스트는 **합성/절대 무효 키만** 사용(실제 키·개인키 저장소·문서 반입 금지). V-2(liboqs) 통과 전 관련 P0 완료 표시 금지.
