"""健康检查 API。

部署或本地启动时，可以访问 /api/v1/health 快速确认 FastAPI 是否正常运行。
"""

from fastapi import APIRouter

from app.schemas.health import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """GET /api/v1/health：返回基础服务状态，用于监控和调试。"""
    return HealthResponse(status="ok", service="gaokao-pilot")
