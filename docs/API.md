# REST API Reference

FastAPI-based REST API for programmatic access to VIBE Agent.

## Starting the API

```bash
# Start the API server
python run_api.py

# Or with uvicorn directly
uvicorn app.api.main:app --reload

# In Docker
docker-compose up -d
```

**Default URL**: `http://localhost:8000`

## Interactive Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Endpoints

### Health Check

**GET** `/health`

Check API health status.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

**Example:**
```bash
curl http://localhost:8000/health
```

---

### Statistics

**GET** `/stats`

Get application statistics and status.

**Response:**
```json
{
  "app_name": "RAG Agent",
  "version": "1.0.0",
  "environment": "development",
  "vector_store": {
    "status": "ready",
    "count": 100,
    "collection": "adk_local_rag"
  },
  "models": {
    "embedding": "nomic-embed-text",
    "chat": "phi3:mini"
  },
  "providers": {
    "local": true,
    "anthropic": true,
    "google": false
  }
}
```

**Example:**
```bash
curl http://localhost:8000/stats
```

---

### Create Session

**POST** `/sessions`

Create a new chat session.

**Request Body:**
```json
{
  "user_id": "my_user"  // optional, defaults to "api_user"
}
```

**Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "my_user"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/sessions \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test_user"}'
```

---

### Chat

**POST** `/chat`

Send a message and get a response.

**Request Body:**
```json
{
  "message": "What is machine learning?",
  "user_id": "my_user",               // optional
  "session_id": "uuid-here",          // optional
  "provider": "local"                 // optional: local, anthropic, google
}
```

**Response:**
```json
{
  "response": "Machine learning is a subset of artificial intelligence...",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "sources": [
    {
      "content": "Relevant context...",
      "metadata": {
        "source": "document.pdf",
        "page": 5
      }
    }
  ]
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is Python?",
    "user_id": "test_user",
    "session_id": "your-session-id"
  }'
```

## Usage Examples

### Python Client

```python
import requests

BASE_URL = "http://localhost:8000"

class RAGClient:
    def __init__(self, base_url: str, user_id: str = "default"):
        self.base_url = base_url
        self.user_id = user_id
        self.session_id = None
    
    def create_session(self):
        """Create a new chat session"""
        response = requests.post(
            f"{self.base_url}/sessions",
            json={"user_id": self.user_id}
        )
        data = response.json()
        self.session_id = data["session_id"]
        return self.session_id
    
    def chat(self, message: str, provider: str = None):
        """Send a chat message"""
        payload = {
            "message": message,
            "user_id": self.user_id,
            "session_id": self.session_id
        }
        if provider:
            payload["provider"] = provider
        
        response = requests.post(
            f"{self.base_url}/chat",
            json=payload
        )
        return response.json()
    
    def get_stats(self):
        """Get system statistics"""
        response = requests.get(f"{self.base_url}/stats")
        return response.json()

# Usage
client = RAGClient("http://localhost:8000", user_id="john")
client.create_session()

# Ask questions
response = client.chat("What is AI?")
print(response["response"])

# Use specific provider
response = client.chat("Analyze this topic", provider="anthropic")
print(response["response"])

# Check stats
stats = client.get_stats()
print(f"Documents indexed: {stats['vector_store']['count']}")
```

### JavaScript/TypeScript Client

```javascript
class RAGClient {
  constructor(baseURL, userId = 'default') {
    this.baseURL = baseURL;
    this.userId = userId;
    this.sessionId = null;
  }

  async createSession() {
    const response = await fetch(`${this.baseURL}/sessions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: this.userId })
    });
    const data = await response.json();
    this.sessionId = data.session_id;
    return this.sessionId;
  }

  async chat(message, provider = null) {
    const payload = {
      message,
      user_id: this.userId,
      session_id: this.sessionId
    };
    if (provider) payload.provider = provider;

    const response = await fetch(`${this.baseURL}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return await response.json();
  }

  async getStats() {
    const response = await fetch(`${this.baseURL}/stats`);
    return await response.json();
  }
}

// Usage
const client = new RAGClient('http://localhost:8000', 'john');
await client.createSession();

const response = await client.chat('What is machine learning?');
console.log(response.response);
```

### cURL Examples

```bash
# Complete workflow
SESSION_ID=$(curl -X POST http://localhost:8000/sessions \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test"}' | jq -r '.session_id')

# Chat with session
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d "{
    \"message\": \"What is RAG?\",
    \"user_id\": \"test\",
    \"session_id\": \"$SESSION_ID\"
  }"

# Use specific provider
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d "{
    \"message\": \"Analyze this topic in depth\",
    \"user_id\": \"test\",
    \"session_id\": \"$SESSION_ID\",
    \"provider\": \"anthropic\"
  }"

# Get stats
curl http://localhost:8000/stats | jq
```

## CORS Configuration

Default: CORS enabled for all origins (development)

**Production Configuration** (in `app/api/main.py`):

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Error Handling

### Error Response Format

```json
{
  "detail": "Error message here"
}
```

### Common Error Codes

| Code | Meaning | Common Cause |
|------|---------|--------------|
| 400 | Bad Request | Invalid input |
| 404 | Not Found | Session doesn't exist |
| 500 | Internal Error | Server/model error |

## Testing

```bash
# Run API tests
pytest tests/test_api.py -v

# With coverage
pytest tests/test_api.py -v --cov=app.api
```

## Security Considerations

### Production Checklist

- [ ] **Add authentication** (JWT, API keys, OAuth2)
- [ ] **Configure CORS** to specific domains
- [ ] **Add rate limiting** to prevent abuse
- [ ] **Use HTTPS** with proper TLS certificates
- [ ] **Validate inputs** and sanitize data
- [ ] **Implement logging** for security events
- [ ] **Set up monitoring** and alerts
- [ ] **Use environment secrets** for API keys

### Example: Add API Key Authentication

```python
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader

API_KEY = "your-secret-key"
api_key_header = APIKeyHeader(name="X-API-Key")

def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key

@app.post("/chat", dependencies=[Security(verify_api_key)])
async def chat(request: ChatRequest):
    # Your code here
    pass
```

## Performance Tips

1. **Session reuse**: Keep session IDs for conversation continuity
2. **Provider selection**: Use `local` for fast queries, `anthropic` for complex analysis
3. **Caching**: API automatically uses cached embeddings
4. **Batch requests**: Group multiple queries when possible
5. **Connection pooling**: Reuse HTTP connections in clients

## Monitoring

```bash
# View logs
tail -f logs/rag_agent.log

# In Docker
docker-compose logs -f rag-agent

# Monitor requests
curl http://localhost:8000/stats | jq '.vector_store'
```