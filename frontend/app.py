import sys
import os
import json
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from backend.scrapers.instagram_scraper import scrape_instagram
from backend.analytics.analytics import generate_analytics
from backend.visualization.charts import generate_charts


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

if "analysis_done" not in st.session_state:
    st.session_state.analysis_done = False

if "profile" not in st.session_state:
    st.session_state.profile = None

if "report" not in st.session_state:
    st.session_state.report = None

if "analyzed_url" not in st.session_state:
    st.session_state.analyzed_url = ""

instagram_url = st.text_input(
    "Enter Instagram Profile URL",
    placeholder="https://www.instagram.com/username/"
)

# ---------------------------------------------------------
# ANALYZE PROFILE
# ---------------------------------------------------------

if st.button("Analyze Profile"):

    if not instagram_url:
        st.warning("Please enter an Instagram profile URL.")

    else:

        with st.spinner("Scraping Instagram profile..."):
            profile = scrape_instagram(instagram_url)

        if profile is None:

            st.error("Instagram profile could not be collected.")

            st.session_state.analysis_done = False
            st.session_state.profile = None
            st.session_state.report = None

        else:

            with st.spinner("Calculating Instagram analytics..."):
                report = generate_analytics()

            if report is None:

                st.error("Analytics generation failed.")

                st.session_state.analysis_done = False
                st.session_state.profile = None
                st.session_state.report = None

            else:

                st.session_state.profile = profile
                st.session_state.report = report
                st.session_state.analyzed_url = instagram_url
                st.session_state.analysis_done = True

                st.success("Instagram profile analyzed successfully!")

# ---------------------------------------------------------
# DASHBOARD
# ---------------------------------------------------------

