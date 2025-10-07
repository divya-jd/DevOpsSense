import os
import hmac
import hashlib
from datetime import datetime
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import PlainTextResponse
from dotenv import load_dotenv
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from models import GitHubActionsEvent, JenkinsEvent
from storage import init_db, insert_event
from prometheus_metrics import PIPELINE_SUCCESS, PIPELINE_FAILURE, PIPELINE_DURATION, K8S_PODS

load_dotenv()
app = FastAPI(title="DevOpsSense")
WEBHOOK_TOKEN = os.getenv("WEBHOOK_TOKEN", "")
init_db()

def verify_signature(secret: str, payload: bytes, signature_header: str | None) -> None:
    if not secret:
        return
    if not signature_header:
        raise HTTPException(status_code=401, detail="Missing signature")
    mac = hmac.new(secret.encode(), msg=payload, digestmod=hashlib.sha256).hexdigest()
    sig = signature_header.split("=")[-1] if "=" in signature_header else signature_header
    if not hmac.compare_digest(mac, sig):
        raise HTTPException(status_code=401, detail="Invalid signature")

@app.get("/healthz")
def health():
    return {"status": "ok"}

@app.get("/metrics")
def metrics():
    return PlainTextResponse(generate_latest().decode("utf-8"), media_type=CONTENT_TYPE_LATEST)

@app.post("/webhooks/github/actions")
async def github_actions(req: Request, x_hub_signature_256: str | None = Header(default=None)):
    body = await req.body()
    verify_signature(WEBHOOK_TOKEN, body, x_hub_signature_256)
    data = await req.json()

    # opinionated extraction (works with workflow_run event + custom dispatcher)
    gh = GitHubActionsEvent(
        workflow=data["workflow"]["name"],
        run_id=str(data["workflow_run"]["id"]),
        repository=data["repository"]["full_name"],
        branch=data["workflow_run"]["head_branch"],
        status=data["workflow_run"]["status"],            # queued, in_progress, completed
        conclusion=data["workflow_run"].get("conclusion"),# success, failure, cancelled
        triggered_by=data["sender"]["login"],
        duration_ms=int((datetime.fromisoformat(data["workflow_run"]["updated_at"].replace('Z','')) - 
                         datetime.fromisoformat(data["workflow_run"]["created_at"].replace('Z',''))).total_seconds()*1000),
        started_at=datetime.fromisoformat(data["workflow_run"]["created_at"].replace('Z','')),
        finished_at=datetime.fromisoformat(data["workflow_run"]["updated_at"].replace('Z','')),
    )

    insert_event(
        source="github",
        pipeline=gh.workflow,
        run_id=gh.run_id,
        repo_or_project=gh.repository,
        branch=gh.branch or "",
        status=gh.conclusion or gh.status,
        duration_ms=gh.duration_ms,
        started_at=gh.started_at,
        finished_at=gh.finished_at,
    )

    labels = {"source": "github", "pipeline": gh.workflow, "branch": gh.branch or "unknown"}
    PIPELINE_DURATION.labels(**labels).observe(gh.duration_ms / 1000.0)
    if (gh.conclusion or "").lower() == "success":
        PIPELINE_SUCCESS.labels(**labels).inc()
    else:
        PIPELINE_FAILURE.labels(**labels).inc()
    return {"ok": True}

@app.post("/webhooks/jenkins")
async def jenkins(event: JenkinsEvent, x_ds_token: str | None = Header(default=None)):
    # simple shared-secret header (X-Ds-Token)
    if WEBHOOK_TOKEN and x_ds_token != WEBHOOK_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")

    insert_event(
        source="jenkins",
        pipeline=event.job_name,
        run_id=str(event.build_number),
        repo_or_project="jenkins",
        branch=event.git_branch or "",
        status=event.status,
        duration_ms=event.duration_ms,
        started_at=event.started_at,
        finished_at=event.finished_at,
    )

    labels = {"source": "jenkins", "pipeline": event.job_name, "branch": event.git_branch or "unknown"}
    PIPELINE_DURATION.labels(**labels).observe(event.duration_ms / 1000.0)
    if event.status.lower() in ("success", "stable"):
        PIPELINE_SUCCESS.labels(**labels).inc()
    else:
        PIPELINE_FAILURE.labels(**labels).inc()
    return {"ok": True}

@app.post("/k8s/pods/{namespace}/{count}")
def update_pods(namespace: str, count: int, x_ds_token: str | None = Header(default=None)):
    if WEBHOOK_TOKEN and x_ds_token != WEBHOOK_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")
    K8S_PODS.labels(namespace=namespace).set(count)
    return {"ok": True, "namespace": namespace, "running": count}
