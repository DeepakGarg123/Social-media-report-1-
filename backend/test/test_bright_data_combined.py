
import os
import time
import requests

from dotenv import load_dotenv


load_dotenv()

API_KEY = os.getenv("BRIGHT_DATA_API_KEY")

BASE_URL = "https://api.brightdata.com/datasets/v3"

PROFILE_DATASET_ID = "gd_l1vikfch901nx3by4"
POST_DATASET_ID = "gd_lk5ns7kz21pck8jpis"

USERNAME = "arman.dxp"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}


def trigger_dataset(dataset_id, payload):

    response = requests.post(
        f"{BASE_URL}/trigger",
        params={
            "dataset_id": dataset_id,
            "format": "json"
        },
        headers=HEADERS,
        json=payload,
        timeout=60
    )

    if response.status_code != 200:
        raise Exception(
            f"Trigger failed: {response.status_code} - {response.text}"
        )

    result = response.json()

    snapshot_id = result.get("snapshot_id")

    if not snapshot_id:
        raise Exception(f"Snapshot ID missing: {result}")

    print(f"Snapshot created: {snapshot_id}")

    return snapshot_id


def wait_for_snapshot(snapshot_id):

    for attempt in range(30):

        response = requests.get(
            f"{BASE_URL}/progress/{snapshot_id}",
            headers=HEADERS,
            timeout=60
        )

        if response.status_code != 200:
            raise Exception(
                f"Progress check failed: {response.status_code} - {response.text}"
            )

        result = response.json()
        status = result.get("status")

        print(f"Check {attempt + 1}: {status}")

        if status == "ready":
            return True

        if status in ["failed", "error"]:
            raise Exception(f"Scraping failed: {result}")

        time.sleep(10)

    raise TimeoutError("Snapshot did not become ready in time")


def download_snapshot(snapshot_id):

    response = requests.get(
        f"{BASE_URL}/snapshot/{snapshot_id}",
        params={"format": "json"},
        headers=HEADERS,
        timeout=120
    )

    print("\nSNAPSHOT DOWNLOAD DIAGNOSTICS")
    print("=============================")

    print("HTTP Status:", response.status_code)
    print("Content Type:", response.headers.get("Content-Type"))
    print("Raw Response:", response.text[:5000])

    if response.status_code != 200:
        raise Exception(
            f"Download failed: {response.status_code} - {response.text}"
        )

    try:
        data = response.json()

    except ValueError:
        raise Exception("Snapshot response is not valid JSON")

    print("Response Type:", type(data).__name__)

    if isinstance(data, list):
        print("Number of Records:", len(data))

    elif isinstance(data, dict):
        print("Response Keys:", list(data.keys()))

    return data


def extract_post_urls(profile):

    profile_posts = profile.get("posts", [])

    post_urls = []

    for post in profile_posts:

        url = (
            post.get("url")
            or post.get("post_url")
            or post.get("postUrl")
            or post.get("link")
        )

        if url and url not in post_urls:
            post_urls.append(url)

    return post_urls


def scrape_profile():

    print("\nSTEP 1: SCRAPING INSTAGRAM PROFILE")

    payload = [
        {
            "url": f"https://www.instagram.com/{USERNAME}/"
        }
    ]

    snapshot_id = trigger_dataset(
        PROFILE_DATASET_ID,
        payload
    )

    wait_for_snapshot(snapshot_id)

    data = download_snapshot(snapshot_id)

    if not isinstance(data, list) or len(data) == 0:

        print("\nNo profile records returned.")
        print("Snapshot ID:", snapshot_id)

        return None

    profile = data[0]

    print("\nPROFILE DATA RECEIVED")
    print("Username:", profile.get("account"))
    print("Followers:", profile.get("followers"))
    print("Following:", profile.get("following"))
    print("Total Posts:", profile.get("posts_count"))
    print("Verified:", profile.get("is_verified"))
    print("Private:", profile.get("is_private"))

    return profile


def scrape_posts(post_urls):
    if not post_urls:
        print("No post URLs available for this account.")
        return []

    # Keep the existing scraping logic below

    payload = [
        {"url": url}
        for url in post_urls
    ]

    snapshot_id = trigger_dataset(
        POST_DATASET_ID,
        payload
    )

    wait_for_snapshot(snapshot_id)

    posts = download_snapshot(snapshot_id)

    if not isinstance(posts, list):
        raise Exception("Post dataset returned an unexpected response format")

    print("\nPOST DATA RECEIVED:", len(posts))

    return posts


def normalize_data(profile, posts):

    print("\nSTEP 3: NORMALIZING DATA")

    normalized_posts = []

    for post in posts:

        normalized_posts.append({
            "username": post.get("user_posted"),
            "url": post.get("url"),
            "caption": post.get("description"),
            "likes": post.get("likes"),
            "comments": post.get("num_comments"),
            "date_posted": post.get("date_posted"),
            "content_type": post.get("content_type")
        })

    normalized_data = {
        "profile": {
            "username": profile.get("account"),
            "full_name": profile.get("full_name"),
            "followers": profile.get("followers"),
            "following": profile.get("following"),
            "total_posts": profile.get("posts_count"),
            "is_verified": profile.get("is_verified"),
            "is_private": profile.get("is_private")
        },
        "posts": normalized_posts
    }

    return normalized_data


def main():

    if not API_KEY:
        raise ValueError("BRIGHT_DATA_API_KEY not found in .env")

    print("BRIGHT DATA COMBINED TEST")
    print("=========================")

    profile = scrape_profile()

    if profile is None:
        print("\nTEST STOPPED: No profile data available.")
        return

    post_urls = extract_post_urls(profile)

    print("\nPost URLs extracted:", len(post_urls))

    posts = scrape_posts(post_urls)

    final_data = normalize_data(profile, posts)

    print("\nSTEP 4: FINAL COMBINED RESULT")
    print("============================")

    print("\nPROFILE:")
    print(final_data["profile"])

    print("\nPOSTS:")

    for index, post in enumerate(final_data["posts"], start=1):

        print(f"\nPost {index}")
        print("Username:", post["username"])
        print("Likes:", post["likes"])
        print("Comments:", post["comments"])
        print("Date:", post["date_posted"])
        print("Content Type:", post["content_type"])

    expected_username = USERNAME.lower()

    mismatches = [
        post for post in final_data["posts"]
        if post["username"]
        and post["username"].lower() != expected_username
    ]

    print("\nFINAL SUMMARY")
    print("Profile fetched:", bool(final_data["profile"]["username"]))
    print("Post URLs submitted:", len(post_urls))
    print("Posts returned:", len(final_data["posts"]))
    print("Username mismatches:", len(mismatches))

    if mismatches:

        print("\nWARNING: Some posts belong to different usernames.")

        for post in mismatches:
            print(post["username"], "-", post["url"])


if __name__ == "__main__":
    main()
