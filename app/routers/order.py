import json
import time

from fastapi import APIRouter, Depends, Body, Form
from fastapi.security import OAuth2PasswordRequestForm

import app.utils.database as database
import app.utils.auth as auth
from app.order.order import add_order, update_order_status
from app.users import manage_users
from app.utils import config, cache, sms, message, exceptions
from app.models import models

from typing import Annotated

from app.utils.pay import wechat_pay
from app.utils.wx import get_phone_number

from app.utils.wx import get_openid

router = APIRouter()

amount = 0.1


# 创建订单，返回支付信息
@router.post(
    "/order/create", tags=[config.API_PROPOSAL], response_model=message.MessageModel
)
async def create(
    current_user: database.UserLogin = Depends(auth.get_current_user),
    db=Depends(database.get_db),
    code: str = Form(description="微信小程序登录code凭证"),
):
    # 使用毫秒时间戳作为order_no
    order_no = str(int(round(time.time() * 1000)))
    openid = get_openid(code)
    # 创建订单
    prepay_id = wechat_pay.pay(openid, amount, order_no, "知命解运")
    if prepay_id is None:
        return message.MessageModel(status=1, msg="创建订单失败")
    payment_params = wechat_pay.sign(prepay_id)
    await add_order(
        db,
        models.OrderModel(
            order_no=order_no,
            phone=current_user.phone,
            order_content="知命解运",
            amount=str(amount),
        ),
    )
    return message.MessageModel(
        status=0,
        msg="创建订单成功",
        data={"order_no": order_no, "payment_params": payment_params},
    )


from fastapi import Request


# 支付回调
# wechat_pay.decrypt_callback()
@router.post("/order/callback", tags=[config.API_PROPOSAL])
async def callback(
    request: Request,
    db=Depends(database.get_db),
):
    # 解密回调
    res = wechat_pay.decrypt_callback(request.headers, await request.body())

    # 解析回调数据
    json_data = json.loads(await request.body())
    print(json_data)
    event_type = json_data.get("event_type")
    res = json.loads(res)
    print(res)
    if event_type == "TRANSACTION.SUCCESS" and res["trade_state"] == "SUCCESS":
        order_no = res["out_trade_no"]
        print("order_no: %s" % order_no)
        await update_order_status(db, order_no, "PAYED")

    # 返回空字符串
    return ""
