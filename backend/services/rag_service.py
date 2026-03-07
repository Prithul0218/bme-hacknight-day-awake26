"""
RAG (Retrieval-Augmented Generation) Service
Handles document chunking, embedding, and semantic search using Gemini.
"""

import os
import json
from typing import List, Dict, Optional, Tuple
import asyncio
from concurrent.futures import ThreadPoolExecutor
import google.generativeai as genai

# Configure Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

# In-memory storage for embeddings (replace with vector DB later)
# Maps file_id -> list of chunks with embeddings
embeddings_store: Dict[str, List[Dict]] = {}

CHUNK_SIZE = 1000  # Characters per chunk
CHUNK_OVERLAP = 200  # Overlap between chunks for context
TOP_K = 5  # Number of chunks to retrieve


class DocumentChunk:
    """Represents a chunk of text from a document with its embedding."""
    
    def __init__(self, file_id: str, chunk_id: int, text: str, embedding: List[float]):
        self.file_id = file_id
        self.chunk_id = chunk_id
        self.text = text
        self.embedding = embedding
        self.metadata = {
            "file_id": file_id,
            "chunk_id": chunk_id,
            "text_length": len(text),
            "start_char": 0,  # Will be set during chunking
            "end_char": 0,
        }
    
    def to_dict(self) -> dict:
        return {
            "file_id": self.file_id,
            "chunk_id": self.chunk_id,
            "text": self.text,
            "embedding": self.embedding,
            "metadata": self.metadata
        }


