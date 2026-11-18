
from backend.rag.vector_store import build_report_vector_store
from backend.rag.query_router import route_query
from backend.rag.answer_generator import generate_answer
from backend.rag.sources import extract_sources


def answer_report_question(report, question):

    vector_store = build_report_vector_store(report)

    sections = route_query(question)

    if not sections:
        return {
            "answer": "Sorry, this information is not available in the Instagram report.",
            "sources": []
        }

    retrieved_documents = vector_store.similarity_search(
        question,
        k=5,
        filter=lambda metadata: metadata.get("section") in sections
    )

    if not retrieved_documents:
        return {
            "answer": "No relevant information found in the report.",
            "sources": []
        }

    answer = generate_answer(question, retrieved_documents)

    sources = extract_sources(retrieved_documents)

    return {
        "answer": answer,
        "sources": sources
    }
