from backend.rag.query_router import route_query

while True:

    question = input("\nEnter your question (or type exit): ")

    if question.lower() == "exit":
        break

    try:
        sections = route_query(question)

        print("\nSelected Sections:", sections)

    except Exception as error:
        print("\nRouter Error:", error)