from sqlalchemy.ext.asyncio import AsyncSession
from app.utils import config, database

from sqlalchemy import func, select
from app.admin import meta


async def fetch_nation_policy(
    db: AsyncSession, business: str, account_level: int
) -> list[database.NationalPolicy]:
    meta_info = await meta.get_all_sys_info(db)
    limit = (
        meta_info.free_nation_policy
        if account_level == config.REGULAR_LEVEL
        else meta_info.vip_nation_policy
    )
    res = await db.execute(
        select(database.NationalPolicy)
        .where(database.NationalPolicy.policy_business == business)
        .order_by(func.random())
        .limit(limit)
    )
    return list(res.scalars().all())


async def fetch_local_policy(
    db: AsyncSession, business: str, province: str, city: str, account_level: int
) -> list[database.LocalPolicy]:
    meta_info = await meta.get_all_sys_info(db)
    limit = (
        meta_info.free_local_policy
        if account_level == config.REGULAR_LEVEL
        else meta_info.vip_local_policy
    )
    res = await db.execute(
        select(database.LocalPolicy)
        .where(database.LocalPolicy.policy_business == business)
        .where(database.LocalPolicy.policy_province == province)
        .where(database.LocalPolicy.policy_city == city)
        .order_by(func.random())
        .limit(limit)
    )
    return list(res.scalars().all())
