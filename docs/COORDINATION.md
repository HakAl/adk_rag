# Coordination Approach

## Overview

The VIBE Code uses a **router-coordinator-specialist** architecture to intelligently handle user requests with cloud-first execution and automatic fallback.

---

## Architecture

```
User Request
     ↓
┌─────────────────────┐
│   Router            │  Classifies request into category
│ (Cloud/Local)       │  Returns: primary + parallel agents
└─────────────────────┘
     ↓
┌─────────────────────┐
│   Coordinator       │  Orchestrates specialist execution
│                     │  Manages parallel execution
└─────────────────────┘
     ↓
┌─────────────────────┐
│   Specialists       │  Execute tasks with fallback:
│ (Cloud → Local)     │  Anthropic → Google → Phi-3
└─────────────────────┘
```

---

## Components

### 1. **Router** (`router.py`)

**Purpose:** Analyze and classify incoming requests

**Categories:**
- `code_validation` - Syntax checking, validation
- `rag_query` - Knowledge base queries
- `code_generation` - Writing new code
- `code_analysis` - Explaining/reviewing code
- `complex_reasoning` - Multi-step problems
- `general_chat` - Casual conversation

**Providers:**
- **Cloud:** Anthropic Claude or Google Gemini (preferred)
- **Local:** llama.cpp with Phi-3 (fallback)

**Output:**
```json
{
    "primary_agent": "code_validation",
    "parallel_agents": ["code_analysis"],
    "confidence": 0.9,
    "reasoning": "needs validation and explanation"
}
```

---

### 2. **Coordinator** (`coordinator_agent.py`)

**Purpose:** Orchestrate specialist execution based on routing decisions

**Responsibilities:**
- Receive routing classifications
- Delegate to appropriate specialists
- Manage parallel execution for complex requests
- Aggregate responses from multiple specialists
- Handle session management

**Execution Modes:**
- **Single specialist:** One agent handles the request
- **Parallel specialists:** Multiple agents run concurrently (cloud = fast!)

---

### 3. **Specialists** (`specialist_manager.py`)

**Purpose:** Execute specialized tasks with intelligent fallback

**Specialist Types:**
1. **Code Validator** - Syntax and error checking
2. **Code Generator** - Writing new code
3. **Code Analyst** - Code explanation and review
4. **Knowledge Assistant** - RAG-based queries
5. **Reasoning Specialist** - Complex problem solving
6. **General Assistant** - Conversational responses

**Provider Cascade:**
```
1. Anthropic (Claude)
   ↓ (if rate limited/unavailable)
2. Google (Gemini)
   ↓ (if rate limited/unavailable)
3. Local (Phi-3)
   ↓ (if unavailable)
4. Error
```

---

## Execution Flow

### Simple Request Example

```
User: "validate this Python code"
  ↓
Router: primary_agent="code_validation", parallel_agents=[]
  ↓
Coordinator: Delegate to Code Validator
  ↓
Specialist Manager:
  → Try Anthropic Claude ✓ (500ms)
  ← Response returned
```

### Complex Request Example

```
User: "validate and explain this code, then suggest improvements"
  ↓
Router: primary_agent="code_validation"
        parallel_agents=["code_analysis"]
  ↓
Coordinator: Run 2 specialists in PARALLEL
  ↓
Specialist Manager:
  → Code Validator (Anthropic) ──┐
  → Code Analyst (Anthropic) ────┤ (parallel, ~600ms total)
                                 │
  ← Aggregate both responses ────┘
```

---

## Fallback Mechanisms

### 1. **Circuit Breaker**

Prevents repeated calls to failing services:

- **CLOSED:** Normal operation
- **OPEN:** Service failing, skip to next provider
- **HALF_OPEN:** Testing recovery

**Configuration:**
- Failure threshold: 5 failures
- Timeout: 60 seconds
- Auto-recovery testing

### 2. **Retry Logic**

Handles transient failures:

- Retry attempts: 3
- Backoff strategy: Exponential (1s, 2s, 4s)
- Rate limit handling: Auto-retry with backoff

### 3. **Provider Cascade**

Automatic fallback chain:

