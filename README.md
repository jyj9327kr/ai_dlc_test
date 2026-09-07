# AEGIS

단일 머신·단일 사용자 개발자 보안 워크스페이스. 세 신뢰 경계를 집행한다.

- **U-1 WebIsolate** — 외부 웹 열람 격리(RBI)
- **U-2 AgentCage** — 로컬 AI 에이전트 실행 샌드박스 게이트
- **U-3 SecretGuard** — 클라우드 LLM 요청의 비밀 차단 포워드 프록시
- **U-4 PolicyCore** — 서명 검증된 정책 판정
- **U-5 AuditTrail & Control** — 감사 기록·제어 서버·UI

## 레이아웃

- `src/aegis/` — 애플리케이션 코드(파이썬 패키지). 문서는 `aidlc-docs/`에만 둔다.
- `apps/extension/`(TS), `apps/ui/` — 프런트엔드.
- `tests/` — 공유 테스트, 유닛별 하위 디렉터리.

## 공유 계약 (UOW-0, `src/aegis/contracts/`)

세 경계와 정책·감사가 공유하는 불변 값 객체·닫힌 집합 열거형·결정적 직렬화·
비밀 없는 증거 해시. **서드파티 런타임 의존 0** (표준 라이브러리만) — 기반 계층의
공급망 표면을 최소화하기 위함. `aegis` 내 다른 패키지를 import 하지 않는다(순환 없음).

## 개발

PEP 668 externally-managed 환경에서는 가상환경을 사용한다.

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/python -m pytest tests/contracts -q
```

런타임 의존 0, 개발 의존은 `pytest`·`hypothesis`(속성 기반 테스트)뿐이다.
