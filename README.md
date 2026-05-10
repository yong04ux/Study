# GaokaoPilot

GaokaoPilot 是一个高考志愿辅助Agent，提供成绩分析、院校查询、志愿推荐、方案管理、报告查询和 RAG 问答能力。

后端使用 `FastAPI + SQLAlchemy + LangGraph + MySQL + Redis + Kafka + Chroma`，前端使用 `React + TypeScript + Vite`。

## 当前能力

- 用户注册、登录、当前用户信息查询
- 登录后工作台：最近推荐、最近浏览院校、报告任务、收藏学校、志愿方案
- 志愿推荐：生成冲 / 稳 / 保结果，并支持保存为个人方案
- 院校查询：搜索学校、查看详情、查看历年分数线、收藏学校
- 志愿方案：创建、列表、详情、复制、删除
- 异步报告：提交 Kafka 任务，通过 Redis 查询状态
- 智能问答：基于 Agent + RAG 的问答能力

## 目录结构

```text
app/
  agents/        LangGraph 工作流
  api/           FastAPI 路由
  cache/         Redis 缓存封装
  core/          配置与安全能力
  db/            MySQL / Redis / Kafka / Chroma 连接
  models/        ORM 和 Pydantic 模型
  mq/            Kafka producer / consumer
  rag/           文档加载、切分、向量检索
  services/      业务服务层
  main.py        FastAPI 入口

frontend/        React 前端
scripts/         初始化、导入、向量库、测试数据脚本
data/            CSV 数据和知识库文档
tests/           后端测试
```

## 环境变量

先复制模板：

```powershell
Copy-Item .env.example .env
```

安全提醒：

- 真实的 `.env`、`frontend/.env` 和其他环境变量文件不要提交到 GitHub。
- 仓库中只保留 `.env.example` 这类模板文件。
- 如果你的 API Key 曾经提交过仓库历史，即使现在删掉，也应立即去对应平台轮换新 Key。

常用变量：

- `MYSQL_HOST` `MYSQL_PORT` `MYSQL_USER` `MYSQL_PASSWORD` `MYSQL_DATABASE`
- `REDIS_HOST` `REDIS_PORT` `REDIS_DB` `REDIS_PASSWORD`
- `KAFKA_BOOTSTRAP_SERVERS`
- `KAFKA_RECOMMENDATION_TOPIC`
- `CHROMA_PERSIST_DIRECTORY`
- `CHROMA_COLLECTION_NAME`
- `JWT_SECRET_KEY`
- `JWT_ALGORITHM`
- `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`
- `OPENAI_API_KEY`
- `OPENAI_MODEL`
- `OPENAI_EMBEDDING_MODEL`
- `LLM_PROVIDER`
- `LLM_API_KEY`
- `LLM_BASE_URL`
- `LLM_MODEL`
- `EMBEDDING_PROVIDER`
- `EMBEDDING_API_KEY`
- `EMBEDDING_MODEL`
- `LOCAL_EMBEDDING_MODEL`
- `LOCAL_EMBEDDING_DEVICE`

## 快速启动

如果你只是想把项目尽快跑起来，推荐按下面这条“最短体验路径”执行。

### 1. 首次准备

```powershell
Copy-Item .env.example .env
python -m pip install -r requirements.txt
cd frontend
npm install
cd ..
```

### 2. 启动基础服务

```powershell
docker run -d --name gaokao-mysql -p 3306:3306 -e MYSQL_ROOT_PASSWORD=123456 mysql:8.0
docker run -d --name gaokao-redis -p 6379:6379 redis:7
docker run -d --name gaokao-kafka -p 9092:9092 -p 9644:9644 redpandadata/redpanda:latest redpanda start --overprovisioned --smp 1 --memory 512M --reserve-memory 0M --node-id 0 --check=false --kafka-addr 0.0.0.0:9092 --advertise-kafka-addr 127.0.0.1:9092
docker exec gaokao-kafka rpk topic create gaokao_recommendation_report
```

### 3. 初始化数据

```powershell
Get-Content .\scripts\init_mysql.sql | mysql -u root -p123456
python scripts\import_data.py
python scripts\build_vector_db.py
python scripts\seed_test_user.py
```

### 4. 启动后端、消费者和前端

建议开 3 个终端窗口分别执行：

终端 1：

```powershell
python -m uvicorn app.main:app --reload
```

终端 2：

```powershell
python -m app.mq.kafka_consumer
```

终端 3：

```powershell
cd frontend
npm run dev
```

### 5. 登录体验

- 前端地址：`http://127.0.0.1:5173`
- 后端文档：`http://127.0.0.1:8000/docs`
- 测试账号：`demo_student`
- 测试密码：`gaokao123`

推荐体验顺序：

1. 登录后先打开 `/dashboard` 确认工作台可用。
2. 进入 `/recommendation` 生成推荐结果。
3. 去 `/schools` 查看学校并收藏。
4. 回 `/recommendation` 保存为方案。
5. 去 `/reports` 提交报告任务。
6. 最后回 `/dashboard` 查看推荐、收藏、方案、报告是否都已汇总。

