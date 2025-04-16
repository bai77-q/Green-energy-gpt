import json
import time
import random
import uuid
from dataclasses import dataclass

from app.utils import gpt, prompts, bing, images, database, auth, cases, config
from app.utils import message
from app.utils import cache
from app.utils import download
from app.models import models
from app import dependencies
from app.proposal import record, plan
from app.common import common
from app.cases import manage_cases

from app.proposal import company

from fastapi import APIRouter, Depends, Body, Query
from fastapi import HTTPException, status
from fastapi.responses import StreamingResponse

from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated, Any

from datetime import datetime

from app.common import policy as policy_util

from app.ads import ads
from app.utils.add_operation import record_user_operation
from app.utils.config import PROPOSAL_OP_TYPE

router = APIRouter()

INIT_EXCEPTION = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST, detail="请初始化提案"
)


def check_record_by_id(user_id: str):
    if not cache.is_user_in_cache(user_id):
        raise INIT_EXCEPTION


@router.post(
    "/proposal/init", response_model=message.MessageModel, tags=[config.API_PROPOSAL]
)
async def init_proposal(
    content: Annotated[record.Record, Body()],
    db: AsyncSession = Depends(database.get_db),
    current_user: database.UserLogin = Depends(auth.get_current_user),
):
    """每次生成提案之前需要调用该请求，用于初始化本次提案。(只需要调用一次）"""
    if current_user.account_type in [
        config.SVIP_LEVEL,
        config.SUB_SVIP_LEVEL,
        config.VIP_LEVEL,
    ]:
        await auth.check_expired(db, current_user)

    # 对直辖市单独处理
    if content.user_province in ["北京市", "上海市", "重庆市", "天津市"]:
        content.user_city = content.user_province

    record_id = "record-" + uuid.uuid4().hex
    cached_record = cache.get_record_in_cache(current_user.id)

    if current_user.account_type != config.ADMIN_LEVEL:
        await auth.check_limit(db, current_user)

    async def _add_new_record():
        res = await record.add_new_record(db, record_id, content, current_user)
        if not res:
            raise INIT_EXCEPTION
        cache.add_user_record_in_cache(current_user.id, content, record_id)
        await record_user_operation(
            PROPOSAL_OP_TYPE,
            record_id,
            current_user.id,
        )

    if cached_record:
        proposal = json.loads(cached_record)
        if (
            proposal["company"] == content.user_company
            and proposal["province"] == content.user_province
            and proposal["city"] == content.user_city
            and proposal["business"] == content.business
            and proposal["category"] == content.category
            and proposal["requirement"] == content.requirement
        ):
            # 在缓存中，也需要增加次数
            await database.commit_with_rollback(db)
            cache.add_user_record_in_cache(current_user.id, content, record_id)
            await record_user_operation(
                PROPOSAL_OP_TYPE,
                record_id,
                current_user.id,
            )
        else:
            await _add_new_record()
    else:
        await _add_new_record()

    return message.MessageModel(status=message.OK_CODE, msg=message.OK_MSG)


@router.get("/proposal/id", tags=[config.API_PROPOSAL])
async def get_record_id(
    current_user: database.UserLogin = Depends(auth.get_current_user),
):
    """返回用户当前的提案ID"""
    check_record_by_id(current_user.id)
    proposal = cache.CachedProposal(
        **json.loads(cache.get_record_in_cache(current_user.id))
    )
    return proposal.record_id


@router.get("/company", response_model=company.CompanyInfo, tags=[config.API_PROPOSAL])
async def get_company_info(
    db: AsyncSession = Depends(database.get_db),
    current_user: database.UserLogin = Depends(auth.get_current_user),
):
    """返回公司的介绍信息"""
    record.check_record_by_id(current_user.id)
    return await company.get_company_info(db, current_user)


