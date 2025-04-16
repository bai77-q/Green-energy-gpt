import qianfan
from fastapi.security import OAuth2PasswordBearer
from openai import AsyncOpenAI
import random
from app.utils.config import CONFIG_SETTINGS, OPENAI_URL

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

OPENAI_KEYS = CONFIG_SETTINGS.keys.openai_api_keys
QIANFAN_API_KEY = CONFIG_SETTINGS.keys.qianfan_api_key
QIANFAN_API_SECRET = CONFIG_SETTINGS.keys.qianfan_secret_key

_open_ai_clients = [AsyncOpenAI(api_key=k, base_url=OPENAI_URL) for k in OPENAI_KEYS]
chat_comp = qianfan.ChatCompletion(ak=QIANFAN_API_KEY, sk=QIANFAN_API_SECRET)


def get_ernie_chat():
    return chat_comp


def get_async_openai_client():
    return random.choice(_open_ai_clients)
