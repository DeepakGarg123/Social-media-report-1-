
def extract_sources(retrieved_documents):

    sources = []

    for document in retrieved_documents:

        section = document.metadata.get("section", "Unknown")

        if section not in sources:
            sources.append(section)

    return sources
