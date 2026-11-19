import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import json
import os
import base64
import urllib.request
from datetime import datetime

import streamlit as st

from backend.analytics.analytics import generate_analytics
from backend.llm.llm import generate_recommendations
from backend.scrapers.instagram_scraper import scrape_instagram
from backend.visualization.charts import generate_charts

from backend.rag.vector_store import build_report_vector_store
from backend.rag.rag_pipeline import answer_report_question


# ---------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------

def fetch_image_as_base64(url: str) -> str | None:
    if not url:
        return None

    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://www.instagram.com/",
            }
        )

        with urllib.request.urlopen(req, timeout=8) as resp:
            content_type = resp.headers.get("Content-Type", "image/jpeg")
            image_data = resp.read()

        encoded = base64.b64encode(image_data).decode("utf-8")
        return f"data:{content_type};base64,{encoded}"

    except Exception:
        return None


def format_month_label(month_str):
    try:
        return datetime.strptime(month_str, "%Y-%m").strftime("%B %Y")
    except Exception:
        return month_str


def show_growth_metrics(history, title="Follower Growth"):
    if len(history) < 2:
        st.info("At least two snapshots are required to calculate follower growth.")
        return

    first = history[0]
    last = history[-1]

    start_followers = first["followers"]
    end_followers = last["followers"]

    growth = end_followers - start_followers
    growth_percentage = (
        (growth / start_followers) * 100
        if start_followers > 0 else 0
    )

    st.write(
        f"Showing growth from **{first['date']}** "
        f"to **{last['date']}**:"
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Start Followers", f"{start_followers:,}")

    with col2:
        st.metric("End Followers", f"{end_followers:,}")

    with col3:
        st.metric("Growth", f"{growth:+,}")

    with col4:
        st.metric("Growth %", f"{growth_percentage:+.2f}%")

    if growth > 0:
        st.success(f"📈 Gained {growth:,} followers")
    elif growth < 0:
        st.error(f"📉 Lost {abs(growth):,} followers")
    else:
        st.info("Follower count remained unchanged.")

    with st.expander("📋 View Snapshot Details"):
        table_rows = []

        for index, snapshot in enumerate(history):
            difference = (
                snapshot["followers"] - history[index - 1]["followers"]
                if index > 0 else 0
            )

            table_rows.append({
                "Date": snapshot["date"],
                "Followers": f"{snapshot['followers']:,}",
                "Daily Change": (
                    f"{difference:+,}"
                    if index > 0 else "Baseline"
                )
            })

        st.dataframe(table_rows, use_container_width=True)


# ---------------------------------------------------------
# PAGE CONFIGURATION
# ---------------------------------------------------------

st.set_page_config(
    page_title="Instagram AI Growth Report",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Instagram AI Growth Report")

st.write(
    "Analyze Instagram profile growth, post performance, "
    "and get AI-powered growth recommendations."
)


# ---------------------------------------------------------
# SESSION STATE
# ---------------------------------------------------------

default_states = {
    "analysis_done": False,
    "profile": None,
    "report": None,
    "analyzed_url": "",
    "llm_recommendations": None,
    "filter_months": False,
    "rag_vector_store": None,
    "rag_chat_history": [],
}

for key, value in default_states.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ---------------------------------------------------------
# SIDEBAR CONFIGURATION
# ---------------------------------------------------------

with st.sidebar:
    st.header("⚙️ Performance & Cache Settings")

    use_cache = st.checkbox(
        "⚡ Use Cached Data if Available",
        value=True,
        help=(
            "Loads profile data from local cache when available. "
            "Uncheck to force fresh scraping."
        )
    )

    scrape_mode = st.selectbox(
        "📊 Live Scraping Depth",
        options=[
            "15 Posts (Fast Mode ~5-10s)",
            "30 Posts (Balanced ~15-25s)",
            "50 Posts (Deep Analysis ~35-60s)"
        ],
        index=0
    )

    if "15" in scrape_mode:
        max_posts = 15
    elif "30" in scrape_mode:
        max_posts = 30
    else:
        max_posts = 50


# ---------------------------------------------------------
# INSTAGRAM URL INPUT
# ---------------------------------------------------------

instagram_url = st.text_input(
    "Enter Instagram Profile URL",
    placeholder="https://www.instagram.com/username/"
)


# ---------------------------------------------------------
# ANALYZE PROFILE
# ---------------------------------------------------------

if st.button("Analyze Profile", type="primary"):

    if not instagram_url.strip():
        st.warning("Please enter an Instagram profile URL.")

    else:

        # Reset previous analysis
        st.session_state.analysis_done = False
        st.session_state.profile = None
        st.session_state.report = None
        st.session_state.llm_recommendations = None
        st.session_state.rag_vector_store = None
        st.session_state.rag_chat_history = []

        st.session_state.pop("cached_charts", None)
        st.session_state.pop("cached_charts_user", None)

        st.session_state.filter_months = False

        for filter_key in [
            "select_start_month",
            "select_end_month",
            "select_single_month",
            "month_filter_type",
            "select_start_date",
            "select_end_date",
        ]:
            st.session_state.pop(filter_key, None)

        # -------------------------------------------------
        # SCRAPING
        # -------------------------------------------------

        result = None

        with st.spinner("Retrieving Instagram profile data..."):

            try:
                result = scrape_instagram(
                    instagram_url.strip(),
                    force_refresh=not use_cache,
                    max_posts=max_posts,
                    return_data=True,
                    save_shared_files=False
                )

            except Exception as error:
                st.error(f"Instagram scraping failed: {error}")

        if result is None:

            st.error("Instagram profile could not be collected.")

        else:

            profile, posts = result

            # -------------------------------------------------
            # ANALYTICS
            # -------------------------------------------------

            report = None

            with st.spinner("Calculating Instagram analytics..."):

                try:
                    report = generate_analytics(
                        profile=profile,
                        data=posts,
                        save_report=False
                    )

                except Exception as error:
                    st.error(f"Analytics generation failed: {error}")

            if report is None:

                st.error("Analytics report could not be generated.")

            else:

                st.session_state.profile = profile
                st.session_state.report = report
                st.session_state.analyzed_url = instagram_url.strip()

                # -------------------------------------------------
                # AI RECOMMENDATIONS
                # -------------------------------------------------

                try:

                    with st.spinner(
                        "Generating AI growth recommendations..."
                    ):

                        recommendations = generate_recommendations(
                            report=report,
                            force_refresh=not use_cache
                        )

                    st.session_state.llm_recommendations = recommendations

                except Exception as error:

                    st.session_state.llm_recommendations = None

                    st.warning(
                        f"AI recommendations could not be generated: {error}"
                    )

                # -------------------------------------------------
                # BUILD RAG VECTOR STORE
                # -------------------------------------------------

                try:

                    with st.spinner(
                        "Preparing your Instagram report for AI chat..."
                    ):

                        vector_store = build_report_vector_store(report)

                    st.session_state.rag_vector_store = vector_store
                    st.session_state.rag_chat_history = []

                    st.success("Your report is ready for AI chat!")

                except Exception as error:

                    st.session_state.rag_vector_store = None

                    st.warning(
                        f"RAG system could not be initialized: {error}"
                    )

                # -------------------------------------------------
                # ANALYSIS COMPLETE
                # -------------------------------------------------

                st.session_state.analysis_done = True

                st.success(
                    "Instagram profile analyzed successfully!"
                )


# ---------------------------------------------------------
# DASHBOARD
# ---------------------------------------------------------

if st.session_state.analysis_done:

    profile = st.session_state.profile
    report = st.session_state.report

    if profile is None or report is None:
        st.error(
            "Analysis data is unavailable. Please analyze the profile again."
        )
        st.stop()

    # -----------------------------------------------------
    # CURRENT PROFILE
    # -----------------------------------------------------

    current_username = profile.get("username", "N/A")

    st.success(
        f"Showing analysis for: {st.session_state.analyzed_url}"
    )

    # -----------------------------------------------------
    # PROFILE DETAILS
    # -----------------------------------------------------

    st.subheader("👤 Profile Details")

    report_profile = report.get("profile", {})

    profile_pic_url = (
        profile.get("profilePicUrlHD")
        or profile.get("profilePicUrl")
        or profile.get("profile_pic_url")
        or report_profile.get("profile_pic_url")
    )

    full_name = (
        profile.get("fullName")
        or report_profile.get("full_name")
    )

    biography = (
        profile.get("biography")
        or report_profile.get("biography")
    )

    pic_cache_key = f"profile_pic_b64_{current_username}"

    if (
        pic_cache_key not in st.session_state
        or st.session_state.get("_last_pic_url")
        != st.session_state.get("analyzed_url")
    ):
        st.session_state[pic_cache_key] = fetch_image_as_base64(
            profile_pic_url
        )

        st.session_state["_last_pic_url"] = (
            st.session_state.get("analyzed_url")
        )

    profile_pic_b64 = st.session_state.get(pic_cache_key)

    if profile_pic_b64 or profile_pic_url:

        col_avatar, col_metrics = st.columns([1, 4])

        with col_avatar:

            if profile_pic_b64:

                st.markdown(
                    f"""
                    <div style="display:flex;justify-content:center;
                    align-items:center;padding-top:5px;">
                        <img src="{profile_pic_b64}" alt="{current_username}"
                        style="width:110px;height:110px;border-radius:50%;
                        object-fit:cover;border:3px solid #E1306C;
                        box-shadow:0 4px 14px rgba(225,48,108,0.25);" />
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            else:

                initials = (full_name or current_username or "?")[:2].upper()

                st.markdown(
                    f"""
                    <div style="display:flex;justify-content:center;
                    align-items:center;padding-top:5px;">
                        <div style="width:110px;height:110px;border-radius:50%;
                        background:linear-gradient(135deg,#E1306C,#833AB4);
                        display:flex;align-items:center;justify-content:center;
                        border:3px solid #E1306C;font-size:36px;
                        font-weight:700;color:#fff;">
                            {initials}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

    else:
        col_metrics = st.container()

    with col_metrics:

        if full_name:
            st.markdown(f"**{full_name}**")

        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.metric("Username", current_username)

        with col2:
            followers = profile.get("followersCount")
            st.metric(
                "Followers",
                f"{followers:,}" if followers is not None else "N/A"
            )

        with col3:
            following = profile.get("followsCount")
            st.metric(
                "Following",
                f"{following:,}" if following is not None else "N/A"
            )

        with col4:
            posts_count = profile.get("postsCount")
            st.metric(
                "Total Posts",
                f"{posts_count:,}" if posts_count is not None else "N/A"
            )

        with col5:
            analyzed_posts = len(profile.get("latestPosts") or [])
            st.metric("Posts Analyzed", f"{analyzed_posts:,}")

    verified = profile.get("verified", False)

    st.write(
        "Verified:",
        "Yes ✅" if verified else "No"
    )

    if biography:
        st.caption(biography)

    st.divider()

    # -----------------------------------------------------
    # FOLLOWER GROWTH
    # -----------------------------------------------------

    st.subheader("📈 Follower Growth")

    shared_history_file = (
        PROJECT_ROOT / "backend" / "data" / "profile_history.json"
    )

    user_history_file = (
        PROJECT_ROOT
        / "backend"
        / "data"
        / "history"
        / f"{current_username.lower()}_history.json"
    )

    history = []

    for file_path in [shared_history_file, user_history_file]:
        if file_path.exists():
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    file_history = json.load(file)

                if isinstance(file_history, list):
                    history.extend(file_history)

            except Exception as error:
                st.warning(f"Could not read {file_path.name}: {error}")

    user_history = [
        item for item in history
        if isinstance(item, dict)
        and item.get("username", "").lower()
        == current_username.lower()
    ]

    user_history = sorted(
        user_history,
        key=lambda item: item.get("date", "")
    )

    valid_history = [
        item for item in user_history
        if item.get("date")
        and item.get("followers") is not None
    ]

    if len(valid_history) >= 2:

        available_months = sorted(
            set(
                item["date"][:7]
                for item in valid_history
                if len(item["date"]) >= 7
            )
        )

        available_dates = [
            item["date"] for item in valid_history
        ]

        filter_months = st.checkbox(
            "Filter by months / dates",
            key="filter_months"
        )

        if not filter_months:

            first = valid_history[0]
            last = valid_history[-1]

            today_str = datetime.now().strftime("%Y-%m-%d")

            if last["date"] == today_str:
                st.info(
                    f"📅 Tracking started on **{first['date']}** "
                    f"and continues up to **today ({today_str})**. "
                    f"{len(valid_history)} snapshots recorded."
                )
            else:
                st.info(
                    f"📅 Tracking started on **{first['date']}**. "
                    f"Last snapshot: **{last['date']}**. "
                    f"{len(valid_history)} snapshots recorded."
                )

            show_growth_metrics(valid_history)

        else:

            if len(available_months) == 1:

                st.info(
                    f"All snapshots are within "
                    f"**{format_month_label(available_months[0])}**. "
                    "You can filter by date range below."
                )

                col1, col2 = st.columns(2)

                with col1:
                    start_date = st.selectbox(
                        "Start Date",
                        available_dates,
                        index=0,
                        key="select_start_date"
                    )

                with col2:
                    end_date = st.selectbox(
                        "End Date",
                        available_dates,
                        index=len(available_dates) - 1,
                        key="select_end_date"
                    )

                if start_date > end_date:
                    st.warning("Start Date must be before End Date.")
                else:
                    filtered_history = [
                        item for item in valid_history
                        if start_date <= item["date"] <= end_date
                    ]

                    if len(filtered_history) >= 2:
                        show_growth_metrics(filtered_history)
                    elif len(filtered_history) == 1:
                        st.info("Only one snapshot is available in this date range.")
                    else:
                        st.warning("No snapshots found in this date range.")

            else:

                filter_mode = st.radio(
                    "Filter Mode:",
                    ["Month Range", "Specific Month", "Date Range"],
                    horizontal=True,
                    key="month_filter_type"
                )

                if filter_mode == "Month Range":

                    col1, col2 = st.columns(2)

                    with col1:
                        start_month = st.selectbox(
                            "Start Month",
                            available_months,
                            format_func=format_month_label,
                            index=0,
                            key="select_start_month"
                        )

                    with col2:
                        end_month = st.selectbox(
                            "End Month",
                            available_months,
                            format_func=format_month_label,
                            index=len(available_months) - 1,
                            key="select_end_month"
                        )

                    if start_month > end_month:
                        st.warning("Start Month must be before End Month.")
                    else:
                        filtered_history = [
                            item for item in valid_history
                            if start_month <= item["date"][:7] <= end_month
                        ]

                        if len(filtered_history) >= 2:
                            show_growth_metrics(filtered_history)
                        elif len(filtered_history) == 1:
                            st.info("Only one snapshot is available in this month range.")
                        else:
                            st.warning("No snapshots found in this month range.")

                elif filter_mode == "Specific Month":

                    selected_month = st.selectbox(
                        "Select Month",
                        available_months,
                        format_func=format_month_label,
                        index=len(available_months) - 1,
                        key="select_single_month"
                    )

                    month_snapshots = [
                        item for item in valid_history
                        if item["date"][:7] == selected_month
                    ]

                    previous_snapshots = [
                        item for item in valid_history
                        if item["date"][:7] < selected_month
                    ]

                    if len(month_snapshots) >= 2:

                        show_growth_metrics(month_snapshots)

                    elif len(month_snapshots) == 1 and previous_snapshots:

                        comparison_history = [
                            previous_snapshots[-1],
                            month_snapshots[0]
                        ]

                        st.caption(
                            "Comparing the selected month's snapshot "
                            "with the previous available snapshot."
                        )

                        show_growth_metrics(comparison_history)

                    elif len(month_snapshots) == 1:

                        st.info(
                            "Only one snapshot is recorded in this month, "
                            "and no earlier snapshot is available."
                        )

                    else:
                        st.warning("No snapshots found for this month.")

                elif filter_mode == "Date Range":

                    col1, col2 = st.columns(2)

                    with col1:
                        start_date = st.selectbox(
                            "Start Date",
                            available_dates,
                            index=0,
                            key="select_start_date"
                        )

                    with col2:
                        end_date = st.selectbox(
                            "End Date",
                            available_dates,
                            index=len(available_dates) - 1,
                            key="select_end_date"
                        )

                    if start_date > end_date:
                        st.warning("Start Date must be before End Date.")
                    else:
                        filtered_history = [
                            item for item in valid_history
                            if start_date <= item["date"] <= end_date
                        ]

                        if len(filtered_history) >= 2:
                            show_growth_metrics(filtered_history)
                        elif len(filtered_history) == 1:
                            st.info("Only one snapshot is available in this date range.")
                        else:
                            st.warning("No snapshots found in this date range.")

    elif len(valid_history) == 1:

        st.info(
            f"Follower tracking started on {valid_history[0]['date']}. "
            "More snapshots are required to calculate growth."
        )

    else:

        st.info("No follower history is available yet.")

    st.divider()

    # -----------------------------------------------------
    # AI GROWTH RECOMMENDATIONS
    # -----------------------------------------------------

    col_rec_title, col_rec_btn = st.columns([4, 1])

    with col_rec_title:
        st.subheader("🤖 AI Growth Recommendations")

    with col_rec_btn:

        if st.button(
            "🔄 Refresh Advice",
            key="refresh_llm_advice",
            help="Generate fresh AI recommendations for this report"
        ):

            with st.spinner("Generating fresh AI growth advice..."):

                try:
                    new_rec = generate_recommendations(
                        report=report,
                        force_refresh=True
                    )

                    st.session_state.llm_recommendations = new_rec
                    st.rerun()

                except Exception as error:
                    st.error(
                        f"Failed to refresh recommendations: {error}"
                    )

    llm_recommendations = st.session_state.get(
        "llm_recommendations"
    )

    if llm_recommendations:

        if isinstance(llm_recommendations, str):

            st.markdown(llm_recommendations)

        elif isinstance(llm_recommendations, dict):

            recommendation_text = (
                llm_recommendations.get("recommendations")
                or llm_recommendations.get("response")
                or llm_recommendations.get("text")
            )

            if recommendation_text:
                st.markdown(recommendation_text)
            else:
                st.json(llm_recommendations)

        else:
            st.write(llm_recommendations)

    else:

        st.info(
            "AI growth recommendations are not available "
            "for this analysis."
        )

        if st.button("✨ Generate AI Growth Recommendations"):

            with st.spinner("Generating recommendations..."):

                try:
                    recommendations = generate_recommendations(
                        report=report,
                        force_refresh=True
                    )

                    st.session_state.llm_recommendations = recommendations
                    st.rerun()

                except Exception as error:
                    st.error(
                        f"Could not generate recommendations: {error}"
                    )

    st.divider()

    # -----------------------------------------------------
    # RAG CHAT
    # -----------------------------------------------------

    st.subheader("💬 Chat with Your Instagram Report")

    st.caption(
        "Ask questions about this Instagram profile, its analytics, "
        "post performance, and growth recommendations."
    )

    if st.session_state.rag_vector_store is None:

        st.info(
            "The report chat is not available because the RAG "
            "vector store could not be created."
        )

    else:

        # Display previous chat messages
        for message in st.session_state.rag_chat_history:

            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        question = st.chat_input(
            "Ask something about your Instagram report..."
        )

        if question:

            st.session_state.rag_chat_history.append({
                "role": "user",
                "content": question
            })

            with st.chat_message("user"):
                st.markdown(question)

            with st.chat_message("assistant"):

                with st.spinner("Searching your Instagram report..."):

                    try:

                        result = answer_report_question(
                            st.session_state.rag_vector_store,
                            question
                        )

                        answer = result.get(
                            "answer",
                            "I could not generate an answer."
                        )

                        sources = result.get("sources", [])

                        st.markdown(answer)

                        if sources:
                            st.caption(
                                "Sources: " + ", ".join(sources)
                            )

                        assistant_message = answer

                        if sources:
                            assistant_message += (
                                "\n\n**Sources:** "
                                + ", ".join(sources)
                            )

                        st.session_state.rag_chat_history.append({
                            "role": "assistant",
                            "content": assistant_message
                        })

                    except Exception as error:

                        error_message = (
                            f"Sorry, I could not answer that question: {error}"
                        )

                        st.error(error_message)

                        st.session_state.rag_chat_history.append({
                            "role": "assistant",
                            "content": error_message
                        })

    st.divider()

    # -----------------------------------------------------
    # INSTAGRAM ANALYTICS CHARTS
    # -----------------------------------------------------

    st.subheader("📊 Instagram Analytics Charts")

    if (
        "cached_charts" in st.session_state
        and st.session_state.get("cached_charts_user")
        == current_username
    ):

        charts = st.session_state.cached_charts

    else:

        try:

            charts = generate_charts(report)

            st.session_state.cached_charts = charts
            st.session_state.cached_charts_user = current_username

        except Exception as error:

            st.error(
                f"Charts could not be generated: {error}"
            )

            charts = {}

    col1, col2 = st.columns(2)

    # -----------------------------------------------------
    # LEFT COLUMN
    # -----------------------------------------------------

    with col1:

        if charts.get("content_distribution") is not None:

            st.subheader("Content Distribution")

            st.pyplot(
                charts["content_distribution"],
                clear_figure=False
            )

        if charts.get("posting_time") is not None:

            st.subheader("Posting Time Performance")

            st.pyplot(
                charts["posting_time"],
                clear_figure=False
            )

    # -----------------------------------------------------
    # RIGHT COLUMN
    # -----------------------------------------------------

    with col2:

        if charts.get("average_likes") is not None:

            st.subheader("Average Likes by Content Type")

            st.pyplot(
                charts["average_likes"],
                clear_figure=False
            )

        if charts.get("top_posts") is not None:

            st.subheader("Top 3 Performing Posts")

            st.pyplot(
                charts["top_posts"],
                clear_figure=False
            )