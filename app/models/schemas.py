from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class IngestionMetadata(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    file_name: str
    chunking_strategy: str
    embedding_model: str
    chunk_count: int
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

class Booking(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    full_name: str
    email: str
    interview_date: str
    interview_time: str
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)