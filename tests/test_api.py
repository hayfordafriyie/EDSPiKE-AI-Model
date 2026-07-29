import os

os.environ["SKIP_MODEL_LOAD"] = "true"
os.environ["EDSPIKE_API_KEY"] = ""
os.environ["MAX_BATCH_SIZE"] = "64"

from fastapi.testclient import TestClient

from src.deployment.inference_server import app


class FakeEngine:
    model_name = "test-model"

    def generate_batch(self, prompts, max_tokens, temperature, top_p):
        return [f"Answer: {prompt}" for prompt in prompts], [3 for _ in prompts]


def test_health_and_single_generation():
    with TestClient(app) as client:
        assert client.get("/health").status_code == 503
        app.state.engine = FakeEngine()
        assert client.get("/health").json()["status"] == "ready"
        response = client.post("/v1/generate", json={"prompt": "What is our return policy?"})
        assert response.status_code == 200
        assert response.json()["model"] == "test-model"


def test_batch_generation():
    with TestClient(app) as client:
        app.state.engine = FakeEngine()
        response = client.post("/v1/generate", json={"prompts": ["Q1?", "Q2?"], "num_agents": 1})
        assert response.status_code == 200
        assert len(response.json()["responses"]) == 2


def test_batch_validation():
    with TestClient(app) as client:
        app.state.engine = FakeEngine()
        assert client.post("/v1/generate", json={"prompts": [], "num_agents": 1}).status_code == 422
