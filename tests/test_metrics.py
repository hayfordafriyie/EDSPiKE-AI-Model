from src.evaluation.metrics import EvaluationMetrics


def test_exact_match_is_case_insensitive():
    assert EvaluationMetrics.exact_match(["Policy"], ["policy"]) == 1


def test_token_f1():
    assert 0 < EvaluationMetrics.token_f1(["customer service policy"], ["service policy"]) < 1


def test_domain_metrics():
    result = EvaluationMetrics.domain_specific(["Our return policy is 30 days"])
    assert result["domain_relevance"] == 1

