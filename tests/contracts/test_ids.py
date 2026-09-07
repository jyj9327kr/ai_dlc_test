"""식별자: 유일성·시간 정렬성 (Functional Q3=A)."""

from __future__ import annotations

import time

from aegis.contracts import new_event_id, new_workflow_id


def test_event_ids_are_unique() -> None:
    ids = {new_event_id() for _ in range(1000)}
    assert len(ids) == 1000


def test_event_ids_are_time_sortable() -> None:
    first = new_event_id()
    time.sleep(0.002)
    second = new_event_id()
    # 나중에 생성된 id가 사전식으로 크거나 같다(단일 writer 정렬 일치, S-U5-1).
    assert second >= first


def test_event_id_has_uuid_shape() -> None:
    eid = new_event_id()
    parts = eid.split("-")
    assert [len(p) for p in parts] == [8, 4, 4, 4, 12]


def test_workflow_ids_are_unique() -> None:
    assert new_workflow_id() != new_workflow_id()
