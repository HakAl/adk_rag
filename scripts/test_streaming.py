"""
Diagnostic script to test streaming at each layer.
Run this to identify where buffering occurs.
"""
import asyncio
import httpx
import json
import time


async def create_test_session():
    """Create a test session."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            "http://localhost:8000/sessions/coordinator",
            json={"user_id": "test_user"}
        )
        response.raise_for_status()
        data = response.json()
        return data["session_id"]


async def test_api_streaming():
    """Test if API is actually streaming or buffering."""

    print("Testing streaming from API...\n")

    # Create session first
    print("Creating session...")
    session_id = await create_test_session()
    print(f"Session created: {session_id[:8]}...\n")

    async with httpx.AsyncClient(timeout=180.0) as client:
        url = "http://localhost:8000/chat/coordinator/stream"

        payload = {
            "message": "Write a long story about a robot learning to code",
            "user_id": "test_user",
            "session_id": session_id
        }

        print("Sending request...")
        start_time = time.time()

        async with client.stream("POST", url, json=payload) as response:
            print(f"Response started at {time.time() - start_time:.2f}s\n")

            chunk_count = 0
            content_chunks = 0

            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    chunk_count += 1
                    elapsed = time.time() - start_time

                    try:
                        data = line[6:]  # Remove "data: " prefix
                        event = json.loads(data)
                        event_type = event.get("type")

                        if event_type == "routing":
                            agent = event["data"].get("agent_name", "Unknown")
                            print(f"[{elapsed:.2f}s] ROUTING: {agent}")

                        elif event_type == "content":
                            content_chunks += 1
                            content = event["data"]
                            print(f"[{elapsed:.2f}s] CHUNK #{content_chunks}: {len(content)} chars")

                        elif event_type == "done":
                            print(f"[{elapsed:.2f}s] DONE")

                        elif event_type == "error":
                            print(f"[{elapsed:.2f}s] ERROR: {event['data']}")

                    except json.JSONDecodeError as e:
                        print(f"[{elapsed:.2f}s] Failed to parse: {line[:100]}")

        total_time = time.time() - start_time
        print(f"\nTotal events: {chunk_count}")
        print(f"Content chunks: {content_chunks}")
        print(f"Total time: {total_time:.2f}s")

        if content_chunks < 5:
            print("\n❌ PROBLEM: Very few chunks - likely buffering or fast response!")
        elif total_time < 1.0:
            print("\n❌ PROBLEM: Response came all at once - not streaming!")
        else:
            print("\n✅ Streaming appears to be working!")
            if content_chunks > 10:
                print(f"   Average time between chunks: {total_time/content_chunks:.3f}s")


if __name__ == "__main__":
    print("=" * 70)
    print("Streaming Diagnostic Test")
    print("=" * 70)
    print("\nMake sure the API is running on http://localhost:8000\n")

    try:
        asyncio.run(test_api_streaming())
    except KeyboardInterrupt:
        print("\n\nTest interrupted.")
    except httpx.HTTPStatusError as e:
        print(f"\n\n❌ HTTP Error: {e.response.status_code}")
        print(f"Response: {e.response.text}")
    except Exception as e:
        print(f"\n\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()