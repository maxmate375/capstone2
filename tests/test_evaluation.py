import pytest

from src.evaluation.evaluate import answer_metrics, compare_baseline_and_agentic


def test_metrics_are_bounded_and_capture_relevance():
    metrics = answer_metrics(
        "Antibiotics do not work for viral colds.",
        "Antibiotics do not treat viral colds.",
        "Antibiotics do not treat infections caused by viruses.",
    )

    assert metrics["bleu"] > 0
    assert metrics["rouge_l"] > 0
    assert metrics["relevance"] > 0.5


def test_comparison_requires_evaluation_rows():
    with pytest.raises(ValueError, match="At least one"):
        compare_baseline_and_agentic([])
