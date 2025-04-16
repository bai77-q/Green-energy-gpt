from datetime import datetime

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy import Column, String, Integer, DateTime, Date, ForeignKey, Text, Enum
from sqlalchemy import select
from . import config

SQLALCHEMY_DATABASE_URL = config.CONFIG_SETTINGS.db.url

if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    # SQLite数据库不支持pool_size和max_overflow等
    engine = create_async_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}, echo=True
    )
else:
    engine = create_async_engine(
        SQLALCHEMY_DATABASE_URL,
        echo=True,
        pool_size=20,
        max_overflow=0,
        pool_pre_ping=True,
    )

Base = declarative_base()
SessionLocal = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db():
    session = SessionLocal()
    try:
        yield session
    finally:
        await session.close()


class IntroImage(Base):
    """行业介绍图片"""

    __tablename__ = "intro_image"
    id = Column(Integer, primary_key=True, autoincrement=True)
    business = Column(String(20), index=True, comment="行业")
    category = Column(String(20), index=True, comment="子行业")
    url = Column(String(512), comment="行业介绍图片")


class ClassicCase(Base):
    """案例"""

    __tablename__ = "classic_case"
    id = Column(Integer, primary_key=True, autoincrement=True)
    business = Column(String(20), index=True, comment="行业")
    category = Column(String(20), index=True, comment="子行业")
    project_name = Column(String(100), index=True, comment="案例名")
    project_profile = Column(Text, comment="案例简介")
    benefit = Column(Text, comment="案例优势")
    summarize_experience = Column(Text, comment="案例总结和经验")
    image_url = Column(Text, comment="案例图片")


class UserLogin(Base):
    """用户登录的表，可以使用username或者phone登录，为了降低判定难度，username要求不能是全部数字"""

    __tablename__ = "user_login"
    # id用于内部标识
    id = Column(String(128), primary_key=True, index=True)
    # 用户名不可为空
    username = Column(String(128), index=True, unique=True, nullable=False)
    # 建议VIP、SVIP用户使用企业名
    full_name = Column(String(40), index=True, comment="姓名（仅仅用于展示）")
    # 电话可以为空
    phone = Column(String(20), index=True, unique=True)
    hashed_password = Column(String(128), nullable=False)
    # 账户类型很重要，包括0（管理员）、1（普通用户）、2（VIP）、3（SVIP）、4（子账户）
    account_type = Column(Integer, comment="账户类型", nullable=False)
    avatar = Column(
        String(256), default="https://green-img.f2ee.com/default/default_avatar.png"
    )
    expired = Column(Date)

    # 今日生成次数
    today_generate_cnt = Column(Integer, default=0)
    # 上次生成时间
    last_generate_time = Column(Date)
    # 今日对话次数
    today_chat_cnt = Column(Integer, default=0)
    # 上次对话时间
    last_chat_time = Column(Date)
    # 图片
    image = Column(String(256))
    # 企业介绍文字
    intro = Column(Text)
    # 定义子账号关系
    parent_id = Column(String(128), ForeignKey("user_login.id"), nullable=True)
    # 子账号数量
    child_limit = Column(Integer)
    children = relationship("UserLogin", remote_side=[id], backref="parent")


class SystemMeta(Base):
    """系统元数据，包括多个key-value，只有一条记录！！"""

    __tablename__ = "system_meta"
    id = Column(Integer, primary_key=True, autoincrement=True)
    # 免费用户每天提案生成次数限制
    free_generate_limit = Column(Integer, default=1)
    # VIP用户每天提案生成次数限制
    vip_generate_limit = Column(Integer, default=50)
    # SVIP用户（及其子账号）每天提案生成次数限制
    svip_generate_limit = Column(Integer, default=50)
    # VIP用户每天聊天次数限制
    vip_chat_limit = Column(Integer, default=50)
    # SVIP用户（及其子账号）每天聊天次数限制
    svip_chat_limit = Column(Integer, default=50)
    # 系统的名称
    system_name = Column(String(128))
    system_logo = Column(String(256))
    # 下面的配置暂时在UI不可见
    free_nation_policy = Column(Integer, default=1)
    free_local_policy = Column(Integer, default=1)
    vip_nation_policy = Column(Integer, default=1)
    vip_local_policy = Column(Integer, default=2)
    free_case = Column(Integer, default=2)
    vip_case = Column(Integer, default=4)
    free_tech = Column(Integer, default=2)
    vip_tech = Column(Integer, default=4)
    free_tech_words = Column(Integer, default=200)
    vip_tech_words = Column(Integer, default=400)
    free_case_words = Column(Integer, default=400)
    vip_case_words = Column(Integer, default=800)