class RAGService:
    """Service for semantic search and RAG operations."""
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.embedding_model = "models/embedding-001"
    
    async def chunk_document(self, document_text: str, file_id: str) -> List[DocumentChunk]:
        """
        Split document text into overlapping chunks.
        
        Args:
            document_text: Full text from the document
            file_id: ID of the uploaded file
            
        Returns:
            List of DocumentChunk objects
        """
        chunks = []
        char_count = 0
        chunk_id = 0
        
        # Simple chunking strategy: split on sentences/paragraphs
        # Improved: split on periods while respecting chunk size
        sentences = document_text.replace('\n', ' ').split('. ')
        
        current_chunk = ""
        start_char = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # Add period back if it's not the last sentence
            sentence_with_period = sentence + "." if not sentence.endswith(".") else sentence
            
            # Check if adding this sentence would exceed chunk size
            if len(current_chunk) + len(sentence_with_period) > CHUNK_SIZE:
                # Save current chunk if not empty
                if current_chunk.strip():
                    chunk = DocumentChunk(
                        file_id=file_id,
                        chunk_id=chunk_id,
                        text=current_chunk.strip(),
                        embedding=[]  # Will be set after embedding
                    )
                    chunk.metadata["start_char"] = start_char
                    chunk.metadata["end_char"] = start_char + len(current_chunk)
                    chunks.append(chunk)
                    chunk_id += 1
                
                # Start new chunk with overlap
                overlap_size = min(CHUNK_OVERLAP, len(current_chunk))
                current_chunk = current_chunk[-overlap_size:] + sentence_with_period
                start_char = char_count - overlap_size
            else:
                current_chunk += " " + sentence_with_period if current_chunk else sentence_with_period
            
            char_count += len(sentence_with_period) + 1  # +1 for space
        
        # Add final chunk if not empty
        if current_chunk.strip():
            chunk = DocumentChunk(
                file_id=file_id,
                chunk_id=chunk_id,
                text=current_chunk.strip(),
                embedding=[]
            )
            chunk.metadata["start_char"] = start_char
            chunk.metadata["end_char"] = char_count
            chunks.append(chunk)
        
        print(f"📄 Chunked document into {len(chunks)} chunks (file_id: {file_id})")
        return chunks
    
    async def embed_chunks(self, chunks: List[DocumentChunk]) -> List[DocumentChunk]:
        """
        Embed document chunks using Gemini's embedding model.
        
        Args:
            chunks: List of DocumentChunk objects to embed
            
        Returns:
            List of DocumentChunk objects with embeddings populated
        """
        if not chunks:
            return chunks
        
        # Batch embed using Gemini's embedding API
        try:
            loop = asyncio.get_event_loop()
            embedding_result = await loop.run_in_executor(
                self.executor,
                lambda: genai.embed_content(
                    model=self.embedding_model,
                    content=[chunk.text for chunk in chunks],
                    task_type="RETRIEVAL_DOCUMENT"
                )
            )
            
            # Assign embeddings to chunks
            for chunk, embedding in zip(chunks, embedding_result['embedding']):
                chunk.embedding = embedding
            
            print(f"✨ Embedded {len(chunks)} chunks using Gemini")
            return chunks
            
        except Exception as e:
            print(f"⚠️  Embedding failed: {e}. Continuing without embeddings.")
            # Return chunks without embeddings to allow graceful degradation
            return chunks
    
    async def index_document(self, document_text: str, file_id: str) -> int:
        """
        Process and index a document for semantic search.
        
        Args:
            document_text: Full text from the document
            file_id: ID of the uploaded file
            
        Returns:
            Number of chunks indexed
        """
        # Step 1: Chunk the document
        chunks = await self.chunk_document(document_text, file_id)
        
        if not chunks:
            return 0
        
        # Step 2: Embed chunks
        embedded_chunks = await self.embed_chunks(chunks)
        
        # Step 3: Store in memory
        embeddings_store[file_id] = [chunk.to_dict() for chunk in embedded_chunks]
        
        print(f"🔍 Indexed file {file_id} with {len(embedded_chunks)} chunks")
        return len(embedded_chunks)
    
    def _cosine_similarity(self, vec_a: List[float], vec_b: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        if not vec_a or not vec_b:
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
        magnitude_a = sum(a ** 2 for a in vec_a) ** 0.5
        magnitude_b = sum(b ** 2 for b in vec_b) ** 0.5
        
        if magnitude_a == 0 or magnitude_b == 0:
            return 0.0
        
        return dot_product / (magnitude_a * magnitude_b)
    
    async def search_with_metadata(self, file_id: str, query: str, top_k: int = TOP_K) -> List[Dict]:
        """
        Retrieve relevant chunks with full metadata for citation tracking.
        
        Args:
            file_id: ID of the file to search in
            query: User's question/search query
            top_k: Number of top chunks to return
            
        Returns:
            List of chunk dictionaries with metadata and similarity scores
        """
        if file_id not in embeddings_store:
            return []
        
        chunks = embeddings_store[file_id]
        
        if not chunks or not chunks[0].get('embedding'):
            # Fallback: return first few chunks without semantic search
            print(f"⚠️  No embeddings found for {file_id}, returning first chunks")
            results = []
            for chunk in chunks[:top_k]:
                chunk_copy = chunk.copy()
                chunk_copy['similarity'] = 0.5
                results.append(chunk_copy)
            return results
        
        try:
            # Embed the query
            loop = asyncio.get_event_loop()
            query_embedding_result = await loop.run_in_executor(
                self.executor,
                lambda: genai.embed_content(
                    model=self.embedding_model,
                    content=query,
                    task_type="RETRIEVAL_QUERY"
                )
            )
            
            query_embedding = query_embedding_result['embedding']
            
            # Score all chunks
            scored_chunks = []
            for chunk in chunks:
                similarity = self._cosine_similarity(
                    query_embedding,
                    chunk.get('embedding', [])
                )
                chunk_with_score = chunk.copy()
                chunk_with_score['similarity'] = similarity
                scored_chunks.append(chunk_with_score)
            
            # Sort by similarity and return top-k
            scored_chunks.sort(key=lambda x: x['similarity'], reverse=True)
            results = scored_chunks[:top_k]
            
            print(f"🔎 Found {len(results)} relevant chunks with metadata (top-k={top_k})")
            return results
            
        except Exception as e:
            print(f"⚠️  Search failed: {e}")
            results = []
            for chunk in chunks[:top_k]:
                chunk_copy = chunk.copy()
                chunk_copy['similarity'] = 0.5
                results.append(chunk_copy)
            return results
    
    async def search(self, file_id: str, query: str, top_k: int = TOP_K) -> List[Tuple[str, float]]:
        """
        Retrieve relevant chunks for a query using semantic search.
        (Legacy method for backwards compatibility - use search_with_metadata for citations)
        
        Args:
            file_id: ID of the file to search in
            query: User's question/search query
            top_k: Number of top chunks to return
            
        Returns:
            List of (chunk_text, similarity_score) tuples, sorted by relevance
        """
        chunks_with_metadata = await self.search_with_metadata(file_id, query, top_k)
        return [(chunk['text'], chunk['similarity']) for chunk in chunks_with_metadata]
    
    async def get_context_with_citations(self, file_id: str, query: str) -> Tuple[str, List[Dict]]:
        """
        Get relevant context for a query WITH citation metadata.
        
        Args:
            file_id: ID of the file
            query: User's question
            
        Returns:
            Tuple of (formatted_context_string, list_of_chunk_metadata)
        """
        results = await self.search_with_metadata(file_id, query, top_k=TOP_K)
        
        if not results:
            return "No relevant context found.", []
        
        # Format context with source markers
        context_parts = []
        citation_metadata = []
        
        for i, chunk in enumerate(results, 1):
            similarity = chunk.get('similarity', 0)
            confidence = f"{similarity:.1%}" if similarity > 0 else "N/A"
            context_parts.append(f"[Source {i} - Relevance: {confidence}]\n{chunk['text']}\n")
            
            # Store citation metadata
            citation_metadata.append({
                'citation_id': i,
                'file_id': chunk['file_id'],
                'chunk_id': chunk['chunk_id'],
                'start_char': chunk['metadata'].get('start_char', 0),
                'end_char': chunk['metadata'].get('end_char', 0),
                'text': chunk['text'],
                'similarity': similarity
            })
        
        context = "\n".join(context_parts)
        return context, citation_metadata
    
    async def get_context_for_query(self, file_id: str, query: str) -> str:
        """
        Get relevant context for a query to use in prompts.
        (Legacy method for backwards compatibility - use get_context_with_citations for citation support)
        
        Args:
            file_id: ID of the file
            query: User's question
            
        Returns:
            Formatted context string from retrieved chunks
        """
        context, _ = await self.get_context_with_citations(file_id, query)
        return context
    
    def clear_index(self, file_id: str):
        """Remove indexed data for a file."""
        if file_id in embeddings_store:
            del embeddings_store[file_id]
            print(f"Cleared index for {file_id}")


# Global RAG service instance
rag_service = RAGService()
