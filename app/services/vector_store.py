"""
Vector store service for managing document embeddings and retrieval.
"""
from typing import List, Optional, Tuple
from pathlib import Path
import time

from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.schema import Document

from config import settings, logger


class VectorStoreService:
    """Service for managing vector store operations."""
    
    def __init__(self):
        """Initialize the vector store service."""
        self.embeddings = OllamaEmbeddings(
            model=settings.embedding_model,
            base_url=settings.ollama_base_url
        )
        self.vectorstore: Optional[Chroma] = None
        self._initialize()
    
    def _initialize(self) -> None:
        """Initialize or load existing vector store."""
        try:
            if self._store_exists():
                logger.info(f"Loading existing vector store from {settings.vector_store_dir}")
                self.vectorstore = Chroma(
                    persist_directory=str(settings.vector_store_dir),
                    embedding_function=self.embeddings,
                    collection_name=settings.collection_name
                )
                count = self.vectorstore._collection.count()
                logger.info(f"Vector store loaded with {count} embeddings")
            else:
                logger.info("No existing vector store found")
        except Exception as e:
            logger.error(f"Error initializing vector store: {e}")
            self.vectorstore = None
    
    def _store_exists(self) -> bool:
        """Check if vector store exists."""
        return settings.vector_store_dir.exists() and any(settings.vector_store_dir.iterdir())
    
    def ingest_pdfs(
        self,
        pdf_directory: Optional[Path] = None,
        overwrite: bool = False
    ) -> Tuple[int, int, List[str]]:
        """
        Ingest PDF documents into the vector store.
        
        Args:
            pdf_directory: Directory containing PDFs (defaults to settings.data_dir)
            overwrite: Whether to overwrite existing collection
        
        Returns:
            Tuple of (num_documents, num_chunks, filenames)
        """
        start_time = time.time()
        pdf_dir = pdf_directory or settings.data_dir
        
        logger.info(f"Loading documents from '{pdf_dir}'...")
        loader = PyPDFDirectoryLoader(str(pdf_dir))
        docs = loader.load()
        
        if not docs:
            logger.warning("No PDF documents found")
            return 0, 0, []
        
        logger.info(f"Loaded {len(docs)} document(s)")
        filenames = list(set([Path(doc.metadata.get('source', '')).name for doc in docs]))
        
        # Split documents
        logger.info("Splitting documents into chunks...")
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap
        )
        splits = text_splitter.split_documents(docs)
        logger.info(f"Created {len(splits)} text chunks")
        
        # Create or update vector store
        if overwrite or not self._store_exists():
            logger.info("Creating new vector store...")
            self.vectorstore = Chroma.from_documents(
                documents=splits,
                embedding=self.embeddings,
                collection_name=settings.collection_name,
                persist_directory=str(settings.vector_store_dir)
            )
        else:
            logger.info("Adding documents to existing vector store...")
            if self.vectorstore is None:
                self._initialize()
            self.vectorstore.add_documents(splits)
        
        duration = time.time() - start_time
        count = self.vectorstore._collection.count()
        logger.info(f"✅ Ingestion complete in {duration:.2f}s. Total embeddings: {count}")
        
        return len(docs), len(splits), filenames
    
    def search(self, query: str, k: Optional[int] = None) -> List[Document]:
        """
        Perform similarity search.
        
        Args:
            query: Search query
            k: Number of results (defaults to settings.retrieval_k)
        
        Returns:
            List of relevant documents
        """
        if self.vectorstore is None:
            logger.warning("Vector store not initialized")
            return []
        
        k = k or settings.retrieval_k
        
        try:
            results = self.vectorstore.similarity_search(query, k=k)
            logger.debug(f"Retrieved {len(results)} documents for query: '{query}'")
            return results
        except Exception as e:
            logger.error(f"Error during similarity search: {e}")
            return []
    
    def get_retriever(self, k: Optional[int] = None):
        """
        Get a retriever instance.
        
        Args:
            k: Number of results
        
        Returns:
            LangChain retriever
        """
        if self.vectorstore is None:
            raise ValueError("Vector store not initialized. Run ingestion first.")
        
        k = k or settings.retrieval_k
        return self.vectorstore.as_retriever(search_kwargs={"k": k})
    
    def get_stats(self) -> dict:
        """Get vector store statistics."""
        if self.vectorstore is None:
            return {
                "status": "not_initialized",
                "count": 0,
                "collection": settings.collection_name
            }
        
        try:
            count = self.vectorstore._collection.count()
            return {
                "status": "ready",
                "count": count,
                "collection": settings.collection_name,
                "embedding_model": settings.embedding_model
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {"status": "error", "error": str(e)}
    
    def clear(self) -> bool:
        """Clear all documents from the collection."""
        try:
            if self.vectorstore:
                self.vectorstore._collection.delete()
                logger.info("Collection cleared")
            self._initialize()
            return True
        except Exception as e:
            logger.error(f"Error clearing collection: {e}")
            return False
