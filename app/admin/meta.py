from sqlalchemy.ext.asyncio import AsyncSession

from app.utils import database
from app.common import common
from app.models import models
from sqlalchemy import select


async def get_sys_info(db: AsyncSession):
    """获取系统的名称和Logo"""
    res = await db.execute(select(database.SystemMeta))
    sys_info: database.SystemMeta = res.scalar_one()
    return models.SysModel(name=sys_info.system_name, logo=sys_info.system_logo)


async def get_all_sys_info(db: AsyncSession) -> database.SystemMeta:
    """获取系统所有配置"""
    res = await db.execute(select(database.SystemMeta))
    return res.scalar_one()


async def update_meta(db: AsyncSession, meta_info: models.SysResponseModel):
    """更新系统的配置信息"""
    # 只有一条信息，所以ID总是1
    return await common.update_item_by_id(db, 1, database.SystemMeta, meta_info)


async def get_payment_info(db: AsyncSession):
    return [
        models.PaymentInfoModel(
            title="免费用户",
            intro="每日 1 次方案生成机会，无智能对话使用权限，无公司定制功能",
            price="0.0",
            icon="https://green-img.f2ee.com/system/common.webp",
        ),
        models.PaymentInfoModel(
            title="VIP",
            intro="提案生成 20 次/天；经济性测算+AI咨询服务 20 次/天；商机实时抓取。能够通过管理员定制公司介绍和产品广告。",
            price="9888",
            icon="https://green-img.f2ee.com/system/vip01.webp",
        ),
        models.PaymentInfoModel(
            title="SVIP",
            intro="提案生成 50 次/天；经济性测算+AI咨询服务 60 次/天；商机实时抓取。能够添加子账号并定制公司介绍和产品广告。",
            price="12888",
            icon="https://green-img.f2ee.com/system/svip01.webp",
        ),
    ]
