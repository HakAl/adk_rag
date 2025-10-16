# Architecture Documentation

## Overview

This RAG Agent application is built using clean architecture principles, ensuring maintainability, testability, and scalability.

## Architecture Layers

### 1. Configuration Layer (`config/`)

**Purpose**: Centralized configuration management

- `settings.py`: Application settings with environment variable support
- `logging_config.py`: Logging configuration and setup

**Design Principles**:
- Single source of truth for configuration
- Environment-aware (development, production, testing)
- Type-safe with dataclasses
- Automatic directory creation

### 2. Core Layer (`app/core/`)

**Purpose**: Core business logic and application orchestration

- `application.py`: Main application class that coordinates all services

**Design Principles**:
- Dependency injection
- Service orchestration
- High-level business operations

### 3. Service Layer (`app/services/`)

**Purpose**: Encapsulated business logic for specific domains

**Services**:

#### VectorStoreService
- **Responsibility**: Document ingestion and vector similarity search
- **Dependencies**: LangChain, ChromaDB, Ollama embeddings
- **Key Methods**:
  - `ingest_pdfs()`: Load and embed documents
  - `search()`: Perform similarity search
  - `get_retriever()`: Get LangChain retriever
  - `get_stats()`: Collection statistics

#### RAGService
- **Responsibility**: Question answering using retrieval and generation
- **Dependencies**: VectorStoreService, LiteLLM
- **Key Methods**:
  - `query()`: Answer questions with RAG
  - `_build_prompt()`: Construct LLM prompts
  - `_generate()`: Generate answers with LLM

#### ADKAgentService
- **Responsibility**: Google ADK agent orchestration
- **Dependencies**: RAGService, Google ADK
- **Key Methods**:
  - `create_session()`: Initialize conversation sessions
  - `chat()`: Process messages through agent
  - `_rag_query_tool()`: Tool function for RAG queries

**Design Principles**:
- Single Responsibility Principle (SRP)
- Dependency Injection
- Clear interfaces
- Error handling and logging

### 4. CLI Layer (`app/cli/`)

**Purpose**: User interface via command line

- `chat.py`: Interactive chat interface

**Design Principles**:
- User-friendly output
- Graceful error handling
- Command processing

### 5. Scripts Layer (`scripts/`)

**Purpose**: Standalone utility scripts

- `ingest.py`: Document ingestion script

**Design Principles**:
- CLI argument parsing
- Reusable logic from services
- Comprehensive output

## Data Flow

### Document Ingestion Flow

```
PDF Files → PyPDFDirectoryLoader → TextSplitter → OllamaEmbeddings → ChromaDB
```

1. **Load**: PDFs loaded from directory
2. **Split**: Documents split into chunks
3. **Embed**: Chunks converted to vectors via Ollama
4. **Store**: Vectors persisted in ChromaDB

### Query Flow (Direct RAG)

```
User Query → VectorStore.search() → Context Retrieval → LLM Prompt → Answer
```

1. **Embed Query**: Convert query to vector
2. **Search**: Find similar document chunks
3. **Build Context**: Aggregate relevant chunks
4. **Generate**: LLM produces answer with context

### Query Flow (ADK Agent)

```
User Message → ADK Agent → Tool Decision → rag_query_tool() → RAG Flow → Response
```

1. **Agent Receives Message**: ADK processes user input
2. **Tool Selection**: Agent decides to call rag_query tool
3. **RAG Execution**: Tool invokes RAG service
4. **Response Assembly**: Agent formats final response

## Key Design Patterns

### 1. Dependency Injection

Services receive dependencies via constructor:

```python
class RAGService:
    def __init__(self, vector_store: VectorStoreService):
        self.vector_store = vector_store

class ADKAgentService:
    def __init__(self, rag_service: RAGService):
        self.rag_service = rag_service
```

**Benefits**:
- Testability (easy to mock dependencies)
- Flexibility (swap implementations)
- Clear dependency graph

### 2. Service Layer Pattern

Business logic encapsulated in service classes:

- Each service has a clear responsibility
- Services are stateless or manage their own state
- Services can be tested independently

