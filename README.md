# Palm Mind Technology - RAG Assessment Project

This repository contains the submission for the AI/ML Engineer technical assessment. It is a production-ready backend system built with FastAPI, featuring a sophisticated RAG agent with document ingestion capabilities.

## Architecture Overview

The system is built on a modern, modular architecture designed for scalability and maintainability.
- **FastAPI:** Serves as the high-performance web framework for the RESTful APIs.
- **Qdrant:** The vector database used for storing and searching text embeddings.
- **PostgreSQL:** The relational database for storing structured metadata (file uploads, bookings).
- **Redis:** Provides a low-latency cache for storing conversational memory between user sessions.
- **LangGraph:** Powers the core reasoning engine, allowing for complex, cyclical, and tool-using agentic behavior.
- **Docker & Docker Compose:** The entire infrastructure is containerized, ensuring a fully reproducible environment.

## Features

1.  **Document Ingestion API (`/api/v1/documents/upload`):**
    -   Accepts `.pdf` and `.txt` file uploads.
    -   Uses **Docling** for robust PDF parsing.
    -   Supports two chunking strategies: `RecursiveCharacterTextSplitter` and the advanced `SemanticChunker`.
    -   Supports two embedding models for comparison: Google's `text-embedding-004` and `bge-small-en-v1.5`.
    -   Stores embeddings in Qdrant and metadata in PostgreSQL.

2.  **Agentic Chat API (`/api/v1/chat/invoke`):**
    -   A stateful RAG agent built with **LangGraph**.
    -   Uses a `document_retriever` tool to answer questions from ingested content.
    -   Uses a `book_interview` tool that captures user details, saves them to the database, and sends a real confirmation email via SMTP.
    -   Maintains conversational context using a **Redis**-backed memory layer.

## Project Setup and Installation

**Prerequisites:**
- Docker and Docker Compose installed.
- Python 3.9+
- A Google Gemini API key and a Gmail App Password.

**1. Clone the Repository:**
```bash
git clone https://github.com/Dipesh-Chaudhary/palm-mind-rag-assessment
cd palm-mind-rag-assessment```

**2. Configure Environment Variables:**
Create a `.env` file in the project root by copying the provided example:
```bash
cp .env.example .env 
```
Now, open the `.env` file and fill in your `GOOGLE_API_KEY` and your Gmail credentials (`SMTP_SENDER_EMAIL` and `SMTP_SENDER_PASSWORD`).
SMTP_SENDER_EMAIL IS YOUR MAIL ACCOUNT AND THEN FOR PASSWORD FOLLOW BELOW STEPS:-
1) CLICK (SMTP_SENDER_PASSWORD)[https://myaccount.google.com/apppasswords?pli=1&rapt=AEjHL4M-f7QM6Gq1MMngFlgTRGkSKTNeGsyNchSEMGmZE9kaM2ESa5Y9uxgbTYf1PWc81CTVN4H7HhhRUXqPtL038uN72MhzFmyGRoSOHUTqzoRdrQJ7r3g] 
2) WRITE App Name as `Mail` and clck on `Create`
3) Finally it will generate an 16 character password so copy and paste it in the environment file but **witout space** i.e it might show (agfs bhgy bgsd rest) but instead you have to put the password value to (agfsbhgybgsdrest)
**3. Launch Infrastructure:**
Start all the required services (Qdrant, PostgreSQL, Redis) with a single command:
```bash
docker-compose up -d
```

**4. Install Dependencies & Run the App:**
It is recommended to use a Python virtual environment.
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run the FastAPI server
uvicorn app.main:app --reload
```
The API will be available at `http://127.0.0.1:8000`. The interactive documentation can be accessed at `http://127.0.0.1:8000/docs`.

## API Usage Examples (cURL)

**1. Upload a Document (PDF):**
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/documents/upload" \
-H "Content-Type: multipart/form-data" \
-F "chunking_strategy=semantic" \
-F "embedding_model=google" \
-F "file=@/path/to/your/document.pdf"
```

**2. Chat with the Agent:**
*Replace `your_unique_session_id` with any string to maintain a conversation.*
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/chat/invoke" \
-H "Content-Type: application/json" \
-d '{
    "session_id": "your_unique_session_id_123",
    "user_input": "What is the main topic of the document I just uploaded?"
}'
```

**3. Book an Interview:**
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/chat/invoke" \
-H "Content-Type: application/json" \
-d '{
    "session_id": "your_unique_session_id_123",
    "user_input": "I would like to book an interview. My name is Dipesh Chaudhary, my email is 9804234394d.@gmail.com, and I am available on 2024-06-25 at 1:00 PM."
}'
```

## Findings and Analysis

For a detailed comparison of chunking strategies, embedding models, and similarity search algorithms, please see the `FINDINGS.md` file.