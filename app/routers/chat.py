from fastapi import APIRouter, Depends, Body
from app.utils import gpt, prompts, database, auth, config
from app.models import models
from app import dependencies
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import StreamingResponse

from app.utils.add_operation import record_user_operation
import uuid

from app.utils import wiki

from app.utils.config import (
    CHAT_OP_TYPE,
    CHAT_SUBTYPE,
    ECO_SUBTYPE,
    SUG_SUBTYPE,
    WIKI_SUBTYPE,
    ENERGY_SUBTYPE,
)

router = APIRouter()

chat_temperature = 0.7


async def log_operation(
    op_type: str, sub_type: str, db: AsyncSession, current_user: database.UserLogin
):
    if current_user.account_type in [
        config.SVIP_LEVEL,
        config.SUB_SVIP_LEVEL,
        config.VIP_LEVEL,
    ]:
        await auth.check_expired(db, current_user)
        await auth.check_chat_limit(db, current_user)
    # 生成 UUID 作为唯一标识符
    unique_key = "chat-" if op_type == CHAT_OP_TYPE else "proposal-" + uuid.uuid4().hex
    # 调用 record_user_operation 函数记录用户操作
    await record_user_operation(
        op_type=op_type,
        unique_key=unique_key,
        user_id=current_user.id,
        sub_type=sub_type,
    )


@router.post("/v2/chat", tags=[config.API_CHAT])
async def chat(
    content: Annotated[models.ChatRequestModel, Body()],
    gpt_client=Depends(dependencies.get_async_openai_client),
    current_user: database.UserLogin = Depends(auth.get_current_non_regular),
    db: AsyncSession = Depends(database.get_db),
):
    """聊天功能"""
    await log_operation(CHAT_OP_TYPE, CHAT_SUBTYPE, db, current_user)

    prompt = prompts.get_chat_prompt(content.chat_context, content.question)
    result = gpt.get_gpt_stream_result(
        prompt, gpt_client, model=gpt.GPT4o_MODEL, temperature=chat_temperature
    )
    return StreamingResponse(result, media_type="text/html")


@router.post("/eco_eval", tags=[config.API_CHAT])
async def eco_eval(
    keywords: Annotated[
        str,
        Body(
            description="包含地区、行业和需求的关键词拼接",
            example="四川省；成都市；建筑行业；学校建筑；小于2万平方；建筑施工",
        ),
    ],
    gpt_client=Depends(dependencies.get_async_openai_client),
    current_user: database.UserLogin = Depends(auth.get_current_non_regular),
    db: AsyncSession = Depends(database.get_db),
):
    """经济系概估"""
    await log_operation(CHAT_OP_TYPE, ECO_SUBTYPE, db, current_user)

    prompt = prompts.get_eco_eval_prompt(keywords)
    result = gpt.get_gpt_stream_result(
        prompt, gpt_client, model=gpt.GPT4o_MODEL, temperature=chat_temperature
    )
    return StreamingResponse(result, media_type="text/html")


@router.post("/energy_suggestion", tags=[config.API_CHAT])
async def energy_suggestion(
    company: str = Body(
        ..., description="公司名称", example="四川天微电子股份有限公司"
    ),
    ernie_chat=Depends(dependencies.get_ernie_chat),
    current_user: database.UserLogin = Depends(auth.get_current_non_regular),
    db: AsyncSession = Depends(database.get_db),
):
    """能源综合建议"""
    await log_operation(CHAT_OP_TYPE, SUG_SUBTYPE, db, current_user)

    prompt = prompts.get_energy_suggestion(company)
    result = gpt.get_ernie_stream_result(prompt, ernie_chat, model=gpt.ERNIE)
    return StreamingResponse(result, media_type="text/html")


@router.post("/wiki_chat", tags=[config.API_CHAT])
async def wiki_chat(
    content: Annotated[models.ChatRequestModel, Body()],
    gpt_client=Depends(dependencies.get_async_openai_client),
    current_user: database.UserLogin = Depends(auth.get_current_non_regular),
    db: AsyncSession = Depends(database.get_db),
    openai: dependencies.AsyncOpenAI = Depends(dependencies.get_async_openai_client),
):
    """产品百科聊天"""
    await log_operation(CHAT_OP_TYPE, WIKI_SUBTYPE, db, current_user)
    wiki_content = await wiki.search_wiki(content.question, openai)
    prompt = prompts.get_wiki_prompt(
        content.chat_context, content.question, wiki_content
    )
    result = gpt.get_gpt_stream_result(
        prompt, gpt_client, model=gpt.GPT4o_MINI_MODEL, temperature=chat_temperature
    )
    return StreamingResponse(result, media_type="text/html")


@router.post("/energy_analysis", tags=[config.API_CHAT])
async def energy_analysis(
    keywords: Annotated[
        str,
        Body(
            description="包含能耗需求分析的关键词拼接",
            example="地区：重庆；制冷面积：26500平方米；制冷方式：水冷机组独立空调；用能人数：1460人；供热方式：独立空调；日常管理：人工开关机；年消耗量：2150000千瓦时。",
        ),
    ],
    gpt_client=Depends(dependencies.get_async_openai_client),
    current_user: database.UserLogin = Depends(auth.get_current_non_regular),
    db: AsyncSession = Depends(database.get_db),
):
    """能耗需求分析"""
    await log_operation(CHAT_OP_TYPE, ENERGY_SUBTYPE, db, current_user)

    prompt = prompts.get_energy_analysis_prompt(keywords)
    result = gpt.get_gpt_stream_result(
        prompt, gpt_client, model=gpt.GPT4o_MODEL, temperature=chat_temperature
    )
    return StreamingResponse(result, media_type="text/html")