### 可选：重新启动时的最短命令

如果你已经初始化过数据库、导入过数据、构建过向量库，后续通常只需要：

```powershell
python scripts\seed_test_user.py
python -m uvicorn app.main:app --reload
python -m app.mq.kafka_consumer
cd frontend
npm run dev
```

## 后端启动

### 1. 安装依赖

```powershell
python -m pip install -r requirements.txt
```

### 2. 启动基础服务

MySQL:

```powershell
docker run -d --name gaokao-mysql -p 3306:3306 -e MYSQL_ROOT_PASSWORD=123456 mysql:8.0
```

Redis:

```powershell
docker run -d --name gaokao-redis -p 6379:6379 redis:7
```

Kafka（开发环境可用 Redpanda）:

```powershell
docker run -d --name gaokao-kafka -p 9092:9092 -p 9644:9644 redpandadata/redpanda:latest redpanda start --overprovisioned --smp 1 --memory 512M --reserve-memory 0M --node-id 0 --check=false --kafka-addr 0.0.0.0:9092 --advertise-kafka-addr 127.0.0.1:9092
```

创建 Topic:

```powershell
docker exec gaokao-kafka rpk topic create gaokao_recommendation_report
```

### 3. 初始化数据库

```powershell
Get-Content .\scripts\init_mysql.sql | mysql -u root -p123456
```

### 4. 导入院校和专业数据

先 dry run：

```powershell
python scripts\import_data.py --dry-run
```

正式导入：

```powershell
python scripts\import_data.py
```

### 5. 构建向量库

先 dry run：

```powershell
python scripts\build_vector_db.py --dry-run
```

正式构建：

```powershell
python scripts\build_vector_db.py
```

### 6. 启动 API

```powershell
python -m uvicorn app.main:app --reload
```

常用地址：

- Swagger: `http://127.0.0.1:8000/docs`
- Root: `http://127.0.0.1:8000/`
- Health: `http://127.0.0.1:8000/api/v1/health`

### 7. 启动报告消费者

```powershell
python -m app.mq.kafka_consumer
```

## 前端启动

```powershell
cd frontend
npm run dev
```

默认地址：`http://127.0.0.1:5173`

前端首页、工作台、推荐页、院校页、方案页和报告页现在都内置了“使用教程”提示，进入页面即可按步骤操作。

## 测试用户数据

项目新增了可重复执行的测试用户种子脚本：

```powershell
python scripts\seed_test_user.py
```

默认账号：

- 用户名：`demo_student`
- 邮箱：`demo_student@example.com`
- 密码：`gaokao123`

脚本会重建这个用户的演示数据，包括：

- 2 条收藏学校
- 1 份志愿方案
- 推荐、院校浏览、问答、报告 4 类工作台活动

这份数据适合直接验证登录后的业务流程和前端工作台展示。

## 登录后推荐体验路径

推荐按下面顺序联调：

1. 登录测试账号或新注册账号。
2. 打开 `/dashboard` 确认登录态正常。
3. 进入 `/recommendation` 生成一组推荐结果。
4. 在 `/schools` 查看学校详情并收藏目标学校。
5. 在 `/recommendation` 把结果保存为方案，随后到 `/plans` 查看。
6. 在 `/reports` 提交异步报告任务，并通过 `task_id` 查询状态。
7. 回到 `/dashboard` 查看最近推荐、收藏学校、报告任务和方案是否已汇总。

## 主要接口

```text
POST /auth/register
POST /auth/login
GET  /auth/me

GET  /dashboard/overview
GET  /dashboard/activities

GET  /schools/search
GET  /schools/{school_id}
GET  /schools/{school_id}/score-lines

POST /favorites/schools/{school_id}
GET  /favorites/schools
DELETE /favorites/schools/{school_id}
GET  /favorites/schools/{school_id}/status

POST /recommendations/generate

POST /plans
GET  /plans
GET  /plans/{plan_id}
PUT  /plans/{plan_id}
DELETE /plans/{plan_id}
POST /plans/{plan_id}/duplicate

POST /reports/submit
GET  /reports/{task_id}

POST /qa/ask
```

## 常用认证示例

注册：

```powershell
curl -X POST "http://127.0.0.1:8000/auth/register" `
  -H "Content-Type: application/json" `
  -d "{\"username\":\"alice\",\"email\":\"alice@example.com\",\"password\":\"secret123\"}"
```

登录：

```powershell
curl -X POST "http://127.0.0.1:8000/auth/login" `
  -H "Content-Type: application/json" `
  -d "{\"username\":\"alice\",\"password\":\"secret123\"}"
```

查询当前用户：

```powershell
curl "http://127.0.0.1:8000/auth/me" `
  -H "Authorization: Bearer your-jwt-token"
```

## 测试

运行全部测试：

```powershell
pytest
```

这次补充的重点测试是：

- `tests/test_authenticated_user_flow.py`

它覆盖了“注册/登录 -> 推荐 -> 收藏学校 -> 保存方案 -> 提交报告 -> 查看工作台”的主流程。
