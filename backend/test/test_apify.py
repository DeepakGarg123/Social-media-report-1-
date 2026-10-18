import os
from dotenv import load_dotenv
from apify_client import ApifyClient

load_dotenv()

token = os.getenv("APIFY_API_TOKEN")

if not token:
    print("API token not found")
    exit()

client = ApifyClient(token)

user = client.user().get()

print("Apify connection successful")
print("Username:", user.username)