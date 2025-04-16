# -*- coding=utf-8

from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client

from app.utils.config import CONFIG_SETTINGS

from fastapi import UploadFile

# 1. 设置用户属性, 包括 secret_id, secret_key, region等。Appid 已在 CosConfig 中移除，请在参数 Bucket 中带上 Appid。Bucket 由 BucketName-Appid 组成
secret_id = CONFIG_SETTINGS.keys.tencent_secret_id
# 用户的 SecretId，建议使用子账号密钥，授权遵循最小权限指引，降低使用风险。子账号密钥获取可参见 https://cloud.tencent.com/document/product/598/37140
secret_key = CONFIG_SETTINGS.keys.tencent_api_key
# 用户的 SecretKey，建议使用子账号密钥，授权遵循最小权限指引，降低使用风险。子账号密钥获取可参见 https://cloud.tencent.com/document/product/598/37140
region = "ap-chengdu"  # 替换为用户的 region，已创建桶归属的 region 可以在控制台查看，https://console.cloud.tencent.com/cos5/bucket
# COS 支持的所有 region 列表参见 https://cloud.tencent.com/document/product/436/6224
token = None  # 如果使用永久密钥不需要填入 token，如果使用临时密钥需要填入，临时密钥生成和使用指引参见 https://cloud.tencent.com/document/product/436/14048
scheme = "https"  # 指定使用 http/https 协议来访问 COS，默认为 https，可不填
config_cos = CosConfig(
    Region=region, SecretId=secret_id, SecretKey=secret_key, Token=token, Scheme=scheme
)
client = CosS3Client(config_cos)


bucket = CONFIG_SETTINGS.cos.bucket
cos_base_url = CONFIG_SETTINGS.cos.cos_base_url
print(bucket)
print(cos_base_url)


def upload_image_bytes_to_cos(file_bytes, file_name) -> bool:
    response = client.put_object(
        Bucket=bucket, Body=file_bytes, Key=file_name, EnableMD5=False
    )
    return response["ETag"]


async def upload_image(img: UploadFile, file_name: str, folder: str):
    contents = await img.read()
    extension = img.filename.split(".")[-1]
    file_name = folder + "/" + file_name + "." + extension
    if not upload_image_bytes_to_cos(contents, file_name):
        return None
    return cos_base_url + file_name


async def upload_file_to_cos(path: str, file_name: str, folder: str):
    # 上传文件并重试5次
    for i in range(0, 5):
        client.upload_file(
            Bucket=bucket, LocalFilePath=path, Key=folder + "/" + file_name
        )
        return cos_base_url + folder + "/" + file_name
