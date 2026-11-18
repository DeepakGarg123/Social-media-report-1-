import json

from backend.rag.report_rag import create_report_documents
from backend.rag.chunker import split_documents
from backend.rag.vector_store import create_vector_store
from backend.rag.query_router import route_query

with open("backend/data/analytics_report.json", "r", encoding="utf-8") as file:
    report = json.load(file)

print("\nCURRENT USERNAME:", report["profile"]["username"])
print("\nCURRENT CONTENT ANALYSIS:")
print(json.dumps(report["content_analysis"], indent=4))

documents = create_report_documents(report)
chunks = split_documents(documents)

vector_store = create_vector_store(chunks)

question = input("Enter your question: ")

sections = route_query(question)

print("\nSelected Sections:", sections)

if not sections:
    print("This question is unrelated to the Instagram report.")

else:
    results = vector_store.similarity_search(
        question,
        k=5,
        filter=lambda metadata: metadata.get("section") in sections
    )

    for index, document in enumerate(results, start=1):
        print(f"\nResult {index}")
        print("Section:", document.metadata["section"])
        print("Content:", document.page_content)