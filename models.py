
# from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.settings import ModelSettings

import os
from dotenv import load_dotenv

load_dotenv(override=True)


# Point at your vLLM server:
provider = OpenAIProvider(
    base_url=os.environ["LOCAL_CHAT_MODEL_BASE_URL"],
    api_key=os.environ["LOCAL_CHAT_MODEL_API_KEY"],
)

# Tell PydanticAI which exact model name vLLM is serving:

agent_model = os.environ.get("MODEL_NAME", 'gpt-4o-mini')
# agent_model = OpenAIModel(os.environ["LOCAL_CHAT_MODEL_NAME"], provider=provider)


model_settings = ModelSettings(
    max_tokens=8000,
    temperature=0.0,
    stream=True
)