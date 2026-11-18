
import json
import re

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()


AVAILABLE_SECTIONS = [
    "profile",
    "metrics",
    "top_posts",
    "suggestions",
    "posting_analysis",
    "content_analysis",
    "growth",
    "llm_insights"
]


def create_router_model():
    model = ChatGoogleGenerativeAI(
        model="gemini-3.5-flash-lite",
        temperature=0
    )

    return model


def route_query(question):

    model = create_router_model()

    prompt = f"""
    You are an intelligent query router for an Instagram analytics report.

    Your task is to understand the user's question and identify
    which report sections contain information needed to answer it.

    Available report sections:

    {AVAILABLE_SECTIONS}

    Section descriptions:

    profile: Username, full name, followers, following, biography.
    metrics: Total likes, comments, interactions and averages.
    top_posts: Individual post captions, likes, comments and views.
    suggestions: Recommendations for improving the Instagram account.
    posting_analysis: Posting hours, number of posts and average likes.
    content_analysis: Performance of different content types.
    growth: Starting followers, ending followers and growth percentage.
    llm_insights: AI-generated observations and supporting evidence.

    Instructions:

    1. Understand the meaning and intent of the user's question.
    2. Select all sections required to answer the question.
    3. Select multiple sections when comparison or combined information is needed.
    4. Select only relevant sections.
    5. Never invent section names.
    6. If the question is unrelated to the Instagram report,
       return an empty list.

    Return ONLY valid JSON in this exact format:

    {{
        "sections": ["section_name"]
    }}

    User Question:
    {question}
    """

    response = model.invoke(prompt)

    response_text = response.text.strip()

    response_text = re.sub(
        r"```json\s*|```\s*",
        "",
        response_text
    ).strip()

    result = json.loads(response_text)

    sections = result.get("sections", [])

    if not isinstance(sections, list):
        raise ValueError("Router must return a list of sections.")

    selected_sections = []

    for section in sections:
        if (
            isinstance(section, str)
            and section in AVAILABLE_SECTIONS
            and section not in selected_sections
        ):
            selected_sections.append(section)

    return selected_sections
