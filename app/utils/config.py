"""系统的一些配置信息，它可以存储在数据库，目前直接统一放在Python代码中"""

import os

import yaml

SYSTEM_NAME = "菱重高投"
SYSTEM_LOGO = "https://green-img.f2ee.com/system/logo.png"

COMPANY_IMAGE = "https://green-img.f2ee.com/system/mhigt.jpg"
COMPANY_NAME = "成都菱重高投能源技术有限公司"
COMPANY_INTRO = """由三菱重工空调系统 (上海)有限公司与成都高新投资集团有限公司共同出资成立的合资公司。优势产业与政策资源的结合，助力碳中和，为西部打造低碳、高效的数字化能源体系提供全方位支持。
业务范围包括综合能源（区域分布式能源站的技术咨询、方案设计、可行性研究、设备集成、工程实施、智慧运维等一站式服务。通过多能互补、源、网、荷、储协同，实现经济效益最大化）、机电工程（电气工程技术、自动控制与仪表、给排水、机械设备安装、供热通风与空调工程、建筑智能化工程、设备及管道防腐蚀与绝热技术）等。
    """
DEFUALT_SVIP_IMAGE = "https://green-img.f2ee.com/default/default_vip_svip.jpg"

DEFAULT_POLICY_IMAGE = "https://green-img.f2ee.com/default/default_policy.png"

Admin_Name = "admin"
Admin_Password = "1234abcd"
Admin_Phone = "02885500899"
ADMIN_id = "admin-1e7e262e4ec047088f0219d957a3af95"

Wechat_Name = "user_test_wechat"
Wechat_Phone = "13855667788"
Wechat_Full_Name = "审核测试用户"
Wechat_Password = "1234abcd"

OPENAI_URL = "https://flag.smarttrot.com/v1/"
LANCE_DB_URL = "lance-data/sample-lancedb410"
INNER_API_KEY = "81c1103e20cd4be49c81e2dfac646b76"

LOGGER_MAIN = "energy_api"

CHAT_OP_TYPE = "conversation"
PROPOSAL_OP_TYPE = "proposal"
CHAT_SUBTYPE = "chat"
WIKI_SUBTYPE = "wiki"
ECO_SUBTYPE = "estimate"
ENERGY_SUBTYPE = "energy_analysis"
SUG_SUBTYPE = "suggestion"

##### 用户等级 #####

ADMIN_LEVEL = 0
REGULAR_LEVEL = 1
VIP_LEVEL = 2
SVIP_LEVEL = 3
SUB_SVIP_LEVEL = 4

FREE_CASE = 2
VIP_CASE = 4

#### 结束用户等级 ####

PAGE_SIZE = 10

# 验证码的过期时间（秒）
EXPIRED_SMS_SECOND = 60 * 10

# 提案ID的缓存过期时间（秒）
EXPIRED_RECORD_SECOND = 60 * 60 * 8

######### API分类 #####

# 登录注册相关
API_SIGN_TAG = "登录注册相关"

# 管理员管理账号相关
API_ADMIN_MANAGE_ACCOUNT = "管理员管理账号相关"

API_AD_MANAGE = "管理广告"

API_CASE_MANAGE = "管理案例"

# 管理员获取的系统统计信息
API_ADMIN_STATISTICS = "管理员获取的系统统计信息"

# SVIP及其子账号获取的统计信息
API_SVIP_STATISTICS = "SVIP及其子账号获取的统计信息"

# SVIP管理账号相关
API_SVIP_MANAGE_ACCOUNT: str = "SVIP管理账号相关"

API_ADMIN_SVIP_MANAGE = "管理员及SVIP通用管理相关"

# 生成提案相关
API_PROPOSAL = "生成提案相关"

# 有依赖关系的生成提案接口
API_PROPOSAL_WITH_DEPENDENCY = "有依赖关系的生成提案接口"

# 分享相关
API_SHARE = "分享相关"

# 人工介入相关
API_HELP = "人工介入相关"

API_SYS = "系统相关（全局变量）"

API_CHAT = "聊天相关"

API_INNER = "内部接口"

# 100M
MAX_ATTACHMENT_SIZE = 1024 * 1024 * 100
ALLOWED_EXTENSIONS = [
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".ppt",
    ".pptx",
    ".png",
    ".jpg",
    ".jpeg",
    ".dwg",
    ".dxf",
    ".dws",
    ".dgn",
]

