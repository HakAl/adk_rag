# Multi-Provider Setup Guide

Configure multiple LLM providers for enhanced flexibility and performance.

## Available Providers

| Provider | Best For | Requires API Key | Cost |
|----------|----------|------------------|------|
| **Local (Ollama)** | Fast queries, privacy, always available | No | Free |
| **Anthropic Claude** | Complex reasoning, analysis, nuanced understanding | Yes | Pay per token |
| **Google Gemini** | Fast responses, factual queries, summaries | Yes | Pay per token |

## Quick Setup

### 1. Install Dependencies

```bash
pip install anthropic google-generativeai
```

### 2. Configure API Keys

Add to your `.env` file:

```bash
# Anthropic Claude (optional)
ANTHROPIC_API_KEY=sk-ant-your-key-here
ANTHROPIC_MODEL=claude-sonnet-4-20250514

# Google Gemini (optional)
GOOGLE_API_KEY=your-google-key-here
GOOGLE_MODEL=gemini-2.0-flash-exp
```

### 3. Run the Application

```bash
python main.py
```

The application automatically detects and enables available providers.

## Provider Details

### Local (Ollama)

**Advantages:**
- ✅ Free to use
- ✅ Runs locally (private)
- ✅ No API rate limits
- ✅ Always available

**Requirements:**
- Ollama installed locally
- Downloaded models

**Setup:**
```bash
# Install Ollama from ollama.com
ollama pull nomic-embed-text
ollama pull phi3:mini
```

**Configuration:**
```bash
OLLAMA_BASE_URL=http://localhost:11434
CHAT_MODEL=phi3:mini
EMBEDDING_MODEL=nomic-embed-text
```

---

### Anthropic Claude

**Advantages:**
- ✅ Best reasoning capabilities
- ✅ Excellent for complex analysis
- ✅ Superior nuanced understanding
- ✅ Long context windows

**Use Cases:**
- Deep technical analysis
- Complex reasoning tasks
- Nuanced interpretation
- Multi-step problem solving

