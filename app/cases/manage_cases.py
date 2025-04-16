from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import delete

from fastapi import UploadFile

from app.utils import cos, database, config, prompts, cases
from app.models import models
from app.common import common

from app.admin import meta


async def get_case_prompt(
    db: AsyncSession,
    account_type: int,
    case_id: int,
    business: str,
    category: str,
    background: str = "",
):
    meta_info = await meta.get_all_sys_info(db)
    case_words = (
        meta_info.free_case_words
        if account_type == config.REGULAR_LEVEL
        else meta_info.vip_case_words
    )

    if case_id < 0:
        # 使用随机选择的case_id获取提示
        prompt = prompts.case_ai_prompt(
            business, category, case_id, words=case_words, background=background
        )
    else:
        # 从数据库获取案例文本
        case = await cases.fetch_case_txt(db, case_id)
        prompt = prompts.case_prompt(business, category, case)
    return prompt


async def _add_case_image(image: UploadFile):
    import uuid

    return await cos.upload_image(image, f"ad-{uuid.uuid4().hex}", "ads")


async def add_case(
    db: AsyncSession,
    business: str,
    category: str,
    project_name: str,
    project_profile: str,
    benefit: str,
    summarize_experience: str,
    image: UploadFile,
):
    """管理员添加案例"""
    image_url = await _add_case_image(image)
    if image_url is None:
        image_url = config.COMPANY_IMAGE
    db.add(
        database.ClassicCase(
            business=business,
            category=category,
            project_name=project_name,
            project_profile=project_profile,
            benefit=benefit,
            summarize_experience=summarize_experience,
            image_url=image_url,
        )
    )
    return await database.commit_with_rollback(db)


async def update_case(
    db: AsyncSession, case_id: int, update_model: models.UpdateCaseModel
):
    """更新案例"""
    return await common.update_item_by_id(
        db, case_id, database.ClassicCase, update_model
    )


async def delete_case(db: AsyncSession, case_id: int):
    """删除案例"""
    stmt = delete(database.ClassicCase).where(database.ClassicCase.id == case_id)
    await db.execute(stmt)
    return await database.commit_with_rollback(db)
