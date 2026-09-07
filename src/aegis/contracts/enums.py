"""닫힌 집합 열거형 (NFR Design P2 — 미정의 값 거부).

- ``Verdict``: 세 경계 공통 판정 (감사·UI 통합 조회 기준).
- 경계별 세부 결정(``NavDecision``/``ProxyDecision``/``CageDecision``)은 별도 열거이며
  ``mapping`` 모듈이 공통 ``Verdict``로 결정적 매핑한다.
- ``ReasonCode``: Unit 네임스페이스 접두 식별자. 사람이 읽는 한글 메시지는 계약 밖
  표시계층(``reason-messages``)에 둔다(R6, 코드/메시지 분리).
"""

from __future__ import annotations

from enum import Enum


class Verdict(str, Enum):
    """공통 판정 (닫힌 집합)."""

    ALLOW = "ALLOW"      # 허용/정상 진행
    BLOCK = "BLOCK"      # 차단(전송·실행·행동 금지)
    ISOLATE = "ISOLATE"  # 원격 격리로 전환(로컬 직접 실행 금지)
    ERROR = "ERROR"      # 검사·판정·기록 불가 → fail-closed


class Unit(str, Enum):
    """이벤트·판정의 출처 식별."""

    CONTRACTS = "CONTRACTS"
    POLICY = "POLICY"      # U-4
    AUDIT = "AUDIT"        # U-5
    GUARD = "GUARD"        # U-3
    CAGE = "CAGE"          # U-2
    WEB = "WEB"            # U-1
    CONTROL = "CONTROL"    # 제어 서버


class ComponentStatus(str, Enum):
    """컴포넌트 상태 4구분 (FR-0.2, S-C-2)."""

    PREPARING = "PREPARING"
    PROTECTING = "PROTECTING"
    BLOCKED = "BLOCKED"
    DISABLED = "DISABLED"


class NavDecision(str, Enum):
    """웹 탐색 경계 결정 (U-1)."""

    DIRECT = "DIRECT"
    ISOLATE = "ISOLATE"
    BLOCK = "BLOCK"


class ProxyDecision(str, Enum):
    """전송 프록시 경계 결정 (U-3)."""

    FORWARD = "FORWARD"
    BLOCK = "BLOCK"      # 시크릿 탐지 차단
    REJECT = "REJECT"    # 검사 불가(413/415/400/503) — reason_code로 구분


class CageDecision(str, Enum):
    """샌드박스 실행 경계 결정 (U-2)."""

    RUN = "RUN"
    DENY = "DENY"


class ReasonCode(str, Enum):
    """사유 코드 (닫힌 집합, Unit 네임스페이스 접두).

    신규 코드는 계약 개정으로만 추가한다. HTTP 유사 숫자 코드가 아니라
    사람이 식별 가능한 문자열 식별자를 사용한다.
    """

    # COMMON_
    COMMON_OK = "COMMON_OK"
    COMMON_INTERNAL_ERROR = "COMMON_INTERNAL_ERROR"

    # POLICY_ (U-4)
    POLICY_OK = "POLICY_OK"
    POLICY_SIGNATURE_INVALID = "POLICY_SIGNATURE_INVALID"
    POLICY_SCHEMA_INVALID = "POLICY_SCHEMA_INVALID"
    POLICY_UNTRUSTED_KEY = "POLICY_UNTRUSTED_KEY"
    POLICY_VERSION_UNSUPPORTED = "POLICY_VERSION_UNSUPPORTED"

    # AUDIT_ (U-5)
    AUDIT_UNAVAILABLE = "AUDIT_UNAVAILABLE"
    AUDIT_EVIDENCE_UNCOMPUTABLE = "AUDIT_EVIDENCE_UNCOMPUTABLE"

    # GUARD_ (U-3)
    GUARD_SECRET_DETECTED = "GUARD_SECRET_DETECTED"
    GUARD_PROXY_BYPASS = "GUARD_PROXY_BYPASS"
    GUARD_BODY_TOO_LARGE = "GUARD_BODY_TOO_LARGE"          # 413
    GUARD_UNSUPPORTED_MEDIA = "GUARD_UNSUPPORTED_MEDIA"    # 415
    GUARD_MALFORMED_BODY = "GUARD_MALFORMED_BODY"          # 400
    GUARD_INSPECTION_UNAVAILABLE = "GUARD_INSPECTION_UNAVAILABLE"  # 503
    GUARD_UNSUPPORTED_DESTINATION = "GUARD_UNSUPPORTED_DESTINATION"

    # CAGE_ (U-2)
    CAGE_SIGNATURE_INVALID = "CAGE_SIGNATURE_INVALID"
    CAGE_POLICY_MUTATED = "CAGE_POLICY_MUTATED"            # TOCTOU
    CAGE_PERMISSION_DENIED = "CAGE_PERMISSION_DENIED"
    CAGE_UNVERIFIED_ENV = "CAGE_UNVERIFIED_ENV"

    # WEB_ (U-1)
    WEB_RISKY_ACTION_BLOCKED = "WEB_RISKY_ACTION_BLOCKED"
    WEB_SSRF_BLOCKED = "WEB_SSRF_BLOCKED"
    WEB_ISOLATION_FAILED = "WEB_ISOLATION_FAILED"
    WEB_SESSION_INVALID = "WEB_SESSION_INVALID"


# U-3 차단 응답의 와이어 코드(HTTP 403 body). 내부 reason_code는
# GUARD_SECRET_DETECTED로 대응한다(domain-entities.md §1.2).
SECRET_BLOCKED_WIRE_CODE = "AEGIS_SECRET_BLOCKED"
