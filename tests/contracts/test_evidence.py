"""증거 게이트·해시 — 비밀 배제 속성 (P4, Security, PBT-07/08/09).

핵심 속성: 해시 입력은 검증된 비민감 서술자뿐이며, 어떤 원문도 해시 함수에
전달되지 않는다. 합성값만 사용(실제 키 금지).
"""

from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from aegis.contracts import EvidenceDescriptor, build_evidence, evidence_hash
from aegis.contracts.errors import EvidenceRejectedError
from aegis.contracts.evidence import _MAX_EXTRA_ITEMS, _MAX_LABEL_LEN


def test_build_accepts_nonsensitive_fields() -> None:
    desc = build_evidence(rule_id="AWS_AKIA", location_label="host:api.test", match_length=20)
    assert isinstance(desc, EvidenceDescriptor)
    assert len(evidence_hash(desc)) == 64


def test_hash_is_deterministic() -> None:
    a = build_evidence(rule_id="R1", match_offset=3)
    b = build_evidence(rule_id="R1", match_offset=3)
    assert evidence_hash(a) == evidence_hash(b)


def test_reject_oversized_label() -> None:
    # 값 복원이 가능한 크기의 자유 텍스트(원문·비밀 혼입 위험) 거부.
    with pytest.raises(EvidenceRejectedError):
        build_evidence(rule_id="x" * (_MAX_LABEL_LEN + 1))


def test_reject_too_many_extra_items() -> None:
    extra = {f"k{i}": i for i in range(_MAX_EXTRA_ITEMS + 1)}
    with pytest.raises(EvidenceRejectedError):
        build_evidence(extra=extra)


def test_reject_bool_extra_value() -> None:
    with pytest.raises(EvidenceRejectedError):
        build_evidence(extra={"flag": True})


def test_reject_negative_match_length() -> None:
    with pytest.raises(EvidenceRejectedError):
        build_evidence(match_length=-1)


def test_reject_non_int_match_length() -> None:
    with pytest.raises(EvidenceRejectedError):
        build_evidence(match_length="20")  # type: ignore[arg-type]


# --- PBT: 해시는 길이·오프셋만 반영, 원문 없음 -----------------------------

@given(
    match_length=st.integers(min_value=0, max_value=10_000),
    match_offset=st.integers(min_value=0, max_value=10_000),
)
def test_hash_stable_for_same_descriptor(match_length: int, match_offset: int) -> None:
    desc = build_evidence(rule_id="R", match_length=match_length, match_offset=match_offset)
    assert evidence_hash(desc) == evidence_hash(desc)


@given(
    label=st.text(
        alphabet=st.characters(blacklist_categories=("Cs",)),
        max_size=_MAX_LABEL_LEN,
    )
)
def test_any_bounded_label_is_accepted_and_hashed(label: str) -> None:
    # 길이 제한 내 라벨은 모두 안전하게 처리되고 64-hex 해시를 만든다.
    desc = build_evidence(location_label=label)
    assert len(evidence_hash(desc)) == 64
