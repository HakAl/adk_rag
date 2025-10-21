"""
Vector store service for managing document embeddings and retrieval.
"""
from typing import List, Optional, Tuple, Dict, Any
from pathlib import Path
import time
import json

from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFDirectoryLoader, CSVLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from config import settings, logger
from app.core.providers import ProviderFactory


class VectorStoreService:
    """Service for managing vector store operations."""

    def __init__(self, provider_type: Optional[str] = None):
        """
        Initialize the vector store service.

        Args:
            provider_type: Provider type override (defaults to settings.provider_type)
        """
        provider_type = provider_type or settings.provider_type

        # Create provider based on type
        if provider_type == 'ollama':
            self.provider = ProviderFactory.create_provider(
                'ollama',
                embedding_model=settings.embedding_model,
                chat_model=settings.chat_model,
                base_url=settings.ollama_base_url,
                debug=settings.debug
            )
        elif provider_type == 'llamacpp':
            if not settings.llamacpp_embedding_model_path:
                raise ValueError("LLAMACPP_EMBEDDING_MODEL_PATH not configured")

            self.provider = ProviderFactory.create_provider(
                'llamacpp',
                embedding_model_path=settings.llamacpp_embedding_model_path,
                chat_model_path=settings.llamacpp_chat_model_path or settings.llamacpp_embedding_model_path,
                n_ctx=settings.llamacpp_n_ctx,
                n_batch=settings.llamacpp_n_batch,
                n_threads=settings.llamacpp_n_threads,
                temperature=settings.llamacpp_temperature,
                max_tokens=settings.llamacpp_max_tokens,
                verbose=settings.debug
            )
        else:
            raise ValueError(f"Unsupported provider type: {provider_type}")

        # Get embeddings from provider
        self.embeddings = self.provider.get_embedding_provider().get_embeddings()
        self.vectorstore: Optional[Chroma] = None
        self._initialize()

    def _get_collection_metadata(self) -> Dict[str, Any]:
        """
        Get optimized collection metadata for ChromaDB.

        Returns:
            Dictionary with HNSW index configuration
        """
        return {
            "hnsw:space": settings.chroma_hnsw_space,
            "hnsw:construction_ef": settings.chroma_hnsw_construction_ef,
            "hnsw:search_ef": settings.chroma_hnsw_search_ef,
            "hnsw:M": settings.chroma_hnsw_m,
        }

    def _initialize(self) -> None:
        """Initialize or load existing vector store."""
        try:
            if self._store_exists():
                logger.info(f"Loading existing vector store from {settings.vector_store_dir}")
                self.vectorstore = Chroma(
                    persist_directory=str(settings.vector_store_dir),
                    embedding_function=self.embeddings,
                    collection_name=settings.collection_name,
                    collection_metadata=self._get_collection_metadata()
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

    def _load_csv_files(self, directory: Path) -> List[Document]:
        """
        Load CSV files from a directory.

        Args:
            directory: Directory containing CSV files

        Returns:
            List of Document objects
        """
        docs = []
        csv_files = list(directory.glob("*.csv"))

        if not csv_files:
            return docs

        logger.info(f"Found {len(csv_files)} CSV file(s)")

        for csv_file in csv_files:
            try:
                loader = CSVLoader(str(csv_file), encoding='utf-8')
                file_docs = loader.load()
                logger.info(f"Loaded {len(file_docs)} rows from {csv_file.name}")
                docs.extend(file_docs)
            except Exception as e:
                logger.error(f"Error loading CSV file {csv_file.name}: {e}")

        return docs

    def _load_jsonl_files(self, directory: Path) -> List[Document]:
        """
        Load JSONL (JSON Lines) files from a directory.

        Args:
            directory: Directory containing JSONL files

        Returns:
            List of Document objects
        """
        docs = []
        jsonl_files = list(directory.glob("*.jsonl"))

        if not jsonl_files:
            return docs

        logger.info(f"Found {len(jsonl_files)} JSONL file(s)")

        for jsonl_file in jsonl_files:
            try:
                with open(jsonl_file, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        line = line.strip()
                        if not line:
                            continue

                        try:
                            data = json.loads(line)
                            text = self._extract_text_from_json(data)

                            if text:
                                doc = Document(
                                    page_content=text,
                                    metadata={
                                        'source': str(jsonl_file),
                                        'line': line_num,
                                        'format': 'jsonl'
                                    }
                                )
                                docs.append(doc)
                        except json.JSONDecodeError as e:
                            logger.warning(f"Invalid JSON at line {line_num} in {jsonl_file.name}: {e}")
                            continue

                logger.info(f"Loaded {len(docs)} entries from {jsonl_file.name}")
            except Exception as e:
                logger.error(f"Error loading JSONL file {jsonl_file.name}: {e}")

        return docs

    def _extract_text_from_json(self, data: dict) -> str:
        """
        Extract text content from JSON data.
        Checks common field names and concatenates multiple fields if needed.

        Args:
            data: JSON data as dictionary

        Returns:
            Extracted text content
        """
        text_fields = ['text', 'content', 'body', 'message', 'description', 'summary']

        for field in text_fields:
            if field in data and isinstance(data[field], str):
                return data[field]

        text_parts = []
        for key, value in data.items():
            if isinstance(value, str) and value.strip():
                text_parts.append(f"{key}: {value}")
            elif isinstance(value, (list, dict)):
                text_parts.append(f"{key}: {json.dumps(value)}")

        return "\n".join(text_parts)

    def _load_pdf_files(self, directory: Path) -> List[Document]:
        """
        Load PDF files from a directory.

        Args:
            directory: Directory containing PDF files

        Returns:
            List of Document objects
        """
        loader = PyPDFDirectoryLoader(str(directory))
        docs = loader.load()

        if docs:
            logger.info(f"Loaded {len(docs)} PDF document(s)")

        return docs

    def ingest_documents(
        self,
        directory: Optional[Path] = None,
        file_types: Optional[List[str]] = None,
        overwrite: bool = False
    ) -> Tuple[int, int, List[str]]:
        """
        Ingest documents (PDF, CSV, JSONL) into the vector store.

        Args:
            directory: Directory containing documents (defaults to settings.data_dir)
            file_types: List of file types to ingest (e.g., ['pdf', 'csv', 'jsonl'])
                       If None, ingests all supported types
            overwrite: Whether to overwrite existing collection

        Returns:
            Tuple of (num_documents, num_chunks, filenames)
        """
        start_time = time.time()
        data_dir = directory or settings.data_dir

        if file_types is None:
            file_types = ['pdf', 'csv', 'jsonl']

        logger.info(f"Loading documents from '{data_dir}'...")
        logger.info(f"File types: {', '.join(file_types)}")

        all_docs = []
        filenames = []

        if 'pdf' in file_types:
            pdf_docs = self._load_pdf_files(data_dir)
            all_docs.extend(pdf_docs)
            if pdf_docs:
                pdf_files = list(set([Path(doc.metadata.get('source', '')).name for doc in pdf_docs]))
                filenames.extend(pdf_files)

        if 'csv' in file_types:
            csv_docs = self._load_csv_files(data_dir)
            all_docs.extend(csv_docs)
            if csv_docs:
                csv_files = list(set([Path(doc.metadata.get('source', '')).name for doc in csv_docs]))
                filenames.extend(csv_files)

        if 'jsonl' in file_types:
            jsonl_docs = self._load_jsonl_files(data_dir)
            all_docs.extend(jsonl_docs)
            if jsonl_docs:
                jsonl_files = list(set([Path(doc.metadata.get('source', '')).name for doc in jsonl_docs]))
                filenames.extend(jsonl_files)

        if not all_docs:
            logger.warning("No documents found to ingest")
            return 0, 0, []

        logger.info(f"Loaded {len(all_docs)} total document(s)")

        logger.info("Splitting documents into chunks...")
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap
        )
        splits = text_splitter.split_documents(all_docs)
        logger.info(f"Created {len(splits)} text chunks")

        if overwrite or not self._store_exists():
            logger.info("Creating new vector store with optimized index settings...")
            self.vectorstore = Chroma.from_documents(
                documents=splits,
                embedding=self.embeddings,
                collection_name=settings.collection_name,
                persist_directory=str(settings.vector_store_dir),
                collection_metadata=self._get_collection_metadata()
            )
        else:
            logger.info("Adding documents to existing vector store...")
            if self.vectorstore is None:
                self._initialize()
            self.vectorstore.add_documents(splits)

        duration = time.time() - start_time
        count = self.vectorstore._collection.count()
        logger.info(f"✅ Ingestion complete in {duration:.2f}s. Total embeddings: {count}")

        return len(all_docs), len(splits), filenames

    def ingest_pdfs(
        self,
        pdf_directory: Optional[Path] = None,
        overwrite: bool = False
    ) -> Tuple[int, int, List[str]]:
        """
        Ingest PDF documents into the vector store.
        (Maintained for backward compatibility)

        Args:
            pdf_directory: Directory containing PDFs (defaults to settings.data_dir)
            overwrite: Whether to overwrite existing collection

        Returns:
            Tuple of (num_documents, num_chunks, filenames)
        """
        return self.ingest_documents(
            directory=pdf_directory,
            file_types=['pdf'],
            overwrite=overwrite
        )

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
                "provider": settings.provider_type
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