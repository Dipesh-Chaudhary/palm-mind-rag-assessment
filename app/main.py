from fastapi import FastAPI
from app.api.router import api_router
from app.core.dependencies import engine
from app.models import schemas # This import is crucial!

app = FastAPI(
    title="Palm Mind Tech - RAG Assessment API",
    description="An advanced RAG system with agentic capabilities and document ingestion.",
    version="1.0.0"
)

app.include_router(api_router, prefix="/api/v1")

@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        # For development, to clear tables on each start
        # await conn.run_sync(schemas.SQLModel.metadata.drop_all)
        await conn.run_sync(schemas.SQLModel.metadata.create_all)

@app.get("/")
def read_root():
    return {"message": "API is running. Head to /docs for documentation."}