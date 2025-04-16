import random
from typing import List
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils import database, config, prompts
from pydantic import BaseModel, Field


class CaseMeta(BaseModel):
    """案例的元数据，包括ID，图片和名称"""

    case_id: int = Field(description="案例编号，如果为-1，表示完全由AI编写")
    case_image: str = Field(description="案例图片URL")
    case_title: str = Field(description="案例名称")


async def fetch_ids_imgs(
    db: AsyncSession, business: str, category: str, user_level: int
) -> List[CaseMeta]:
    """
    根据用户等级和业务领域获取案例ID，并可能从数据库获取案例图片和标题，
    或者为负数case_id随机选择图片URL，并确保图片URL不重复。
    """
    case_metas_list = []
    prompts_length = prompts.get_cases_prompts_length()

    # 获取案例ID列表
    case_ids = await get_case_ids(db, business, category, user_level, prompts_length)

    # 获取负数案例的图片URL
    negative_case_count = sum(1 for case_id in case_ids if case_id < 0)
    image_urls_list = config.CASE_IMGS.get(business, [])
    selected_images = random.sample(
        image_urls_list, min(len(image_urls_list), negative_case_count)
    )

    # 生成案例元数据列表
    negative_case_index = 1
    for case_id in case_ids:
        if case_id > 0:
            img, title = await get_case_img_title(db, case_id)
        else:
            img = selected_images.pop(0) if selected_images else None
            title = f"环保{category}案例{negative_case_index}" if img else ""
            negative_case_index += 1
        case_metas_list.append(
            CaseMeta(case_id=case_id, case_image=img, case_title=title)
        )

    return case_metas_list


async def get_case_ids(
    db: AsyncSession, business: str, category: str, user_level: int, prompts_length: int
) -> List[int]:
    """
    根据用户等级获取案例ID列表。
    """
    if user_level == config.REGULAR_LEVEL:
        return random.sample(range(-prompts_length, 0), config.FREE_CASE)
    else:
        business_case_ids = await _get_case_ids_by_business(
            db, business, category, config.VIP_CASE
        )
        real_case_count = len(business_case_ids)
        extra_case_ids = random.sample(
            range(-prompts_length, 0), config.VIP_CASE - real_case_count
        )
        return random.sample(business_case_ids, real_case_count) + extra_case_ids


async def _get_case_ids_by_business(
    db: AsyncSession, business: str, category: str, limit: int
) -> List[int]:
    """
    根据业务领域获取案例ID列表。
    异步地通过业务领域获取数据库中的案例ID。
    """
    query_filters = [database.ClassicCase.business == business]
    if category != "其他":
        query_filters.append(database.ClassicCase.category == category)

    stmt = (
        select(database.ClassicCase.id)
        .filter(*query_filters)
        .order_by(func.random())
        .limit(limit)
    )
    result = await db.execute(stmt)
    all_case_ids = result.scalars().all()
    return list(all_case_ids)


async def get_case_img_title(db: AsyncSession, case_id: int):
    print("case_id=", case_id)
    res = await db.execute(
        select(database.ClassicCase.image_url, database.ClassicCase.project_name).where(
            database.ClassicCase.id == case_id
        )
    )
    case = res.first()
    return case.image_url, case.project_name


async def fetch_case_txt(db: AsyncSession, case_id: int):
    result = await db.execute(
        select(database.ClassicCase).where(database.ClassicCase.id == case_id)
    )
    """暂时不使用，因为都用AI写了"""
    case = result.scalars().first()
    if case:
        return f"""
该项目的介绍：{case.project_profile}。
该项目取得成果：{case.benefit}。
该项目的总结和经验：{case.summarize_experience}。
"""

    return """闵行工业区智慧能源示范项目: 为减少用户侧企业能耗、优化企业能源利用结构、并为企业员工绿色出行提供便利，
    在满足用可靠性的同时，探索在用户侧构建风光储充结合智能微能源网的可能。
国网上海综合能源服务有限公司以降低城市能耗为目标，协同满足生态环保等需求，
以上海闵行工业区为示范站点，通过技术进步和模式创新实现以可再生能源、储能为代表的清洁、智慧能源全面应用。
该项目自2021年从6月投入试运行，经济效益显著，社会效益明显，每年可节约标煤约665吨，减少二氧化碳排放约1760吨，减少有害气体排放约1.8吨。
"""
