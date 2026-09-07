# PolicyCore (U-4) — NFR Requirements

유닛: UOW-1 PolicyCore | 단계: NFR Requirements | 작성일: 2026-09-07
결정: Q1~Q6 = A. 집행: Security(Full), PBT(Partial, blocking), C-PQC-1, C-SCOPE-1.

## 1. 적용 NFR (필수)

### NFR-PC-1 — 암호 정확성 (NFR-3, S-U4-2) [Security, blocking]
- ML-DSA-65(NIST category 3) 서명을 **실제 PQC 라이브러리**로 검증한다.
- **1비트 변조**(정책 bytes 또는 서명값) 시 반드시 검증 실패.
- 서명 메시지 = `ASCII("AEGIS-OPENSHELL-POLICY-v1") + 0x00 + policy.yaml raw`(C-PQC-1).
- **공개키 전용**: 실행 환경·저장소에 개인키 부재. HMAC/대칭키 대체·mock 성공·우회 금지.
- **검증**: T-SIGN, **V-2**(liboqs ML-DSA-65) 통과 전 관련 P0 완료 표시 금지.

### NFR-PC-2 — 원문·키 비노출 (NFR-4, T-PRIVACY 전제) [Security]
- `Judgment`·감사 경로에 정책 원문·개인키·키 원문·비밀을 노출하지 않는다. `policy_digest`·`pubkey_id`·`reason_code`만.
- 예외·로그 메시지에 원문·키를 담지 않는다(비민감 메타만).

### NFR-PC-3 — 순환 없음·독립성 (NFR-6)
- `aegis.policy`는 `contracts`에만 의존, 다른 방어 UOW를 import하지 않는다(단방향).
- PolicyCore 단독으로 테스트 가능(순수 판정 함수, 부수효과 없음).

### NFR-PC-4 — Fail-Closed (NFR-8/9, C-SCOPE-1) [Security]
- 검증 결과를 확신할 수 없으면 거부(`verdict=ERROR`/`BLOCK`). 성공 추정·경고/통과 완화 금지.
- 라이브러리 부재·예외는 성공으로 강등하지 않고 `COMMON_INTERNAL_ERROR`로 신호.

### NFR-PC-5 — 결정성 (판정 재현성)
- 동일 입력(bytes·서명·keystore·시각) → 동일 `Judgment`. 비결정 요소 배제.

## 2. Deferred / N/A

| NFR 영역 | 상태 | 근거 |
|---|---|---|
| 성능(검증 지연·처리량, NFR-1/2) | `[Deferred:perf-NFR]` | Q3=A. MVP는 동작만 확인, 수치 목표 미설정 |
| 확장성(부하·수평 확장) | N/A | 단일 사용자·단일 장비 |
| 가용성(HA·failover) | N/A | 단일 장비. 단, fail-closed는 필수(NFR-PC-4) |
| 사용성 | N/A | 라이브러리(대면 UI 없음). 사유 메시지는 계약 밖 표시계층 |
| Resiliency 확장 | N/A(OFF) | 세션 설정 Resiliency=off |

## 3. PBT 강제 대상 (PBT Partial, blocking, Q6=A)
- 서명 왕복: 유효 키쌍 서명 → `ALLOW`/`POLICY_OK`.
- 1비트 변조: bytes/서명 임의 1비트 → `BLOCK`/`POLICY_SIGNATURE_INVALID`.
- 도메인 분리: `0x00` 누락·도메인 문자열 변경 → 검증 실패.
- 키 상태: 폐기/만료/미등록 → `BLOCK`/`POLICY_UNTRUSTED_KEY`.
- 결정성: 동일 입력 반복 → 동일 Judgment.
- **합성/절대 무효 키만** 사용(실제 키·개인키 반입 금지).

## 4. 보안 집행 지점 요약
| 지점 | 규칙 | 확인 |
|---|---|---|
| 서명 검증 | 실제 ML-DSA-65, 1비트 변조 실패 | NFR-PC-1, T-SIGN, V-2 |
| 키 관리 | 공개키 전용, 폐기 즉시 효력 | NFR-PC-1, T-KEY |
| 인증 우선 | 서명 성공 후에만 파싱 | R3(FD), NFR-PC-1 |
| 비노출 | digest/식별자만, 원문·키 미노출 | NFR-PC-2 |
| fail-closed | 불확실 시 거부 | NFR-PC-4 |
