
import os
import json
from urllib.parse import urlparse
from datetime import datetime
import concurrent.futures

from dotenv import load_dotenv
from apify_client import ApifyClient

from backend.logs.logs import logger


load_dotenv()

token = os.getenv("APIFY_API_TOKEN")

if not token:
    raise ValueError("APIFY_API_TOKEN not found in .env file")

client = ApifyClient(token)


def scrape_instagram(
    instagram_url,
    force_refresh=False,
    max_posts=15,
    return_data=False,
    save_shared_files=True
):
    parsed_url = urlparse(instagram_url)
    username = parsed_url.path.strip("/").split("/")[0]

    if not username:
        print("Invalid Instagram profile URL.")
        logger.error("Invalid Instagram profile URL.")
        return None

    clean_username = username.lower()

    cache_dir = "backend/data/cache"
    history_dir = "backend/data/history"

    os.makedirs(cache_dir, exist_ok=True)
    os.makedirs(history_dir, exist_ok=True)

    cache_profile_file = os.path.join(
        cache_dir, f"{clean_username}_profile.json"
    )

    cache_data_file = os.path.join(
        cache_dir, f"{clean_username}_data.json"
    )

    profile_file = "backend/data/instagram_profile.json"
    data_file = "backend/data/instagram_data.json"
    shared_history_file = "backend/data/profile_history.json"

    user_history_file = os.path.join(
        history_dir, f"{clean_username}_history.json"
    )

    history_file = (
        shared_history_file
        if save_shared_files
        else user_history_file
    )

    # --------------------------------------------------
    # CACHE CHECK
    # --------------------------------------------------

    if not force_refresh:

        if (
            os.path.exists(cache_profile_file)
            and os.path.exists(cache_data_file)
        ):
            try:
                with open(cache_profile_file, "r", encoding="utf-8") as f:
                    profile_items = json.load(f)

                with open(cache_data_file, "r", encoding="utf-8") as f:
                    items = json.load(f)

                if profile_items and isinstance(profile_items, list):

                    profile = profile_items[0]

                    if profile.get("error"):
                        logger.warning(
                            f"Cached profile for {username} contains "
                            "an error response. Forcing live scrape."
                        )

                    else:

                        if save_shared_files:
                            with open(profile_file, "w", encoding="utf-8") as f:
                                json.dump(profile_items, f, indent=4)

                            with open(data_file, "w", encoding="utf-8") as f:
                                json.dump(items, f, indent=4)

                        print(
                            f"Loaded profile '{username}' "
                            "from local cache (Instant)."
                        )

                        logger.info(
                            f"Loaded cached profile data for: {username}"
                        )

                        if return_data:
                            return profile, items

                        return profile

            except Exception as e:
                logger.warning(
                    f"Failed to read cache for {username}: {e}"
                )

        # Existing shared-file fallback is allowed only in legacy mode.
        elif save_shared_files and os.path.exists(profile_file) and os.path.exists(data_file):

            try:
                with open(profile_file, "r", encoding="utf-8") as f:
                    existing_profiles = json.load(f)

                if (
                    existing_profiles
                    and existing_profiles[0].get("username", "").lower()
                    == clean_username
                ):

                    profile = existing_profiles[0]

                    if profile.get("error"):
                        logger.warning(
                            f"Existing profile file for {username} "
                            "contains an error response. Forcing live scrape."
                        )

                    else:

                        with open(data_file, "r", encoding="utf-8") as f:
                            items = json.load(f)

                        with open(cache_profile_file, "w", encoding="utf-8") as f:
                            json.dump(existing_profiles, f, indent=4)

                        with open(cache_data_file, "w", encoding="utf-8") as f:
                            json.dump(items, f, indent=4)

                        print(
                            f"Loaded existing profile '{username}' data "
                            "(Instant)."
                        )

                        logger.info(
                            f"Loaded existing profile file for: {username}"
                        )

                        if return_data:
                            return profile, items

                        return profile

            except Exception as e:
                logger.warning(
                    f"Failed to check existing data files: {e}"
                )

    # --------------------------------------------------
    # LIVE APIFY SCRAPING
    # --------------------------------------------------

    token = os.getenv("APIFY_API_TOKEN")

    if not token:
        raise ValueError("APIFY_API_TOKEN not found in .env file")

    client = ApifyClient(token)

    profile_input = {
        "usernames": [username]
    }

    run_input = {
        "addParentData": False,
        "directUrls": [instagram_url],
        "resultsLimit": max_posts,
        "resultsType": "posts",
        "searchLimit": 10,
        "searchType": "hashtag"
    }

    print(
        f"\nScraping Instagram profile & up to {max_posts} "
        "posts concurrently via Apify..."
    )

    logger.info(
        f"Instagram concurrent scraping started for: "
        f"{username} (max_posts: {max_posts})"
    )

    def _fetch_profile():
        p_run = client.actor(
            "apify/instagram-profile-scraper"
        ).call(run_input=profile_input)

        return client.dataset(
            p_run.default_dataset_id
        ).list_items().items

    def _fetch_posts():
        posts_run = client.actor(
            "apify/instagram-scraper"
        ).call(run_input=run_input)

        return client.dataset(
            posts_run.default_dataset_id
        ).list_items().items

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:

        profile_future = executor.submit(_fetch_profile)
        posts_future = executor.submit(_fetch_posts)

        try:
            profile_items = profile_future.result()

        except Exception as err:
            logger.error(f"Apify profile scraping failed: {err}")
            profile_items = None

        try:
            items = posts_future.result()

        except Exception as err:
            logger.error(f"Apify post scraping failed: {err}")
            items = []

    if not profile_items:
        print("Instagram profile not found.")

        logger.error(
            f"Instagram profile not found: {username}"
        )

        return None

    profile = profile_items[0]

    if profile.get("error"):

        error_desc = profile.get(
            "errorDescription",
            "unknown error"
        )

        print(
            f"Apify profile scraper returned an error "
            f"for '{username}': {error_desc}"
        )

        logger.error(
            f"Apify profile scraper error for {username}: "
            f"{profile.get('error')} — {error_desc}"
        )

        return None

    total_posts = profile.get("postsCount")

    print(f"Total posts on profile: {total_posts}")
    print(f"Posts collected for analysis: {len(items)}")

    logger.info(
        f"Profile {username} has {total_posts} posts. "
        f"Posts collected: {len(items)}."
    )

    # --------------------------------------------------
    # SAVE DATA
    # --------------------------------------------------

    # Shared files are written only in legacy mode.
    if save_shared_files:

        with open(data_file, "w", encoding="utf-8") as f:
            json.dump(items, f, indent=4)

        with open(profile_file, "w", encoding="utf-8") as f:
            json.dump(profile_items, f, indent=4)

    # Username-specific cache is preserved in both modes.
    with open(cache_data_file, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=4)

    with open(cache_profile_file, "w", encoding="utf-8") as f:
        json.dump(profile_items, f, indent=4)

    print(f"Posts collected: {len(items)}")

    logger.info(
        f"Instagram posts collected: {len(items)}"
    )

    # Save follower history to the appropriate file.
    _save_follower_snapshot(profile, history_file)

    print("Profile and post data saved successfully.")

    if return_data:
        return profile, items

    return profile


