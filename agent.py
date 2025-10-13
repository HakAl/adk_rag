import os
import uuid
import litellm
import asyncio

# --- ADK Imports (Matching the working sample) ---
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm #
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# --- LangChain Imports ---
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma

# --- Configuration for Local RAG Agent -----------------------------
VECTOR_STORE_DIR = "chroma_db"
COLLECTION_NAME = "adk_local_rag"
EMBEDDING_MODEL = "nomic-embed-text"
OLLAMA_MODEL = "llama3.1:8b-instruct-q4_K_M"


# --- SYNCHRONOUS Tool Definition (Matching the working sample) ---
def rag_query(query: str) -> str:
    """
    Retrieve relevant snippets from the local knowledge base and
    return a concise answer with citations using a local model.
    """
    # Components are initialized here to be thread-safe.
    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
    vectorstore = Chroma(
        persist_directory=VECTOR_STORE_DIR,
        embedding_function=embeddings,
        collection_name=COLLECTION_NAME
    )
    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

    print(f"\n[Tool Call: rag_query] Retrieving documents for query: '{query}'")
    # Use synchronous .invoke()
    results = retriever.invoke(query)
    contexts = [doc.page_content for doc in results]
    cites = [os.path.basename(doc.metadata.get('source', 'Unknown')) for doc in results]

    prompt = (
        "You are a helpful assistant. Answer the question concisely "
        "using only the provided context. Cite the source file name in brackets.\n\n"
        f"Context:\n{chr(10).join(contexts)}\n\n"
        f"Question: {query}\nAnswer:"
    )

    messages = [{"role": "user", "content": prompt}]
    # Use synchronous .completion()
    response = litellm.completion(model=f"ollama/{OLLAMA_MODEL}", messages=messages)
    answer = response.choices[0].message.content
    return f"{answer}\n\n📚 Sources: {', '.join(set(cites))}"


# --- Main Asynchronous Application Logic ---
async def main():
    """Sets up the agent and runs the interactive CLI loop."""
    print(f"Initializing agent model: '{OLLAMA_MODEL}'...")
    local_llm = LiteLlm(model=f"ollama_chat/{OLLAMA_MODEL}")

    # --- ADK Agent Initialization (Using LlmAgent) ---
    agent = LlmAgent(
        name="local_rag_agent",
        model=local_llm,
        tools=[rag_query],
        output_key="rag_result",
        instruction=(
            "You are a friendly RAG assistant. "
            "Whenever the user asks a question, ALWAYS call the rag_query() tool "
            "to look up information in the knowledge base."
        )
    )

    # --- ADK Runner and Session Setup ---
    APP_NAME = "local_rag_cli"
    USER_ID = "local_user"
    SESSION_ID = str(uuid.uuid4())

    session_service = InMemorySessionService()
    # KEY CHANGE: Session creation is required, as you correctly identified.
    await session_service.create_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)
    runner = Runner(agent=agent, app_name=APP_NAME, session_service=session_service)

    print(f"\n✅ Local RAG Agent is ready. Session ID: {SESSION_ID}")
    while True:
        q = input("\n❓> ")
        if q.lower() in {"exit", "quit"}:
            break

        content = types.Content(role='user', parts=[types.Part(text=q)])

        print("\n🤖 Assistant:")
        # --- KEY CHANGE: Use run_async with an async for loop ---
        async for event in runner.run_async(user_id=USER_ID, session_id=SESSION_ID, new_message=content):
            if event.is_final_response() and event.content:
                final_answer = event.content.parts[0].text.strip()
                print(final_answer)


# --- Application Entry Point ---
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting...")