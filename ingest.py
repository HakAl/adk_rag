import os, glob
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OllamaEmbeddings
from langchain_chroma import Chroma

# --- Configuration for Local RAG Ingestion -------------------------
# 1. Directory where your PDF files are stored
PDF_SOURCE_DIR = "data/"

# 2. Directory where the local vector database will be saved
VECTOR_STORE_DIR = "chroma_db"

# 3. The name of the collection within the vector database
COLLECTION_NAME = "adk_local_rag"

# 4. The Ollama model to use for creating embeddings
EMBEDDING_MODEL = "nomic-embed-text"

# --- Local RAG Ingestion Pipeline -----------------------------------

# 1. Load all PDF documents from the specified directory
print(f"Loading documents from '{PDF_SOURCE_DIR}'...")
loader = PyPDFDirectoryLoader(PDF_SOURCE_DIR)
docs = loader.load()

if not docs:
    print("No PDF documents found. Please check the directory.")
else:
    print(f"Loaded {len(docs)} document(s).")

    # 2. Split the documents into smaller chunks
    print("Splitting documents into chunks...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1024, chunk_overlap=100)
    splits = text_splitter.split_documents(docs)
    print(f"Created {len(splits)} text chunks.")

    # 3. Initialize the Ollama embedding model
    print(f"Initializing embedding model: '{EMBEDDING_MODEL}'...")
    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)

    # 4. Create the vector store and ingest the documents
    #    This will generate embeddings and save them to disk in the VECTOR_STORE_DIR.
    print(f"Creating vector store in '{VECTOR_STORE_DIR}'...")
    vectorstore = Chroma.from_documents(
        documents=splits,
        embedding=embeddings,
        collection_name=COLLECTION_NAME,
        persist_directory=VECTOR_STORE_DIR
    )

    print("\n✅ Ingestion complete.")
    print(f"Vector store created with {vectorstore._collection.count()} embeddings.")