from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import models
from app.utils import database


async def add_order(db: AsyncSession, form: models.OrderModel):
    """添加新的普通用户"""
    regular_user = database.Order(
        order_no=form.order_no,
        phone=form.phone,
        order_content=form.order_content,
        amount=form.amount,
    )
    db.add(regular_user)
    return await database.commit_with_rollback(db)


# 更新order status
async def update_order_status(db: AsyncSession, order_no: str, status: str):
    """更新order status"""
    order = await db.execute(
        update(database.Order)
        .where(database.Order.order_no == order_no)
        .values(order_status=status)
    )
    return await database.commit_with_rollback(db)
