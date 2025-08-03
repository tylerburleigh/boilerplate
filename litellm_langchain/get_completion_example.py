"""
LiteLLM + LangChain Integration with Structured Output

This module provides a unified interface for LLM completions using LiteLLM proxy
with LangChain's ChatOpenAI, featuring structured JSON output via Pydantic schemas
and the o4-mini model.
"""

import os
from typing import Union
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI


class CompletionResponse(BaseModel):
    """Pydantic schema for structured LLM responses."""
    answer: str = Field(description="The main answer to the user's question")
    reasoning: str = Field(description="Brief explanation of the reasoning behind the answer")


# Module-level LLM initialization for efficiency
def _initialize_llm():
    """Initialize the LangChain ChatOpenAI client with LiteLLM proxy configuration."""
    proxy_url = os.getenv("LITELLM_PROXY_URL", "http://localhost:4000")
    api_key = os.getenv("LITELLM_MASTER_KEY", "sk-1234")  # Default for local development
    
    return ChatOpenAI(
        base_url=proxy_url,
        api_key=api_key,
        model="o4-mini"
    )


# Initialize LLM and structured output version
llm = _initialize_llm()
structured_llm = llm.with_structured_output(CompletionResponse)


def get_completion(prompt: str, use_structured_output: bool = True) -> Union[str, CompletionResponse]:
    """
    Get a completion from the LLM via LiteLLM proxy.
    
    Args:
        prompt: The input prompt for the LLM
        use_structured_output: Whether to return structured Pydantic object (default: True)
        
    Returns:
        CompletionResponse object if use_structured_output=True, otherwise string
        
    Raises:
        Exception: If the LLM request fails
    """
    try:
        if use_structured_output:
            response = structured_llm.invoke(prompt)
            return response
        else:
            response = llm.invoke(prompt)
            return response.content
            
    except Exception as e:
        raise Exception(f"LLM completion failed: {str(e)}")


def get_completion_json(prompt: str) -> dict:
    """
    Get a completion as a JSON dictionary.
    
    Args:
        prompt: The input prompt for the LLM
        
    Returns:
        Dictionary representation of the CompletionResponse
        
    Raises:
        Exception: If the LLM request fails
    """
    try:
        response = structured_llm.invoke(prompt)
        return response.model_dump()
    except Exception as e:
        raise Exception(f"LLM completion failed: {str(e)}")


def get_completion_string(prompt: str) -> str:
    """
    Get a completion as a plain string (no structured output).
    
    Args:
        prompt: The input prompt for the LLM
        
    Returns:
        String response from the LLM
        
    Raises:
        Exception: If the LLM request fails
    """
    return get_completion(prompt, use_structured_output=False)


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