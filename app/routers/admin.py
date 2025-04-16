from fastapi import APIRouter, Depends, Body, Form

import app.utils.database as database
import app.utils.auth as auth
from app.utils import config, psw
from app.users import manage_users
from app.utils import message

from app.models import models
from app.proposal import record


from typing import Annotated, Optional
from app.utils import cos

from datetime import date

from fastapi import UploadFile

router = APIRouter()


@router.post(
    "/admin/upgrade_user",
    response_model=message.MessageModel,
    tags=[config.API_ADMIN_MANAGE_ACCOUNT],
)
async def upgrade_regular(
    user: Annotated[models.UserUpgradeModel, Body()],
    db=Depends(database.get_db),
    _=Depends(auth.get_current_admin),
):
    """升级用户，只有三种情况：普通用户到VIP，普通用户到SVIP，VIP到SVIP"""
    if user.expired < date.today():
        return message.MessageModel(status=3, msg="过期时间不能小于当前时间")
    res = await manage_users.upgrade_user(
        db, user.userid, user.expired, int(user.target_level)
    )
    return message.construct_msg(res)


@router.get(
    "/admin/get_users_cnt",
    response_model=list[models.UserCntModel],
    tags=[config.API_ADMIN_STATISTICS],
)
async def get_users_cnt(db=Depends(database.get_db), _=Depends(auth.get_current_admin)):
    """管理员获取关于用户数量的统计信息"""
    regular_cnt, vip_cnt, svip_cnt = await manage_users.get_cnt_users(db)
    return [
        models.UserCntModel(name="普通用户", cnt=regular_cnt),
        models.UserCntModel(name="VIP用户", cnt=vip_cnt),
        models.UserCntModel(name="SVIP用户", cnt=svip_cnt),
    ]


@router.get(
    "/admin/get_records_cnt", response_model=int, tags=[config.API_ADMIN_STATISTICS]
)
async def get_records_cnt(
    db=Depends(database.get_db), _=Depends(auth.get_current_admin)
):
    """管理员获取关于近三个月提案记录数量的统计信息"""
    return await record.get_cnt_of_records(db)


@router.post(
    "/admin/add_svip",
    response_model=message.MessageModel,
    tags=[config.API_ADMIN_MANAGE_ACCOUNT],
)
async def add_svip(
    image: UploadFile,
    username: str = Form(description="用户名"),
    full_name: str = Form(description="企业名称"),
    phone: Optional[str] = Form(description="手机号", default=None),
    password: str = Form(description="密码"),
    intro: str = Form(description="简介"),
    expired: date = Form(description="到期时间"),
    child_limit: int = Form(description="子账号数量上限"),
    db=Depends(database.get_db),
    current_admin=Depends(auth.get_current_admin),
):
    """添加SVIP（不需要提前注册）"""
    svip = models.AddSVIPModel(
        username=username,
        full_name=full_name,
        phone=phone,
        password=password,
        intro=intro,
        expired=expired,
        child_limit=child_limit,
        image=config.DEFUALT_SVIP_IMAGE,
    )

    check_err = await manage_users.check_user_basic_info(db, svip)
    if check_err is not None:
        return check_err

    user_id = psw.generate_user_uuid()
    image_url = await cos.upload_image(image, user_id, "svip")
    if image_url:
        svip.image = image_url
    res = await manage_users.add_svip(db, user_id, svip)
    return message.construct_msg(res)


@router.post(
    "/admin/add_vip",
    response_model=message.MessageModel,
    tags=[config.API_ADMIN_MANAGE_ACCOUNT],
)
async def add_vip(
    image: UploadFile,
    username: str = Form(description="用户名"),
    full_name: str = Form(description="企业名称"),
    phone: Optional[str] = Form(description="手机号", default=None),
    password: str = Form(description="密码"),
    intro: str = Form(description="简介"),
    expired: date = Form(description="到期时间"),
    db=Depends(database.get_db),
    _=Depends(auth.get_current_admin),
):
    """添加VIP，不需要提前注册"""
    vip = models.AddVIPModel(
        username=username,
        full_name=full_name,
        phone=phone,
        password=password,
        expired=expired,
        intro=intro,
        image=config.DEFUALT_SVIP_IMAGE,
    )
    check_err = await manage_users.check_user_basic_info(db, vip)
    if check_err is not None:
        return check_err

    user_id = psw.generate_user_uuid()

    image_url = await cos.upload_image(image, user_id, "vip")
    if image_url:
        vip.image = image_url
    res = await manage_users.add_vip(db, user_id, vip)
    return message.construct_msg(res)


@router.post(
    "/admin/update_vip/{vip_id}",
    response_model=message.MessageModel,
    tags=[config.API_ADMIN_MANAGE_ACCOUNT],
)
async def update_vip(
    vip_id: str,
    username: Optional[str] = Form(description="用户名", default=None),
    full_name: Optional[str] = Form(description="企业名称", default=None),
    phone: Optional[str] = Form(description="手机号", default=None),
    intro: Optional[str] = Form(description="简介", default=None),
    expired: Optional[date] = Form(description="到期时间", default=None),
    image: UploadFile = None,
    db=Depends(database.get_db),
    _=Depends(auth.get_current_admin),
):
    """更新VIP"""
    vip = models.UpdateVIPModel(
        username=username,
        full_name=full_name,
        phone=phone,
        expired=expired,
        intro=intro,
        image=None,
    )

    check_err = await manage_users.check_user_basic_info(db, vip)
    if check_err is not None:
        return check_err

    if image:
        vip.image = await cos.upload_image(image, vip_id, "vip")

    res = await manage_users.update_user(db, vip_id, vip)
    return message.construct_msg(res)


@router.post(
    "/admin/update_svip/{user_id}",
    response_model=message.MessageModel,
    tags=[config.API_ADMIN_MANAGE_ACCOUNT],
)
async def update_svip(
    svip_id: str,
    username: Optional[str] = Form(description="用户名", default=None),
    full_name: Optional[str] = Form(description="企业名称", default=None),
    phone: Optional[str] = Form(description="手机号", default=None),
    intro: Optional[str] = Form(description="简介", default=None),
    expired: Optional[date] = Form(description="到期时间", default=None),
    child_limit: Optional[int] = Form(description="子账号数量上限", default=None),
    image: UploadFile = None,
    db=Depends(database.get_db),
    _=Depends(auth.get_current_admin),
):
    """更新SVIP"""
    svip = models.UpdateSVIPModel(
        username=username,
        full_name=full_name,
        phone=phone,
        intro=intro,
        expired=expired,
        child_limit=child_limit,
        image=None,
    )
    check_err = await manage_users.check_user_basic_info(db, svip)
    if check_err is not None:
        return check_err

    if image:
        svip.image = await cos.upload_image(image, svip_id, "svip")

    res = await manage_users.update_user(db, svip_id, svip)
    return message.construct_msg(res)
