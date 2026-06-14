"""Analysis CRUD + run endpoints (brief §4)."""

from __future__ import annotations

import json
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import ALLOWED_EXTENSIONS, MAX_UPLOAD_MB
from ..db import get_db
from ..ingestion.parse import parse_file
from ..models import Analysis, FileRecord
from ..schemas import (
    AnalysisConfig,
    AnalysisDetail,
    AnalysisSummary,
    OkResponse,
    ResultsOut,
    RunResponse,
    UploadResponse,
)
from ..services import file_meta, record_to_meta, run_analysis
from ..storage import storage

router = APIRouter(prefix="/api/analyses", tags=["analyses"])


def _get_or_404(db: Session, analysis_id: str) -> Analysis:
    a = db.get(Analysis, analysis_id)
    if a is None:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return a


@router.post("", response_model=UploadResponse)
async def create_analysis(files: list[UploadFile] = File(...), db: Session = Depends(get_db)):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    analysis_id = str(uuid.uuid4())
    default_name = Path(files[0].filename or "analysis").stem
    analysis = Analysis(id=analysis_id, name=f"Analysis — {default_name}", status="uploaded")
    db.add(analysis)

    metas, warnings = [], []
    for up in files:
        ext = Path(up.filename or "").suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            warnings.append(f"{up.filename}: unsupported type '{ext}', skipped.")
            continue
        content = await up.read()
        if len(content) > MAX_UPLOAD_MB * 1024 * 1024:
            warnings.append(f"{up.filename}: exceeds {MAX_UPLOAD_MB} MB, skipped.")
            continue

        path = storage.save(analysis_id, up.filename, content)
        res = parse_file(up.filename, content, mode="cv")  # detection preview
        db.add(
            FileRecord(
                analysis_id=analysis_id,
                filename=up.filename,
                circuit_name=res.circuit_name,
                load_type=res.load_type,
                storage_path=path,
                row_count=res.row_count,
                start_ts=res.start_ts,
                end_ts=res.end_ts,
                detected_cols_json=json.dumps({**res.detected_cols, "_headerRow": res.header_row}),
                flags_json=json.dumps(res.warnings),
            )
        )
        metas.append(file_meta(res))
        warnings.extend(f"{up.filename}: {w}" for w in res.warnings)

    if not metas:
        raise HTTPException(status_code=400, detail="No valid meter files in upload")

    db.commit()
    return UploadResponse(analysisId=analysis_id, files=metas, warnings=warnings)


@router.get("", response_model=list[AnalysisSummary])
def list_analyses(db: Session = Depends(get_db)):
    rows = db.scalars(select(Analysis).order_by(Analysis.created_at.desc())).all()
    return [
        AnalysisSummary(id=a.id, name=a.name, createdAt=a.created_at.isoformat(), status=a.status)
        for a in rows
    ]


@router.get("/{analysis_id}", response_model=AnalysisDetail)
def get_analysis(analysis_id: str, db: Session = Depends(get_db)):
    a = _get_or_404(db, analysis_id)
    config = AnalysisConfig.model_validate_json(a.config_json) if a.config_json else None
    results = ResultsOut.model_validate_json(a.results_json) if a.results_json else None
    return AnalysisDetail(
        id=a.id,
        name=a.name,
        status=a.status,
        createdAt=a.created_at.isoformat(),
        config=config,
        files=[record_to_meta(f) for f in a.files],
        results=results,
    )


@router.put("/{analysis_id}/config", response_model=OkResponse)
def set_config(analysis_id: str, config: AnalysisConfig, db: Session = Depends(get_db)):
    a = _get_or_404(db, analysis_id)
    a.config_json = config.model_dump_json()
    if a.status == "uploaded":
        a.status = "configured"
    db.commit()
    return OkResponse()


@router.post("/{analysis_id}/run", response_model=RunResponse)
def run(analysis_id: str, db: Session = Depends(get_db)):
    a = _get_or_404(db, analysis_id)
    config = (
        AnalysisConfig.model_validate_json(a.config_json) if a.config_json else AnalysisConfig()
    )
    try:
        results = run_analysis(db, a, config)
    except ValueError as e:
        a.status = "error"
        db.commit()
        raise HTTPException(status_code=422, detail=str(e)) from e
    return RunResponse(results=results)


@router.delete("/{analysis_id}", response_model=OkResponse)
def delete_analysis(analysis_id: str, db: Session = Depends(get_db)):
    a = _get_or_404(db, analysis_id)
    db.delete(a)
    db.commit()
    storage.delete_analysis(analysis_id)
    return OkResponse()
