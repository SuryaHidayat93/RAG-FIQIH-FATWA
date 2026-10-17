from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    primary_model: str = "llama3.1:8b"
    comparison_model: str = "qwen2.5:7b"

    # Embedding & Reranker
    embedding_model_name: str = "BAAI/bge-m3"
    reranker_model_name: str = "BAAI/bge-reranker-v2-m3"

    # Qdrant
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_local_path: str = "./data/qdrant_storage"
    use_local_qdrant: bool = True

    # Search parameters
    dense_top_k: int = 15
    bm25_top_k: int = 15
    rerank_top_k: int = 5
    rrf_k: int = 60
    max_crag_retries: int = 1

    # App
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    streamlit_port: int = 8501


settings = Settings()
