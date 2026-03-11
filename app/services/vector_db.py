import os
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from flask import current_app

class VectorDBService:
    def __init__(self):
        self._vector_store = None
        self._embeddings = None

    @property
    def embeddings(self):
        if self._embeddings is None:
            # text-embedding-3-small is cheap and highly effective
            self._embeddings = OpenAIEmbeddings(
                model="text-embedding-3-small",
                api_key=current_app.config.get('OPENAI_API_KEY')
            )
        return self._embeddings

    @property
    def vector_store(self):
        if self._vector_store is None:
            persist_directory = current_app.config.get('CHROMA_DB_DIR')
            
            # Ensure the directory exists
            os.makedirs(persist_directory, exist_ok=True)
            
            self._vector_store = Chroma(
                collection_name="enterprise_knowledge",
                embedding_function=self.embeddings,
                persist_directory=persist_directory
            )
        return self._vector_store

    def store_documents(self, chunks):
        """
        Takes chunked LangChain Documents and inserts them into ChromaDB.
        """
        if not chunks:
            current_app.logger.warning("No chunks provided to store_documents. Skipping.")
            return False
            
        try:
            current_app.logger.info(f"Storing {len(chunks)} chunks into ChromaDB...")
            vector_store = self.vector_store
            
            # Add documents returns a list of assigned IDs
            ids = vector_store.add_documents(documents=chunks)
            current_app.logger.info(f"Successfully stored {len(ids)} chunks.")
            
            return True
        except Exception as e:
            current_app.logger.error(f"Failed to store documents in VectorDB: {e}")
            raise

    def get_retriever(self, search_kwargs=None):
        """
        Returns a LangChain VectorStoreRetriever for the initialized DB.
        """
        if search_kwargs is None:
            # Return top 4 most similar chunks by default
            search_kwargs = {"k": 4}
            
        return self.vector_store.as_retriever(search_kwargs=search_kwargs)

vector_db_service = VectorDBService()
