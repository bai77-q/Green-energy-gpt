"""Redis相关，用于记录提案ID，短信验证码"""

from pydantic import BaseModel, Field

from typing import Optional

import redis
from datetime import timedelta

from app.utils import config
from app.proposal import record

from app.utils.config import CONFIG_SETTINGS

redis_params = {
    "host": CONFIG_SETTINGS.redis.host,
    "port": CONFIG_SETTINGS.redis.port,
    "decode_responses": True,
}

if CONFIG_SETTINGS.redis.password:
    redis_params["password"] = CONFIG_SETTINGS.redis.password

print("Redis params:", redis_params)

r = redis.Redis(**redis_params)

RECORD_PREFIX = "record:"
SMS_PREFIX = "sms:"
EMBEDDING_PREFIX = "embedding:"
AD_PREFIX = "ad:"
ADMIN_PREFIX = "admin:"
WIKI_PREFIX = "wiki:"

# 用于记录提案详情
PROPOSAL_INTRO_TEXT_PREFIX = "proposal_intro_text:"
PROPOSAL_INTRO_IMAGE_PREFIX = "proposal_intro_image:"
PROPOSAL_CHART_JSON_PREFIX = "proposal_chart_json:"  # wechat only
PROPOSAL_POLICY_IMAGE = "proposal_policy_image:"
PROPOSAL_POLICY_NATION = "proposal_policy_nation:"
PROPOSAL_POLICY_LOCAL = "proposal_policy_local:"
PROPOSAL_TECH_PLAN = "proposal_tech_plan:"
PROPOSAL_TECHS = "proposal_techs:"
PROPOSAL_TECH_TEXT = "proposal_tech_text:"
PROPOSAL_TECH_IMAGE = "proposal_tech_image:"
PROPOSAL_CASES = "proposal_cases:"
PROPOSAL_CASE_TITLE = "proposal_case_title:"
PROPOSAL_CASE_TEXT = "proposal_case_text:"
PROPOSAL_CASE_IMAGE = "proposal_case_image:"


class CachedProposal(BaseModel):
    """缓存提案记录"""

    record_id: str = Field(description="提案ID")
    company: str = Field(description="所在公司，默认是用户姓名")
    province: str = Field(description="所在省份")
    city: str = Field(description="所在城市")
    business: str = Field(description="行业（一级分类）")
    category: str = Field(description="行业子分类（二级分类）")
    requirement: str = Field(description="具体需求清单")


def is_user_in_cache(phone: str):
    """通过电话检查是否在缓存中"""
    return r.exists(RECORD_PREFIX + phone)


def get_record_in_cache(phone: str):
    """通过电话获得提案信息"""
    return r.get(RECORD_PREFIX + phone)


def remove_record_in_cache(phone: str):
    r.delete(RECORD_PREFIX + phone)


def add_user_record_in_cache(phone: str, content: record.Record, record_id: str):
    """将用户初始化提案信息记录在缓存"""
    cached_proposal = CachedProposal(
        company=content.user_company,
        province=content.user_province,
        city=content.user_city,
        business=content.business,
        category=content.category,
        record_id=record_id,
        requirement=content.requirement,
    )
    proposal_json = cached_proposal.model_dump_json()
    r.set(
        RECORD_PREFIX + phone,
        proposal_json,
        ex=timedelta(seconds=config.EXPIRED_RECORD_SECOND),
    )


def add_sms_in_cache(phone: str, sms: str):
    r.set(SMS_PREFIX + phone, sms, ex=timedelta(seconds=config.EXPIRED_SMS_SECOND))


def get_sms_in_cache(phone: str):
    return r.get(SMS_PREFIX + phone)


def get_embedding_in_cache(key: str):
    return r.get(EMBEDDING_PREFIX + key)


def add_embedding_in_cache(key: str, embeddings: str):
    r.set(EMBEDDING_PREFIX + key, embeddings)


def add_ad_in_cache(key: str, ad_image: str):
    r.set(AD_PREFIX + key, ad_image)


def get_ad_in_cache(key: str):
    return r.get(AD_PREFIX + key)


def get_wiki_in_cache(key: str):
    return r.get(WIKI_PREFIX + key)


def add_wiki_in_cache(key: str, wiki: str):
    r.set(WIKI_PREFIX + key, wiki)


def add_proposal_intro_text_in_cache(user_id: str, intro_text: str):
    r.set(
        PROPOSAL_INTRO_TEXT_PREFIX + user_id,
        intro_text,
        ex=timedelta(seconds=config.EXPIRED_RECORD_SECOND),
    )


def get_proposal_intro_text_in_cache(user_id: str):
    return r.get(PROPOSAL_INTRO_TEXT_PREFIX + user_id)


def add_proposal_intro_image_in_cache(user_id: str, intro_image: str):
    r.set(
        PROPOSAL_INTRO_IMAGE_PREFIX + user_id,
        intro_image,
        ex=timedelta(seconds=config.EXPIRED_RECORD_SECOND),
    )


def get_proposal_intro_image_in_cache(user_id: str):
    return r.get(PROPOSAL_INTRO_IMAGE_PREFIX + user_id)


def add_proposal_chart_json_in_cache(user_id: str, chart_json: str):
    r.set(
        PROPOSAL_CHART_JSON_PREFIX + user_id,
        chart_json,
        ex=timedelta(seconds=config.EXPIRED_RECORD_SECOND),
    )


