
import os
import json
from urllib.parse import urlparse
from datetime import datetime
import concurrent.futures

from dotenv import load_dotenv
from apify_client import ApifyClient
from apify_client.errors import ApifyApiError

from backend.logs.logs import logger


load_dotenv()

# ---------------------------------------------------------------------------
# Custom Apify-specific exception hierarchy
# ---------------------------------------------------------------------------

class ApifyScrapingError(Exception):
    """Base class for all Apify scraping failures."""


class ApifyTokenMissingError(ApifyScrapingError):
    """Raised when the APIFY_API_TOKEN environment variable is not set."""


class ApifyAuthenticationError(ApifyScrapingError):
    """Raised when Apify rejects the token (401 / 403)."""


class ApifyRateLimitError(ApifyScrapingError):
    """Raised when Apify returns HTTP 429 (Too Many Requests)."""


class ApifyActorTimeoutError(ApifyScrapingError):
    """Raised when an Apify actor run times out."""


class ApifyActorRunError(ApifyScrapingError):
    """Raised when an Apify actor run fails or is aborted."""


class ApifyDatasetEmptyError(ApifyScrapingError):
    """Raised when an Apify actor run succeeds but the dataset is empty."""


class ApifyNetworkError(ApifyScrapingError):
    """Raised for network-level errors (connection refused, DNS, SSL …)."""


class ApifyInvalidInputError(ApifyScrapingError):
    """Raised when the input sent to the actor is invalid."""


# ---------------------------------------------------------------------------
# Token validation at import time
# ---------------------------------------------------------------------------

_token = os.getenv("APIFY_API_TOKEN")

if not _token:
    raise ApifyTokenMissingError(
        "[Apify Failure] APIFY_API_TOKEN not found in the .env file. "
        "Please set a valid token and restart the application."
    )

_client = ApifyClient(_token)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _classify_apify_error(err: Exception, context: str) -> ApifyScrapingError:
    """
    Inspect a raw exception raised by the Apify client and return a
    descriptive ApifyScrapingError subclass so callers can distinguish
    failure modes without catching a bare Exception.
    """
    err_str = str(err).lower()

    # --- HTTP-level errors surfaced by ApifyApiError ---
    if isinstance(err, ApifyApiError):
        status = getattr(err, "status_code", None)

        if status in (401, 403):
            return ApifyAuthenticationError(
                f"[Apify Failure – {context}] "
                f"Authentication failed (HTTP {status}). "
                "Your APIFY_API_TOKEN may be invalid or expired. "
                f"Original error: {err}"
            )

        if status == 429:
            return ApifyRateLimitError(
                f"[Apify Failure – {context}] "
                "Rate limit exceeded (HTTP 429). "
                "Too many requests were sent to Apify. "
                f"Original error: {err}"
            )

        if status == 400:
            return ApifyInvalidInputError(
                f"[Apify Failure – {context}] "
                "Invalid input sent to the Apify actor (HTTP 400). "
                f"Original error: {err}"
            )

        if status is not None and status >= 500:
            return ApifyActorRunError(
                f"[Apify Failure – {context}] "
                f"Apify server error (HTTP {status}). "
                f"Original error: {err}"
            )

    # --- Keyword-based classification for non-HTTP errors ---
    if any(kw in err_str for kw in ("timeout", "timed out", "time out")):
        return ApifyActorTimeoutError(
            f"[Apify Failure – {context}] "
            "The Apify actor run timed out. "
            "Consider reducing max_posts or retrying later. "
            f"Original error: {err}"
        )

    if any(kw in err_str for kw in ("abort", "aborted", "failed", "did not succeed")):
        return ApifyActorRunError(
            f"[Apify Failure – {context}] "
            "The Apify actor run was aborted or failed. "
            f"Original error: {err}"
        )

    if any(kw in err_str for kw in (
        "connection", "refused", "ssl", "certificate",
        "network", "dns", "resolve", "unreachable", "socket"
    )):
        return ApifyNetworkError(
            f"[Apify Failure – {context}] "
            "A network error occurred while communicating with Apify. "
            "Check your internet connection. "
            f"Original error: {err}"
        )

    if any(kw in err_str for kw in ("unauthorized", "forbidden", "invalid token", "token")):
        return ApifyAuthenticationError(
            f"[Apify Failure – {context}] "
            "Authentication error. Your APIFY_API_TOKEN may be invalid. "
            f"Original error: {err}"
        )

    if any(kw in err_str for kw in ("quota", "limit", "exceeded", "rate")):
        return ApifyRateLimitError(
            f"[Apify Failure – {context}] "
            "Apify quota or rate limit exceeded. "
            f"Original error: {err}"
        )

    # --- Generic fallback ---
    return ApifyScrapingError(
        f"[Apify Failure – {context}] "
        f"An unexpected Apify error occurred: {err}"
    )


