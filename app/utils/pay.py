import json
import os.path
import time
from wechatpayv3 import WeChatPay, WeChatPayType

# 全局配置（需替换为实际值）
MERCHANT_ID = "1677832967"  # 商户号
APPID = "wx6a0ac8e9c4b91f7c"  # 小程序APPID
API_V3_KEY = "Fzjz20230808Fzjz20230808Fzjz0808"  # APIv3密钥
CERT_SERIAL_NO = "4429349CB3B61454783D6AF345950694F309595C"  # 商户证书序列号
# CERT_SERIAL_NO = "720604BD49624EDFD6B802C1ACC347862143A199"  # 商户证书序列号

PRIVATE_KEY = """-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC6Ed7JrahzOT7e
UjZL93r9rPOXZBWeBkDK1/eZHBoekZj5TK1IxU73WDJyGCG+AG8kgPm6szS4yLgp
lIaKeXANdjbNsvlV8+qk4hhy5sqFDRfwiuWVhPNDjEqEGZLEcupla6wqgvvWuX1n
CkzGNAKSINvgl2X8e/oDMIkiL7Lwzvb3ylrVX9KJ6oXAscudolNJWjoG5BumbGeT
QZVqKWIFxqRDDaRj9kgQF5Rvcco2wvfMsZP4MvgP01pKbJsd8NHOYhhdkRVZPXbE
H6a3bq/xAdnjYJcPyJhsRtI/Dq2+uQ5sH38+lWhCiHLv2kSu9lD7MRMiAIg7Cgct
5e4c2Pv9AgMBAAECggEAYpQPJWhEo28DuMNzksG1vmn/0AgtT8BeWVkcC1kRGXrn
wcR21eP61x4586qHTeNq/rr6E4jX+MIWl6jhssFttSQZGtekM357pQlIDK/rQZxT
P5RG1/VM8E+GNwBZeoyrVDo8R3WHuRYisxGI5UUuy35vH0j2tlJ0fXYcYSlGMz96
u/Ac5ebME5+UraNdJnm/ojmgPH2oM6L5UcBG0HnmuxoXiXOehpPcNgJUuXH+ILDb
J894vmkQTrL9fpk3Pq7OYsTwas8tjI2r7jdJoa87gAHqtxehI3SaCV6q4P3NkD7H
Cm5XCWkPCTnCknfRGXqKoGFqHESaAiwBfyVzc+ImgQKBgQDxMn08CbGDxZdEABy+
UpKsAHfl0i2oBjLDaGyFwTUiKbK+3p9cZVJQgUaIGJVBOve6u0axhvMFyjQ8eFNc
AibNYIJUH4G4vQYvIMnIchNYrhGewWax0Lek7LIzTtn+gwZVY1SWJHGeSwL23uTW
mQdxMgublSntDRz78A8/nc4gHQKBgQDFfUKdab8talqzj6tGoJbhxn87Sp5s1UfI
e04IvvFSIU3/mXqSgWByM8rMPVSlN6QiCnXJA3lGJGsgq3OAVNWIlGVbj8OMoCTn
EQe6zKGemBRU3zuQzVTRCXG3B1Kbj7+dvNyu/U94lLlTe7Xa9iLAD134csTwMydB
tImx8cNFYQKBgQDCK4okBg2w7iWLKaf6E5FeBHaBPkVhCbReGTecKeDzYqwx+hhC
kpLEmn3EXD3zqFv8KH2Ntvz3gUOyFo/M9zJzjaj9vet5ZDqRQA0RX7xxXJh0vG9G
4Kamj6IZqfXWbXZw0SksQaRx8SMuyFti4wjZuJcdpeR9oFvf+e7coNZqhQKBgHPA
+KOlUL4A4YrvwbdS9zz8iKSrFvK5jCqRQ2rS6EV4aexP/E0U8f/eJZbSt+NjGpwt
P16D37hiLjxm4fstPj+go0wolri9QQQCsmImAPEhOIGKmrJD99vSSkm6TAwMFIcT
JNKYfNUzbvDkyPG/ZRznpO+z7YTQpsjXVgHrr8XhAoGAFJiLPu4hTVSnwa2TLmus
hMbxThUPbbVt54hyybogo6OkgavEZmX36jrfjOaRvkSpIQj160vW97p9l8BMiGSU
4GH9g3mxiLHsk0zUqALofGhh6zqHLK7cAp5dQieZYNkwiUoQ52mpn4m1EC0CXDgi
kSVAdYSgx/MXt5ze+LgwQE8=
-----END PRIVATE KEY-----
"""


