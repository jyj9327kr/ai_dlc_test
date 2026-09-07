# PolicyCore (U-4) — Business Rules

유닛: UOW-1 PolicyCore | 단계: Functional Design | 작성일: 2026-09-07
집행: Security(Full, blocking), C-PQC-1, C-SCOPE-1. [Security] 표시는 완화 불가 하드 제약.

## R1. 서명 메시지 구성 (C-PQC-1) [Security]
- R1.1 서명 검증 메시지 = `ASCII("AEGIS-OPENSHELL-POLICY-v1")` **+ 단일 바이트 `0x00`** + `PolicyBytes.raw`.
- R1.2 도메인 분리 바이트 `0x00`은 반드시 포함(다른 용도 서명과의 혼용·교차 재사용 차단).
- R1.3 메시지는 검증 시점에 원본 바이트열로부터 결정적으로 재구성한다. 정규화·재직렬화·트림 금지(bytes 그대로).

## R2. 서명 검증 무결성 (FR-4.2, NFR-3) [Security]
- R2.1 검증은 **ML-DSA-65(NIST category 3)** 공개키 알고리즘으로만 성립한다.
- R2.2 **1비트라도** 원본 bytes 또는 서명값이 변조되면 검증은 실패해야 한다.
- R2.3 **공개키 전용**: 실행 환경에 개인키가 없어야 하며, 개인키를 요구하는 경로가 없어야 한다.
- R2.4 **금지**: HMAC·대칭키 대체, mock/스텁 성공, 예외를 성공으로 간주, 검증 결과 무시. 검증 라이브러리 부재·오류 시 성공으로 강등하지 않는다(→ R7 fail-closed).

## R3. 인증 우선 순서 (Q2=A) [Security]
- R3.1 신뢰키 조회·서명 검증을 **먼저** 수행한다.
- R3.2 파싱·스키마 검증은 **서명 검증 성공 이후에만** 수행한다(신뢰되지 않은 입력을 파서에 노출하지 않음).
- R3.3 서명 실패 시 정책 내용을 해석·적용하지 않는다.

## R4. 신뢰키 상태·폐기 (FR-4.3, Q3) [일부 Security]
- R4.1 서명자 `pubkey_id`가 KeyStore에 없으면 **미신뢰** → `POLICY_UNTRUSTED_KEY`.
- R4.2 키 상태가 `REVOKED`이거나 검증 시각이 유효기간 밖이면 **미신뢰**로 간주 → `POLICY_UNTRUSTED_KEY`. [Security] 폐기는 즉시 효력.
- R4.3 다중 `ACTIVE` 키 허용(교체 중첩기): 신·구 키로 서명된 정책 모두 유효기간·상태 조건 충족 시 신뢰.
- R4.4 키 교체·폐기는 KeyStore 상태 전이로만 표현(코드 변경 불필요), 개인키는 저장소·실행 환경에 두지 않는다.

## R5. 스키마 분리 검증 (FR-4.1, Q1) 
- R5.1 `common` 섹션과 `policy` 섹션을 **분리**하여 각기 스키마 검증한다.
- R5.2 핵심 필드(`schema_version`, `policy_id`, `policy_version`, 섹션 구분, 규칙 식별자)의 존재·타입을 검증한다.
- R5.3 알려지지 않은 필드는 불투명 통과하되, 필수 필드 누락·타입 오류는 `POLICY_SCHEMA_INVALID`로 거부한다.

## R6. 버전 호환성 (FR-4.4, Q6) [Security-adjacent, fail-closed]
- R6.1 지원 `schema_version` 집합을 명시적으로 정의한다.
- R6.2 지원 집합 밖의 버전은 **부분 해석하지 않고** `POLICY_VERSION_UNSUPPORTED`로 거부한다(상위 호환 추정 금지).

## R7. Fail-Closed 판정 (FR-4.4, C-SCOPE-1) [Security]
- R7.1 검증의 어느 단계든 결과를 확신할 수 없으면 **거부**한다(성공 추정 금지).
- R7.2 내부 오류(라이브러리 부재·예기치 못한 예외 등)는 `verdict=ERROR`, `reason_code=COMMON_INTERNAL_ERROR`로 신호하며, 소비 유닛은 이를 보호 동작 차단으로 해석한다.
- R7.3 안전한 거부를 경고·통과로 완화하지 않는다.

## R8. 평가 우선순위·reason_code 매핑 (Q4=A, FR-4.4)
결정적 우선순위로 **첫 실패에서 단락**한다. Q2=A(인증 우선)와 정합:

| 순위 | 검사 | 실패 시 verdict | reason_code |
|---|---|---|---|
| 1 | 신뢰키 조회·상태·유효기간 (R4) | BLOCK | `POLICY_UNTRUSTED_KEY` |
| 2 | ML-DSA-65 서명 검증 (R2) | BLOCK | `POLICY_SIGNATURE_INVALID` |
| 3 | (파싱 후) 스키마 분리 검증 (R5) | BLOCK | `POLICY_SCHEMA_INVALID` |
| 4 | 버전 지원 여부 (R6) | BLOCK | `POLICY_VERSION_UNSUPPORTED` |
| — | 전부 통과 | ALLOW | `POLICY_OK` |
| — | 내부 오류 (R7) | ERROR | `COMMON_INTERNAL_ERROR` |

- R8.1 파싱은 순위 2 성공 후 수행하므로, 스키마·버전 오류는 인증된 정책에 대해서만 발생한다.
- R8.2 하나의 실패만 대표 reason_code로 보고(집계하지 않음) — 소비자·감사의 결정적 해석 보장.

## R9. 부수효과·인터페이스 (Q5=A)
- R9.1 PolicyCore는 **순수 판정**만 수행하고 감사 기록·상태 변경 등 부수효과를 갖지 않는다.
- R9.2 판정 결과는 contracts `Judgment`로 반환하며, 감사 기록은 호출자(U-2/U-3/U-1)가 수행한다.
- R9.3 예상된 검증 실패는 예외가 아니라 `Judgment`(BLOCK)로 신호한다(예외는 내부 오류에 한정, R7).
