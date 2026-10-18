import json
import os

CACHE_FILE = "backend/data/cache/post_names_cache.json"


def _get_clean_post_name(short_code, report):
    """Find or resolve a human-readable post name without exposing short codes."""
    if not short_code:
        return "Featured Instagram Reel"

    # 1. Check top_posts in report
    for post in report.get("top_posts", []):
        if post.get("short_code") == short_code and post.get("post_name"):
            return post.get("post_name")

    # 2. Check local post name cache
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                cache = json.load(f)
                if short_code in cache and cache[short_code]:
                    return cache[short_code]
        except Exception:
            pass

    return "Peak Engagement Reel"


def build_recommendations(report):
    """
    Build rich, evidence-grounded recommendations for all analytics signals:
    - Content Format Strategy (Clips/Reels vs Carousels)
    - Peak Upload Window (Best Posting Time)
    - Video Interaction Benchmark (Highest Engagement Reel)
    - Top Creative Anchor (Highest-Liked Post)
    - Audience Growth Momentum (Follower Growth & Retention)
    """
    insights = report.get("llm_insights", [])
    recommendations = []
    handled_types = set()

    for insight in insights:
        insight_type = insight.get("type")
        evidence = insight.get("evidence", {})

        if insight_type == "content_type":
            handled_types.add("content_type")
            carousel_posts = evidence.get("carousel_posts", 0)
            carousel_avg = evidence.get("carousel_average_likes", 0)
            clips_posts = evidence.get("clips_posts", 0)
            clips_avg = evidence.get("clips_average_likes", 0)

            if clips_avg >= carousel_avg:
                action = (
                    f"Prioritize short-form video Reels/Clips as your primary reach engine. "
                    f"Your video clips averaged {clips_avg:,.0f} likes across {clips_posts} posts, "
                    f"outperforming carousels which averaged {carousel_avg:,.0f} likes across {carousel_posts} posts."
                )
                winning_format = "Reels / Video Clips"
            else:
                action = (
                    f"Prioritize multi-slide Carousel posts as your primary engagement driver. "
                    f"Your carousels averaged {carousel_avg:,.0f} likes across {carousel_posts} posts, "
                    f"outperforming video clips which averaged {clips_avg:,.0f} likes across {clips_posts} posts."
                )
                winning_format = "Carousels"

            recommendations.append({
                "type": "content_type",
                "title": f"Focus on {winning_format} for Higher Average Engagement",
                "action": action,
                "evidence": {
                    "winning_format": winning_format,
                    "clips_posts": clips_posts,
                    "clips_average_likes": clips_avg,
                    "carousel_posts": carousel_posts,
                    "carousel_average_likes": carousel_avg
                }
            })

        elif insight_type == "posting_time":
            handled_types.add("posting_time")
            hour = evidence.get("hour")
            posts = evidence.get("posts", 0)
            avg_likes = evidence.get("average_likes", 0)

            if hour is not None:
                formatted_time = f"{hour:02d}:00 UTC"
                recommendations.append({
                    "type": "posting_time",
                    "title": f"Publish During Your Peak Engagement Window ({formatted_time})",
                    "action": (
                        f"Schedule your highest-priority posts around {formatted_time}. "
                        f"In this posting window, your posts achieved their highest average of {avg_likes:,.0f} likes "
                        f"across {posts} analyzed posts."
                    ),
                    "evidence": {
                        "peak_hour": hour,
                        "peak_time_utc": formatted_time,
                        "posts_in_window": posts,
                        "average_likes": avg_likes
                    }
                })

        elif insight_type == "video_performance":
            handled_types.add("video_performance")
            post_name = evidence.get("post_name")
            short_code = evidence.get("short_code")
            if not post_name:
                post_name = _get_clean_post_name(short_code, report)

            interaction_rate = evidence.get("interaction_rate")
            views = evidence.get("views")
            likes = evidence.get("likes")
            comments = evidence.get("comments")

            if interaction_rate is not None:
                recommendations.append({
                    "type": "video_performance",
                    "title": f"Benchmark Video Hooks Against Your Top Reel ('{post_name}')",
                    "action": (
                        f"Study the opening hook, pacing, and visual style of '{post_name}', "
                        f"which achieved a stellar {interaction_rate:.2f}% interaction rate "
                        f"({likes:,.0f} likes and {comments:,.0f} comments over {views:,.0f} views). "
                        f"Use this {interaction_rate:.2f}% interaction rate as the benchmark to beat for future videos."
                    ),
                    "evidence": {
                        "post_name": post_name,
                        "interaction_rate": interaction_rate,
                        "views": views,
                        "likes": likes,
                        "comments": comments
                    }
                })

        elif insight_type == "top_post":
            handled_types.add("top_post")
            post_name = evidence.get("post_name") or "Your Highest-Liked Post"
            likes = evidence.get("likes")
            comments = evidence.get("comments")
            views = evidence.get("views")

            if likes is not None:
                recommendations.append({
                    "type": "top_post",
                    "title": f"Deconstruct and Scale Your Winning Content Anchor ('{post_name}')",
                    "action": (
                        f"Analyze the themes, caption hook, and presentation of '{post_name}', "
                        f"which generated your highest total engagement with {likes:,.0f} likes and {comments:,.0f} comments. "
                        f"Turn this proven topic or aesthetic into a recurring series or signature style."
                    ),
                    "evidence": {
                        "post_name": post_name,
                        "likes": likes,
                        "comments": comments,
                        "views": views
                    }
                })

        elif insight_type == "follower_growth":
            handled_types.add("follower_growth")
            growth = evidence.get("growth")
            growth_pct = evidence.get("growth_percentage")
            direction = evidence.get("direction", "increase")
            start_date = evidence.get("start_date")
            end_date = evidence.get("end_date")

            if growth is not None:
                if direction == "increase" or growth > 0:
                    action = (
                        f"Keep up your posting consistency to sustain your upward audience momentum. "
                        f"Your account grew by +{abs(growth):,} followers (+{abs(growth_pct):.2f}%) "
                        f"between {start_date} and {end_date}."
                    )
                else:
                    action = (
                        f"Focus on active community engagement and interactive content to stabilize follower numbers, "
                        f"which shifted by {growth:,} ({growth_pct:.2f}%) between {start_date} and {end_date}."
                    )

                recommendations.append({
                    "type": "follower_growth",
                    "title": "Sustain Audience Momentum and Follower Conversion",
                    "action": action,
                    "evidence": {
                        "growth": growth,
                        "growth_percentage": growth_pct,
                        "direction": direction,
                        "start_date": start_date,
                        "end_date": end_date
                    }
                })

    # Fallbacks in case llm_insights was missing some signals
    if "top_post" not in handled_types and report.get("top_posts"):
        top_post = report["top_posts"][0]
        post_name = top_post.get("post_name") or "Your Top Post"
        likes = top_post.get("likes")
        comments = top_post.get("comments")
        views = top_post.get("views")
        if likes is not None:
            recommendations.append({
                "type": "top_post",
                "title": f"Deconstruct and Scale Your Winning Content Anchor ('{post_name}')",
                "action": (
                    f"Analyze the themes, caption hook, and presentation of '{post_name}', "
                    f"which generated your highest total engagement with {likes:,.0f} likes and {comments:,.0f} comments."
                ),
                "evidence": {
                    "post_name": post_name,
                    "likes": likes,
                    "comments": comments,
                    "views": views
                }
            })

    return recommendations