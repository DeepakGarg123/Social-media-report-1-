
from backend.test import test_bright_data_combined as bright_data

USERNAME = "sidhu_moosewala"


def scrape_with_apify(username):

    print("\nPRIMARY PROVIDER: APIFY")
    print("Simulating Apify API usage limit...")

    raise RuntimeError("Simulated Apify API usage limit")


def scrape_with_bright_data(username):

    print("\nSECONDARY PROVIDER: BRIGHT DATA")
    print("Starting Bright Data fallback...")

    bright_data.USERNAME = username

    profile = bright_data.scrape_profile()

    if not profile:
        raise RuntimeError("Bright Data could not fetch profile")

    post_urls = bright_data.extract_post_urls(profile)

    posts = bright_data.scrape_posts(post_urls)

    result = bright_data.normalize_data(profile, posts)

    return result


def main():

    print("PROVIDER FALLBACK TEST")
    print("======================")

    try:
        result = scrape_with_apify(USERNAME)

    except Exception as error:

        print(f"\nApify failed: {error}")
        print("Switching to Bright Data...")

        try:
            result = scrape_with_bright_data(USERNAME)

            print("\nFALLBACK SUCCESSFUL!")
            print("====================")
            print(result)

        except Exception as fallback_error:

            print("\nBoth providers failed.")
            print(f"Bright Data error: {fallback_error}")


if __name__ == "__main__":
    main()
