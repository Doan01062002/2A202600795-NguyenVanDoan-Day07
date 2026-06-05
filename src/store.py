from __future__ import annotations

from typing import Any, Callable

from .chunking import _dot, compute_similarity
from .embeddings import _mock_embed
from .models import Document


class EmbeddingStore:
    """
    A vector store for text chunks.

    Tries to use ChromaDB if available; falls back to an in-memory store.
    The embedding_fn parameter allows injection of mock embeddings for tests.
    """

    def __init__(
        self,
        collection_name: str = "documents",
        embedding_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        self._embedding_fn = embedding_fn or _mock_embed
        self._collection_name = collection_name
        self._use_chroma = False
        self._store: list[dict[str, Any]] = []
        self._collection = None
        self._next_index = 0

        try:
            import chromadb
            self._chroma_client = chromadb.EphemeralClient()
            self._collection = self._chroma_client.get_or_create_collection(
                name=self._collection_name
            )
            self._use_chroma = True
        except Exception:
            self._use_chroma = False
            self._collection = None

    def _make_record(self, doc: Document) -> dict[str, Any]:
        embedding = self._embedding_fn(doc.content)
        metadata = dict(doc.metadata or {})
        if "doc_id" not in metadata:
            metadata["doc_id"] = doc.id
        return {
            "id": doc.id,
            "content": doc.content,
            "metadata": metadata,
            "embedding": embedding
        }

    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        query_embedding = self._embedding_fn(query)
        scored_records = []
        for r in records:
            score = compute_similarity(query_embedding, r["embedding"])
            scored_records.append({
                "id": r["id"],
                "content": r["content"],
                "metadata": r["metadata"],
                "score": score
            })
        scored_records.sort(key=lambda x: x["score"], reverse=True)
        return scored_records[:top_k]

    def add_documents(self, docs: list[Document]) -> None:
        """
        Embed each document's content and store it.

        For ChromaDB: use collection.add(ids=[...], documents=[...], embeddings=[...])
        For in-memory: append dicts to self._store
        """
        if self._use_chroma and self._collection is not None:
            ids = []
            documents = []
            embeddings = []
            metadatas = []
            for doc in docs:
                record = self._make_record(doc)
                ids.append(record["id"])
                documents.append(record["content"])
                embeddings.append(record["embedding"])
                metadatas.append(record["metadata"])
            if ids:
                self._collection.add(
                    ids=ids,
                    documents=documents,
                    embeddings=embeddings,
                    metadatas=metadatas
                )
        else:
            for doc in docs:
                record = self._make_record(doc)
                self._store.append(record)

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Find the top_k most similar documents to query.

        For in-memory: compute dot product of query embedding vs all stored embeddings.
        """
        if self._use_chroma and self._collection is not None:
            chroma_data = self._collection.get(include=["documents", "metadatas", "embeddings"])
            records = []
            for i in range(len(chroma_data["ids"])):
                records.append({
                    "id": chroma_data["ids"][i],
                    "content": chroma_data["documents"][i],
                    "metadata": chroma_data["metadatas"][i],
                    "embedding": chroma_data["embeddings"][i]
                })
            return self._search_records(query, records, top_k)
        else:
            return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        if self._use_chroma and self._collection is not None:
            return self._collection.count()
        return len(self._store)

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict = None) -> list[dict]:
        """
        Search with optional metadata pre-filtering.

        First filter stored chunks by metadata_filter, then run similarity search.
        """
        if self._use_chroma and self._collection is not None:
            chroma_data = self._collection.get(include=["documents", "metadatas", "embeddings"])
            records = []
            for i in range(len(chroma_data["ids"])):
                records.append({
                    "id": chroma_data["ids"][i],
                    "content": chroma_data["documents"][i],
                    "metadata": chroma_data["metadatas"][i],
                    "embedding": chroma_data["embeddings"][i]
                })
        else:
            records = self._store

        if metadata_filter:
            filtered_records = []
            for r in records:
                meta = r.get("metadata") or {}
                match = True
                for k, v in metadata_filter.items():
                    if meta.get(k) != v:
                        match = False
                        break
                if match:
                    filtered_records.append(r)
        else:
            filtered_records = records

        return self._search_records(query, filtered_records, top_k)

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.

        Returns True if any chunks were removed, False otherwise.
        """
        if self._use_chroma and self._collection is not None:
            results = self._collection.get()
            ids_to_delete = []
            for i in range(len(results["ids"])):
                cid = results["ids"][i]
                meta = results["metadatas"][i] or {}
                if cid == doc_id or meta.get("doc_id") == doc_id:
                    ids_to_delete.append(cid)
            if ids_to_delete:
                self._collection.delete(ids=ids_to_delete)
                return True
            return False
        else:
            initial_size = len(self._store)
            self._store = [
                r for r in self._store
                if r.get("id") != doc_id and r.get("metadata", {}).get("doc_id") != doc_id
            ]
            return len(self._store) < initial_size
