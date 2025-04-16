import base64
import json
from io import BytesIO

import httpx
import lancedb
from openai import AsyncOpenAI
from fastapi import Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
import random

from . import database
from . import bing, config, cache
from . import gpt

from playwright.async_api import async_playwright
import logging

logger = logging.getLogger(f"{config.LOGGER_MAIN}.{__name__}")


async def get_random_intro_img(
    business: str,
    category: str,
    db: AsyncSession = Depends(database.get_db),
):
    async def _get_image():
        query = select(database.IntroImage)
        query = query.where(database.IntroImage.business == business)
        if category != "其他" and business != "空气压缩":
            # 如果类别不是 "其他" 并且业务不是 "空气压缩"，添加一个过滤条件，限制类别匹配
            query = query.where(database.IntroImage.category == category)
        query = query.order_by(func.random()).limit(1)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    image = await _get_image()
    if image:
        return image.url
    url = await bing.get_img(f"{business} {category}")
    return url


async def capture_screenshot(url: str) -> bytes:
    async with async_playwright() as p:
        browser = await p.firefox.launch()
        page = await browser.new_page()
        await page.goto(url)
        # 等待页面加载完成，可以根据实际情况调整等待时间
        await page.wait_for_load_state("load")
        # 截取页面截图并获取二进制流
        screenshot_binary = await page.screenshot(type="jpeg", quality=80)
        await browser.close()
    return screenshot_binary


async def capture_and_save(url: str, path: str):
    async with async_playwright() as p:
        browser = await p.firefox.launch()
        page = await browser.new_page()
        await page.goto(url)
        # 等待页面加载完成，可以根据实际情况调整等待时间
        await page.wait_for_load_state("load")
        # 截取页面截图
        await page.screenshot(type="jpeg", quality=70, path=path)
        await browser.close()


async def _search_policy_img(db: AsyncSession, table, condition):
    res = await db.execute(
        select(table.image_url).where(*condition).order_by(func.random()).limit(1)
    )
    return res.scalar_one_or_none()


async def get_image_url_from_local_policy(
    province: str,
    city: str,
    business: str,
    category: str,
    db: AsyncSession,
):
    # 定义查询条件
    query_filters = [
        database.LocalPolicy.policy_province == province,
        database.LocalPolicy.policy_city == city,
        database.LocalPolicy.policy_business == business,
    ]
    if category != "其他":
        query_filters.append(database.LocalPolicy.policy_category == category)
    return await _search_policy_img(db, database.LocalPolicy, query_filters)


async def get_image_url_from_national_policy(
    business: str,
    category: str,
    db: AsyncSession,
):
    # 定义查询条件
    query_filters = [
        database.NationalPolicy.policy_business == business,
    ]
    if category != "其他":
        query_filters.append(database.NationalPolicy.policy_category == category)

    return await _search_policy_img(db, database.NationalPolicy, query_filters)


async def get_image_by_policy_url(url: str) -> str:
    # 检查COS是否有
    image_str = base64.b64encode(str.encode(url, encoding="utf-8"))
    image_name = image_str.decode("utf-8") + ".jpeg"
    image_url = "https://green-img.f2ee.com/policy/" + image_name
    if await bing.is_url_image(image_url):
        return image_url
    # 否则需要手动截图
    try:
        image_binary = await capture_screenshot(url)
        if len(image_binary) / 1024 < 30:
            # too small
            raise Exception("too small image")
        # 保存在COS
        from app.utils import cos

        cos.upload_image_bytes_to_cos(image_binary, "policy/" + image_name)
        return image_url
    except Exception as e:
        logger.error(f"Failed to capture screenshot for {url}. {e}")
        return "https://green-img.f2ee.com/default/policy-1.jpg"


async def search_image_urls(tech: str, openai: AsyncOpenAI):
    try:
        embedding = cache.get_embedding_in_cache(tech)
        if embedding is None:
            embedding = await gpt.get_gpt_embedding(tech, openai)
            cache.add_embedding_in_cache(tech, embeddings=json.dumps(embedding))
        else:
            embedding = json.loads(embedding)

        with await lancedb.connect_async(config.LANCE_DB_URL) as async_db:
            tbl = await async_db.open_table("tech_images")
            result = await tbl.vector_search(embedding).limit(1).to_pandas()
            image_urls = result["image_urls"].iloc[0]
            random_image_url = random.choice(image_urls)
            return random_image_url
    except Exception as e:
        logger.error(f"Failed to search image urls for {tech}. {e}")
    return None


async def get_image_bytes_by_url(url: str) -> BytesIO:
    import io

    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return io.BytesIO(response.content)
