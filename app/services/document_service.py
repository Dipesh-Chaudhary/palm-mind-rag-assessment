import tempfile
import os
from langchain_community.document_loaders.docling import DoclingLoader
from langchain_community.document_loaders import TextLoader
from langchain_experimental.text_splitter import SemanticChunker
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_qdrant import Qdrant
from sqlmodel import AsyncSession
from app.models.schemas import IngestionMetadata
from app.core.config import settings

async def process_document(
    db: AsyncSession,
    file_content: bytes,
    file_name: str,
    chunking_strategy: str,
    embedding_model_name: str
):
    # Use a temporary file to leverage LangChain loaders effectively
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file_name)[1]) as tmp_file:
        tmp_file.write(file_content)
        tmp_file_path = tmp_file.name

    try:
        if file_name.lower().endswith(".pdf"):
            loader = DoclingLoader(tmp_file_path)
        elif file_name.lower().endswith(".txt"):
            loader = TextLoader(tmp_file_path, encoding='utf-8')
        else:
            raise ValueError(f"Unsupported file type: {os.path.splitext(file_name)[1]}")
        docs = loader.load()
    finally:
        os.remove(tmp_file_path)

    if embedding_model_name == "google":
        embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004", google_api_key=settings.GOOGLE_API_KEY)
    elif embedding_model_name == "bge":
        embeddings = HuggingFaceBgeEmbeddings(model_name="BAAI/bge-small-en-v1.5", encode_kwargs={'normalize_embeddings': True})
    else:
        raise ValueError("Unsupported embedding model")

    if chunking_strategy == "semantic":
        text_splitter = SemanticChunker(embeddings, breakpoint_threshold_type="percentile")
    elif chunking_strategy == "recursive":
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    else:
        raise ValueError("Unsupported chunking strategy")

    chunks = text_splitter.split_documents(docs)
    for i, chunk in enumerate(chunks):
        chunk.metadata["chunk_index"] = i
        chunk.metadata["file_name"] = file_name


    await Qdrant.from_documents(
        chunks,
        embeddings,
        url=settings.QDRANT_URL,
        collection_name=settings.QDRANT_COLLECTION_NAME,
        force_recreate=False,
    )

    metadata_record = IngestionMetadata(
        file_name=file_name,
        chunking_strategy=chunking_strategy,
        embedding_model=embedding_model_name,
        chunk_count=len(chunks)
    )
    db.add(metadata_record)
    await db.commit()
    await db.refresh(metadata_record)

    return metadata_record