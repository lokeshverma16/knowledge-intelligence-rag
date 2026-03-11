import os
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from flask import current_app

class DocumentIngestionService:
    def __init__(self):
        # We use RecursiveCharacterTextSplitter as it tries to keep paragraphs/sentences together
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            is_separator_regex=False,
        )

    def load_document(self, file_path, source_metadata=None):
        """
        Loads a document based on its extension.
        Returns a list of raw LangChain Documents.
        """
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        
        documents = []
        try:
            if ext == '.pdf':
                loader = PyPDFLoader(file_path)
                documents = loader.load()
            elif ext in ['.txt', '.md', '.csv']:
                loader = TextLoader(file_path, encoding='utf-8')
                documents = loader.load()
            else:
                raise ValueError(f"Unsupported file extension: {ext}")
                
            # Enhance metadata
            for i, doc in enumerate(documents):
                doc.metadata['source_type'] = ext
                if source_metadata:
                    doc.metadata.update(source_metadata)
                    
            return documents
        except Exception as e:
            current_app.logger.error(f"Error loading document {file_path}: {e}")
            raise

    def process_and_chunk(self, file_path, source_url):
        """
        End-to-end processing: load file, chunk it, prepare for vector DB.
        Returns chunked documents.
        """
        source_metadata = {"source_url": source_url}
        raw_documents = self.load_document(file_path, source_metadata)
        
        current_app.logger.info(f"Loaded {len(raw_documents)} pages/sections from {source_url}.")
        
        chunks = self.text_splitter.split_documents(raw_documents)
        
        current_app.logger.info(f"Split document into {len(chunks)} semantic chunks.")
        
        return chunks

ingestion_service = DocumentIngestionService()
