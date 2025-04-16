from fastapi import HTTPException, Depends, Query
from fastapi import APIRouter
from app.utils import config, database, message
from app.models import models

from app.users import manage_users

from typing import Annotated

from app.utils.config import INNER_API_KEY

router = APIRouter()


def verify_api_key(api_key: str = Query(..., description="API key")):
    if api_key != INNER_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key


@router.get(
    "/internal/user/{user}",
    tags=[config.API_INNER],
    response_model=models.User,
)
async def read_user(
    user: str, _: str = Depends(verify_api_key), db=Depends(database.get_db)
):
    """根据用户ID或电话返回用户信息，仅内部访问"""
    return await manage_users.find_user_by_id_or_phone(
        db, user, is_userid=not user.isdigit()
    )


@router.post(
    "/internal/extend_vip",
    response_model=message.MessageModel,
    tags=[config.API_INNER],
)
async def extend_vip(
    extend: Annotated[models.VIPExtendModel, Depends()],
    _: str = Depends(verify_api_key),
    db=Depends(database.get_db),
):
    """内部接口，用于延长/缩短VIP/SVIP的到期时间；或者将普通用户升级成VIP。
    注意本接口也可以用于VIP/SVIP退款时修改其到期时间。"""
    user = await manage_users.find_user_by_id_or_phone(
        db, extend.userid, is_userid=not extend.userid.isdigit()
    )

    if user and user.account_type == config.REGULAR_LEVEL:
        res = await manage_users.upgrade_user(
            db, extend.userid, extend.expired, config.VIP_LEVEL
        )
    else:
        update_vip_model = models.UpdateVIPModel(
            expired=extend.expired,
            intro=None,
            image=None,
            full_name=None,
            username=None,
            phone=None,
        )
        res = await manage_users.update_user(db, extend.userid, update_vip_model)
    return message.construct_msg(res)


@router.post(
    "/internal/downgrade/{user}",
    tags=[config.API_INNER],
    response_model=message.MessageModel,
)
async def downgrade_vip(
    user: str, _: str = Depends(verify_api_key), db=Depends(database.get_db)
):
    """根据ID或电话将VIP降级为普通用户。仅用于调试接口，后面会删除。"""
    user = await manage_users.find_user_by_id_or_phone(
        db, user, is_userid=not user.isdigit()
    )
    if user.account_type != config.VIP_LEVEL:
        return message.construct_msg(False)

    user.account_type = config.REGULAR_LEVEL
    user.expired = None
    user.intro = None
    user.image = None

    res = await database.commit_with_rollback(db)
    return message.construct_msg(res)
