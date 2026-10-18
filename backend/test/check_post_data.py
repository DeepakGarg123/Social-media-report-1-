import json

with open(
    "backend/data/instagram_data.json",
    "r",
    encoding="utf-8"
) as f:
    posts = json.load(f)

target_posts = [
    "DM5lwWPBYhx",
    "CuuCPv_pfnY",
    "DTFdq6uki-L"
]

for post in posts:

    if post.get("shortCode") in target_posts:

        print("\n===================================")
        print("SHORT CODE:", post.get("shortCode"))
        print("===================================")

        print("Caption:", post.get("caption"))
        print("Type:", post.get("type"))
        print("URL:", post.get("url"))
        print("Timestamp:", post.get("timestamp"))
        print("Likes:", post.get("likesCount"))
        print("Comments:", post.get("commentsCount"))