# AEGIS — Unit of Work ↔ Story Map

작성일: 2026-09-07 | 단계: INCEPTION → Units Generation (Part 2) | 출처: stories.md, unit-of-work.md
목적: 모든 사용자 스토리가 정확히 하나의 UOW에 배정되었는지(전 스토리 배정) 확인. 경계를 걸치는 계약은 primary + shared로 표기.

## 1. P0 스토리 배정 (25개 고유)

### UOW-0 · Contracts
| 스토리 | 요약 | 페르소나 | FR | 검증 | 태그 |
|---|---|---|---|---|---|
| S-U4-4 ✅(정의) | 공통 판정 식별자 계약(verdict/reason_code/Judgment 타입) | P-B/전체 | FR-4.4 | T-FLOW | MVP:P0-core |
> S-U4-4는 계약 **정의**가 UOW-0 primary(✅ 2026-09-07 완료, `35 passed`), 산출(판정 생성)은 UOW-1 U-4가 소비(shared, 미구현).

### UOW-1 · PolicyCore (U-4) — 선행 V-2
| 스토리 | 요약 | 페르소나 | FR | 검증 | 태그 |
|---|---|---|---|---|---|
| S-U4-1 | 공통/정책 스키마 분리 검증 | P-B | FR-4.1 | T-SIGN | MVP:P0-core |
| S-U4-2 | ML-DSA-65 원본 bytes 서명/검증 | P-B | FR-4.2, NFR-3 | T-SIGN(+PBT) | MVP:P0-core |
| S-U4-3 | 신뢰키 교체·폐기 | P-B | FR-4.3 | T-KEY | MVP:P0-core |
| S-U4-4 (shared) | 판정 산출·공통 설정 갱신 | P-B | FR-4.4 | T-FLOW | MVP:P0-core |

### UOW-2 · AuditTrail & Control (U-5 + FR-0.x + 제어 서버/UI)
| 스토리 | 요약 | 페르소나 | FR | 검증 | 태그 |
|---|---|---|---|---|---|
| S-U5-1 | 단일 writer JSONL 순차 기록·조회 | P-A | FR-5.1 | T-AUDIT(+PBT) | MVP:P0-core |
| S-U5-2 | 원문 없는 evidence_hash | P-A | FR-5.2, NFR-4 | T-PRIVACY(+PBT) | MVP:P0-core |
| S-U5-3 | 통합 상태 UI(3카드·최근 이벤트) | P-A | FR-5.3 | T-UX | MVP:P0-core / 집계 Deferred:P1 |
| S-U5-4 | 필수 감사 실패 → fail-closed | P-A | FR-5.4, NFR-8/9 | T-AUDIT | MVP:P0-core |
| S-C-1 | 단일 실행 진입점(doctor/up/down/demo/test) | P-C | FR-0.1 | T-BOOT | MVP:P0-core |
| S-C-2 | 컴포넌트 상태 4구분 | P-C | FR-0.2 | T-UX | MVP:P0-core |
| S-C-3 | workflow_id 전파 | P-C | FR-0.3 | T-FLOW | MVP:P0-core |
| S-C-4 | README 기반 재현 | P-C | FR-0.1, NFR-7/11 | T-BOOT | MVP:P0-core / 사용성 측정 Deferred:usability-NFR |

### UOW-3 · SecretGuard (U-3) — 선행 V-3
| 스토리 | 요약 | 페르소나 | FR | 검증 | 태그 |
|---|---|---|---|---|---|
| S-U3-1 | 프록시 강제 경유 | P-A | FR-3.1 | T-PROXY, D-3 | MVP:P0-core |
| S-U3-2 | 요청 정규화 + 시크릿 8종 탐지 | P-A | FR-3.2, NFR-10 | S/B 코퍼스(+PBT) | MVP:P0-core |
| S-U3-3 | 탐지 시 전송 전 403 차단 | P-A | FR-3.3 | D-3 | MVP:P0-core |
| S-U3-4 | 정상 인증·콘텐츠 무손상 전달 | P-A | FR-3.4 | B-07, T-PROXY | MVP:P0-core |
| S-U3-5 | 검사 불가 요청 명시적 거부(413/415/400/503) | P-A | FR-3.5, NFR-13 | T-BODY | MVP:P0-core |
| S-U3-6 | TLS·지원 제공자 한정 | P-A | FR-3.6, NFR-5 | T-TRANSPORT | MVP:P0-core |

