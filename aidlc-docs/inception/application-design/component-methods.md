# AEGIS — Component Methods (고수준 시그니처)

작성일: 2026-09-07 | 단계: INCEPTION → Application Design
메서드 시그니처·입출력·고수준 목적만 정의한다. **상세 비즈니스 규칙·알고리즘·경계 조건은 Functional Design(per-unit, CONSTRUCTION)에서 확정한다.** 시그니처는 언어 무관 의사표기(Python 타입 힌트 스타일)이며 최종 시그니처는 코드 생성 단계에서 확정.

---

## C0. contracts (`src/aegis/contracts/`)
| 메서드 | 시그니처(고수준) | 목적 |
|---|---|---|
| new_workflow_id | `() -> WorkflowId` | 실행 단위 식별자 생성(FR-0.3) |
| new_event_id | `() -> EventId` | 이벤트 유일 식별자 |
| make_verdict | `(verdict: Verdict, reason: ReasonCode, location?: SafeLocation, action?: str) -> Judgment` | 공통 판정 생성(Q4=A) |
| make_audit_event | `(workflow_id, unit, judgment, target?, ...) -> AuditEvent` | 원문 없는 이벤트 구성(FR-5.2) |
| to_jsonl / from_jsonl | `(AuditEvent) -> str` / `(str) -> AuditEvent` | 직렬화 왕복(**PBT 대상**) |
| evidence_hash | `(AuditEvent) -> Hash` | 안전 메타데이터 해시(FR-5.2, **PBT**) |

## C1. U-4 PolicyCore (`src/aegis/policy/`)
| 메서드 | 시그니처(고수준) | 목적 |
|---|---|---|
| load_common_config | `(path) -> Config` | 공통 설정 schema_version=1 검증 로드(FR-4.1); 실패 시 거부 |
| load_policy | `(path) -> PolicyDoc` | OpenShell policy version=1 스키마 검증(FR-4.1) |
| snapshot | `(path) -> PolicySnapshot{raw_bytes, digest}` | 검증 대상 원본 bytes 고정(TOCTOU, FR-2.2) |
| verify_signature | `(snapshot, sig, trust_store) -> VerifyResult{ok, pubkey_id, reason_code}` | ML-DSA-65 원본 bytes 검증(FR-4.2). 메시지=`"AEGIS-OPENSHELL-POLICY-v1"+0x00+bytes` |
| load_trust_store | `(config) -> TrustStore` | 신뢰키(pubkey_id) 로드, 폐기 반영(FR-4.3) |
| judgment | `(verify_result, policy_doc) -> Judgment` | 공통 판정(policy_id/version/digest/rule_id/verdict/reason_code)(FR-4.4) |

**주의**: 서명은 오프라인 도구(실행 환경 밖). 실행 환경엔 공개키만. HMAC 대체·mock 검증 성공 금지.

## C2. U-5 AuditTrail (`src/aegis/audit/`)
| 메서드 | 시그니처(고수준) | 목적 |
|---|---|---|
| AuditClient.emit | `(event: AuditEvent) -> Ack | AuditUnavailable` | loopback로 단일 writer에 송신(Q2=A) |
| Writer.run | `(socket, jsonl_path) -> None` | 단일 writer 프로세스: 수신→순차 append(FR-5.1) |
| Writer.health | `() -> AuditHealth{writable, running}` | fail-closed 판단 근거(FR-5.4) |
| query | `(filter{workflow_id?, unit?, verdict?}) -> list[AuditEvent]` | 조회·필터(FR-5.3) |
| verify_hash | `(event) -> bool` | evidence_hash 재계산 일치(NFR-9) |

**동시성**: 여러 Unit emit → writer가 직렬화. event_id 유일·행 무손상(**PBT**).

