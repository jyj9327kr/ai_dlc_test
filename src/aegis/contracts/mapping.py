"""경계별 세부 결정 → 공통 ``Verdict`` 매핑 (R1.3).

결정적·전역 함수. 감사·UI가 공통 Verdict로 통일 조회하고, 경계 의미는
reason_code로 세분한다. ``ProxyDecision.REJECT``(검사 불가)는 공통적으로 BLOCK이며
413/415/400/503 구분은 reason_code가 담당한다.
"""

from __future__ import annotations

from .enums import CageDecision, NavDecision, ProxyDecision, Verdict

_NAV = {
    NavDecision.DIRECT: Verdict.ALLOW,
    NavDecision.ISOLATE: Verdict.ISOLATE,
    NavDecision.BLOCK: Verdict.BLOCK,
}

_PROXY = {
    ProxyDecision.FORWARD: Verdict.ALLOW,
    ProxyDecision.BLOCK: Verdict.BLOCK,
    ProxyDecision.REJECT: Verdict.BLOCK,
}

_CAGE = {
    CageDecision.RUN: Verdict.ALLOW,
    CageDecision.DENY: Verdict.BLOCK,
}


def map_nav(decision: NavDecision) -> Verdict:
    return _NAV[decision]


def map_proxy(decision: ProxyDecision) -> Verdict:
    return _PROXY[decision]


def map_cage(decision: CageDecision) -> Verdict:
    return _CAGE[decision]
