
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

    documents.append(profile_document)
    documents.append(metrics_document)
    documents.extend(top_posts_documents)

    return documents


