import json

from src.config import get_settings
from src.evaluation.evaluate import compare_baseline_and_agentic
from src.service import build_assistant


def main() -> None:
    settings = get_settings()
    assistant = build_assistant(settings)
    rows = []
    with (settings.knowledge_base_path.parent / "evaluation_set.jsonl").open(
        encoding="utf-8"
    ) as evaluation_file:
        for line in evaluation_file:
            item = json.loads(line)
            baseline_answer, baseline_context = assistant.baseline_answer(
                item["query"]
            )
            result = assistant.query(item["query"], f"evaluation-{len(rows)}")
            rows.append(
                {
                    **item,
                    "baseline_answer": baseline_answer,
                    "baseline_context": "\n".join(baseline_context),
                    "agentic_answer": result["answer"],
                    "agentic_context": "\n".join(result["retrieved_context"]),
                }
            )

    comparison = compare_baseline_and_agentic(rows)
    print(json.dumps(comparison, indent=2))


if __name__ == "__main__":
    main()
