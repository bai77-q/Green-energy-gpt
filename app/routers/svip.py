from fastapi import APIRouter, Depends, Form

import app.utils.database as database
import app.utils.auth as auth
from app.utils import config, message
from app.users import manage_users
from app.models import models

from app.utils import cos

from typing import Optional

from fastapi import UploadFile

router = APIRouter()


@router.post(
    "/svip/add_subsvip",
    response_model=message.MessageModel,
    tags=[config.API_SVIP_MANAGE_ACCOUNT],
)
async def add_subsvip(
    username: str = Form(description="用户名（可用于登录）"),
    full_name: str = Form(description="子账号名称"),
    phone: Optional[str] = Form(description="手机号", default=None),
    password: str = Form(description="密码"),
    db=Depends(database.get_db),
    current_svip: database.UserLogin = Depends(auth.get_current_svip),
):
    """SVIP添加子账号。注意，子账号不需要提前注册，此处的电话号码也不需要验证码等操作。
    根据status判定结果。
    0：成功，其他失败
    """
    # 首先需要检查它的子账号是否超过限制
    sub_cnt = await manage_users.get_sub_cnt(db, current_svip.id)
    if sub_cnt >= current_svip.child_limit:
        return message.MessageModel(status=1, msg="超过新增子账号限制")

    user = models.AccountModel(
        username=username, full_name=full_name, phone=phone, password=password
    )
    # 检查电话号码、用户名是否可用
    check_err = await manage_users.check_user_basic_info(db, user)
    if check_err is not None:
        return check_err

    res = await manage_users.add_sub_svip(db, user, current_svip.id)
    return message.construct_msg(res)


@router.get("/get_sub_cnt", response_model=int, tags=[config.API_SVIP_STATISTICS])
async def get_sub_cnt(
    db=Depends(database.get_db),
    current_user: database.UserLogin = Depends(auth.get_current_svip),
):
    """SVIP获取子账号的数量"""
    return await manage_users.get_sub_cnt(db, current_user.id)


@router.post(
    "/profile/update_profile",
    response_model=message.MessageModel,
    tags=[config.API_ADMIN_SVIP_MANAGE],
)
async def update_profile(
    full_name: Optional[str] = Form(description="公司名称", default=None),
    intro: Optional[str] = Form(description="公司简介", default=None),
    image: UploadFile = None,
    db=Depends(database.get_db),
    current_user: database.UserLogin = Depends(auth.get_current_admin_svip),
):
    """管理员/SVIP更新公司信息"""
    image_url = None
    if image:
        # 这里并没有单独处理图片更新不成功的情况
        folder = "admin" if current_user.account_type == 0 else "svip"
        image_url = await cos.upload_image(image, current_user.id, folder)
    admin_svip = models.AdminSVIPUpdateProfileModel(
        full_name=full_name, intro=intro, image=image_url
    )
    res = await manage_users.update_user(db, current_user.id, admin_svip)

    return message.construct_msg(res)
