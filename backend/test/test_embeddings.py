from backend.rag.embeddings import create_embedding_model

print("Starting embedding test...", flush=True)

embedding_model = create_embedding_model()

print("Model loaded successfully!", flush=True)