@router.get("/proposal/intro_txt", tags=[config.API_PROPOSAL])
async def get_intro_txt(
    gpt_client=Depends(dependencies.get_async_openai_client),
    current_user: database.UserLogin = Depends(auth.get_current_user),
):
    """根据行业和子分类获得行业介绍（注意：这是流式文本）。请使用其ws版本：/proposal/ws/intro_txt"""
    # 检查当前用户记录
    record.check_record_by_id(current_user.id)
    # 从缓存中获取提案并解析
    proposal = cache.CachedProposal(
        **json.loads(cache.get_record_in_cache(current_user.id))
    )
    prompt_text = prompts.intro_prompt(proposal.business, proposal.category)

    update_cache_func = lambda intro_text: cache.add_proposal_intro_text_in_cache(
        current_user.id, intro_text
    )
    # 生成并返回流式响应
    return StreamingResponse(
        gpt.get_gpt_stream_result(
            prompt_text, gpt_client, update_cache_func=update_cache_func
        ),
        media_type="text/html",
    )


@router.get(
    "/proposal/intro_img",
    response_model=models.ImageURLModel,
    tags=[config.API_PROPOSAL],
)
async def get_intro_img(
    db: AsyncSession = Depends(database.get_db),
    current_user=Depends(auth.get_current_user),
):
    """获取行业介绍图片的URL"""
    record.check_record_by_id(current_user.id)
    proposal = cache.CachedProposal(
        **json.loads(cache.get_record_in_cache(current_user.id))
    )
    url = await images.get_random_intro_img(proposal.business, proposal.category, db=db)
    cache.add_proposal_intro_image_in_cache(current_user.id, url)
    return models.ImageURLModel(url=url)


@router.post(
    "/proposal/chart", tags=[config.API_PROPOSAL, config.API_PROPOSAL_WITH_DEPENDENCY]
)
async def get_chart(
    content: Annotated[models.ChartContent, Body()],
    gpt_client=Depends(dependencies.get_async_openai_client),
    current_user=Depends(auth.get_current_user),
):
    """【有请求依赖】根据文字提取其中数字生成JSON用于绘制bar chart等（参考https://www.chartjs.org/docs/latest/getting-started/）；
    注意该请求依赖/proposal/intro的返回结果。由于内容是AI生成的，客户端需要在渲染不成功时，使用fallback方案。"""
    record.check_record_by_id(current_user.id)
    prompt = prompts.chart_prompt(content.content)
    json_result = await gpt.get_gpt_json_result(prompt, gpt_client)
    if json_result is not None:
        return json.loads(json_result)
    return config.CHART_DEFAULT


@router.post(
    "/proposal/v2/chart",
    tags=[config.API_PROPOSAL, config.API_PROPOSAL_WITH_DEPENDENCY],
)
async def get_chart_v2(
    content: Annotated[models.ChartContent, Body()],
    gpt_client=Depends(dependencies.get_async_openai_client),
    current_user=Depends(auth.get_current_user),
):
    """【有请求依赖】（小程序使用）根据文字提取其中数字生成JSON用于绘制bar chart等（参考https://github.com/ecomfe/echarts-for-weixin）；
    注意该请求依赖/proposal/intro的返回结果。由于内容是AI生成的，客户端需要在渲染不成功时，使用fallback方案。"""
    record.check_record_by_id(current_user.id)
    prompt = prompts.echart_prompt(content.content)
    json_result = await gpt.get_gpt_json_result(prompt, gpt_client)
    if json_result is not None:
        cache.add_proposal_chart_json_in_cache(current_user.id, json_result)
        return json.loads(json_result)
    cache.add_proposal_chart_json_in_cache(current_user.id, config.ECHART_DEFAULT)
    return config.ECHART_DEFAULT


