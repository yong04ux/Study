"""健康检查接口使用的响应模型。"""

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """统一的健康检查响应结构。"""

    status: str = Field(..., description="Current service status.")
    service: str = Field(..., description="Service name.")
