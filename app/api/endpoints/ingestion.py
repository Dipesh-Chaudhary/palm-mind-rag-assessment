from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.document_service import process_document
from app.core.dependencies import get_db_session

router = APIRouter()

@router.post("/upload")
async def upload_file(
    chunking_strategy: str = Form(..., description="'recursive' or 'semantic'"),
    embedding_model: str = Form(..., description="'google' or 'bge'"),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Uploads a .pdf or .txt file, processes it through a chunking and embedding
    pipeline, and stores the results in Qdrant and metadata in PostgreSQL.
    """
    if not file.filename.lower().endswith(('.pdf', '.txt')):
        raise HTTPException(status_code=400, detail="Invalid file type. Only .pdf and .txt are supported.")

    try:
        content = await file.read()
        metadata = await process_document(
            db=db,
            file_content=content,
            file_name=file.filename,
            chunking_strategy=chunking_strategy,
            embedding_model_name=embedding_model
        )
        return {
            "status": "success",
            "message": f"Successfully processed and ingested {file.filename}",
            "data": metadata
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
