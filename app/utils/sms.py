"""使用腾讯云发送短信"""

from tencentcloud.common import credential
from tencentcloud.common.exception.tencent_cloud_sdk_exception import (
    TencentCloudSDKException,
)

# 导入对应产品模块的client models。
from tencentcloud.sms.v20210111 import sms_client, models

# 导入可选配置类
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile

from app.utils.config import CONFIG_SETTINGS, LOGGER_MAIN

import logging

logger = logging.getLogger(f"{LOGGER_MAIN}.{__name__}")

SecretId = CONFIG_SETTINGS.keys.tencent_secret_id
SecretKey = CONFIG_SETTINGS.keys.tencent_api_key

PHONE_PREFIX = "+86"
SmsSdkAppId = "1400903517"
TemplateId = "2130810"
SignName = "成都分子矩阵科技"


def send_sms(code: str, phone: str):
    """发送短信"""
    try:
        # SecretId、SecretKey 查询: https://console.cloud.tencent.com/cam/capi
        cred = credential.Credential(SecretId, SecretKey)

        # 实例化一个http选项，可选的，没有特殊需求可以跳过。
        httpProfile = HttpProfile()
        httpProfile.reqMethod = "POST"  # post请求(默认为post请求)
        httpProfile.reqTimeout = 30  # 请求超时时间，单位为秒(默认60秒)
        httpProfile.endpoint = (
            "sms.tencentcloudapi.com"  # 指定接入地域域名(默认就近接入)
        )

        # 非必要步骤:
        # 实例化一个客户端配置对象，可以指定超时时间等配置
        clientProfile = ClientProfile()
        clientProfile.signMethod = "TC3-HMAC-SHA256"  # 指定签名算法
        clientProfile.httpProfile = httpProfile

        # 实例化要请求产品(以sms为例)的client对象
        # 第二个参数是地域信息，可以直接填写字符串ap-guangzhou，支持的地域列表参考 https://cloud.tencent.com/document/api/382/52071#.E5.9C.B0.E5.9F.9F.E5.88.97.E8.A1.A8
        client = sms_client.SmsClient(cred, "ap-guangzhou", clientProfile)

        req = models.SendSmsRequest()

        req.SmsSdkAppId = SmsSdkAppId
        req.SignName = SignName
        req.TemplateId = TemplateId
        req.TemplateParamSet = [code]
        req.PhoneNumberSet = [PHONE_PREFIX + phone]
        req.SessionContext = ""
        req.ExtendCode = ""
        req.SenderId = ""
        resp = client.SendSms(req)
        # 输出json格式的字符串回包
        import json

        status = json.loads(resp.to_json_string())
        return status["SendStatusSet"][0]["Code"] == "Ok"
    except TencentCloudSDKException as err:
        logger.error(f"Failed to send sms to {phone}")
        return False


def get_random_sms_code():
    import random

    code = ""
    for _ in range(6):
        code += str(random.randint(0, 9))
    return code
