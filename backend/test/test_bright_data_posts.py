
import os
import time
import requests

from dotenv import load_dotenv


load_dotenv()

API_KEY = os.getenv("BRIGHT_DATA_API_KEY")

PROFILE_DATASET_ID = "gd_l1vikfch901nx3by4"
POST_DATASET_ID = "gd_lk5ns7kz21pck8jpis"

BASE_URL = "https://api.brightdata.com/datasets/v3"

USERNAME = "sidhu_moosewala"


def get_headers():
    if not API_KEY:
        raise ValueError("BRIGHT_DATA_API_KEY is missing from .env")

    return {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }


def trigger_dataset(dataset_id, payload):
    url = f"{BASE_URL}/trigger"

    params = {
        "dataset_id": dataset_id,
        "format": "json"
    }

    response = requests.post(
        url,
        headers=get_headers(),
        params=params,
        json=payload,
        timeout=60
    )

    response.raise_for_status()

    result = response.json()

    snapshot_id = result.get("snapshot_id")

    if not snapshot_id:
        raise Exception(f"Snapshot ID missing: {result}")

    print(f"Snapshot started: {snapshot_id}")

    return snapshot_id


def wait_for_snapshot(snapshot_id, max_attempts=30):
    url = f"{BASE_URL}/progress/{snapshot_id}"

    for attempt in range(max_attempts):
        response = requests.get(
            url,
            headers=get_headers(),
            timeout=30
        )

        response.raise_for_status()

        result = response.json()
        status = result.get("status")

        print(f"Attempt {attempt + 1}: {status}")

        if status == "ready":
            print("Snapshot is ready!")
            return

        if status in ("failed", "error"):
            raise Exception(f"Snapshot failed: {result}")

        time.sleep(10)

    raise TimeoutError("Snapshot processing timed out.")


def download_snapshot(snapshot_id):
    url = f"{BASE_URL}/snapshot/{snapshot_id}"

    response = requests.get(
        url,
        headers=get_headers(),
        params={"format": "json"},
        timeout=120
    )

    response.raise_for_status()

    data = response.json()

    if not isinstance(data, list):
        raise Exception("Unexpected snapshot response format.")

    return data


def run_dataset(dataset_id, payload):
    snapshot_id = trigger_dataset(dataset_id, payload)

    wait_for_snapshot(snapshot_id)

    return download_snapshot(snapshot_id)


def extract_post_urls(profile_data):
    post_urls = []

    embedded_posts = profile_data.get("posts", [])

    if not isinstance(embedded_posts, list):
        return post_urls

    for post in embedded_posts:
        if not isinstance(post, dict):
            continue

        post_url = (
            post.get("url")
            or post.get("post_url")
            or post.get("postUrl")
            or post.get("link")
        )

        if post_url and post_url not in post_urls:
            post_urls.append(post_url)

    return post_urls


def scrape_profile(username):
    print("\nScraping Instagram profile...")

    profile_url = f"https://www.instagram.com/{username}/"

    records = run_dataset(
        PROFILE_DATASET_ID,
        [{"url": profile_url}]
    )

    if not records:
        raise Exception("No profile data returned.")

    print(f"Profile records received: {len(records)}")

    return records[0]


def scrape_posts(post_urls):
    if not post_urls:
        print("\nNo post URLs found.")
        return []

    print(f"\nScraping {len(post_urls)} Instagram posts...")

    payload = [
        {"url": url}
        for url in post_urls
    ]

    records = run_dataset(
        POST_DATASET_ID,
        payload
    )

    print(f"Post records received: {len(records)}")

    return records


def normalize_data(profile_data, post_records, username):
    account = (
        profile_data.get("account")
        or profile_data.get("username")
    )

    if not account or account.lower() != username.lower():
        raise Exception(
            f"Profile mismatch. Requested: {username}, Received: {account}"
        )

    profile = {
        "username": account,
        "fullName": profile_data.get("full_name", ""),
        "followersCount": profile_data.get("followers", 0) or 0,
        "followsCount": profile_data.get("following", 0) or 0,
        "postsCount": profile_data.get("posts_count", 0) or 0,
        "verified": profile_data.get("is_verified", False),
        "private": profile_data.get("is_private", False),
        "profilePicUrlHD": profile_data.get("profile_pic_url", ""),
        "biography": profile_data.get("biography", ""),
        "latestPosts": [],
        "_provider": "bright_data"
    }

    posts = []

    mismatches = 0

    for post in post_records:
        post_username = post.get("user_posted", "")

        if not post_username or post_username.lower() != username.lower():
            mismatches += 1
            continue

        normalized_post = {
            "ownerUsername": post_username,
            "url": post.get("url", ""),
            "caption": post.get("description", "") or "",
            "likesCount": post.get("likes", 0) or 0,
            "commentsCount": post.get("num_comments", 0) or 0,
            "timestamp": post.get("date_posted"),
            "shortCode": post.get("shortcode", ""),
            "productType": (
                post.get("product_type")
                or post.get("content_type")
                or "unknown"
            ),
            "videoViewCount": post.get("video_views")
        }

        posts.append(normalized_post)

    print(f"\nMatching posts: {len(posts)}")
    print(f"Rejected mismatched posts: {mismatches}")

    return profile, posts


def main():
    print("=" * 60)
    print("BRIGHT DATA COMBINED TEST")
    print("=" * 60)

    profile_data = scrape_profile(USERNAME)

    post_urls = extract_post_urls(profile_data)

    print(f"\nPost URLs found: {len(post_urls)}")

    post_records = scrape_posts(post_urls[:12])

    print("\n" + "=" * 60)
    print("RAW PROFILE RECORD")
    print("=" * 60)
    print(profile_data)

    print("\n" + "=" * 60)
    print("RAW POST RECORD")
    print("=" * 60)

    if post_records:
        print(post_records[0])
    else:
        print("No post records available.")

    profile, posts = normalize_data(
        profile_data,
        post_records,
        USERNAME
    )

    print("\n" + "=" * 60)
    print("NORMALIZED PROFILE")
    print("=" * 60)
    print(profile)

    print("\n" + "=" * 60)
    print("NORMALIZED POSTS")
    print("=" * 60)

    for post in posts:
        print(post)

    print("\n" + "=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)

    print("Username:", profile["username"])
    print("Followers:", profile["followersCount"])
    print("Following:", profile["followsCount"])
    print("Total posts:", profile["postsCount"])
    print("Posts collected:", len(posts))

    print("\nBRIGHT DATA TEST COMPLETED!")


if __name__ == "__main__":
    main()
