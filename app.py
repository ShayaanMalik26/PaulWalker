from fastapi import FastAPI, Query, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import chromadb
from sentence_transformers import SentenceTransformer
import os
import json
from add_embedding import load_json, generate_embeddings, store_in_chromadb

app = FastAPI()

# Serve static files (HTML, CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize ChromaDB client
client = chromadb.PersistentClient(path="./chromadb_store")
collection = client.get_or_create_collection("patents_collection", metadata={"hnsw:space": "cosine"})

# Load BERT model
model = SentenceTransformer("all-MiniLM-L6-v2")

@app.get("/")
def serve_homepage():
    return FileResponse("static/index.html")  # Serve the HTML file

@app.get("/search")
def search(query: str = Query(..., description="Search query text")):
    # Compute query embedding
    query_embedding = model.encode([query])[0].tolist()

    # Perform search in ChromaDB
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=3  # Return top 5 results
    )

    # Format response
    documents = results.get("documents", [[]])[0]
    return {"query": query, "results": documents}



# Run with: uvicorn app:app --reload
