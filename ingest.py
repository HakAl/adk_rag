import os, glob, time
from vertexai.preview import rag
import vertexai

PROJECT_ID = os.environ["GOOGLE_CLOUD_PROJECT"]
LOCATION   = "us-central1"
BUCKET     = os.environ["BUCKET"]          # gs://adk-rag-demo-xxx

vertexai.init(project=PROJECT_ID, location=LOCATION)

corpus_display = "adk_quickstart_corpus"
embedding_config = rag.EmbeddingModelConfig(
    publisher_model="publishers/google/models/text-embedding-004"
)

# 1. Create (or re-use) corpus
try:
    corpus = rag.RAGCorpus.create(
        display_name=corpus_display,
        embedding_model_config=embedding_config,
    )
    print("Corpus created:", corpus.name)
except Exception:   # already exists
    corpus = next(c for c in rag.RAGCorpus.list()
                  if c.display_name == corpus_display)
    print("Re-using corpus:", corpus.name)

# 2. Upload & import every PDF
for local_pdf in glob.glob("data/*.pdf"):
    blob_name = os.path.basename(local_pdf)
    gs_path   = f"{BUCKET}/{blob_name}"

    # a) upload to GCS
    os.system(f"gsutil cp '{local_pdf}' {gs_path}")

    # b) import into RAG corpus
    corpus.add_document(
        uri=gs_path,
        chunk_size=1024,
        chunk_overlap=100
    )
    print(f"Imported {blob_name}")

print("Waiting for indexing…")
time.sleep(20)