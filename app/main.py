"""FastAPI 应用入口。

这个文件做三件事：
1. 创建 FastAPI 实例。
2. 在启动阶段初始化项目需要的基础表。
3. 注册所有路由，让外部请求能访问对应功能。
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.exc import SQLAlchemyError

from app.api.auth import router as auth_router
from app.api.dashboard import router as dashboard_router
from app.api.favorites import router as favorites_router
from app.api.plans import router as plans_router
from app.api.qa import router as qa_router
from app.api.recommendation import router as recommendation_router
from app.api.reports import router as reports_router
from app.api.school import router as school_router
from app.api.router import api_router
from app.core.config import settings
from app.db.database import engine
from app.models.favorite_school import FavoriteSchool
from app.models.plan import Plan, PlanItem
from app.models.user_activity import UserActivity
from app.models.user import User


@asynccontextmanager
async def lifespan(_: FastAPI):
    """处理应用启动和关闭时机。

    FastAPI 会在服务真正开始接收请求前先进入这里，
    在 `yield` 之后的代码则会在应用关闭时执行。
    """
    # 这里先输出启动信息，方便本地开发时确认当前环境。
    # 如果以后要初始化 Redis、Kafka、向量库连接，也适合放在这里。
    print(f"Starting {settings.app_name} in {settings.app_env} mode...")
    try:
        # create_all 只会在表不存在时创建，不会删除已有数据。
        # 这里初始化的是当前项目已经用到的轻量表，避免首次启动就因缺表报错。
        User.metadata.create_all(
            bind=engine,
            tables=[
                User.__table__,
                Plan.__table__,
                PlanItem.__table__,
                UserActivity.__table__,
                FavoriteSchool.__table__,
            ],
        )
    except SQLAlchemyError as exc:
        # 数据库不可用时不阻塞服务启动，方便只调试不依赖数据库的接口。
        print(f"Skipping auth/plan/dashboard table initialization because database is unavailable: {exc}")
    yield
    print(f"Stopping {settings.app_name}...")


app = FastAPI(
    title=settings.app_name,
    description="Agent + RAG powered Gaokao assistant backend skeleton.",
    version="0.1.0",
    debug=settings.app_debug,
    lifespan=lifespan,
)

app.include_router(api_router, prefix=settings.api_v1_prefix)
app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(favorites_router)
app.include_router(plans_router)
app.include_router(school_router)
app.include_router(qa_router)
app.include_router(recommendation_router)
app.include_router(reports_router)


@app.get("/", tags=["root"])
async def read_root() -> dict[str, str]:
    """根路径检查接口。

    访问 `/` 时返回欢迎信息和文档地址，方便确认服务是否已启动。
    """
    return {
        "message": "Welcome to gaokao-pilot!",
        "docs": "/docs",
    }
