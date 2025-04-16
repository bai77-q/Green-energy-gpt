from pydantic import BaseModel, Field, field_validator

from dataclasses import dataclass

from fastapi import Query

from datetime import date, datetime
from typing import List, Optional


class PhoneNumberModel(BaseModel):
    phone: str = Field(
        description="国内11位电话号码，用于获取短信验证码",
        min_length=11,
        max_length=11,
        pattern=r"^1[3-9]\d{9}$",
    )


class RegisterFormModel(BaseModel):
    full_name: str = Field(description="用户名称（用于显示，不用于登录）")
    phone: str = Field(description="手机号码")
    password: str = Field(description="密码")
    code: str = Field(description="验证码")


class ImageURLModel(BaseModel):
    url: str = Field(description="图片URL")


class ChartContent(BaseModel):
    content: str = Field(
        ...,
        title="行业介绍描述（用于生成bar chart等），内容来自于接口 /proposal/intro_txt",
        example="自2018年以来，酒店建筑的能源效率提升比例逐年攀升，由20%增至30%。这反映了业界对于采用先进技术和设计理念的不懈追求，以减少能源浪费。  其次，LED照明技术的广泛应用也在不断推动节能进程。照明是建筑能源消耗的一个主要领域，而自2017年以来，酒店业对LED照明的应用率从40%迅速提升至2020年的95%，实现了明显的节能效果。  酒店业对可再生能源的采用也在逐年增加，从2018年的5%上升至2020年的15%。这表明酒店业正在积极转向更环保的能源来源，减少对传统能源的依赖。  最后，智能建筑系统的应用范围也在迅速扩大。2017年时，仅有40%的酒店使用智能建筑系统，而到2020年，这一比例已经增长至90%。这不仅提高了建筑的运行效率，还通过实时监测和调整，最大程度地降低了能源浪费。",
    )


class PlanModel(BaseModel):
    """方案整理介绍以及关键技术名称列表"""

    intro: str = Field(description="方案整体介绍")
    techs: list[str] = Field(description="技术名称列表")


class TechDetail(BaseModel):
    tech_name: str
    tech_img: str


class Planv2Model(BaseModel):
    """方案整理介绍以及关键技术点详情列表"""

    intro: str = Field(description="方案整体介绍")
    techs: List[TechDetail] = Field(description="技术点详情列表")


@dataclass
class Tech:
    tech: str = Query(..., description="技术名称", example="空调隔热")


class FlowContent(BaseModel):
    content: str = Field(
        ...,
        title="技术概要描述",
        example="1. 能源审查和评估：      进行全面的建筑能源审查，包括空调设备、建筑隔热性能、用电设备等。     "
        "利用先进的能源模拟软件，分析建筑热负荷，确定最佳的空调系统容量。  2. 设备更新和优化：      替换老化可再生能源。     "
        "考虑地源热泵系统，充分利用地下稳定的温度来提供空调所需的冷热能源。  4. 智能控制系统的引入：      部署先进的传感器网络，实时监测室内环境参数。     "
        "利用人体感应技术，调整空调系统运行状态，确保只有在需要的时候才启动。  5. 空气流通和隔热改进：      优化建筑风道设计，确保空气流通畅通。     "
        "更新建筑外墙和窗户隔热材料，减小冷热交换。",
    )


class TechModel(BaseModel):
    """关键技术"""

    tech_name: str = Field(description="技术名称")
    tech_img: str = Field(description="技术图片URL")
    tech_intro: str = Field(description="技术描述")


class CaceModel(BaseModel):
    """案例"""

    case_name: str = Field(description="案例名称")
    case_img: str = Field(description="案例图片URL")
    case_intro: str = Field(description="案例介绍")


