from google.adk import Agent
from vertexai.preview import rag
import vertexai, os

PROJECT_ID = os.environ["GOOGLE_CLOUD_PROJECT"]
LOCATION   = "us-central1"
CORPUS_DISPLAY = "adk_quickstart_corpus"

vertexai.init(project=PROJECT_ID, location=LOCATION)

# --- Tool: retrieve top-5 chunks + generate answer -----------------
def rag_query(query: str) -> str:
    """
    Retrieve relevant snippets from the knowledge base and
    return a concise answer with citations.
    """
    corpus = next(c for c in rag.RAGCorpus.list()
                  if c.display_name == CORPUS_DISPLAY)
    results = corpus.query(text=query, similarity_top_k=5)

    contexts = [r.text for r in results]
    cites    = [r.uri for r in results]

    prompt = (
        "You are a helpful assistant. Answer the question concisely "
        "using only the provided context. Cite the source file name in brackets.\n\n"
        f"Context:\n{chr(10).join(contexts)}\n\n"
        f"Question: {query}\nAnswer:"
    )
    import vertexai.generative_models as gm
    model = gm.GenerativeModel("gemini-2.0-flash-exp")
    answer = model.generate_content(prompt).text
    return f"{answer}\n\n📚 Sources: {', '.join(set(cites))}"

# --- ADK Agent ----------------------------------------------------
agent = Agent(
    model="gemini-2.0-flash-exp",
    tools=[rag_query],
    instruction=(
        "You are a friendly RAG assistant. "
        "Whenever the user asks a question, ALWAYS call rag_query() "
        "to look up the knowledge base."
    )
)

# local CLI loop (optional)
if __name__ == "__main__":
    while True:
        q = input("\n❓> ")
        if q.lower() in {"exit","quit"}: break
        print(agent.run(q))