# Bharat Scheme Saathi

An India central-government scheme eligibility assistant built with a modular
`src/` layout, following the Python project style in the ML repository. The
application combines a real public MyScheme-derived dataset, FAISS semantic
search, BM25 keyword retrieval, LangGraph agents, FastAPI, and a Streamlit chat
interface.

Eligibility suggestions are preliminary information only. They are not an
official eligibility decision, application, or approval. Always verify current
rules and deadlines on the linked MyScheme or ministry website.

## Public data

The corpus includes **526 central-government scheme records** filtered from a
2,066-record public MyScheme dataset snapshot. It keeps records with eligibility
criteria and a canonical MyScheme source link; state/UT schemes are excluded.
Each record contains the source title, scheme level, ministry, description,
eligibility criteria, exclusions, benefits, application steps, documents, FAQs,
and links where available.

Dataset attribution and snapshot metadata are in
[`data/source_info.json`](data/source_info.json). Upstream dataset:
[Indian Government MyScheme Dataset](https://github.com/Aryan-Pardeshi/gov-myscheme-dataset),
CSV file pinned to commit
[`4ddfa18`](https://github.com/Aryan-Pardeshi/gov-myscheme-dataset/tree/4ddfa18d7aa3e630cc4ae3374731e5819d7875e7).
Its README attributes the data to the official
[MyScheme portal](https://www.myscheme.gov.in/) and the
[Hugging Face `gov_myscheme` dataset](https://huggingface.co/datasets/shrijayan/gov_myscheme),
and states an Apache-2.0 license. This app filters central-government entries
and preserves their MyScheme links. Records are a dataset snapshot and may be
out of date; users should confirm facts with the official scheme source.

## Project structure

```text
government_scheme_eligibility_assistant/
├── api/                       # FastAPI routes and Pydantic schemas
├── data/
│   ├── central_schemes.jsonl  # 526 central government schemes
│   ├── evaluation_set.jsonl   # Questions derived from scheme records
│   └── source_info.json       # Dataset source, version and attribution
├── src/
│   ├── agents/workflow.py    # Planner, RAG, eligibility specialist, validator
│   ├── evaluation/           # BLEU, ROUGE-L, relevance and comparison runner
│   ├── ingestion/            # Dataset loading, chunking and FAISS creation
│   ├── retrieval/            # FAISS + BM25 hybrid search
│   ├── tools/                # Feedback persistence
│   ├── config.py
│   └── service.py
├── tests/
├── .github/workflows/        # Test and lint checks
├── docs/                     # Capstone report
├── .streamlit/config.toml     # Clean, minimal Streamlit toolbar
├── .env.example
├── main.py                    # Streamlit UI
├── requirements.txt
└── requirements-dev.txt
```

## Agents and eligibility workflow

1. **Planner** routes scheme information questions and profile-based eligibility
   requests.
2. **Retriever** calls a reusable `rag_search` tool. FAISS semantic matches and
   BM25 keyword matches are fused using reciprocal-rank fusion.
3. **Eligibility assessment agent** is invoked for profile-based questions. It
   compares supplied profile details against retrieved criteria and labels
   results `potential_match`, `needs_more_information`, or `may_not_match`.
   Missing and matched criteria are shown explicitly.
4. **Consultation agent** explains scheme benefits, documents, and application
   steps using retrieved evidence only.
5. **Validator** checks the answer against the retrieved scheme records. If
   grounding fails, the graph rewrites the search and increases top-k before
   trying again; after the retry limit it returns a safe no-evidence response.
6. **Feedback endpoint** stores a thumbs-up/down rating and optional correction
   in SQLite. Profile data is not included in feedback records.

User profile details are optional. They are passed to the workflow only for the
current query and are cleared from the graph's checkpoint at the end of that
turn. Do not enter Aadhaar numbers, bank details, or other sensitive identifiers.

## Setup and run

Requires Python 3.11+ and an Azure OpenAI-compatible endpoint with deployed
chat and embedding models.

```powershell
cd D:\ML\CAPSTONE\second\government_scheme_eligibility_assistant
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
Copy-Item .env.example .env
```

Set `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`,
`AZURE_OPENAI_CHAT_DEPLOYMENT`, and `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` in
`.env`, then build the local FAISS index. Deployment settings must be the
deployment names configured in Azure, not necessarily the underlying model
names. For the Azure OpenAI v1 API, set the endpoint to
`https://<resource-name>.openai.azure.com/openai/v1/`; the app uses the
OpenAI-compatible API for that endpoint, and `AZURE_OPENAI_API_VERSION` is
ignored. For the older Azure OpenAI API, use the resource endpoint
`https://<resource-name>.openai.azure.com/`; `AZURE_OPENAI_API_VERSION`
defaults to `2024-10-21`. The chat and embedding deployments must exist on the
same endpoint, and the embedding deployment must support embeddings. The FAISS
index must be rebuilt whenever changing the embedding deployment. The app
combines vector matches with BM25 keyword search:

On Windows, the application uses the Windows certificate store for HTTPS
verification.

```powershell
python -m src.ingestion.prepare_dataset
python -m src.ingestion.build_index
```

The checked-in scheme data is already prepared. `prepare_dataset` re-downloads
the pinned public snapshot, verifies its content hash, and regenerates the
central-scheme records and attribution file.

Run the FastAPI service and Streamlit UI in two terminals:

```powershell
uvicorn api.main:app --reload
streamlit run main.py
```

Open the Streamlit app at `http://localhost:8501`; FastAPI Swagger docs are at
`http://localhost:8000/docs`. The UI is designed for desktop and mobile widths,
with an optional profile form, suggested questions, chat history, preliminary
match cards, official source links, feedback, and an expandable agent trace.

## API

`POST /query`

```json
{
  "session_id": "optional-session-id",
  "query": "Which central schemes might I qualify for?",
  "profile": {
    "age": 28,
    "state": "Maharashtra",
    "annual_household_income": 240000,
    "is_farmer": true
  }
}
```

The profile is optional. A response contains the answer, `eligibility_matches`,
source links, retrieved context, agent trace, and grounding confidence. A
potential match is only a suggestion to check the linked official page.

`POST /feedback` accepts `session_id`, `query`, a `rating` of `1` or `-1`, and an
optional correction. Feedback is stored in `data/feedback.sqlite3`.

## Evaluation

The small review set in `data/evaluation_set.jsonl` uses eligibility excerpts
from the included dataset. The runner compares basic top-k RAG with the agentic
workflow using corpus BLEU, ROUGE-L F1, and reference-token context relevance:

```powershell
python -m src.evaluation.run_evaluation
```

Evaluation requires a configured API key and built index. This is a smoke
benchmark, not an official policy or eligibility audit; expand it with
human-reviewed questions and answers before drawing quality conclusions.

## Tests and quality checks

```powershell
ruff check api src tests main.py
pytest -q
```

GitHub Actions runs lint and unit/API tests for pushes and pull requests.

## Safety and data limitations

- Eligibility labels are generated guidance, not eligibility determinations.
- Scheme criteria, benefit amounts, and application routes can change.
- Confirm all information on the linked MyScheme and ministry pages.
- Profile details are used for assessment but are not written to feedback storage.
- Never enter government IDs, financial account details, or sensitive documents.
- The local FAISS index is trusted local data because its loader uses Python
  pickle deserialization; do not load an index from an untrusted source.
