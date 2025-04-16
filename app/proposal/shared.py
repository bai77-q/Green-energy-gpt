from sqlalchemy.ext.asyncio import AsyncSession

from app.utils import database, cache
from app.utils import download
from app.proposal import company
from sqlalchemy import select

from datetime import datetime
import json


def generate_shared_id():
    import os
    import base64

    return f"share-{base64.urlsafe_b64encode(os.urandom(6)).decode()}"


async def add_shared_record(db: AsyncSession, share: database.SharedRecord):
    db.add(share)
    return await database.commit_with_rollback(db)


async def get_shared_by_id(db: AsyncSession, share_id: str):
    res = await db.execute(
        select(database.SharedRecord).where(database.SharedRecord.id == share_id)
    )
    return res.scalars().first()


async def generate_shared_from_cache(
    db: AsyncSession, gpt_client, user: database.UserLogin
):
    shared_id = generate_shared_id()
    company_info: company.CompanyInfo = await company.get_company_info(db, user)
    await download.generate_remaining_proposal(db, gpt_client, user)
    techs = []
    for tech in cache.get_proposal_techs(user.id):
        tech_txt = cache.get_proposal_tech_text_in_cache(user.id, tech)
        tech_img = cache.get_proposal_tech_image_in_cache(user.id, tech)
        techs.append({"tech_name": tech, "tech_intro": tech_txt, "tech_img": tech_img})
    cases = []
    for case in cache.get_proposal_cases(user.id):
        case_txt = cache.get_proposal_case_text_in_cache(user.id, case)
        case_img = cache.get_proposal_case_image_in_cache(user.id, case)
        case_name = cache.get_proposal_case_title_in_cache(user.id, case)
        cases.append(
            {"case_name": case_name, "case_intro": case_txt, "case_img": case_img}
        )
    content = {
        "intro_txt": cache.get_proposal_intro_text_in_cache(user.id),
        "intro_img": cache.get_proposal_intro_image_in_cache(user.id),
        "intro_chart": cache.get_proposal_chart_json_in_cache(user.id),
        "policy_img": cache.get_proposal_policy_image_in_cache(user.id),
        "policy_nation_txt": cache.get_proposal_policy_nation_in_cache(user.id),
        "policy_local_txt": cache.get_proposal_policy_local_in_cache(user.id),
        "company_name": company_info.full_name,
        "company_intro": company_info.intro,
        "company_img": company_info.image,
        "plan_flow": "",
        "plan_intro": cache.get_proposal_tech_plan_in_cache(user.id),
        "techs": techs,
        "cases": cases,
    }
    shared_record: database.SharedRecord = database.SharedRecord(
        id=shared_id,
        shared_by=user.full_name,
        shared_time=datetime.now(),
        content_json=json.dumps(content),
    )
    res = await add_shared_record(db, shared_record)
    if res:
        return shared_id
    else:
        return None
