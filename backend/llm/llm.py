
import os

import requests
from dotenv import load_dotenv

from backend.llm.recommendation_builder import build_recommendations

load_dotenv()

gemini_api_key = os.getenv("GEMINI_API_KEY")

_gemini_client = None

if gemini_api_key:
    try:
        from google import genai as _genai
        _gemini_client = _genai.Client(api_key=gemini_api_key)
    except Exception as _e:
        print(f"[LLM] Warning: could not initialise Gemini client: {_e}")
else:
    print("[LLM] Warning: GEMINI_API_KEY not set — will use Ollama directly.")


# --------------------------------------------------
# OLLAMA CONFIGURATION
# --------------------------------------------------

OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://localhost:11434/api/generate"
)

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:latest")


# --------------------------------------------------
# BUILD DETERMINISTIC RECOMMENDATIONS
# --------------------------------------------------

def get_supported_recommendations(report):

    supported_recommendations = build_recommendations(
        report
    )

    return supported_recommendations


# --------------------------------------------------
# CREATE LLM-READY ANALYTICS
# --------------------------------------------------

def create_llm_report(
    report,
    supported_recommendations
):

    return {

        "profile": report.get("profile"),

        "metrics": report.get("metrics"),

        "growth": report.get("growth"),

        "top_posts": report.get("top_posts"),

        "video_analysis": report.get("video_analysis"),

        "llm_insights": report.get("llm_insights"),

        "supported_recommendations":
            supported_recommendations

    }


# --------------------------------------------------
# CREATE LLM PROMPT
# --------------------------------------------------

def create_prompt(llm_report):

    username = (llm_report.get("profile") or {}).get(
        "username",
        "creator"
    )

    prompt = f"""
You are an expert Instagram Growth Coach & Strategist conducting a personalized, 1-on-1 growth consulting session with the creator @{username}.

Your objective is to review the creator's real performance report and deliver clear, inspiring, data-backed advice explaining:
"By doing these specific things, you can grow your Instagram account."

==================================================
CREATOR & ACCOUNT PROFILE
==================================================
Creator: @{username}
Followers: {(llm_report.get("profile") or {}).get("followers", "N/A")}
Total Posts: {(llm_report.get("profile") or {}).get("total_posts", "N/A")}

==================================================
DATA INTEGRITY & ACCURACY RULES (STRICT)
==================================================
1. Base your factual claims and metrics ONLY on the provided analytics data and "supported_recommendations".
2. Never invent fake stats, demographic polls, or unverified claims.
3. Keep all numbers (e.g. likes, comments, interaction rates, follower gains, peak hours) 100% accurate.
4. NEVER mention Instagram internal short codes (such as "Dd_oTRvBf0g", "DZh470dtCr5"). Always refer to posts by their provided "post_name", or naturally as "your top Reel / post".
5. Speak in a confident, encouraging, conversational tone directly to the creator using "you" and "your".
6. For every recommendation, explicitly show the creator HOW doing this will grow their Instagram account (e.g. increasing audience retention, triggering Explore feed recommendations, improving engagement velocity, converting viewers into loyal followers).

==================================================
OUTPUT STRUCTURE
==================================================
Format your response using clean, beautifully formatted GitHub Markdown with the following exact sections:

## 👋 Hey @{username}! Your Personalized Instagram Growth Roadmap

[Write 1 engaging paragraph welcoming the creator. Summarize their core account momentum from the report (such as total interactions or follower growth) and set an encouraging, high-energy stage for their growth plan.]

---

## 🚀 Strategic Moves to Grow Your Account

Generate a detailed subsection for EACH item in "supported_recommendations" (e.g. Strategy 1, Strategy 2, etc.):

### Strategy [Number]: [Actionable, Catchy Title]
- **📊 What Your Data Shows:** [1-2 sentences highlighting the exact metrics conversationally—e.g. likes, comments, interaction %, or peak posting hour.]
- **💡 Actionable Advice (What to do):** [Practical, creator-tested advice on how to execute this—such as content themes, video hooks, structure, or caption prompts.]
- **📈 How Doing This Grows Your Account:** [Clearly explain the growth mechanism—e.g. how this triggers the Instagram algorithm, boosts dwell time, expands reach on Reels / Explore, or drives profile visits.]
- **🧪 Your Next Experiment:** [A concrete, testable action for their next post and the specific metric to monitor.]

---

## 🎯 14-Day Growth Execution Checklist

[Provide a punchy, 3-4 bullet checklist summarizing the highest-leverage actions the creator should implement over the next two weeks to accelerate their account growth.]

---

[Conclude with 1-2 inspiring sentences signing off as their dedicated Instagram Growth Advisor.]

==================================================
ANALYTICS & SUPPORTED RECOMMENDATIONS DATA
==================================================
{__import__("json").dumps(llm_report, indent=2)}
"""

    return prompt


