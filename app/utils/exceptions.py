from fastapi import HTTPException, status

INIT_EXCEPTION = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST, detail="请初始化提案"
)

NO_FOUND_EXCEPTION = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND, detail="找不到纪录"
)

DOWNLOAD_EXCEPTION = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST, detail="下载异常，稍后重试"
)
