from fastapi import APIRouter, Depends, Body, Form
from fastapi.security import OAuth2PasswordRequestForm

import app.utils.database as database
import app.utils.auth as auth
from app.users import manage_users
from app.utils import config, cache, sms, message, exceptions
from app.models import models

from typing import Annotated

from app.utils.wx import get_phone_number

router = APIRouter()


@router.post("/login", response_model=auth.Token, tags=[config.API_SIGN_TAG])
async def login_for_token(
    db=Depends(database.get_db), form_data: OAuth2PasswordRequestForm = Depends()
):
    """使用手机号/用户名，成果返回token；失败则401错误"""
    login_user = await auth.authenticate_user(
        db, form_data.username, form_data.password
    )
    return auth.construct_login_token(login_user)


# 微信登录
@router.post("/wx_login", response_model=auth.Token, tags=[config.API_SIGN_TAG])
async def wx_login(
    db=Depends(database.get_db),
    code: str = Form(description="微信小程序获取的手机号code凭证"),
):
    print("手机号code:", code)
    """使用微信登录，成果返回token；失败则401错误"""
    phone_info = get_phone_number(code)
    phone = phone_info["phone_number"]
    if await manage_users.check_phone_unique(db, phone):
        await manage_users.add_regular_user(
            db,
            models.RegisterFormModel(
                phone=phone,
                full_name="用户" + phone[-4:],
                password=phone + "abcd",
                code="",
            ),
        )
    login_user = await auth.get_user_by_phone(db, phone)
    return auth.construct_login_token(login_user)


@router.post(
    "/send_sms", tags=[config.API_SIGN_TAG], response_model=message.MessageModel
)
async def send_sms(phone_num: Annotated[models.PhoneNumberModel, Body()]):
    """获取短信验证码，根据status判定结果。短信验证码五分钟内有效。"""
    sms_code = cache.get_sms_in_cache(phone_num.phone)
    if sms_code is not None:
        # 尚未过期（过于频繁）
        return message.MessageModel(status=1, msg="发送过于频繁，稍微重试")
    sms_code = sms.get_random_sms_code()
    if sms.send_sms(code=sms_code, phone=phone_num.phone):
        cache.add_sms_in_cache(phone_num.phone, sms_code)
        return message.MessageModel(status=message.OK_CODE, msg="发送成功")
    else:
        return message.MessageModel(status=2, msg="发送失败")


@router.post(
    "/register", tags=[config.API_SIGN_TAG], response_model=message.MessageModel
)
async def register(
    content: Annotated[models.RegisterFormModel, Body()],
    db=Depends(database.get_db),
):
    """注册普通用户，根据status判定结果。status为0表示成功"""
    # 首先判定电话是否存在
    if not await manage_users.check_phone_unique(db, content.phone):
        return message.MessageModel(status=1, msg="电话号码已经注册")
    # 再判定验证码是否正确，是否过期
    sms_code = cache.get_sms_in_cache(content.phone)
    if sms_code is None or sms_code != content.code:
        return message.MessageModel(status=2, msg="验证码不正确或已经过期")
    res = await manage_users.add_regular_user(db, content)
    if res:
        return message.MessageModel(status=message.OK_CODE, msg="注册成功")
    return message.MessageModel(status=3, msg="注册失败")


@router.get("/users/me", response_model=models.User, tags=[config.API_SIGN_TAG])
async def read_users_me(
    current_user: database.UserLogin = Depends(auth.get_current_user),
    db=Depends(database.get_db),
):
    """获取当前登录用户信息，具体参考User Model"""
    if current_user.account_type == config.SUB_SVIP_LEVEL:
        # 对于子账号，其过期时间就是SVIP的过期时间
        current_user.expired = await manage_users.get_user_expired(
            db, current_user.parent_id
        )
    return current_user


@router.get(
    "/users/search",
    response_model=list[models.User],
    tags=[config.API_ADMIN_SVIP_MANAGE],
)
async def search_users(
    condition: Annotated[models.UserSearchConditionModel, Depends()],
    db=Depends(database.get_db),
    current_user: database.UserLogin = Depends(auth.get_current_admin_svip),
):
    """管理员、SVIP能够搜索所管理的用户，根据电话或名称（名称支持前缀匹配，电话必须完全匹配）。返回用户列表。"""
    if not condition.phone and not condition.name:
        return []

    return await manage_users.search_users_by_conditions(
        db,
        condition.phone,
        condition.name,
        current_user.account_type,
        current_user.id,
    )


@router.get(
    "/users/id/{user_id}",
    response_model=models.User,
    tags=[config.API_ADMIN_SVIP_MANAGE],
)
async def get_user_by_id(
    user_id: str,
    current_user: database.UserLogin = Depends(auth.get_current_admin_svip),
    db=Depends(database.get_db),
):
    """根据用户ID返回用户具体信息，找不到或权限不够则404（SVIP仅能搜索它能管理子账号）"""
    if current_user.account_type == config.SVIP_LEVEL:
        res = await manage_users.find_user_by_id_or_phone(
            db, user_id, is_userid=True, parent_id=current_user.id
        )
    else:
        res = await manage_users.find_user_by_id_or_phone(db, user_id, is_userid=True)
    if res is None:
        raise exceptions.NO_FOUND_EXCEPTION
    return res


@router.get(
    "/users/phone/{phone}",
    response_model=models.User,
    tags=[config.API_ADMIN_SVIP_MANAGE],
)
async def get_user_by_phone(
    phone: str,
    current_user: database.UserLogin = Depends(auth.get_current_admin_svip),
    db=Depends(database.get_db),
):
    """根据用户电话返回用户具体信息，找不到或权限不够则404（SVIP仅能搜索它能管理子账号）"""
    if current_user.account_type == config.SVIP_LEVEL:
        res = await manage_users.find_user_by_id_or_phone(
            db, phone, is_userid=False, parent_id=current_user.id
        )
    else:
        res = await manage_users.find_user_by_id_or_phone(db, phone, is_userid=False)
    if res is None:
        raise exceptions.NO_FOUND_EXCEPTION
    return res
