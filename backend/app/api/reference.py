"""Reference dataset endpoints (brief §4, §6)."""

from __future__ import annotations

from fastapi import APIRouter

from .. import reference
from ..schemas import EmissionFactorOut, TariffOut

router = APIRouter(prefix="/api/reference", tags=["reference"])


@router.get("/emission-factors", response_model=list[EmissionFactorOut])
def emission_factors():
    return reference.emission_factors()


@router.get("/tariffs", response_model=list[TariffOut])
def tariffs():
    return reference.tariffs()
