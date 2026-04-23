from flask import current_app
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI

from app.services.vector_db import vector_db_service

PROMPT_TEMPLATE = """You are an Enterprise Knowledge Assistant. Answer the
user's question using only the quoted context below.

Ground rules:
  1. If the context does not contain the answer, reply exactly:
     "I don't have enough information to answer that."
     Do not speculate, do not use outside knowledge.
  2. Cite every fact inline using the format provided at the top of each
     context block, e.g. (Source: handbook.pdf, Page: 4).
  3. Be concise and professional. Short paragraphs or bullet lists are fine.

Context:
{context}

Question: {question}

Answer:"""


class RAGEngine:
    """Retrieval-Augmented Generation pipeline, kept deliberately small."""

    def __init__(self) -> None:
        self._llm: ChatOpenAI | None = None

    @property
    def llm(self) -> ChatOpenAI:
        if self._llm is None:
            self._llm = ChatOpenAI(
                model=current_app.config["OPENAI_CHAT_MODEL"],
                temperature=0,
                api_key=current_app.config.get("OPENAI_API_KEY"),
            )
        return self._llm

    @staticmethod
    def _format_docs(docs) -> str:
        """Inline the citation header so the LLM can reference it verbatim."""
        blocks = []
        for d in docs:
            source = d.metadata.get(
                "source_url", d.metadata.get("source", "Unknown Source")
            )
            page = d.metadata.get("page", "N/A")
            blocks.append(f"[Source: {source}, Page: {page}]\n{d.page_content}")
        return "\n\n---\n\n".join(blocks)

    def query(self, query_text: str) -> dict:
        retriever = vector_db_service.get_retriever(
            search_kwargs={"k": current_app.config["RETRIEVAL_K"]}
        )

        # Retrieve explicitly so we can both (a) feed the LLM the same context
        # and (b) return the raw citations in the API response.
        raw_docs = retriever.invoke(query_text)

        if not raw_docs:
            return {
                "answer": "I don't have enough information to answer that.",
                "citations": [],
            }

        prompt = PromptTemplate.from_template(PROMPT_TEMPLATE)
        chain = (
            {
                "context": lambda _: self._format_docs(raw_docs),
                "question": RunnablePassthrough(),
            }
            | prompt
            | self.llm
            | StrOutputParser()
        )

        answer = chain.invoke(query_text)

        citations = [
            {
                "source": d.metadata.get(
                    "source_url", d.metadata.get("source", "Unknown")
                ),
                "page": d.metadata.get("page", "N/A"),
                "content_preview": (d.page_content[:180] + "...")
                if len(d.page_content) > 180
                else d.page_content,
            }
            for d in raw_docs
        ]

        return {"answer": answer, "citations": citations}


rag_engine = RAGEngine()
