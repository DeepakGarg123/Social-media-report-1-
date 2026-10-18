import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


import json
import os
import base64
from datetime import datetime
import urllib.request

import streamlit as st

from backend.analytics.analytics import generate_analytics
from backend.llm.llm import generate_recommendations
from backend.scrapers.instagram_scraper import scrape_instagram
from backend.visualization.charts import generate_charts


def fetch_image_as_base64(url: str) -> str | None:
    """
    Fetch an image URL server-side (bypassing Instagram CDN hotlink/CORS blocks)
    and return it as a base64-encoded data URI string, or None on failure.
    Instagram CDN rejects requests from browsers but allows Python HTTP clients
    with a realistic User-Agent header.
    """
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

if "llm_recommendations" not in st.session_state:
    st.session_state.llm_recommendations = None

if "filter_months" not in st.session_state:
    st.session_state.filter_months = False



# ---------------------------------------------------------
# SIDEBAR CONFIGURATION (SCRAPING SPEED & CACHING)
# ---------------------------------------------------------

with st.sidebar:
    st.header("⚙️ Performance & Cache Settings")

    use_cache = st.checkbox(
        "⚡ Use Cached Data if Available",
        value=True,
        help="Loads profile data instantly (<1s) if available locally. Uncheck to force fresh live scraping from Apify."
    )

    scrape_mode = st.selectbox(
        "📊 Live Scraping Depth",
        options=[
            "15 Posts (Fast Mode ~5-10s)",
            "30 Posts (Balanced ~15-25s)",
            "50 Posts (Deep Analysis ~35-60s)"
        ],
        index=0,
        help="Reducing post count significantly speeds up live Apify scraping."
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

        # Reset previous analysis before starting a new one
        st.session_state.analysis_done = False
        st.session_state.profile = None
        st.session_state.report = None
        st.session_state.llm_recommendations = None
        st.session_state.pop("cached_charts", None)

        # Reset follower filters for the new profile
        st.session_state.filter_months = False
        for filter_key in [
            "select_start_month",
            "select_end_month",
            "select_single_month",
            "month_filter_type",
            "select_start_date",
            "select_end_date"
        ]:
            st.session_state.pop(filter_key, None)


        # -------------------------------------------------
        # SCRAPING
        # -------------------------------------------------

        with st.spinner("Retrieving Instagram profile data..."):

            try:
                profile = scrape_instagram(
                    instagram_url.strip(),
                    force_refresh=not use_cache,
                    max_posts=max_posts
                )

            except Exception as error:
                profile = None
                st.error(
                    f"Instagram scraping failed: {error}"
                )

        if profile is None:

            st.error(
                "Instagram profile could not be collected."
            )

        else:

            # -------------------------------------------------
            # ANALYTICS
            # -------------------------------------------------

            with st.spinner("Calculating Instagram analytics..."):

                try:
                    report = generate_analytics()

                except Exception as error:
                    report = None
                    st.error(
                        f"Analytics generation failed: {error}"
                    )

            if report is None:

                st.error(
                    "Analytics report could not be generated."
                )

            else:

                # -------------------------------------------------
                # SAVE CURRENT PROFILE REPORT
                # -------------------------------------------------

                st.session_state.profile = profile
                st.session_state.report = report
                st.session_state.analyzed_url = instagram_url.strip()

                # -------------------------------------------------
                # GEMINI RECOMMENDATIONS
                # -------------------------------------------------

                try:

                    with st.spinner(
                        "Generating AI growth recommendations..."
                    ):

                        llm_recommendations = (
                            generate_recommendations(force_refresh=not use_cache)
                        )

                    st.session_state.llm_recommendations = (
                        llm_recommendations
                    )

                except Exception as error:

                    st.session_state.llm_recommendations = None

                    st.warning(
                        f"AI recommendations could not be generated: {error}"
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


    # ---------------------------------------------------------
    # CURRENT PROFILE
    # ---------------------------------------------------------

    current_username = profile.get(
        "username",
        "N/A"
    )

    st.success(
        f"Showing analysis for: {st.session_state.analyzed_url}"
    )


    # ---------------------------------------------------------
    # PROFILE DETAILS
    # ---------------------------------------------------------

    st.subheader("👤 Profile Details")

    profile_pic_url = (
        profile.get("profilePicUrlHD")
        or profile.get("profilePicUrl")
        or profile.get("profile_pic_url")
        or (report.get("profile", {}) if isinstance(report, dict) else {}).get("profile_pic_url")
    )
    full_name = (
        profile.get("fullName")
        or (report.get("profile", {}) if isinstance(report, dict) else {}).get("full_name")
    )
    biography = (
        profile.get("biography")
        or (report.get("profile", {}) if isinstance(report, dict) else {}).get("biography")
    )

    # Fetch the profile picture server-side to bypass Instagram CDN
    # CORS / hotlink protection. Cache it so we don't re-fetch on every render.
    pic_cache_key = f"profile_pic_b64_{current_username}"
    if pic_cache_key not in st.session_state or st.session_state.get("analyzed_url") != st.session_state.get("_last_pic_url"):
        st.session_state[pic_cache_key] = fetch_image_as_base64(profile_pic_url)
        st.session_state["_last_pic_url"] = st.session_state.get("analyzed_url")

    profile_pic_b64 = st.session_state.get(pic_cache_key)

    if profile_pic_b64 or profile_pic_url:
        col_avatar, col_metrics = st.columns([1, 4])

        with col_avatar:
            if profile_pic_b64:
                # Embed as data URI — never blocked by CDN
                st.markdown(
                    f"""
                    <div style="display: flex; justify-content: center; align-items: center; padding-top: 5px;">
                        <img src="{profile_pic_b64}" alt="{current_username}"
                             style="width: 110px; height: 110px; border-radius: 50%; object-fit: cover;
                                    border: 3px solid #E1306C; box-shadow: 0 4px 14px rgba(225, 48, 108, 0.25);" />
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                # Fallback: show a placeholder avatar with initials
                initials = (full_name or current_username or "?")[:2].upper()
                st.markdown(
                    f"""
                    <div style="display: flex; justify-content: center; align-items: center; padding-top: 5px;">
                        <div style="width: 110px; height: 110px; border-radius: 50%; background: linear-gradient(135deg,#E1306C,#833AB4);
                                    display: flex; align-items: center; justify-content: center;
                                    border: 3px solid #E1306C; box-shadow: 0 4px 14px rgba(225,48,108,0.25);
                                    font-size: 36px; font-weight: 700; color: #fff; letter-spacing: 1px;">
                            {initials}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        with col_metrics:
            if full_name:
                st.markdown(f"**{full_name}**")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric(
                    "Username",
                    current_username
                )

            with col2:
                followers = profile.get(
                    "followersCount",
                    0
                )
                st.metric(
                    "Followers",
                    f"{followers:,}"
                )

            with col3:
                following = profile.get(
                    "followsCount"
                )
                st.metric(
                    "Following",
                    f"{following:,}" if following is not None else "N/A"
                )

            with col4:
                posts = profile.get(
                    "postsCount",
                    0
                )
                st.metric(
                    "Posts",
                    f"{posts:,}"
                )

            verified = profile.get(
                "verified",
                False
            )
            st.write(
                "Verified:",
                "Yes ✅" if verified else "No"
            )

            if biography:
                st.caption(biography)

    else:
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Username",
                current_username
            )

        with col2:
            followers = profile.get(
                "followersCount",
                0
            )
            st.metric(
                "Followers",
                f"{followers:,}"
            )

        with col3:
            following = profile.get(
                "followsCount"
            )
            st.metric(
                "Following",
                f"{following:,}" if following is not None else "N/A"
            )

        with col4:
            posts = profile.get(
                "postsCount",
                0
            )
            st.metric(
                "Posts",
                f"{posts:,}"
            )

        verified = profile.get(
            "verified",
            False
        )
        st.write(
            "Verified:",
            "Yes ✅" if verified else "No"
        )

        if biography:
            st.caption(biography)

    st.divider()


    # ---------------------------------------------------------
    # FOLLOWER GROWTH
    # ---------------------------------------------------------

    st.subheader("📈 Follower Growth")

    history_file = (
        "backend/data/profile_history.json"
    )

    if not os.path.exists(history_file):

        st.info(
            "Follower history is not available yet."
        )

    else:

        try:

            with open(
                history_file,
                "r",
                encoding="utf-8"
            ) as file:

                history = json.load(file)

        except Exception as error:

            st.error(
                f"Could not read follower history: {error}"
            )

            history = []


        # -----------------------------------------------------
        # FILTER HISTORY FOR CURRENT PROFILE ONLY (CASE-INSENSITIVE)
        # -----------------------------------------------------

        user_history = [
            item
            for item in history
            if item.get("username", "").lower() == current_username.lower()
        ]


        # Sort current profile's history only
        user_history = sorted(
            user_history,
            key=lambda item: item.get(
                "date",
                ""
            )
        )


        # Remove invalid snapshots
        valid_history = [
            item
            for item in user_history
            if (
                item.get("date")
                and item.get("followers") is not None
            )
        ]


        # -----------------------------------------------------
        # TWO OR MORE SNAPSHOTS
        # -----------------------------------------------------

        if len(valid_history) >= 2:

            def format_month_label(month_str):
                try:
                    return datetime.strptime(month_str, "%Y-%m").strftime("%B %Y")
                except Exception:
                    return month_str

            available_months = sorted(
                list(set(item["date"][:7] for item in valid_history if len(item.get("date", "")) >= 7))
            )
            available_dates = [item["date"] for item in valid_history]

            filter_months = st.checkbox(
                "Filter by months / dates",
                key="filter_months"
            )

            # -------------------------------------------------
            # COMPLETE HISTORY
            # -------------------------------------------------

            if not filter_months:

                first = valid_history[0]
                last = valid_history[-1]

                today_str = datetime.now().strftime("%Y-%m-%d")

                start_followers = first["followers"]
                end_followers = last["followers"]

                growth = end_followers - start_followers

                if start_followers > 0:
                    growth_percentage = (growth / start_followers) * 100
                else:
                    growth_percentage = 0

                # Show from the first time tracking started to today
                if last["date"] == today_str:
                    range_label = (
                        f"📅 Follower tracking started on **{first['date']}** — "
                        f"showing growth up to **today ({today_str})**  "
                        f"({len(valid_history)} snapshots recorded)"
                    )
                else:
                    range_label = (
                        f"📅 Follower tracking started on **{first['date']}** — "
                        f"last snapshot on **{last['date']}**  "
                        f"({len(valid_history)} snapshots recorded)  \n"
                        f"⚠️ No snapshot found for today ({today_str}). "
                        f"Re-analyze the profile to record today's follower count."
                    )

                st.info(range_label)

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric(
                        "Start Followers",
                        f"{start_followers:,}",
                        help=f"Followers when first recorded on {first['date']}"
                    )

                with col2:
                    st.metric(
                        "Current Followers",
                        f"{end_followers:,}",
                        help=f"Latest followers as of {last['date']}"
                    )

                with col3:
                    st.metric(
                        "Total Growth",
                        f"{growth:+,}",
                        help=f"Change from {first['date']} to {last['date']}"
                    )

                with col4:
                    st.metric(
                        "Growth %",
                        f"{growth_percentage:+.2f}%",
                        help="Percentage growth since tracking started"
                    )

                if growth > 0:
                    st.success(
                        f"📈 Gained **{growth:,} followers** from "
                        f"{first['date']} to {last['date']}"
                    )
                elif growth < 0:
                    st.error(
                        f"📉 Lost **{abs(growth):,} followers** from "
                        f"{first['date']} to {last['date']}"
                    )
                else:
                    st.info(
                        f"No follower change recorded from "
                        f"{first['date']} to {last['date']}."
                    )

                with st.expander("📋 View Snapshot Details", expanded=False):
                    table_rows = []
                    for idx, snap in enumerate(valid_history):
                        diff = (snap["followers"] - valid_history[idx - 1]["followers"]) if idx > 0 else 0
                        is_today = snap["date"] == today_str
                        table_rows.append({
                            "Date": f"{snap['date']} 🟢 Today" if is_today else snap["date"],
                            "Followers": f"{snap['followers']:,}",
                            "Daily Change": f"{diff:+,}" if idx > 0 else "Baseline (first record)"
                        })
                    st.dataframe(table_rows, use_container_width=True)

            # -------------------------------------------------
            # FILTERED HISTORY
            # -------------------------------------------------

            else:

                # Scenario 1: Only 1 month of snapshot data exists
                if len(available_months) == 1:
                    single_month = available_months[0]
                    month_label = format_month_label(single_month)

                    st.info(
                        f"📅 All recorded snapshots ({len(valid_history)}) are within **{month_label}**. "
                        "Month-to-month comparison will become available once data across multiple months is tracked. "
                        "You can filter snapshots by date range below:"
                    )

                    # Ensure safe state for date keys
                    if "select_start_date" in st.session_state and st.session_state.select_start_date not in available_dates:
                        del st.session_state.select_start_date
                    if "select_end_date" in st.session_state and st.session_state.select_end_date not in available_dates:
                        del st.session_state.select_end_date

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
                        st.warning("Please select a Start Date that comes before or is equal to the End Date.")
                    else:
                        range_history = [
                            item for item in valid_history
                            if start_date <= item["date"] <= end_date
                        ]

                        if len(range_history) >= 2:
                            first_snapshot = range_history[0]
                            last_snapshot = range_history[-1]

                            start_followers = first_snapshot["followers"]
                            end_followers = last_snapshot["followers"]

                            growth = end_followers - start_followers
                            growth_percentage = (growth / start_followers * 100) if start_followers > 0 else 0

                            st.write(
                                f"Showing follower growth from **{first_snapshot['date']}** to **{last_snapshot['date']}** "
                                f"({month_label}):"
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
                                st.success(f"Follower growth increased from {start_date} to {end_date} 📈")
                            elif growth < 0:
                                st.error(f"Follower growth decreased from {start_date} to {end_date} 📉")
                            else:
                                st.info(f"Follower count remained unchanged from {start_date} to {end_date}.")

                            with st.expander("📋 View Filtered Snapshots", expanded=False):
                                table_rows = []
                                for idx, snap in enumerate(range_history):
                                    diff = (snap["followers"] - range_history[idx - 1]["followers"]) if idx > 0 else 0
                                    table_rows.append({
                                        "Date": snap["date"],
                                        "Followers": f"{snap['followers']:,}",
                                        "Daily Change": f"{diff:+,}" if idx > 0 else "Baseline"
                                    })
                                st.dataframe(table_rows, use_container_width=True)

                        elif len(range_history) == 1:
                            st.info(
                                f"Single snapshot selected ({range_history[0]['date']}: {range_history[0]['followers']:,} followers). "
                                "Please select different start and end dates to calculate growth."
                            )
                        else:
                            st.warning(f"No follower snapshots available between {start_date} and {end_date}.")

                # Scenario 2: Multiple months of snapshot data exist
                elif len(available_months) > 1:

                    filter_mode = st.radio(
                        "Filter Mode:",
                        ["Month Range", "Specific Month", "Date Range"],
                        horizontal=True,
                        key="month_filter_type"
                    )

                    if filter_mode == "Month Range":

                        # Clean up stale session keys if options changed
                        if "select_start_month" in st.session_state and st.session_state.select_start_month not in available_months:
                            del st.session_state.select_start_month
                        if "select_end_month" in st.session_state and st.session_state.select_end_month not in available_months:
                            del st.session_state.select_end_month

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
                            st.warning("Please select a Start Month that comes before or is equal to the End Month.")
                        else:
                            range_history = [
                                item for item in valid_history
                                if start_month <= item["date"][:7] <= end_month
                            ]

                            if len(range_history) >= 2:
                                first_snapshot = range_history[0]
                                last_snapshot = range_history[-1]

                                start_followers = first_snapshot["followers"]
                                end_followers = last_snapshot["followers"]

                                growth = end_followers - start_followers
                                growth_percentage = (growth / start_followers * 100) if start_followers > 0 else 0

                                start_label = format_month_label(start_month)
                                end_label = format_month_label(end_month)

                                if start_month == end_month:
                                    st.write(
                                        f"Showing follower growth within **{start_label}** "
                                        f"({first_snapshot['date']} → {last_snapshot['date']}):"
                                    )
                                else:
                                    st.write(
                                        f"Showing follower growth from **{start_label}** to **{end_label}** "
                                        f"({first_snapshot['date']} → {last_snapshot['date']}):"
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

                                if start_month == end_month:
                                    if growth > 0:
                                        st.success(f"Follower growth increased in {start_label} 📈")
                                    elif growth < 0:
                                        st.error(f"Follower growth decreased in {start_label} 📉")
                                    else:
                                        st.info(f"Follower count remained unchanged in {start_label}.")
                                else:
                                    if growth > 0:
                                        st.success(f"Follower growth increased from {start_label} to {end_label} 📈")
                                    elif growth < 0:
                                        st.error(f"Follower growth decreased from {start_label} to {end_label} 📉")
                                    else:
                                        st.info(f"Follower count remained unchanged from {start_label} to {end_label}.")

                                with st.expander("📋 View Filtered Snapshots", expanded=False):
                                    table_rows = []
                                    for idx, snap in enumerate(range_history):
                                        diff = (snap["followers"] - range_history[idx - 1]["followers"]) if idx > 0 else 0
                                        table_rows.append({
                                            "Date": snap["date"],
                                            "Followers": f"{snap['followers']:,}",
                                            "Daily Change": f"{diff:+,}" if idx > 0 else "Baseline"
                                        })
                                    st.dataframe(table_rows, use_container_width=True)

                            elif len(range_history) == 1:
                                st.info(
                                    f"Only one snapshot ({range_history[0]['date']}: {range_history[0]['followers']:,} followers) "
                                    f"is available in the selected range. At least two snapshots are required to calculate growth."
                                )
                            else:
                                st.warning(f"No follower snapshots available between {format_month_label(start_month)} and {format_month_label(end_month)}.")

                    elif filter_mode == "Specific Month":

                        if "select_single_month" in st.session_state and st.session_state.select_single_month not in available_months:
                            del st.session_state.select_single_month

                        selected_month = st.selectbox(
                            "Select Month",
                            available_months,
                            format_func=format_month_label,
                            index=len(available_months) - 1,
                            key="select_single_month"
                        )

                        month_label = format_month_label(selected_month)
                        month_snapshots = [
                            item for item in valid_history
                            if item["date"][:7] == selected_month
                        ]
                        prior_snapshots = [
                            item for item in valid_history
                            if item["date"][:7] < selected_month
                        ]

                        if len(month_snapshots) >= 2:
                            first_snapshot = month_snapshots[0]
                            last_snapshot = month_snapshots[-1]

                            start_followers = first_snapshot["followers"]
                            end_followers = last_snapshot["followers"]

                            growth = end_followers - start_followers
                            growth_percentage = (growth / start_followers * 100) if start_followers > 0 else 0

                            st.write(
                                f"Showing follower growth within **{month_label}** "
                                f"({first_snapshot['date']} → {last_snapshot['date']}):"
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
                                st.success(f"Follower growth increased in {month_label} 📈")
                            elif growth < 0:
                                st.error(f"Follower growth decreased in {month_label} 📉")
                            else:
                                st.info(f"Follower count remained unchanged in {month_label}.")

                            with st.expander("📋 View Month Snapshots", expanded=False):
                                table_rows = []
                                for idx, snap in enumerate(month_snapshots):
                                    diff = (snap["followers"] - month_snapshots[idx - 1]["followers"]) if idx > 0 else 0
                                    table_rows.append({
                                        "Date": snap["date"],
                                        "Followers": f"{snap['followers']:,}",
                                        "Daily Change": f"{diff:+,}" if idx > 0 else "Baseline"
                                    })
                                st.dataframe(table_rows, use_container_width=True)

                        elif len(month_snapshots) == 1 and prior_snapshots:
                            prev_snapshot = prior_snapshots[-1]
                            curr_snapshot = month_snapshots[0]

                            start_followers = prev_snapshot["followers"]
                            end_followers = curr_snapshot["followers"]

                            growth = end_followers - start_followers
                            growth_percentage = (growth / start_followers * 100) if start_followers > 0 else 0
                            prev_month_label = format_month_label(prev_snapshot["date"][:7])

                            st.write(
                                f"Showing month-over-month growth from **{prev_snapshot['date']}** ({prev_month_label}) "
                                f"to **{curr_snapshot['date']}** ({month_label}):"
                            )

                            col1, col2, col3, col4 = st.columns(4)

                            with col1:
                                st.metric("Previous Followers", f"{start_followers:,}")

                            with col2:
                                st.metric(f"{month_label} Followers", f"{end_followers:,}")

                            with col3:
                                st.metric("Growth", f"{growth:+,}")

                            with col4:
                                st.metric("Growth %", f"{growth_percentage:+.2f}%")

                            if growth > 0:
                                st.success(f"Follower growth increased from {prev_month_label} to {month_label} 📈")
                            elif growth < 0:
                                st.error(f"Follower growth decreased from {prev_month_label} to {month_label} 📉")
                            else:
                                st.info(f"Follower count remained unchanged from {prev_month_label} to {month_label}.")

                            with st.expander("📋 View Snapshots", expanded=False):
                                table_rows = [
                                    {"Date": prev_snapshot["date"], "Followers": f"{prev_snapshot['followers']:,}", "Daily Change": "Baseline"},
                                    {"Date": curr_snapshot["date"], "Followers": f"{curr_snapshot['followers']:,}", "Daily Change": f"{growth:+,}"}
                                ]
                                st.dataframe(table_rows, use_container_width=True)

                        elif len(month_snapshots) == 1:
                            st.info(
                                f"Only one snapshot ({month_snapshots[0]['date']}: {month_snapshots[0]['followers']:,} followers) "
                                f"is recorded in {month_label}. Tracking began in this month, so more snapshots are required to calculate growth."
                            )
                        else:
                            st.warning(f"No follower snapshots recorded in {month_label}.")

                    elif filter_mode == "Date Range":

                        if "select_start_date" in st.session_state and st.session_state.select_start_date not in available_dates:
                            del st.session_state.select_start_date
                        if "select_end_date" in st.session_state and st.session_state.select_end_date not in available_dates:
                            del st.session_state.select_end_date

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
                            st.warning("Please select a Start Date that comes before or is equal to the End Date.")
                        else:
                            range_history = [
                                item for item in valid_history
                                if start_date <= item["date"] <= end_date
                            ]

                            if len(range_history) >= 2:
                                first_snapshot = range_history[0]
                                last_snapshot = range_history[-1]

                                start_followers = first_snapshot["followers"]
                                end_followers = last_snapshot["followers"]

                                growth = end_followers - start_followers
                                growth_percentage = (growth / start_followers * 100) if start_followers > 0 else 0

                                st.write(
                                    f"Showing follower growth from **{first_snapshot['date']}** to **{last_snapshot['date']}**:"
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
                                    st.success(f"Follower growth increased from {start_date} to {end_date} 📈")
                                elif growth < 0:
                                    st.error(f"Follower growth decreased from {start_date} to {end_date} 📉")
                                else:
                                    st.info(f"Follower count remained unchanged from {start_date} to {end_date}.")

                                with st.expander("📋 View Filtered Snapshots", expanded=False):
                                    table_rows = []
                                    for idx, snap in enumerate(range_history):
                                        diff = (snap["followers"] - range_history[idx - 1]["followers"]) if idx > 0 else 0
                                        table_rows.append({
                                            "Date": snap["date"],
                                            "Followers": f"{snap['followers']:,}",
                                            "Daily Change": f"{diff:+,}" if idx > 0 else "Baseline"
                                        })
                                    st.dataframe(table_rows, use_container_width=True)

                            elif len(range_history) == 1:
                                st.info(
                                    f"Single snapshot selected ({range_history[0]['date']}: {range_history[0]['followers']:,} followers). "
                                    "Please select different start and end dates to calculate growth."
                                )
                            else:
                                st.warning(f"No follower snapshots available between {start_date} and {end_date}.")

                else:
                    st.warning("No valid snapshot dates found to filter.")



        # -----------------------------------------------------
        # ONLY ONE SNAPSHOT
        # -----------------------------------------------------

        elif len(valid_history) == 1:

            snapshot = valid_history[0]

            st.info(
                f"Follower tracking started on "
                f"{snapshot['date']}. "
                "More snapshots are required to calculate growth."
            )


        # -----------------------------------------------------
        # NO SNAPSHOTS
        # -----------------------------------------------------

        else:

            st.info(
                "No follower history is available yet."
            )


    st.divider()


    # ---------------------------------------------------------
    # AI GROWTH RECOMMENDATIONS
    # ---------------------------------------------------------

    col_rec_title, col_rec_btn = st.columns([4, 1])
    with col_rec_title:
        st.subheader("🤖 AI Growth Recommendations")
    with col_rec_btn:
        if st.button("🔄 Refresh Advice", key="refresh_llm_advice", help="Generate fresh AI recommendations for this report"):
            with st.spinner("Generating fresh AI growth advice..."):
                try:
                    new_rec = generate_recommendations(force_refresh=True)
                    st.session_state.llm_recommendations = new_rec
                    st.rerun()
                except Exception as err:
                    st.error(f"Failed to refresh recommendations: {err}")

    llm_recommendations = (
        st.session_state.get(
            "llm_recommendations"
        )
    )

    if llm_recommendations:
        with st.container():
            if isinstance(
                llm_recommendations,
                str
            ):
                st.markdown(
                    llm_recommendations
                )

            elif isinstance(
                llm_recommendations,
                dict
            ):
                recommendation_text = (
                    llm_recommendations.get(
                        "recommendations"
                    )
                    or llm_recommendations.get(
                        "response"
                    )
                    or llm_recommendations.get(
                        "text"
                    )
                )

                if recommendation_text:
                    st.markdown(
                        recommendation_text
                    )
                else:
                    st.json(
                        llm_recommendations
                    )

            else:
                st.write(
                    llm_recommendations
                )

    else:
        st.info(
            "AI growth recommendations are not available "
            "for this analysis."
        )
        if st.button("✨ Generate AI Growth Recommendations"):
            with st.spinner("Generating recommendations..."):
                try:
                    rec = generate_recommendations(force_refresh=True)
                    st.session_state.llm_recommendations = rec
                    st.rerun()
                except Exception as err:
                    st.error(f"Could not generate recommendations: {err}")


    st.divider()


    st.subheader("📊 Instagram Analytics Charts")

    # Charts are generated from the CURRENT report and cached in session_state (no old PNG files used).
    if "cached_charts" in st.session_state and st.session_state.get("cached_charts_user") == current_username:
        charts = st.session_state.cached_charts
    else:
        try:
            charts = generate_charts(
                report
            )
            st.session_state.cached_charts = charts
            st.session_state.cached_charts_user = current_username
        except Exception as error:
            st.error(
                f"Charts could not be generated: {error}"
            )
            charts = {}


    col1, col2 = st.columns(2)


    # ---------------------------------------------------------
    # LEFT COLUMN
    # ---------------------------------------------------------

    with col1:

        if charts.get(
            "content_distribution"
        ) is not None:

            st.subheader(
                "Content Distribution"
            )

            st.pyplot(
                charts["content_distribution"],
                clear_figure=True
            )


        if charts.get(
            "posting_time"
        ) is not None:

            st.subheader(
                "Posting Time Performance"
            )

            st.pyplot(
                charts["posting_time"],
                clear_figure=True
            )


    # ---------------------------------------------------------
    # RIGHT COLUMN
    # ---------------------------------------------------------

    with col2:

        if charts.get(
            "average_likes"
        ) is not None:

            st.subheader(
                "Average Likes by Content Type"
            )

            st.pyplot(
                charts["average_likes"],
                clear_figure=True
            )


        if charts.get(
            "top_posts"
        ) is not None:

            st.subheader(
                "Top 3 Performing Posts"
            )

            st.pyplot(
                charts["top_posts"],
                clear_figure=True
            )
