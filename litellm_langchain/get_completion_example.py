"""
LiteLLM + LangChain Integration with Structured Output

This module provides a unified interface for LLM completions using LiteLLM proxy
with LangChain's ChatOpenAI, featuring structured JSON output via Pydantic schemas.
Supports multiple model providers including OpenAI, Anthropic, and Google.
"""

import os
from typing import Union, Optional, Dict, Any
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI


class CompletionResponse(BaseModel):
    """Pydantic schema for structured LLM responses."""
    answer: str = Field(description="The main answer to the user's question")
    reasoning: str = Field(description="Brief explanation of the reasoning behind the answer")


# Cache for initialized LLM instances
_llm_cache: Dict[str, Any] = {}


def _get_llm(model: str = "gpt-4.1-nano-2025-04-14", temperature: float = 0, **kwargs):
    """
    Get or create a LangChain ChatOpenAI client with LiteLLM proxy configuration.
    
    Args:
        model: The model to use (e.g., "gpt-4.1-nano-2025-04-14")
        temperature: Temperature setting for the model (default: 0)
        **kwargs: Additional parameters to pass to ChatOpenAI
        
    Returns:
        ChatOpenAI instance configured for the specified model
    """
    cache_key = f"{model}_{temperature}"
    
    if cache_key not in _llm_cache:
        proxy_url = os.getenv("LITELLM_PROXY_URL", "http://localhost:4000")
        api_key = os.getenv("LITELLM_API_KEY") or os.getenv("LITELLM_MASTER_KEY", "sk-1234")
        
        _llm_cache[cache_key] = ChatOpenAI(
            base_url=proxy_url,
            api_key=api_key,
            model=model,
            temperature=temperature,
            **kwargs
        )
    
    return _llm_cache[cache_key]


def get_completion(
    prompt: str, 
    model: str = "gpt-4.1-nano-2025-04-14",
    temperature: float = 0,
    use_structured_output: bool = True,
    **kwargs
) -> Union[str, CompletionResponse]:
    """
    Get a completion from the LLM via LiteLLM proxy.
    
    Args:
        prompt: The input prompt for the LLM
        model: The model to use (default: "gpt-4.1-nano-2025-04-14")
        temperature: Temperature setting for the model (default: 0)
        use_structured_output: Whether to return structured Pydantic object (default: True)
        **kwargs: Additional parameters to pass to the model
        
    Returns:
        CompletionResponse object if use_structured_output=True, otherwise string
        
    Raises:
        Exception: If the LLM request fails
    """
    try:
        llm = _get_llm(model=model, temperature=temperature, **kwargs)
        
        if use_structured_output:
            structured_llm = llm.with_structured_output(CompletionResponse)
            response = structured_llm.invoke(prompt)
            return response
        else:
            response = llm.invoke(prompt)
            return response.content
            
    except Exception as e:
        raise Exception(f"LLM completion failed: {str(e)}")


def get_completion_json(
    prompt: str,
    model: str = "gpt-4.1-nano-2025-04-14",
    temperature: float = 0,
    **kwargs
) -> dict:
    """
    Get a completion as a JSON dictionary.
    
    Args:
        prompt: The input prompt for the LLM
        model: The model to use (default: "gpt-4.1-nano-2025-04-14")
        temperature: Temperature setting for the model (default: 0)
        **kwargs: Additional parameters to pass to the model
        
    Returns:
        Dictionary representation of the CompletionResponse
        
    Raises:
        Exception: If the LLM request fails
    """
    try:
        llm = _get_llm(model=model, temperature=temperature, **kwargs)
        structured_llm = llm.with_structured_output(CompletionResponse)
        response = structured_llm.invoke(prompt)
        return response.model_dump()
    except Exception as e:
        raise Exception(f"LLM completion failed: {str(e)}")


def get_completion_string(
    prompt: str,
    model: str = "gpt-4.1-nano-2025-04-14",
    temperature: float = 0,
    **kwargs
) -> str:
    """
    Get a completion as a plain string (no structured output).
    
    Args:
        prompt: The input prompt for the LLM
        model: The model to use (default: "gpt-4.1-nano-2025-04-14")
        temperature: Temperature setting for the model (default: 0)
        **kwargs: Additional parameters to pass to the model
        
    Returns:
        String response from the LLM
        
    Raises:
        Exception: If the LLM request fails
    """
    return get_completion(prompt, model=model, temperature=temperature, use_structured_output=False, **kwargs)


if __name__ == "__main__":
    # Example usage patterns
    test_prompt = "What is the capital of France? Please provide a confident answer."
    
    print("=== Structured Output Example ===")
    try:
        structured_response = get_completion(test_prompt)
        print(f"Answer: {structured_response.answer}")
        print(f"Reasoning: {structured_response.reasoning}")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n=== JSON Dictionary Example ===")
    try:
        json_response = get_completion_json(test_prompt)
        print(json_response)
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n=== String Output Example ===")
    try:
        string_response = get_completion_string(test_prompt)
        print(string_response)
    except Exception as e:
        print(f"Error: {e}")