### UOW-4 · AgentCage (U-2) — 선행 V-1
| 스토리 | 요약 | 페르소나 | FR | 검증 | 태그 |
|---|---|---|---|---|---|
| S-U2-1 | 검증 후 실제 OpenShell 실행 | P-A | FR-2.1 | T-SIGN, D-2 | MVP:P0-core |
| S-U2-2 | 검증본=적용본(TOCTOU) | P-A | FR-2.2 | T-TOCTOU | MVP:P0-core |
| S-U2-3 | 최소 워크스페이스·통신 권한 | P-A | FR-2.3 | T-CAGE, D-2 | MVP:P0-core |
| S-U2-4 | 실행 시작·거부·종료 기록 | P-A | FR-2.4 | T-CAGE, T-PRIVACY | MVP:P0-core |
| S-U2-5 | 실행 중 정책 고정·재검증 | P-B | FR-2.5 | T-CAGE | MVP:P0-core |

### UOW-5 · WebIsolate (U-1) — 선행 V-4
| 스토리 | 요약 | 페르소나 | FR | 검증 | 태그 |
|---|---|---|---|---|---|
| S-U1-1 | 탐색 판정 직접/격리/차단 | P-A | FR-1.1 | T-WEB, D-1 | MVP:P0-core |
| S-U1-2 | 픽셀 중계·로컬 HTML 부재 | P-A | FR-1.2 | D-1 | MVP:P0-core / 화질·지연 Deferred:perf-NFR |
| S-U1-3 | 위험 액션 차단·한글 사유 | P-A | FR-1.3 | D-1, §3 | MVP:P0-core |
| S-U1-4 | 세션 인증·만료·데이터 폐기 | P-A | FR-1.4 | T-WEB, NFR-13 | MVP:P0-core |
| S-U1-5 | 격리 실패 시 안전한 재시도(우회 없음) | P-A | FR-1.5, NFR-8 | D-1 | MVP:P0-core |
| S-U1-6 | 원격 브라우저 SSRF 제한 | P-A | FR-1.6 | T-SSRF(+PBT) | MVP:P0-core |

## 2. 배정 완결성 확인
- 고유 P0 스토리 25개 = S-U4-1~4(4) + S-U5-1~4(4) + S-C-1~4(4) + S-U3-1~6(6) + S-U2-1~5(5) + S-U1-1~6(6) = **25** → 100% 배정, 미배정 0.
- 걸치는 계약: S-U4-4만 UOW-0(정의) + UOW-1(소비)로 공유. 나머지는 단일 UOW.
- 공통 실행(S-C-*)은 Q3=A에 따라 UOW-2에 귀속(별도 UOW 미신설).

## 3. P1/P2 스텁 배정 (Deferred — MVP 이후 상세화)
| ID | 요약 | 배정 UOW | 우선순위 |
|---|---|---|---|
| S-P1-1 | SHA-256 탐지 예외 목록 | UOW-3 | P1 |
| S-P1-2 | 서명된 정책 동적 갱신 | UOW-1 | P1 |
| S-P1-3 | gzip 텍스트 요청 지원 | UOW-3 | P1 |
| S-P1-4 | RBI 품질·지연 최적화 | UOW-5 | P1 |
| S-P1-5 | 집계 지표 대시보드 | UOW-2 | P1 |
| S-P2-1 | 요청 자동 redact | UOW-3 | P2 |
| S-P2-2 | 정책 편집 GUI | UOW-2 | P2 |
| S-P2-3 | 감사 해시체인·외부 서명 보관 | UOW-2 | P2 |
| S-P2-4 | WebRTC/다중 세션·브라우저 | UOW-5 | P2 |
| S-P2-5 | ML-DSA-87/자동 키 회전·HSM·KMS | UOW-1 | P2 |
| S-P2-6 | 외부 위협 피드 | UOW-3 | P2 |

## 4. 페르소나 커버리지
- **P-A 개발자**: UOW-2(상태·감사), UOW-3(전송), UOW-4(cage), UOW-5(웹) 전반.
- **P-B 정책 관리자**: UOW-0/1(계약·정책·키), UOW-4(S-U2-5 정책 고정).
- **P-C 검증 동료**: UOW-2(S-C-1~4 실행·재현), 전 UOW 재현 경로.
