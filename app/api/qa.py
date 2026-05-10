"""问答接口。

这个接口对前端暴露统一的 `/qa/ask` 能力，
内部再由 RagQaService 判断是走 RAG 检索问答，还是走志愿推荐流程。
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from openai import OpenAIError
from sqlalchemy.orm import Session

from app.core.security import get_optional_current_user
from app.db.database import get_db
from app.models.qa_schema import QaAskRequest, QaAskResponse
from app.models.user import User
from app.services.activity_service import ActivityService
from app.services.rag_qa_service import RagQaService


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/qa", tags=["qa"])
qa_service = RagQaService()


@router.post("/ask", response_model=QaAskResponse)
def ask_question(
    payload: QaAskRequest,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
) -> QaAskResponse:
    """回答用户问题，并在有登录态时顺手记录一次访问行为。"""
    try:
        response = qa_service.ask(payload, top_k=4)
        # 问答成功后记录操作轨迹，便于后续做历史记录和活跃度统计。
        ActivityService.record_activity(
            db,
            user=current_user,
            activity_type="qa",
            summary=payload.question.strip()[:255] or "qa",
            payload={"question": payload.question},
        )
        return response
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except OpenAIError as exc:
        logger.exception("OpenAI-compatible LLM request failed for /qa/ask.")
        # 这里通常是模型调用失败，例如 Key 错误、网络错误或上游接口异常。
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="QA model request failed. Please check API credentials and network connectivity.",
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected RAG QA failure for /qa/ask.")
        # 剩余异常统一按服务内部错误处理，避免把底层细节暴露给前端。
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="RAG QA execution failed. Please check Chroma and model configuration.",
        ) from exc
