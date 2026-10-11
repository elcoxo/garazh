import os

from pydantic_ai.models import Model
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.models.groq import GroqModel
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.providers.groq import GroqProvider

from models.enums import AIProvider
from settings import get_settings

cfg = get_settings()

NOT_CHAT_MARKERS = ('whisper', 'guard', 'tts', 'orpheus', 'image', 'audio')


def build_model(provider: AIProvider, name: str) -> Model:
    if provider == AIProvider.GEMINI:
        return GoogleModel(name, provider=GoogleProvider(api_key=cfg.gemini_api_key))
    return GroqModel(name, provider=GroqProvider(api_key=cfg.groq_api_key))


async def _list_model_names(provider: AIProvider) -> list[str]:
    names = []
    if provider == AIProvider.GEMINI:
        client = GoogleProvider(api_key=cfg.gemini_api_key).client
        async for model in await client.aio.models.list():
            if 'generateContent' in (model.supported_actions or []):
                names.append(model.name.removeprefix('models/'))
        return names
    response = await GroqProvider(api_key=cfg.groq_api_key).client.models.list()
    for model in response.data:
        names.append(model.id)
    return names


async def find_available_model(provider: AIProvider, gone_name: str) -> str | None:
    """Ближайшая по имени к отозванной доступная чат-модель провайдера"""
    candidates = []
    for name in await _list_model_names(provider):
        if name == gone_name or any(marker in name for marker in NOT_CHAT_MARKERS):
            continue
        candidates.append(name)
    return max(candidates, key=lambda name: len(os.path.commonprefix([name, gone_name])), default=None)