@router.get("/proposal/nation_policy", tags=[config.API_PROPOSAL])
async def get_nation_policy(
    gpt_client: Any = Depends(dependencies.get_async_openai_client),
    current_user: database.UserLogin = Depends(auth.get_current_user),
    db: AsyncSession = Depends(database.get_db),
) -> StreamingResponse:
    """返回国家级政策环境（流式文本），请使用其ws版本/proposal/ws/nation_policy"""
    record.check_record_by_id(current_user.id)
    proposal = cache.CachedProposal(
        **json.loads(cache.get_record_in_cache(current_user.id))
    )
    policies = await policy_util.fetch_nation_policy(
        db, proposal.business, current_user.account_type
    )

    if policies:
        policy_content = [policy.policy_content for policy in policies]
        cache.add_proposal_policy_nation_in_cache(
            current_user.id, "\n\n".join(policy_content)
        )
        return StreamingResponse(
            common.stream_list_str(policy_content), media_type="text/html"
        )
    # 如果数据库中没有政策内容，或者选中的政策内容为空，执行备用逻辑
    content = await bing.search_policy_content(
        f"{proposal.business} {proposal.category} {bing.LOW_CARBON_NATION_POLICY}",
    )
    prompt = prompts.policy_nation_prompt(proposal.business, proposal.category, content)
    update_cache_func = lambda p: cache.add_proposal_policy_nation_in_cache(
        current_user.id, p
    )
    policy_content = gpt.get_gpt_stream_result(
        prompt, gpt_client, update_cache_func=update_cache_func
    )
    return StreamingResponse(policy_content, media_type="text/html")


@router.get("/proposal/local_policy", tags=[config.API_PROPOSAL])
async def get_local_policy(
    gpt_client: Any = Depends(dependencies.get_async_openai_client),
    current_user: database.UserLogin = Depends(auth.get_current_user),
    db: AsyncSession = Depends(database.get_db),
) -> StreamingResponse:
    """
    返回针对用户查询条件的本地政策环境信息。
    """
    record.check_record_by_id(current_user.id)
    proposal = cache.CachedProposal(
        **json.loads(cache.get_record_in_cache(current_user.id))
    )
    # 确定用户等级
    local_policies = await policy_util.fetch_local_policy(
        db,
        proposal.business,
        proposal.province,
        proposal.city,
        current_user.account_type,
    )
    if local_policies:
        policy_content = [policy.policy_content for policy in local_policies]
        cache.add_proposal_policy_local_in_cache(
            current_user.id, "\n\n".join(policy_content)
        )
        return StreamingResponse(
            common.stream_list_str(policy_content), media_type="text/html"
        )
    # 备用逻辑：当没有查询到足够的地区政策时，使用GPT生成政策内容
    content = await bing.search_policy_content(
        f"{proposal.business} {proposal.category} {proposal.province}{proposal.city} {bing.LOW_CARBON_POLICY}",
    )
    prompt = prompts.policy_local_prompt(
        proposal.province, proposal.city, proposal.business, proposal.category, content
    )
    update_cache_func = lambda p: cache.add_proposal_policy_local_in_cache(
        current_user.id, p
    )
    policy_content = gpt.get_gpt_stream_result(
        prompt, gpt_client, update_cache_func=update_cache_func
    )
    return StreamingResponse(policy_content, media_type="text/html")


@router.get(
    "/proposal/policy_img",
    response_model=models.ImageURLModel,
    tags=[config.API_PROPOSAL],
)
async def get_policy_img(
    current_user: database.UserLogin = Depends(auth.get_current_user),
    db=Depends(database.get_db),
):
    """返回政策图片的URL。"""
    record.check_record_by_id(current_user.id)
    proposal = cache.CachedProposal(
        **json.loads(cache.get_record_in_cache(current_user.id))
    )
    try:
        if random.random() < 0.9:  # 有0.9的概率查询local_policy表
            policy_url = await images.get_image_url_from_local_policy(
                proposal.province,
                proposal.city,
                proposal.business,
                proposal.category,
                db=db,
            )
        else:
            policy_url = await images.get_image_url_from_national_policy(
                proposal.business, proposal.category, db=db
            )

        # 如果数据库中找到了政策图片的URL，则返回
        if policy_url:
            cache.add_proposal_policy_image_in_cache(current_user.id, policy_url)
            return models.ImageURLModel(url=policy_url)
        # 如果数据库中没有找到，尝试使用Bing搜索
        query = f"{proposal.province} {proposal.city} {proposal.business} {proposal.category} 低碳政策"
        policy_url = await bing.get_policy_url(query)
        url = await images.get_image_by_policy_url(policy_url)
        cache.add_proposal_policy_image_in_cache(current_user.id, url)
        return models.ImageURLModel(url=url)
    except Exception as e:
        print(e)
    cache.add_proposal_policy_image_in_cache(
        current_user.id, config.DEFAULT_POLICY_IMAGE
    )
    return models.ImageURLModel(url=config.DEFAULT_POLICY_IMAGE)


