import chromadb
from typing import List, Dict, Any
import uuid
import os

PERSISTENT_DB_PATH = "./chroma_db_data"
CHROMA_CLIENT = chromadb.PersistentClient(path=PERSISTENT_DB_PATH)
print(f"INFO: ChromaDB PersistentClient initialized at path: {PERSISTENT_DB_PATH}")

DEFAULT_COLLECTION_NAME = "insightlens_documents"

def get_or_create_collection(collection_name: str = DEFAULT_COLLECTION_NAME):
    try:
        collection = CHROMA_CLIENT.get_collection(name=collection_name)
        print(f"INFO: Using existing ChromaDB collection: '{collection_name}'")
    except Exception as e:
        print(f"INFO: Collection '{collection_name}' not found or error getting it: {e}. Creating new collection.")
        collection = CHROMA_CLIENT.create_collection(name=collection_name)
        print(f"INFO: ChromaDB collection '{collection_name}' created.")
    return collection

def add_documents_to_store(
    collection_name: str,
    chunks: List[str],
    embeddings: List[List[float]],
    metadatas: List[Dict[str, Any]] | None = None,
    doc_ids: List[str] | None = None
):
    if not chunks or not embeddings or len(chunks) != len(embeddings):
        print("ERROR: Chunks and embeddings must be non-empty and of the same length.")
        return

    collection = get_or_create_collection(collection_name)

    if metadatas is None:
        metadatas = [{}] * len(chunks)
    
    if doc_ids is None:
        doc_ids = [str(uuid.uuid4()) for _ in chunks]
    elif len(doc_ids) != len(chunks):
        print("WARNING: doc_ids length mismatch with chunks. Generating new unique IDs.")
        doc_ids = [str(uuid.uuid4()) for _ in chunks]
    
    if len(metadatas) != len(chunks):
        print(f"WARNING: Metadatas length ({len(metadatas)}) mismatch with chunks ({len(chunks)}). Padding with empty metadata.")
        padded_metadatas = metadatas[:]
        while len(padded_metadatas) < len(chunks):
            padded_metadatas.append({})
        metadatas = padded_metadatas[:len(chunks)]

    try:
        collection.add(
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadatas,
            ids=doc_ids
        )
        print(f"INFO: Added/updated {len(chunks)} chunks in collection '{collection_name}'.")
        print(f"INFO: Current count in collection '{collection_name}': {collection.count()}")
    except Exception as e:
        print(f"ERROR: Error adding/updating documents in ChromaDB: {e}")

def query_store(
    collection_name: str,
    query_embedding: List[float],
    top_k: int = 5
) -> List[Dict[str, Any]] | None:
    try:
        collection = get_or_create_collection(collection_name)
        if collection.count() == 0:
            print(f"WARNING: Collection '{collection_name}' is empty. Cannot query.")
            return []
            
    except Exception as e:
        print(f"ERROR: Could not get or create collection '{collection_name}' for query: {e}")
        return None

    try:
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, collection.count()),
            include=['documents', 'metadatas', 'distances']
        )
        
        if not results or not results.get('ids') or not results['ids'][0]:
            print(f"INFO: No results found in collection '{collection_name}' for the query.")
            return []

        processed_results = []
        num_results_retrieved = len(results['ids'][0])

        for i in range(num_results_retrieved):
            doc = results['documents'][0][i] if results.get('documents') and results['documents'][0] else None
            meta = results['metadatas'][0][i] if results.get('metadatas') and results['metadatas'][0] else {}
            dist = results['distances'][0][i] if results.get('distances') and results['distances'][0] else None
            
            if doc is not None :
                processed_results.append({
                    "document": doc,
                    "metadata": meta,
                    "distance": dist,
                })
        
        if not processed_results:
             print(f"INFO: Query returned matches, but processing yielded no valid results (e.g. docs were None).")

        return processed_results

    except Exception as e:
        print(f"ERROR: Error querying ChromaDB collection '{collection_name}': {e}")
        return None

def reset_collection(collection_name: str = DEFAULT_COLLECTION_NAME):
    try:
        print(f"INFO: Attempting to delete collection '{collection_name}'...")
        CHROMA_CLIENT.delete_collection(name=collection_name)
        print(f"INFO: Collection '{collection_name}' deleted successfully.")
    except Exception as e:
        print(f"INFO: Collection '{collection_name}' not found for deletion, or other error during deletion: {e}")
    
def get_collection_count(collection_name: str = DEFAULT_COLLECTION_NAME) -> int:
    try:
        collection = CHROMA_CLIENT.get_collection(name=collection_name)
        return collection.count()
    except:
        return 0