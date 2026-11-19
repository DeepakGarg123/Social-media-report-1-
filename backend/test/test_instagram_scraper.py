
from backend.scrapers.instagram_scraper import scrape_instagram

result = scrape_instagram(
    "https://www.instagram.com/jay.sheru/",
    return_data=True,
    save_shared_files=False
)

if result:
    profile, posts = result

    print("Username:", profile.get("username"))
    print("Posts collected:", len(posts))
