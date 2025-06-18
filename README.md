# Palm Mind Technology - RAG Assessment Project

This repository contains the submission for the AI/ML Engineer technical assessment. It is a production-ready backend system built with FastAPI, featuring a sophisticated RAG agent with document ingestion capabilities and automated analysis.

## Architecture Overview

The system is built on a modern, modular architecture designed for scalability and maintainability.
- **FastAPI:** Serves as the high-performance web framework for the RESTful APIs.
- **Qdrant:** The vector database used for storing and searching text embeddings.
- **PostgreSQL:** The relational database for storing structured metadata (file uploads, bookings).
- **Redis Stack:** Provides a low-latency cache for storing conversational memory, with the necessary RediSearch module for advanced queries.
- **LangGraph:** Powers the core reasoning engine, allowing for complex, cyclical, and tool-using agentic behavior.
- **Docker & Docker Compose:** The entire infrastructure is containerized, ensuring a fully reproducible environment.

## Features

1.  **Document Ingestion API (`/api/v1/documents/upload`):**
    -   Accepts `.pdf` and `.txt` file uploads.
    -   Uses **Docling** for robust PDF parsing.
    -   Supports multiple chunking strategies (`Recursive`, `Semantic`) and embedding models (`Google`, `BGE`).
    -   Stores embeddings in Qdrant and metadata in PostgreSQL.

2.  **Agentic Chat API (`/api/v1/chat/invoke`):**
    -   A stateful RAG agent built with **LangGraph**.
    -   Uses a `document_retriever` tool to answer questions from ingested content.
    -   Features an intelligent `book_interview` tool.

## Project Setup and Installation

**Prerequisites:**
- Docker and Docker Compose installed.
- Python 3.9+
- A Google Gemini API key and a Gmail App Password.

**1. Clone the Repository:**
```bash
git clone https://github.com/Dipesh-Chaudhary/palm-mind-rag-assessment
cd palm-mind-rag-assessment
```

**2. Configure Environment Variables:**
Create a `.env` file in the project root. You can copy the provided `.env.example` file to start.
```bash
cp .env.example .env
```
Now, open the `.env` file and fill in your `GOOGLE_API_KEY` and your Gmail credentials (`SMTP_SENDER_EMAIL` and `SMTP_SENDER_PASSWORD`).

SMTP_SENDER_EMAIL IS YOUR MAIL ACCOUNT AND THEN FOR PASSWORD FOLLOW BELOW STEPS:-
1) CLICK (SMTP_SENDER_PASSWORD)[https://myaccount.google.com/apppasswords?pli=1&rapt=AEjHL4M-f7QM6Gq1MMngFlgTRGkSKTNeGsyNchSEMGmZE9kaM2ESa5Y9uxgbTYf1PWc81CTVN4H7HhhRUXqPtL038uN72MhzFmyGRoSOHUTqzoRdrQJ7r3g] 
2) WRITE App Name as `Mail` and clck on `Create`
3) Finally it will generate an 16 character password so copy and paste it in the environment file but **witout space** i.e it might show (agfs bhgy bgsd rest) but instead you have to put the password value to (agfsbhgybgsdrest)


**3. Launch Infrastructure:**
Start all the required services (Qdrant, PostgreSQL, Redis Stack) with a single command:
```bash
docker-compose up -d
```

**4. Install Dependencies & Run the App:**
This project uses a virtual environment to manage dependencies, which is a best practice.
```bash
# Create the virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install all required libraries
pip install -r requirements.txt

# Run the FastAPI server
uvicorn app.main:app --reload --reload-dir app
```
The API is now running. The interactive documentation (your testing UI) can be accessed at `http://127.0.0.1:8000/docs`.

## How to Test the Features

### Testing Document Ingestion and RAG

1.  Navigate to the `/docs` page in your browser.
2.  Expand the `POST /api/v1/documents/upload` endpoint.
3.  Click "Try it out", select a `.pdf` or `.txt` file, choose a chunking strategy (`semantic` is recommended), and an embedding model (`google`), then click "Execute".
4.  Once the upload is successful, expand the `POST /api/v1/chat/invoke` endpoint.
5.  Click "Try it out", provide a `session_id` (e.g., "test1"), and ask a question about the document you just uploaded. The agent will use its `document_retriever` tool to find and provide an answer.

### Testing the Interview Booking Process

The agent is designed to handle interview booking as a conversational tool. To test this feature for yourself and see the confirmation email, follow these steps:

1.  Go to the `/docs` page and expand the `POST /api/v1/chat/invoke` endpoint.
2.  Click "Try it out".
3.  Start a conversation by providing a `session_id` and expressing your intent.

**Example Conversation:**

*   **Your First Request:**
    ```json
    {
      "session_id": "my-interview-test",
      "user_input": "Hello, I would like to book an interview."
    }
    ```
    *The agent will recognize the intent and ask for the necessary details (name, email, date, time).*

*   **Your Second Request (providing the details):**
    ```json
    {
      "session_id": "my-interview-test",
      "user_input": "I want to book interview to name: Dipesh Chaudhary, my email is your-email@gmail.com, and I would like to book it for August 25th, 2024 at 3 PM."
    }
    ```
    *(**Important:** Use the email address you configured in your `.env` file.)*

**Expected Result:**
The API will return a confirmation message like "Interview booked successfully...". Simultaneously, the system will have called the `book_interview` tool, which saves the booking to the PostgreSQL database and sends a confirmation email **to the address you provided**. Check your inbox to confirm the entire workflow was successful.

## Findings and Analysis

For a detailed comparison of chunking strategies, embedding models, and similarity search algorithms, please see the `FINDINGS.md` file. The experiments were conducted in a GPU-accelerated Colab environment, and the notebook (`run_experiments.ipynb`) is included in this repository.
