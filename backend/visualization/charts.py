import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter


# ---------------------------------------------------------
# NUMBER FORMATTER
# ---------------------------------------------------------

def format_number(value, position=None):
    value = float(value)

    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"

    if abs(value) >= 1_000:
        return f"{value / 1_000:.1f}K"

    return f"{value:.0f}"


number_formatter = FuncFormatter(format_number)


# ---------------------------------------------------------
# CONTENT TYPE NAME
# ---------------------------------------------------------

def format_content_type(content_type):
    mapping = {
        "carousel_container": "Carousel",
        "clips": "Reels / Clips",
        "feed": "Feed"
    }

    return mapping.get(
        content_type,
        str(content_type).replace("_", " ").title()
    )


# ---------------------------------------------------------
# CONTENT DISTRIBUTION
# ---------------------------------------------------------

def generate_content_distribution(report):

    content_analysis = report.get(
        "content_analysis",
        []
    )

    if not content_analysis:
        return None

    labels = [
        format_content_type(
            item.get("content_type", "Unknown")
        )
        for item in content_analysis
    ]

    values = [
        item.get("posts", 0)
        for item in content_analysis
    ]

    fig, ax = plt.subplots(
        figsize=(8, 5)
    )

    ax.pie(
        values,
        labels=labels,
        autopct="%1.1f%%",
        startangle=90
    )

    ax.set_title(
        "Content Distribution"
    )

    return fig


# ---------------------------------------------------------
# AVERAGE LIKES BY CONTENT TYPE
# ---------------------------------------------------------

def generate_average_likes_chart(report):

    content_analysis = report.get(
        "content_analysis",
        []
    )

    if not content_analysis:
        return None

    labels = [
        format_content_type(
            item.get("content_type", "Unknown")
        )
        for item in content_analysis
    ]

    values = [
        item.get("average_likes", 0)
        for item in content_analysis
    ]

    fig, ax = plt.subplots(
        figsize=(8, 5)
    )

    bars = ax.bar(
        labels,
        values
    )

    ax.set_title(
        "Average Likes by Content Type"
    )

    ax.set_xlabel(
        "Content Type"
    )

    ax.set_ylabel(
        "Average Likes"
    )

    # Format Y-axis as K/M
    ax.yaxis.set_major_formatter(
        number_formatter
    )

    # Show exact value above every bar
    for bar, value in zip(
        bars,
        values
    ):

        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            format_number(value),
            ha="center",
            va="bottom",
            fontsize=10
        )

    plt.xticks(
        rotation=20
    )

    plt.tight_layout()

    return fig


# ---------------------------------------------------------
# POSTING TIME PERFORMANCE
# ---------------------------------------------------------

def generate_posting_time_chart(report):

    posting_analysis = report.get(
        "posting_analysis",
        []
    )

    if not posting_analysis:
        return None

    # Sort by hour so chart is chronological
    posting_analysis = sorted(
        posting_analysis,
        key=lambda item: item.get("hour", 0)
    )

    hours = [
        item.get("hour", 0)
        for item in posting_analysis
    ]

    average_likes = [
        item.get("average_likes", 0)
        for item in posting_analysis
    ]

    # Convert hour to readable time
    time_labels = [
        f"{hour:02d}:00"
        for hour in hours
    ]

    fig, ax = plt.subplots(
        figsize=(10, 5)
    )

    bars = ax.bar(
        time_labels,
        average_likes
    )

    ax.set_title(
        "Posting Time Performance"
    )

    ax.set_xlabel(
        "Posting Time"
    )

    ax.set_ylabel(
        "Average Likes"
    )

    # Format Y-axis as K/M
    ax.yaxis.set_major_formatter(
        number_formatter
    )

    # Show exact average likes above every bar
    for bar, value in zip(
        bars,
        average_likes
    ):

        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            format_number(value),
            ha="center",
            va="bottom",
            fontsize=9
        )

    plt.xticks(
        rotation=45,
        ha="right"
    )

    plt.tight_layout()

    return fig


# ---------------------------------------------------------
# TOP 3 POSTS
# ---------------------------------------------------------

def generate_top_posts_chart(report):

    top_posts = report.get(
        "top_posts",
        []
    )

    if not top_posts:
        return None

    top_posts = top_posts[:3]

    names = [
        (
            post.get("post_name")
            or "Instagram Post"
        )
        for post in top_posts
    ]

    likes = [
        post.get(
            "likes",
            0
        )
        for post in top_posts
    ]

    fig, ax = plt.subplots(
        figsize=(10, 5)
    )

    bars = ax.bar(
        names,
        likes
    )

    ax.set_title(
        "Top 3 Posts by Likes"
    )

    ax.set_xlabel(
        "Post"
    )

    ax.set_ylabel(
        "Likes"
    )

    # Format Y-axis as K/M
    ax.yaxis.set_major_formatter(
        number_formatter
    )

    # Show exact likes above every post
    for bar, value in zip(
        bars,
        likes
    ):

        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            format_number(value),
            ha="center",
            va="bottom",
            fontsize=10
        )

    plt.xticks(
        rotation=20,
        ha="right"
    )

    plt.tight_layout()

    return fig


# ---------------------------------------------------------
# GENERATE ALL CHARTS
# ---------------------------------------------------------

def generate_charts(report):

    return {
        "content_distribution":
            generate_content_distribution(report),

        "average_likes":
            generate_average_likes_chart(report),

        "posting_time":
            generate_posting_time_chart(report),

        "top_posts":
            generate_top_posts_chart(report)
    }