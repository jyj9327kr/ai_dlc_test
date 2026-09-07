"""값 객체 불변성·안전 팩토리 (P1/P4). 합성값만 사용."""

from __future__ import annotations

import dataclasses

import pytest

from aegis.contracts import (
    SCHEMA_VERSION,
    AuditEvent,
    BlockResponse,
    PolicySnapshot,
    ReasonCode,
    RecommendedAction,
    SafeLocation,
    SafeLocationKind,
    Unit,
    Verdict,
)
from aegis.contracts.models import ActionCode


def _event() -> AuditEvent:
    return AuditEvent.create(
        workflow_id="wf-1",
        unit=Unit.CAGE,
        ts="2026-09-07T00:00:00Z",
        verdict=Verdict.ALLOW,
        reason_code=ReasonCode.COMMON_OK,
        target=SafeLocation(kind=SafeLocationKind.COMMAND_LABEL, label="build"),
        evidence_hash="0" * 64,
    )


def test_audit_event_is_frozen() -> None:
    event = _event()
    with pytest.raises(dataclasses.FrozenInstanceError):
        event.verdict = Verdict.BLOCK  # type: ignore[misc]


def test_create_sets_schema_version_and_event_id() -> None:
    event = _event()
    assert event.schema_version == SCHEMA_VERSION
    assert event.event_id  # 자동 생성됨


def test_create_defaults_recommended_action_none() -> None:
    event = _event()
    assert event.recommended_action == RecommendedAction(ActionCode.NONE)


def test_audit_event_has_no_forbidden_fields() -> None:
    # 구조적 비노출: 금지 필드명이 아예 존재하지 않아야 한다(NFR-4).
    field_names = {f.name for f in dataclasses.fields(AuditEvent)}
    forbidden = {
        "body", "raw_body", "headers", "raw_headers", "url", "query",
        "key", "private_key", "secret", "args", "argv", "env", "command",
        "plaintext", "content",
    }
    assert field_names.isdisjoint(forbidden)


def test_policy_snapshot_digest_matches() -> None:
    snap = PolicySnapshot.of(b"policy-bytes")
    assert len(snap.digest) == 64


def test_policy_snapshot_rejects_mismatched_digest() -> None:
    with pytest.raises(ValueError):
        PolicySnapshot(raw_bytes=b"a", digest="deadbeef")


def test_block_response_defaults_wire_code() -> None:
    resp = BlockResponse(
        event_id="e1",
        rule_id="r1",
        safe_location=SafeLocation(kind=SafeLocationKind.HOST, label="h"),
    )
    assert resp.code == "AEGIS_SECRET_BLOCKED"
