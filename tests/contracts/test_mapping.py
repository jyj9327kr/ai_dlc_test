"""경계 결정 → 공통 Verdict 매핑 (R1.3). 전수·결정적 검증."""

from __future__ import annotations

from aegis.contracts import (
    CageDecision,
    NavDecision,
    ProxyDecision,
    Verdict,
    map_cage,
    map_nav,
    map_proxy,
)


def test_map_nav_total() -> None:
    assert map_nav(NavDecision.DIRECT) == Verdict.ALLOW
    assert map_nav(NavDecision.ISOLATE) == Verdict.ISOLATE
    assert map_nav(NavDecision.BLOCK) == Verdict.BLOCK
    # 전수: 모든 값이 매핑됨.
    for d in NavDecision:
        assert isinstance(map_nav(d), Verdict)


def test_map_proxy_reject_is_block() -> None:
    # 검사 불가(REJECT)도 공통적으로 BLOCK — 안전한 차단을 통과로 완화 금지.
    assert map_proxy(ProxyDecision.REJECT) == Verdict.BLOCK
    assert map_proxy(ProxyDecision.BLOCK) == Verdict.BLOCK
    assert map_proxy(ProxyDecision.FORWARD) == Verdict.ALLOW
    for d in ProxyDecision:
        assert isinstance(map_proxy(d), Verdict)


def test_map_cage_total() -> None:
    assert map_cage(CageDecision.RUN) == Verdict.ALLOW
    assert map_cage(CageDecision.DENY) == Verdict.BLOCK
    for d in CageDecision:
        assert isinstance(map_cage(d), Verdict)
