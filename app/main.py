import os

from fastapi import FastAPI, Request
from starlette.datastructures import UploadFile as StarletteUploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
import logging
from logging.handlers import RotatingFileHandler
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import SQLAlchemyError

import json
from typing import Callable

import app.utils.database as database
import app.utils.config as config
from app.routers import (
    users,
    proposal,
    admin,
    share,
    ws_proposal,
    metas,
    svip,
    proxy,
    chat,
    ads,
    cases,
    record,
    inner,
    questionnaire,
    order,
)
import sys
import datetime

logging.getLogger("passlib").setLevel(logging.ERROR)

logger = logging.getLogger(config.LOGGER_MAIN)
logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler(sys.stdout)
log_formatter = logging.Formatter(
    "%(asctime)s [%(processName)s: %(process)d] [%(threadName)s: %(thread)d] [%("
    "levelname)s] %(name)s: %(message)s"
)
beijing = datetime.timezone(datetime.timedelta(hours=8))
log_formatter.converter = lambda *args: datetime.datetime.now(tz=beijing).timetuple()
stream_handler.setFormatter(log_formatter)
logger.addHandler(stream_handler)

file_handler = RotatingFileHandler(
    "green-api.log", maxBytes=1024 * 1024 * 500, backupCount=5
)
file_formatter = logging.Formatter(
    "%(asctime)s [%(processName)s: %(process)d] [%(threadName)s: %(thread)d] [%("
    "levelname)s] %(name)s: %(message)s"
)
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

if os.getenv("ENV", "prod").lower() == "prod":
    app = FastAPI(docs_url=None, redoc_url=None)
else:
    app = FastAPI()

routers = [
    users.router,
    proposal.router,
    admin.router,
    share.router,
    ws_proposal.router,
    metas.router,
    svip.router,
    proxy.router,
    chat.router,
    ads.router,
    cases.router,
    record.router,
    inner.router,
    questionnaire.router,
    order.router,
]
for router in routers:
    app.include_router(router)

# origins = [
#     "http://localhost",
#     "http://localhost:3000",
# ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def start_db():
    async with database.engine.begin() as conn:
        await conn.run_sync(database.Base.metadata.create_all)
        async with database.SessionLocal() as db:
            await database.init_db(db)


@app.exception_handler(StarletteHTTPException)
async def value_error_exception_handler(request: Request, exc: StarletteHTTPException):
    logger.error(f"Request: {request.url}")
    logger.error(exc)
    return JSONResponse(status_code=400, content={"message": exc.detail})


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    logger.error(f"Request: {request.url}")
    logger.error(exc, exc_info=True)
    return JSONResponse(status_code=500, content={"message": "Database Error"})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Request: {request.url}")
    logger.error(exc)
    return JSONResponse(
        status_code=422,
        content={"message": "Validation Error", "details": exc.errors()},
    )


@app.exception_handler(Exception)
async def validation_exception_handler(request: Request, exc: Exception):
    logger.error(f"Request: {request.url}")
    logger.error(exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"message": f"Internal Server Error", "details": str(exc)},
    )


async def log_request_body(request: Request, call_next: Callable):
    body = await request.body()
    content_type = request.headers.get("Content-Type", "")

    if "multipart/form-data" in content_type:
        # 处理 multipart/form-data 请求
        form = await request.form()
        body_dict = {}
        for key, value in form.items():
            if isinstance(value, StarletteUploadFile):
                body_dict[key] = f"<File: {value.filename}>"
            else:
                body_dict[key] = value
        body_str = json.dumps(body_dict, ensure_ascii=False)
    else:
        try:
            body_json = json.loads(body)
            body_str = json.dumps(body_json, ensure_ascii=False)
        except json.JSONDecodeError:
            body_str = body.decode()

    logger.info(f"Request: {request.method} {request.url}")
    logger.info(f"Body: {body_str}")

    response = await call_next(request)

    return response


@app.middleware("http")
async def exception_handling_middleware(request: Request, call_next):
    try:
        return await log_request_body(request, call_next)
    except Exception as e:
        logger.error(e, exc_info=True)
        return JSONResponse(content="Something went wrong", status_code=500)


@app.get("/")
async def index():
    return "Green Energy API v.1.0.3"
