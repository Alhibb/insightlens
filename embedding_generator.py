import google.generativeai as genai
from typing import List
import time

EMBEDDING_MODEL_NAME = "models/embedding-001" 

def get_embeddings(texts: List[str], task_type: str = "RETRIEVAL_DOCUMENT") -> List[List[float]] | None:
    if not texts:
        return []
    
    all_embeddings = []
    BATCH_SIZE = 100 
    for i in range(0, len(texts), BATCH_SIZE):
        batch_texts = texts[i:i + BATCH_SIZE]
        try:
            print(f"Generating embeddings for batch {i//BATCH_SIZE + 1} ({len(batch_texts)} texts)...")
            result = genai.embed_content(
                model=EMBEDDING_MODEL_NAME,
                content=batch_texts,
                task_type=task_type
            )
            all_embeddings.extend(result['embedding'])
            if len(texts) > BATCH_SIZE and i + BATCH_SIZE < len(texts):
                 time.sleep(1) 
        except Exception as e:
            print(f"Error generating embeddings for a batch: {e}")
            return None 
            
    return all_embeddings