# --------------------------------------------------
# SEND REQUEST TO GEMINI
# --------------------------------------------------

CANDIDATE_MODELS = [
    "gemini-3.6-flash",
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite"
]


def _generate_gemini_response(prompt):

    if not _gemini_client:
        raise RuntimeError(
            "Gemini client is not initialised (no API key)."
        )

    last_error = None

    for model_name in CANDIDATE_MODELS:

        try:

            print(f"[LLM] Trying Gemini model: {model_name} ...")

            response = _gemini_client.models.generate_content(
                model=model_name,
                contents=prompt,
                config={
                    "temperature": 0.7,
                    "top_p": 0.9,
                }
            )

            if response and response.text:

                print(
                    f"[LLM] Gemini succeeded with model: {model_name}"
                )

                return response.text.strip()

        except Exception as error:

            print(
                f"[LLM] Gemini model {model_name} failed: {error}"
            )

            last_error = error

            continue

    raise RuntimeError(
        f"Gemini failed across all models {CANDIDATE_MODELS}: {last_error}"
    )


# --------------------------------------------------
# SEND REQUEST TO OLLAMA
# --------------------------------------------------

def _generate_ollama_response(prompt):

    print(
        f"[LLM] Sending request to Ollama ({OLLAMA_MODEL}) at {OLLAMA_URL} ..."
    )

    payload = {

        "model": OLLAMA_MODEL,

        "prompt": prompt,

        "stream": False,

        "options": {
            "temperature": 0.7,
            "top_p": 0.9,
        }

    }

    response = requests.post(
        OLLAMA_URL,
        json=payload,
        timeout=300
    )

    if response.status_code != 200:

        raise RuntimeError(
            f"Ollama returned HTTP {response.status_code}: {response.text[:200]}"
        )

    result = response.json()

    text = result.get("response", "").strip()

    if not text:

        raise RuntimeError(
            "Ollama returned an empty response."
        )

    print("[LLM] Ollama succeeded.")

    return text


# --------------------------------------------------
# HYBRID: GEMINI FIRST → OLLAMA FALLBACK
# --------------------------------------------------

def generate_llm_response(prompt):

    gemini_error = None

    if _gemini_client:

        try:

            return _generate_gemini_response(prompt)

        except Exception as error:

            gemini_error = error

            print(
                f"\n[LLM] All Gemini models exhausted — "
                f"handing over to Ollama fallback.\n"
                f"Gemini error: {gemini_error}\n"
            )

    else:

        print(
            "[LLM] Gemini client unavailable — going straight to Ollama."
        )

    try:

        return _generate_ollama_response(prompt)

    except Exception as ollama_error:

        raise RuntimeError(
            f"Both Gemini and Ollama failed.\n"
            f"Gemini error: {gemini_error}\n"
            f"Ollama error: {ollama_error}"
        )


# --------------------------------------------------
# MAIN RECOMMENDATION FUNCTION
# --------------------------------------------------

def generate_recommendations(report, force_refresh=False):

    if not isinstance(report, dict):

        raise ValueError(
            "A valid analytics report must be provided."
        )

    print("\nAnalytics report received.")

    supported_recommendations = get_supported_recommendations(
        report
    )

    print(
        "Supported recommendations:",
        len(supported_recommendations)
    )

    for recommendation in supported_recommendations:

        print(
            "\nType:",
            recommendation["type"]
        )

        print(
            "Action:",
            recommendation["action"]
        )

        print(
            "Evidence:",
            recommendation["evidence"]
        )

    llm_report = create_llm_report(
        report,
        supported_recommendations
    )

    print("\nLLM-ready analytics created.")

    prompt = create_prompt(
        llm_report
    )

    print(
        "\nPrompt size:",
        len(prompt),
        "characters"
    )

    print(
        "Sending analytics to AI engine (Gemini → Ollama fallback)..."
    )

    llm_response = generate_llm_response(
        prompt
    )

    print("\nResponse received.")

    print("\n===================================")
    print("      LLM Growth Recommendations")
    print("===================================\n")

    try:

        print(llm_response)

    except UnicodeEncodeError:

        print(
            llm_response.encode(
                "ascii",
                errors="replace"
            ).decode("ascii")
        )

    return llm_response
