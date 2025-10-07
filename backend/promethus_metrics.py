from prometheus_client import Counter, Histogram, Gauge

# counts
PIPELINE_SUCCESS = Counter(
    "devopssense_pipeline_success_total",
    "Successful pipeline runs",
    ["source", "pipeline", "branch"]
)
PIPELINE_FAILURE = Counter(
    "devopssense_pipeline_failure_total",
    "Failed pipeline runs",
    ["source", "pipeline", "branch"]
)

# durations
PIPELINE_DURATION = Histogram(
    "devopssense_pipeline_duration_seconds",
    "Pipeline duration in seconds",
    ["source", "pipeline", "branch"],
    buckets=(30, 60, 120, 300, 600, 1200, 1800, 3600)
)

# k8s pods (optional external updater)
K8S_PODS = Gauge(
    "devopssense_k8s_pods_running",
    "Count of running pods by namespace",
    ["namespace"]
)
