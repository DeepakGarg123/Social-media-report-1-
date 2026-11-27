from backend.scrapers.bright_data_scraper import (
    normalize_profile,
    normalize_post
)


username = "sidhu_moosewala"

profile_data = {
    "account": "sidhu_moosewala",
    "full_name": "Sidhu Moose Wala",
    "followers": 1000,
    "following": 50,
    "posts_count": 100,
    "is_verified": True,
    "is_private": False
}

post_data = {
    "user_posted": "sidhu_moosewala",
    "url": "https://www.instagram.com/p/example/",
    "description": "Test Instagram post",
    "likes": 500,
    "num_comments": 25,
    "date_posted": "2026-11-20",
    "shortcode": "ABC123",
    "content_type": "reel"
}

profile = normalize_profile(profile_data, username)
post = normalize_post(post_data, username)

print("NORMALIZED PROFILE")
print(profile)

print("\nNORMALIZED POST")
print(post)

assert profile["followersCount"] == 1000
assert profile["verified"] is True
assert post["likesCount"] == 500
assert post["commentsCount"] == 25
assert post["ownerUsername"] == username

print("\nPASS: Normalization tests successful!")