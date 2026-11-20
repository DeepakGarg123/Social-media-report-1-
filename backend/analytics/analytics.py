
import json
import concurrent.futures

from pathlib import Path
from datetime import datetime
from collections import defaultdict

from backend.logs.logs import logger
from backend.llm.post_namer import generate_post_name


def generate_analytics(
    profile,
    data,
    profile_history=None,
    start_month=None,
    end_month=None,
    save_report=False
):
    """Generate an Instagram analytics report from supplied profile and posts."""

    if not isinstance(profile, dict) or not profile:
        raise ValueError("A valid Instagram profile is required.")

    if not isinstance(data, list):
        raise ValueError("Instagram posts data must be a list.")

    username = profile.get("username", "").lower()

    if not username:
        raise ValueError("Instagram username is missing from the profile.")

    report = {
        "profile": {},
        "metrics": {},
        "top_posts": [],
        "posting_analysis": [],
        "content_analysis": [],
        "video_analysis": [],
        "growth": {},
        "suggestions": [],
        "llm_insights": []
    }

    # -------------------- Load Data --------------------

    logger.info(
        f"Analytics processing started for: {username}"
    )

    # -------------------- Load Profile History --------------------

    if profile_history is None:

        history_files = [
            Path("backend/data/profile_history.json"),
            Path("backend/data/history") / f"{username}_history.json"
        ]

        history_by_date = {}

        for history_file in history_files:

            if history_file.exists():

                try:
                    with open(
                        history_file,
                        "r",
                        encoding="utf-8"
                    ) as f:
                        saved_history = json.load(f)

                    for snapshot in saved_history:

                        if (
                            snapshot.get("username", "").lower() == username
                            and snapshot.get("date")
                        ):
                            history_by_date[snapshot["date"]] = snapshot

                except Exception as error:
                    logger.warning(
                        f"Could not read history file {history_file}: {error}"
                    )

        profile_history = list(history_by_date.values())

    # -------------------- Profile Information --------------------

    report["profile"] = {
        "username": profile["username"],
        "followers": profile.get("followersCount", 0),
        "following": profile.get("followsCount", 0),
        "total_posts": profile.get("postsCount"),
        "analyzed_posts_count": len(profile.get("latestPosts", [])),
        "verified": profile.get("verified", False),
        "private": profile.get("private", False),
        "profile_pic_url": (
            profile.get("profilePicUrlHD")
            or profile.get("profilePicUrl")
        ),
        "full_name": profile.get("fullName"),
        "biography": profile.get("biography")
    }

    # -------------------- Filter Profile History --------------------

    user_history = [
        snapshot
        for snapshot in profile_history
        if snapshot.get("username", "").lower() == username
    ]

    # -------------------- Follower Growth --------------------

    user_history.sort(
        key=lambda item: item.get("date", "")
    )

    print("\nFollower Growth History:")

    for snapshot in user_history:
        print(
            f"{snapshot.get('date')} -> "
            f"{snapshot.get('followers')} followers"
        )

    def calculate_growth(history, start_month=None, end_month=None):

        if not history:
            return {
                "status": "insufficient_data",
                "reason": "No follower history is available for this profile."
            }

        selected_history = history

        if start_month and end_month:

            selected_history = [
                item
                for item in history
                if start_month <= item.get("date", "")[:7] <= end_month
            ]

        if len(selected_history) < 2:

            if start_month and end_month:
                return {
                    "status": "insufficient_data",
                    "reason": (
                        f"Not enough follower snapshots are available "
                        f"between {start_month} and {end_month}."
                    ),
                    "start_month": start_month,
                    "end_month": end_month
                }

            return {
                "status": "insufficient_data",
                "reason": "At least two follower snapshots are required."
            }

        first = selected_history[0]
        last = selected_history[-1]

        start_followers = first["followers"]
        end_followers = last["followers"]

        growth = end_followers - start_followers

        if start_followers > 0:
            growth_percentage = (
                growth / start_followers
            ) * 100
        else:
            growth_percentage = 0

        if growth > 0:
            direction = "increase"
        elif growth < 0:
            direction = "decrease"
        else:
            direction = "no_change"

        result = {
            "status": "available",
            "start_date": first["date"],
            "end_date": last["date"],
            "start_followers": start_followers,
            "end_followers": end_followers,
            "growth": growth,
            "growth_percentage": round(growth_percentage, 2),
            "direction": direction
        }

        if start_month and end_month:
            result["start_month"] = start_month
            result["end_month"] = end_month
            result["filter_applied"] = True
        else:
            result["filter_applied"] = False

        return result

    # Default behavior:
    # Show growth across the complete available history.

    report["growth"] = calculate_growth(user_history)

    print("\nOverall follower growth:")

    if report["growth"]["status"] == "available":

        print(
            f"Period: {report['growth']['start_date']} "
            f"to {report['growth']['end_date']}"
        )

        print(
            f"Starting followers: "
            f"{report['growth']['start_followers']}"
        )

        print(
            f"Ending followers: "
            f"{report['growth']['end_followers']}"
        )

        print(
            f"Growth: "
            f"{report['growth']['growth']}"
        )

        print(
            f"Growth percentage: "
            f"{report['growth']['growth_percentage']}%"
        )

        print(
            f"Direction: "
            f"{report['growth']['direction']}"
        )

    else:

        print(
            report["growth"]["reason"]
        )

    # -------------------- Optional Month Filter --------------------

    if start_month and end_month:

        filtered_growth = calculate_growth(
            user_history,
            start_month,
            end_month
        )

        report["growth"] = filtered_growth

        print("\nFiltered follower growth:")

        if filtered_growth["status"] == "available":

            print(
                f"Period: {filtered_growth['start_date']} "
                f"to {filtered_growth['end_date']}"
            )

            print(
                f"Starting followers: "
                f"{filtered_growth['start_followers']}"
            )

            print(
                f"Ending followers: "
                f"{filtered_growth['end_followers']}"
            )

            print(
                f"Growth: "
                f"{filtered_growth['growth']}"
            )

            print(
                f"Growth percentage: "
                f"{filtered_growth['growth_percentage']}%"
            )

            print(
                f"Direction: "
                f"{filtered_growth['direction']}"
            )

        else:

            print(
                filtered_growth["reason"]
            )

    # -------------------- Instagram Profile --------------------

    print("\nInstagram Profile:")

    print(
        f"Username: {profile['username']}"
    )

    print(
        f"Followers: {profile.get('followersCount', 0)}"
    )

    print(
        f"Following: {profile.get('followsCount', 0)}"
    )

    print(
        f"Total posts: "
        f"{profile.get('postsCount') or len(profile.get('latestPosts', []))}"
    )

    print(
        f"Verified: {profile.get('verified', False)}"
    )

    print(
        f"Scraped posts analyzed: {len(data)}"
    )

    # -------------------- Basic Metrics --------------------

    valid_likes = [
        post.get("likesCount")
        for post in data
        if post.get("likesCount") is not None
        and post.get("likesCount") >= 0
    ]

    total_comments = sum(
        post.get("commentsCount", 0) or 0
        for post in data
    )

    average_comments = (
        total_comments / len(data)
        if data
        else 0
    )

    total_likes = sum(valid_likes)

    average_likes = (
        total_likes / len(valid_likes)
        if valid_likes
        else 0
    )

    # -------------------- Engagement Metrics --------------------

    total_interactions = (
        total_likes +
        total_comments
    )

    average_interactions = (
        total_interactions / len(data)
        if data
        else 0
    )

    print(
        f"Total interactions: {total_interactions}"
    )

    print(
        f"Average interactions per post: {average_interactions}"
    )

    video_views = [
        post.get("videoViewCount")
        for post in data
        if post.get("videoViewCount") is not None
        and post.get("videoViewCount") >= 0
    ]

    total_video_views = sum(video_views)

    average_video_views = (
        total_video_views / len(video_views)
        if video_views
        else 0
    )

    report["metrics"] = {
        "total_interactions": total_interactions,
        "average_interactions_per_post": average_interactions,
        "total_comments": total_comments,
        "average_comments": average_comments,
        "total_likes": total_likes,
        "average_likes": average_likes,
        "total_video_views": total_video_views,
        "average_video_views": average_video_views
    }

    print(
        f"Total comments: {total_comments}"
    )

    print(
        f"Average comments: {average_comments}"
    )

    print(
        f"Total likes: {total_likes}"
    )

    print(
        f"Average likes: {average_likes}"
    )

    print(
        f"Total video views: {total_video_views}"
    )

    print(
        f"Average video views: {average_video_views}"
    )

    # -------------------- Best Performing Post --------------------

    posts_with_likes = [
        post
        for post in data
        if post.get("likesCount") is not None
        and post.get("likesCount") >= 0
    ]

    if posts_with_likes:

        best_post = max(
            posts_with_likes,
            key=lambda post: post.get("likesCount")
        )

        print("\nBest performing post:")

        print(
            f"URL: {best_post.get('url')}"
        )

        print(
            f"Likes: {best_post.get('likesCount')}"
        )

        print(
            f"Comments: {best_post.get('commentsCount')}"
        )

        print(
            f"Views: {best_post.get('videoViewCount')}"
        )

        print(
            f"Timestamp: {best_post.get('timestamp')}"
        )

    # -------------------- Top Performing Posts --------------------

    top_posts = sorted(
        posts_with_likes,
        key=lambda post: post.get("likesCount"),
        reverse=True
    )[:3]

    report["top_posts"] = []

    def _resolve_post_name(p):
        try:
            name = generate_post_name(p)
            return name if name else "Instagram Post"

        except Exception as error:
            logger.error(
                f"Post name generation failed for "
                f"{p.get('shortCode')}: {error}"
            )
            return "Instagram Post"

    if top_posts:

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=min(3, len(top_posts))
        ) as executor:

            resolved_names = list(
                executor.map(_resolve_post_name, top_posts)
            )

    else:
        resolved_names = []

    for post, post_name in zip(top_posts, resolved_names):

        caption = post.get("caption")

        if caption:
            caption = caption.strip()

        report["top_posts"].append({
            "short_code": post.get("shortCode"),
            "post_name": post_name,
            "caption": caption,
            "likes": post.get("likesCount"),
            "comments": post.get("commentsCount", 0),
            "views": post.get("videoViewCount"),
            "url": post.get("url"),
            "timestamp": post.get("timestamp")
        })

    print("\nTop Performing Posts:")

    for index, post in enumerate(
        report["top_posts"],
        start=1
    ):

        print(
            f"\n{index}. {post.get('post_name')}"
        )

        print(
            f"Short code: {post.get('short_code')}"
        )

        print(
            f"Likes: {post.get('likes')}"
        )

        print(
            f"Comments: {post.get('comments')}"
        )

        print(
            f"Views: {post.get('views')}"
        )

        print(
            f"URL: {post.get('url')}"
        )

    # -------------------- Post Details --------------------

    for post in data:

        product_type = post.get("productType")

        if product_type:
            post_type = product_type.replace(
                "_",
                " "
            ).title()
        else:
            post_type = "Unknown"

        print("\n--------------------")

        print(
            f"Type: {post_type}"
        )

        print(
            f"URL: {post.get('url')}"
        )

        print(
            f"Likes: {post.get('likesCount')}"
        )

        print(
            f"Comments: {post.get('commentsCount')}"
        )

        print(
            f"Views: {post.get('videoViewCount')}"
        )

        print(
            f"Timestamp: {post.get('timestamp')}"
        )

        print(
            f"Content type: {product_type}"
        )

    # -------------------- Posting Time Analysis --------------------

    hourly_likes = defaultdict(list)

    for post in data:

        likes = post.get("likesCount")

        if likes is None or likes < 0:
            continue

        timestamp = post.get("timestamp")

        if timestamp:

            date = datetime.fromisoformat(
                timestamp.replace("Z", "+00:00")
            )

            hour = date.hour

            print(
                f"Post: {post.get('shortCode')} | "
                f"Hour: {hour} | "
                f"Likes: {likes}"
            )

            hourly_likes[hour].append(likes)

    print("\nHourly likes:")

    for hour, likes in hourly_likes.items():

        average = sum(likes) / len(likes)

        print(
            f"{hour:02d}:00 -> "
            f"Posts: {len(likes)} | "
            f"Average likes: {average}"
        )

    posting_analysis = []

    for hour, likes in hourly_likes.items():

        average = sum(likes) / len(likes)

        posting_analysis.append({
            "hour": hour,
            "posts": len(likes),
            "average_likes": average
        })

    report["posting_analysis"] = posting_analysis

    # -------------------- Content Type Analysis --------------------

    content_likes = defaultdict(list)

    for post in data:

        likes = post.get("likesCount")

        if likes is None or likes < 0:
            continue

        product_type = post.get("productType")

        if product_type:
            content_type = product_type
        else:
            content_type = "unknown"

        content_likes[content_type].append(likes)

    print("\nContent type performance:")

    for content_type, likes in content_likes.items():

        average = sum(likes) / len(likes)

        readable_type = content_type.replace(
            "_",
            " "
        ).title()

        print(
            f"{readable_type} -> "
            f"Posts: {len(likes)} | "
            f"Average likes: {average}"
        )

    content_analysis = []

    for content_type, likes in content_likes.items():

        average = sum(likes) / len(likes)

        content_analysis.append({
            "content_type": content_type,
            "posts": len(likes),
            "average_likes": average
        })

    report["content_analysis"] = content_analysis

    # -------------------- Detect All Content Types --------------------

    print("\nContent types found in scraped data:")

    all_content_types = set(
        post.get("productType")
        for post in data
        if post.get("productType")
    )

    for content_type in sorted(all_content_types):

        print(
            f"- {content_type}"
        )

    # -------------------- Video Interaction Rate --------------------

    video_engagement = []

    for post in data:

        views = post.get("videoViewCount")
        likes = post.get("likesCount")
        comments = post.get("commentsCount", 0) or 0

        if likes is None or likes < 0:
            continue

        if views is None or views <= 0:
            continue

        interaction_rate = (
            (likes + comments) / views
        ) * 100

        video_engagement.append(
            (interaction_rate, post)
        )

    print("\nVideo Interaction Rate:")

    for interaction_rate, post in video_engagement:

        print(
            f"{post.get('shortCode')} -> "
            f"Interaction rate: {interaction_rate:.2f}%"
        )

    video_analysis = []

    for interaction_rate, post in video_engagement:

        video_analysis.append({
            "short_code": post.get("shortCode"),
            "views": post.get("videoViewCount"),
            "likes": post.get("likesCount"),
            "comments": post.get("commentsCount", 0),
            "interaction_rate": round(
                interaction_rate,
                2
            )
        })

    report["video_analysis"] = video_analysis

    # ============================================================
    # LLM RELIABLE INSIGHTS
    # ============================================================

    llm_insights = []

    # -------------------- Reliable Posting Time Insight --------------------

    reliable_hours = {
        hour: likes
        for hour, likes in hourly_likes.items()
        if len(likes) >= 5
    }

    if reliable_hours:

        best_hour = max(
            reliable_hours,
            key=lambda hour:
            sum(reliable_hours[hour]) /
            len(reliable_hours[hour])
        )

        best_hour_likes = reliable_hours[best_hour]

        best_hour_average = (
            sum(best_hour_likes) /
            len(best_hour_likes)
        )

        llm_insights.append({
            "type": "posting_time",
            "insight": (
                f"{best_hour:02d}:00 has the highest average likes "
                f"among posting hours with at least 5 analyzed posts."
            ),
            "evidence": {
                "hour": best_hour,
                "posts": len(best_hour_likes),
                "average_likes": round(
                    best_hour_average,
                    2
                )
            }
        })

    # -------------------- Reliable Content Type Insight --------------------

    reliable_content_types = {
        content_type: likes
        for content_type, likes in content_likes.items()
        if len(likes) >= 5
    }

    if (
        "carousel_container" in reliable_content_types
        and "clips" in reliable_content_types
    ):

        carousel_likes = reliable_content_types["carousel_container"]
        video_likes = reliable_content_types["clips"]

        carousel_average = (
            sum(carousel_likes) /
            len(carousel_likes)
        )

        video_average = (
            sum(video_likes) /
            len(video_likes)
        )

        if carousel_average > video_average:

            llm_insights.append({
                "type": "content_type",
                "insight": (
                    "Carousel posts have a higher average like count "
                    "than clips in the analyzed sample."
                ),
                "evidence": {
                    "carousel_posts": len(carousel_likes),
                    "carousel_average_likes": round(
                        carousel_average,
                        2
                    ),
                    "clips_posts": len(video_likes),
                    "clips_average_likes": round(
                        video_average,
                        2
                    )
                }
            })

        elif video_average > carousel_average:

            llm_insights.append({
                "type": "content_type",
                "insight": (
                    "Clips have a higher average like count "
                    "than carousel posts in the analyzed sample."
                ),
                "evidence": {
                    "carousel_posts": len(carousel_likes),
                    "carousel_average_likes": round(
                        carousel_average,
                        2
                    ),
                    "clips_posts": len(video_likes),
                    "clips_average_likes": round(
                        video_average,
                        2
                    )
                }
            })

    # -------------------- Reliable Video Insight --------------------

    if video_engagement:

        best_video = max(
            video_engagement,
            key=lambda item: item[0]
        )

        best_video_rate = best_video[0]
        best_video_post = best_video[1]
        best_video_name = _resolve_post_name(best_video_post)

        llm_insights.append({
            "type": "video_performance",
            "insight": (
                f"Your top analyzed video '{best_video_name}' achieved the highest observed "
                "video interaction rate in the sample."
            ),
            "evidence": {
                "short_code": best_video_post.get("shortCode"),
                "post_name": best_video_name,
                "interaction_rate": round(
                    best_video_rate,
                    2
                ),
                "views": best_video_post.get("videoViewCount"),
                "likes": best_video_post.get("likesCount"),
                "comments": best_video_post.get("commentsCount", 0)
            }
        })

    # -------------------- Follower Growth Insight --------------------

    if report["growth"].get("status") == "available":

        growth = report["growth"]

        llm_insights.append({
            "type": "follower_growth",
            "insight": (
                "Follower growth can be used to evaluate whether future "
                "content strategies are associated with account growth, "
                "but the available data does not establish the cause of growth."
            ),
            "evidence": {
                "start_date": growth["start_date"],
                "end_date": growth["end_date"],
                "start_followers": growth["start_followers"],
                "end_followers": growth["end_followers"],
                "growth": growth["growth"],
                "growth_percentage": growth["growth_percentage"],
                "direction": growth["direction"]
            }
        })

    if report["top_posts"]:

        top_post = report["top_posts"][0]

        llm_insights.append({
            "type": "top_post",
            "insight": (
                f"The highest-liked analyzed post "
                f"'{top_post.get('post_name')}' received "
                f"{top_post.get('likes')} likes and "
                f"{top_post.get('comments')} comments."
            ),
            "evidence": {
                "short_code": top_post.get("short_code"),
                "post_name": top_post.get("post_name"),
                "likes": top_post.get("likes"),
                "comments": top_post.get("comments"),
                "views": top_post.get("views")
            }
        })

    report["llm_insights"] = llm_insights

    print("\nLLM Reliable Insights:")

    for insight in llm_insights:

        print(
            f"\nType: {insight['type']}"
        )

        print(
            f"Insight: {insight['insight']}"
        )

        print(
            f"Evidence: {insight['evidence']}"
        )

    # -------------------- Growth Suggestions --------------------

    print("\nGrowth Suggestions:")

    suggestions = []

    video_likes = content_likes.get(
        "clips",
        []
    )

    carousel_likes = content_likes.get(
        "carousel_container",
        []
    )

    video_avg = (
        sum(video_likes) / len(video_likes)
        if video_likes
        else 0
    )

    carousel_avg = (
        sum(carousel_likes) / len(carousel_likes)
        if carousel_likes
        else 0
    )

    if video_likes and carousel_likes:

        if video_avg > carousel_avg:

            suggestion = (
                "Video posts have a higher average like count "
                "than carousel posts in the scraped sample. "
                "Consider testing more short-form video content."
            )

            suggestions.append(suggestion)

            print(
                f"- {suggestion}"
            )

        elif carousel_avg > video_avg:

            suggestion = (
                "Carousel posts have a higher average like count "
                "than video posts in the scraped sample. "
                "Consider testing more carousel content."
            )

            suggestions.append(suggestion)

            print(
                f"- {suggestion}"
            )

    # -------------------- Best Posting Time Suggestion --------------------

    if hourly_likes:

        reliable_hours = {
            hour: likes
            for hour, likes in hourly_likes.items()
            if len(likes) >= 5
        }

        if reliable_hours:

            best_hour = max(
                reliable_hours,
                key=lambda hour:
                sum(reliable_hours[hour]) /
                len(reliable_hours[hour])
            )

            suggestion = (
                f"The highest observed average like count "
                f"among posting times with at least 5 posts "
                f"occurred at {best_hour:02d}:00."
            )

            suggestions.append(suggestion)

            print(
                f"- {suggestion}"
            )

            suggestion = (
                "Consider testing this posting window with "
                "future posts and comparing the results."
            )

            suggestions.append(suggestion)

            print(
                f"- {suggestion}"
            )

        else:

            # Fallback: use all hours even if < 5 posts per hour,
            # but flag it as preliminary data.
            if hourly_likes:

                best_hour_fallback = max(
                    hourly_likes,
                    key=lambda hour:
                    sum(hourly_likes[hour]) /
                    len(hourly_likes[hour])
                )

                best_avg_fallback = (
                    sum(hourly_likes[best_hour_fallback]) /
                    len(hourly_likes[best_hour_fallback])
                )

                suggestion = (
                    f"Based on your current data, posts at "
                    f"{best_hour_fallback:02d}:00 have the highest "
                    f"average likes ({best_avg_fallback:,.0f}). "
                    f"Note: this is based on limited data "
                    f"(fewer than 5 posts per hour). Post more "
                    f"consistently to get a more reliable recommendation."
                )

            else:

                suggestion = (
                    "There is not enough data to identify a "
                    "best posting time yet. Start posting regularly "
                    "so we can analyze your performance."
                )

            suggestions.append(suggestion)

            print(
                f"- {suggestion}"
            )

    # -------------------- Best Video Engagement Suggestion --------------------

    if video_engagement:

        best_engagement = max(
            video_engagement,
            key=lambda item: item[0]
        )

        suggestion = (
            f"The highest observed video interaction rate "
            f"was {best_engagement[0]:.2f}%."
        )

        suggestions.append(suggestion)

        print(
            f"- {suggestion}"
        )

    report["suggestions"] = suggestions

    # -------------------- Logging --------------------

    logger.info(
        f"Analytics processing completed for: {username}"
    )

    # -------------------- Optional Report Saving --------------------

    if save_report:

        report_file = Path(
            "backend/data/analytics_report.json"
        )

        report_file.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        with open(
            report_file,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                report,
                f,
                indent=4,
                ensure_ascii=False
            )

    # -------------------- Final Report --------------------

    print(
        "\n\n========== FINAL REPORT =========="
    )

    print(
        json.dumps(
            report,
            indent=4,
            ensure_ascii=True
        )
    )

    return report