##### 结束 API分类 ####

# 定义空气压缩行业共享的列表
shared_air_list = [
    "动力源",
    "清洁吹扫",
    "制冷媒介",
    "金属处理",
    "物料输送",
    "驱动仪表",
    "设备保护",
    "增压功能",
    "余热回收",
    "空气处理",
]

TECH_DICT = {
    "建筑行业": {
        "家用住宅": [
            "分体机",
            "地暖",
            "多联机",
            "家用新风系统",
            "光伏",
            "储能",
            "光伏+储能一体化",
        ],
        "办公写字楼": [
            "多联机",
            "空气源热泵",
            "风机盘管",
            "冷水机组",
            "集中新风系统",
            "智能照明",
        ],
        "酒店建筑": [
            "多联机",
            "空气源热泵",
            "风机盘管",
            "冷水机组",
            "集中新风系统",
            "锅炉",
            "智能照明",
            "光伏",
        ],
        "医院建筑": [
            "洁净空调",
            "风机盘管+新风系统",
            "多联机系统",
            "组空系统",
            "冷水机组",
            "锅炉",
            "光伏",
            "储能",
        ],
        "学校建筑": [
            "分体机",
            "多联机",
            "家用新风系统",
            "风机盘管+新风系统",
            "空气源热泵",
            "智能照明",
        ],
        "商场建筑": [
            "多联机",
            "空气源热泵",
            "风机盘管",
            "冷水机组",
            "集中新风系统",
            "锅炉",
        ],
        "片区开发": [
            "空气源热泵",
            "地（水）源热泵",
            "污水源热泵",
            "水（冰）蓄能",
            "冷水机组",
            "锅炉",
            "储能",
            "光伏",
        ],
        "城市综合体": [
            "空气源热泵",
            "地（水）源热泵",
            "污水源热泵",
            "水（冰）蓄能",
            "冷水机组",
            "锅炉",
            "光伏",
        ],
    },
    "工业": {
        "石化行业": ["空气源热泵", "余热回收", "光伏", "储能", "能源管理平台"],
        "生物医药行业": [
            "洁净空调",
            "转轮除湿机",
            "组合式空调柜",
            "冷水机组",
            "风机盘管+新风系统",
            "车间温室独立控制系统",
            "空气净化系统",
            "恒温恒湿",
        ],
        "半导体行业": [
            "洁净空调",
            "转轮除湿机",
            "组合式空调柜",
            "冷水机组",
            "风机盘管+新风系统",
            "车间温室独立控制系统",
            "空气净化系统",
            "恒温恒湿",
        ],
        "食品加工行业": [
            "洁净空调",
            "转轮除湿机",
            "组合式空调柜",
            "冷水机组",
            "风机盘管+新风系统",
            "车间温室独立控制系统",
            "空气净化系统",
            "恒温恒湿",
        ],
        "纺织行业": ["空气源热泵机组", "高温水源热泵", "余热利用"],
        "造纸行业": ["空气源热泵机组", "高温水源热泵", "余热利用"],
        "建筑材料行业": ["空气源热泵机组", "水源热泵", "余热利用"],
        "晶圆行业": [
            "洁净空调",
            "转轮除湿机",
            "组合式空调柜",
            "冷水机组",
            "风机盘管+新风系统",
            "车间温室独立控制系统",
            "空气净化系统",
            "恒温恒湿",
        ],
    },
    "农业": {
        "农林业相关": [
            "空气源热泵机组",
            "光照管理",
            "二氧化碳浓度控制",
            "室内温湿度控制",
        ],
        "经济农作物相关": [
            "空气源热泵机组",
            "光照管理",
            "二氧化碳浓度控制",
            "室内温湿度控制",
        ],
        "家禽养殖相关": ["热泵热水机", "闭式承压热水系统", "地暖系统"],
        "水产养殖相关": ["空气源热泵", "水源热泵", "恒温控制"],
    },
    "工艺": {
        "制热": ["空气源热泵", "燃气锅炉", "蒸气热泵"],
        "制冷": ["离心式冷水机组", "低温离心式冷水机组"],
        "储能": ["水蓄冷", "水蓄热", "冰蓄冷", "电储能"],
        "保温": ["盖纳涂层", "气凝胶保温"],
        "压缩空气品质": ["空压机热回收"],
        "电能质量": ["谐波治理", "无功补偿", "三项平衡"],
    },
    "空气压缩": {
        category: shared_air_list
        for category in [
            "电力行业",
            "纺织行业",
            "食品行业",
            "冶金工业",
            "交通运输",
            "航空航天",
            "机械制造",
            "化工行业",
        ]
    },
}
###
# 按业务领域分类的图片URL字典
CASE_IMGS = {
    "建筑行业": [
        f"https://green-img.f2ee.com/cases/ai-case/ai-Construction industry-{i}.jpg"
        for i in range(1, 20)
    ],
    "工业": [
        f"https://green-img.f2ee.com/cases/ai-case/ai-industry-{i}.jpg"
        for i in range(1, 20)
    ],
    "工艺": [
        f"https://green-img.f2ee.com/cases/ai-case/ai-craft-{i}.jpg"
        for i in range(1, 21)
    ],
    "智能化": [
        f"https://green-img.f2ee.com/cases/ai-case/ai-intelligentization-{i}.jpg"
        for i in range(1, 21)
    ],
    "农业": [
        f"https://green-img.f2ee.com/cases/ai-case/ai-agriculture-{i}.jpg"
        for i in range(1, 20)
    ],
    "空气压缩": [
        f"https://green-img.f2ee.com/cases/ai-case/ai-AirCompression-{i}.jpg"
        for i in range(1, 20)
    ],
}

