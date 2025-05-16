import os
from typing import List, Dict, Any
from dotenv import load_dotenv

# OpenAI and LangChain components
import openai
from langchain.embeddings.openai import OpenAIEmbeddings

# Local imports
from .database import semantic_search

# Load environment variables
load_dotenv()

# Set OpenAI API key in environment
openai.api_key = os.getenv("OPENAI_API_KEY", "")
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "")
# Initialize with minimal parameters for older version
embeddings = OpenAIEmbeddings()

def generate_query_embedding(query: str) -> List[float]:
    """
    Generate embedding for a query string.
    
    Args:
        query: Question or query text
        
    Returns:
        Embedding vector
    """
    return embeddings.embed_query(query)

def retrieve_relevant_chunks(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Retrieve the most relevant chunks for a query.
    
    Args:
        query: Question or query text
        top_k: Number of chunks to retrieve
        
    Returns:
        List of relevant document chunks
    """
    # Generate query embedding
    query_embedding = generate_query_embedding(query)
    
    # Retrieve similar chunks
    chunks = semantic_search(query_embedding, limit=top_k)
    
    # Format results
    results = []
    for chunk in chunks:
        results.append({
            "text": chunk.text,
            "document_id": chunk.document_id,
            "page_number": chunk.page_number,
            "chunk_index": chunk.chunk_index
        })
    
    return results

def format_context(chunks: List[Dict[str, Any]]) -> str:
    """
    Format retrieved chunks into a context string for the LLM.
    
    Args:
        chunks: List of retrieved document chunks
        
    Returns:
        Formatted context string
    """
    context_parts = []
    
    for i, chunk in enumerate(chunks):
        context_parts.append(
            f"[Document {chunk['document_id']}, Page {chunk['page_number']}, Chunk {chunk['chunk_index']}]\n"
            f"{chunk['text']}\n"
        )
    
    return "\n\n".join(context_parts)

def generate_answer(query: str, chunks: List[Dict[str, Any]]) -> str:
    """
    Generate an answer to the query using retrieved chunks as context.
    
    Args:
        query: Question or query text
        chunks: List of retrieved document chunks
        
    Returns:
        Generated answer
    """
    # Format context from chunks
    context = format_context(chunks)
    
    # Create system prompt
    system_prompt = """You are a helpful assistant that answers questions based on the provided document context.
Your answers should:
1. Be directly based on the context information
2. Be comprehensive and detailed
3. Include specific references to document numbers and pages where appropriate
4. Say "I don't know" when the context doesn't contain the answer

Respond to the user's question based ONLY on the provided context."""
    
    # Call OpenAI API with older version
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"}
        ],
        temperature=0.2,
        max_tokens=1000
    )
    
    return response.choices[0].message.content

def answer_query(query: str) -> Dict[str, Any]:
    """
    Answer a query using the RAG pipeline.
    
    Args:
        query: Question or query text
        
    Returns:
        Dictionary with answer and source information
    """
    # Retrieve relevant chunks
    chunks = retrieve_relevant_chunks(query)
    
    # Generate answer
    if not chunks:
        answer = "I couldn't find any relevant information in the documents to answer your question."
    else:
        answer = generate_answer(query, chunks)
    
    # Format sources
    sources = []
    for chunk in chunks:
        sources.append({
            "document_id": chunk["document_id"],
            "page_number": chunk["page_number"],
            "text_snippet": chunk["text"][:200] + "..." if len(chunk["text"]) > 200 else chunk["text"]
        })
    
    return {
        "answer": answer,
        "sources": sources
    } 