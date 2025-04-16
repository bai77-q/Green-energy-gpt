from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.utils import config, database
from sqlalchemy import select


class CompanyInfo(BaseModel):
    full_name: str = Field(description="公司名称", alias="name")
    image: str = Field(description="图片地址")
    # 后续需要改进，应该支持图文介绍，目前仅单段文字 TODO
    intro: str = Field(description="公司及业务介绍文字")

    class Config:
        from_attributes = True
        populate_by_name = True
        response_model_by_alias = True


async def get_company_info(db: AsyncSession, user: database.UserLogin) -> CompanyInfo:
    """返回公司介绍"""
    if user.account_type in [config.ADMIN_LEVEL, config.REGULAR_LEVEL]:
        # 普通用户和管理员都返回管理员信息
        res = await db.execute(
            select(database.UserLogin).where(database.UserLogin.id == config.ADMIN_id)
        )
        return res.scalar()
    user_id = user.id
    if user.account_type == config.SUB_SVIP_LEVEL:
        # 如果是子账号，返回其SVIP信息
        user_id = user.parent_id
    res = await db.execute(
        select(database.UserLogin).where(database.UserLogin.id == user_id)
    )
    return res.scalar()
