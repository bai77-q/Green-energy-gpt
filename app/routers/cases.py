from fastapi import APIRouter, Depends, Form, Query
import app.utils.database as database
import app.utils.auth as auth
from app.utils import config
from app.cases import manage_cases
from app.utils import message, cos
from app.common import common

from app.models import models
from typing import Optional

from fastapi import UploadFile

router = APIRouter()


@router.post(
    "/admin/add_case",
    response_model=message.MessageModel,
    tags=[config.API_CASE_MANAGE],
)
async def admin_add_case(
    image: UploadFile,
    business: str = Form(..., description="业务一级分类"),
    category: str = Form(..., description="业务二级分类"),
    project_name: str = Form(..., description="案例名"),
    project_profile: str = Form(..., description="案例简介"),
    benefit: str = Form(..., description="案例优势"),
    summarize_experience: str = Form(..., description="案例总结和经验"),
    db=Depends(database.get_db),
    _=Depends(auth.get_current_admin),
):
    """管理员添加案例"""
    res = await manage_cases.add_case(
        db,
        business,
        category,
        project_name,
        project_profile,
        benefit,
        summarize_experience,
        image,
    )
    return message.construct_msg(res)


@router.get(
    "/admin/search_cases/{business}",
    response_model=models.CasesResponseModel,
    tags=[config.API_CASE_MANAGE],
)
async def search_cases_by_business(
    business: str,
    page: Optional[int] = Query(default=1, gt=0),
    db=Depends(database.get_db),
    _=Depends(auth.get_current_admin),
):
    """管理员根据行业分类搜索查看案例。"""
    cases = await common.search_items_by_business(
        db, business, database.ClassicCase, page
    )
    total_pages = await common.pages_by_business(db, business, database.ClassicCase)

    return models.CasesResponseModel(cases=cases, total_pages=total_pages)


@router.post(
    "/admin/update_case/{case_id}",
    response_model=message.MessageModel,
    tags=[config.API_CASE_MANAGE],
)
async def admin_update_case(
    case_id: int,
    image: UploadFile = None,
    business: Optional[str] = Form(description="业务一级分类", default=None),
    category: Optional[str] = Form(description="业务二级分类", default=None),
    project_name: Optional[str] = Form(description="案例名", default=None),
    project_profile: Optional[str] = Form(description="案例简介", default=None),
    benefit: Optional[str] = Form(description="案例优势", default=None),
    summarize_experience: Optional[str] = Form(
        description="案例总结和经验", default=None
    ),
    db=Depends(database.get_db),
    _=Depends(auth.get_current_admin),
):
    """更新案例"""
    image_url = None
    if image:
        image_url = await cos.upload_image(image, f"{case_id}", "cases")

    update_case_model = models.UpdateCaseModel(
        business=business,
        category=category,
        project_name=project_name,
        project_profile=project_profile,
        benefit=benefit,
        summarize_experience=summarize_experience,
        image_url=image_url,
    )
    res = await manage_cases.update_case(db, case_id, update_case_model)
    return message.construct_msg(res)


@router.post(
    "/admin/delete_case/{case_id}",
    response_model=message.MessageModel,
    tags=[config.API_CASE_MANAGE],
)
async def admin_delete_case(
    case_id: int, db=Depends(database.get_db), _=Depends(auth.get_current_admin)
):
    """删除案例"""
    res = await manage_cases.delete_case(db, case_id)
    return message.construct_msg(res)
