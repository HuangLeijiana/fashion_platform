from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

_EMBEDDING_MODEL_NAME = "shibing624/text2vec-base-chinese"
_COLLECTION_KNOWLEDGE = "fashion_knowledge"
_COLLECTION_USER_MEMORY = "user_memory"

_embedding_model: SentenceTransformer | None = None
_chroma_client: chromadb.ClientAPI | None = None


def _get_embedding_model() -> SentenceTransformer:
    global _embedding_model
    if _embedding_model is None:
        cache_dir = os.environ.get(
            "SENTENCE_TRANSFORMERS_HOME",
            os.path.join(os.path.dirname(__file__), "..", "models", "text2vec"),
        )
        _embedding_model = SentenceTransformer(_EMBEDDING_MODEL_NAME, cache_folder=cache_dir)
        logger.info("Embedding model loaded: %s", _EMBEDDING_MODEL_NAME)
    return _embedding_model


def _get_chroma_client() -> chromadb.ClientAPI:
    global _chroma_client
    if _chroma_client is None:
        persist_dir = os.environ.get(
            "CHROMA_PERSIST_DIR",
            os.path.join(os.path.dirname(__file__), "..", "..", "chroma_data"),
        )
        os.makedirs(persist_dir, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(
            path=persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        logger.info("ChromaDB client initialized at %s", persist_dir)
    return _chroma_client


def embed_texts(texts: list[str]) -> list[list[float]]:
    model = _get_embedding_model()
    embeddings = model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
    return embeddings.tolist()


def embed_single(text: str) -> list[float]:
    return embed_texts([text])[0]


def get_knowledge_collection():
    client = _get_chroma_client()
    return client.get_or_create_collection(
        name=_COLLECTION_KNOWLEDGE,
        metadata={"hnsw:space": "cosine"},
    )


def get_user_memory_collection(user_id: str):
    client = _get_chroma_client()
    return client.get_or_create_collection(
        name=f"{_COLLECTION_USER_MEMORY}_{user_id}",
        metadata={"hnsw:space": "cosine"},
    )


def index_knowledge_base(force: bool = False) -> int:
    data_path = Path(__file__).resolve().parent.parent / "fashion_advisor" / "data" / "style_knowledge.json"
    if not data_path.exists():
        logger.warning("Knowledge base data not found: %s", data_path)
        return 0

    with data_path.open("r", encoding="utf-8") as f:
        documents = json.load(f)

    collection = get_knowledge_collection()
    if force and collection.count() > 0:
        collection.delete(ids=collection.get().get("ids", []))

    existing_ids = set(collection.get().get("ids", [])) if collection.count() > 0 else set()
    new_docs = documents if force else [d for d in documents if str(d.get("id", "")) not in existing_ids]
    if not new_docs:
        return collection.count()

    ids = [str(d.get("id", f"doc_{idx}")) for idx, d in enumerate(new_docs)]
    texts = []
    metadatas = []
    for doc in new_docs:
        text = " ".join(
            [
                str(doc.get("title", "")),
                str(doc.get("category", "")),
                " ".join(doc.get("tags", [])),
                str(doc.get("content", "")),
            ]
        ).strip()
        texts.append(text)
        metadatas.append(
            {
                "title": str(doc.get("title", "")),
                "category": str(doc.get("category", "")),
                "tags": json.dumps(doc.get("tags", []), ensure_ascii=False),
            }
        )

    collection.upsert(ids=ids, documents=texts, embeddings=embed_texts(texts), metadatas=metadatas)
    logger.info("Indexed %d knowledge documents into ChromaDB.", len(new_docs))
    return collection.count()


def index_user_wardrobe(user_id: str) -> int:
    from app.models import ClothingItem, UserProfile

    collection = get_user_memory_collection(user_id)
    if collection.count() > 0:
        collection.delete(ids=collection.get().get("ids", []))

    ids: list[str] = []
    texts: list[str] = []
    metadatas: list[dict[str, Any]] = []

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
        profile_text = "，".join([bit for bit in profile_bits if bit])
        if profile_text:
            ids.append(f"profile-{user_id}")
            texts.append(profile_text)
            metadatas.append(
                {
                    "type": "profile",
                    "title": "用户风格偏好",
                    "name": profile.username or "用户画像",
                    "category": "用户画像",
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
        text = " ".join([value for value in parts if value]).strip()
        if not text:
            continue
        ids.append(f"wardrobe-{item.id}")
        texts.append(text)
        metadatas.append(
            {
                "type": "wardrobe_item",
                "item_id": str(item.id),
                "title": item.name or "衣橱单品",
                "name": item.name or "衣橱单品",
                "category": item.category or "衣橱",
                "color": item.color or "",
                "image_path": item.image_path or "",
            }
        )

    if not texts:
        return 0

    collection.upsert(ids=ids, documents=texts, embeddings=embed_texts(texts), metadatas=metadatas)
    logger.info("Indexed %d user-memory documents for user %s.", len(texts), user_id)
    return len(texts)


def search_knowledge(query: str, top_k: int = 3) -> list[dict[str, Any]]:
    collection = get_knowledge_collection()
    if collection.count() == 0:
        index_knowledge_base()
    if collection.count() == 0:
        return []

    results = collection.query(
        query_embeddings=[embed_single(query)],
        n_results=min(top_k, collection.count()),
        include=["documents", "metadatas", "distances"],
    )
    return _normalize_results(results)


def search_user_memory(user_id: str, query: str, top_k: int = 3) -> list[dict[str, Any]]:
    collection = get_user_memory_collection(user_id)
    if collection.count() == 0:
        index_user_wardrobe(user_id)
    if collection.count() == 0:
        return []

    results = collection.query(
        query_embeddings=[embed_single(query)],
        n_results=min(top_k, collection.count()),
        include=["documents", "metadatas", "distances"],
    )
    return _normalize_results(results)


def _normalize_results(results: dict[str, Any]) -> list[dict[str, Any]]:
    ids_list = results.get("ids", [[]])[0]
    docs_list = results.get("documents", [[]])[0]
    metas_list = results.get("metadatas", [[]])[0]
    dists_list = results.get("distances", [[]])[0]

    output: list[dict[str, Any]] = []
    for doc_id, doc, meta, dist in zip(ids_list, docs_list, metas_list, dists_list):
        tags_raw = meta.get("tags", "[]")
        try:
            tags = json.loads(tags_raw)
        except (TypeError, json.JSONDecodeError):
            tags = []
        output.append(
            {
                "document_id": doc_id,
                "title": meta.get("title", meta.get("name", "")),
                "category": meta.get("category", ""),
                "content": doc or "",
                "score": round(1.0 - float(dist), 4),
                "tags": tags,
                "metadata": {k: v for k, v in meta.items() if k != "tags"},
            }
        )
    return output