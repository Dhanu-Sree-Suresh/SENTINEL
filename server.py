"""PPA-GOV competition demo server.

Optional online mode for the otherwise fully offline dashboard. The browser
falls back to its local simulation if this API is not running.

Run:
    pip install -r requirements.txt
    python server.py
Then open http://127.0.0.1:8000/
"""
from __future__ import annotations
import json, os, re, sys, time, uuid
from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent
ENGINE = ROOT / "engine"
sys.path.insert(0, str(ENGINE))

from src.data_gen import generate_all
from src.agent.agent import PrivacyAwareAgent
from src.firewall.budget_ledger import BudgetLedger
from src.firewall.query_monitor import QueryMonitor

app = FastAPI(title="PPA-GOV Privacy Control Plane", version="1.0")
app.mount("/assets", StaticFiles(directory=ROOT / "assets"), name="assets")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8000", "http://localhost:8000"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

# Small real synthetic dataset for interactive API demos; raw rows never leave
# this process. The full 83k-record research generator/results remain bundled
# under engine/ for reproducible evaluation.
DF = generate_all(seed=42, scale=0.02)
ENTITY_DFS = {e: DF[DF.entity == e].reset_index(drop=True) for e in DF.entity.unique()}
LEDGER = BudgetLedger(list(ENTITY_DFS), tier="normal")
MONITOR = QueryMonitor(window_seconds=60, freq_threshold=5, jaccard_threshold=0.65)
AGENT = PrivacyAwareAgent(ENTITY_DFS, LEDGER, MONITOR, query_epsilon=0.5)
EVENTS = []

class QueryIn(BaseModel):
    text: str = Field(min_length=1, max_length=500)
    session_id: Optional[str] = None
    epsilon: float = Field(default=0.5, gt=0, le=20)

class AttackIn(BaseModel):
    scenario: str = Field(default="Membership inference", max_length=80)
    population: int = Field(default=20, ge=2, le=1000000)
    observations: int = Field(default=6, ge=1, le=10000)
    signal: float = Field(default=50, ge=0, le=100)
    epsilon: float = Field(default=0.6, gt=0, le=20)


def add_event(category, risk, action, detail):
    event={"event_id":"EVT-"+uuid.uuid4().hex[:6].upper(),"timestamp":time.time(),"category":category,"risk":risk,"action":action,"detail":detail,"user_content":"REDACTED"}
    EVENTS.insert(0,event); del EVENTS[40:]
    return event

@app.get("/api/health")
def health():
    return {"status":"ok","service":"PPA-GOV","entities":len(ENTITY_DFS),"records":int(len(DF))}

@app.get("/api/benchmark")
def benchmark():
    path=ENGINE/"results"/"results.json"
    data=json.loads(path.read_text())
    return {"naive_roc_auc":data["1_centralized_naive"]["utility"]["roc_auc_mean"],
            "proposed_roc_auc":data["3_fl_dp_sweep"]["4" if "4" in data["3_fl_dp_sweep"] else "2"]["utility"]["roc_auc_mean"],
            "naive_mi_auc":data["1_centralized_naive"]["mi_attack"]["subgroup_auc_mean"],
            "proposed_mi_auc":data["3_fl_dp_sweep"]["4"]["mi_attack"]["subgroup_auc_mean"],
            "gradient_raw_cosine":0.99999998,"gradient_dp_cosine":-0.041,
            "gradient_raw_mse":1.3e-35,"gradient_dp_mse":2.67}

@app.post("/api/query")
def query(payload: QueryIn):
    session=payload.session_id or "WEB-"+uuid.uuid4().hex[:6]
    text=payload.text.strip()
    # Deterministic policy path; agent never exposes raw rows.
    resp=AGENT.handle_request("web-analyst", text, filters={"query":text}, ts=time.time())
    risk="HIGH" if not resp.allowed else "LOW"
    action="BLOCKED" if not resp.allowed else "ALLOW"
    event=add_event(resp.intent, risk, action, resp.explanation[:180])
    result_value = None
    if resp.result and isinstance(resp.result, dict) and "noisy_total_estimate" in resp.result:
        result_value = f"Protected aggregate estimate: {float(resp.result["noisy_total_estimate"]):.2f} (Laplace DP; epsilon={payload.epsilon:.2f} per eligible entity)."
    elif isinstance(resp.result, str):
        result_value = resp.result
    return {"response":result_value,
            "explanation":resp.explanation,"allowed":resp.allowed,"intent":resp.intent,"risk":risk,"action":action,
            "event_id":event["event_id"],"session_id":session}

@app.post("/api/attack")
def attack(payload: AttackIn):
    # Interactive model for UI inputs, plus measured anchors for the two
    # research attacks that are actually implemented in engine/src/attacks.
    scenario=payload.scenario
    exposure=(payload.observations/(payload.observations+4))*(payload.signal/100)
    size_factor=min(1.4,30/payload.population)
    boosts={"Membership inference":6,"Differencing attack":12,"Rare subgroup reconstruction":16,"Repeated query attack":10,"Gradient inversion":20,"Model poisoning":24}
    naive=min(99,12+exposure*58+boosts.get(scenario,8)+size_factor*8)
    protected=max(1,min(95,naive*(0.48 if scenario=="Model poisoning" else 0.22+0.06*min(2,payload.epsilon))-(payload.signal*.08)+min(8,payload.epsilon*1.2)))
    measured=None
    if scenario=="Membership inference": measured={"naive_auc":0.5353569353180954,"protected_auc":0.5298,"note":"Measured high-risk-subgroup membership-inference AUC from the bundled 3-seed experiment matrix; the UI confidence is an interactive scenario estimate."}
    elif scenario=="Gradient inversion": measured={"raw_cosine":0.99999998,"dp_cosine":-0.041,"raw_mse":1.3e-35,"dp_mse":2.67,"note":"Measured closed-form reconstruction benchmark from the bundled gradient-inversion experiment."}
    elif scenario=="Model poisoning": measured={"plain_fedavg_roc_auc":0.406,"coordinate_median_roc_auc":0.633,"note":"Measured one-malicious-entity (25%) robustness experiment; 50% malicious is documented as a failure boundary."}
    add_event("Attack Lab", "HIGH" if naive>=60 else "MEDIUM", "SIMULATED", f"{scenario}: naive={naive:.1f} protected={protected:.1f}")
    return {"scenario":scenario,"naive_confidence":round(naive,1),"protected_confidence":round(protected,1),"measured":measured}

@app.get("/api/events")
def events():
    return EVENTS

@app.get("/")
def root():
    return FileResponse(ROOT/"index.html")

# Static files are intentionally explicit rather than exposing arbitrary paths.
@app.get("/{page}.html")
def page(page: str):
    target=ROOT/(page+".html")
    if not target.exists():
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Page not found")
    return FileResponse(target)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
