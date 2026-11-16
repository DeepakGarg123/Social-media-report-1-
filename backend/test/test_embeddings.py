from backend.rag.embeddings import create_embedding_model

print("Starting embedding test...", flush=True)

embedding_model = create_embedding_model()

print("Model loaded successfully!", flush=True)

text = "Instagram growth depends on engaging content."

vector = embedding_model.embed_query(text)

print("Embedding length:", len(vector))
print("First 5 values:", vector[:5])