###
CHART_DEFAULT = """
 {
        "type": "bar",
        "data": {
          "labels": ["石油", "煤炭", "天然气", "水电", "可再生", "核能"],
          "datasets": [
            {
              "label": "全球一次能源结构",
              "data": [31, 27, 25, 7, 6, 4]
            }
          ]
        }
}
"""

ECHART_DEFAULT = """
{
        "xAxis": {
          "data": ["石油", "煤炭", "天然气", "水电", "可再生", "核能"]
        },
        "yAxis": {},
        "series": [
          {
            "name": "占比",
            "type": "bar",
            "data": [31, 27, 25, 7, 6, 4]
          }
        ]
}
"""

DEFAULT_PLAN = """
{
"intro": "整体技术方案包括建立能源管理系统，实施能源监控和分析，发现能源浪费和效率低下的问题，并采取相应措施加以改进。",
"techs": ["照明系统升级", "资源回收与利用"]
}
"""


class KeyClass:
    def __init__(self, raw):
        self.tencent_api_key = raw["TCLOUD_API_KEY"]
        self.tencent_secret_id = raw["TCLOUD_SECRET_ID"]
        self.token_secret = raw["TOKEN_SECRET"]
        self.qianfan_api_key = raw["QIANFAN_API_KEY"]
        self.qianfan_secret_key = raw["QIANFAN_SECRET_KEY"]
        self.openai_api_keys = raw["OPENAI_API_KEYS"]
        self.bing_api_keys = raw["BING_API_KEYS"]


class DBClass:
    def __init__(self, raw):
        self.url = raw["url"]


class RedisClass:
    def __init__(self, raw):
        self.host = raw["host"]
        self.port = raw["port"]
        self.password = raw["password"]


class GateClass:
    def __init__(self, raw):
        self.add_operate_url = raw["add_operate_url"]


class WikiClass:
    def __init__(self, raw):
        self.url = raw["url"]


class CosClass:
    def __init__(self, raw):
        self.cos_base_url = raw["cos_base_url"]
        self.bucket = raw["bucket"]


class KeyConfig:
    def __init__(self, raw):
        self.keys = KeyClass(raw["keys"])
        self.db = DBClass(raw["db"])
        self.redis = RedisClass(raw["redis"])
        self.gate = GateClass(raw["gate"])
        self.wiki = WikiClass(raw["wiki"])
        self.cos = CosClass(raw["cos"])


def _load_conf_file():
    config_file = "config-prod.yml"
    if os.getenv("ENV", "").lower() == "debug":
        config_file = "config-dev.yml"
    elif os.getenv("ENV", "").lower() == "local":
        config_file = "config-local.yml"
    print("Using config file:", config_file)
    with open(config_file, "r") as f:
        c = yaml.safe_load(f)
        return c


CONFIG_SETTINGS = KeyConfig(_load_conf_file())
