"""顶层 API 路由注册。

main.py 会把这里的 api_router 挂载到 /api/v1 下。
这样可以把版本化 API 和根级业务 API 分开管理。
"""

from fastapi import APIRouter

from app.api.v1.endpoints.agent import router as agent_router
from app.api.v1.endpoints.health import router as health_router

api_router = APIRouter()
# 健康检查接口：用于确认服务是否启动成功。
api_router.include_router(health_router, tags=["health"])
# 占位 Agent 聊天接口：保留给后续扩展多 Agent 问答。
api_router.include_router(agent_router, prefix="/agent", tags=["agent"])
