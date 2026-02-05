from src.evaluation.metrics import EvaluationMetrics


def test_exact_match_is_case_insensitive():
    assert EvaluationMetrics.exact_match(["WAEC"], ["waec"]) == 1


def test_token_f1():
    assert 0 < EvaluationMetrics.token_f1(["Ghana education service"], ["education service"]) < 1


def test_education_metrics():
    result = EvaluationMetrics.education_specific(["GES curriculum assessment"])
    assert result["curriculum_alignment"] == 1

