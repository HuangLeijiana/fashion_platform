from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.models import ClothingItem, UserProfile


@dataclass(slots=True)
class RetrievedDocument:
    document_id: str
    title: str
    category: str
    content: str
    score: float
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class FashionKnowledgeBase:
    """Hybrid knowledge base with LangChain/Chroma and TF-IDF fallback."""

    def __init__(self, top_k: int = 3) -> None:
        self.top_k = top_k
        self._documents = self._load_documents()
        self._vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=3000)
        self._matrix = self._vectorizer.fit_transform([self._build_text(doc) for doc in self._documents])

    def search(self, query: str, top_k: int | None = None) -> list[RetrievedDocument]:
        if not query.strip():
            return []

        from flask import current_app

        use_langchain = current_app.config.get("FEATURE_ADVISOR_LANGCHAIN", False)
        use_vector = current_app.config.get("FEATURE_ADVISOR_RAG", True)

        if use_langchain:
            try:
                return self._search_langchain(query, top_k)
            except Exception:
                pass
        if use_vector:
            try:
                return self._search_vector(query, top_k)
            except Exception:
                pass
        return self._search_tfidf(query, top_k)

    def search_user_memory(self, user_id: str | None, query: str, top_k: int | None = None) -> list[RetrievedDocument]:
        if not user_id or not query.strip():
            return []

        from flask import current_app

        use_langchain = current_app.config.get("FEATURE_ADVISOR_LANGCHAIN", False)
        use_vector = current_app.config.get("FEATURE_ADVISOR_RAG", True)

        if use_langchain:
            try:
                return self._search_user_memory_langchain(user_id, query, top_k)
            except Exception:
                pass
        if use_vector:
            try:
                return self._search_user_memory_vector(user_id, query, top_k)
            except Exception:
                pass
        return self._search_user_memory_tfidf(user_id, query, top_k)

    def _search_langchain(self, query: str, top_k: int | None = None) -> list[RetrievedDocument]:
        from app.fashion_advisor.langchain_retriever import LangChainKnowledgeRetriever

        retriever = LangChainKnowledgeRetriever(collection_name="fashion_knowledge")
        return retriever.search(query, top_k=top_k or self.top_k)

    def _search_user_memory_langchain(self, user_id: str, query: str, top_k: int | None = None) -> list[RetrievedDocument]:
        from app.fashion_advisor.langchain_retriever import LangChainKnowledgeRetriever
        from app.services.vector_store import index_user_wardrobe

        index_user_wardrobe(user_id)
        retriever = LangChainKnowledgeRetriever(collection_name=f"user_memory_{user_id}")
        return retriever.search(query, top_k=top_k or self.top_k)

    def _search_vector(self, query: str, top_k: int | None = None) -> list[RetrievedDocument]:
        from app.services.vector_store import search_knowledge

        results = search_knowledge(query, top_k=top_k or self.top_k)
        return [self._from_mapping(item) for item in results]

    def _search_user_memory_vector(self, user_id: str, query: str, top_k: int | None = None) -> list[RetrievedDocument]:
        from app.services.vector_store import search_user_memory

        results = search_user_memory(user_id, query, top_k=top_k or self.top_k)
        return [self._from_mapping(item) for item in results]

    def _search_tfidf(self, query: str, top_k: int | None = None) -> list[RetrievedDocument]:
        size = top_k or self.top_k
        query_vector = self._vectorizer.transform([query])
        scores = cosine_similarity(query_vector, self._matrix)[0]
        ranked = sorted(enumerate(scores), key=lambda item: item[1], reverse=True)[:size]
        return [
            self._to_retrieved_document(self._documents[index], float(score))
            for index, score in ranked
            if score > 0
        ]

    def _search_user_memory_tfidf(self, user_id: str, query: str, top_k: int | None = None) -> list[RetrievedDocument]:
        documents = self._build_user_memory_documents(user_id)
        if not documents:
            return []

        vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=2000)
        matrix = vectorizer.fit_transform([self._build_text(doc) for doc in documents])
        query_vector = vectorizer.transform([query])
        scores = cosine_similarity(query_vector, matrix)[0]
        ranked = sorted(enumerate(scores), key=lambda item: item[1], reverse=True)[: (top_k or self.top_k)]
        return [
            self._to_retrieved_document(documents[index], float(score))
            for index, score in ranked
            if score > 0
        ]

    def _load_documents(self) -> list[dict[str, Any]]:
        data_path = Path(__file__).with_name("data") / "style_knowledge.json"
        with data_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    @staticmethod
    def _build_text(document: dict[str, Any]) -> str:
        tags = " ".join(document.get("tags", []))
        return " ".join(
            [
                str(document.get("title", "")),
                str(document.get("category", "")),
                tags,
                str(document.get("content", "")),
            ]
        ).strip()

    @staticmethod
    def _to_retrieved_document(document: dict[str, Any], score: float) -> RetrievedDocument:
        return RetrievedDocument(
            document_id=str(document.get("id", "")),
            title=str(document.get("title", "")),
            category=str(document.get("category", "")),
            content=str(document.get("content", "")),
            score=round(score, 4),
            tags=list(document.get("tags", [])),
            metadata=dict(document.get("metadata", {})),
        )

    @staticmethod
    def _from_mapping(item: dict[str, Any]) -> RetrievedDocument:
        return RetrievedDocument(
            document_id=str(item.get("document_id", "")),
            title=str(item.get("title", "")),
            category=str(item.get("category", "")),
            content=str(item.get("content", "")),
            score=float(item.get("score", 0.0)),
            tags=list(item.get("tags", [])),
            metadata=dict(item.get("metadata", {})),
        )

    def _build_user_memory_documents(self, user_id: str) -> list[dict[str, Any]]:
        documents: list[dict[str, Any]] = []

        profile = UserProfile.query.filter_by(user_id=user_id).first()
        if profile:
            profile_bits = [
                profile.username or "",
                profile.body_shape or "",
                profile.skin_tone or "",
                profile.gender or "",
                str(profile.height or ""),
                str(profile.weight or ""),
                str(profile.age or ""),
                profile.style_pref or "",
            ]
            documents.append(
                {
                    "id": f"profile-{user_id}",
                    "title": "用户风格偏好",
                    "category": "用户画像",
                    "tags": ["用户偏好", "风格", "画像"],
                    "content": "，".join([item for item in profile_bits if item]),
                    "metadata": {"type": "profile"},
                }
            )

        items = (
            ClothingItem.query.filter_by(user_id=user_id)
            .order_by(ClothingItem.created_at.desc())
            .limit(40)
            .all()
        )
        for item in items:
            parts = [
                item.name or "",
                item.category or "",
                item.color or "",
                item.brand or "",
                item.season or "",
                item.occasion or "",
                item.material or "",
                item.style_tags or "",
            ]
            documents.append(
                {
                    "id": f"wardrobe-{item.id}",
                    "title": item.name or "衣橱单品",
                    "category": item.category or "衣橱",
                    "tags": ["衣橱", "历史偏好", item.color or "", item.occasion or ""],
                    "content": "，".join([value for value in parts if value]),
                    "metadata": {
                        "type": "wardrobe_item",
                        "item_id": item.id,
                        "image_path": item.image_path,
                    },
                }
            )

        return documents