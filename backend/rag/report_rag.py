from langchain_core.documents import Document
def create_profile_document(report):
    profile = report["profile"]

    content = f"""
    Instagram Username: {profile['username']}
    Full Name: {profile['full_name']}
    Followers: {profile['followers']}
    Following: {profile['following']}
    Total Posts: {profile['total_posts']}
    Biography: {profile['biography']}
    """

    document = Document(
        page_content=content,
        metadata={"section": "profile"}
    )
    return document

def create_metrics_document(report):
    metrics = report["metrics"]

    content = f"""
    Total Interactions: {metrics['total_interactions']}
    Average Interactions Per Post: {metrics['average_interactions_per_post']}
    Total Likes: {metrics['total_likes']}
    Average Likes: {metrics['average_likes']}
    Total Comments: {metrics['total_comments']}
    Average Comments: {metrics['average_comments']}
    """

    document = Document(
        page_content=content,
        metadata={"section": "metrics"}
    )
    return document


def create_top_posts_documents(report):
    top_posts = report["top_posts"]

    documents = []

    for post in top_posts:
        content = f"""
        Post Name: {post['post_name']}
        Caption: {post['caption']}
        Likes: {post['likes']}
        Comments: {post['comments']}
        Views: {post['views']}
        Post URL: {post['url']}
        """

        document = Document(
            page_content=content,
            metadata={
                "section": "top_posts",
                "post_name": post["post_name"]
            }
        )

        documents.append(document)

    return documents



def create_report_documents(report):
    documents = []

    profile_document = create_profile_document(report)
    metrics_document = create_metrics_document(report)
    top_posts_documents = create_top_posts_documents(report)
    suggestions_document = create_suggestions_document(report)
    posting_analysis_document = create_posting_analysis_document(report)
    content_analysis_document = create_content_analysis_document(report)
    growth_analysis_document = create_growth_document(report)
    llm_insights_document = create_llm_insights_document(report)

    documents.append(profile_document)
    documents.append(metrics_document)
    documents.extend(top_posts_documents)
    documents.append(suggestions_document)
    documents.append(posting_analysis_document)
    documents.append(content_analysis_document)
    documents.append(growth_analysis_document)
    documents.append(llm_insights_document)

    return documents


def create_suggestions_document(report):
    suggestions = report["suggestions"]

    content = "Instagram Account Suggestions:\n"

    for index, suggestion in enumerate(suggestions, start=1):
        content += f"\nSuggestion {index}: {suggestion}"

    document = Document(
        page_content=content,
        metadata={"section": "suggestions"}
    )

    return document


def create_posting_analysis_document(report):
    posting_analysis = report["posting_analysis"]

    content = "Instagram Posting Time Analysis:\n"

    for item in posting_analysis:
        content += (
            f"\nHour: {item['hour']}:00"
            f"\nNumber of Posts: {item['posts']}"
            f"\nAverage Likes: {item['average_likes']}"
            "\n"
        )

    document = Document(
        page_content=content,
        metadata={"section": "posting_analysis"}
    )

    return document

def create_content_analysis_document(report):
    content_analysis = report["content_analysis"]

    content = "Instagram Content Type Analysis:\n"

    for item in content_analysis:
        content += (
            f"\nContent Type: {item['content_type']}"
            f"\nNumber of Posts: {item['posts']}"
            f"\nAverage Likes: {item['average_likes']}"
            "\n"
        )

    document = Document(
        page_content=content,
        metadata={"section": "content_analysis"}
    )

    return document

def create_growth_document(report):
    growth = report["growth"]

    content = f"""
    Instagram Follower Growth Analysis:

    Status: {growth['status']}
    Start Date: {growth['start_date']}
    End Date: {growth['end_date']}
    Starting Followers: {growth['start_followers']}
    Ending Followers: {growth['end_followers']}
    Follower Growth: {growth['growth']}
    Growth Percentage: {growth['growth_percentage']}
    Growth Direction: {growth['direction']}
    Filter Applied: {growth['filter_applied']}
    """

    document = Document(
        page_content=content,
        metadata={"section": "growth"}
    )

    return document

def create_llm_insights_document(report):
    insights = report["llm_insights"]

    content = "Instagram AI-Generated Insights:\n"

    for index, item in enumerate(insights, start=1):
        content += (
            f"\nInsight {index}"
            f"\nType: {item['type']}"
            f"\nInsight: {item['insight']}"
            f"\nEvidence: {item['evidence']}"
            "\n"
        )

    document = Document(
        page_content=content,
        metadata={"section": "llm_insights"}
    )

    return document


