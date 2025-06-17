from fastapi import APIRouter
from app.api.endpoints import ingestion, chat

api_router = APIRouter()
api_router.include_router(ingestion.router, prefix="/documents", tags=["Document Ingestion"])

api_router.include_router(chat.router, prefix="/chat", tags=["RAG Agent"])