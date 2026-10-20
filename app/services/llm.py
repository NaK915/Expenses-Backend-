import logging
from functools import lru_cache
from typing import Any, Dict, List

from langchain_huggingface import HuggingFaceEmbeddings
from transformers import pipeline

from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

EXPENSE_CATEGORIES = [
    "Food & drink",
    "Transport",
    "Stay",
    "Groceries",
    "Activities",
    "Shopping",
    "Bills & utilities",
    "Health",
    "Other",
]


def get_embeddings() -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(model_name=settings.hf_embeddings_model)


@lru_cache(maxsize=1)
def get_category_classifier() -> Any:
    """Load the zero-shot category model once and run it locally with Transformers."""
    return pipeline(
        task="zero-shot-classification",
        model=settings.hf_category_model,
        device=-1,
    )


def categorize_expense(name: str, description: str = "") -> str:
    text = name.strip()
    if description.strip():
        text = f"{text}. Description: {description.strip()}"

    try:
        result: Dict[str, Any] = get_category_classifier()(
            text,
            candidate_labels=EXPENSE_CATEGORIES,
            hypothesis_template="This expense is about {}.",
            multi_label=False,
        )
        labels: List[str] = result.get("labels", [])
        return labels[0] if labels and labels[0] in EXPENSE_CATEGORIES else "Other"
    except Exception:
        logger.exception("Local expense categorization failed")
        return "Other"
