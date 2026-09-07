"""계약 예외 계층 (NFR Design P5 — fail-closed 신호).

계약 위반은 예외로 신호한다. 반환값 무시로 인한 조용한 통과를 막기 위함(C-SCOPE-1).
소비 Unit은 이 예외를 잡아 ``verdict=ERROR`` + 적절한 ``*_UNAVAILABLE`` / ``*_INVALID``
reason_code로 fail-closed 전환한다.

중요(NFR-4 / T-PRIVACY): 예외 메시지에 원문·비밀·키·명령 인자를 담지 않는다.
필드 이름·코드·버전 등 비민감 메타만 포함한다.
"""

from __future__ import annotations


class ContractError(Exception):
    """모든 계약 위반의 기반 예외."""


class SchemaVersionError(ContractError):
    """지원하지 않는 ``schema_version`` (부분 해석 금지, FR-4.4 정렬)."""


class UnknownFieldError(ContractError):
    """계약에 정의되지 않은 필드가 포함됨 (엄격 파싱, 계약 드리프트 방지)."""


class InvalidEnumError(ContractError):
    """닫힌 집합(Verdict/ReasonCode/...) 밖의 값."""


class EvidenceRejectedError(ContractError):
    """증거 서술자가 비민감 규칙을 위반함 (비밀/원문 혼입 의심, 과대 크기 등)."""
