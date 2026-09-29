"""Free legal-aid lookup (LLD: no auth, no user data stored)."""
from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

from ..infrastructure.legal_aid import JsonLegalAidDirectory

router = APIRouter(prefix="/api/v1/legal-aid", tags=["legal-aid"])

directory = JsonLegalAidDirectory()


class LegalAidEntry(BaseModel):
    name: str
    phone: str | None = None
    url: str | None = None
    verified: bool = False


class LegalAidResponse(BaseModel):
    national: list[LegalAidEntry] = []
    entries: list[LegalAidEntry] = []
    state: str | None = None
    district: str | None = None


class LegalAidStatesResponse(BaseModel):
    states: list[dict] = []


@router.get("", response_model=LegalAidResponse)
def get_legal_aid(
    state: str | None = Query(default=None),
    district: str | None = Query(default=None),
) -> LegalAidResponse:
    data = directory.lookup(state=state, district=district)
    return LegalAidResponse(
        national=[LegalAidEntry(**e) for e in data.get("national", [])],
        entries=[LegalAidEntry(**e) for e in data.get("entries", [])],
        state=state,
        district=district,
    )


@router.get("/states", response_model=LegalAidStatesResponse)
def list_legal_aid_states() -> LegalAidStatesResponse:
    return LegalAidStatesResponse(states=directory.states())
