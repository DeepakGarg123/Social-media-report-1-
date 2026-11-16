from langchain_community.vectorstores import FAISS

from backend.rag.embeddings import create_embedding_model


def create_vector_store(chunks):
    embedding_model = create_embedding_model()

    vector_store = FAISS.from_documents(
        documents=chunks,
        embedding=embedding_model
    )

    return vector_store