def get_proposal_chart_json_in_cache(user_id: str):
    return r.get(PROPOSAL_CHART_JSON_PREFIX + user_id)


def add_proposal_policy_image_in_cache(user_id: str, policy_image: str):
    r.set(
        PROPOSAL_POLICY_IMAGE + user_id,
        policy_image,
        ex=timedelta(seconds=config.EXPIRED_RECORD_SECOND),
    )


def get_proposal_policy_image_in_cache(user_id: str):
    return r.get(PROPOSAL_POLICY_IMAGE + user_id)


def add_proposal_policy_nation_in_cache(user_id: str, policy_nation: str):
    r.set(
        PROPOSAL_POLICY_NATION + user_id,
        policy_nation,
        ex=timedelta(seconds=config.EXPIRED_RECORD_SECOND),
    )


def get_proposal_policy_nation_in_cache(user_id: str):
    return r.get(PROPOSAL_POLICY_NATION + user_id)


def add_proposal_policy_local_in_cache(user_id: str, policy_local: str):
    r.set(
        PROPOSAL_POLICY_LOCAL + user_id,
        policy_local,
        ex=timedelta(seconds=config.EXPIRED_RECORD_SECOND),
    )


def get_proposal_policy_local_in_cache(user_id: str):
    return r.get(PROPOSAL_POLICY_LOCAL + user_id)


def add_proposal_tech_plan_in_cache(user_id: str, tech_plan: str):
    r.set(
        PROPOSAL_TECH_PLAN + user_id,
        tech_plan,
        ex=timedelta(seconds=config.EXPIRED_RECORD_SECOND),
    )


def get_proposal_tech_plan_in_cache(user_id: str):
    return r.get(PROPOSAL_TECH_PLAN + user_id)


def add_proposal_techs(user_id, techs: list[str]):
    r.set(
        PROPOSAL_TECHS + user_id,
        "|".join(techs),
        ex=timedelta(seconds=config.EXPIRED_RECORD_SECOND),
    )


def get_proposal_techs(user_id) -> list[str]:
    return r.get(PROPOSAL_TECHS + user_id).split("|")


def add_proposal_cases(user_id, cases: list[int]):
    r.set(
        PROPOSAL_CASES + user_id,
        "|".join([str(case) for case in cases]),
        ex=timedelta(seconds=config.EXPIRED_RECORD_SECOND),
    )


def get_proposal_cases(user_id) -> list[int]:
    return [int(case) for case in r.get(PROPOSAL_CASES + user_id).split("|")]


def add_proposal_tech_text_in_cache(user_id: str, tech_name: str, tech_text: str):
    r.set(
        f"{PROPOSAL_TECH_TEXT}{user_id}-{tech_name}",
        tech_text,
        ex=timedelta(seconds=config.EXPIRED_RECORD_SECOND),
    )


def is_proposal_tech_text_in_cache(user_id: str, tech_name: str):
    return r.exists(f"{PROPOSAL_TECH_TEXT}{user_id}-{tech_name}")


def get_proposal_tech_text_in_cache(user_id: str, tech_name: str):
    return r.get(f"{PROPOSAL_TECH_TEXT}{user_id}-{tech_name}")


def add_proposal_tech_image_in_cache(user_id: str, tech_name: str, tech_image: str):
    r.set(
        f"{PROPOSAL_TECH_IMAGE}{user_id}-{tech_name}",
        tech_image,
        ex=timedelta(seconds=config.EXPIRED_RECORD_SECOND),
    )


def is_proposal_tech_image_in_cache(user_id: str, tech_name: str):
    return r.exists(f"{PROPOSAL_TECH_IMAGE}{user_id}-{tech_name}")


def get_proposal_tech_image_in_cache(user_id: str, tech_name: str):
    return r.get(f"{PROPOSAL_TECH_IMAGE}{user_id}-{tech_name}")


def add_proposal_case_text_in_cache(user_id: str, case_id: int, case_text: str):
    r.set(
        f"{PROPOSAL_CASE_TEXT}{user_id}-{case_id}",
        case_text,
        ex=timedelta(seconds=config.EXPIRED_RECORD_SECOND),
    )


def is_proposal_case_text_in_cache(user_id: str, case_id: int):
    return r.exists(f"{PROPOSAL_CASE_TEXT}{user_id}-{case_id}")


def get_proposal_case_text_in_cache(user_id: str, case_id: int):
    return r.get(f"{PROPOSAL_CASE_TEXT}{user_id}-{case_id}")


def add_proposal_case_image_in_cache(user_id: str, case_id: int, case_image: str):
    r.set(
        f"{PROPOSAL_CASE_IMAGE}{user_id}-{case_id}",
        case_image,
        ex=timedelta(seconds=config.EXPIRED_RECORD_SECOND),
    )


def get_proposal_case_image_in_cache(user_id: str, case_id: int):
    return r.get(f"{PROPOSAL_CASE_IMAGE}{user_id}-{case_id}")


def add_proposal_case_title_in_cache(user_id: str, case_id: int, case_title: str):
    r.set(
        f"{PROPOSAL_CASE_TITLE}{user_id}-{case_id}",
        case_title,
        ex=timedelta(seconds=config.EXPIRED_RECORD_SECOND),
    )


def get_proposal_case_title_in_cache(user_id: str, case_id: int):
    return r.get(f"{PROPOSAL_CASE_TITLE}{user_id}-{case_id}")
