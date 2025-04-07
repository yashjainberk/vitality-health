import os
import time
from typing import Dict, List, Any, Optional, Union
from openai import OpenAI
import tiktoken

from agent_marketplace.config import get_settings
from agent_marketplace.schemas.agents import Context

class OpenAILLMProvider:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.settings = get_settings()
        self.api_key = self.config.get("api_key") or self.settings.openai_api_key or os.getenv("OPENAI_API_KEY")
        self.model = self.config.get("model", "gpt-4o")
        self.client = OpenAI(api_key=self.api_key)
        self.max_tokens_per_request = self.config.get("max_tokens_per_request", 25000)  # Lower than the 30k TPM limit
        
    def _count_tokens(self, messages: List[Dict[str, str]]) -> int:
        """Count the number of tokens in the messages"""
        try:
            encoding = tiktoken.encoding_for_model(self.model)
        except KeyError:
            # Fallback for models not explicitly supported by tiktoken
            encoding = tiktoken.get_encoding("cl100k_base")
            
        num_tokens = 0
        for message in messages:
            # Add tokens for each message
            num_tokens += 4  # Every message follows <im_start>{role/name}\n{content}<im_end>\n
            for key, value in message.items():
                if key == "content" and value:
                    num_tokens += len(encoding.encode(value))
                elif key == "role":
                    num_tokens += len(encoding.encode(value))
                    
        num_tokens += 2  # Every reply is primed with <im_start>assistant
        return num_tokens
    
    def _truncate_context(self, messages: List[Dict[str, str]], max_tokens: int) -> List[Dict[str, str]]:
        """Truncate conversation history to fit within token limits"""
        # Always keep system and current user message
        system_message = None
        user_message = None
        
        # Extract system and most recent user message
        history_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg
            elif msg["role"] == "user":
                user_message = msg
                # Add previous user messages to history
                if user_message != msg:
                    history_messages.append(msg)
            else:
                history_messages.append(msg)
        
        # Start with required messages
        result = []
        if system_message:
            result.append(system_message)
        if user_message:
            result.append(user_message)
            
        # Calculate tokens used by required messages
        token_count = self._count_tokens(result)
        
        # Add historical messages until we approach the token limit
        # Start from the most recent history (reversed)
        for msg in reversed(history_messages):
            msg_tokens = self._count_tokens([msg])
            if token_count + msg_tokens < max_tokens:
                # Insert historical message at position 1 (after system, before current user message)
                # This keeps the chronological order intact
                insert_pos = 1 if system_message else 0
                result.insert(insert_pos, msg)
                token_count += msg_tokens
            else:
                break
                
        return result
        
    def generate(self, prompt: str, system_prompt: str = "", context: Context = None, 
                 tools: Optional[List[Dict[str, Any]]] = None, 
                 tool_choice: Optional[Union[str, Dict[str, Any]]] = "auto") -> Dict[str, Any]:
        """
        Generate text using LLM with optional tool support
        
        Args:
            prompt (str): The user prompt to generate a response for
            system_prompt (str, optional): System prompt to guide model behavior
            context (Context, optional): Conversation history and context
            tools (List[Dict[str, Any]], optional): List of tools in OpenAI format for function calling
            tool_choice (Union[str, Dict[str, Any]], optional): Tool choice parameter - "auto", "none", or specific tool config
            
        Returns:
            Dict[str, Any]: Dictionary containing:
                - content (str): The generated text response
                - tool_calls (Optional[List]): Tool call information if tools were used
                
        Raises:
            ValueError: If API key is not provided or API call fails
        """
        if not self.api_key:
            raise ValueError("API key not provided")
            
        # Prepare messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # Add context if provided
        if context:
            for msg in context.history:
                messages.append({"role": msg.role, "content": msg.content})
                
        # Add current prompt
        messages.append({"role": "user", "content": prompt})

        # Check token count and truncate if needed
        estimated_tokens = self._count_tokens(messages)
        if estimated_tokens > self.max_tokens_per_request:
            messages = self._truncate_context(messages, self.max_tokens_per_request)

        # Call OpenAI API using the official client
        try:
            # Prepare API call parameters
            api_params = {
                "model": self.model,
                "messages": messages,
                "temperature": self.config.get("temperature", 0.7),
                "max_tokens": self.config.get("max_tokens", 1000),
            }
            
            # Add tools and tool_choice if provided
            if tools:
                api_params["tools"] = tools
                api_params["tool_choice"] = tool_choice
            
            # Add retry with backoff for rate limiting
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = self.client.chat.completions.create(**api_params)
                    return {
                        "content": response.choices[0].message.content,
                        "tool_calls": response.choices[0].message.tool_calls
                    }
                except Exception as e:
                    error_str = str(e)
                    # Handle rate limit errors specifically
                    if "rate_limit_exceeded" in error_str and attempt < max_retries - 1:
                        # Exponential backoff: 1s, 2s, 4s...
                        backoff_time = 2 ** attempt
                        time.sleep(backoff_time)
                        continue
                    else:
                        # Re-raise the exception if we've exhausted retries or it's not a rate limit error
                        raise
            
        except Exception as e:
            raise ValueError(f"OpenAI API error: {str(e)}") 
