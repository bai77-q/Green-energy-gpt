from sqlalchemy.ext.asyncio import AsyncSession
from app.utils import database, config
from datetime import date
from sqlalchemy import select, update, func, case, and_

from app.models import models
from app.utils import message
from app.common import common

from app.utils import psw


async def check_user_basic_info(db, user_model):
    if user_model.username and not await check_username_unique(db, user_model.username):
        return message.MessageModel(status=2, msg="用户名已经注册")
    if user_model.phone and not await check_phone_unique(db, user_model.phone):
        return message.MessageModel(status=3, msg="电话号码已经注册")
    try:
        # 对于子账号，它没有单独过期的概念
        if user_model.expired and user_model.expired < date.today():
            return message.MessageModel(status=4, msg="过期时间不能小于当前时间")
    except Exception as e:
        print(e)
    return None


async def add_regular_user(db: AsyncSession, form: models.RegisterFormModel):
    """添加新的普通用户"""
    regular_user = database.UserLogin(
        id=psw.generate_user_uuid(),
        username=psw.generate_random_username(form.phone),
        full_name=form.full_name,
        phone=form.phone,
        hashed_password=psw.get_password_hash(form.password),
        account_type=config.REGULAR_LEVEL,
        last_generate_time=date.today(),
    )
    db.add(regular_user)
    return await database.commit_with_rollback(db)


async def add_vip(db: AsyncSession, user_id: str, vip_model: models.AddVIPModel):
    """添加VIP"""
    vip = database.UserLogin(
        id=user_id,
        username=vip_model.username,
        full_name=vip_model.full_name,
        phone=vip_model.phone,
        hashed_password=psw.get_password_hash(vip_model.password),
        account_type=config.VIP_LEVEL,
        expired=vip_model.expired,
        intro=vip_model.intro,
        image=vip_model.image,
        last_generate_time=date.today(),
        last_chat_time=date.today(),
    )
    db.add(vip)
    return await database.commit_with_rollback(db)


async def add_svip(db: AsyncSession, user_id: str, svip_model: models.AddSVIPModel):
    """添加SVIP"""
    svip = database.UserLogin(
        id=user_id,
        username=svip_model.username,
        full_name=svip_model.full_name,
        image=svip_model.image,
        phone=svip_model.phone,
        hashed_password=psw.get_password_hash(svip_model.password),
        account_type=config.SVIP_LEVEL,
        expired=svip_model.expired,
        intro=svip_model.intro,
        child_limit=svip_model.child_limit,
        last_generate_time=date.today(),
        last_chat_time=date.today(),
    )
    db.add(svip)
    return await database.commit_with_rollback(db)


async def get_user_expired(db: AsyncSession, user_id: str):
    """user_id必须是SVIP或VIP"""
    res = await db.execute(
        select(database.UserLogin.expired).where(database.UserLogin.id == user_id)
    )
    return res.scalar()


async def upgrade_user(
    db: AsyncSession, user_id, expire_time: date, target_level
) -> bool:
    """普通用户升级为VIP（target_level=2）/SVIP（target_level=3）；VIP升级到SVIP"""
    res = await db.execute(
        select(database.UserLogin).where(database.UserLogin.id == user_id)
    )
    old_user: database.UserLogin = res.scalar_one_or_none()
    if old_user is None:
        return False

    valid_transitions = {
        config.REGULAR_LEVEL: {config.VIP_LEVEL, config.SVIP_LEVEL},
        config.VIP_LEVEL: {config.SVIP_LEVEL},
    }
    if old_user.account_type not in valid_transitions:
        return False
    if target_level not in valid_transitions[old_user.account_type]:
        return False

    old_user.account_type = target_level
    old_user.expired = expire_time

    # reset
    old_user.today_generate_cnt = 0
    old_user.today_chat_cnt = 0
    old_user.last_generate_time = date.today()
    old_user.last_chat_time = date.today()

    if target_level == config.SVIP_LEVEL:
        old_user.child_limit = 1
    if old_user.intro is None:
        old_user.intro = "请修改企业介绍"
    if old_user.image is None:
        old_user.image = config.DEFUALT_SVIP_IMAGE

    return await database.commit_with_rollback(db)