if st.session_state.analysis_done:

    profile = st.session_state.profile
    report = st.session_state.report

    st.success(
        "Showing analysis for: "
        + st.session_state.analyzed_url
    )

    # ---------------------------------------------------------
    # PROFILE DETAILS
    # ---------------------------------------------------------

    st.subheader("Profile Details")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Username",
            profile.get("username", "N/A")
        )

    with col2:
        followers = profile.get("followersCount", 0)

        st.metric(
            "Followers",
            f"{followers:,}"
        )

    with col3:
        following = profile.get("followsCount")

        if following is not None:
            st.metric(
                "Following",
                f"{following:,}"
            )
        else:
            st.metric(
                "Following",
                "N/A"
            )

    with col4:
        posts = profile.get("postsCount", 0)

        st.metric(
            "Posts",
            f"{posts:,}"
        )

    verified = profile.get("verified", False)

    st.write(
        "Verified:",
        "Yes" if verified else "No"
    )

    st.divider()

    # ---------------------------------------------------------
    # FOLLOWER GROWTH
    # ---------------------------------------------------------

    st.subheader("📈 Follower Growth")

    history_file = "backend/data/profile_history.json"

    if os.path.exists(history_file):

        with open(
            history_file,
            "r",
            encoding="utf-8"
        ) as f:
            history = json.load(f)

        history = sorted(
            history,
            key=lambda item: item.get("date", "")
        )

        valid_history = [
            item
            for item in history
            if item.get("date")
            and item.get("followers") is not None
        ]

        if len(valid_history) >= 2:

            filter_months = st.checkbox(
                "Filter by months",
                key="filter_months"
            )

            if not filter_months:

                first = valid_history[0]
                last = valid_history[-1]

                start_followers = first["followers"]
                end_followers = last["followers"]

                growth = end_followers - start_followers

                if start_followers > 0:
                    growth_percentage = (
                        growth / start_followers
                    ) * 100
                else:
                    growth_percentage = 0

                st.write(
                    f"Showing complete follower history: "
                    f"{first['date']} → {last['date']}"
                )

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric(
                        "Start Followers",
                        f"{start_followers:,}"
                    )

                with col2:
                    st.metric(
                        "End Followers",
                        f"{end_followers:,}"
                    )

                with col3:
                    st.metric(
                        "Growth",
                        f"{growth:+,}"
                    )

                with col4:
                    st.metric(
                        "Growth %",
                        f"{growth_percentage:+.2f}%"
                    )

                if growth > 0:
                    st.success("Follower growth increased 📈")
                elif growth < 0:
                    st.error("Follower growth decreased 📉")
                else:
                    st.info("No follower growth was recorded.")

            else:

                try:
                    first_date = datetime.strptime(
                        valid_history[0]["date"],
                        "%Y-%m-%d"
                    )

                    last_date = datetime.strptime(
                        valid_history[-1]["date"],
                        "%Y-%m-%d"
                    )

                except ValueError:

                    st.error(
                        "Follower history contains an invalid date format."
                    )

                    first_date = None
                    last_date = None

                if first_date and last_date:

                    available_months = []

                    current_year = first_date.year
                    current_month = first_date.month

                    while (
                        current_year < last_date.year
                        or (
                            current_year == last_date.year
                            and current_month <= last_date.month
                        )
                    ):

                        available_months.append(
                            f"{current_year:04d}-{current_month:02d}"
                        )

                        if current_month == 12:
                            current_month = 1
                            current_year += 1
                        else:
                            current_month += 1

                    col1, col2 = st.columns(2)

                    with col1:
                        start_month = st.selectbox(
                            "Start Month",
                            available_months,
                            index=0,
                            key="start_month"
                        )

                    with col2:
                        end_month = st.selectbox(
                            "End Month",
                            available_months,
                            index=len(available_months) - 1,
                            key="end_month"
                        )

                    if start_month > end_month:

                        st.warning(
                            "Please select a start month that "
                            "comes before the end month."
                        )

                    else:

                        start_data = [
                            item
                            for item in valid_history
                            if item["date"][:7] == start_month
                        ]

                        end_data = [
                            item
                            for item in valid_history
                            if item["date"][:7] == end_month
                        ]

                        if not start_data:

                            st.warning(
                                f"Follower data is not available for "
                                f"{start_month}. Please select a month "
                                "with stored follower history."
                            )

                        elif not end_data:

                            st.warning(
                                f"Follower data is not available for "
                                f"{end_month}. Please select a month "
                                "with stored follower history."
                            )

                        else:

                            start_snapshot = start_data[0]
                            end_snapshot = end_data[-1]

                            start_followers = start_snapshot["followers"]
                            end_followers = end_snapshot["followers"]

                            growth = (
                                end_followers
                                - start_followers
                            )

                            if start_followers > 0:
                                growth_percentage = (
                                    growth / start_followers
                                ) * 100
                            else:
                                growth_percentage = 0

                            st.write(
                                f"Showing follower growth from "
                                f"{start_snapshot['date']} to "
                                f"{end_snapshot['date']}"
                            )

                            col1, col2, col3, col4 = st.columns(4)

                            with col1:
                                st.metric(
                                    "Start Followers",
                                    f"{start_followers:,}"
                                )

                            with col2:
                                st.metric(
                                    "End Followers",
                                    f"{end_followers:,}"
                                )

                            with col3:
                                st.metric(
                                    "Growth",
                                    f"{growth:+,}"
                                )

                            with col4:
                                st.metric(
                                    "Growth %",
                                    f"{growth_percentage:+.2f}%"
                                )

                            if growth > 0:
                                st.success(
                                    f"Follower growth increased "
                                    f"from {start_month} to {end_month} 📈"
                                )
                            elif growth < 0:
                                st.error(
                                    f"Follower growth decreased "
                                    f"from {start_month} to {end_month} 📉"
                                )
                            else:
                                st.info(
                                    "Follower count remained unchanged."
                                )

        elif len(valid_history) == 1:

            snapshot = valid_history[0]

            st.info(
                f"Follower tracking started on {snapshot['date']}. "
                "More snapshots are required to calculate growth."
            )

        else:

            st.info("No follower history is available yet.")

    else:

        st.info("Follower history is not available yet.")

    st.divider()

    # ---------------------------------------------------------
    # CHARTS
    # ---------------------------------------------------------

    st.subheader("📊 Instagram Analytics Charts")

    try:
        with st.spinner("Generating analytics charts..."):
            charts = generate_charts(report)

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Content Distribution")
            if charts.get("content_distribution") is not None:
                st.pyplot(charts["content_distribution"], clear_figure=True)
            else:
                st.info("No content distribution data available.")

            st.subheader("Posting Time Performance")
            if charts.get("posting_time") is not None:
                st.pyplot(charts["posting_time"], clear_figure=True)
            else:
                st.info("No posting time data available.")

        with col2:
            st.subheader("Average Likes by Content Type")
            if charts.get("average_likes") is not None:
                st.pyplot(charts["average_likes"], clear_figure=True)
            else:
                st.info("No average likes data available.")

            st.subheader("Top 3 Performing Posts")
            if charts.get("top_posts") is not None:
                st.pyplot(charts["top_posts"], clear_figure=True)
            else:
                st.info("No top posts data available.")

    except Exception as error:
        st.error(f"Charts could not be generated: {error}")
