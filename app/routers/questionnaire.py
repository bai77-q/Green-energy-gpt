import uuid
import os

from fastapi import APIRouter, Depends
from app.utils import cos, auth, database, message, config

from fastapi import UploadFile

import tempfile

router = APIRouter()


@router.post(
    "/help/upload",
    response_model=message.FileMessageModel,
    tags=[config.API_HELP],
)
async def upload_attachment(
    attachment: UploadFile = None,
    _: database.UserLogin = Depends(auth.get_current_user),
):
    """上传附件。返回status=0表示成功，其他失败。当status=0时，file_path为文件的URL地址。"""
    if attachment.size > config.MAX_ATTACHMENT_SIZE:
        return message.FileMessageModel(status=2, msg="文件大小超过限制", file_url="")
    extension = os.path.splitext(attachment.filename)[1].lower()
    if extension not in config.ALLOWED_EXTENSIONS:
        return message.FileMessageModel(status=3, msg="文件类型不支持", file_url="")
    file_name = f"attachment-{uuid.uuid4().hex}{extension}"
    with tempfile.NamedTemporaryFile() as tmp:
        tmp.write(await attachment.read())
        tmp.flush()
        print(tmp.name)
        file_path = await cos.upload_file_to_cos(tmp.name, file_name, "attachments")
    return message.construct_file_msg(file_path)
