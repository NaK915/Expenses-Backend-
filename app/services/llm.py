from typing import Any

from langchain_huggingface import HuggingFaceHubEmbeddings, HuggingFacePipeline

from app.config import get_settings

settings = get_settings()


def get_embeddings() -> HuggingFaceHubEmbeddings:
    return HuggingFaceHubEmbeddings(
        repo_id=settings.hf_embeddings_model,
        task="feature-extraction",
        huggingfacehub_api_token=settings.hf_api_token,
    )


def get_llm() -> Any:
    return HuggingFacePipeline.from_model_id(
        model_id=settings.hf_model_name,
        task="text2text-generation",
        pipeline_kwargs={"tokenizer_kwargs": {"padding": True, "truncation": True}},
    )


def generate_text(prompt: str) -> str:
    llm = get_llm()
    return llm.invoke(prompt)
