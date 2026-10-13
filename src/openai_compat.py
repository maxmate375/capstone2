from urllib.parse import urlsplit


def is_openai_v1_endpoint(endpoint: str) -> bool:
    return urlsplit(endpoint.rstrip("/")).path.rstrip("/").endswith(
        "/openai/v1"
    )


def normalize_openai_v1_endpoint(endpoint: str) -> str:
    return endpoint.rstrip("/") + "/"
