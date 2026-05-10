"""项目配置中心。

本文件统一管理环境变量，避免在业务代码里到处直接读取 `os.environ`。
这样做的好处是：
1. 配置项集中，便于查看和维护。
2. 可以给每个配置设置默认值和类型。
3. 方便在本地开发、测试、生产环境之间切换。
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用运行时配置对象。"""

    app_name: str = Field(default="gaokao-pilot", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    app_debug: bool = Field(default=True, alias="APP_DEBUG")
    api_v1_prefix: str = Field(default="/api/v1", alias="API_V1_PREFIX")

    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_base_url: str = Field(default="", alias="OPENAI_BASE_URL")
    openai_model: str = Field(default="gpt-4.1-mini", alias="OPENAI_MODEL")
    openai_embedding_model: str = Field(
        default="text-embedding-3-small",
        alias="OPENAI_EMBEDDING_MODEL",
    )
    llm_provider: str = Field(default="openai", alias="LLM_PROVIDER")
    llm_api_key: str = Field(default="", alias="LLM_API_KEY")
    llm_base_url: str = Field(default="", alias="LLM_BASE_URL")
    llm_model: str = Field(default="", alias="LLM_MODEL")
    llm_timeout_seconds: float = Field(default=45.0, alias="LLM_TIMEOUT_SECONDS")
    embedding_provider: str = Field(default="openai", alias="EMBEDDING_PROVIDER")
    embedding_api_key: str = Field(default="", alias="EMBEDDING_API_KEY")
    embedding_base_url: str = Field(default="", alias="EMBEDDING_BASE_URL")
    embedding_model: str = Field(default="", alias="EMBEDDING_MODEL")
    local_embedding_model: str = Field(
        default="BAAI/bge-small-zh-v1.5",
        alias="LOCAL_EMBEDDING_MODEL",
    )
    local_embedding_device: str = Field(default="cpu", alias="LOCAL_EMBEDDING_DEVICE")
    local_embedding_normalize: bool = Field(default=True, alias="LOCAL_EMBEDDING_NORMALIZE")

    mysql_host: str = Field(default="127.0.0.1", alias="MYSQL_HOST")
    mysql_port: int = Field(default=3306, alias="MYSQL_PORT")
    mysql_user: str = Field(default="root", alias="MYSQL_USER")
    mysql_password: str = Field(default="", alias="MYSQL_PASSWORD")
    mysql_database: str = Field(default="gaokao_pilot", alias="MYSQL_DATABASE")
    jwt_secret_key: str = Field(default="change-me-in-production", alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(
        default=60 * 24 * 7,
        alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES",
    )

    redis_host: str = Field(default="127.0.0.1", alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")
    redis_db: int = Field(default=0, alias="REDIS_DB")
    redis_password: str = Field(default="", alias="REDIS_PASSWORD")

    kafka_bootstrap_servers: str = Field(
        default="127.0.0.1:9092",
        alias="KAFKA_BOOTSTRAP_SERVERS",
    )
    kafka_recommendation_topic: str = Field(
        default="gaokao_recommendation_report",
        alias="KAFKA_RECOMMENDATION_TOPIC",
    )

    chroma_persist_directory: str = Field(
        default="./data/chroma",
        alias="CHROMA_PERSIST_DIRECTORY",
    )
    chroma_collection_name: str = Field(
        default="gaokao_knowledge",
        alias="CHROMA_COLLECTION_NAME",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        populate_by_name=True,
        extra="ignore",
    )

    @property
    def mysql_dsn(self) -> str:
        """拼接 SQLAlchemy 可识别的 MySQL 连接字符串。"""
        return (
            f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
        )

    @property
    def redis_url(self) -> str:
        """拼接 Redis 连接地址。"""
        auth_part = f":{self.redis_password}@" if self.redis_password else ""
        return f"redis://{auth_part}{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def resolved_llm_provider(self) -> str:
        """返回规范化后的大模型提供商名称。"""
        return self.llm_provider.strip().lower() or "openai"

    @property
    def resolved_llm_api_key(self) -> str:
        """优先使用通用 LLM Key，未配置时退回到 OpenAI Key。"""
        return self.llm_api_key.strip() or self.openai_api_key.strip()

    @property
    def resolved_llm_model(self) -> str:
        """优先使用通用模型名，未配置时退回到 OpenAI 模型名。"""
        return self.llm_model.strip() or self.openai_model.strip()

    @property
    def resolved_llm_base_url(self) -> str | None:
        """解析聊天模型的 Base URL，兼容 OpenAI 风格接口。"""
        if self.llm_base_url.strip():
            return self.llm_base_url.strip()
        if self.openai_base_url.strip():
            return self.openai_base_url.strip()
        if self.resolved_llm_provider == "deepseek":
            return "https://api.deepseek.com"
        return None

    @property
    def resolved_embedding_provider(self) -> str:
        """返回规范化后的 embedding 提供商名称。"""
        return self.embedding_provider.strip().lower() or "openai"

    @property
    def resolved_embedding_api_key(self) -> str:
        """优先使用 embedding 专用 Key，未配置时退回到 OpenAI Key。"""
        return self.embedding_api_key.strip() or self.openai_api_key.strip()

    @property
    def resolved_embedding_model(self) -> str:
        """解析最终使用的 embedding 模型名。"""
        if self.embedding_model.strip():
            return self.embedding_model.strip()
        if self.resolved_embedding_provider == "local":
            return self.local_embedding_model.strip()
        return self.openai_embedding_model.strip()

    @property
    def resolved_embedding_base_url(self) -> str | None:
        """解析 embedding 服务的 Base URL。"""
        if self.embedding_base_url.strip():
            return self.embedding_base_url.strip()
        return None


@lru_cache
def get_settings() -> Settings:
    """缓存配置对象，避免在同一进程里重复读取和解析 `.env`。"""
    return Settings()


settings = get_settings()
