"""志愿推荐业务服务。

Service 层负责把 API 请求转换成 LangGraph 需要的 State，
并在流程结束后把 Agent 输出整理成前端稳定可用的结构。
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import text

from app.agents.graph import GaokaoAgentGraph
from app.agents.state import GaokaoState


class RecommendationService:
    """运行志愿推荐工作流，并统一返回协议。"""

    def __init__(self, graph: GaokaoAgentGraph | None = None) -> None:
        self.graph = graph or GaokaoAgentGraph()

    async def recommend(
        self,
        *,
        user_id: str,
        province: str,
        subject_type: str,
        score: int,
        rank: int,
        preferred_provinces: list[str],
        preferred_majors: list[str],
    ) -> dict[str, Any]:
        """生成前端推荐页需要的完整结果。

        业务流程：
        1. 清洗用户输入的省份、科类、地区偏好和专业偏好。
        2. 先尝试从 MySQL 拉取符合分数区间的院校专业候选项。
        3. 把候选项放入 GaokaoState，交给 LangGraph 多 Agent 顺序处理。
        4. 将 Agent 输出归一化，保证前端始终拿到 rush/stable/safe 三个列表。
        """
        initial_state: GaokaoState = {
            "user_id": user_id.strip(),
            "province": province.strip(),
            "subject_type": subject_type.strip(),
            "score": score,
            "rank": rank,
            "preferred_provinces": [item.strip() for item in preferred_provinces if item.strip()],
            "preferred_majors": [item.strip() for item in preferred_majors if item.strip()],
            "score_analysis": {},
            # 优先使用数据库候选项；如果为空，后续图节点会自动使用 mock 兜底数据。
            "retrieved_schools": self._load_database_candidates(
                province=province.strip(),
                subject_type=subject_type.strip(),
                score=score,
            ),
            "recommended_choices": {"rush": [], "stable": [], "safe": []},
            "study_plan": "",
            "final_answer": "",
        }

        result = await self.graph.generate_recommendation(initial_state)
        choices = self._normalize_choices(result.get("recommended_choices"))
        score_analysis = self._normalize_score_analysis(result.get("score_analysis"))
        return {
            "score_analysis": score_analysis,
            "recommended_choices": choices,
            "study_plan": str(result.get("study_plan") or ""),
            "final_answer": str(result.get("final_answer") or ""),
        }

    @staticmethod
    def _normalize_choices(payload: Any) -> dict[str, list[dict[str, Any]]]:
        """保证推荐结果一定包含 rush、stable、safe 三个列表。"""
        data = payload if isinstance(payload, dict) else {}
        return {
            "rush": list(data.get("rush") or []),
            "stable": list(data.get("stable") or []),
            "safe": list(data.get("safe") or []),
        }

    @staticmethod
    def _normalize_score_analysis(payload: Any) -> dict[str, str]:
        """只保留页面需要的成绩分析字段，避免前端处理不稳定结构。"""
        data = payload if isinstance(payload, dict) else {}
        return {
            "level": str(data.get("level") or ""),
            "summary": str(data.get("summary") or ""),
            "suggestion": str(data.get("suggestion") or ""),
        }

    @staticmethod
    def _load_database_candidates(*, province: str, subject_type: str, score: int) -> list[dict[str, Any]]:
        """
        从 MySQL 加载候选院校专业。

        查询逻辑：
        1. 只查用户所在省份和科类。
        2. 取最新年份的分数线。
        3. 分数范围控制在用户分数 -50 到 +15，正好覆盖保底、稳妥、冲刺。
        4. 如果数据库不可用或查询失败，返回空列表，由 Agent 节点兜底。
        """
        try:
            from app.db.database import engine

            params = {
                "province": province,
                "subject_type": subject_type,
                "target_score": score,
                "min_score_lower": max(score - 50, 0),
                "min_score_upper": min(score + 15, 750),
            }
            sql = text(
                """
                SELECT
                  s.id AS school_id,
                  m.id AS major_id,
                  s.name AS school_name,
                  COALESCE(m.name, '未区分专业') AS major_name,
                  s.province AS province,
                  s.city AS city,
                  sl.min_score AS min_score,
                  sl.min_rank AS min_rank,
                  s.is_985 AS is_985,
                  s.is_211 AS is_211,
                  s.is_double_first_class AS is_double_first_class
                FROM score_line sl
                JOIN school s ON s.id = sl.school_id
                LEFT JOIN major m ON m.id = sl.major_id
                WHERE sl.province = :province
                  AND sl.subject_type = :subject_type
                  AND sl.min_score BETWEEN :min_score_lower AND :min_score_upper
                  AND sl.year = (
                    SELECT MAX(inner_sl.year)
                    FROM score_line inner_sl
                    WHERE inner_sl.province = sl.province
                      AND inner_sl.subject_type = sl.subject_type
                  )
                ORDER BY ABS(sl.min_score - :target_score), sl.min_score DESC
                LIMIT 60
                """
            )
            with engine.connect() as conn:
                rows = conn.execute(sql, params).mappings().all()
            return [dict(row) for row in rows]
        except Exception:
            return []
