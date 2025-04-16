from pydantic import BaseModel, Field
from typing import Optional


class MessageModel(BaseModel):
    status: int = Field(description="操作状态码，成功为0，其他表示不成功")
    msg: str = Field(description="操作消息")
    # data字段
    data: Optional[dict] = Field(description="操作数据")


class FileMessageModel(MessageModel):
    file_path: Optional[str] = Field(description="文件路径")


OK_CODE = 0
ERR_CODE = 1
OK_MSG = "操作成功"
ERR_MSG = "操作失败"


def construct_msg(res: bool):
    if res:
        return MessageModel(status=OK_CODE, msg=OK_MSG)
    else:
        return MessageModel(status=ERR_CODE, msg=ERR_MSG)


def construct_file_msg(file_path: str):
    if file_path is None:
        return FileMessageModel(status=ERR_CODE, msg=ERR_MSG, file_path=None)
    return FileMessageModel(status=OK_CODE, msg=OK_MSG, file_path=file_path)


# 初始化提案
ERR_INIT_PROPOSAL_CODE = 1
ERR_INIT_PROPOSAL_MSG = "生成提案错误，请稍后重试！"