def _safe_call_actor(actor_id: str, run_input: dict, context: str):
    """
    Call an Apify actor, convert any failure into a typed ApifyScrapingError,
    and return the resulting dataset items.

    Raises
    ------
    ApifyTokenMissingError      – token not set
    ApifyAuthenticationError    – HTTP 401 / 403 / bad token keyword
    ApifyRateLimitError         – HTTP 429 / quota exceeded
    ApifyActorTimeoutError      – run timed out
    ApifyActorRunError          – run aborted / failed
    ApifyDatasetEmptyError      – run succeeded but dataset is empty
    ApifyNetworkError           – connection / DNS / SSL error
    ApifyInvalidInputError      – HTTP 400 bad input
    ApifyScrapingError          – any other Apify-related error
    """
    token = os.getenv("APIFY_API_TOKEN")

    if not token:
        raise ApifyTokenMissingError(
            f"[Apify Failure – {context}] "
            "APIFY_API_TOKEN is missing. "
            "Cannot proceed with live scraping."
        )

    client = ApifyClient(token)

    try:
        actor_run = client.actor(actor_id).call(run_input=run_input)

    except ApifyApiError as api_err:
        raise _classify_apify_error(api_err, context) from api_err

    except Exception as err:
        raise _classify_apify_error(err, context) from err

    # Validate the run object returned by Apify
    if actor_run is None:
        raise ApifyActorRunError(
            f"[Apify Failure – {context}] "
            "Apify returned None instead of a run object. "
            "The actor may have failed to start."
        )

    run_status = (actor_run.get("status") or "").upper()

    if run_status in ("FAILED", "ABORTED", "TIMED-OUT"):
        status_msg = {
            "FAILED":    "The actor run failed.",
            "ABORTED":   "The actor run was aborted.",
            "TIMED-OUT": "The actor run timed out.",
        }.get(run_status, f"The actor run ended with status '{run_status}'.")

        if run_status == "TIMED-OUT":
            raise ApifyActorTimeoutError(
                f"[Apify Failure – {context}] {status_msg}"
            )

        raise ApifyActorRunError(
            f"[Apify Failure – {context}] {status_msg}"
        )

    dataset_id = actor_run.get("defaultDatasetId")

    if not dataset_id:
        raise ApifyActorRunError(
            f"[Apify Failure – {context}] "
            "Apify run did not return a dataset ID."
        )

    try:
        items = client.dataset(dataset_id).list_items().items

    except ApifyApiError as api_err:
        raise _classify_apify_error(api_err, f"{context} / dataset fetch") from api_err

    except Exception as err:
        raise _classify_apify_error(err, f"{context} / dataset fetch") from err

    if items is None:
        raise ApifyDatasetEmptyError(
            f"[Apify Failure – {context}] "
            "Dataset list_items() returned None."
        )

    return items


# ---------------------------------------------------------------------------
# Main scrape function
# ---------------------------------------------------------------------------

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
        return _safe_call_actor(
            "apify/instagram-profile-scraper",
            profile_input,
            context="profile scraper"
        )

    def _fetch_posts():
        return _safe_call_actor(
            "apify/instagram-scraper",
            run_input,
            context="post scraper"
        )

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:

        profile_future = executor.submit(_fetch_profile)
        posts_future = executor.submit(_fetch_posts)

        # --- Profile fetch error handling ---
        profile_items = None

        try:
            profile_items = profile_future.result()

        except ApifyTokenMissingError as err:
            msg = str(err)
            print(msg)
            logger.error(msg)
            return None

        except ApifyAuthenticationError as err:
            msg = str(err)
            print(msg)
            logger.error(msg)
            return None

        except ApifyRateLimitError as err:
            msg = str(err)
            print(msg)
            logger.warning(msg)
            return None

        except ApifyActorTimeoutError as err:
            msg = str(err)
            print(msg)
            logger.error(msg)
            return None

        except ApifyActorRunError as err:
            msg = str(err)
            print(msg)
            logger.error(msg)
            return None

        except ApifyDatasetEmptyError as err:
            msg = str(err)
            print(msg)
            logger.warning(msg)
            # treat as not found — will be caught below by `if not profile_items`

        except ApifyInvalidInputError as err:
            msg = str(err)
            print(msg)
            logger.error(msg)
            return None

        except ApifyNetworkError as err:
            msg = str(err)
            print(msg)
            logger.error(msg)
            return None

        except ApifyScrapingError as err:
            msg = str(err)
            print(msg)
            logger.error(msg)
            return None

        except Exception as err:
            msg = (
                f"[Apify Failure – profile scraper] "
                f"An unexpected error occurred: {err}"
            )
            print(msg)
            logger.error(msg)
            return None

        # --- Posts fetch error handling ---
        items = []

        try:
            items = posts_future.result()

        except ApifyTokenMissingError as err:
            msg = str(err)
            print(msg)
            logger.error(msg)

        except ApifyAuthenticationError as err:
            msg = str(err)
            print(msg)
            logger.error(msg)

        except ApifyRateLimitError as err:
            msg = str(err)
            print(msg)
            logger.warning(msg)

        except ApifyActorTimeoutError as err:
            msg = str(err)
            print(msg)
            logger.error(msg)

        except ApifyActorRunError as err:
            msg = str(err)
            print(msg)
            logger.error(msg)

        except ApifyDatasetEmptyError as err:
            msg = str(err)
            print(msg)
            logger.warning(msg)

        except ApifyInvalidInputError as err:
            msg = str(err)
            print(msg)
            logger.error(msg)

        except ApifyNetworkError as err:
            msg = str(err)
            print(msg)
            logger.error(msg)

        except ApifyScrapingError as err:
            msg = str(err)
            print(msg)
            logger.error(msg)

        except Exception as err:
            msg = (
                f"[Apify Failure – post scraper] "
                f"An unexpected error occurred: {err}"
            )
            print(msg)
            logger.error(msg)

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
