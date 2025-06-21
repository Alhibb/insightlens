import re

def simple_chunker(text: str, chunk_size: int = 1000, chunk_overlap: int = 150) -> list[str]:
    if not text:
        return []

    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    
    all_chunks = []
    current_chunk = ""

    for paragraph in paragraphs:
        if len(current_chunk) + len(paragraph) + 1 < chunk_size:
            current_chunk += (" " if current_chunk else "") + paragraph
        else:
            if current_chunk:
                if len(current_chunk) > chunk_size:
                    for i in range(0, len(current_chunk), chunk_size - chunk_overlap):
                        all_chunks.append(current_chunk[i:i + chunk_size])
                else:
                    all_chunks.append(current_chunk)
                current_chunk = paragraph
            else:
                current_chunk = paragraph

            if len(current_chunk) > chunk_size:
                for i in range(0, len(current_chunk), chunk_size - chunk_overlap):
                    all_chunks.append(current_chunk[i:i + chunk_size])
                current_chunk = "" 

    if current_chunk:
        if len(current_chunk) > chunk_size:
            for i in range(0, len(current_chunk), chunk_size - chunk_overlap):
                all_chunks.append(current_chunk[i:i + chunk_size])
        else:
            all_chunks.append(current_chunk)
            
    return [chunk for chunk in all_chunks if chunk.strip()]