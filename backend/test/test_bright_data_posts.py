
import os
import time
import requests

from pathlib import Path
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = PROJECT_ROOT / ".env"

load_dotenv(ENV_PATH, override=True)

API_KEY = os.getenv("BRIGHT_DATA_API_KEY")

BASE_URL = "https://api.brightdata.com/datasets/v3"

DATASET_ID = "gd_lk5ns7kz21pck8jpis"

POST_URLS = [
    "https://www.instagram.com/p/DfmPsyGB2pe/",
    "https://www.instagram.com/p/DfUWHlklC56/",
    "https://www.instagram.com/p/DfEy8kLAMqR/"
]

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}


def check_response(response, step):

    print(f"\n{step} status:", response.status_code)

    if not response.ok:
        print("Error response:")
        print(response.text)
        response.raise_for_status()


def trigger_scraping():

    url = f"{BASE_URL}/trigger"

    params = {
        "dataset_id": DATASET_ID,
        "format": "json"
    }

    payload = [
        {
            "url": post_url,
            "country": ""
        }
        for post_url in POST_URLS
    ]

    print("\nStarting Instagram posts scraping...")
    print("Number of posts:", len(POST_URLS))

    response = requests.post(
        url,
        headers=HEADERS,
        params=params,
        json=payload,
        timeout=60
    )

    check_response(response, "Trigger")

    result = response.json()

    snapshot_id = result.get("snapshot_id")

    if not snapshot_id:
        raise ValueError(f"Snapshot ID missing: {result}")

    print("\nSnapshot ID:", snapshot_id)

    return snapshot_id


def check_progress(snapshot_id):

    url = f"{BASE_URL}/progress/{snapshot_id}"

    for attempt in range(1, 31):

        print(f"\nChecking progress: {attempt}/30")

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=60
        )

        check_response(response, "Progress")

        result = response.json()

        status = result.get("status")

        print("Current status:", status)

        if status == "ready":
            return True

        if status == "failed":
            raise RuntimeError(
                f"Scraping failed: {result}"
            )

        time.sleep(10)

    raise TimeoutError(
        "Scraping did not finish within 5 minutes."
    )


def download_snapshot(snapshot_id):

    url = f"{BASE_URL}/snapshot/{snapshot_id}"

    params = {
        "format": "json"
    }

    print("\nDownloading post data...")

    response = requests.get(
        url,
        headers=HEADERS,
        params=params,
        timeout=120
    )

    check_response(response, "Snapshot")

    return response.json()


def display_results(data):

    print("\nInstagram Post Engagement Results")
    print("=" * 50)

    if isinstance(data, dict):
        data = [data]

    if not isinstance(data, list):
        print("Unexpected response format:")
        print(data)
        return

    for index, post in enumerate(data, start=1):

        print(f"\nPost {index}")
        print("-" * 40)

        print("Username:", post.get("user_posted"))
        print("Post URL:", post.get("url"))

        print("Likes:", post.get("likes"))
        print("Comments:", post.get("num_comments"))

        print("Date:", post.get("date_posted"))

        print("Caption:", post.get("description"))

        print("Available fields:", list(post.keys()))


def main():

    print("Project root:", PROJECT_ROOT)
    print("Env file exists:", ENV_PATH.exists())
    print("API key loaded:", bool(API_KEY))

    if not API_KEY:
        raise ValueError(
            "BRIGHT_DATA_API_KEY is missing from .env"
        )

    snapshot_id = trigger_scraping()

    check_progress(snapshot_id)

    data = download_snapshot(snapshot_id)

    print("\nScraping completed successfully!")

    display_results(data)


if __name__ == "__main__":

    try:
        main()

    except requests.exceptions.HTTPError:
        print("\nHTTP request failed.")

    except requests.exceptions.Timeout:
        print("\nRequest timed out.")

    except requests.exceptions.ConnectionError:
        print("\nConnection error.")

    except Exception as error:
        print("\nError:", error)
