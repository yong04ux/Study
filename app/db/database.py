"""SQLAlchemy 数据库连接配置。

本文件负责把 FastAPI 和 MySQL 连接起来：
1. 根据 .env 中的 MySQL 配置拼接连接地址。
2. 创建全局 Engine 和 SessionLocal。
3. 提供 get_db 依赖，让每个 API 请求都能安全拿到数据库会话。
"""

from collections.abc import Generator

from sqlalchemy import URL, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


def build_mysql_url() -> URL:
    """构建 MySQL 连接 URL，并安全处理密码中的特殊字符。"""
    return URL.create(
        drivername="mysql+pymysql",
        username=settings.mysql_user,
        password=settings.mysql_password,
        host=settings.mysql_host,
        port=settings.mysql_port,
        database=settings.mysql_database,
    )


engine: Engine = create_engine(
    build_mysql_url(),
    # pool_pre_ping 会在连接复用前做一次探活，避免 MySQL 断开空闲连接后请求报错。
    pool_pre_ping=True,
    # 定期回收连接，适合本地开发和长时间运行的后端服务。
    pool_recycle=3600,
    pool_size=10,
    max_overflow=20,
)

SessionLocal = sessionmaker(
    bind=engine,
    # autoflush=False 表示不会在每次查询前自动 flush，初学阶段更容易理解事务边界。
    autoflush=False,
    # expire_on_commit=False 表示提交后对象字段仍可读取，减少新手遇到懒加载困惑。
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """SQLAlchemy ORM 模型基类，后续如果写 ORM class 可以继承它。"""


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI 数据库依赖函数。

    用法示例：
        db: Session = Depends(get_db)

    每次请求进入时创建 Session，请求结束后 finally 中关闭连接，
    这样可以避免数据库连接泄漏。
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