# 商户证书私钥
# with open('./apiclient_key.pem') as f:
#     PRIVATE_KEY = f.read()


class Pay:
    def __init__(self):
        """
        :param wechatpay_type: 微信支付类型，示例值:WeChatPayType.MINIPROG
        :param mchid: 直连商户号，示例值:'1230000109'
        :param private_key: 商户证书私钥，示例值:'MIIEvwIBADANBgkqhkiG9w0BAQE...'
        :param cert_serial_no: 商户证书序列号，示例值:'444F4864EA9B34415...'
        :param appid: 应用ID，示例值:'wxd678efh567hg6787'
        :param apiv3_key: 商户APIv3密钥，示例值:'a12d3924fd499edac8a5efc...'
        :param notify_url: 通知地址，示例值:'https://www.weixin.qq.com/wxpay/pay.php'
        :param cert_dir: 平台证书存放目录，示例值:'/server/cert'
        :param partner_mode: 接入模式，默认False为直连商户模式，True为服务商模式
        :param proxy: 代理设置，示例值:{"https": "http://10.10.1.10:1080"},没有就是None
        :param timeout: 超时时间，示例值：(10, 30), 10为建立连接的最大超时时间，30为读取响应的最大超时实践
        """
        self.wxpay = WeChatPay(
            wechatpay_type=WeChatPayType.JSAPI,
            mchid=MERCHANT_ID,
            private_key=PRIVATE_KEY,
            cert_serial_no=CERT_SERIAL_NO,
            apiv3_key=API_V3_KEY,
            appid=APPID,
            notify_url="https://fd24-50-114-155-134.ngrok-free.app/order/callback",
            # cert_dir=os.path.join(Config.BASE_DIR, 'config/cert'),
            partner_mode=False,
            proxy=None,
            timeout=30,
        )

    def refund(self, out_trade_no, out_refund_no, amount, reason) -> bool:
        code, message = self.wxpay.refund(
            out_trade_no=out_trade_no,
            out_refund_no=out_refund_no,
            amount=amount,
            reason=reason,
        )
        message = json.loads(message)
        print("code: %s, message: %s" % (code, message))
        return (
            True
            if message["status"] == "SUCCESS" or message["status"] == "PROCESSING"
            else False
        )

    def pay(self, openid, price, order_no, description, attach=None):
        """
        :param attach: 【附加数据】 附加数据，在查询API和支付通知中原样返回，可作为自定义参数使用，实际情况下只有支付完成状态才会返回该字段。
        :param openid: 微信用户的唯一标识
        :param price: 该订单的价格
        :param nonce_str: 请求随机串nonce_str,与签名使用的随机字符串值仙童
        :param description: 商户证书序列号，示例值:'444F4864EA9B34415...'
        return prepay_id : 【预支付交易会话标识】 预支付交易会话标识。用于后续接口调用中使用，该值有效期为2小时
        """
        code, message = self.wxpay.pay(
            description=description,
            out_trade_no=order_no,
            amount={"total": int(price * 100), "currency": "CNY"},
            payer={"openid": openid},
            attach=attach,
            pay_type=WeChatPayType.JSAPI,
        )
        # print('code: %s, message: %s' % (code, message))
        message = json.loads(message)
        print(message)
        return message["prepay_id"]

    def sign(
        self,
        prepay_id,
    ):
        """
        :param prepay_id: 预支付交易会话标识
        :param price: 该订单的价格
        :param nonce_str: 请求随机串nonce_str,与签名使用的随机字符串值仙童
        :param description: 商户证书序列号，示例值:'444F4864EA9B34415...'
        return prepay_id : 【预支付交易会话标识】 预支付交易会话标识。用于后续接口调用中使用，该值有效期为2小时
        """
        timeStamp = str(int(time.time()))
        nonce_str = os.urandom(16 // 2).hex()
        # :微信支付订单采用RSAwithSHA256算法时，示例值: ['wx888', '1414561699', '5K8264ILTKCH16CQ2502S....','prepay_id=wx201410272009395522657....']
        sign = [APPID, timeStamp, nonce_str, f"prepay_id={prepay_id}"]
        # print(self.wxpay.sign(sign))
        paySign = self.wxpay.sign(sign)

        return {
            "timeStamp": timeStamp,
            "nonceStr": nonce_str,
            "package": f"prepay_id={prepay_id}",
            "signType": "RSA",
            "paySign": paySign,
        }

    def decrypt_callback(self, headers, body):
        """
        :param headers:
        :param body:
        return prepay_id
        """
        return self.wxpay.decrypt_callback(headers, body)


wechat_pay = Pay()
