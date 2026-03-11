from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from app.services.vector_db import vector_db_service
from flask import current_app

class RAGEngine:
    def __init__(self):
        self._llm = None
        
    @property
    def llm(self):
        if self._llm is None:
            self._llm = ChatOpenAI(
                model_name="gpt-4o-mini",
                temperature=0, 
                api_key=current_app.config.get('OPENAI_API_KEY')
            )
        return self._llm

    def _format_docs(self, docs):
        """
        Formats retrieved documents to include citation metadata directly in the context.
        """
        formatted = []
        for d in docs:
            # Extract standard metadata safely
            source = d.metadata.get('source_url', d.metadata.get('source', 'Unknown Source'))
            page = d.metadata.get('page', 'N/A')
            
            # Format the text with its explicit reference
            formatted.append(f"[Source: {source}, Page: {page}]\n{d.page_content}")
            
        return "\n\n---\n\n".join(formatted)

    def query(self, query_text):
        """
        Executes a RAG query against the knowledge base and returns the answer with citations.
        """
        retriever = vector_db_service.get_retriever(search_kwargs={"k": 5})
        
        # We explicitly retrieve docs first to form the citation payload for the API response
        raw_docs = retriever.invoke(query_text)
        
        # Build prompt enforcing citations
        template = """You are an Enterprise Knowledge Assistant. Use the following quoted context to answer the user's question.
        
        CRITICAL INSTRUCTIONS:
        1. If you don't know the answer based strictly on the context, say "I don't have enough information to answer that." Do not make up an answer.
        2. You MUST cite your sources using the exact format provided in the context blocks, e.g., (Source: doc_name.pdf, Page: 4).
        3. Be concise and professional.
        
        Context:
        {context}
        
        Question: {question}
        
        Answer:"""
        
        prompt = PromptTemplate.from_template(template)
        
        # LangChain Runnable execution
        rag_chain = (
            {"context": lambda x: self._format_docs(raw_docs), "question": RunnablePassthrough()}
            | prompt
            | self.llm
            | StrOutputParser()
        )
        
        answer = rag_chain.invoke(query_text)
        
        # Extract metadata to return as structured citation array for the API client
        citations = []
        for doc in raw_docs:
            citations.append({
                "source": doc.metadata.get('source_url', doc.metadata.get('source', 'Unknown')),
                "page": doc.metadata.get('page', 'N/A'),
                "content_preview": doc.page_content[:150] + "..."
            })
            
        return {
            "answer": answer,
            "citations": citations
        }

rag_engine = RAGEngine()
