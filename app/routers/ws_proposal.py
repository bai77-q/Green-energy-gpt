import json

from app.common import policy as policy_util
from app.utils import gpt, prompts, bing, database, auth
from app.utils import cache
from app import dependencies
from app.proposal import record
from app.cases import manage_cases
from app.ads import ads

from fastapi import APIRouter, Depends, Query, WebSocket

from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


async def _auth_helper(token: str, db: AsyncSession):
    current_user = await auth.get_current_user(db, token)
    record.check_record_by_id(current_user.id)
    proposal = cache.CachedProposal(
        **json.loads(cache.get_record_in_cache(current_user.id))
    )
    return current_user, proposal


async def _gpt_ws_helper(
    websocket: WebSocket, prompt, gpt_client, update_cache_func=None
):
    async for txt in gpt.get_gpt_stream_result(
        prompt, gpt_client, update_cache_func=update_cache_func
    ):
        await websocket.send_text(txt)


@router.websocket("/proposal/ws/intro_txt")
async def get_intro_txt_ws(
    websocket: WebSocket,
    token: str = Query(...),
    db: AsyncSession = Depends(database.get_db),
    gpt_client=Depends(dependencies.get_async_openai_client),
):
    """根据行业和子分类获得行业介绍（注意：这是流式文本）"""
    current_user, proposal = await _auth_helper(token, db)
    await websocket.accept()
    prompt = prompts.intro_prompt(proposal.business, proposal.category)

    update_cache_func = lambda intro_text: cache.add_proposal_intro_text_in_cache(
        current_user.id, intro_text
    )

    try:
        await _gpt_ws_helper(
            websocket, prompt, gpt_client, update_cache_func=update_cache_func
        )
    finally:
        await websocket.close()


async def _policy_helper(
    websocket: WebSocket,
    token: str,
    db: AsyncSession,
    gpt_client,
    is_nation: bool = False,
):
    current_user, proposal = await _auth_helper(token, db)
    await websocket.accept()

    if is_nation:
        policies = await policy_util.fetch_nation_policy(
            db, proposal.business, current_user.account_type
        )
        query = (
            f"{proposal.business} {proposal.category} {bing.LOW_CARBON_NATION_POLICY}"
        )
    else:
        policies = await policy_util.fetch_local_policy(
            db,
            proposal.business,
            proposal.province,
            proposal.city,
            current_user.account_type,
        )
        query = f"{proposal.province} {proposal.city} {proposal.business} {proposal.category} {bing.LOW_CARBON_POLICY}"
    if policies:
        complete_output = ""
        try:
            for policy in policies:
                if policy.policy_content:
                    complete_output += policy.policy_content + "\n\n"
                    await websocket.send_text(policy.policy_content + "\n\n")
        finally:
            # 添加到Cache
            if is_nation:
                cache.add_proposal_policy_nation_in_cache(
                    current_user.id, complete_output
                )
            else:
                cache.add_proposal_policy_local_in_cache(
                    current_user.id, complete_output
                )
            await websocket.close()
        return

    content = await bing.search_policy_content(query)
    if is_nation:
        prompt = prompts.policy_nation_prompt(
            proposal.business, proposal.category, content
        )
    else:
        prompt = prompts.policy_local_prompt(
            proposal.province,
            proposal.city,
            proposal.business,
            proposal.category,
            content,
        )
    try:
        if is_nation:
            update_cache_func = (
                lambda policy_text: cache.add_proposal_policy_nation_in_cache(
                    current_user.id, policy_text
                )
            )
        else:
            update_cache_func = (
                lambda policy_text: cache.add_proposal_policy_local_in_cache(
                    current_user.id, policy_text
                )
            )
        await _gpt_ws_helper(
            websocket, prompt, gpt_client, update_cache_func=update_cache_func
        )
    finally:
        await websocket.close()


@router.websocket("/proposal/ws/nation_policy")
async def get_nation_policy_ws(
    websocket: WebSocket,
    token: str = Query(...),
    db: AsyncSession = Depends(database.get_db),
    gpt_client=Depends(dependencies.get_async_openai_client),
):
    """返回国家级政策环境（流式文本）"""
    await _policy_helper(websocket, token, db, gpt_client, is_nation=True)


@router.websocket("/proposal/ws/local_policy")
async def get_local_policy_ws(
    websocket: WebSocket,
    token: str = Query(...),
    db: AsyncSession = Depends(database.get_db),
    gpt_client=Depends(dependencies.get_async_openai_client),
):
    """返回地区政策环境（流式文本）"""
    await _policy_helper(websocket, token, db, gpt_client, is_nation=False)


@router.websocket("/proposal/ws/tech_txt")
async def get_plan_tech_ws(
    websocket: WebSocket,
    token: str = Query(...),
    tech: str = Query(...),
    db: AsyncSession = Depends(database.get_db),
    gpt_client=Depends(dependencies.get_async_openai_client),
):
    """【有请求依赖】根据具体的技术名称生成某个具体技术点的方案描述（流式文本）。
    注意！该请求依赖/proposal/plan的返回结果。"""
    current_user, proposal = await _auth_helper(token, db)
    await websocket.accept()

    # 首先从广告中获取
    ad = await ads.search_ad_by_tech_point(
        db, proposal.business, proposal.category, tech, current_user
    )
    prompt = await prompts.plan_tech_prompt(
        ad=ad,
        tech=tech,
        business=proposal.business,
        category=proposal.category,
        user=current_user,
        db=db,
        background=proposal.requirement,
    )
    try:
        update_cache_func = lambda tech_text: cache.add_proposal_tech_text_in_cache(
            current_user.id, tech, tech_text
        )
        await _gpt_ws_helper(
            websocket, prompt, gpt_client, update_cache_func=update_cache_func
        )
    finally:
        await websocket.close()


@router.websocket("/proposal/ws/case_txt")
async def get_case_txt_ws(
    websocket: WebSocket,
    token: str = Query(...),
    case_id: int = Query(..., description="案例ID", example=1),
    gpt_client=Depends(dependencies.get_async_openai_client),
    db=Depends(database.get_db),
):
    """根据案例编号返回案例数据（流式文本）。
    注意本请求需要依赖/proposal/case_meta的返回结果"""
    current_user, proposal = await _auth_helper(token, db)
    await websocket.accept()
    prompt = await manage_cases.get_case_prompt(
        db=db,
        account_type=current_user.account_type,
        case_id=case_id,
        business=proposal.business,
        category=proposal.category,
        background=proposal.requirement,
    )
    try:
        update_cache_func = lambda case_text: cache.add_proposal_case_text_in_cache(
            current_user.id, case_id, case_text
        )
        await _gpt_ws_helper(
            websocket, prompt, gpt_client, update_cache_func=update_cache_func
        )
    finally:
        await websocket.close()
