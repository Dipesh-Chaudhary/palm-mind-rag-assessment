from sqlmodel import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from qdrant_client import QdrantClient
from app.core.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)

async def get_db_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session

def get_qdrant_client() -> QdrantClient:
    return QdrantClient(url=settings.QDRANT_URL)