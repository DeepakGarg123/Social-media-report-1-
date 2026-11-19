from backend.scrapers.instagram_scraper import scrape_instagram
from backend.analytics.analytics import generate_analytics
from backend.llm.llm import generate_recommendations


result = scrape_instagram(
    "https://www.instagram.com/jay.sheru/",
    return_data=True,
    save_shared_files=False
)

if result:
    profile, posts = result

    report = generate_analytics(
        profile=profile,
        data=posts,
        save_report=False
    )
    recommendations = generate_recommendations(
        report=report,
        force_refresh=True
    )

    print("\nRecommendations Test Successful!")
    print(recommendations[:500])

    print("\nAnalytics Test Successful!")
    print("Username:", report["profile"]["username"])
    print("Followers:", report["profile"]["followers"])
    print("Analyzed posts:", len(posts))
    print("Total likes:", report["metrics"]["total_likes"])
    print("Total comments:", report["metrics"]["total_comments"])
    print("Top posts:", len(report["top_posts"]))

else:
    print("Instagram scraping failed.")
