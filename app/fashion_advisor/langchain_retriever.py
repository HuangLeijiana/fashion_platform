from __future__ import annotations

import json
import os
from typing import Any

from app.fashion_advisor.knowledge_base import RetrievedDocument


class LangChainKnowledgeRetriever:
    """Optional LangChain-based retriever built on the same Chroma store."""

    def __init__(
        self,
        *,
        collection_name: str,
        persist_directory: str | None = None,
        model_name: str = "shibing624/text2vec-base-chinese",
    ) -> None:
        self.collection_name = collection_name
        self.persist_directory = persist_directory or os.environ.get(
            "CHROMA_PERSIST_DIR",
            os.path.join(os.path.dirname(__file__), "..", "..", "chroma_data"),
        )
        self.model_name = model_name

    def search(self, query: str, top_k: int = 3) -> list[RetrievedDocument]:
        from langchain_community.vectorstores import Chroma
        from langchain_huggingface import HuggingFaceEmbeddings

        embeddings = HuggingFaceEmbeddings(
            model_name=self.model_name,
            cache_folder=os.environ.get(
                "SENTENCE_TRANSFORMERS_HOME",
                os.path.join(os.path.dirname(__file__), "..", "models", "text2vec"),
            ),
            encode_kwargs={"normalize_embeddings": True},
        )
        vectorstore = Chroma(
            collection_name=self.collection_name,
            persist_directory=self.persist_directory,
            embedding_function=embeddings,
        )
        pairs = vectorstore.similarity_search_with_relevance_scores(query, k=top_k)

        results: list[RetrievedDocument] = []
        for index, (document, score) in enumerate(pairs, start=1):
            metadata: dict[str, Any] = dict(document.metadata or {})
            tags_raw = metadata.get("tags", "[]")
            try:
                tags = json.loads(tags_raw) if isinstance(tags_raw, str) else list(tags_raw)
            except (TypeError, json.JSONDecodeError):
                tags = []
            results.append(
                RetrievedDocument(
                    document_id=str(metadata.get("id", metadata.get("item_id", f"doc-{index}"))),
                    title=str(metadata.get("title", metadata.get("name", ""))),
                    category=str(metadata.get("category", "")),
                    content=document.page_content,
                    score=round(float(score), 4),
                    tags=tags,
                    metadata=metadata,
                )
            )
        return results