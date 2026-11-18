
import pickle
import faiss
from sentence_transformers import SentenceTransformer

# Load the saved FAISS index
index = faiss.read_index("college_faiss.index")

# Load the saved text chunks
with open("college_chunks.pkl", "rb") as file:
    chunks = pickle.load(file)

# Load the embedding model
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# Ask a question
question = "When is the Student Support Office open?"

# Convert question into an embedding
question_embedding = model.encode(
    [question],
    convert_to_numpy=True,
    normalize_embeddings=True
).astype("float32")

# Search for the 3 most relevant chunks
distances, indices = index.search(question_embedding, 3)

print("\nYour Question:", question)
print("\nRelevant Information:\n")

for position, chunk_index in enumerate(indices[0], start=1):
    if chunk_index == -1:
        continue

    result = chunks[chunk_index]

    print(f"Result {position}")
    print("Source:", result["source"])
    print("Page:", result["page"])
    print("Content:", result["text"])
    print("-" * 50)
