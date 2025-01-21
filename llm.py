import os
from abc import ABC, abstractmethod
from dotenv import load_dotenv
from openai import OpenAI
from google import genai
from log import Logger

logger = Logger.get_logger()

# Registry to hold provider information
PROVIDERS = {}

def register_provider(name, constructor, env_var):
    """
    Register a provider with its constructor and associated environment variable for the API key.
    """
    PROVIDERS[name.lower()] = {"constructor": constructor, "env_var": env_var}

def format_messages(messages):
    """
    Replace literal "\n" with actual newlines in a list of message dictionaries.
    """
    formatted = []
    for msg in messages:
        formatted.append({
            "role": msg.get("role"),
            "content": msg.get("content", "").replace("\\n", "\n")
        })
    return formatted

def format_response_content(content):
    """
    Replace literal "\n" with actual newlines in a string.
    """
    return content.replace("\\n", "\n")

class LLM(ABC):
    @abstractmethod
    def chat(self, messages):
        pass

class OpenAiLLM(LLM):
    def __init__(self, api_key, model="gpt-4o", **kwargs):
        self.client = OpenAI(api_key=api_key, **kwargs)
        self.model = model

    def chat(self, messages):
        formatted_messages = format_messages(messages)
        logger.info(f"LLM request (OpenAI, model={self.model}): {formatted_messages}")

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages
        )

        formatted_choices = []
        for choice in response.choices:
            msg = choice.message
            formatted_choices.append({
                "role": msg.role,
                "content": format_response_content(msg.content)
            })
        logger.info(f"LLM response (OpenAI): {formatted_choices}")

        output_messages = []
        for choice in response.choices:
            msg = choice.message
            output_messages.append({
                "role": msg.role,
                "content": msg.content
            })
        return output_messages

class GoogleGeminiLLM(LLM):
    def __init__(self, api_key, vertexai=False, project=None, location="us-central1", model="gemini-2.0-flash-exp", **kwargs):
        if vertexai:
            self.client = genai.Client(vertexai=True, project=project, location=location)
        else:
            self.client = genai.Client(api_key=api_key)
        self.model = model

    def chat(self, messages):
        formatted_messages = format_messages(messages)
        logger.info(f"LLM request (GoogleGemini, model={self.model}): {formatted_messages}")

        last_user_msg = None
        for msg in reversed(messages):
            if msg["role"] == "user":
                last_user_msg = msg["content"]
                break
        if last_user_msg is None:
            raise ValueError("No user message found in the conversation.")

        response = self.client.models.generate_content(
            model=self.model,
            contents=last_user_msg
        )

        formatted_response_text = format_response_content(response.text)
        logger.info(f"LLM response (GoogleGemini): {formatted_response_text}")

        return [{"role": "assistant", "content": response.text}]

# Register default providers
register_provider("openai", OpenAiLLM, "OPENAI_API_KEY")
register_provider("google", GoogleGeminiLLM, "GOOGLE_API_KEY")

def get_llm(provider="openai", api_key='', model="gpt-4o", **kwargs):
    """
    Factory method to get an LLM instance for a given provider.
    It attempts to load the API key from a .env file if not provided.
    """
    load_dotenv()  # Load environment variables from .env file
    provider = provider.lower()

    if provider not in PROVIDERS:
        raise ValueError(f"Unsupported provider: {provider}")

    provider_info = PROVIDERS[provider]

    # If no API key provided, attempt to load from environment variables
    if not api_key:
        api_key = os.getenv(provider_info["env_var"], "")

    # If still no API key, throw an error
    if not api_key:
        raise ValueError(f"No API key provided for provider '{provider}' and not found in environment.")

    constructor = provider_info["constructor"]
    return constructor(api_key=api_key, model=model, **kwargs)
