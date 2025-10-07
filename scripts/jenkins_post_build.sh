#!/usr/bin/env bash
# Usage: source in a post-build step (Adjust URL/TOKEN, and provide Jenkins env vars)
API_URL="https://YOUR_HOST/webhooks/jenkins"
TOKEN="changeme"

payload=$(cat <<JSON
{
  "job_name": "${JOB_NAME}",
  "build_number": ${BUILD_NUMBER},
  "status": "${BUILD_STATUS:-${1:-SUCCESS}}",
  "duration_ms": ${BUILD_DURATION_MS:-0},
  "git_branch": "${GIT_BRANCH:-main}",
  "git_commit": "${GIT_COMMIT:-unknown}",
  "triggered_by": "${BUILD_CAUSE_USERID:-jenkins}",
  "started_at": "$(date -u -d "@$(( $(date +%s) - ${BUILD_DURATION_SEC:-0} ))" +"%Y-%m-%dT%H:%M:%S")",
  "finished_at": "$(date -u +"%Y-%m-%dT%H:%M:%S")"
}
JSON
)

curl -s -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -H "X-Ds-Token: $TOKEN" \
  -d "$payload"
echo
