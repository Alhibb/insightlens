import google.generativeai as genai
from typing import List, Dict, Any

GENERATION_MODEL_NAME = "gemini-2.0-flash" 

def construct_rag_prompt(query: str, context_chunks: List[Dict[str, Any]], persona: str | None = None) -> str:
    context_str = "\n\n---\n\n".join([chunk['document'] for chunk in context_chunks])
    persona_instruction = ""
    if persona:
        persona_instruction = f"Please answer from the perspective of {persona}. "

    prompt = f"""You are InsightLens, an expert AI assistant. Your task is to answer the user's question based *solely* on the provided context.
If the information to answer the question is not present in the context, clearly state that you cannot answer based on the provided information.
Do not make up information or answer from your general knowledge if it's not supported by the context.
{persona_instruction}Be concise and directly answer the question.

Provided Context:
---
{context_str}
---

User Question: {query}

Answer:
"""
    return prompt

def generate_answer_with_gemini(prompt: str) -> str | None:
    try:
        model = genai.GenerativeModel(GENERATION_MODEL_NAME)
        response = model.generate_content(prompt)
        
        if not response.candidates or not response.candidates[0].content.parts:
            block_reason = "Unknown reason"
            if response.prompt_feedback and response.prompt_feedback.block_reason:
                block_reason = response.prompt_feedback.block_reason.name
            return f"The response was blocked by the safety filter. Reason: {block_reason}. Try rephrasing your query or adjusting the content."

        return response.text
    except Exception as e:
        print(f"Error during Gemini generation: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"API Error Details: {e.response}")
        return None