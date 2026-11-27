
bright_data_called = False


def scrape_with_apify(username):

    print("\nPRIMARY PROVIDER: APIFY")
    print("Scraping Instagram profile...")

    return {
        "profile": {
            "username": username,
            "followers": 10000,
            "following": 500,
            "total_posts": 150,
            "is_verified": False,
            "is_private": False
        },
        "posts": [
            {
                "username": username,
                "caption": "Test Instagram post",
                "likes": 500,
                "comments": 50,
                "content_type": "Image"
            }
        ]
    }


def scrape_with_bright_data(username):

    global bright_data_called

    bright_data_called = True

    print("ERROR: Bright Data should not have been called!")

    raise RuntimeError("Unexpected Bright Data call")


def main():

    global bright_data_called

    username = "test_account"

    print("PROVIDER SUCCESS TEST")
    print("=====================")

    try:
        result = scrape_with_apify(username)

        print("\nApify succeeded!")
        print("Using Apify data.")

    except Exception as error:

        print(f"Apify failed: {error}")
        print("Switching to Bright Data...")

        result = scrape_with_bright_data(username)

    print("\nFINAL RESULT")
    print("============")
    print(result)

    print("\nTEST VALIDATION")
    print("===============")

    if not bright_data_called:
        print("PASS: Bright Data was not called.")
    else:
        print("FAIL: Bright Data was called unnecessarily.")


if __name__ == "__main__":
    main()
