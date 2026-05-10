"""MySQL 客户端工厂。

当前项目统一使用 app.db.database 中的 SQLAlchemy engine。
保留这个函数是为了让其他模块可以通过更直观的名字获取 MySQL 引擎。
"""

from sqlalchemy.engine import Engine

from app.db.database import engine


def get_mysql_engine() -> Engine:
    """返回全局共享的 MySQL SQLAlchemy Engine。"""
    return engine
