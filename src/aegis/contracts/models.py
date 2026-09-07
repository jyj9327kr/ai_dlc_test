"""불변 값 객체 (NFR Design P1 / P4).

모든 계약 타입은 ``@dataclass(frozen=True, slots=True)`` 로 불변이다.

원문·비밀 비노출(NFR-4, FR-5.2, T-PRIVACY): 어떤 값 객체도 요청 본문·전체 URL
query·원시 헤더·키·개인키·명령 인자·환경변수를 담는 필드를 두지 않는다(구조적 불가능).
``AuditEvent``는 안전 팩토리 ``create`` 로만 생성하며, 완성된 ``evidence_hash``(문자열)만
수용한다 — 원문이 이벤트 경로에 진입할 표면이 없다.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from enum import Enum

from .enums import ReasonCode, Unit, Verdict
from .ids import new_event_id

SCHEMA_VERSION = 1


class SafeLocationKind(str, Enum):
    HOST = "HOST"
    COMMAND_LABEL = "COMMAND_LABEL"
    SESSION = "SESSION"
    FIELD_LABEL = "FIELD_LABEL"


class ActionCode(str, Enum):
    RETRY_ISOLATED = "RETRY_ISOLATED"
    REMOVE_SECRET_RETRY = "REMOVE_SECRET_RETRY"
    REOPEN_SESSION = "REOPEN_SESSION"
    CONTACT_ADMIN = "CONTACT_ADMIN"
    NONE = "NONE"


@dataclass(frozen=True, slots=True)
class PolicySnapshot:
    """검증 대상이 된 정책의 불변 스냅샷 (TOCTOU 방지, S-U2-2).

    ``raw_bytes`` 는 정책 설정값이며 비밀·자격증명이 아니다. 서명 검증 메시지 구성에만
    쓰이고, 감사에는 ``digest`` 만 남긴다.
    """

    raw_bytes: bytes
    digest: str

    @staticmethod
    def of(raw_bytes: bytes) -> "PolicySnapshot":
        digest = hashlib.sha256(raw_bytes).hexdigest()
        return PolicySnapshot(raw_bytes=raw_bytes, digest=digest)

    def __post_init__(self) -> None:
        if self.digest != hashlib.sha256(self.raw_bytes).hexdigest():
            raise ValueError("PolicySnapshot.digest가 raw_bytes의 sha256과 불일치")


@dataclass(frozen=True, slots=True)
class Judgment:
    """정책 판정 결과 (S-U4-4, 잠긴 필드)."""

    policy_id: str
    policy_version: int
    policy_digest: str
    pubkey_id: str
    verdict: Verdict
    reason_code: ReasonCode
    rule_id: str | None = None


@dataclass(frozen=True, slots=True)
class SafeLocation:
    """차단·격리 시 안전 위치의 비민감 식별자. label은 원문·인자가 아니다."""

    kind: SafeLocationKind
    label: str


@dataclass(frozen=True, slots=True)
class RecommendedAction:
    action_code: ActionCode = ActionCode.NONE


@dataclass(frozen=True, slots=True)
class AuditEvent:
    """감사 이벤트 (S-U5-1/2). 금지 필드는 구조적으로 존재하지 않는다.

    생성은 ``AuditEvent.create`` 팩토리로만 한다 — 원시 본문/헤더/키/인자를 받는
    매개변수가 없다.
    """

    schema_version: int
    event_id: str
    workflow_id: str
    unit: Unit
    ts: str  # RFC3339 UTC
    verdict: Verdict
    reason_code: ReasonCode
    target: SafeLocation
    recommended_action: RecommendedAction
    evidence_hash: str
    policy_digest: str | None = None
    pubkey_id: str | None = None

    @staticmethod
    def create(
        *,
        workflow_id: str,
        unit: Unit,
        ts: str,
        verdict: Verdict,
        reason_code: ReasonCode,
        target: SafeLocation,
        evidence_hash: str,
        recommended_action: RecommendedAction | None = None,
        policy_digest: str | None = None,
        pubkey_id: str | None = None,
        event_id: str | None = None,
    ) -> "AuditEvent":
        return AuditEvent(
            schema_version=SCHEMA_VERSION,
            event_id=event_id or new_event_id(),
            workflow_id=workflow_id,
            unit=unit,
            ts=ts,
            verdict=verdict,
            reason_code=reason_code,
            target=target,
            recommended_action=recommended_action or RecommendedAction(),
            evidence_hash=evidence_hash,
            policy_digest=policy_digest,
            pubkey_id=pubkey_id,
        )


@dataclass(frozen=True, slots=True)
class BlockResponse:
    """U-3 차단 응답 (HTTP 403 body, S-U3-3)."""

    event_id: str
    rule_id: str
    safe_location: SafeLocation
    code: str = field(default="AEGIS_SECRET_BLOCKED")
