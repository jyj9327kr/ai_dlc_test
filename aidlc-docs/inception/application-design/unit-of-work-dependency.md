# AEGIS — Unit of Work Dependencies

작성일: 2026-09-07 | 단계: INCEPTION → Units Generation (Part 2) | 출처: component-dependency.md, unit-of-work.md

## 1. UOW 의존 매트릭스 (행 → 열: 행이 열에 의존)
| ↓의존 \ 대상→ | UOW-0 contracts | UOW-1 Policy | UOW-2 Audit/Ctl | UOW-3 Guard | UOW-4 Cage | UOW-5 Web |
|---|---|---|---|---|---|---|
| **UOW-0 contracts** | — | | | | | |
| **UOW-1 PolicyCore** | ✅ | — | | | | |
| **UOW-2 AuditTrail/Control** | ✅ | | — | (상태) | (상태) | (상태) |
| **UOW-3 SecretGuard** | ✅ | ✅ | ✅ | — | | |
| **UOW-4 AgentCage** | ✅ | ✅ | ✅ | (경유) | — | |
| **UOW-5 WebIsolate** | ✅ | ✅ | ✅ | | | — |

- 방어 UOW(3/4/5) → UOW-1(검증), UOW-2(기록) **단방향**. UOW-1·UOW-2는 방어 UOW·서로를 코드 참조하지 않음. **순환 없음**(NFR-6).
- UOW-4 → UOW-3: 코드 의존이 아니라 **런타임 트래픽 경유**(보호 클라이언트가 프록시 통과, D-3/T-FLOW). 매트릭스의 (경유)는 참조 아님.
- UOW-2 제어 서버 → 각 서비스 (상태): loopback 상태 조회일 뿐 방어 UOW가 UOW-2에 역참조되지 않음.
- UOW-0은 모든 것의 최하위 공유 계약.

## 2. 빌드·구현 순서 (Q2=A) — 위상 정렬과 일치
```
UOW-0 contracts
   └─→ UOW-1 PolicyCore        (V-2)
          └─→ UOW-2 AuditTrail & Control
                 └─→ UOW-3 SecretGuard   (V-3)
                        └─→ UOW-4 AgentCage   (V-1)
                               └─→ UOW-5 WebIsolate  (V-4)
```
- 위 순서는 의존 위상 정렬을 만족(각 UOW는 자신이 의존하는 UOW 이후 착수).
- UOW-3/4/5는 모두 UOW-1·UOW-2에만 의존하므로 상호 순서는 자유 → **통합 검증 순서(D-3 → D-2 → D-1)** 를 채택해 문서 기본 순서(Q2=A)와 정렬.
- 각 UOW 착수 전 해당 **환경 smoke test** 통과 필요: V-2→UOW-1, V-3→UOW-3, V-1→UOW-4, V-4→UOW-5. 미통과 시 관련 P0 완료 표시 금지(C-SCOPE-2, C-DEP-3).

## 3. UOW 간 통신 패턴 (Q1=A 하이브리드)
| 관계 | 패턴 | 계약/보안 |
|---|---|---|
| 방어 UOW → UOW-1 검증 | **in-process 함수 호출**(공유 lib, Q3=A) | 공개키만, ML-DSA-65, 가짜 성공 금지 |
| 방어 UOW → UOW-2 기록 | **loopback IPC** `AuditClient.emit` → 단일 writer | event_id 유일·행 무손상, fail-closed |
| UOW-2 제어 서버 → UOW-2 조회 | in-process / loopback | 상태·이벤트 집약(Q5=A) |
| UOW-2 제어 서버 → 각 서비스 상태 | **loopback API** | 토큰/Origin/Host 검증 |
| UOW-5 확장 ↔ UOW-5 RBI 서버 | **loopback 제어 메시지 + 픽셀** | 구조화 메시지만, HTML 삽입 금지 |
| UOW-4 보호 클라이언트 → UOW-3 → 업스트림 | **강제 경유 HTTP(S)** | 업스트림 TLS 검증, 지원 제공자 한정 |

## 4. UOW 내부 코드 위치 결합 (Q2=A, UOW-5)
- UOW-5는 `apps/extension/`(TS)과 `src/aegis/web/`(Py) 두 코드 위치를 **하나의 UOW**로 관리. 둘 사이 loopback 제어 메시지 프로토콜은 UOW **내부 인터페이스**(별도 UOW 간 계약 아님)로, 로컬 선실행 방지·픽셀 릴레이가 한 기능이므로 함께 설계·테스트.
- UOW-2도 writer 프로세스 + AuditClient lib + 제어 서버 + UI를 하나의 UOW로 관리(Q3=A). AuditClient는 방어 UOW가 import하는 경계 인터페이스.

## 5. 검증 (D-4)
- **순환 없음**: 매트릭스 상삼각만 채워짐(방어 UOW → 하위 UOW), 역방향 코드 참조 없음.
- **독립 테스트 가능**(NFR-6): UOW-0 계약, UOW-1 서명, UOW-2 감사, UOW-3 프록시, UOW-4 cage, UOW-5 격리가 각각 분리 테스트. 방어 UOW는 UOW-1/2 계약 스텁으로 단위 테스트 가능.
- **환경 게이팅 표기 완료**: V-1/2/3/4를 각 UOW에 매핑.
- **전 스토리 배정**: unit-of-work-story-map.md에서 25개 P0 스토리 100% 배정 확인.
