
import json

from backend.rag.report_rag import create_report_documents
from backend.rag.chunker import split_documents
with open("backend/data/analytics_report.json", "r", encoding="utf-8") as file:
    report = json.load(file)

documents = create_report_documents(report)

chunks = split_documents(documents)

print("\nTOTAL DOCUMENTS:", len(documents))
print("TOTAL CHUNKS:", len(chunks))

for index, chunk in enumerate(chunks, start=1):
    print(f"\nChunk {index}")
    print("Section:", chunk.metadata["section"])
    print("Content:", chunk.page_content[:150])

print("TOTAL DOCUMENTS:", len(documents))

for index, document in enumerate(documents, start=1):
    print(f"\nDocument {index}")
    print("Section:", document.metadata["section"])
    print("Content:", document.page_content[:100])