@router.get(
    "/proposal/plan", response_model=models.PlanModel, tags=[config.API_PROPOSAL]
)
async def get_plan(
    gpt_client=Depends(dependencies.get_async_openai_client),
    current_user: database.UserLogin = Depends(auth.get_current_user),
    db: AsyncSession = Depends(database.get_db),
):
    """返回技术方案的概述JSON，包括方案概述和技术点。"""
    check_record_by_id(current_user.id)
    proposal = cache.CachedProposal(
        **json.loads(cache.get_record_in_cache(current_user.id))
    )

    plan_details = await plan.get_plans(
        db, proposal, current_user.account_type, gpt_client
    )

    cache.add_proposal_tech_plan_in_cache(current_user.id, plan_details["intro"])
    cache.add_proposal_techs(current_user.id, plan_details["techs"])
    return plan_details


@router.get(
    "/proposal/v2/plan", response_model=models.Planv2Model, tags=[config.API_PROPOSAL]
)
async def get_plan_v2(
    gpt_client=Depends(dependencies.get_async_openai_client),
    current_user: database.UserLogin = Depends(auth.get_current_user),
    db: AsyncSession = Depends(database.get_db),
):
    """返回技术方案的概述JSON，包括方案概述和技术点详情（技术点名称和图片URL）。"""
    check_record_by_id(current_user.id)
    proposal = cache.CachedProposal(
        **json.loads(cache.get_record_in_cache(current_user.id))
    )

    plan_details = await plan.get_plans(
        db, proposal, current_user.account_type, gpt_client
    )

    # 异步任务：提高效率
    techs_details = []

    async def fetch_img(tech):
        url = (
            cache.get_ad_in_cache(f"{current_user.id}-{tech}")
            or await images.search_image_urls(tech, gpt_client)
            or await bing.get_img(tech + " 示意图")
        )
        techs_details.append(models.TechDetail(tech_name=tech, tech_img=url))

    import asyncio

    tasks = [fetch_img(tech) for tech in plan_details["techs"]]
    await asyncio.gather(*tasks)

    cache.add_proposal_tech_plan_in_cache(current_user.id, plan_details["intro"])
    techs = [tech.tech_name for tech in techs_details]
    cache.add_proposal_techs(current_user.id, techs)

    for tech in techs_details:
        cache.add_proposal_tech_image_in_cache(
            current_user.id, tech.tech_name, tech.tech_img
        )

    return models.Planv2Model(
        intro=plan_details["intro"],
        techs=techs_details,
    )


@dataclass
class Tech:
    tech: str = Query(..., description="技术名称", example="空调隔热")


@router.get(
    "/proposal/tech_txt",
    tags=[config.API_PROPOSAL, config.API_PROPOSAL_WITH_DEPENDENCY],
)
async def get_plan_tech(
    tech: Annotated[models.Tech, Depends()],
    gpt_client=Depends(dependencies.get_async_openai_client),
    current_user: database.UserLogin = Depends(auth.get_current_user),
    db: AsyncSession = Depends(database.get_db),
):
    """【有请求依赖】根据具体的技术名称生成某个具体技术点的方案描述（流式文本）。
    注意！该请求依赖/proposal/plan的返回结果。请使用其ws版本：/proposal/ws/tech_txt"""
    check_record_by_id(current_user.id)
    proposal = cache.CachedProposal(
        **json.loads(cache.get_record_in_cache(current_user.id))
    )
    ad = await ads.search_ad_by_tech_point(
        db, proposal.business, proposal.category, tech.tech, current_user
    )

    prompt = await prompts.plan_tech_prompt(
        ad=ad,
        tech=tech.tech,
        business=proposal.business,
        category=proposal.category,
        user=current_user,
        db=db,
        background=proposal.requirement,
    )
    update_cache_func = lambda t: cache.add_proposal_tech_text_in_cache(
        current_user.id, tech.tech, t
    )
    return StreamingResponse(
        gpt.get_gpt_stream_result(
            prompt, gpt_client, update_cache_func=update_cache_func
        ),
        media_type="text/html",
    )


