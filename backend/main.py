from backend.scrapers.instagram_scraper import scrape_instagram
from backend.analytics.analytics import generate_analytics
from backend.visualization.charts import generate_charts
from backend.llm.llm import generate_recommendations


print("===================================")
print("     Instagram AI Growth Report")
print("===================================")


# --------------------------------------------------
# STEP 1: GET INSTAGRAM PROFILE
# --------------------------------------------------

instagram_url = input(
    "\nEnter Instagram profile URL: "
)


# --------------------------------------------------
# STEP 2: SCRAPE INSTAGRAM DATA
# --------------------------------------------------

print(
    "\n==================================="
)

print(
    "        Instagram Scraping"
)

print(
    "===================================\n"
)


profile = scrape_instagram(
    instagram_url
)


if profile is None:

    print(
        "\nInstagram scraping failed."
    )

    exit()


print(
    "\n==================================="
)

print(
    "     Instagram Profile Collected"
)

print(
    "===================================\n"
)


print(
    "Username:",
    profile["username"]
)

print(
    "Followers:",
    profile["followersCount"]
)

print(
    "Posts:",
    profile["postsCount"]
)

print(
    "\nScraping completed successfully."
)


# --------------------------------------------------
# STEP 3: RUN ANALYTICS
# --------------------------------------------------

print(
    "\n==================================="
)

print(
    "          Running Analytics"
)

print(
    "===================================\n"
)


report = generate_analytics()


if report is None:

    print(
        "\nAnalytics generation failed."
    )

    exit()


print(
    "\n==================================="
)

print(
    "        Analytics Completed"
)

print(
    "===================================\n"
)


print(
    "Username:",
    report["profile"]["username"]
)

print(
    "Followers:",
    report["profile"]["followers"]
)

print(
    "Growth:",
    report["growth"]["growth"]
)

print(
    "Growth %:",
    report["growth"]["growth_percentage"]
)


# --------------------------------------------------
# STEP 4: GENERATE CHARTS
# --------------------------------------------------

print(
    "\n==================================="
)

print(
    "         Generating Charts"
)

print(
    "===================================\n"
)


try:

    generate_charts()

    print(
        "\nCharts generated successfully."
    )

except Exception as error:

    print(
        "\nChart generation failed:"
    )

    print(error)


# --------------------------------------------------
# STEP 5: GENERATE LLM RECOMMENDATIONS
# --------------------------------------------------

print(
    "\n==================================="
)

print(
    "     Generating AI Recommendations"
)

print(
    "===================================\n"
)


try:

    llm_response = generate_recommendations()

    print(
        "\nAI recommendations generated successfully."
    )

except Exception as error:

    print(
        "\nLLM recommendation generation failed:"
    )

    print(error)


# --------------------------------------------------
# FINAL STATUS
# --------------------------------------------------

print(
    "\n==================================="
)

print(
    "      Instagram AI Report Ready"
)

print(
    "==================================="
)

print(
    "\nGenerated files:"
)

print(
    "1. analytics_report.json"
)

print(
    "2. llm_recommendations.json"
)

print(
    "3. content_distribution.png"
)

print(
    "4. average_likes_content_type.png"
)

print(
    "5. posting_time_performance.png"
)

print(
    "6. top_3_posts.png"
)

print(
    "\nPipeline completed successfully."
)