async def check_phone_unique(db: AsyncSession, phone: str):
    """检查手机号是否唯一"""
    result = await db.execute(
        select(database.UserLogin).where(database.UserLogin.phone == phone)
    )
    return result.scalars().first() is None


async def check_username_unique(db: AsyncSession, username: str):
    """检查用户名是否唯一"""
    result = await db.execute(
        select(database.UserLogin).where(database.UserLogin.username == username)
    )
    return result.scalars().first() is None


async def add_sub_svip(db: AsyncSession, user: models.AccountModel, svip_id: str):
    """SVIP添加子账号"""
    sub_svip = database.UserLogin(
        id=psw.generate_user_uuid(),
        account_type=config.SUB_SVIP_LEVEL,
        username=user.username,
        full_name=user.full_name,
        phone=user.phone,
        hashed_password=psw.get_password_hash(user.password),
        parent_id=svip_id,
        last_generate_time=date.today(),
        last_chat_time=date.today(),
    )
    db.add(sub_svip)
    return await database.commit_with_rollback(db)


async def get_cnt_users(db: AsyncSession):
    stmt = select(
        func.count(
            case((database.UserLogin.account_type == config.REGULAR_LEVEL, 1))
        ).label("regular_cnt"),
        func.count(
            case((database.UserLogin.account_type == config.VIP_LEVEL, 1))
        ).label("vip_cnt"),
        func.count(
            case((database.UserLogin.account_type == config.SVIP_LEVEL, 1))
        ).label("svip_cnt"),
    )
    res = await db.execute(stmt)
    cnt = res.first()
    return cnt.regular_cnt, cnt.vip_cnt, cnt.svip_cnt


async def search_users_by_conditions(
    db: AsyncSession, phone: str, name: str, user_level: int, user_id: str
) -> list[database.UserLogin]:
    where_conditions = []

    if phone:
        where_conditions.append(and_(database.UserLogin.phone == phone))
    if name:
        where_conditions.append(and_(database.UserLogin.full_name.startswith(name)))

    if user_level == config.ADMIN_LEVEL:
        where_conditions.append(
            and_(database.UserLogin.account_type != config.ADMIN_LEVEL)
        )
    else:
        where_conditions.append(and_(database.UserLogin.parent_id == user_id))

    res = await db.execute(select(database.UserLogin).where(*where_conditions))
    return list(res.scalars().all())


async def _update_user_image(db: AsyncSession, user_id, image_url: str):
    await db.execute(
        update(database.UserLogin)
        .where(database.UserLogin.id == user_id)
        .values(image=image_url)
    )
    return await database.commit_with_rollback(db)


async def update_user(db: AsyncSession, user_id: str, update_model):
    return await common.update_item_by_id(db, user_id, database.UserLogin, update_model)


async def find_user_by_id_or_phone(
    db: AsyncSession, key: str, is_userid=True, parent_id: str = None
):
    where_conditions = []
    if is_userid:
        where_conditions.append(and_(database.UserLogin.id == key))
    else:
        where_conditions.append(and_(database.UserLogin.phone == key))
    if parent_id:
        where_conditions.append(and_(database.UserLogin.parent_id == parent_id))
    res = await db.execute(select(database.UserLogin).where(*where_conditions))
    return res.scalars().first()


async def update_sys_mete_data(db, update_data):
    """更新系统配置信息"""
    try:
        await db.execute(update(database.SystemMeta).values(**update_data))
        await db.commit()
    except Exception as e:
        # 如果发生错误，则回滚事务
        await db.rollback()
        raise e  # 将错误重新抛出以便调用方处理


async def get_sub_cnt(db, svip_id):
    """获取SVIP的子账号数量"""
    res = await db.execute(
        select(func.count())
        .select_from(database.UserLogin)
        .where(database.UserLogin.parent_id == svip_id)
    )
    return res.scalar()
