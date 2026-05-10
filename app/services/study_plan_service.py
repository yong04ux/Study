"""学习规划服务占位实现。"""


class StudyPlanService:
    """根据科类、成绩和目标院校生成学习规划的服务类。"""

    async def build_plan(self, subject_type: str) -> dict:
        """返回占位学习规划数据，后续可扩展为按科目和薄弱点生成计划。"""
        return {
            "subject_type": subject_type,
            "plan": "Study plan placeholder.",
        }
