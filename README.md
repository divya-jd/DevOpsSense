# DevOpsSense — CI/CD & Infra Observability (GitHub Actions + Jenkins + Prometheus + Grafana)

DevOpsSense is a lightweight, cloud-friendly **DevOps monitoring stack**:
- Ingest **GitHub Actions** and **Jenkins** events
- Normalize & store runs (SQLite)
- Export **Prometheus** metrics (`/metrics`)
- Preprovisioned **Grafana** dashboard
- Optional **Kubernetes** pod count metric

## ✨ Features
- SLIs: success/failure totals, duration histogram, failure rate proxy
- Shared-secret verification for webhooks
- Single-command bring-up with Docker Compose
- Minimal deps; easy to extend

---

## 🧰 Quick Start

###  Clone & configure

git clone https://github.com/divya-jd/DevOpsSense.git
cd DevOpsSense
cp backend/.env.example backend/.env
- edit WEBHOOK_TOKEN=changeme (set your secret)

### Run the stack
docker compose up --build

### 🔗 Webhook Setup
GitHub Actions (recommended: workflow_run event)

Go to Repo → Settings → Webhooks → Add webhook

Payload URL: http://YOUR_HOST:8000/webhooks/github/actions

Content type: application/json

Secret: your WEBHOOK_TOKEN (must match backend)

Which events?: Let me select individual events → check workflow run

Save.

For local testing, use ngrok http 8000 → use the forwarding URL as webhook target.

### Testing locally
curl -s -X POST http://localhost:8000/webhooks/github/actions \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature-256: sha256=$(python - <<'PY'
import hmac, hashlib, json, os
secret=os.environ.get("WEBHOOK_TOKEN","changeme").encode()
body=open("scripts/sample_github_actions_event.json","rb").read()
print(hmac.new(secret, body, hashlib.sha256).hexdigest())
PY
)" \
  --data-binary @scripts/sample_github_actions_event.json | jq

### Jenkins

Add a Post build step (Execute shell) and paste:

bash ${WORKSPACE}/jenkins_post_build.sh

Place scripts/jenkins_post_build.sh into your repo; adjust:

API_URL → your public API URL: http(s)://HOST:8000/webhooks/jenkins

TOKEN → must match WEBHOOK_TOKEN in backend

Make sure Jenkins env vars (JOB_NAME, BUILD_NUMBER) are available.

### Grafana Dashboard
Auto-provisioned at startup

Panels: Success/Failure totals, p95 duration

Add filters by source, pipeline, branch using PromQL label matchers

### Security

Set WEBHOOK_TOKEN everywhere (GitHub webhook secret, Jenkins header X-Ds-Token)

Use HTTPS in production (behind a reverse proxy or API Gateway)

Rotate token periodically

### Extending

Kubernetes pods metric
# set running pods for a namespace:
curl -X POST "http://localhost:8000/k8s/pods/prod/42" -H "X-Ds-Token: changeme"

dd new sources

Create a new Pydantic model in models.py

Create a new /webhooks/… route in app.py

Normalize & insert_event(...)

Update metrics labels as needed

### Health & Diagnostics

API health: GET /healthz

Prometheus target up: http://localhost:9090/targets

If dashboard missing: check Grafana logs and provisioning paths

### 🛠 Local Dev (without Docker)

cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app:app --reload --port 8000

---

1) Create the repo on GitHub: **`DevOpsSense`**  
2) Copy these files into it (match the layout)  
3) Commit & push  
4) docker compose up --build 
5) Add the GitHub + Jenkins webhooks → watch Grafana light up 🌈



Copyright (c) 2025 Velankani Joise Divya G C
