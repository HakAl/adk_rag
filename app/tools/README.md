# Tools Package

This package contains all tools available to the ADK agent. Tools are functions that the agent can call to perform specific tasks.

## Structure

```
app/tools/
├── __init__.py          # Package exports
├── validation.py        # Code validation tools
├── rag_tools.py         # RAG query tools
└── README.md           # This file
```

## Available Tools

### Validation Tools (`validation.py`)

#### `validate_code(code: str, language: str) -> str`
Validates code syntax for various programming languages.

**Supported Languages:**
- Python
- JavaScript (requires Node.js)
- JSON

**Example:**
```python
from app.tools import validate_code

result = validate_code("def hello():\n    return 'world'", "python")
print(result)  # ✅ Python code syntax is valid.
```

### RAG Tools (`rag_tools.py`)

RAG tools are created as closures that capture service instances. This is required by the ADK framework's tool calling mechanism.

#### `create_rag_query_tool(rag_service: RAGService) -> Callable`
Creates a tool for querying the local knowledge base.

#### `create_rag_anthropic_tool(rag_anthropic_service: RAGAnthropicService) -> Callable`
Creates a tool for querying using Anthropic Claude (for complex reasoning).

#### `create_rag_google_tool(rag_google_service: RAGGoogleService) -> Callable`
Creates a tool for querying using Google Gemini (for factual queries).

#### `create_rag_tools(rag_service, rag_anthropic_service=None, rag_google_service=None) -> List[Callable]`
Factory function that creates all available RAG tools based on provided services.

**Example:**
```python
from app.tools import create_rag_tools

# Create tools for all available providers
tools = create_rag_tools(
    rag_service=local_rag,
    rag_anthropic_service=anthropic_rag,
    rag_google_service=google_rag
)

# Returns list of callable tools
for tool in tools:
    print(tool.__name__)  # rag_query, rag_query_anthropic, rag_query_google
```

## Adding New Tools

To add a new tool:

1. **Create a new file** in `app/tools/` (e.g., `web_search.py`)
2. **Define your tool function:**
   ```python
   def web_search(query: str) -> str:
       """
       Search the web for information.
       
       Args:
           query: Search query
           
       Returns:
           Search results
       """
       # Implementation here
       pass
   ```

3. **Export in `__init__.py`:**
   ```python
   from app.tools.web_search import web_search
   
   __all__ = [
       'validate_code',
       'create_rag_tools',
       'web_search',  # Add your tool
   ]
   ```

4. **Add to ADK agent** in `app/services/adk_agent.py`:
   ```python
   from app.tools import validate_code, create_rag_tools, web_search
   
   def _build_tools(self):
       tools = [
           validate_code,
           web_search,  # Add your tool
       ]
       # ... rest of code
   ```

5. **Write tests** in `tests/test_tools/test_web_search.py`

## Design Principles

### 1. Simple Functions
Tools should be simple functions with clear signatures and docstrings. The ADK framework uses these docstrings to help the agent understand when to use each tool.

### 2. Closures for Dependencies
When a tool needs dependencies (like service instances), create it using a factory function that returns a closure:

```python
def create_my_tool(service: MyService) -> Callable:
    def my_tool(query: str) -> str:
        return service.do_something(query)
    return my_tool
```

This pattern is required because the ADK framework expects callable tools, not class methods.

### 3. Error Handling
Tools should handle errors gracefully and return user-friendly error messages:

```python
def my_tool(input: str) -> str:
    try:
        # Do something
        return "✅ Success"
    except Exception as e:
        logger.error(f"Tool error: {e}")
        return f"❌ Error: {str(e)}"
```

### 4. Clear Docstrings
The agent uses docstrings to understand what each tool does. Write clear, concise docstrings:

```python
def my_tool(query: str) -> str:
    """
    Brief description of what the tool does.
    
    Args:
        query: Description of the parameter
        
    Returns:
        Description of what's returned
    """
```

## Testing

All tools should have comprehensive tests in `tests/test_tools/`. See existing test files for examples.

Run tests:
```bash
pytest tests/test_tools/
```

Run specific tool tests:
```bash
pytest tests/test_tools/test_validation.py
pytest tests/test_tools/test_rag_tools.py
```