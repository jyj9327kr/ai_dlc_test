"""증거 서술자·해시 (NFR Design P4 — 원문 비노출 이중 방어, Security 집행).

evidence_hash 는 판정을 재현·대조하기 위한 **비밀 없는** 서술자를 SHA-256 한 값이다.
원문·비밀을 해시 입력으로도 사용하지 않는다(Q4=A / R2.4). 해시로 원문을 복원할 수 없다.

강제 지점(Q3=A): ``EvidenceDescriptor`` 는 오직 ``build()`` 단일 게이트로만 생성한다.
게이트가 (1) 허용된 비민감 필드만 수용, (2) 값의 타입·최대 길이 검증,
(3) 자유 텍스트/비밀 의심 시 ``EvidenceRejectedError`` 로 거부한다.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Mapping

from .errors import EvidenceRejectedError

# extra 값으로 허용하는 비민감 문자열의 최대 길이. 값 복원이 가능한 크기의
# 자유 텍스트를 원천 차단한다(비밀·원문 혼입 방지).
_MAX_LABEL_LEN = 128
_MAX_EXTRA_ITEMS = 16


@dataclass(frozen=True, slots=True)
class EvidenceDescriptor:
    """evidence_hash 입력. 비밀·원문 미포함. ``build()`` 로만 생성."""

    rule_id: str | None = None
    location_label: str | None = None
    normalization_id: str | None = None
    match_length: int | None = None
    match_offset: int | None = None
    extra: Mapping[str, str | int] = field(default_factory=dict)


def _check_label(name: str, value: str | None) -> None:
    if value is None:
        return
    if not isinstance(value, str):
        raise EvidenceRejectedError(f"{name}는 문자열이어야 함")
    if len(value) > _MAX_LABEL_LEN:
        # 값 복원이 가능한 크기의 자유 텍스트 — 비밀/원문 혼입 위험으로 거부.
        raise EvidenceRejectedError(f"{name} 길이 초과({_MAX_LABEL_LEN})")


def _check_int(name: str, value: int | None) -> None:
    if value is None:
        return
    if isinstance(value, bool) or not isinstance(value, int):
        raise EvidenceRejectedError(f"{name}는 정수여야 함")
    if value < 0:
        raise EvidenceRejectedError(f"{name}는 음수 불가")


def build(
    *,
    rule_id: str | None = None,
    location_label: str | None = None,
    normalization_id: str | None = None,
    match_length: int | None = None,
    match_offset: int | None = None,
    extra: Mapping[str, str | int] | None = None,
) -> EvidenceDescriptor:
    """비민감 증거 서술자를 검증 후 생성하는 단일 게이트."""
    _check_label("rule_id", rule_id)
    _check_label("location_label", location_label)
    _check_label("normalization_id", normalization_id)
    _check_int("match_length", match_length)
    _check_int("match_offset", match_offset)

    checked_extra: dict[str, str | int] = {}
    if extra:
        if len(extra) > _MAX_EXTRA_ITEMS:
            raise EvidenceRejectedError(f"extra 항목 수 초과({_MAX_EXTRA_ITEMS})")
        for key, value in extra.items():
            if not isinstance(key, str) or len(key) > _MAX_LABEL_LEN:
                raise EvidenceRejectedError("extra 키가 유효하지 않음")
            if isinstance(value, bool):
                raise EvidenceRejectedError("extra 값에 bool 불가")
            if isinstance(value, int):
                _check_int(f"extra[{key}]", value)
            elif isinstance(value, str):
                _check_label(f"extra[{key}]", value)
            else:
                raise EvidenceRejectedError("extra 값은 문자열/정수만 허용")
            checked_extra[key] = value

    return EvidenceDescriptor(
        rule_id=rule_id,
        location_label=location_label,
        normalization_id=normalization_id,
        match_length=match_length,
        match_offset=match_offset,
        extra=checked_extra,
    )


def _descriptor_payload(descriptor: EvidenceDescriptor) -> dict:
    return {
        "rule_id": descriptor.rule_id,
        "location_label": descriptor.location_label,
        "normalization_id": descriptor.normalization_id,
        "match_length": descriptor.match_length,
        "match_offset": descriptor.match_offset,
        "extra": dict(descriptor.extra),
    }


def evidence_hash(descriptor: EvidenceDescriptor) -> str:
    """canonical JSON(descriptor) → SHA-256 hex. 원문 미입력."""
    from .serialization import canonical_dumps

    payload = _descriptor_payload(descriptor)
    return hashlib.sha256(canonical_dumps(payload).encode("utf-8")).hexdigest()
