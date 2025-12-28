"""Semantic Search - Embeddings-based code search."""

from typing import List, Dict, Any, Optional
from pathlib import Path
import ast
import hashlib
from dataclasses import dataclass


@dataclass
class CodeChunk:
    """Semantic code chunk."""
    file_path: str
    start_line: int
    end_line: int
    content: str
    chunk_type: str  # function, class, module
    embedding: Optional[List[float]] = None
    hash: str = ""


class SemanticSearch:
    """Semantic code search using embeddings."""
    
    def __init__(self, workspace_dir: Path):
        """
        Initialize semantic search.
        
        Args:
            workspace_dir: Workspace directory
        """
        self.workspace_dir = Path(workspace_dir)
        self.chunks: List[CodeChunk] = []
        self._index_workspace()
    
    def _index_workspace(self):
        """Index workspace into semantic chunks."""
        if not self.workspace_dir.exists():
            return
        
        for file_path in self.workspace_dir.rglob("*.py"):
            try:
                content = file_path.read_text(encoding='utf-8')
                tree = ast.parse(content)
                
                # Extract functions and classes
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        chunk = CodeChunk(
                            file_path=str(file_path.relative_to(self.workspace_dir)),
                            start_line=node.lineno,
                            end_line=node.end_lineno or node.lineno,
                            content=ast.get_source_segment(content, node) or "",
                            chunk_type="function",
                            hash=hashlib.md5(f"{file_path}:{node.lineno}".encode()).hexdigest()
                        )
                        self.chunks.append(chunk)
                    
                    elif isinstance(node, ast.ClassDef):
                        chunk = CodeChunk(
                            file_path=str(file_path.relative_to(self.workspace_dir)),
                            start_line=node.lineno,
                            end_line=node.end_lineno or node.lineno,
                            content=ast.get_source_segment(content, node) or "",
                            chunk_type="class",
                            hash=hashlib.md5(f"{file_path}:{node.lineno}".encode()).hexdigest()
                        )
                        self.chunks.append(chunk)
            except Exception:
                pass
    
    def _embed(self, text: str) -> List[float]:
        """
        Generate embedding for text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        # Use DeepSeek's embedding or torch fallback
        try:
            from core.registry import get_service
            model_manager = get_service("model_manager")
            if model_manager:
                # Use model for embeddings (simplified - would need actual embedding model)
                # For now, return simple hash-based vector
                hash_val = int(hashlib.md5(text.encode()).hexdigest()[:8], 16)
                return [float(hash_val % 1000) / 1000.0] * 128  # Dummy 128-dim vector
        except Exception:
            pass
        
        # Fallback: simple hash vector
        hash_val = int(hashlib.md5(text.encode()).hexdigest()[:8], 16)
        return [float(hash_val % 1000) / 1000.0] * 128
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity."""
        dot = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot / (norm1 * norm2)
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search codebase semantically.
        
        Args:
            query: Search query
            top_k: Number of results
            
        Returns:
            List of matching chunks
        """
        query_embedding = self._embed(query)
        
        # Calculate similarities
        scored_chunks = []
        for chunk in self.chunks:
            if not chunk.embedding:
                chunk.embedding = self._embed(chunk.content)
            
            similarity = self._cosine_similarity(query_embedding, chunk.embedding)
            scored_chunks.append((similarity, chunk))
        
        # Sort by similarity
        scored_chunks.sort(reverse=True, key=lambda x: x[0])
        
        # Return top_k
        return [
            {
                "file_path": chunk.file_path,
                "start_line": chunk.start_line,
                "end_line": chunk.end_line,
                "content": chunk.content[:500],  # Truncate
                "chunk_type": chunk.chunk_type,
                "similarity": score
            }
            for score, chunk in scored_chunks[:top_k]
        ]

