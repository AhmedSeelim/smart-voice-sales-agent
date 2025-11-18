import json
import sqlite3
import torch
import faiss
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple
from sentence_transformers import SentenceTransformer


class ProductVectorDB:
    """Vector database for product similarity search using FAISS and multilingual embeddings."""

    def __init__(self, model_name: str = "Alibaba-NLP/gte-multilingual-base", db_directory: str = "./product_db"):
        """Initialize the vector database with SentenceTransformer model."""
        print("Loading embedding model...")
        self.model_name = model_name
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.db_directory = Path(db_directory)
        self.db_directory.mkdir(parents=True, exist_ok=True)

        # Initialize SentenceTransformer
        self.model = SentenceTransformer(model_name, trust_remote_code=True).to(self.device)

        self.index = None
        self.products_data = []
        self.id_to_index = {}

        print(f"Model loaded on device: {self.device}")

    def load_from_json(self, json_path: str):
        """Load products from JSON file and build vector database."""
        print(f"Loading products from {json_path}...")

        with open(json_path, 'r', encoding='utf-8') as f:
            products = json.load(f)

        # Store products data
        self.products_data = products

        # Create id to index mapping
        self.id_to_index = {product['id']: idx for idx, product in enumerate(products)}

        # Prepare texts for embedding (combine name and description)
        texts = [f"{product['name']} {product['description']}" for product in products]

        # Generate embeddings
        print("Generating embeddings...")
        embeddings = self.model.encode(
            texts,
            convert_to_numpy=True,
            show_progress_bar=True,
            device=self.device
        )

        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)

        # Build FAISS index
        print("Building FAISS index...")
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)  # Inner Product for cosine similarity
        self.index.add(embeddings.astype('float32'))

        print(f"Vector database created with {len(products)} products.")
        print(f"Embedding dimension: {dimension}")

    def search_similar_products(self, query: str, top_k: int = 3) -> List[Dict]:
        """Search for similar products based on query."""
        if self.index is None:
            raise ValueError("Index not initialized. Call load_from_json first.")

        # Encode query
        query_embedding = self.model.encode(
            [query],
            convert_to_numpy=True,
            device=self.device
        )

        # Normalize query embedding
        faiss.normalize_L2(query_embedding)

        # Search in FAISS index
        scores, indices = self.index.search(query_embedding.astype('float32'), top_k)

        # Extract products
        similar_products = []
        for idx, score in zip(indices[0], scores[0]):
            if idx < len(self.products_data):
                product = self.products_data[idx].copy()
                product['similarity_score'] = float(score)
                similar_products.append(product)

        return similar_products

    def save_index(self):
        """Save FAISS index and products data to disk."""
        if self.index is None:
            raise ValueError("No index to save.")

        index_path = self.db_directory / "faiss_index.bin"
        data_path = self.db_directory / "data.json"

        # Save FAISS index
        faiss.write_index(self.index, str(index_path))

        # Save products data
        with open(data_path, 'w', encoding='utf-8') as f:
            json.dump(self.products_data, f, ensure_ascii=False, indent=2)

        print(f"Index saved to {index_path}")
        print(f"Products data saved to {data_path}")

    def load_index(self):
        """Load FAISS index and products data from disk."""
        index_path = self.db_directory / "faiss_index.bin"
        data_path = self.db_directory / "data.json"

        if not index_path.exists() or not data_path.exists():
            raise FileNotFoundError("Index or data file not found.")

        # Load FAISS index
        self.index = faiss.read_index(str(index_path))

        # Load products data
        with open(data_path, 'r', encoding='utf-8') as f:
            self.products_data = json.load(f)

        # Rebuild id to index mapping
        self.id_to_index = {product['id']: idx for idx, product in enumerate(self.products_data)}

        print(f"Index loaded from {index_path}")
        print(f"Products data loaded from {data_path}")