class GenerateRecord(Base):
    """生成提案的记录
    这个设计有点冗余，主要为了方便搜索
    """

    __tablename__ = "generate_record"
    id = Column(String(128), primary_key=True)
    record_time = Column(DateTime, index=True)
    user_id = Column(String(128), ForeignKey("user_login.id"), index=True)
    svip_id = Column(String(128), ForeignKey("user_login.id"), index=True)
    # 提案人姓名/公司名称，目前的设计允许和账号本身的不一样
    user_name = Column(String(20))
    user_company = Column(String(20))
    user_province = Column(String(20))
    user_city = Column(String(20))
    user_phone = Column(String(20))
    business = Column(String(20))
    category = Column(String(20))
    # 其他业务需求
    requirements = Column(String(1000), default="")
    # 人工接入需求（帮助），后续可能为设计成问卷
    artificial_help = Column(Text, default="")


class Ads(Base):
    """广告信息"""

    __tablename__ = "ads"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(128), ForeignKey("user_login.id"), index=True)
    business = Column(String(128), index=True)
    category = Column(String(128), index=True)
    tech = Column(String(128), index=True)
    image_url = Column(String(256))
    ad_info = Column(Text)


class SharedRecord(Base):
    """分享的提案。目前不直接纪录谁分享的。"""

    __tablename__ = "shared_record"
    id = Column(String(128), primary_key=True, index=True)
    shared_time = Column(DateTime)
    # 分享人姓名
    shared_by = Column(String(128))
    # 直接把分享内容保存成JSON
    content_json = Column(Text)


class NationalPolicy(Base):
    """全国性政策文件"""

    __tablename__ = "national_policy"
    policy_id = Column(Integer, primary_key=True, autoincrement=True)
    policy_business = Column(String(20), index=True)
    policy_category = Column(String(20), index=True)
    policy_content = Column(Text)
    image_url = Column(Text)


class LocalPolicy(Base):
    """地方政策文件"""

    __tablename__ = "local_policy"
    policy_id = Column(Integer, primary_key=True, autoincrement=True)
    policy_business = Column(String(20), index=True)
    policy_category = Column(String(20), index=True)
    policy_province = Column(String(20), index=True)
    policy_city = Column(String(20), index=True)
    # 政策内容
    policy_content = Column(Text)
    # 政策图片连接
    image_url = Column(Text)


class Order(Base):
    """订单"""

    __tablename__ = "order"
    id = Column(Integer, primary_key=True, autoincrement=True)
    # 下单人手机号
    phone = Column(String(20), ForeignKey("user_login.phone"))
    # 订单号，唯一
    order_no = Column(String(20), index=True)
    # 创建时间。默认是当前时间
    order_time = Column(DateTime, default=datetime.now)
    # 未支付 NOT_PAYED, 已支付 PAYED
    order_status = Column(Enum("NOT_PAYED", "PAYED"), default="NOT_PAYED")
    # 订单内容，可为空
    order_content = Column(Text, nullable=True)
    # 金额
    amount = Column(String(20), default="")


class TechPoint(Base):
    """技术点"""

    __tablename__ = "tech_point"
    tech_id = Column(Integer, primary_key=True, autoincrement=True)
    business = Column(String(20))
    category = Column(String(20))
    tech = Column(String(20), index=True)


class TechAdMatch(Base):
    """技术点和广告的匹配"""

    __tablename__ = "tech_ad_match"
    id = Column(Integer, primary_key=True, autoincrement=True)
    tech_id = Column(Integer, ForeignKey("tech_point.tech_id"), index=True)
    ad_user_id = Column(String(128), ForeignKey("user_login.id"), index=True)
    ad_id = Column(Integer, ForeignKey("ads.id"), index=True)


async def commit_with_rollback(db: AsyncSession):
    success = True
    try:
        await db.commit()
    except Exception as e:
        print("commit_with_roallback", e)
        await db.rollback()
        await db.flush()
        success = False
    return success


async def init_db(db: AsyncSession):
    res = await db.execute(select(SystemMeta))
    if res.scalar_one_or_none():
        return
    from . import psw

    # 添加默认管理员
    new_admin = UserLogin(
        id=config.ADMIN_id,
        account_type=config.ADMIN_LEVEL,
        hashed_password=psw.get_password_hash(config.Admin_Password),
        phone=config.Admin_Phone,
        username=config.Admin_Name,
        full_name=config.COMPANY_NAME,
        image=config.COMPANY_IMAGE,
        intro=config.COMPANY_INTRO,
    )
    db.add(new_admin)
    # 用于小程序的审核账号
    test_wechat = UserLogin(
        id=config.Wechat_Name,
        account_type=config.VIP_LEVEL,
        username=config.Wechat_Name,
        phone=config.Wechat_Phone,
        full_name=config.Wechat_Full_Name,
        image=config.COMPANY_IMAGE,
        intro=config.COMPANY_INTRO,
        hashed_password=psw.get_password_hash("1234abcd"),
    )
    db.add(test_wechat)
    # 添加Meta信息
    init_meta = SystemMeta(
        system_name=config.SYSTEM_NAME,
        system_logo=config.SYSTEM_LOGO,
    )
    db.add(init_meta)
    # 初始化技术点
    for business in config.TECH_DICT:
        for category, tech_names in config.TECH_DICT[business].items():
            for tech_name in tech_names:
                new_tech = TechPoint(
                    business=business, category=category, tech=tech_name
                )
                db.add(new_tech)
    await db.commit()
