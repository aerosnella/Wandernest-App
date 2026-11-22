"""Azure OpenAI embeddings / chat model and the Azure AI Search vector store (LangChain)."""
from __future__ import annotations

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from langchain_community.vectorstores.azuresearch import AzureSearch
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings

from config import Config


def get_embeddings(cfg: Config) -> AzureOpenAIEmbeddings:
    return AzureOpenAIEmbeddings(
        azure_deployment=cfg.embedding_deployment,
        azure_endpoint=cfg.openai_endpoint,
        api_key=cfg.openai_api_key,
        api_version=cfg.openai_api_version,
    )


def get_llm(cfg: Config, temperature: float = 0.0) -> AzureChatOpenAI:
    return AzureChatOpenAI(
        azure_deployment=cfg.chat_deployment,
        azure_endpoint=cfg.openai_endpoint,
        api_key=cfg.openai_api_key,
        api_version=cfg.openai_api_version,
        temperature=temperature,
    )


def get_vector_store(cfg: Config, embeddings: AzureOpenAIEmbeddings | None = None) -> AzureSearch:
    """Return the LangChain AzureSearch store; the index is created on first use if missing."""
    embeddings = embeddings or get_embeddings(cfg)
    return AzureSearch(
        azure_search_endpoint=cfg.search_endpoint,
        azure_search_key=cfg.search_key,
        index_name=cfg.search_index_name,
        embedding_function=embeddings,
    )


def get_search_client(cfg: Config) -> SearchClient:
    return SearchClient(cfg.search_endpoint, cfg.search_index_name, AzureKeyCredential(cfg.search_key))


def get_index_client(cfg: Config) -> SearchIndexClient:
    return SearchIndexClient(cfg.search_endpoint, AzureKeyCredential(cfg.search_key))
