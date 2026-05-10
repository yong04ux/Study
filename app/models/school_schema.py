"""院校查询 API 的 Pydantic 响应模型。

Pydantic 模型的作用：
1. 约束后端返回给前端的字段结构。
2. 自动生成 Swagger 文档。
3. 在接口返回前做基础类型校验。
"""

from pydantic import BaseModel, Field


class SchoolSummary(BaseModel):
    """院校列表页使用的简要院校信息。"""

    id: int = Field(..., description="School primary key.")
    school_name: str = Field(..., description="School name.")
    province: str = Field(..., description="School province.")
    city: str | None = Field(default=None, description="School city.")
    school_type: str | None = Field(default=None, description="School type.")
    school_level: str | None = Field(default=None, description="Education level.")
    is_985: bool = Field(..., description="Whether the school is in Project 985.")
    is_211: bool = Field(..., description="Whether the school is in Project 211.")
    is_double_first_class: bool = Field(..., description="Whether the school is Double First-Class.")
    is_favorited: bool = Field(default=False, description="Whether the current user favorited the school.")


class SchoolDetail(SchoolSummary):
    """院校详情接口返回的信息，在列表字段基础上增加代码和简介。"""

    school_code: str = Field(..., description="Official school code.")
    description: str | None = Field(default=None, description="School introduction.")


class SchoolSearchResponse(BaseModel):
    """院校搜索分页响应结构。"""

    total: int = Field(..., description="Total matched schools.")
    page: int = Field(..., description="Current page number.")
    page_size: int = Field(..., description="Page size.")
    items: list[SchoolSummary] = Field(default_factory=list, description="Current page results.")


class SchoolScoreLine(BaseModel):
    """某院校某专业在指定省份/科类下的历年分数线。"""

    year: int = Field(..., description="Admission year.")
    province: str = Field(..., description="Candidate province.")
    subject_type: str = Field(..., description="Subject type.")
    batch: str = Field(..., description="Admission batch.")
    major_name: str | None = Field(default=None, description="Major name.")
    min_score: int = Field(..., description="Minimum admission score.")
    min_rank: int | None = Field(default=None, description="Minimum admission rank.")
    avg_score: float | None = Field(default=None, description="Average admission score.")
    max_score: int | None = Field(default=None, description="Highest admission score.")
