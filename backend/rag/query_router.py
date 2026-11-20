
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

    question_lower = question.lower().strip()

    post_pattern = (
        r"\b(which post|what post|highest post|top post|"
        r"best post|most liked post|most commented post|"
        r"highest performing post|top performing post|"
        r"which reel|what reel|most liked reel|"
        r"top reels|individual post|post received|"
        r"posts received|posts with|post with)\b"
    )

    time_pattern = (
        r"\b(hour|hours|time slot|posting time|best time|"
        r"when should i post|weekday|weekdays|day of week|"
        r"which day|posting schedule|posting frequency)\b"
    )

    content_pattern = (
        r"\b(content type|content types|reels vs|"
        r"reel vs|carousel|carousels|content format|"
        r"video posts|photo posts)\b"
    )

    has_post_intent = bool(re.search(post_pattern, question_lower))
    has_time_intent = bool(re.search(time_pattern, question_lower))
    has_content_intent = bool(re.search(content_pattern, question_lower))

    if has_post_intent and not has_time_intent:
        return ["top_posts"]

    if has_time_intent and not has_post_intent:
        return ["posting_analysis"]

    if has_content_intent:
        return ["content_analysis"]

    model = create_router_model()

    prompt = f"""
    You are an intelligent query router for an Instagram analytics report.

    Identify which report sections contain information needed
    to answer the user's question.

    Available sections:
    {AVAILABLE_SECTIONS}

    Section descriptions:

    profile: Username, full name, followers, following, biography.

    metrics: Account-wide total likes, comments, interactions,
    average likes per post and average comments per post.

    top_posts: Individual post captions, likes, comments and views.
    Use this section to identify the post with the highest likes,
    comments or views.

    suggestions: Recommendations for improving the Instagram account.

    posting_analysis: Posting hours, posting days, number of posts
    and average likes by posting time.

    content_analysis: Performance of different content types.

    growth: Starting followers, ending followers and growth percentage.

    llm_insights: AI-generated observations and supporting evidence.

    Important routing rules:

    1. Questions about a specific individual post must use top_posts.
    2. Questions about average likes across the entire account
       must use metrics.
    3. Questions about the best posting hour or day must use
       posting_analysis.
    4. Questions about content formats must use content_analysis.
    5. For comparisons, select all required sections.
    6. Select only sections that directly help answer the question.
    7. Never invent section names.
    8. If unrelated to the Instagram report, return an empty list.

    Return ONLY valid JSON:

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
