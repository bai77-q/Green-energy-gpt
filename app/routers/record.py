from app.utils import database, auth, config
from app.models import models
from app.proposal import record

from fastapi import APIRouter, Depends, Query

from typing import Annotated, Optional

router = APIRouter()


@router.get(
    "/records/search_records_page",
    response_model=models.RecordsResponseModel,
    tags=[config.API_ADMIN_SVIP_MANAGE],
)
async def search_records_page(
    condition: Annotated[models.RecordSearchConditionModel, Depends()],
    page: Optional[int] = Query(1, ge=1),
    db=Depends(database.get_db),
    current_user=Depends(auth.get_current_admin_svip),
):
    """管理员，SVIP 搜索所管理的提案记录，支持分页"""
    if condition.start > condition.end:
        return models.RecordsResponseModel(records=[], total_pages=0)

    offset = (page - 1) * config.PAGE_SIZE
    records = await record.search_records_by_condition(
        db,
        phone=condition.phone,
        start=condition.start,
        end=condition.end,
        user=current_user,
        offset=offset,
    )

    # 计算总页数
    total_pages = await record.get_total_pages_count(
        db,
        condition.phone,
        condition.start,
        condition.end,
        current_user,
    )

    return models.RecordsResponseModel(records=records, total_pages=total_pages)