def _save_follower_snapshot(profile, history_file):

    """
    Upsert today's live follower count into the history file.

    This function is called only after a successful live scrape,
    never when loading cached data.
    """

    try:
        with open(history_file, "r", encoding="utf-8") as f:
            profile_history = json.load(f)

    except FileNotFoundError:
        profile_history = []

    except Exception as e:
        logger.warning(
            f"Could not read history file: {e}"
        )
        profile_history = []

    today = datetime.now().strftime("%Y-%m-%d")

    username = profile.get("username")
    followers = profile.get("followersCount")

    updated = False

    for item in profile_history:

        if (
            item.get("username") == username
            and item.get("date") == today
        ):

            if item["followers"] != followers:

                item["followers"] = followers

                logger.info(
                    f"Follower snapshot updated for "
                    f"{username} on {today}: {followers}"
                )

                print(
                    f"Follower snapshot updated for today: "
                    f"{followers} followers."
                )

            else:
                print(
                    "Follower snapshot for today already up-to-date."
                )

            updated = True
            break

    if not updated:

        profile_history.append({
            "username": username,
            "date": today,
            "followers": followers
        })

        logger.info(
            f"New follower snapshot saved for {username}: {followers}"
        )

        print(
            f"New follower snapshot saved: {followers} followers."
        )

    try:
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(profile_history, f, indent=4)

    except Exception as e:
        logger.error(
            f"Could not write history file: {e}"
        )