## C3. U-3 SecretGuard (`src/aegis/guard/`)
| 메서드 | 시그니처(고수준) | 목적 |
|---|---|---|
| addon.request | `(flow) -> None` | mitmproxy hook: 목적지·크기·본문 검사 후 통과/차단(FR-3.1/3.6) |
| normalize | `(raw_body, headers) -> NormalizedRequest` | JSON escape 복원·청크 병합·헤더 추출(FR-3.2, **PBT**) |
| detect | `(normalized) -> DetectResult{hits: list[rule_id, SafeLocation]}` | 정규식+문맥 엔트로피(LLM 없음)(FR-3.2, **PBT**) |
| decide | `(detect_result) -> Judgment` | 탐지 시 BLOCK, 아니면 ALLOW(FR-3.3/3.4) |
| block_response | `(judgment, event_id) -> HttpResponse(403)` | `AEGIS_SECRET_BLOCKED`·rule_id·안전 위치(FR-3.3) |
| reject_uninspectable | `(reason) -> HttpResponse(413|415|400|503)` | 검사 불가 명시 거부(FR-3.5) |

## C4. U-2 AgentCage (`src/aegis/cage/`)
| 메서드 | 시그니처(고수준) | 목적 |
|---|---|---|
| cli_run | `(policy_path, command, argv) -> ExitCode` | `aegis-cage run` 진입점 |
| verify_then_run | `(policy_path, command) -> RunResult` | U-4 검증 통과 후에만 OpenShell 호출(FR-2.1) |
| build_sandbox_spec | `(policy_snapshot) -> SandboxSpec` | 워크스페이스·통신 경계(FR-2.3) |
| invoke_openshell | `(spec, command) -> ProcResult` | 실제 OpenShell 실행(검증 실패 시 미호출) |
| record | `(judgment, digest, pubkey_id, exit) -> None` | 시작·거부·종료 기록, 인자·환경 미저장(FR-2.4) |
| on_policy_change | `(running) -> None` | 실행 중 고정, 재적용 시 종료·재검증(FR-2.5) |

**선행**: V-1 통과 전 D-2 관련 P0 완료 표시 금지.

## C5. U-1 WebIsolate — 확장(`apps/extension/`) + RBI 서버(`src/aegis/web/`)
| 메서드 | 시그니처(고수준) | 목적 |
|---|---|---|
| classify_navigation | `(url, policy) -> {DIRECT|ISOLATE|BLOCK}` | 탐색 판정, 정책 부재 시 직접 접속 안 함(FR-1.1, **PBT**: URL 정규화) |
| enforce_pre_nav (DNR) | `(request) -> Allow|Redirect(viewer)` | 로컬 선실행 방지(FR-1.1) |
| RBIServer.open_session | `(url, auth_token) -> SessionId` | 격리 세션 생성·인증(FR-1.4) |
| RBIServer.relay | `(session, input_event) -> PixelFrame|ControlMsg` | 픽셀·허용 입력 릴레이, HTML 미전달(FR-1.2) |
| block_risky_action | `(action) -> Judgment(RISKY_ACTION_BLOCKED)` | 다운로드/업로드/클립보드/password/mailto 차단(FR-1.3) |
| ssrf_guard | `(target) -> Allow|Block(SSRF_BLOCKED)` | 내부망·메타데이터·비HTTP(S) 거부(FR-1.6, **PBT**) |
| close_session | `(session, reason) -> None` | 만료·종료·데이터 폐기(FR-1.4/1.5) |

## 제어 서버 (`src/aegis/` 제어 평면, FastAPI, Q5=A)
| 메서드 | 시그니처(고수준) | 목적 |
|---|---|---|
| status | `() -> {unit: ComponentState}` | 준비/보호활성/차단/사용안함(FR-0.2), 3초 내 반영 |
| events | `(filter) -> list[AuditEvent]` | U-5 조회 프록시(FR-5.3) |
| doctor / up / down / demo / test | `(...) -> ExitCode` | 단일 진입점(`scripts/aegis`)(FR-0.1) |

**보안**: 모든 loopback 엔드포인트는 토큰·Origin·Host 검증(C-SEC, T-TRANSPORT). 목적지·오류를 HTML로 해석 금지.
