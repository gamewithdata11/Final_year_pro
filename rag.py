import numpy as np
import faiss
import pickle
from sentence_transformers import SentenceTransformer
from pypdf import PdfReader
from pathlib import Path

DOCUMENTS_FOLDER = Path("documents")

def load_documents():
    all_text = []

    for pdf_file in DOCUMENTS_FOLDER.glob("*.pdf"):
        reader = PdfReader(str(pdf_file))

        for page_number, page in enumerate(reader.pages, start=1):
            text = page.extract_text()

            if text:
                all_text.append({
                    "text": text,
                    "source": pdf_file.name,
                    "page": page_number
                })

    return all_text


def create_chunks(documents, chunk_size=500, overlap=100):
    chunks = []

    for document in documents:
        text = document["text"]
        start = 0

        while start < len(text):
            end = start + chunk_size

            chunks.append({
                "text": text[start:end],
                "source": document["source"],
                "page": document["page"]
            })

            start += chunk_size - overlap

    return chunks

def build_vector_index(chunks):
    print("Loading embedding model...")

    model = SentenceTransformer(
        "sentence-transformers/all-MiniLM-L6-v2"
    )

    texts = [chunk["text"] for chunk in chunks]

    print("Creating embeddings...")

    embeddings = model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True
    ).astype("float32")

    print("Building FAISS index...")

    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)

    faiss.write_index(index, "college_faiss.index")

    with open("college_chunks.pkl", "wb") as file:
        pickle.dump(chunks, file)

    print("Vector index created successfully!")
    print("Total indexed chunks:", index.ntotal)

# These variables keep the model and index loaded in memory
# so they don't need to reload for every question.

_retrieval_model = None
_retrieval_index = None
_retrieval_chunks = None


def retrieve_relevant_chunks(question, top_k=3):
    global _retrieval_model, _retrieval_index, _retrieval_chunks

    # Load resources only the first time
    if _retrieval_model is None:
        print("Loading RAG resources...")

        _retrieval_model = SentenceTransformer(
            "sentence-transformers/all-MiniLM-L6-v2"
        )

        _retrieval_index = faiss.read_index("college_faiss.index")

        with open("college_chunks.pkl", "rb") as file:
            _retrieval_chunks = pickle.load(file)

    # Convert the question into an embedding
    question_embedding = _retrieval_model.encode(
        [question],
        convert_to_numpy=True,
        normalize_embeddings=True
    ).astype("float32")

    # Search FAISS for relevant chunks
    distances, indices = _retrieval_index.search(
        question_embedding,
        min(top_k, _retrieval_index.ntotal)
    )

    results = []

    for chunk_index in indices[0]:
        if chunk_index == -1:
            continue

        results.append(_retrieval_chunks[chunk_index])

    return results

if __name__ == "__main__":
    
    documents = load_documents()

    print("Total pages loaded:", len(documents))

    chunks = create_chunks(documents)

    print("Total text chunks created:", len(chunks))

    build_vector_index(chunks)

    print("Total pages loaded:", len(documents))
    print("Total text chunks created:", len(chunks))

