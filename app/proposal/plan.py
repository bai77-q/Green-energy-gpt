from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.meta import get_all_sys_info
from app.utils import prompts, gpt, database, config
from sqlalchemy import func, select
from app.utils import cache
from app.models import models

import json


async def get_plans(
    db: AsyncSession, proposal: cache.CachedProposal, account_type: int, gpt_client
):
    sys_info = await get_all_sys_info(db)
    tech_num = (
        sys_info.free_tech
        if account_type == config.REGULAR_LEVEL
        else sys_info.vip_tech
    )

    prompt = await prompts.plan_overview_prompt(
        name=proposal.company,
        business=proposal.business,
        category=proposal.category,
        requirement=proposal.requirement,
        tech_num=tech_num,
        db=db,
    )
    json_result = await gpt.get_gpt_json_result(prompt, gpt_client)
    if json_result is not None:
        plan_details = json.loads(json_result)
    else:
        plan_details = {
            "intro": f"为了实现环保{proposal.category}，我们建议从空气源热泵和集中新风系统两个方面入手。",
            "techs": ["空气源热泵", "集中新风系统"],
        }
    return plan_details