### 3. Configuration Pattern

Centralized configuration with environment support:

```python
settings = Settings.from_env()
```

**Benefits**:
- Easy to change configuration
- Environment-specific settings
- Type safety

### 4. Factory Pattern (Implicit)

Application creates and wires services:

```python
class RAGAgentApp:
    def __init__(self):
        self.vector_store = VectorStoreService()
        self.rag_service = RAGService(self.vector_store)
        self.adk_agent = ADKAgentService(self.rag_service)
```

## Error Handling Strategy

### Levels of Error Handling

1. **Service Level**: Catch specific exceptions, log errors
2. **Application Level**: Catch service errors, provide fallbacks
3. **CLI Level**: Catch all errors, display user-friendly messages

### Logging Strategy

- **DEBUG**: Detailed information for debugging
- **INFO**: General information about application state
- **WARNING**: Warning messages
- **ERROR**: Error messages with stack traces

## Testing Strategy

### Test Types

1. **Unit Tests**: Test individual functions/methods
2. **Integration Tests**: Test service interactions
3. **End-to-End Tests**: Test complete workflows

### Test Structure

```
tests/
├── unit/
│   ├── test_vector_store.py
│   ├── test_rag.py
│   └── test_adk_agent.py
├── integration/
│   ├── test_ingestion_flow.py
│   └── test_query_flow.py
└── e2e/
    └── test_chat_session.py
```

## Scalability Considerations

### Current Architecture (Single Process)

- Suitable for: Single user, local deployment
- Limitations: No concurrent users, no horizontal scaling

### Future Extensions

#### 1. API Layer
Add Flask/FastAPI REST API:
- Multiple concurrent users
- Stateless request handling
- Session management in Redis

#### 2. Database Layer
Replace in-memory sessions:
- PostgreSQL for metadata
- Redis for session state
- Persistent conversation history

#### 3. Message Queue
Async processing for long operations:
- Celery for ingestion tasks
- RabbitMQ/Redis for queue
- Background job processing

#### 4. Microservices
Split services into separate deployments:
- Vector store service
- RAG service
- Agent service
- API gateway

## Security Considerations

### Current Implementation

- Local-only (no network exposure)
- No authentication needed
- Files stored locally

### Production Requirements

- Authentication & authorization
- Input validation & sanitization
- Rate limiting
- API key management
- TLS/SSL for API endpoints
- Secrets management (not in code)

## Performance Optimization

### Current Optimizations

- Lazy loading of vector store
- Reuse of embeddings model
- Efficient chunk storage

### Future Optimizations

- Caching of frequent queries
- Batch processing for ingestion
- GPU acceleration for embeddings
- Query result caching
- Connection pooling

## Monitoring & Observability

### Current Capabilities

- Console logging
- File logging (optional)
- Application statistics

### Production Requirements

- Structured logging (JSON)
- Metrics (Prometheus)
- Tracing (OpenTelemetry)
- Error tracking (Sentry)
- Performance monitoring

## Deployment Architecture

### Development

```
Developer Machine
├── Ollama Service (localhost:11434)
├── Python Application
└── ChromaDB (local files)
```

### Production (Future)

```
Load Balancer
├── API Instances (N)
│   └── Connect to shared services
├── Ollama Service (dedicated server/cluster)
├── PostgreSQL (metadata)
├── Redis (sessions/cache)
└── ChromaDB/Qdrant (vector store)
```

## Extension Points

The architecture is designed for easy extension:

1. **New Tools for Agent**: Add to ADKAgentService.tools
2. **New Document Types**: Add loaders to VectorStoreService
3. **New LLM Providers**: Update RAGService model config
4. **New Interfaces**: Add API/Web alongside CLI
5. **New Storage Backends**: Implement interface for vector store

## Conclusion

This architecture balances:
- **Simplicity**: Easy to understand and maintain
- **Flexibility**: Easy to extend and modify
- **Scalability**: Clear path to production deployment
- **Testability**: Services can be tested independently
- **Maintainability**: Clean separation of concerns
