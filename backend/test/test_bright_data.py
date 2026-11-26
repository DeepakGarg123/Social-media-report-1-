
import os
import time
import requests

from pathlib import Path
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = PROJECT_ROOT / ".env"

load_dotenv(ENV_PATH, override=True)

API_KEY = os.getenv("BRIGHT_DATA_API_KEY")

USERNAME = "karanaujla"

DATASET_ID = "gd_l1vikfch901nx3by4"

BASE_URL = "https://api.brightdata.com/datasets/v3"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}


def check_response(response, step):
    print(f"\n{step} status:", response.status_code)

    if not response.ok:
        print("Bright Data error response:")
        print(response.text)
        response.raise_for_status()


def trigger_scraping():

    url = f"{BASE_URL}/trigger"

    params = {
        "dataset_id": DATASET_ID,
        "format": "json",
        "include_errors": "true"
    }

    payload = [
        {
            "url": f"https://www.instagram.com/{USERNAME}/"
        }
    ]

    print("\nStarting Bright Data scraping...")
    print("Instagram username:", USERNAME)
    print("Dataset ID:", DATASET_ID)

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
        raise ValueError(
            f"Snapshot ID missing. Response: {result}"
        )

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
                f"Bright Data scraping failed: {result}"
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

    print("\nDownloading scraped data...")

    response = requests.get(
        url,
        headers=HEADERS,
        params=params,
        timeout=120
    )

    check_response(response, "Snapshot")

    return response.json()


def main():

    print("Project root:", PROJECT_ROOT)
    print("Env file exists:", ENV_PATH.exists())
    print("API key loaded:", bool(API_KEY))

    if not API_KEY:
        raise ValueError(
            "BRIGHT_DATA_API_KEY is missing from .env"
        )

    snapshot_id = trigger_scraping()

    completed = check_progress(snapshot_id)

    if completed:
        data = download_snapshot(snapshot_id)

        print("\nScraping completed successfully!")
        print("\nScraped data:")
        print(data)


if __name__ == "__main__":

    try:
        main()

    except requests.exceptions.HTTPError:
        print("\nHTTP request failed. Check the error response above.")

    except requests.exceptions.Timeout:
        print("\nRequest timed out.")

    except requests.exceptions.ConnectionError:
        print("\nCould not connect to Bright Data.")

    except Exception as error:
        print("\nError:", error)
