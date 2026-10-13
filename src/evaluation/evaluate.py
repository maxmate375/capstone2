from collections import Counter

from nltk.translate.bleu_score import SmoothingFunction, sentence_bleu
from rouge_score import rouge_scorer

_ROUGE = rouge_scorer.RougeScorer(["rougeL"], use_stemmer=True)


def _tokens(text: str) -> list[str]:
    return [token.casefold() for token in text.split() if token.strip()]


def relevance_score(context: str, reference: str) -> float:
    context_tokens = set(_tokens(context))
    reference_tokens = set(_tokens(reference))
    if not reference_tokens:
        return 0.0
    return len(context_tokens & reference_tokens) / len(reference_tokens)


def answer_metrics(answer: str, reference: str, context: str) -> dict[str, float]:
    answer_tokens = _tokens(answer)
    reference_tokens = _tokens(reference)
    bleu = (
        sentence_bleu(
            [reference_tokens],
            answer_tokens,
            smoothing_function=SmoothingFunction().method1,
        )
        if answer_tokens and reference_tokens
        else 0.0
    )
    rouge_l = _ROUGE.score(reference, answer)["rougeL"].fmeasure
    return {
        "bleu": float(bleu),
        "rouge_l": float(rouge_l),
        "relevance": relevance_score(context, reference),
    }


def compare_baseline_and_agentic(
    rows: list[dict[str, str]],
) -> dict[str, dict[str, float]]:
    if not rows:
        raise ValueError("At least one evaluation row is required.")

    totals: dict[str, Counter[str]] = {
        "baseline": Counter(),
        "agentic": Counter(),
    }
    for row in rows:
        for variant, variant_totals in totals.items():
            metrics = answer_metrics(
                row[f"{variant}_answer"],
                row["reference"],
                row[f"{variant}_context"],
            )
            variant_totals.update(metrics)

    return {
        variant: {metric: total / len(rows) for metric, total in values.items()}
        for variant, values in totals.items()
    }
