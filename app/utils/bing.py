import httpx
import random
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

from app.utils.config import CONFIG_SETTINGS, LOGGER_MAIN

import logging

logger = logging.getLogger(f"{LOGGER_MAIN}.{__name__}")

BING_API_ENDPOINT = "https://api.bing.microsoft.com"

BING_API_KEYS = CONFIG_SETTINGS.keys.bing_api_keys

LOW_CARBON_POLICY = "环保政策"
LOW_CARBON_NATION_POLICY = "国家环保政策"

FILTER_KEYWORDS = [
    "绿色",
    "低碳",
    "节能",
    "减排",
    "环保",
    "碳中和",
    "能源",
    "资源",
    "生态",
    "环境",
]

"""最多分析20个网页"""
TRIAL_LIMIT = 20

FALLBACK_IMG = " https://green-img.f2ee.com/system/fallback.jpg"


async def is_url_image(img_url):
    try:
        image_formats = ("image/png", "image/jpeg", "image/jpg", "image/webp")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36"
        }
        async with httpx.AsyncClient() as client:
            r = await client.head(img_url, headers=headers)

        if r.status_code in [301, 302]:
            return await is_url_image(r.headers["Location"])
        return r.headers.get("content-type") in image_formats
    except Exception:
        logger.error(f"Failed to check if {img_url} is an image")
        return False


async def get_img_list(query: str, cnt: int = 1):
    """免费的API每秒3次，每月1000次。本函数调用的几率很小，基本能从本地获取图片"""
    mkt = "zh-CN"
    params = {"q": query, "mkt": mkt, "minWidth": 400, "maxWidth": 1800}
    headers = {"Ocp-Apim-Subscription-Key": random.choice(BING_API_KEYS)}

    # 发起 GET 请求获取图片搜索结果
    async with httpx.AsyncClient() as client:
        response = await client.get(
            BING_API_ENDPOINT + "/v7.0/images/search", headers=headers, params=params
        )

    # 初始化结果列表
    result_urls = []
    # 从 JSON 数据中提取图片 URL 列表
    urls = [img.get("contentUrl", "") for img in response.json().get("value", [])]

    # 遍历 urls，直到获得足够的有效图片 URL 或 urls 列表被消耗完
    trial = 0
    for url in urls:
        trial += 1
        if len(result_urls) >= cnt or trial >= TRIAL_LIMIT:
            break
        if url not in result_urls and await is_url_image(url):
            result_urls.append(url)

    # 如果结果列表中的 URL 数量不足，则用备用图片链接填充列表
    result_urls.extend([FALLBACK_IMG] * (cnt - len(result_urls)))
    # 返回图片链接列表
    return result_urls


async def get_img(query: str):
    """免费的API每秒3次，每月1000次。为了突破这个限制，可以设置多个key。"""
    img_list = await get_img_list(query, cnt=1)
    return img_list[0]


async def search(query: str):
    params = {"q": query, "mkt": "zh-CN"}
    headers = {"Ocp-Apim-Subscription-Key": random.choice(BING_API_KEYS)}

    async with httpx.AsyncClient() as client:
        response = await client.get(
            BING_API_ENDPOINT + "/v7.0/search", headers=headers, params=params
        )

    web_pages = [
        page
        for page in response.json().get("webPages", {}).get("value", [])
        if not page.get("url", "").endswith(".pdf")
    ]
    return web_pages


async def gov_search(query: str):
    """搜索政府网站"""
    web_pages = await search(query)
    web_pages = [page for page in web_pages if "gov.cn" in page.get("url", "")]
    return web_pages


async def search_policy_content(query: str):
    web_pages = await gov_search(query)
    result_list = []

    def _contains(line: str):
        for keyword in FILTER_KEYWORDS:
            if keyword in line:
                return True
        return False

    trial = 0
    # 目前的提示词不能很好的输出多条政策，需要暂时只搜索一条
    result_limit = 1
    for item in web_pages:
        if trial >= TRIAL_LIMIT or len(result_list) >= result_limit:
            break
        trial += 1
        result_dict = {"title": item.get("name", "")}
        # 提取文本
        text_content = await extract_text_from_url_with_playwright_firefox(
            item.get("url", "")
        )
        # 提取包含特定关键词的句子
        sentences = [
            sentence for sentence in text_content.split("。") if _contains(sentence)
        ][:10]
        filtered_text_content = "。".join(sentences)
        # 存储文本内容（不能过长）
        result_dict["content"] = (
            filtered_text_content
            if len(filtered_text_content) < 500
            else filtered_text_content[:500]
        )
        # 将信息字典添加到结果列表中（内容必须足够多）
        if len(result_dict["content"]) > 50:
            result_list.append(result_dict)
    return result_list


async def extract_text_from_url_with_playwright_firefox(url):
    try:
        async with async_playwright() as p:
            browser = await p.firefox.launch()
            page = await browser.new_page()
            await page.goto(url, timeout=10 * 1000)
            # 等待页面加载完成（根据需要调整等待时间）
            await page.wait_for_load_state("domcontentloaded")
            # 获取页面内容
            page_content = await page.content()
            # 使用 BeautifulSoup 解析 HTML 内容并提取文本
            soup = BeautifulSoup(page_content, "html.parser")
            paragraphs = soup.find_all("p")
            text_content = " ".join([paragraph.get_text() for paragraph in paragraphs])
            await browser.close()

        return text_content

    except Exception as e:
        logger.error(f"从URL提取文本时发生错误: {e}")
        return "《“十四五”节能减排综合工作方案》习近平新时代中国特色社会主义思想为指导，全面贯彻党的十九大和十九届历次全会精神，深入贯彻习近平生态文明思想，坚持稳中求进工作总基调，立足新发展阶段，完整、准确、全面贯彻新发展理念，构建新发展格局，推动高质量发展，完善实施能源消费强度和总量双控（以下称能耗双控）、主要污染物排放总量控制制度，组织实施节能减排重点工程，进一步健全节能减排政策机制，推动能源利用效率大幅提高、主要污染物排放总量持续减少，实现节能降碳减污协同增效、生态环境质量持续改善，确保完成“十四五”节能减排目标，为实现碳达峰、碳中和目标奠定坚实基础。"


async def get_policy_url(query: str):
    web_pages = await gov_search(query)
    # 获取网页的 URL 作为 policy_url
    policy_url = random.choice(web_pages).get("url", "")
    return policy_url
