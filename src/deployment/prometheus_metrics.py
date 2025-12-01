from prometheus_client import Counter, Gauge, Histogram

REQUESTS = Counter("edspike_requests_total", "API requests", ["endpoint", "status"])
TOKENS = Counter("edspike_tokens_total", "Generated tokens")
LATENCY = Histogram(
    "edspike_latency_seconds", "Inference latency",
    buckets=(0.01, 0.05, 0.1, 0.2, 0.5, 1, 2, 5, 10, 30),
)
THROUGHPUT = Gauge("edspike_throughput_tokens_per_second", "Last request throughput")
MODEL_READY = Gauge("edspike_model_ready", "Whether the inference model is loaded")

