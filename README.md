# 新能源提案生成

- 需要从群里得到`lance-data`文件夹，放在项目根目录
- 需要从群里得到SQL插入数据脚本，在MySQL中执行

## 使用方法

### 本地测试
- 建议使用`virtualenv`创建虚拟环境，然后使用`pip install -r requirements.txt`安装依赖，确保使用最新的`lancedb`。
- 执行`playwright install firefox`安装Firefox浏览器，用于在线截图服务。
- 本地启动Redis。
- 本地启动MySQL（可选）。
- 复制`config-local.yml.sample`成`config-local.yml`，并根据实际情况修改配置。

```shell
ENV=local uvicorn app.main:app --reload
```

### 服务器部署（开发环境）

使用下面的命令启动：

```shell
docker-compose -f docker-compose-dev.yml up
```
第一次启动需要下载大量依赖（累计约1GB镜像）。后续直接使用`docker-compose -f docker-compose-dev.yml start`即可。

### 服务器部署（生产环境）

使用下面的命令启动：

```shell
docker-compose up
```

第一次启动需要下载大量依赖（累计约1GB镜像）。后续直接使用`docker-compose start`即可。

## 代码规范

请先安装`black`（使用版本`24.4.0`）和`pre-commit`，并执行`pre-commit install`安装进行提交检查的钩子。