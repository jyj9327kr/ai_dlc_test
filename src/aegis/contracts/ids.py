"""식별자 생성 (Functional Q3=A).

- ``new_event_id()``: 전역 유일 + **시간 정렬 가능**. 단일 writer가 append 순서와
  event_id 정렬을 일치시킬 수 있어야 한다(S-U5-1).
- ``new_workflow_id()``: 한 작업(D-1~D-3)을 묶는 상위 식별자(S-C-3).

구현 노트: Python 표준 ``uuid``에 UUIDv7이 없으면(3.11~3.13) time-prefixed 정렬
식별자로 대체한다. 서드파티 의존을 추가하지 않는다(zero 3rd-party, tech-stack Q1=A).
"""

from __future__ import annotations

import os
import time
import uuid

# 48-bit 밀리초 타임스탬프(hex 12자리) + 80-bit 랜덤(hex 20자리) = 32 hex.
# 사전식 정렬이 시간 정렬과 일치한다. UUID 문자열과 동일 폭(대시 삽입).
_RANDOM_BYTES = 10  # 80 bits


def _time_sortable_hex() -> str:
    ms = int(time.time() * 1000) & 0xFFFFFFFFFFFF  # 48 bits
    rand = int.from_bytes(os.urandom(_RANDOM_BYTES), "big")  # 80 bits
    value = (ms << 80) | rand
    return f"{value:032x}"


def _as_uuid_string(hex32: str) -> str:
    return f"{hex32[0:8]}-{hex32[8:12]}-{hex32[12:16]}-{hex32[16:20]}-{hex32[20:32]}"


def new_event_id() -> str:
    """시간 정렬 가능한 전역 유일 이벤트 식별자."""
    native = getattr(uuid, "uuid7", None)
    if native is not None:  # Python 3.14+
        return str(native())
    return _as_uuid_string(_time_sortable_hex())


def new_workflow_id() -> str:
    """한 작업(D-1~D-3)을 묶는 워크플로우 식별자."""
    return str(uuid.uuid4())