**Setup:**
1. Get API key from [console.anthropic.com](https://console.anthropic.com)
2. Add to `.env`:
```bash
ANTHROPIC_API_KEY=sk-ant-your-key-here
ANTHROPIC_MODEL=claude-sonnet-4-20250514
```

**Pricing:** See [anthropic.com/pricing](https://www.anthropic.com/pricing)

---

### Google Gemini

**Advantages:**
- ✅ Very fast responses
- ✅ Excellent for factual queries
- ✅ Good at summarization
- ✅ Cost-effective

**Use Cases:**
- Quick factual lookups
- Summarization tasks
- Fast conversational responses
- High-volume queries

**Setup:**
1. Get API key from [makersuite.google.com](https://makersuite.google.com)
2. Add to `.env`:
```bash
GOOGLE_API_KEY=your-google-key-here
GOOGLE_MODEL=gemini-2.0-flash-exp
```

**Pricing:** See [ai.google.dev/pricing](https://ai.google.dev/pricing)

## Provider Selection

### Automatic Routing

The ADK agent intelligently routes queries:

```
Simple factual questions     → Local/Gemini (fast)
Complex analysis/reasoning   → Claude (best quality)
Technical deep-dives         → Claude
Quick summaries              → Gemini/Local
```

### Manual Selection

Specify provider in your queries:

**CLI:**
```bash
# Uses automatic routing
> What is machine learning?

# Specific provider (future feature)
# Currently uses default routing
```

**API:**
```python
# Automatic routing
response = client.chat("What is AI?")

# Specific provider
response = client.chat("Analyze this topic", provider="anthropic")
response = client.chat("Quick summary", provider="google")
response = client.chat("Private query", provider="local")
```

**Python:**
```python
from app.core.application import RAGAgentApp

app = RAGAgentApp()

# Use local provider
answer, sources = app.query_rag("What is X?", provider="local")

# Use Anthropic
answer, sources = app.query_rag("Analyze Y", provider="anthropic")

# Use Google
answer, sources = app.query_rag("Summarize Z", provider="google")
```

## Check Available Providers

```python
from app.core.application import RAGAgentApp

app = RAGAgentApp()
stats = app.get_stats()

print(stats['providers'])
# Output: {'local': True, 'anthropic': True, 'google': False}
```

**Via API:**
```bash
curl http://localhost:8000/stats | jq '.providers'
```

## Cost Management

### Default Behavior

- Uses **local provider** by default (free)
- Routes to external providers only when beneficial for quality
- Minimizes API costs automatically

### Cost Estimation

| Provider | Input Cost | Output Cost | Example Query Cost |
|----------|-----------|-------------|-------------------|
| Local | Free | Free | $0.00 |
| Claude Sonnet | ~$3/M tokens | ~$15/M tokens | ~$0.01 |
| Gemini Flash | ~$0.075/M tokens | ~$0.30/M tokens | ~$0.0005 |

*Prices approximate - check provider websites for current rates*

### Cost Control Tips

1. **Use local by default** - Set as primary provider
2. **Batch queries** - Group related questions
3. **Monitor usage** - Check provider dashboards
4. **Set budget alerts** - Configure in provider console
5. **Cache aggressively** - Vector store caching reduces queries

## Configuration Examples

### Local Only (No Costs)

```bash
# .env
OLLAMA_BASE_URL=http://localhost:11434
CHAT_MODEL=phi3:mini
EMBEDDING_MODEL=nomic-embed-text

# Don't set ANTHROPIC_API_KEY or GOOGLE_API_KEY
```

### Local + Claude (Best Quality)

```bash
# .env
OLLAMA_BASE_URL=http://localhost:11434
CHAT_MODEL=phi3:mini
EMBEDDING_MODEL=nomic-embed-text

ANTHROPIC_API_KEY=sk-ant-your-key-here
ANTHROPIC_MODEL=claude-sonnet-4-20250514
```

### All Providers (Maximum Flexibility)

```bash
# .env
OLLAMA_BASE_URL=http://localhost:11434
CHAT_MODEL=phi3:mini
EMBEDDING_MODEL=nomic-embed-text

ANTHROPIC_API_KEY=sk-ant-your-key-here
ANTHROPIC_MODEL=claude-sonnet-4-20250514

GOOGLE_API_KEY=your-google-key-here
GOOGLE_MODEL=gemini-2.0-flash-exp
```

## Troubleshooting

### Provider Not Available

**Check 1:** Verify API key is set
```bash
echo $ANTHROPIC_API_KEY
echo $GOOGLE_API_KEY
```

**Check 2:** Check stats
```bash
curl http://localhost:8000/stats | jq '.providers'
```

**Check 3:** View logs
```bash
tail -f logs/rag_agent.log | grep -i provider
```

### API Key Errors

**Anthropic:**
```bash
# Verify key format
# Should start with: sk-ant-api03-...

# Test key
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -d '{"model":"claude-sonnet-4-20250514","max_tokens":10,"messages":[{"role":"user","content":"test"}]}'
```

**Google:**
```bash
# Verify key exists
echo $GOOGLE_API_KEY

# Test key
curl "https://generativelanguage.googleapis.com/v1/models?key=$GOOGLE_API_KEY"
```

### Rate Limits

**Solution 1:** Use local provider for high-volume queries
```python
answer = app.query_rag("Query", provider="local")
```

**Solution 2:** Implement retry logic
```python
import time
from anthropic import RateLimitError

try:
    answer = app.query_rag("Query", provider="anthropic")
except RateLimitError:
    time.sleep(60)
    answer = app.query_rag("Query", provider="anthropic")
```

**Solution 3:** Increase rate limits with provider

## Best Practices

1. **Start local** - Test with Ollama first
2. **Add providers incrementally** - Enable cloud providers as needed
3. **Monitor costs** - Set up budget alerts
4. **Use appropriate providers** - Match provider to task complexity
5. **Cache results** - Avoid redundant API calls
6. **Handle errors gracefully** - Implement fallbacks
7. **Secure API keys** - Use environment variables, never commit to git

## Provider Comparison

### When to Use Each Provider

**Local (Ollama):**
- ✅ Development and testing
- ✅ Privacy-sensitive queries
- ✅ High-volume, simple queries
- ✅ No internet connection
- ✅ Cost control

**Anthropic Claude:**
- ✅ Complex analysis required
- ✅ Nuanced understanding needed
- ✅ Multi-step reasoning
- ✅ High-stakes decisions
- ✅ Best possible quality

**Google Gemini:**
- ✅ Fast responses needed
- ✅ Factual lookups
- ✅ Summarization tasks
- ✅ Cost-sensitive scenarios
- ✅ High-volume production use

## Example Workflows

### Research Task (Use Claude)
```python
# Deep analysis of complex topic
answer = app.query_rag(
    "Analyze the implications of X on Y, considering Z factors",
    provider="anthropic"
)
```

### Quick Lookup (Use Gemini or Local)
```python
# Fast factual query
answer = app.query_rag(
    "What is the definition of X?",
    provider="google"  # or "local"
)
```

### Private Query (Use Local)
```python
# Sensitive company data
answer = app.query_rag(
    "What are our Q4 projections?",
    provider="local"  # Stays on your machine
)
```

## Security Notes

- **Never commit API keys** to version control
- **Use environment variables** for all credentials
- **Rotate keys regularly** per provider recommendations
- **Monitor for unauthorized usage** in provider dashboards
- **Use least-privilege keys** when possible
- **Implement rate limiting** in production
- **Log API usage** for audit trails