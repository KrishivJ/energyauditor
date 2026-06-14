"""Load-type classification from a circuit name (brief §5.4).

Pure string logic; first keyword hit wins, case-insensitive.
"""

from __future__ import annotations

import re

from .constants import DEFAULT_LOAD_TYPE, LOAD_TYPE_RULES

_COMPILED = [(re.compile(pat, re.IGNORECASE), load_type) for pat, load_type in LOAD_TYPE_RULES]


def classify_load_type(circuit_name: str) -> str:
    """Return the load type for a circuit name; default General Power on no match.

    Note (brief §5.4): a combined feed whose name contains ``HVAC`` (e.g.
    "E-block Power & HVAC") classifies as HVAC under this simple rule. The
    optional regression split (§5.9) can later apportion such circuits.
    """
    name = circuit_name or ""
    for pattern, load_type in _COMPILED:
        if pattern.search(name):
            return load_type
    return DEFAULT_LOAD_TYPE