class ProposalModel(BaseModel):
    """当前提案的所有信息，用于分享"""

    intro_txt: str = Field(description="行业介绍文字")
    intro_img: str = Field(description="行业介绍图片URL")
    intro_chart: str = Field(description="行业介绍的Chart JSON")
    policy_img: str = Field(description="政策图片的URL")
    policy_nation_txt: str = Field(description="国家政策文字")
    policy_local_txt: str = Field(description="地方政策文字")
    company_name: str = Field(description="公司名称")
    company_img: str = Field(description="公司图片URL")
    company_intro: str = Field(description="公司介绍文字")
    plan_intro: str = Field(description="整体技术方案文字")
    plan_flow: str = Field(description="整体技术方案流程图 JSON")
    techs: list[TechModel] = Field(description="技术点")
    cases: list[CaceModel] = Field(description="案例")


class LinkModel(BaseModel):
    link: str = Field(description="分享的链接")


class HelpModel(BaseModel):
    content: str = Field(description="生成提案后，用户填写的人工介入信息")


class AdAccountModel(BaseModel):
    name: str = Field(description="用户类型")
    price: str = Field(description="每年定价")
    intros: list[str] = Field(description="权益介绍")


class SysModel(BaseModel):
    name: str = Field(description="系统名称", example="智慧探索")
    logo: str = Field(description="logo的URL")


class SysResponseModel(BaseModel):
    free_generate_limit: Optional[int] = Field(
        description="普通用户每日生成次数上限", gt=0
    )
    vip_generate_limit: Optional[int] = Field(
        ..., description="VIP用户每日生成次数上限", gt=0
    )
    svip_generate_limit: Optional[int] = Field(
        ..., description="SVIP用户每日生成次数上限", gt=0
    )
    vip_chat_limit: Optional[int] = Field(
        ..., description="VIP用户每日聊天次数上限", gt=0
    )
    svip_chat_limit: Optional[int] = Field(
        ..., description="SVIP每日聊天次数上限", gt=0
    )
    system_name: Optional[str] = Field(..., description="系统名称")
    system_logo: Optional[str] = Field(..., description="系统logo")

    class Config:
        from_attributes = True


class User(BaseModel):
    """用于返回/users/me和搜索"""

    username: str
    full_name: str
    # 用户等级。0：管理员，1: 普通用户，2：VIP，3：SVIP，4：子账号
    account_type: int
    phone: Optional[str]
    id: str = Field(description="用户ID", alias="user_id")
    expired: Optional[date]
    image: Optional[str]
    intro: Optional[str]
    parent_id: Optional[str]
    child_limit: Optional[int]

    class Config:
        from_attributes = True
        populate_by_name = True
        response_model_by_alias = True


class VIPExtendModel(BaseModel):
    userid: str = Field(description="用户ID")
    expired: date = Field(description="到期时间 YYYY-MM-DD")


class UserUpgradeModel(VIPExtendModel):
    target_level: str = Field(description="目标用户等级（VIP：2，SVIP：3）")


class UserCntModel(BaseModel):
    name: str = Field(description="用户类型")
    cnt: int = Field(description="用户数量")


class UserSearchConditionModel(BaseModel):
    """按电话或用户名搜索用户（用户名支持前缀）"""

    phone: str = Field(description="电话", default="")
    name: str = Field(description="企业名称", default="")


class RecordSearchConditionModel(BaseModel):
    """按电话或时间搜索"""

    phone: str = Field(description="电话", default="")
    start: date = Field(description="开始时间", default=date(year=2024, month=1, day=1))
    end: date = Field(description="结束时间", default=date.today())


class RecordModel(BaseModel):
    id: str = Field(description="记录ID", alias="generate_id")
    record_time: datetime = Field(description="记录时间")
    user_id: str = Field(description="用户ID")
    # 提案人姓名/公司名称
    user_name: str = Field(description="用户名称")
    user_company: str = Field(description="用户公司")
    user_province: str = Field(description="用户所在省份")
    user_city: str = Field(description="用户所在城市")
    # 提案人电话
    user_phone: str = Field(description="用户电话")
    # 业务一级分类
    business: str = Field(description="业务一级分类")
    # 业务二级分类
    category: str = Field(description="业务二级分类")
    # 其他业务需求
    requirements: str = Field(description="其他业务需求", default="")
    # 人工接入需求（帮助）
    artificial_help: str = Field(description="人工接入需求", default="")

    class Config:
        from_attributes = True
        populate_by_name = True
        response_model_by_alias = True


