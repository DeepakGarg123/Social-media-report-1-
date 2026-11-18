
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()


def create_answer_model():

    model = ChatGoogleGenerativeAI(
        model="gemini-3.5-flash-lite",
        temperature=0
    )

    return model


def generate_answer(question, retrieved_documents):

    model = create_answer_model()

    context = ""

    for index, document in enumerate(retrieved_documents, start=1):

        section = document.metadata.get("section", "Unknown")

        context += (
            f"\nDocument {index}\n"
            f"Section: {section}\n"
            f"Content: {document.page_content}\n"
        )

    prompt = f"""
    You are an intelligent Instagram Analytics Assistant.

    Answer the user's question using ONLY the provided context.

    Instructions:

    1. Do not invent or assume any information.
    2. If the answer is not available in the context,
       clearly say that the report does not contain the answer.
    3. Understand the language of the user's question.
    4. Respond in the same language as the user's question.
    5. If the user asks in Hinglish, respond in Hinglish.
    6. Keep the answer clear and easy to understand.
    7. Round numerical values to a maximum of 2 decimal places.
    8. Never show the original unrounded number alongside the rounded number.

    Context:
    {context}

    User Question:
    {question}

    Final Answer:
    """

    response = model.invoke(prompt)

    return response.text.strip()
