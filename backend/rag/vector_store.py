from langchain_community.vectorstores import FAISS
from backend.rag.report_rag import create_report_documents
from backend.rag.chunker import split_documents
from backend.rag.embeddings import create_embedding_model


def create_vector_store(chunks):
    embedding_model = create_embedding_model()

    vector_store = FAISS.from_documents(
        documents=chunks,
        embedding=embedding_model
    )

    return vector_store

def build_report_vector_store(report):

    documents = create_report_documents(report)

    chunks = split_documents(documents)

    vector_store = create_vector_store(chunks)

    return vector_store