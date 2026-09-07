"""직렬화 라운드트립·결정성·엄격 파싱 (NFR-CT-3, P2/P3, PBT-02/03/07/08/09).

합성값만 사용한다(실제 키·비밀 금지).
"""

from __future__ import annotations

import json

import pytest
from hypothesis import given
from hypothesis import strategies as st

from aegis.contracts import (
    SCHEMA_VERSION,
    ActionCode,
    AuditEvent,
    RecommendedAction,
    ReasonCode,
    SafeLocation,
    SafeLocationKind,
    Unit,
    Verdict,
    canonical_dumps,
    deserialize,
    serialize,
)
from aegis.contracts.errors import (
    InvalidEnumError,
    SchemaVersionError,
    UnknownFieldError,
)

# --- 합성 전략 (실제 값 아님) ---------------------------------------------

_safe_text = st.text(
    alphabet=st.characters(blacklist_categories=("Cs",)),
    max_size=32,
)


@st.composite
def audit_events(draw) -> AuditEvent:
    return AuditEvent.create(
        workflow_id=draw(st.uuids()).hex,
        unit=draw(st.sampled_from(list(Unit))),
        ts="2026-09-07T00:00:00Z",
        verdict=draw(st.sampled_from(list(Verdict))),
        reason_code=draw(st.sampled_from(list(ReasonCode))),
        target=SafeLocation(
            kind=draw(st.sampled_from(list(SafeLocationKind))),
            label=draw(_safe_text),
        ),
        evidence_hash=draw(st.text(alphabet="0123456789abcdef", min_size=64, max_size=64)),
        recommended_action=RecommendedAction(
            action_code=draw(st.sampled_from(list(ActionCode))),
        ),
        policy_digest=draw(st.none() | st.text(alphabet="0123456789abcdef", min_size=64, max_size=64)),
        pubkey_id=draw(st.none() | _safe_text),
        event_id=draw(st.uuids()).hex,
    )


# --- PBT-02/03: 라운드트립 불변식 -----------------------------------------

@given(audit_events())
def test_round_trip_preserves_value(event: AuditEvent) -> None:
    assert deserialize(serialize(event)) == event


@given(audit_events())
def test_serialize_is_deterministic(event: AuditEvent) -> None:
    assert serialize(event) == serialize(event)


@given(audit_events())
def test_canonical_is_sorted_and_compact(event: AuditEvent) -> None:
    text = serialize(event)
    # 최소 구분자: 공백 없는 구분.
    assert ", " not in text and ": " not in text
    # 키 정렬: 재파싱 후 재직렬화 동일.
    assert canonical_dumps(json.loads(text)) == text


# --- P3: 부동소수 배제 ----------------------------------------------------

def test_canonical_rejects_float() -> None:
    with pytest.raises(ValueError):
        canonical_dumps({"x": 1.5})


def test_canonical_rejects_nested_float() -> None:
    with pytest.raises(ValueError):
        canonical_dumps({"a": [1, {"b": 2.0}]})


# --- P2: 엄격 파싱 (fail-closed) ------------------------------------------

def _valid_payload() -> dict:
    event = AuditEvent.create(
        workflow_id="wf-1",
        unit=Unit.GUARD,
        ts="2026-09-07T00:00:00Z",
        verdict=Verdict.BLOCK,
        reason_code=ReasonCode.GUARD_SECRET_DETECTED,
        target=SafeLocation(kind=SafeLocationKind.HOST, label="api.example.test"),
        evidence_hash="0" * 64,
    )
    return json.loads(serialize(event))


def test_reject_unsupported_schema_version() -> None:
    payload = _valid_payload()
    payload["schema_version"] = SCHEMA_VERSION + 1
    with pytest.raises(SchemaVersionError):
        deserialize(canonical_dumps(payload))


def test_reject_unknown_field() -> None:
    payload = _valid_payload()
    payload["injected"] = "x"
    with pytest.raises(UnknownFieldError):
        deserialize(canonical_dumps(payload))


def test_reject_undefined_enum() -> None:
    payload = _valid_payload()
    payload["verdict"] = "SOFTEN"  # 닫힌 집합 밖 — 조용히 통과 금지.
    with pytest.raises(InvalidEnumError):
        deserialize(canonical_dumps(payload))


def test_reject_unknown_field_in_nested_target() -> None:
    payload = _valid_payload()
    payload["target"]["extra"] = "x"
    with pytest.raises(UnknownFieldError):
        deserialize(canonical_dumps(payload))


def test_reject_non_object_top_level() -> None:
    with pytest.raises(UnknownFieldError):
        deserialize("[]")
