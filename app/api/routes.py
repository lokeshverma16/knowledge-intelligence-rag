from flask import request, jsonify, current_app
from . import api_bp
import traceback

# Import our new business logic services
from app.services.s3_service import s3_service
from app.services.ingestion import ingestion_service
from app.services.vector_db import vector_db_service
from app.services.rag_engine import rag_engine

@api_bp.route('/ingest', methods=['POST'])
def ingest_document():
    """
    Endpoint to trigger ingestion from S3, process the document, 
    and store embeddings in ChromaDB.
    Expected payload: {"s3_url": "s3://bucket-name/path/to/doc.pdf"}
    """
    data = request.get_json()
    if not data or 's3_url' not in data:
        return jsonify({"error": "Missing 's3_url' in request body"}), 400
        
    s3_url = data['s3_url']
    
    try:
        # 1. Download file locally
        temp_file_path = s3_service.download_file(s3_url)
        
        # 2. Extract and split into LangChain documents
        chunks = ingestion_service.process_and_chunk(temp_file_path, source_url=s3_url)
        
        # 3. Store into ChromaDB vector store
        success = vector_db_service.store_documents(chunks)
        
        # Cleanup temp file
        import os
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            
        if success:
            return jsonify({
                "message": f"Successfully ingested {len(chunks)} chunks from {s3_url}",
                "status": "success"
            }), 201
        else:
            return jsonify({"error": "Failed to store vectors"}), 500
            
    except Exception as e:
        current_app.logger.error(f"Ingestion Error: {traceback.format_exc()}")
        return jsonify({
            "error": "Failed to process document",
            "details": str(e)
        }), 500

@api_bp.route('/query', methods=['POST'])
def query_knowledge_base():
    """
    Endpoint to answer questions using RAG.
    Expected payload: {"query": "What is the company policy on remote work?"}
    """
    data = request.get_json()
    if not data or 'query' not in data:
        return jsonify({"error": "Missing 'query' in request body"}), 400
        
    query_text = data['query']
    
    try:
        # Ask RAG Engine for Answer and Source Metadata
        result = rag_engine.query(query_text)
        
        return jsonify({
            "query": query_text,
            "answer": result['answer'],
            "citations": result['citations']
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Query Error: {traceback.format_exc()}")
        return jsonify({
            "error": "Failed to query knowledge base",
            "details": str(e)
        }), 500
