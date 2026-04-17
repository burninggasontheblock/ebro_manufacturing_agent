"""
Manufacturing Operations AI — Download Server

Serves the pitch deck and (optionally) dynamically generated PPTX reports.

Start with:
  uvicorn api.server:app --reload --port 8000
  # or from the manufacturing_ai root:
  python -m api.server
"""
from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse

BASE_DIR  = Path(__file__).resolve().parent.parent
PITCH_PATH = BASE_DIR / "MFG_OPS_AI_Pitch.pptx"

app = FastAPI(title="Manufacturing Ops AI", docs_url=None, redoc_url=None)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

# ── Landing page ──────────────────────────────────────────────────────────────

_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Manufacturing Operations AI</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      background: #0b1520;
      color: #c8d8e8;
      font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 2rem;
    }

    .card {
      background: #162436;
      border: 1px solid #1c3450;
      border-radius: 12px;
      padding: 3rem 3.5rem;
      max-width: 680px;
      width: 100%;
      text-align: center;
    }

    .badge {
      display: inline-block;
      background: #f5a623;
      color: #0b1520;
      font-size: 0.7rem;
      font-weight: 700;
      letter-spacing: 0.12em;
      padding: 0.25rem 0.75rem;
      border-radius: 4px;
      margin-bottom: 1.4rem;
      text-transform: uppercase;
    }

    h1 {
      font-size: 1.85rem;
      font-weight: 800;
      color: #fff;
      line-height: 1.2;
      margin-bottom: 0.5rem;
      letter-spacing: -0.01em;
    }

    .subtitle {
      color: #f5a623;
      font-size: 0.9rem;
      font-style: italic;
      margin-bottom: 2rem;
    }

    .pipeline {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 0;
      flex-wrap: wrap;
      margin: 1.6rem 0 2rem;
      font-size: 0.72rem;
      font-weight: 700;
      letter-spacing: 0.05em;
    }
    .step {
      background: #1c2d40;
      border-radius: 6px;
      padding: 0.35rem 0.6rem;
      white-space: nowrap;
    }
    .step.red    { border: 1px solid #e74c3c; color: #e74c3c; }
    .step.amber  { border: 1px solid #f5a623; color: #f5a623; }
    .step.cyan   { border: 1px solid #00bcd4; color: #00bcd4; }
    .step.purple { border: 1px solid #9b59b6; color: #9b59b6; }
    .step.green  { border: 1px solid #2ecc71; color: #2ecc71; }
    .arrow { color: #3e5a72; padding: 0 0.3rem; font-size: 0.9rem; }

    .features {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 0.75rem;
      margin: 0 0 2rem;
      text-align: left;
    }
    .feature {
      background: #111d2c;
      border: 1px solid #1c3450;
      border-radius: 8px;
      padding: 0.7rem 0.9rem;
      font-size: 0.82rem;
    }
    .feature-title {
      font-weight: 700;
      margin-bottom: 0.2rem;
    }
    .feature-title.cyan   { color: #00bcd4; }
    .feature-title.amber  { color: #f5a623; }
    .feature-title.green  { color: #2ecc71; }
    .feature-title.purple { color: #9b59b6; }
    .feature-desc { color: #7a98b0; font-size: 0.78rem; }

    .download-btn {
      display: inline-flex;
      align-items: center;
      gap: 0.6rem;
      background: #f5a623;
      color: #0b1520;
      font-weight: 800;
      font-size: 1rem;
      letter-spacing: 0.03em;
      text-decoration: none;
      padding: 0.85rem 2.2rem;
      border-radius: 8px;
      transition: background 0.15s, transform 0.1s;
    }
    .download-btn:hover  { background: #e09520; transform: translateY(-1px); }
    .download-btn:active { transform: translateY(0); }

    .download-btn svg { flex-shrink: 0; }

    .meta {
      margin-top: 1.6rem;
      font-size: 0.75rem;
      color: #3e5a72;
    }

    .stack {
      display: flex;
      flex-wrap: wrap;
      justify-content: center;
      gap: 0.5rem;
      margin-top: 2rem;
    }
    .pill {
      background: #0f2030;
      border: 1px solid #1c3450;
      border-radius: 20px;
      padding: 0.2rem 0.7rem;
      font-size: 0.72rem;
      color: #c8d8e8;
    }
  </style>
</head>
<body>
  <div class="card">
    <div class="badge">Manufacturing Operations AI</div>

    <h1>Multi-Agent Root-Cause Analysis</h1>
    <p class="subtitle">From Alert to Action in Seconds</p>

    <!-- Pipeline flow -->
    <div class="pipeline">
      <span class="step red">INCIDENT ALERT</span>
      <span class="arrow">›</span>
      <span class="step amber">ORCHESTRATOR</span>
      <span class="arrow">›</span>
      <span class="step cyan">5 AGENTS</span>
      <span class="arrow">›</span>
      <span class="step purple">AGENTIC RAG</span>
      <span class="arrow">›</span>
      <span class="step green">RCA SYNTHESIZER</span>
      <span class="arrow">›</span>
      <span class="step amber">4 ACTION DOCS</span>
    </div>

    <!-- Feature grid -->
    <div class="features">
      <div class="feature">
        <div class="feature-title cyan">Shift Handoff Note</div>
        <div class="feature-desc">Watch items, do-not-restart conditions, escalation contacts</div>
      </div>
      <div class="feature">
        <div class="feature-title amber">Maintenance Work Order</div>
        <div class="feature-desc">Equipment tasks, part numbers, LOTO safety precautions</div>
      </div>
      <div class="feature">
        <div class="feature-title green">Corrective Action Plan</div>
        <div class="feature-desc">Immediate / Short / Long term with owners, KPIs, due dates</div>
      </div>
      <div class="feature">
        <div class="feature-title purple">Supplier Questionnaire</div>
        <div class="feature-desc">Root cause, timeline, prevention & compensation questions</div>
      </div>
    </div>

    <!-- Download button -->
    <a href="/download/pitch" class="download-btn">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none"
           stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
        <polyline points="7 10 12 15 17 10"/>
        <line x1="12" y1="15" x2="12" y2="3"/>
      </svg>
      Download Pitch Deck (.pptx)
    </a>

    <p class="meta">MFG_OPS_AI_Pitch.pptx &nbsp;·&nbsp; Single slide &nbsp;·&nbsp; LAYOUT_WIDE 13.3"×7.5"</p>

    <div class="stack">
      <span class="pill">LangChain Agents</span>
      <span class="pill">LangGraph</span>
      <span class="pill">Agentic RAG</span>
      <span class="pill">FAISS Vector Store</span>
      <span class="pill">Claude AI (Anthropic)</span>
    </div>
  </div>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
def landing():
    return HTMLResponse(content=_HTML)


@app.get("/download/pitch")
def download_pitch():
    if not PITCH_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail="Pitch deck not found. Run `cd /tmp/slide_build && node generate.js` to build it.",
        )
    return FileResponse(
        path=str(PITCH_PATH),
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        filename="Manufacturing_Ops_AI_Pitch.pptx",
        headers={"Content-Disposition": "attachment; filename=Manufacturing_Ops_AI_Pitch.pptx"},
    )


@app.get("/health")
def health():
    return {"status": "ok", "pitch_available": PITCH_PATH.exists()}


# ── Dev runner ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.server:app", host="0.0.0.0", port=8000, reload=True)
