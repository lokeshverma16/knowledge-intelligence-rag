# Knowledge Intelligence System (Enterprise RAG Platform)

An end-to-end Retrieval-Augmented Generation (RAG) system with document ingestion, semantic chunking, and vector search, designed to deliver grounded, context-aware LLM responses.

## Tech Stack
*   **API Framework:** Flask (Python)
*   **LLM & Orchestration:** LangChain / OpenAI (`gpt-4o-mini`, `text-embedding-3-small`)
*   **Vector Database:** ChromaDB
*   **Storage Integration:** AWS S3 (`boto3`)
*   **Infrastructure:** Docker & Docker Compose

## Features
1.  **Direct S3 Ingestion:** Pulls PDF and Text documents directly from secure AWS S3 buckets.
2.  **Intelligent Chunking:** Uses LangChain's semantic chunking to ensure context isn't lost during vectorization.
3.  **Citation-Backed Answers:** Guarantees LLM references explicit source documents and pages, aggressively reducing hallucinations.
4.  **Containerized:** Instantly bootable local development environment or production-ready container logic via Docker.

## Setup Instructions

1.  **Clone/Navigate to the Repo:**
    ```bash
    cd enterprise_rag_platform
    ```

2.  **Environment Setup:**
    ```bash
    cp .env.example .env
    ```
    Populate the `.env` file with your `OPENAI_API_KEY`, and ideally your `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` if you intend to fetch non-public documents.

3.  **Launch via Docker Compose:**
    ```bash
    docker-compose up --build
    ```
    This will start two containers:
    *   `rag_platform_api` on port `5000`
    *   `chroma_backend` on port `8000`

## API Usage

### 1. Ingest a Document
Triggers the system to download a file from S3, slice it semantically, embed the data via OpenAI, and store it persistently in ChromaDB.

```bash
curl -X POST http://localhost:5000/api/v1/ingest \
-H "Content-Type: application/json" \
-d '{"s3_url": "s3://your-bucket-name/documents/employee_handbook.pdf"}'
```

### 2. Query the Knowledge Base
Ask a question. The system conducts a vector search against the ChromaDB chunks, formats a context-aware prompt, and streams it to OpenAI.

```bash
curl -X POST http://localhost:5000/api/v1/query \
-H "Content-Type: application/json" \
-d '{"query": "What is the policy for remote work according to the handbook?"}'
```

**Example Response:**
```json
{
  "query": "What is the policy for remote work according to the handbook?",
  "answer": "According to the handbook, remote work is allowed up to 3 days per week upon manager approval. Employees must maintain core hours between 10 AM and 3 PM.",
  "citations": [
    {
      "source": "s3://your-bucket-name/documents/employee_handbook.pdf",
      "page": "14",
      "content_preview": "3.1 Remote Working Guidelines: Employees are eligible to work remotely for a maximum of three (3) days per standard work week. This requires explicitly written approval from a direct manager..."
    }
  ]
}
```
