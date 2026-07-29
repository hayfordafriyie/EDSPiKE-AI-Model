from prometheus_client import Counter, Gauge, Histogram

REQUESTS = Counter("EDSPiKE_requests_total", "API requests", ["endpoint", "status"])
TOKENS = Counter("EDSPiKE_tokens_total", "Generated tokens")
LATENCY = Histogram(
    "EDSPiKE_latency_seconds", "Inference latency",
    buckets=(0.01, 0.05, 0.1, 0.2, 0.5, 1, 2, 5, 10, 30),
)
THROUGHPUT = Gauge("EDSPiKE_throughput_tokens_per_second", "Last request throughput")
MODEL_READY = Gauge("edspike_agent_ready", "Whether the inference agent is ready")