class UpdateAccountModel(BaseModel):
    """更新账号，密码不能修改"""

    full_name: Optional[str] = Field(
        description="企业名称（用于显示，不用于登录）", min_length=2, max_length=20
    )
    username: Optional[str] = Field(
        description="用户名（用于登录）", min_length=2, max_length=20
    )
    phone: Optional[str] = Field(
        description="手机号码", min_length=11, max_length=11, pattern=r"^1[3-9]\d{9}$"
    )

    @field_validator("username")
    def check_username(cls, v):
        if v and v.isdigit():
            raise ValueError("用户名不能全为数字")
        return v


class AccountModel(UpdateAccountModel):
    """用于后台添加账号"""

    password: str = Field(description="密码", min_length=6, max_length=20)


class AddVIPModel(AccountModel):
    """后台添加VIP"""

    expired: date
    intro: str
    image: Optional[str]


class AddSVIPModel(AddVIPModel):
    """后台添加SVIP"""

    child_limit: int = Field(description="子账号数量限制")


class UpdateVIPModel(UpdateAccountModel):
    expired: Optional[date]
    intro: Optional[str]
    image: Optional[str]


class UpdateSVIPModel(UpdateVIPModel):
    child_limit: Optional[int]


class AdminSVIPUpdateProfileModel(BaseModel):
    """用于SVIP自行更新个人资料"""

    full_name: Optional[str]
    intro: Optional[str]
    image: Optional[str]


class UpdateCaseModel(BaseModel):
    business: Optional[str] = Field(description="业务一级分类")
    category: Optional[str] = Field(description="业务二级分类")
    project_name: Optional[str] = Field(description="项目名称")
    project_profile: Optional[str] = Field(description="项目简介")
    benefit: Optional[str] = Field(description="项目成果")
    summarize_experience: Optional[str] = Field(description="经验总结")
    image_url: Optional[str] = Field(description="图片链接")

    class Config:
        from_attributes = True


class Cases(UpdateCaseModel):
    id: int = Field(description="案例ID")


class CasesResponseModel(BaseModel):
    total_pages: int
    cases: List[Cases]


class Ads(BaseModel):
    id: int = Field(description="广告ID")
    user_id: str = Field(description="用户ID")
    business: str = Field(description="业务一级分类")
    category: str = Field(description="业务二级分类")
    tech: str = Field(description="技术名称")
    image_url: str = Field(description="广告url")
    ad_info: str = Field(description="广告内容")

    class Config:
        from_attributes = True


class AdsResponseModel(BaseModel):
    total_pages: int
    ads: List[Ads]


class UpdateAdModel(BaseModel):
    business: Optional[str] = Field(description="业务一级分类")
    category: Optional[str] = Field(description="业务二级分类")
    tech: Optional[str] = Field(description="技术名称")
    image_url: Optional[str] = Field(description="广告url")
    ad_info: Optional[str] = Field(description="广告内容")

    class Config:
        from_attributes = True


class RecordsResponseModel(BaseModel):
    total_pages: int
    records: List[RecordModel]


class ChatRequestModel(BaseModel):
    chat_context: str = Field(
        description="对话的上下文",
        example="""
                              [{'user': '请解释废热回收技术',
                              'assistant': '废热回收技术：利用生产过程中的余热，通过热交换器、热泵等设备将其回收利用，用于供暖、制冷或发电，从而提高整体能源利用效率。']
                              """,
    )
    question: str = Field(description="本次的提问", example="如何选择空气压缩机？")


class PaymentInfoModel(BaseModel):
    title: str
    intro: str
    price: str
    icon: str


class OrderModel(BaseModel):
    phone: str
    order_no: str
    order_content: str
    amount: str
