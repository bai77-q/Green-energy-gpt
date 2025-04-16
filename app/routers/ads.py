from fastapi import APIRouter, Depends, Form, Query
import app.utils.database as database
import app.utils.auth as auth
from app.utils import config
from app.utils import message, cos
from app.ads import ads as ads_util
from app.users import manage_users
from app.models import models
from typing import Optional

from fastapi import UploadFile

router = APIRouter()


@router.post(
    "/ads/add", response_model=message.MessageModel, tags=[config.API_AD_MANAGE]
)
async def add_ads(
    image: UploadFile,
    business: str = Form(..., description="业务一级分类"),
    category: str = Form(..., description="业务二级分类"),
    tech: str = Form(..., description="技术名称"),
    ad_info: str = Form(..., description="广告内容"),
    db=Depends(database.get_db),
    current_user=Depends(auth.get_current_admin_svip),
):
    """管理员，SVIP添加自己的广告"""
    res = await ads_util.add_ad(
        db, current_user.id, business, category, tech, ad_info, image
    )
    return message.construct_msg(bool(res))


@router.post(
    "/admin/add_ad/{user_id}",
    response_model=message.MessageModel,
    tags=[config.API_AD_MANAGE],
)
async def admin_add_ad(
    user_id: str,
    image: UploadFile,
    business: str = Form(..., description="业务一级分类"),
    category: str = Form(..., description="业务二级分类"),
    tech: str = Form(..., description="技术名称"),
    ad_info: str = Form(..., description="广告内容"),
    db=Depends(database.get_db),
    current_user=Depends(auth.get_current_admin),
):
    """管理员为VIP/SVIP添加广告。
    注意，添加分两个步骤：
    1）管理员使用 /users/phone/{phone} 接口得到用户信息（包括user_id），并让用户确认（只有VIP/SVIP才进入第二步）；
    2）再使用本接口"""
    res, _ = await ads_util.add_ad(
        db, user_id, business, category, tech, ad_info, image
    )
    return message.construct_msg(bool(res))


@router.post(
    "/ads/update/{ad_id}",
    response_model=message.MessageModel,
    tags=[config.API_AD_MANAGE],
)
async def update_ads(
    ad_id: int,
    image: UploadFile = None,
    business: Optional[str] = Form(description="业务一级分类", default=None),
    category: Optional[str] = Form(description="业务二级分类", default=None),
    tech: Optional[str] = Form(description="技术名称", default=None),
    ad_info: Optional[str] = Form(description="广告内容", default=None),
    db=Depends(database.get_db),
    current_user=Depends(auth.get_current_admin_svip),
):
    """管理员或SVIP更新广告。"""
    image_url = None
    if image:
        image_url = await cos.upload_image(image, f"{ad_id}", "ads")

    update_model = models.UpdateAdModel(
        business=business,
        category=category,
        tech=tech,
        ad_info=ad_info,
        image_url=image_url,
    )

    res = await ads_util.update_ad(db, ad_id, current_user, update_model)
    return message.construct_msg(res)


@router.get(
    "/ads/business/{business}",
    response_model=models.AdsResponseModel,
    tags=[config.API_AD_MANAGE],
)
async def search_ads_by_business(
    business: str,
    page: Optional[int] = Query(default=1, gt=0),
    db=Depends(database.get_db),
    current_user=Depends(auth.get_current_admin_svip),
):
    """管理员/SVIP根据行业分类查看自己的广告。"""
    ads = await ads_util.search_ads_by_userid(db, current_user.id, page, business)
    total_pages = await ads_util.ads_pages_by_userid(db, current_user.id, business)

    return models.AdsResponseModel(ads=ads, total_pages=total_pages)


@router.get(
    "/admin/ads/{phone}",
    tags=[config.API_AD_MANAGE],
    response_model=models.AdsResponseModel,
)
async def get_all_ads(
    phone: str,
    page: Optional[int] = Query(default=1, gt=0),
    db=Depends(database.get_db),
    current_admin=Depends(auth.get_current_admin),
):
    """管理员根据电话号码查看某个VIP/SVIP的广告"""
    user = await manage_users.find_user_by_id_or_phone(db, phone, is_userid=False)
    if user is None or user.account_type not in [
        config.ADMIN_LEVEL,
        config.VIP_LEVEL,
        config.SVIP_LEVEL,
    ]:
        return models.AdsResponseModel(ads=[], total_pages=0)
    ads = await ads_util.search_ads_by_userid(db, user.id, page)
    total_pages = await ads_util.ads_pages_by_userid(db, user.id)
    return models.AdsResponseModel(ads=ads, total_pages=total_pages)
