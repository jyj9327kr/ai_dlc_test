"""AEGIS 공유 계약 (UOW-0).

세 신뢰 경계(U-1/U-2/U-3)와 정책(U-4)·감사(U-5)가 공유하는 불변 값 객체,
닫힌 집합 열거형, 결정적 직렬화, 비밀 없는 증거 해시를 제공한다.

의존 규칙(NFR-6): 이 패키지는 ``aegis`` 내 다른 어떤 패키지도 import 하지 않는다
(순환 없음, 독립 테스트 가능). 서드파티 의존 0개(표준 라이브러리만).
"""

from __future__ import annotations

from .enums import (
    SECRET_BLOCKED_WIRE_CODE,
    CageDecision,
    ComponentStatus,
    NavDecision,
    ProxyDecision,
    ReasonCode,
    Unit,
    Verdict,
)
from .errors import (
    ContractError,
    EvidenceRejectedError,
    InvalidEnumError,
    SchemaVersionError,
    UnknownFieldError,
)
from .evidence import EvidenceDescriptor, build as build_evidence, evidence_hash
from .ids import new_event_id, new_workflow_id
from .mapping import map_cage, map_nav, map_proxy
from .models import (
    SCHEMA_VERSION,
    ActionCode,
    AuditEvent,
    BlockResponse,
    Judgment,
    PolicySnapshot,
    RecommendedAction,
    SafeLocation,
    SafeLocationKind,
)
from .serialization import (
    audit_event_from_dict,
    audit_event_to_dict,
    canonical_dumps,
    deserialize,
    serialize,
)

__all__ = [
    # version
    "SCHEMA_VERSION",
    # enums
    "Verdict",
    "Unit",
    "ComponentStatus",
    "NavDecision",
    "ProxyDecision",
    "CageDecision",
    "ReasonCode",
    "SECRET_BLOCKED_WIRE_CODE",
    # models
    "ActionCode",
    "AuditEvent",
    "BlockResponse",
    "Judgment",
    "PolicySnapshot",
    "RecommendedAction",
    "SafeLocation",
    "SafeLocationKind",
    # evidence
    "EvidenceDescriptor",
    "build_evidence",
    "evidence_hash",
    # ids
    "new_event_id",
    "new_workflow_id",
    # mapping
    "map_nav",
    "map_proxy",
    "map_cage",
    # serialization
    "serialize",
    "deserialize",
    "canonical_dumps",
    "audit_event_to_dict",
    "audit_event_from_dict",
    # errors
    "ContractError",
    "SchemaVersionError",
    "UnknownFieldError",
    "InvalidEnumError",
    "EvidenceRejectedError",
]
