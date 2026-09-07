"""결정적 직렬화·엄격 역직렬화 (NFR Design P3 / P2).

- ``canonical_dumps``: sort_keys + 최소 구분자 + ensure_ascii=False + 부동소수 배제.
  동일 값 → 동일 바이트열(NFR-CT-3). evidence_hash·정책 digest 재현성의 기반.
- ``serialize``/``deserialize``: 계약 값 객체 ↔ canonical JSON.
- ``deserialize`` 는 **엄격**하다(P2, fail-closed): 미지원 schema_version·정의되지 않은
  enum 값·알 수 없는 필드를 조용히 무시하지 않고 거부한다.
"""

from __future__ import annotations

import json
from enum import Enum
from typing import Any, Mapping, Type, TypeVar

from .enums import ReasonCode, Unit, Verdict
from .errors import InvalidEnumError, SchemaVersionError, UnknownFieldError
from .models import (
    SCHEMA_VERSION,
    ActionCode,
    AuditEvent,
    RecommendedAction,
    SafeLocation,
    SafeLocationKind,
)


def _reject_floats(value: Any) -> None:
    """부동소수 배제(NFR-CT-3): 비결정적 표현을 원천 차단."""
    if isinstance(value, float):
        raise ValueError("계약 직렬화는 부동소수를 허용하지 않음")
    if isinstance(value, Mapping):
        for item in value.values():
            _reject_floats(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _reject_floats(item)


def canonical_dumps(payload: Any) -> str:
    """결정적 canonical JSON 문자열."""
    _reject_floats(payload)
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


# ---- enum 안전 파싱 -------------------------------------------------------

_E = TypeVar("_E", bound=Enum)


def _parse_enum(enum_cls: Type[_E], raw: Any) -> _E:
    try:
        return enum_cls(raw)
    except ValueError:
        # 정의되지 않은 enum 값 — fail-closed로 거부(조용한 무시 금지).
        raise InvalidEnumError(f"{enum_cls.__name__}에 정의되지 않은 값")


def _require_keys(data: Mapping[str, Any], allowed: set[str]) -> None:
    unknown = set(data) - allowed
    if unknown:
        # 알 수 없는 필드 — 스키마 표류·주입 위험으로 거부(P2).
        raise UnknownFieldError(f"알 수 없는 필드: {sorted(unknown)}")


# ---- AuditEvent 직렬화 ----------------------------------------------------

_AUDIT_FIELDS = {
    "schema_version",
    "event_id",
    "workflow_id",
    "unit",
    "ts",
    "verdict",
    "reason_code",
    "target",
    "recommended_action",
    "evidence_hash",
    "policy_digest",
    "pubkey_id",
}

_SAFE_LOCATION_FIELDS = {"kind", "label"}
_RECOMMENDED_ACTION_FIELDS = {"action_code"}


def _safe_location_to_dict(loc: SafeLocation) -> dict:
    return {"kind": loc.kind.value, "label": loc.label}


def _safe_location_from_dict(data: Mapping[str, Any]) -> SafeLocation:
    _require_keys(data, _SAFE_LOCATION_FIELDS)
    return SafeLocation(
        kind=_parse_enum(SafeLocationKind, data.get("kind")),
        label=data["label"],
    )


def _recommended_action_to_dict(action: RecommendedAction) -> dict:
    return {"action_code": action.action_code.value}


def _recommended_action_from_dict(data: Mapping[str, Any]) -> RecommendedAction:
    _require_keys(data, _RECOMMENDED_ACTION_FIELDS)
    return RecommendedAction(
        action_code=_parse_enum(ActionCode, data.get("action_code")),
    )


def audit_event_to_dict(event: AuditEvent) -> dict:
    return {
        "schema_version": event.schema_version,
        "event_id": event.event_id,
        "workflow_id": event.workflow_id,
        "unit": event.unit.value,
        "ts": event.ts,
        "verdict": event.verdict.value,
        "reason_code": event.reason_code.value,
        "target": _safe_location_to_dict(event.target),
        "recommended_action": _recommended_action_to_dict(event.recommended_action),
        "evidence_hash": event.evidence_hash,
        "policy_digest": event.policy_digest,
        "pubkey_id": event.pubkey_id,
    }


def audit_event_from_dict(data: Mapping[str, Any]) -> AuditEvent:
    _require_keys(data, _AUDIT_FIELDS)

    schema_version = data.get("schema_version")
    if schema_version != SCHEMA_VERSION:
        # 미지원 스키마 버전 — 조용히 강등·수용하지 않고 거부(fail-closed).
        raise SchemaVersionError(f"지원하지 않는 schema_version: {schema_version!r}")

    target_raw = data.get("target")
    action_raw = data.get("recommended_action")
    if not isinstance(target_raw, Mapping) or not isinstance(action_raw, Mapping):
        raise UnknownFieldError("target/recommended_action 형식 오류")

    return AuditEvent(
        schema_version=schema_version,
        event_id=data["event_id"],
        workflow_id=data["workflow_id"],
        unit=_parse_enum(Unit, data.get("unit")),
        ts=data["ts"],
        verdict=_parse_enum(Verdict, data.get("verdict")),
        reason_code=_parse_enum(ReasonCode, data.get("reason_code")),
        target=_safe_location_from_dict(target_raw),
        recommended_action=_recommended_action_from_dict(action_raw),
        evidence_hash=data["evidence_hash"],
        policy_digest=data.get("policy_digest"),
        pubkey_id=data.get("pubkey_id"),
    )


def serialize(event: AuditEvent) -> str:
    """AuditEvent → canonical JSON 문자열."""
    return canonical_dumps(audit_event_to_dict(event))


def deserialize(text: str) -> AuditEvent:
    """canonical JSON 문자열 → AuditEvent (엄격 파싱)."""
    data = json.loads(text)
    if not isinstance(data, dict):
        raise UnknownFieldError("최상위는 객체여야 함")
    return audit_event_from_dict(data)
