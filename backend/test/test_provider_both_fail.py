
def scrape_with_apify(username):

    print("\nPRIMARY PROVIDER: APIFY")
    print("Scraping Instagram profile...")

    raise RuntimeError("Simulated Apify API usage limit")


def scrape_with_bright_data(username):

    print("\nSECONDARY PROVIDER: BRIGHT DATA")
    print("Starting Bright Data fallback...")

    raise RuntimeError("Simulated Bright Data API failure")


def scrape_instagram(username):

    try:
        result = scrape_with_apify(username)
        print("\nApify succeeded!")
        return result

    except Exception as apify_error:

        print(f"\nApify failed: {apify_error}")
        print("Switching to Bright Data...")

    try:
        result = scrape_with_bright_data(username)
        print("\nBright Data succeeded!")
        return result

    except Exception as bright_data_error:

        print(f"\nBright Data failed: {bright_data_error}")

        return {
            "success": False,
            "error": "Both Instagram data providers failed.",
            "profile": None,
            "posts": []
        }


def main():

    print("BOTH PROVIDERS FAILURE TEST")
    print("===========================")

    result = scrape_instagram("sidhu_moosewala")

    print("\nFINAL RESULT")
    print("============")
    print(result)

    print("\nTEST VALIDATION")
    print("===============")

    if (
        result["success"] is False
        and result["profile"] is None
        and result["posts"] == []
    ):
        print("PASS: Both failures handled gracefully.")
    else:
        print("FAIL: Unexpected result.")


if __name__ == "__main__":
    main()
