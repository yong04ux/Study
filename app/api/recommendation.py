"""志愿推荐接口。

这一层只负责三件事：
1. 接收并校验 HTTP 请求参数。
2. 调用 Service 层执行业务。
3. 把结果整理成稳定的响应模型返回给前端。
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.security import get_optional_current_user
from app.db.database import get_db
from app.models.user import User
from app.services.activity_service import ActivityService
from app.services.recommendation_service import RecommendationService


router = APIRouter(prefix="/recommendations", tags=["recommendations"])
recommendation_service = RecommendationService()


class RecommendationRequest(BaseModel):
    """`POST /recommendations/generate` 的请求体。"""

    user_id: str = Field(..., min_length=1, max_length=64)
    province: str = Field(..., min_length=1, max_length=32)
    subject_type: str = Field(..., min_length=1, max_length=32)
    score: int = Field(..., ge=0, le=750)
    rank: int = Field(..., ge=1)
    preferred_provinces: list[str] = Field(default_factory=list, max_length=10)
    preferred_majors: list[str] = Field(default_factory=list, max_length=10)


class RecommendationScoreAnalysis(BaseModel):
    """成绩分析部分。"""

    level: str = ""
    summary: str = ""
    suggestion: str = ""


class RecommendationChoiceItem(BaseModel):
    """单条院校-专业推荐结果。"""

    school_id: int | None = None
    major_id: int | None = None
    school_name: str
    major_name: str
    province: str
    city: str | None = None
    min_score: int
    min_rank: int | None = None
    is_985: bool = False
    is_211: bool = False
    is_double_first_class: bool = False
    reason: str


class RecommendationChoiceGroup(BaseModel):
    """按冲刺、稳妥、保底分组后的推荐结果。"""

    rush: list[RecommendationChoiceItem] = Field(default_factory=list)
    stable: list[RecommendationChoiceItem] = Field(default_factory=list)
    safe: list[RecommendationChoiceItem] = Field(default_factory=list)


class RecommendationResponse(BaseModel):
    """推荐页需要的完整响应结构。"""

    score_analysis: RecommendationScoreAnalysis
    recommended_choices: RecommendationChoiceGroup
    study_plan: str
    final_answer: str


@router.post("/generate", response_model=RecommendationResponse)
async def generate_recommendation(
    payload: RecommendationRequest,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
) -> RecommendationResponse:
    """生成一份志愿推荐结果。"""
    province = payload.province.strip()
    subject_type = payload.subject_type.strip()
    if not province or not subject_type:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="province and subject_type cannot be blank.",
        )

    try:
        result = await recommendation_service.recommend(
            user_id=payload.user_id,
            province=province,
            subject_type=subject_type,
            score=payload.score,
            rank=payload.rank,
            preferred_provinces=payload.preferred_provinces,
            preferred_majors=payload.preferred_majors,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate recommendation result.",
        ) from exc

    response = RecommendationResponse(
        score_analysis=RecommendationScoreAnalysis(**result["score_analysis"]),
        recommended_choices=RecommendationChoiceGroup(**result["recommended_choices"]),
        study_plan=result["study_plan"],
        final_answer=result["final_answer"],
    )
    # 记录用户行为，供后续仪表盘、历史记录或埋点分析使用。
    ActivityService.record_activity(
        db,
        user=current_user,
        activity_type="recommendation",
        summary=f"{province}-{subject_type} {payload.score} score recommendation",
        payload={
            "province": province,
            "subject_type": subject_type,
            "score": payload.score,
            "rank": payload.rank,
            "rush_count": len(response.recommended_choices.rush),
            "stable_count": len(response.recommended_choices.stable),
            "safe_count": len(response.recommended_choices.safe),
        },
    )
    return response