```
Request → Anthropic
          ↓ (fails)
          Google
          ↓ (fails)
          Phi-3 Local
          ↓ (fails)
          Error message
```

---

## Performance

### Cloud Specialists (Anthropic/Google)

**Single Specialist:**
- Latency: ~500ms
- Parallelism: ✓ True concurrency

**3 Parallel Specialists:**
- Total time: ~600ms (all run simultaneously)
- Network: Multiple concurrent API calls

### Local Specialist (Phi-3)

**Single Specialist:**
- Latency: ~3s
- Parallelism: ⚠️ Limited (CPU/GPU contention)

**3 Parallel Specialists:**
- Total time: ~5-9s (resource contention)
- Hardware: Fights for CPU/memory

---

## Configuration

### Cloud-Only (Recommended)

```bash
# .env
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...  # optional backup
USE_COORDINATOR_AGENT=true

# No local models needed!
```

**Performance:** ~600ms for 3 parallel specialists

### Cloud + Local Fallback

```bash
# .env
ANTHROPIC_API_KEY=sk-ant-...
LLAMACPP_CHAT_MODEL_PATH=chat/phi3-mini-4k-instruct-q4_k_m.gguf
ENABLE_LOCAL_FALLBACK=true
USE_COORDINATOR_AGENT=true
```

**Performance:** Cloud speed with local reliability

### Local-Only

```bash
# .env
PROVIDER_TYPE=llamacpp
LLAMACPP_CHAT_MODEL_PATH=chat/phi3-mini-4k-instruct-q4_k_m.gguf
ROUTER_MODEL_PATH=phi3-mini-4k-instruct-q4.gguf
USE_COORDINATOR_AGENT=true
```

**Performance:** ~5-9s for 3 parallel specialists (slower but private)

---

## Session Management

**Session Storage:** In-memory (per coordinator instance)

**Session Contents:**
- Conversation history (user + assistant messages)
- Context for follow-up questions
- Isolated per session

**Session Lifecycle:**
```python
session_id = await coordinator.create_session(user_id)
response = await coordinator.chat(message, user_id, session_id)
```

---

## RAG Integration

**For Knowledge Queries (`rag_query` category):**

1. Coordinator detects RAG query
2. Retrieves context from vector store
3. Passes context to specialist
4. Specialist answers using context

**RAG Priority:**
- Anthropic RAG (if available)
- Google RAG (if available)
- Local RAG (fallback)

---

## Error Handling

### Graceful Degradation

```
Specialist Error
    ↓
Try Next Provider
    ↓
All Providers Failed?
    ↓
Fallback to General Assistant
    ↓
General Assistant Failed?
    ↓
User-Friendly Error Message
```

### Circuit Breaker Protection

- Prevents cascading failures
- Auto-recovery after timeout
- Per-provider isolation

---

## Monitoring

### Get Specialist Status

```python
status = coordinator.get_specialist_status()
# Returns:
# {
#   "anthropic": {"available": true, "circuit_state": "CLOSED"},
#   "google": {"available": true, "circuit_state": "CLOSED"},
#   "local": {"available": true, "model_loaded": true}
# }
```

### Reset Circuit Breakers

```python
coordinator.reset_circuit_breakers()
```

---

## Best Practices

### 1. **Use Cloud for Production**
- Faster parallel execution
- Better quality responses
- Lower resource usage

### 2. **Enable Local Fallback**
- Reliability during cloud outages
- Rate limit protection
- Privacy option

### 3. **Monitor Circuit Breakers**
- Check status regularly
- Alert on OPEN state
- Auto-recovery testing

### 4. **Tune Retry Logic**
- Adjust retry attempts for your use case
- Configure backoff strategy
- Balance latency vs reliability

---

## Summary

The coordination approach provides:

✅ **Intelligent routing** - Right specialist for each task  
✅ **Cloud-first execution** - Fast parallel processing  
✅ **Automatic fallback** - Reliability across providers  
✅ **Circuit breakers** - Protection from cascading failures  
✅ **Parallel execution** - Multiple specialists concurrently  
✅ **Session management** - Conversation context  
✅ **RAG integration** - Knowledge-based responses  

**Result:** Fast, reliable, intelligent agent coordination with graceful degradation.