from langchain_community.embeddings.fastembed import FastEmbedEmbeddings


def create_embedding_model():
    embedding_model = FastEmbedEmbeddings(
        model_name="BAAI/bge-small-en-v1.5"
    )

    return embedding_model