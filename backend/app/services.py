"""Orchestration between the API, storage, ingestion, and the pure engine.

Keeps the engine free of I/O: this module loads stored files, parses them with
the chosen config, runs the engine, and serialises results.
"""

from __future__ import annotations

import json

from sqlalchemy.orm import Session

from .engine.core import run as run_engine
from .ingestion.parse import FileParseResult, parse_file
from .models import Analysis, FileRecord
from .schemas import AnalysisConfig, FileMeta, ResultsOut
from .storage import storage


def file_meta(res: FileParseResult) -> FileMeta:
    return FileMeta(
        filename=res.filename,
        circuitName=res.circuit_name,
        loadType=res.load_type,
        rowCount=res.row_count,
        startTs=res.start_ts,
        endTs=res.end_ts,
        detectedCols=res.detected_cols,
        headerRow=res.header_row,
        warnings=res.warnings,
    )


def record_to_meta(rec: FileRecord) -> FileMeta:
    return FileMeta(
        filename=rec.filename,
        circuitName=rec.circuit_name,
        loadType=rec.load_type,
        rowCount=rec.row_count,
        startTs=rec.start_ts,
        endTs=rec.end_ts,
        detectedCols=json.loads(rec.detected_cols_json) if rec.detected_cols_json else {},
        headerRow=(
            (json.loads(rec.detected_cols_json) or {}).get("_headerRow", 0)
            if rec.detected_cols_json
            else 0
        ),
        warnings=json.loads(rec.flags_json) if rec.flags_json else [],
    )


def run_analysis(db: Session, analysis: Analysis, config: AnalysisConfig) -> ResultsOut:
    """Re-parse stored files under ``config`` and run the engine."""
    eng_cfg = config.to_engine_config()
    overrides = {fn: ov.model_dump(exclude_none=True) for fn, ov in config.columnOverrides.items()}

    circuits = []
    for rec in analysis.files:
        content = storage.read(rec.storage_path)
        res = parse_file(
            rec.filename, content, mode=config.mode, override=overrides.get(rec.filename)
        )
        if res.circuit:
            circuits.append(res.circuit)
        # refresh stored detection/metadata under the active config
        rec.circuit_name = res.circuit_name
        rec.load_type = res.load_type
        rec.row_count = res.row_count
        rec.start_ts, rec.end_ts = res.start_ts, res.end_ts
        rec.detected_cols_json = json.dumps({**res.detected_cols, "_headerRow": res.header_row})
        rec.flags_json = json.dumps(res.warnings)

    if not circuits:
        raise ValueError("No parseable circuits — check the column mapping for each file.")

    result = run_engine(circuits, eng_cfg)
    out = ResultsOut.of(result)
    analysis.results_json = out.model_dump_json()
    analysis.config_json = config.model_dump_json()
    analysis.status = "complete"
    db.commit()
    return out
