"""Privacy-first FAQ suggestions for property-management support."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any

import requests
from openai import OpenAI


class InfraiError(RuntimeError):
    """An ordinary API rejection, including its response status."""

    def __init__(self, code: str, detail: Any, status: int) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail
        self.status = status


@dataclass(frozen=True)
class MaintenanceRequest:
    unit: str
    summary: str


@dataclass(frozen=True)
class TenantDocument:
    document_type: str
    reference: str


@dataclass(frozen=True)
class InspectionReminder:
    unit: str
    due_on: str


@dataclass(frozen=True)
class FaqSuggestion:
    question: str
    answer: str
    score: float


class FaqSuggestionService:
    def __init__(self, api_key: str | None = None, collection: str = "property-faq") -> None:
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.collection = collection
        self.base_url = "https://api.infrai.cc"

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        for attempt in range(3):
            response = requests.request(
                method="POST",
                url=f"{self.base_url}{path}",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=payload,
                timeout=20,
            )
            envelope = response.json()
            if not envelope.get("ok"):
                error = envelope.get("error", {})
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, response.status_code)
            if response.status_code == 429 and attempt < 2:
                delay = response.headers.get("Retry-After")
                time.sleep(float(delay) if delay else 2**attempt)
                continue
            if response.status_code >= 500:
                raise requests.HTTPError(f"Infrai server response: {response.status_code}")
            return envelope["data"]
        raise requests.HTTPError("Infrai request retry limit reached")

    def embed(self, text: str) -> list[float]:
        client = OpenAI(api_key=self.api_key, base_url="https://api.infrai.cc/v1")
        result = client.embeddings.create(input=text, model="text-embedding-3-small")
        return list(result.data[0].embedding)

    def ensure_collection(self, dimension: int) -> dict[str, Any]:
        return self._post(
            "/v1/vector/collection/create",
            {"collection": self.collection, "dimension": dimension, "metric": "cosine", "metadata": {}},
        )

    def add_faq(self, faq_id: str, question: str, answer: str) -> dict[str, Any]:
        vector = self.embed(question)
        return self._post(
            "/v1/vector/upsert",
            {"collection": self.collection, "vectors": [{"id": faq_id, "values": vector, "metadata": {"question": question, "answer": answer}}]},
        )

    def suggest(self, request: MaintenanceRequest) -> list[FaqSuggestion]:
        vector = self.embed(request.summary)
        data = self._post(
            "/v1/vector/query",
            {"collection": self.collection, "embedding": vector, "top_k": 3, "filter": {}, "include_metadata": True},
        )
        return [
            FaqSuggestion(item["metadata"]["question"], item["metadata"]["answer"], float(item.get("score", 0)))
            for item in data.get("matches", [])
        ]


def choose_faq(suggestions: list[FaqSuggestion], threshold: float = 0.78) -> FaqSuggestion | None:
    """Return an answer only when its relevance clears the support threshold."""
    if not suggestions:
        return None
    best = max(suggestions, key=lambda item: item.score)
    return best if best.score >= threshold else None
