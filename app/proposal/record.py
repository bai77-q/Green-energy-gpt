import math

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import update, func

from datetime import date
from datetime import datetime, timedelta
from sqlalchemy import and_, or_, select
from app.models.models import RecordModel
from app.utils import config, database
from typing import Optional, List


class Record(BaseModel):
    """一次提案的记录（用于系统工单）"""

    user_name: str = Field(
        description="提案人姓名，默认从用户信息读取", example="菱重高投"
    )
    user_phone: str = Field(
        description="提案人电话（包括固定电话或手机），默认从用户信息读取",
        example="17788990022",
    )
    user_company: str = Field(
        description="所在公司，默认是用户姓名", example="菱重高投"
    )
    user_province: str = Field(description="所在省份", example="江西省")
    user_city: str = Field(description="所在城市", example="南昌市")
    business: str = Field(description="行业（一级分类）", example="建筑行业")
    category: str = Field(description="行业子分类（二级分类）", example="家用住宅")
    requirement: str = Field(description="具体需求清单", example="大于2万平米")


async def add_new_record(
    db: AsyncSession, record_id: str, record: Record, user: database.UserLogin
):
    # 如果是测试用户，直接返回
    if user.id == config.Wechat_Name:
        return True
    db.add(
        database.GenerateRecord(
            id=record_id,
            record_time=datetime.now(),
            user_id=user.id,
            svip_id=user.parent_id,
            user_name=record.user_name,
            user_phone=record.user_phone,
            user_company=record.user_company,
            user_province=record.user_province,
            user_city=record.user_city,
            business=record.business,
            category=record.category,
            requirements=record.requirement,
        )
    )
    return await database.commit_with_rollback(db)


async def update_help_request_for_record(db: AsyncSession, record_id: str, help: str):
    await db.execute(
        update(database.GenerateRecord)
        .where(database.GenerateRecord.id == record_id)
        .values(artificial_help=help)
    )
    return await database.commit_with_rollback(db)


def check_record_by_id(user_id: str):
    from app.utils import cache, exceptions

    if not cache.is_user_in_cache(user_id):
        raise exceptions.INIT_EXCEPTION


async def get_cnt_of_records(db: AsyncSession):
    # 计算30天前的日期
    thirty_days_ago = datetime.now() - timedelta(days=30)

    # 执行数据库查询，计算近30天内的记录总数
    query = (
        select(func.count())
        .select_from(database.GenerateRecord)
        .where(database.GenerateRecord.record_time >= thirty_days_ago)
    )
    res = await db.execute(query)

    # 返回查询结果的第一个元素（记录总数）
    return res.scalar()


async def search_records_by_condition(
    db: database.AsyncSession,
    phone: str,
    start: date,
    end: date,
    user: database.UserLogin,
    offset: Optional[int] = 0,
) -> List[database.GenerateRecord]:
    where_conditions = []
    if phone:
        where_conditions.append(database.GenerateRecord.user_phone == phone)
    print("start=", start, "end=", end)
    where_conditions.append(
        and_(
            database.GenerateRecord.record_time >= start,
            database.GenerateRecord.record_time < end + timedelta(days=1),
        )
    )

    if user.account_type == config.ADMIN_LEVEL:
        query = select(database.GenerateRecord).filter(*where_conditions)
    else:
        user_id = user.id
        if user.account_type == config.SUB_SVIP_LEVEL:
            user_id = user.parent_id
        _where = or_(
            database.GenerateRecord.svip_id == user_id,
            database.GenerateRecord.user_id == user_id,
        )
        where_conditions.append(_where)
        query = select(database.GenerateRecord).where(and_(*where_conditions))

    query = query.limit(config.PAGE_SIZE).offset(offset)

    res = await db.execute(query)
    return list(res.scalars().all())


async def get_total_pages_count(
    db: AsyncSession,
    phone: str,
    start_date: date,
    end_date: date,
    user: database.UserLogin,
):
    where_conditions = []
    if phone:
        where_conditions.append(database.GenerateRecord.user_phone == phone)
    where_conditions.append(
        and_(
            database.GenerateRecord.record_time >= start_date,
            database.GenerateRecord.record_time < end_date + timedelta(days=1),
        )
    )

    if user.account_type == config.ADMIN_LEVEL:
        query = select(func.count()).filter(*where_conditions)
    else:
        _where = or_(
            database.GenerateRecord.svip_id == user.id,
            database.GenerateRecord.user_id == user.id,
        )
        where_conditions.append(_where)
        query = select(func.count()).where(and_(*where_conditions))

    result = await db.execute(query)
    count = result.scalar()
    return math.ceil(count / config.PAGE_SIZE)
