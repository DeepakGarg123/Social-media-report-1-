from backend.llm.post_namer import generate_post_name


test_post = {
    "caption": "❤️‍🔥🫶🏻…",
    "hashtags": [
        "#brothers",
        "#like",
        "#post",
        "#trends",
        "#trendingsongs",
        "#trendingnow"
    ],
    "type": "Sidecar"
}


name = generate_post_name(test_post)

print("\nGenerated Post Name:")
print(name)