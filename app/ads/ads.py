from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import UploadFile

from app.utils import cos, database, config, cache
from app.models import models
from app.users import manage_users
from app.common import common
from app.utils import wiki

from sqlalchemy import select, update, func, and_

import math


async def _add_ad_image(image: UploadFile):
    """添加广告图片"""
    import uuid

    return await cos.upload_image(image, f"ad-{uuid.uuid4().hex}", "ads")


async def add_ad(
    db: AsyncSession,
    user_id: str,
    business: str,
    category: str,
    tech: str,
    ad_info: str,
    image: UploadFile,
):
    """添加广告；成功：True，失败：False"""
    # 要求这个user_id必须是SVIP/VIP/Admin
    user = await manage_users.find_user_by_id_or_phone(db, user_id, is_userid=True)
    if user is None or user.account_type not in [
        config.ADMIN_LEVEL,
        config.VIP_LEVEL,
        config.SVIP_LEVEL,
    ]:
        return False
    image_url = await _add_ad_image(image)
    if image_url is None:
        image_url = config.COMPANY_IMAGE
    ad_to_add = database.Ads(
        user_id=user_id,
        business=business,
        category=category,
        tech=tech,
        ad_info=ad_info,
        image_url=image_url,
    )
    db.add(ad_to_add)
    res = await database.commit_with_rollback(db)
    if res:
        await wiki.add_wiki(ad_to_add.id, business, category, tech, ad_info)
        return True
    return False


def chained_ad_user_id(user: database.UserLogin):
    """根据用户类型返回其匹配的广告用户ID"""
    user_id = user.id
    if user.account_type == config.REGULAR_LEVEL:
        user_id = config.ADMIN_id
    if user.account_type == config.SUB_SVIP_LEVEL:
        user_id = user.parent_id
    return user_id


async def search_ads_by_user(
    db: AsyncSession, user_id: str, business: str, category: str
):
    """根据用户搜索广告"""
    stmt = select(database.Ads).where(
        and_(
            database.Ads.user_id == user_id,
            database.Ads.business == business,
            database.Ads.category == category,
        )
    )
    res = await db.execute(stmt)
    return list(res.scalars().all())


async def search_ads_by_userid(
    db: AsyncSession, user_id: str, page: int = 1, business: str = None
) -> list[database.Ads]:
    """根据用户ID搜索广告，分类/页码可选"""
    offset = (page - 1) * config.PAGE_SIZE
    where_conditions = [and_(database.Ads.user_id == user_id)]
    if business is not None:
        where_conditions.append(and_(database.Ads.business == business))
    stmt = (
        select(database.Ads)
        .where(*where_conditions)
        .offset(offset)
        .limit(config.PAGE_SIZE)
    )
    res = await db.execute(stmt)
    return list(res.scalars().all())


async def ads_pages_by_userid(
    db: AsyncSession, user_id: str, business: str = None
) -> int:
    """根据用户ID返回广告页码总数，分类可选"""
    where_conditions = [and_(database.Ads.user_id == user_id)]
    if business is not None:
        where_conditions.append(and_(database.Ads.business == business))
    stmt = select(func.count()).select_from(database.Ads).where(*where_conditions)
    res = await db.execute(stmt)
    return math.ceil(res.scalar() / config.PAGE_SIZE)


async def update_ad(
    db: AsyncSession,
    ad_id: int,
    user: database.UserLogin,
    update_model: models.UpdateAdModel,
):
    old_ad = await common.get_item_by_id(db, ad_id, database.Ads)
    if old_ad is None:
        return False
    if user.account_type == config.SVIP_LEVEL and old_ad.user_id != user.id:
        """如果是SVIP，仅能更新自己的广告"""
        return False
    update_values = update_model.model_dump(exclude_unset=True, exclude_none=True)
    if not update_values:
        return True
    await db.execute(
        update(database.Ads)
        .where(and_(database.Ads.id == ad_id))
        .values(**update_values)
    )
    return database.commit_with_rollback(db)


async def _search_tech_point(
    db: AsyncSession, business: str, category: str, tech: str
) -> list[database.TechPoint]:
    """根据业务分类和技术名称搜索技术点"""
    stmt = select(database.TechPoint).where(
        and_(
            database.TechPoint.business == business,
            database.TechPoint.category == category,
            database.TechPoint.tech == tech,
        )
    )
    res = await db.execute(stmt)
    return list(res.scalars().all())


async def _search_ad_by_tech_point(
    db: AsyncSession, business: str, category: str, tech: str, user: database.UserLogin
) -> database.TechAdMatch | None:
    """根据技术点搜索广告"""
    tech_points = await _search_tech_point(db, business, category, tech)
    if not tech_points:
        return None
    tech_point = tech_points[0]

    async def _match_ad(_user_id):
        stmt = (
            select(database.TechAdMatch)
            .where(
                and_(
                    database.TechAdMatch.tech_id == tech_point.tech_id,
                    database.TechAdMatch.ad_user_id == _user_id,
                )
            )
            .order_by(func.random())
            .limit(1)
        )
        _res = await db.execute(stmt)
        return _res.scalar_one_or_none()

    user_id = user.id
    if user.account_type in [config.ADMIN_LEVEL, config.REGULAR_LEVEL]:
        user_id = config.ADMIN_id
        return await _match_ad(user_id)
    if user.account_type == config.SUB_SVIP_LEVEL:
        user_id = user.parent_id
    res = await _match_ad(user_id)
    if res is None:
        return await _match_ad(config.ADMIN_id)
    return res


async def search_ad_by_tech_point(
    db: AsyncSession, business: str, category: str, tech: str, user: database.UserLogin
) -> database.Ads | None:
    """根据技术点搜索广告"""
    tech_ad_match = await _search_ad_by_tech_point(db, business, category, tech, user)
    if tech_ad_match is None:
        return None
    stmt = select(database.Ads).where(database.Ads.id == tech_ad_match.ad_id)
    res = await db.execute(stmt)
    res_ad: database.Ads = res.scalar_one_or_none()
    if res_ad:
        # add ad into cache
        cache.add_ad_in_cache(f"{user.id}-{tech}", res_ad.image_url)
    return res_ad


async def search_tech_points(
    db: AsyncSession, business: str, category: str
) -> list[str]:
    """根据业务分类搜索技术点"""
    stmt = select(database.TechPoint.tech).where(
        and_(
            database.TechPoint.business == business,
            database.TechPoint.category == category,
        )
    )
    res = await db.execute(stmt)
    return [i[0] for i in res.all()]