@router.post(
    "/proposal/plan_flow",
    tags=[config.API_PROPOSAL, config.API_PROPOSAL_WITH_DEPENDENCY],
)
async def get_plan_flow(
    content: Annotated[models.FlowContent, Body()],
    gpt_client=Depends(dependencies.get_async_openai_client),
    current_user: database.UserLogin = Depends(auth.get_current_user),
):
    """返回技术方案的流程图，使用mermaid.js描述；客户端需要使用http://mermaid.js.org绘制。
    注意该请求依赖/proposal/plan的返回结果。由于内容是AI生成的，客户端需要在渲染不成功时，使用fallback方案。
    由于流程图很复杂，目前版本并没有使用。
    """
    check_record_by_id(current_user.id)
    prompt = prompts.plan_flow_prompt(content.content)
    if current_user.account_type == config.REGULAR_LEVEL:
        mermaid_json = await gpt.get_gpt_json_result(prompt, gpt_client)
    else:
        mermaid_json = await gpt.get_gpt_json_result(
            prompt, gpt_client, model=gpt.GPT4_MODEL
        )
    return json.loads(mermaid_json)


@router.get(
    "/proposal/tech_img",
    response_model=models.ImageURLModel,
    tags=[config.API_PROPOSAL, config.API_PROPOSAL_WITH_DEPENDENCY],
)
async def get_tech_image(
    tech: Annotated[models.Tech, Depends()],
    gpt_client=Depends(dependencies.get_async_openai_client),
    current_user: database.UserLogin = Depends(auth.get_current_user),
):
    """返回某个技术点名称的示意图的URL，
    注意该请求依赖/proposal/plan的返回结果。
    """
    check_record_by_id(current_user.id)

    image_url = (
        cache.get_ad_in_cache(f"{current_user.id}-{tech.tech}")
        or await images.search_image_urls(tech.tech, gpt_client)
        or await bing.get_img(tech.tech + " 示意图")
    )

    cache.add_proposal_tech_image_in_cache(current_user.id, tech.tech, image_url)
    return models.ImageURLModel(url=image_url)


@router.get(
    "/proposal/case_meta",
    response_model=list[cases.CaseMeta],
    tags=[config.API_PROPOSAL],
)
async def get_case_meta(
    db=Depends(database.get_db),
    current_user: database.UserLogin = Depends(auth.get_current_user),
) -> list[cases.CaseMeta]:
    """
    根据当前用户的提案信息，返回符合条件的案例元数据列表。
    """
    check_record_by_id(current_user.id)
    proposal = cache.CachedProposal(
        **json.loads(cache.get_record_in_cache(current_user.id))
    )
    res = await cases.fetch_ids_imgs(
        db, proposal.business, proposal.category, current_user.account_type
    )

    case_ids = [case.case_id for case in res]
    cache.add_proposal_cases(current_user.id, case_ids)

    for case in res:
        cache.add_proposal_case_image_in_cache(
            current_user.id, case.case_id, case.case_image
        )
        cache.add_proposal_case_title_in_cache(
            current_user.id, case.case_id, case.case_title
        )

    return res


