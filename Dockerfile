# 使用基础镜像
FROM zhongpu/python:latest

# 设置工作目录
WORKDIR /

# 复制项目文件到工作目录
COPY ./requirements_extra.txt /

# 使用阿里云镜像源安装依赖
RUN pip install -r requirements_extra.txt -i https://mirrors.aliyun.com/pypi/simple
