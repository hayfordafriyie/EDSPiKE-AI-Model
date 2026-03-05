import argparse
import statistics
import time

import httpx


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:8000")
    parser.add_argument("--api-key", default="")
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--runs", type=int, default=3)
    args = parser.parse_args()
    headers = {"Authorization": f"Bearer {args.api_key}"} if args.api_key else {}
    rates, latencies = [], []
    with httpx.Client(timeout=300) as client:
        for _ in range(args.runs):
            started = time.perf_counter()
            response = client.post(
                f"{args.url}/v1/generate-batch", headers=headers,
                json={"prompts": ["Explain WAEC in Ghana."] * args.batch_size, "max_tokens": 128},
            )
            response.raise_for_status()
            elapsed = time.perf_counter() - started
            rates.append(response.json()["throughput_tokens_per_second"])
            latencies.append(elapsed)
    print(f"throughput mean={statistics.mean(rates):.2f} tok/s")
    print(f"batch latency p50={statistics.median(latencies) * 1000:.2f} ms")


if __name__ == "__main__":
    main()
