
import json

from backend.rag.rag_pipeline import answer_report_question

with open("backend/data/analytics_report.json", "r", encoding="utf-8") as file:
    report = json.load(file)

question = input("\nEnter your question: ")

result = answer_report_question(report, question)

print("\nFinal Answer:")
print(result["answer"])

print("\nSources:")
for source in result["sources"]:
    print(source)
