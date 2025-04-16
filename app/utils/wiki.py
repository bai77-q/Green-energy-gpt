import json

from app.utils.config import CONFIG_SETTINGS, INNER_API_KEY, LOGGER_MAIN
from app.utils import cache, gpt
import httpx
from openai import AsyncOpenAI
import logging

logger = logging.getLogger(f"{LOGGER_MAIN}.{__name__}")

wiki_url = CONFIG_SETTINGS.wiki.url
TIME_OUT = 10


async def search_wiki(query: str, openai: AsyncOpenAI) -> str:
    embedding = cache.get_wiki_in_cache(query)
    if embedding is None:
        embedding = await gpt.get_gpt_embedding(query, openai)
        cache.add_wiki_in_cache(query, wiki=json.dumps(embedding))
    else:
        embedding = json.loads(embedding)
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{wiki_url}/wiki/search?api_key={INNER_API_KEY}",
                json={"query": query, "query_embedding": embedding},
                timeout=TIME_OUT,
            )
            return response.json()["wiki"]
        except Exception as e:
            logger.error(f"Failed to search wiki: {e}")
            return ""


async def add_wiki(ad_id: int, business: str, category: str, tech: str, ad_info: str):
    async with httpx.AsyncClient() as client:
        await client.post(
            f"{wiki_url}/wiki/create?api_key={INNER_API_KEY}",
            json={
                "ad_id": ad_id,
                "business": business,
                "category": category,
                "tech": tech,
                "ad_info": ad_info,
            },
            timeout=TIME_OUT * 1.5,
        )
