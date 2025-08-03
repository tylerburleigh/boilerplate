# LiteLLM + LangChain Integration

A minimal working Python implementation that integrates LiteLLM proxy with LangChain for unified LLM access, featuring structured JSON output via Pydantic schemas and using `o4-mini`.

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Install `docker-compose`.

### 2. Set Up Environment Variables

Create `litellm/.env` like `/litellm/.env.example`

### 3. Configure LiteLLM

Configure `litellm/litellm_config.yaml` as appropriate

### 4. Start LiteLLM Proxy with Docker Compose

Navigate to the `litellm/` directory and start the services:

```bash
cd litellm/
docker-compose up
```

Note: You might need to `sudo docker-compose up`

This will start:
- LiteLLM proxy on `http://localhost:4000`
- PostgreSQL database for logging and management
- Prometheus for monitoring

The proxy will automatically use your `litellm_config.yaml` configuration and load environment variables from your `.env` file.

### 5. Run the Example

Once LiteLLM proxy is running, you can run the example.

(Note: The example uses `o4-mini` so you might need to change that, or add the necessary config and keys to your config and env files.)

```bash
python get_completion_example.py
```

## Usage Examples

Completions can be run with or without "structured output".

### Structured Output, returning Pydantic Object

```python
from get_completion_example import get_completion

# Get structured response with Pydantic validation
response = get_completion("What is the capital of France?")
print(f"Answer: {response.answer}")
print(f"Reasoning: {response.reasoning}")
```

### Structured Output, returning JSON dictionary

```python
from get_completion_example import get_completion_json

# Get response as dictionary
response = get_completion_json("What is the capital of France?")
print(response)
# Output: {'answer': 'Paris', 'reasoning': 'Paris is the capital and largest city of France...'}
```

### No Structured Output, returning String

```python
from get_completion_example import get_completion_string

# Get response as plain string
response = get_completion_string("What is the capital of France?")
print(response)
# Output: "The capital of France is Paris."
```

## Configuration

### LiteLLM Configuration

The `litellm/litellm_config.yaml` file contains the configuration for the o4-mini model:

```yaml
model_list:
  - model_name: o4-mini
    litellm_params:
      model: openai/o4-mini
      api_key: os.environ/OPENAI_API_KEY
      timeout: 60

general_settings:
  master_key: os.environ/LITELLM_MASTER_KEY
  
litellm_settings:
  request_timeout: 60
  drop_params: true
```

**Parameter Filtering**: `drop_params: true` will automatically drop unsupported parameters like `parallel_tool_calls` which o4-mini doesn't support, preventing 400 errors when using structured output.

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | Your OpenAI API key |
| `LITELLM_MASTER_KEY` | Yes | LiteLLM proxy authentication key (must start with `sk-`) |
| `LITELLM_PROXY_URL` | No | Proxy URL (default: `http://localhost:4000`) |

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Your App     │───▷│  get_completion  │───▷│   LangChain     │
│                │    │    Function      │    │   ChatOpenAI    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
                                               ┌─────────────────┐
                                               │  LiteLLM Proxy  │
                                               │ (localhost:4000)│
                                               └─────────────────┘
                                                        │
                                                        ▼
                                         ┌─────────────────────────────┐
                                         │     Various LLM Providers   │
                                         │  OpenAI │ Anthropic │ etc.  │
                                         └─────────────────────────────┘
```

## Structured Output Schema

The `CompletionResponse` is a simple example Pydantic model that includes:

```python
class CompletionResponse(BaseModel):
    answer: str              # The main answer to the user's question
    reasoning: str           # Brief explanation of the reasoning behind the answer
```

## Error Handling

The functions include error handling:

```python
try:
    response = get_completion("Your prompt here")
    print(response.answer)
except Exception as e:
    print(f"Error: {e}")
```

Common error scenarios:
- LiteLLM proxy not running
- Invalid API keys
- Network connectivity issues
- Invalid response format

## Security Best Practices

1. **Never hardcode API keys** in configuration files
2. **Use environment variables** for all sensitive data
3. **Keep .env files out of version control**

## Integration Patterns

### With FastAPI

```python
from fastapi import FastAPI
from get_completion_example import get_completion

app = FastAPI()

@app.post("/complete")
async def complete(prompt: str):
    response = get_completion(prompt)
    return response.model_dump()
```

### With Jupyter Notebooks

```python
# Cell 1: Import and setup
from get_completion_example import get_completion

# Cell 2: Interactive usage
prompt = input("Enter your prompt: ")
response = get_completion(prompt)
print(f"Answer: {response.answer}")
```

## Restarting LiteLLM

```
docker compose down
docker-compose up
```