from typing import Any, Dict, List, Literal, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from sentence_transformers import SentenceTransformer
from src.config import settings
from src.state import Document


class DenseRetriever:
    def __init__(
        self,
        model_name: Optional[str] = None,
        client: Optional[QdrantClient] = None,
    ):
        self.model_name = model_name or settings.embedding_model_name
        self._model: Optional[SentenceTransformer] = None

        if client is not None:
            self.client = client
        elif settings.use_local_qdrant:
            self.client = QdrantClient(path=settings.qdrant_local_path)
        else:
            self.client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)

    @property
    def model(self) -> SentenceTransformer:
        if self._model is None:
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def ensure_collection(self, collection_name: str, vector_size: int = 1024):
        collections = [c.name for c in self.client.get_collections().collections]
        if collection_name not in collections:
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
            )

    def embed_texts(
        self,
        texts: List[str],
        batch_size: int = 32,
        show_progress_bar: bool = False,
    ) -> List[List[float]]:
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress_bar,
            normalize_embeddings=True,
        )
        return embeddings.tolist()

    def search(
        self,
        collection_name: str,
        query: str,
        corpus: Literal["fatwa", "fiqih"],
        top_k: int = 15,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Document]:
        """Search embedding dense di koleksi Qdrant."""
        query_vector = self.embed_texts([query])[0]

        qdrant_filter = None
        if filters:
            conditions = [
                FieldCondition(key=k, match=MatchValue(value=v))
                for k, v in filters.items()
            ]
            qdrant_filter = Filter(must=conditions)

        # Kompatibilitas qdrant-client modern (query_points) vs legacy (search)
        if hasattr(self.client, "query_points"):
            response = self.client.query_points(
                collection_name=collection_name,
                query=query_vector,
                query_filter=qdrant_filter,
                limit=top_k,
            )
            hits = response.points
        else:
            hits = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                query_filter=qdrant_filter,
                limit=top_k,
            )

        documents: List[Document] = []
        for hit in hits:
            payload = hit.payload or {}
            documents.append(
                Document(
                    id=str(payload.get("doc_id") or hit.id),
                    content=payload.get("content", ""),
                    corpus=corpus,
                    score=float(hit.score),
                    metadata=payload.get("metadata", {}),
                )
            )
        return documents
