import typer
from typing_extensions import Annotated
import os
import time

from utils import load_api_key
from document_loader import load_document
from text_chunker import simple_chunker
from embedding_generator import get_embeddings, EMBEDDING_MODEL_NAME
from vector_store_manager import (
    add_documents_to_store,
    query_store,
    reset_collection as reset_db_collection,
    DEFAULT_COLLECTION_NAME
)
from rag_core import construct_rag_prompt, generate_answer_with_gemini

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

try:
    from docx import Document as DocxCreator
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False


APP_STATE = {
    "api_key_loaded": False,
    "current_collection": DEFAULT_COLLECTION_NAME,
    "last_loaded_doc_path": None,
    "chunk_size": 1000,
    "chunk_overlap": 150,
    "top_k_retrieval": 3
}

app = typer.Typer(help="InsightLens: Query your documents with AI.")

def ensure_api_key():
    if not APP_STATE["api_key_loaded"]:
        try:
            load_api_key()
            APP_STATE["api_key_loaded"] = True
            typer.echo("Gemini API key loaded and configured.", color=typer.colors.GREEN)
        except ValueError as e:
            typer.secho(f"API Key Error: {e}", fg=typer.colors.RED, err=True)
            typer.secho("Please ensure your GEMINI_API_KEY is set in a .env file or as an environment variable.", fg=typer.colors.YELLOW, err=True)
            raise typer.Exit(code=1)

