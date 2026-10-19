from typing import Annotated, Any, Dict, List, Literal, Optional
from typing_extensions import TypedDict
import operator


class Document(TypedDict, total=False):
    id: str
    content: str
    corpus: Literal["fatwa", "fiqih"]
    score: float
    metadata: Dict[str, Any]


class RAGState(TypedDict):
    # Query lifecycle
    query: str
    normalized_query: str
    rewritten_query: str
    route: Literal["fatwa", "fiqih", "keduanya", "di_luar_cakupan"]

    # Retrieval & Rerank
    retrieved_documents: Annotated[List[Document], operator.add]
    reranked_documents: List[Document]

    # Grader & CRAG Loop
    grade: Literal["relevan", "ambigu", "tidak_relevan"]
    retry_count: int

    # Generation & Evaluation
    generation: str
    raw_generation: Optional[str]
    citations: List[Dict[str, Any]]
    faithfulness_passed: bool
    faithfulness_explanation: Optional[str]
    abstain: bool
