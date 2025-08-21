# LiteLLM + LangChain Integration

A minimal working Python implementation that integrates LiteLLM proxy with LangChain for unified LLM access, featuring structured JSON output via Pydantic schemas and configured to use OpenAI, Anthropic/Claude, and Google/Gemini models.

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Install `docker-compose`.

### 2. Set Up Environment Variables

The docker-compose configuration pulls environment variables from your system. Set these in your shell profile (`~/.bashrc`, `~/.zshrc`, etc.):

```bash
export LITELLM_MASTER_KEY="sk-1234"  # Your master key for LiteLLM admin
export LITELLM_SALT_KEY="sk-1234"    # Salt key for encryption (optional, defaults to sk-1234)

# LLM Provider API Keys (set the ones you plan to use)
export OPENAI_API_KEY="your-openai-api-key"
export ANTHROPIC_API_KEY="your-anthropic-api-key"  # For Claude models
export GOOGLE_API_KEY="your-google-api-key"  # For Gemini models

# Optional custom base URLs
export OPENAI_BASE_URL="https://api.openai.com/v1/"  # Optional, defaults to OpenAI's API
```

Alternatively, you can create a `litellm/.env` file (see `litellm/.env.example`) but system environment variables will take precedence.

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
- PostgreSQL database on `localhost:5432` for logging and management
- Prometheus on `http://localhost:9090` for monitoring

The proxy will automatically use your `litellm_config.yaml` configuration and load environment variables from your `.env` file.

### 5. Create a LiteLLM "virtual key"

Go to `http://localhost:4000` and log in using your `LITELLM_MASTER_KEY` from step 2.

Navigate to the Virtual Keys tab and click `+ Create New Key`. 

Save this virtual key in your shell profile:

```bash
export LITELLM_API_KEY="sk-your-generated-virtual-key"
```

This virtual key (different from the master key) will be used by your application to authenticate with the LiteLLM proxy.

### 6. Run the Example

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
| `LITELLM_MASTER_KEY` | Yes | Master key for LiteLLM admin access (must start with `sk-`) |
| `LITELLM_API_KEY` | Yes | Virtual key for API authentication (obtained from LiteLLM UI) |
| `OPENAI_API_KEY` | If using OpenAI | Your OpenAI API key |
| `ANTHROPIC_API_KEY` | If using Claude | Your Anthropic API key for Claude models |
| `GOOGLE_API_KEY` | If using Gemini | Your Google API key for Gemini models |
| `LITELLM_SALT_KEY` | No | Salt key for encryption (default: `sk-1234`) |
| `OPENAI_BASE_URL` | No | Custom OpenAI base URL (default: `https://api.openai.com/v1/`) |
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
