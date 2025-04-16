from app.utils import database, config

from fastapi import HTTPException, status
from fastapi import APIRouter, Depends

from sqlalchemy.ext.asyncio import AsyncSession
from app.proposal import shared

router = APIRouter()


@router.get("/shared/{link}", tags=[config.API_SHARE])
async def get_shared_content(link, db: AsyncSession = Depends(database.get_db)):
    """根据分享ID返回提案内容JSON（要处理可能的404错误）"""
    shared_record: database.SharedRecord = await shared.get_shared_by_id(db, link)
    if shared_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No such shared record"
        )
    import json

    return json.loads(shared_record.content_json)
