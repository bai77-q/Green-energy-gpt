from app.utils import database
from app.models import models
from app.utils import config, auth
from app.utils import message, cos
from app.admin import meta

from fastapi import APIRouter, Depends, Form, UploadFile

from typing import Optional

router = APIRouter()


@router.get("/sys", response_model=models.SysModel, tags=[config.API_SYS])
async def system_meta_info(db=Depends(database.get_db)):
    """获取系统的Logo和名称"""
    info = await meta.get_sys_info(db)
    return info


@router.get("/v2/sys", response_model=models.SysResponseModel, tags=[config.API_SYS])
async def system_meta_info(db=Depends(database.get_db)):
    """
    获取系统的配置信息。
    """
    return await meta.get_all_sys_info(db)


@router.get(
    "/payment_info", response_model=list[models.PaymentInfoModel], tags=[config.API_SYS]
)
async def payment_info(db=Depends(database.get_db)):
    """获取系统的支付信息"""
    return await meta.get_payment_info(db)


@router.post(
    "/admin/update_sys_meta",
    response_model=message.MessageModel,
    tags=[config.API_SYS],
)
async def update_sys_meta(
    free_generate_limit: Optional[int] = Form(None, description="免费用户提案生成上限"),
    vip_generate_limit: Optional[int] = Form(None, description="VIP提案生成上限"),
    svip_generate_limit: Optional[int] = Form(None, description="SVIP提案生成上限"),
    vip_chat_limit: Optional[int] = Form(None, description="VIP聊天上限"),
    svip_chat_limit: Optional[int] = Form(None, description="SVIP聊天上限"),
    system_name: Optional[str] = Form(None, description="系统名称"),
    system_logo: UploadFile = None,
    db=Depends(database.get_db),
    _: database.UserLogin = Depends(auth.get_current_admin),
):
    """更新系统元信息"""
    meta_info = models.SysResponseModel(
        free_generate_limit=free_generate_limit,
        vip_generate_limit=vip_generate_limit,
        svip_generate_limit=svip_generate_limit,
        vip_chat_limit=vip_chat_limit,
        svip_chat_limit=svip_chat_limit,
        system_name=system_name,
        system_logo=None,
    )
    if system_logo:
        logo_url = await cos.upload_image(system_logo, "logo", "system")
        meta_info.system_logo = logo_url

    res = await meta.update_meta(db, meta_info)
    return message.construct_msg(res)