@router.get(
    "/proposal/case_txt",
    tags=[
        config.API_PROPOSAL,
        config.API_PROPOSAL_WITH_DEPENDENCY,
    ],
)
async def get_case_txt(
    case_id: int = Query(..., description="案例ID", example=1),
    gpt_client=Depends(dependencies.get_async_openai_client),
    db=Depends(database.get_db),
    current_user=Depends(auth.get_current_user),
):
    """
    根据案例编号返回案例数据（流式文本）。
    注意本请求需要依赖/proposal/case_meta的返回结果。对于实时数据交互更复杂的场景，请使用WebSocket版本：/proposal/ws/case_txt。
    """
    check_record_by_id(current_user.id)
    proposal = cache.CachedProposal(
        **json.loads(cache.get_record_in_cache(current_user.id))
    )

    prompt = await manage_cases.get_case_prompt(
        db=db,
        account_type=current_user.account_type,
        case_id=case_id,
        business=proposal.business,
        category=proposal.category,
        background=proposal.requirement,
    )
    update_cache_func = lambda c: cache.add_proposal_case_text_in_cache(
        current_user.id, case_id, c
    )
    ai_response = gpt.get_gpt_stream_result(
        prompt, gpt_client, update_cache_func=update_cache_func
    )

    return StreamingResponse(ai_response, media_type="text/html")


@router.post(
    "/proposal/generate_link", response_model=models.LinkModel, tags=[config.API_SHARE]
)
async def generate_proposal_link(
    content: Annotated[models.ProposalModel, Body()],
    db=Depends(database.get_db),
    current_user: database.UserLogin = Depends(auth.get_current_user),
):
    """得到当前生成的提案的永久链接ID"""
    check_record_by_id(current_user.id)
    from app.proposal import shared

    shared_id = shared.generate_shared_id()
    from fastapi.encoders import jsonable_encoder

    shared_record: database.SharedRecord = database.SharedRecord(
        id=shared_id,
        shared_by=current_user.full_name,
        shared_time=datetime.now(),
        content_json=json.dumps(jsonable_encoder(content)),
    )
    res = await shared.add_shared_record(db, shared_record)
    if res:
        return models.LinkModel(link=shared_id)
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot generate link"
    )


@router.post(
    "/proposal/v2/generate_link",
    response_model=models.LinkModel,
    tags=[config.API_SHARE],
)
async def generate_proposal_link_v2(
    db=Depends(database.get_db),
    current_user=Depends(auth.get_current_user),
    gpt_client=Depends(dependencies.get_async_openai_client),
):
    """这是/proposal/generate_link的改进版本，返回提案的永久链接ID。不再需要手动传入提案内容，而是直接从缓存中获取。"""
    check_record_by_id(current_user.id)
    from app.proposal import shared

    res = await shared.generate_shared_from_cache(db, gpt_client, current_user)
    if res:
        return models.LinkModel(link=res)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot generate link"
        )


@router.get("/proposal/download", tags=[config.API_SHARE])
async def download_proposal(
    current_user: database.UserLogin = Depends(auth.get_current_user),
    db=Depends(database.get_db),
    gpt_client=Depends(dependencies.get_async_openai_client),
):
    """下载当前用户的提案，返回word地址。注意：后台可能需要动态生成技术点和案例，所以耗时较长"""
    check_record_by_id(current_user.id)
    link = await download.generate_proposal(db, gpt_client, current_user)
    return link


@router.post(
    "/proposal/help", response_model=message.MessageModel, tags=[config.API_HELP]
)
async def send_help_request(
    _help: Annotated[models.HelpModel, Body()],
    db=Depends(database.get_db),
    current_user=Depends(auth.get_current_user),
):
    """用户填写人工介入的需求"""
    check_record_by_id(current_user.id)
    proposal = cache.CachedProposal(
        **json.loads(cache.get_record_in_cache(current_user.id))
    )
    res = await record.update_help_request_for_record(
        db, proposal.record_id, _help.content
    )
    return message.construct_msg(res)


@router.get("/green")
async def get_green():
    def output():
        texts = "“中国将提高国家自主贡献力度，采取更加有力的政策和措施，二氧化碳排放力争于2030年前达到峰值，努力争取2060年前实现碳中和”。"
        for ch in texts:
            yield ch
            time.sleep(0.1)

    return StreamingResponse(output(), media_type="text/html")
