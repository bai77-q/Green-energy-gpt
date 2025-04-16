from datetime import datetime, timedelta, timezone

import httpx
from app.utils.config import Wechat_Name, CONFIG_SETTINGS, INNER_API_KEY


async def record_user_operation(
    op_type: str,
    unique_key: str,
    user_id: str,
    sub_type="",
    ext="",
):
    # 如果 userId 是 Wechat_Name，则跳过记录操作
    if user_id == Wechat_Name:
        return

    headers = {"Content-Type": "application/json"}

    # 获取当前时间并转换为上海时间
    shanghai_now = datetime.now(timezone(timedelta(hours=8))).strftime(
        "%Y-%m-%dT%H:%M:%S"
    )
    payload = {
        "ext": ext,
        "recordTime": shanghai_now,
        "subType": sub_type,
        "type": op_type,
        "uniqueKey": unique_key,
        "userId": user_id,
    }
    api_endpoint = f"{CONFIG_SETTINGS.gate.add_operate_url}?apiKey={INNER_API_KEY}"
    async with httpx.AsyncClient() as client:
        await client.post(api_endpoint, json=payload, headers=headers, timeout=5)
