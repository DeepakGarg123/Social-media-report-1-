import json

from backend.rag.report_rag import create_report_documents
from backend.rag.chunker import split_documents
from backend.rag.vector_store import create_vector_store

with open("backend/data/analytics_report.json", "r", encoding="utf-8") as file:
    report = json.load(file)

documents = create_report_documents(report)
chunks = split_documents(documents)

vector_store = create_vector_store(chunks)

question = "What content strategy was suggested in the report?"

results = vector_store.similarity_search(question, k=3)

for index, document in enumerate(results, start=1):
    print(f"\nResult {index}")
    print("Section:", document.metadata["section"])
    print("Content:", document.page_content)