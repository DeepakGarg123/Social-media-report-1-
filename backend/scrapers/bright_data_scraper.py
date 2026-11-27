
import os
import time
import requests

from dotenv import load_dotenv


load_dotenv()

PROFILE_DATASET_ID = "gd_l1vikfch901nx3by4"
POST_DATASET_ID = "gd_lk5ns7kz21pck8jpis"

BASE_URL = "https://api.brightdata.com/datasets/v3"


class BrightDataScrapingError(Exception):
    pass


def get_api_key():
    api_key = os.getenv("BRIGHT_DATA_API_KEY")

    if not api_key:
        raise BrightDataScrapingError(
            "BRIGHT_DATA_API_KEY is missing from .env"
        )

    return api_key


def trigger_dataset(dataset_id, payload):
    headers = {
        "Authorization": f"Bearer {get_api_key()}",
        "Content-Type": "application/json"
    }

    url = f"{BASE_URL}/trigger"

    params = {
        "dataset_id": dataset_id,
        "format": "json"
    }

    response = requests.post(
        url,
        headers=headers,
        params=params,
        json=payload,
        timeout=60
    )

    response.raise_for_status()

    result = response.json()

    snapshot_id = result.get("snapshot_id")

    if not snapshot_id:
        raise BrightDataScrapingError(
            "Bright Data did not return a snapshot ID."
        )

    return snapshot_id


def wait_for_snapshot(snapshot_id, max_attempts=30):
    headers = {
        "Authorization": f"Bearer {get_api_key()}"
    }

    url = f"{BASE_URL}/progress/{snapshot_id}"

    for attempt in range(max_attempts):
        response = requests.get(
            url,
            headers=headers,
            timeout=30
        )

        response.raise_for_status()

        result = response.json()
        status = result.get("status")

        if status == "ready":
            return

        if status in ("failed", "error"):
            raise BrightDataScrapingError(
                f"Bright Data snapshot failed: {result}"
            )

        time.sleep(10)

    raise BrightDataScrapingError(
        "Bright Data snapshot timed out."
    )


def download_snapshot(snapshot_id):
    headers = {
        "Authorization": f"Bearer {get_api_key()}"
    }

    url = f"{BASE_URL}/snapshot/{snapshot_id}"

    response = requests.get(
        url,
        headers=headers,
        params={"format": "json"},
        timeout=120
    )

    response.raise_for_status()

    data = response.json()

    if not isinstance(data, list):
        raise BrightDataScrapingError(
            "Unexpected Bright Data snapshot format."
        )

    return data


def run_dataset(dataset_id, payload):
    snapshot_id = trigger_dataset(dataset_id, payload)

    wait_for_snapshot(snapshot_id)

    return download_snapshot(snapshot_id)


def extract_post_urls(profile_data, username):
    post_urls = []

    embedded_posts = profile_data.get("posts", [])

    if not isinstance(embedded_posts, list):
        return post_urls

    for post in embedded_posts:
        if not isinstance(post, dict):
            continue

        post_username = (
            post.get("user_posted")
            or post.get("username")
            or post.get("ownerUsername")
        )

        if post_username and post_username.lower() != username.lower():
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


def normalize_profile(profile_data, username):
    account = (
        profile_data.get("account")
        or profile_data.get("username")
    )

    if not account or account.lower() != username.lower():
        raise BrightDataScrapingError(
            "Bright Data returned a different Instagram profile."
        )

    return {
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


def normalize_post(post, username):
    post_username = post.get("user_posted", "")

    if not post_username or post_username.lower() != username.lower():
        return None

    return {
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


def scrape_bright_data(username, max_posts=15):
    username = username.strip().lstrip("@")

    if not username:
        raise BrightDataScrapingError(
            "Instagram username cannot be empty."
        )

    profile_url = f"https://www.instagram.com/{username}/"

    profile_records = run_dataset(
        PROFILE_DATASET_ID,
        [{"url": profile_url}]
    )

    if not profile_records:
        raise BrightDataScrapingError(
            "Bright Data returned no profile data."
        )

    raw_profile = profile_records[0]

    profile = normalize_profile(raw_profile, username)

    post_urls = extract_post_urls(raw_profile, username)

    post_urls = post_urls[:max_posts]

    if not post_urls:
        return profile, []

    post_payload = [
        {"url": url}
        for url in post_urls
    ]

    raw_posts = run_dataset(
        POST_DATASET_ID,
        post_payload
    )

    posts = []

    for raw_post in raw_posts:
        normalized_post = normalize_post(
            raw_post,
            username
        )

        if normalized_post:
            posts.append(normalized_post)

    return profile, posts