@app.command()
def load(
    filepath: Annotated[str, typer.Argument(help="Path to the document (PDF, DOCX, TXT).")],
    collection_name: Annotated[str, typer.Option(help="Name of the ChromaDB collection to use.")] = DEFAULT_COLLECTION_NAME,
    force_reload: Annotated[bool, typer.Option("--force-reload", "-f", help="Force reloading and re-embedding if collection already exists with this document name.")] = False
):
    ensure_api_key()
    APP_STATE["current_collection"] = collection_name
    raw_text = load_document(filepath)
    if not raw_text:
        typer.secho(f"Failed to load document: {filepath}", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    
    APP_STATE["last_loaded_doc_path"] = filepath
    filename = os.path.basename(filepath)
    typer.echo(f"Document '{filename}' loaded successfully. ({len(raw_text)} characters)")

    chunks = simple_chunker(raw_text, chunk_size=APP_STATE["chunk_size"], chunk_overlap=APP_STATE["chunk_overlap"])
    if not chunks:
        typer.secho("Failed to chunk document or document is empty.", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    typer.echo(f"Document split into {len(chunks)} chunks.")

    embeddings = get_embeddings(chunks, task_type="RETRIEVAL_DOCUMENT")
    if not embeddings:
        typer.secho("Failed to generate embeddings for chunks.", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    typer.echo(f"Generated {len(embeddings)} embeddings using model '{EMBEDDING_MODEL_NAME}'.")

    metadatas = [{"source_document": filename, "chunk_index": i} for i in range(len(chunks))]
    chunk_ids = [f"{filename}_{i}" for i in range(len(chunks))]

    add_documents_to_store(
        collection_name=collection_name,
        chunks=chunks,
        embeddings=embeddings,
        metadatas=metadatas,
        doc_ids=chunk_ids
    )
    typer.secho(f"Document '{filename}' processed and stored in collection '{collection_name}'.", fg=typer.colors.GREEN)

@app.command()
def ask(
    query: Annotated[str, typer.Argument(help="Your question about the loaded document(s).")],
    collection_name: Annotated[str, typer.Option(help="Name of the ChromaDB collection to query.")] = DEFAULT_COLLECTION_NAME,
    persona: Annotated[str, typer.Option(help="Optional persona for the AI (e.g., 'a domain expert', 'a curious child').")] = None,
    top_k: Annotated[int, typer.Option(help="Number of relevant chunks to retrieve.")] = None
):
    ensure_api_key()
    if top_k is None:
        top_k = APP_STATE["top_k_retrieval"]
    APP_STATE["current_collection"] = collection_name

    typer.echo(f"Embedding your query using '{EMBEDDING_MODEL_NAME}'...")
    query_embedding_list = get_embeddings([query], task_type="RETRIEVAL_QUERY")
    
    if not query_embedding_list or not query_embedding_list[0]:
        typer.secho("Failed to generate embedding for your query.", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    query_embedding = query_embedding_list[0]
    typer.echo("Query embedded successfully.")

    typer.echo(f"Retrieving top {top_k} relevant context chunks from collection '{collection_name}'...")
    context_chunks = query_store(collection_name, query_embedding, top_k=top_k)

    if not context_chunks:
        typer.secho(f"No relevant context found in collection '{collection_name}' for your query.", fg=typer.colors.YELLOW)
        typer.secho("Consider loading relevant documents or refining your query.", fg=typer.colors.YELLOW)
        return

    typer.echo(f"Retrieved {len(context_chunks)} context chunks. Constructing prompt for Gemini...")
    prompt = construct_rag_prompt(query, context_chunks, persona=persona)
    
    typer.echo("Asking Gemini...")
    answer = generate_answer_with_gemini(prompt)

    if answer:
        typer.echo("\n🤖 InsightLens says:")
        typer.secho(answer, fg=typer.colors.CYAN)
    else:
        typer.secho("InsightLens could not generate an answer. There might have been an API issue or the content was filtered.", fg=typer.colors.RED)

@app.command()
def summarize_doc(
    filepath: Annotated[str, typer.Argument(help="Path to the document to summarize.")],
    output_format: Annotated[str, typer.Option(help="Output format: 'text', 'pdf', 'docx'. Default is 'text'.")] = "text",
    max_chunks_to_summarize: Annotated[int, typer.Option(help="Max document chunks to process for summarization (0 for all).")] = 0,
    chunk_summary_batch_size: Annotated[int, typer.Option(help="How many chunk summaries to combine for final summary prompt.")] = 5
):
    ensure_api_key()
    
    filename = os.path.basename(filepath)
    typer.echo(f"Initiating summarization for: {filename}")

    raw_text = load_document(filepath)
    if not raw_text:
        typer.secho(f"Failed to load document: {filepath}", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    
    full_doc_chunks = simple_chunker(raw_text, chunk_size=APP_STATE["chunk_size"], chunk_overlap=APP_STATE["chunk_overlap"])
    if not full_doc_chunks:
        typer.secho("Failed to chunk document or document is empty.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    if max_chunks_to_summarize > 0:
        full_doc_chunks = full_doc_chunks[:max_chunks_to_summarize]
    
    typer.echo(f"Processing {len(full_doc_chunks)} chunks for initial summarization...")

    chunk_summaries = []
    for i, chunk_text in enumerate(full_doc_chunks):
        prompt = f"Please provide a concise summary of the following text excerpt from a larger document:\n\n---\n{chunk_text}\n---\n\nSummary:"
        typer.echo(f"  Summarizing chunk {i+1}/{len(full_doc_chunks)}...")
        summary_part = generate_answer_with_gemini(prompt)
        if summary_part:
            chunk_summaries.append(summary_part)
        else:
            typer.echo(f"  Skipping chunk {i+1} due to summarization error.")
        if len(full_doc_chunks) > 10 and i < len(full_doc_chunks) -1 :
             time.sleep(0.5)

    if not chunk_summaries:
        typer.secho("No chunk summaries were generated. Cannot create final summary.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    typer.echo(f"Generated {len(chunk_summaries)} chunk summaries. Combining them for the final summary...")
    combined_chunk_summaries_text = "\n\n---\n\n".join(chunk_summaries)
    
    final_summary_prompt = f"""The following are summaries of consecutive sections from a document titled '{filename}'.
Please synthesize these into a single, coherent, and comprehensive overall summary of the entire document.
Ensure the final summary flows well and captures the main points effectively.

Section Summaries:
---
{combined_chunk_summaries_text}
---

Comprehensive Overall Summary of '{filename}':
"""
    
    final_summary = generate_answer_with_gemini(final_summary_prompt)

    if not final_summary:
        typer.secho("Failed to generate the final comprehensive summary.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    typer.echo("\n--- Generated Document Summary ---")
    typer.secho(final_summary, fg=typer.colors.BLUE)

    if output_format != "text":
        output_filename_base = os.path.splitext(filename)[0] + "_summary"
        if output_format == "pdf":
            if not REPORTLAB_AVAILABLE:
                typer.secho("ReportLab library not found. Cannot create PDF. Please install it: pip install reportlab", fg=typer.colors.RED)
                raise typer.Exit(code=1)
            pdf_filename = f"{output_filename_base}.pdf"
            doc = SimpleDocTemplate(pdf_filename, pagesize=letter)
            styles = getSampleStyleSheet()
            story = []
            story.append(Paragraph(f"Summary of: {filename}", styles['h1']))
            story.append(Spacer(1, 12))
            for para_text in final_summary.split('\n\n'):
                if para_text.strip():
                    story.append(Paragraph(para_text.strip(), styles['Normal']))
                    story.append(Spacer(1, 6))
            try:
                doc.build(story)
                typer.echo(f"\nSummary saved to: {pdf_filename}", fg=typer.colors.GREEN)
            except Exception as e:
                typer.secho(f"Error saving PDF: {e}", fg=typer.colors.RED)

        elif output_format == "docx":
            if not DOCX_AVAILABLE:
                typer.secho("python-docx library not found. Cannot create DOCX. Please install it: pip install python-docx", fg=typer.colors.RED)
                raise typer.Exit(code=1)
            docx_filename = f"{output_filename_base}.docx"
            doc_creator_instance = DocxCreator()
            doc_creator_instance.add_heading(f"Summary of: {filename}", level=1)
            for para_text in final_summary.split('\n\n'):
                if para_text.strip():
                    doc_creator_instance.add_paragraph(para_text.strip())
            try:
                doc_creator_instance.save(docx_filename)
                typer.echo(f"\nSummary saved to: {docx_filename}", fg=typer.colors.GREEN)
            except Exception as e:
                typer.secho(f"Error saving DOCX: {e}", fg=typer.colors.RED)

@app.command()
def configure(
    chunk_size: Annotated[int, typer.Option(help="Character size for text chunks.")] = None,
    chunk_overlap: Annotated[int, typer.Option(help="Character overlap between chunks.")] = None,
    top_k: Annotated[int, typer.Option(help="Number of chunks to retrieve for context.")] = None
):
    if chunk_size is not None:
        APP_STATE["chunk_size"] = chunk_size
        typer.echo(f"Chunk size set to: {chunk_size}")
    if chunk_overlap is not None:
        APP_STATE["chunk_overlap"] = chunk_overlap
        typer.echo(f"Chunk overlap set to: {chunk_overlap}")
    if top_k is not None:
        APP_STATE["top_k_retrieval"] = top_k
        typer.echo(f"Top-K retrieval set to: {top_k}")
    
    if not any([chunk_size, chunk_overlap, top_k]):
        typer.echo("Current configuration:")
        typer.echo(f"  Chunk Size: {APP_STATE['chunk_size']}")
        typer.echo(f"  Chunk Overlap: {APP_STATE['chunk_overlap']}")
        typer.echo(f"  Top-K Retrieval: {APP_STATE['top_k_retrieval']}")
        typer.echo("Use options to set new values.")

@app.command()
def reset_collection(
    collection_name: Annotated[str, typer.Argument(help="Name of the ChromaDB collection to reset (delete and recreate).")],
    confirm: Annotated[bool, typer.Option(prompt="Are you sure you want to delete all data in this collection?", help="Confirm deletion.")] = False
):
    ensure_api_key()
    if not confirm:
        typer.echo("Reset cancelled.", fg=typer.colors.YELLOW)
        raise typer.Exit(code=1)
    
    reset_db_collection(collection_name)
    typer.secho(f"Collection '{collection_name}' has been reset.", fg=typer.colors.GREEN)

if __name__ == "__main__":
    app()