"""
main.py — FastAPI Entry Point for Insight Narrator AI
"""
import os
import uvicorn
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from backend.agents.orchestrator import OrchestratorAgent
from backend.utils.data_utils import load_dataframe

# ── App Setup ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="Insight Narrator AI",
    description="Agentic AI system that analyzes datasets and generates narrative insights",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend static files
# (parent of main.py is the repository root)
FRONTEND_DIR = Path(__file__).parent / "frontend"
DATA_DIR     = Path(__file__).parent / "data"
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")
app.mount("/data",   StaticFiles(directory=str(DATA_DIR)),     name="data")

orchestrator = OrchestratorAgent()

# ── Routes ─────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serve the main dashboard HTML."""
    html_path = FRONTEND_DIR / "index.html"
    if not html_path.exists():
        raise HTTPException(status_code=404, detail="Frontend not found")
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))


@app.post("/api/analyze")
async def analyze_dataset(file: UploadFile = File(...)):
    """
    Accept a CSV or Excel file, run the full agent pipeline, and return results.
    """
    allowed_types = {
        "text/csv", "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    }
    # Be lenient with content type (browsers sometimes send octet-stream)
    filename = file.filename or "upload.csv"

    if not filename.lower().endswith((".csv", ".xls", ".xlsx")):
        raise HTTPException(
            status_code=400,
            detail="Only CSV and Excel files (.csv, .xls, .xlsx) are supported.",
        )

    try:
        raw_bytes = await file.read()
        df = load_dataframe(raw_bytes, filename)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to parse file: {e}")

    if df.empty:
        raise HTTPException(status_code=422, detail="The uploaded file is empty.")

    if len(df) > 50_000:
        raise HTTPException(
            status_code=413,
            detail="Dataset too large. Please upload a file with fewer than 50,000 rows.",
        )

    try:
        result = orchestrator.run(df, dataset_name=filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis pipeline failed: {e}")

    # Convert non-serializable types (numpy ints/floats) before returning
    import json
    import numpy as np

    def _convert(obj):
        # handle numpy types first
        if isinstance(obj, (np.integer,)):  return int(obj)
        if isinstance(obj, (np.floating,)): return float(obj)
        if isinstance(obj, (np.ndarray,)):  return obj.tolist()
        # pandas / datetime handling
        import pandas as pd
        import datetime
        if isinstance(obj, (pd.Timestamp, datetime.datetime, datetime.date)):
            # convert to ISO string
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    serialized = json.loads(json.dumps(result, default=_convert))
    return JSONResponse(content=serialized)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "insight-narrator-ai"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=True,
    )