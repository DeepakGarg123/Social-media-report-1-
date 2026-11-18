
import json

from backend.rag.report_rag import create_report_documents
from backend.rag.chunker import split_documents
with open("backend/data/analytics_report.json", "r", encoding="utf-8") as file:
    report = json.load(file)
    
    print("\nREPORT SECTIONS:")

for section, data in report.items():
    print(f"\n{section}: {type(data).__name__}")

    if isinstance(data, dict):
        print("Keys:", list(data.keys()))

    elif isinstance(data, list):
        print("Items:", len(data))

        if data and isinstance(data[0], dict):
            print("First item keys:", list(data[0].keys()))

documents = create_report_documents(report)

chunks = split_documents(documents)

print("\nTOTAL DOCUMENTS:", len(documents))
print("TOTAL CHUNKS:", len(chunks))

for index, chunk in enumerate(chunks, start=1):
    print(f"\nChunk {index}")
    print("Section:", chunk.metadata["section"])
    print("Content:", chunk.page_content)

print("TOTAL DOCUMENTS:", len(documents))

for index, document in enumerate(documents, start=1):
    print(f"\nDocument {index}")
    print("Section:", document.metadata["section"])
    print("Content:", document.page_content)
