from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.utils import database, config

from sqlalchemy import select, func, update

import math


async def pages_by_business(db: AsyncSession, business: str, table) -> int:
    """按行业分类返回总页数（可扩展）"""
    stmt = select(func.count()).select_from(table).where(table.business == business)
    res = await db.execute(stmt)
    return math.ceil(res.scalar() / config.PAGE_SIZE)


async def get_item_by_id(
    db: AsyncSession, key: int | str, table
) -> database.ClassicCase | database.Ads:
    """返回案例或广告（可扩展）"""
    stmt = select(table).where(table.id == key)
    res = await db.execute(stmt)
    return res.scalar()


async def search_items_by_business(
    db: AsyncSession, business: str, table, page: int = 1
) -> list[database.ClassicCase] | list[database.Ads]:
    """管理员根据行业分类搜索查看案例/广告（可扩展）"""
    offset = (page - 1) * config.PAGE_SIZE
    stmt = (
        select(table)
        .where(table.business == business)
        .offset(offset)
        .limit(config.PAGE_SIZE)
    )
    res = await db.execute(stmt)
    return list(res.scalars().all())


async def update_item_by_id(
    db: AsyncSession, key: int | str, table, update_model: BaseModel
) -> bool:
    """根据ID更新（可扩展）"""
    old_item = await get_item_by_id(db, key, table)
    if old_item is None:
        return False
    update_values = update_model.model_dump(exclude_unset=True, exclude_none=True)
    if not update_values:
        return True
    await db.execute(update(table).where(table.id == key).values(**update_values))
    return await database.commit_with_rollback(db)


def stream_list_str(data: list[str]):
    if len(data) > 0:
        yield data[0]
        for line in data[1:]:
            yield "\n\n" + line
