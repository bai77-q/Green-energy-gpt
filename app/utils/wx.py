# wx.py
import datetime

import requests
import json

# 全局常量配置
APP_ID = "wx6a0ac8e9c4b91f7c"  # 替换为你的小程序appid
APP_SECRET = "95d4bf6a8d9df2941f69ed6d0de9aa7b"  # 替换为你的小程序appsecret
ACCESS_TOKEN_URL = "https://api.weixin.qq.com/cgi-bin/token"
PHONE_NUMBER_URL = "https://api.weixin.qq.com/wxa/business/getuserphonenumber"

ACCESS_TOKEN = {"access_token": "", "expires_in": datetime.datetime.now()}


def get_access_token():
    if (
        ACCESS_TOKEN["access_token"]
        and ACCESS_TOKEN["expires_in"] > datetime.datetime.now()
    ):
        return ACCESS_TOKEN["access_token"]
    """获取微信接口调用凭证"""
    params = {"grant_type": "client_credential", "appid": APP_ID, "secret": APP_SECRET}

    try:
        response = requests.get(ACCESS_TOKEN_URL, params=params)
        response.raise_for_status()
        data = response.json()

        if "access_token" in data:
            ACCESS_TOKEN["access_token"] = data["access_token"]
            ACCESS_TOKEN["expires_in"] = datetime.datetime.now() + datetime.timedelta(
                seconds=data["expires_in"] - 5 * 60
            )
            return data["access_token"]
        else:
            raise ValueError(f"获取access_token失败: {data.get('errmsg', '未知错误')}")
    except requests.exceptions.RequestException as e:
        raise SystemError(f"网络请求异常: {str(e)}")


def get_openid(code):
    """根据前端传入的code获取openid"""
    access_token = get_access_token()
    url = f"https://api.weixin.qq.com/sns/jscode2session"
    try:
        response = requests.post(
            url,
            params={
                "appid": APP_ID,
                "secret": APP_SECRET,
                "js_code": code,
                "grant_type": "authorization_code",
            },
        )
        response.raise_for_status()
        data = response.json()
        print(data)
        if "openid" in data:
            return data.get("openid")
        else:
            raise ValueError(
                f"微信接口错误[{data['errcode']}]: {data.get('errmsg', '未知错误')}"
            )
    except requests.exceptions.RequestException as e:
        raise SystemError(f"微信接口请求异常: {str(e)}")


def get_phone_number(code):
    """根据前端传入的code获取手机号"""
    access_token = get_access_token()
    url = f"{PHONE_NUMBER_URL}?access_token={access_token}"

    try:
        response = requests.post(url, json={"code": code})
        response.raise_for_status()
        result = response.json()
        print(result)

        if result.get("errcode") == 0:
            phone_info = result.get("phone_info", {})
            return {
                "phone_number": phone_info.get("purePhoneNumber"),
                "country_code": phone_info.get("countryCode"),
            }
        else:
            error_map = {
                40001: "参数错误",
                40002: "请求方法错误",
                40029: "code无效",
                45011: "频率限制",
            }
            errmsg = error_map.get(result["errcode"], result.get("errmsg", "未知错误"))
            raise ValueError(f"微信接口错误[{result['errcode']}]: {errmsg}")
    except requests.exceptions.RequestException as e:
        raise SystemError(f"手机号接口请求异常: {str(e)}")


# if __name__ == '__main__':
#     # 测试示例
#     test_code = '前端获取的code'  # 替换实际测试code
#     try:
#         phone_data = get_phone_number(test_code)
#         print(f"手机号: {phone_data['country_code']}{phone_data['phone_number']}")
#     except Exception as e:
#         print(f"错误发生: {str(e)}")
