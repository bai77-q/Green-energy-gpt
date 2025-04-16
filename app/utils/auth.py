from pydantic import BaseModel
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from datetime import datetime, timedelta, date, timezone

from jose import jwt

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from . import database, config, psw
from app import dependencies

from app.utils.config import CONFIG_SETTINGS

from app.admin import meta

TOKEN_SECRET = CONFIG_SETTINGS.keys.token_secret

ALGORITHM = "HS256"
# 一个月
ACCESS_TOKEN_EXPIRE_MINUTES = 30 * 24 * 60

CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)

LIMIT_EXCEPTION = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST, detail="Exceed limits"
)

CHAT_LIMIT_EXCEPTION = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN, detail="Chat limit"
)

EXPIRED_EXCEPTION = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST, detail="VIP expired"
)


class Token(BaseModel):
    access_token: str
    token_type: str


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


async def get_user(db: AsyncSession, username: str) -> database.UserLogin:
    # 如果username全部是数字，认为是电话号码
    if username.isdigit():
        result = await db.execute(
            select(database.UserLogin).where(database.UserLogin.phone == username)
        )
    else:
        result = await db.execute(
            select(database.UserLogin).where(database.UserLogin.username == username)
        )
    return result.scalars().first()


async def get_user_by_id(db: AsyncSession, userid: str) -> database.UserLogin:
    result = await db.execute(
        select(database.UserLogin).where(database.UserLogin.id == userid)
    )
    return result.scalars().first()


def construct_login_token(login_user: database.UserLogin):
    if not login_user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": login_user.id,
            "full_name": login_user.full_name,
            "phone": login_user.phone,
        },
        expires_delta=access_token_expires,
    )
    return {"access_token": access_token, "token_type": "bearer"}


async def authenticate_user(db: AsyncSession, username: str, password: str):
    """用于登录，username可能是电话号码或者用户名"""
    user: database.UserLogin = await get_user(db, username)
    if not user:
        return False
    if not psw.verify_password(password, user.hashed_password):
        return False
    return user


async def get_user_by_phone(db: AsyncSession, phone: str):
    result = await db.execute(
        select(database.UserLogin).where(database.UserLogin.phone == phone)
    )
    return result.scalars().first()


async def get_user_by_token(db: AsyncSession, token: str):
    try:
        payload = jwt.decode(token, TOKEN_SECRET, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        print(payload.get("exp"))
        if user_id is None:
            raise CREDENTIALS_EXCEPTION
    except Exception:
        raise CREDENTIALS_EXCEPTION
    user = await get_user_by_id(db, user_id)
    return user


async def get_current_user(
    db: AsyncSession = Depends(database.get_db),
    token: str = Depends(dependencies.oauth2_scheme),
) -> database.UserLogin:
    user = await get_user_by_token(db, token)
    if user is None:
        raise CREDENTIALS_EXCEPTION
    return user


async def check_expired(db: AsyncSession, user: database.UserLogin):
    user_id = user.id
    if user.account_type == config.SUB_SVIP_LEVEL:
        user_id = user.parent_id
    res = await db.execute(
        select(database.UserLogin.expired).where(database.UserLogin.id == user_id)
    )
    expire_time: date = res.scalar_one()
    if expire_time < date.today():
        raise EXPIRED_EXCEPTION


async def check_limit(db: AsyncSession, user: database.UserLogin):
    meta_info = await meta.get_all_sys_info(db)
    record_limit_map = {
        config.REGULAR_LEVEL: meta_info.free_generate_limit,
        config.VIP_LEVEL: meta_info.vip_generate_limit,
        config.SVIP_LEVEL: meta_info.svip_generate_limit,
        config.SUB_SVIP_LEVEL: meta_info.svip_generate_limit,
    }
    if user.today_generate_cnt >= record_limit_map[user.account_type]:
        raise LIMIT_EXCEPTION
    # 更新次数
    if user.last_generate_time < date.today():
        user.today_generate_cnt = 1
        user.last_generate_time = date.today()
    else:
        user.today_generate_cnt += 1
    # 注意：后面在加入提案纪录的时候会统一commit


async def check_chat_limit(db: AsyncSession, user: database.UserLogin):
    meta_info = await meta.get_all_sys_info(db)
    chat_limit_map = {
        config.VIP_LEVEL: meta_info.vip_chat_limit,
        config.SVIP_LEVEL: meta_info.svip_chat_limit,
        config.SUB_SVIP_LEVEL: meta_info.svip_chat_limit,
    }
    if user.today_chat_cnt >= chat_limit_map[user.account_type]:
        raise CHAT_LIMIT_EXCEPTION
    # 更新次数
    if user.last_chat_time < date.today():
        user.today_chat_cnt = 1
        user.last_chat_time = date.today()
    else:
        user.today_chat_cnt += 1
    await database.commit_with_rollback(db)


async def get_current_admin(
    db: AsyncSession = Depends(database.get_db),
    token: str = Depends(dependencies.oauth2_scheme),
) -> database.UserLogin:
    user = await get_user_by_token(db, token)
    if user is None or user.account_type != config.ADMIN_LEVEL:
        raise CREDENTIALS_EXCEPTION
    return user


async def get_current_non_regular(
    db: AsyncSession = Depends(database.get_db),
    token: str = Depends(dependencies.oauth2_scheme),
) -> database.UserLogin:
    user = await get_user_by_token(db, token)
    if user is None or user.account_type == config.REGULAR_LEVEL:
        raise CREDENTIALS_EXCEPTION
    return user


async def get_current_svip(
    db: AsyncSession = Depends(database.get_db),
    token: str = Depends(dependencies.oauth2_scheme),
) -> database.UserLogin:
    user = await get_user_by_token(db, token)
    if user is None or user.account_type != config.SVIP_LEVEL:
        raise CREDENTIALS_EXCEPTION
    return user


async def get_current_admin_svip(
    db: AsyncSession = Depends(database.get_db),
    token: str = Depends(dependencies.oauth2_scheme),
) -> database.UserLogin:
    user = await get_user_by_token(db, token)
    if user is None or user.account_type not in [
        config.SVIP_LEVEL,
        config.ADMIN_LEVEL,
    ]:
        raise CREDENTIALS_EXCEPTION
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=60)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, TOKEN_SECRET, algorithm=ALGORITHM)
    return encoded_jwt
