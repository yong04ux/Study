"""RAG 智能问答服务，支持"知识问答 + 志愿推荐意图路由"。

核心思路：
1. 用户问题先做关键词+正则意图识别。
2. 政策、专业、规则、学习规划、院校介绍等知识类问题走 RAG。
3. "多少分能上""推荐学校""冲稳保"等推荐类问题走 LangGraph 推荐流程。
4. /qa/ask 对前端保持统一返回格式：answer + sources。
5. 支持 conversation_id 上下文，实现多轮追问。
"""

from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Literal

from openai import OpenAI

from app.agents.graph import GaokaoAgentGraph
from app.agents.state import GaokaoState
from app.core.config import settings
from app.core.llm import build_llm_client
from app.models.qa_schema import QaAskRequest, QaAskResponse, QaSource
from app.rag.vector_store import ChromaVectorStore, get_shared_vector_store

logger = logging.getLogger(__name__)

QuestionIntent = Literal["rag", "recommendation"]

INSUFFICIENT_INFO_ANSWER = (
    "当前知识库暂未收录该问题的详细资料。"
    "建议你查询所在省份教育考试院官网的招生文件，或在系统中使用「志愿推荐」功能获取基于分数和位次的院校推荐。"
)
MISSING_LLM_CONFIG_ERROR = "未配置问答模型 API Key。请在环境变量中设置 OPENAI_API_KEY 或 LLM_API_KEY。"

# 推荐意图关键词 —— 命中任一即路由到推荐 Agent，而非 RAG。
RECOMMENDATION_KEYWORDS = (
    "推荐学校", "推荐院校", "能上什么大学", "能报什么学校", "可以报考",
    "冲稳保", "志愿推荐", "多少分能上", "位次", "分数",
    "录取概率", "报哪些学校", "报什么大学", "能上哪些",
    "可以上什么", "推荐专业", "能报哪些", "能上什么",
    "可以报什么", "推荐一下", "帮我看看", "能考上",
    "能录取", "有没有希望", "稳不稳",
)

# 推荐意图的正则模式 —— 匹配 "X分能上/能报/可以上" 等分数查询模式。
RECOMMENDATION_PATTERNS = (
    re.compile(r"(\d{2,3})\s*分.*(?:能|可以|够).*(?:上|报|考|录取)"),
    re.compile(r"(?:能|可以|够).*(?:上|报|考).*(\d{2,3})\s*分"),
    re.compile(r"(?:位次|排名|排位).*(\d{3,7}).*(?:推荐|能上|能报|可以)"),
)

# 全国31个省、自治区、直辖市。
KNOWN_PROVINCES = (
    "北京", "上海", "广东", "江苏", "浙江", "山东", "四川", "河南",
    "湖北", "湖南", "福建", "云南", "天津", "重庆", "河北", "安徽",
    "辽宁", "吉林", "黑龙江", "陕西", "山西", "甘肃", "青海",
    "海南", "贵州", "江西", "广西", "内蒙古", "宁夏", "新疆", "西藏",
)

# 专业别名词典 —— 将口语化表达映射到规范专业名称。
MAJOR_ALIASES: dict[str, str] = {
    # 计算机类
    "计算机": "Computer Science and Technology",
    "计算机科学与技术": "Computer Science and Technology",
    "计科": "Computer Science and Technology",
    "软件工程": "Software Engineering",
    "软工": "Software Engineering",
    "软件": "Software Engineering",
    "人工智能": "Artificial Intelligence",
    "ai": "Artificial Intelligence",
    "AI": "Artificial Intelligence",
    "大数据": "Data Science and Big Data Technology",
    "数据科学": "Data Science and Big Data Technology",
    "物联网": "Internet of Things Engineering",
    "网络工程": "Network Engineering",
    "信息安全": "Information Security",
    "网络空间安全": "Cyberspace Security",
    # 电子信息类
    "电子信息": "Electronic Information Engineering",
    "电子信息工程": "Electronic Information Engineering",
    "通信工程": "Communication Engineering",
    "通信": "Communication Engineering",
    "微电子": "Microelectronics Science and Engineering",
    "集成电路": "Integrated Circuit Design and System",
    "光电": "Optoelectronic Information Science and Engineering",
    # 经济与管理类
    "金融": "Finance",
    "金融学": "Finance",
    "金融工程": "Financial Engineering",
    "会计": "Accounting",
    "会计学": "Accounting",
    "经济学": "Economics",
    "工商管理": "Business Administration",
    "市场营销": "Marketing",
    # 医学类
    "临床医学": "Clinical Medicine",
    "临床": "Clinical Medicine",
    "口腔医学": "Stomatology",
    "口腔": "Stomatology",
    "中医学": "Traditional Chinese Medicine",
    "中医": "Traditional Chinese Medicine",
    "药学": "Pharmacy",
    # 法学与文学类
    "法学": "Law",
    "法律": "Law",
    "英语": "English",
    "日语": "Japanese",
    "新闻": "Journalism",
    "新闻学": "Journalism",
    "传播学": "Communication Studies",
    # 理学类
    "数学": "Mathematics and Applied Mathematics",
    "数学与应用数学": "Mathematics and Applied Mathematics",
    "物理学": "Physics",
    "物理": "Physics",
    "化学": "Chemistry",
    "生物科学": "Biological Science",
    "生物": "Biological Science",
    "统计学": "Statistics",
    # 工科其他
    "机械工程": "Mechanical Engineering",
    "机械": "Mechanical Engineering",
    "土木工程": "Civil Engineering",
    "土木": "Civil Engineering",
    "建筑学": "Architecture",
    "建筑": "Architecture",
    "电气工程": "Electrical Engineering",
    "电气": "Electrical Engineering",
    "自动化": "Automation",
    "材料科学": "Materials Science and Engineering",
    "材料": "Materials Science and Engineering",
    "环境工程": "Environmental Engineering",
    # 教育类
    "师范": "Teacher Education",
    "教育学": "Education",
    "学前教育": "Preschool Education",
}

# 科类关键词映射。
SUBJECT_KEYWORDS: dict[str, str] = {
    "物理类": "物理类", "物理": "物理类", "理科": "物理类",
    "历史类": "历史类", "历史": "历史类", "文科": "历史类",
    "综合": "综合", "不分文理": "综合",
}

# 内置兜底知识库 —— 当 Chroma 向量库为空或不可用时使用。
FALLBACK_RAG_DOCUMENTS: list[dict[str, Any]] = [
    {
        "filename": "gaokao_policy_fallback.md",
        "source": "fallback://gaokao_policy",
        "chunk_index": 0,
        "content": (
            "平行志愿遵循分数优先、遵循志愿、一次投档的原则。分数优先指按考生总分从高到低排序，"
            "先检索高分考生的全部志愿。遵循志愿指对每位考生按其所填报的志愿顺序依次检索，"
            "第一个符合投档条件的志愿即被投档。一次投档指在同一批次中每位考生只有一次投档机会，"
            "一旦投档成功，后续志愿不再检索；如被退档，只能参加征集志愿或下一批次录取。"
            "填报时建议形成冲刺、稳妥、保底三个梯度，每个梯度间保持合理分差。"
        ),
    },
    {
        "filename": "major_intro_fallback.md",
        "source": "fallback://major_intro",
        "chunk_index": 0,
        "content": (
            "计算机科学与技术主要学习程序设计、数据结构、算法分析、操作系统、数据库原理、"
            "计算机网络、编译原理、软件工程等核心课程。就业方向包括互联网公司软件开发、"
            "金融IT、人工智能研发、游戏开发、科研院所等。"
            "软件工程侧重工程化软件开发方法，包括需求分析、系统设计、编码测试、项目管理等。"
            "人工智能研究机器学习、深度学习、计算机视觉、自然语言处理等技术。"
        ),
    },
    {
        "filename": "application_advice_fallback.md",
        "source": "fallback://application_advice",
        "chunk_index": 0,
        "content": (
            "志愿填报建议：首先根据一分一段表确认自己的全省位次；然后用位次比对目标院校专业"
            "近三年的录取最低位次；冲刺志愿位次略高于自己（一般高10%-20%），稳妥志愿与自己"
            "位次接近或略低，保底志愿位次明显低于自己（一般低20%-40%）。还需注意专业的选科"
            "要求、体检限制、单科成绩要求。服从调剂建议勾选，可降低退档风险，但需接受可能被"
            "调剂到冷门专业的可能。"
        ),
    },
    {
        "filename": "special_plans_fallback.md",
        "source": "fallback://special_plans",
        "chunk_index": 0,
        "content": (
            "强基计划面向基础学科拔尖创新人才选拔，参与高校为39所原985高校，聚焦数学、物理、"
            "化学、生物、力学、基础医学、历史和哲学等专业。录取在提前批之前完成，未被录取不影响"
            "后续批次。高校专项、国家专项和地方专项计划面向农村和脱贫地区学生，通常有户籍和学籍"
            "要求。报考前需查阅各校招生简章和本省具体实施细则。"
        ),
    },
    {
        "filename": "batch_rules_fallback.md",
        "source": "fallback://batch_rules",
        "chunk_index": 0,
        "content": (
            "高考录取分为提前批、本科批、专科批等批次。提前批包括军队、公安、司法院校及公费师范生、"
            "优师专项等特殊类型。本科批为绝大多数考生的主要录取批次，采用平行志愿投档。"
            "退档常见原因包括：不服从专业调剂、单科成绩不达标、身体条件不符合要求等。"
            "征集志愿是每批次录取结束后对未完成计划进行的补充录取，时间紧、名额少。"
        ),
    },
    {
        "filename": "score_rank_fallback.md",
        "source": "fallback://score_rank",
        "chunk_index": 0,
        "content": (
            "位次比分数更适合跨年份比较。由于每年试卷难度不同，同样的650分在不同年份对应的全省排名"
            "可能相差数千名。建议以位次为主要依据、分数为辅助参考。正式填报前务必查看省教育考试院"
            "公布的一分一段表，确认自己的准确位次。使用分数粗略估算时，上下浮动10-15分作为合理区间。"
        ),
    },
    {
        "filename": "major_transfer_fallback.md",
        "source": "fallback://major_transfer",
        "chunk_index": 0,
        "content": (
            "多数高校允许学生在大一或大二申请转专业，一般要求大一成绩排名前列（如前10%-30%），"
            "并通过转专业考试或面试。热门专业转入竞争激烈，中外合作办学专业通常不可转入转出。"
            "除转专业外，还可考虑辅修/双学位、跨专业考研等路径。各校具体政策差异大，需查阅"
            "目标院校的本科生转专业管理办法。"
        ),
    },
    {
        "filename": "postgraduate_fallback.md",
        "source": "fallback://postgraduate",
        "chunk_index": 0,
        "content": (
            "985高校平均保研率约20%-35%，清华北大超过50%，211高校约10%-20%，普通本科一般低于10%。"
            "计算机、金融、法律（非法学）等方向考研热度极高，报录比可超10:1。"
            "选专业时建议结合兴趣、能力和就业前景综合判断，避免盲目追逐热门——四年后行业冷热可能变化。"
        ),
    },
]

@dataclass
class RecommendationSlots:
    """从推荐类问题中抽取出的结构化信息。"""

    score: int | None = None
    rank: int | None = None
    province: str | None = None
    subject_type: str | None = None
    preferred_provinces: list[str] = field(default_factory=list)
    preferred_majors: list[str] = field(default_factory=list)


def classify_question_intent(question: str) -> QuestionIntent:
    """根据关键词和正则模式判断问题是志愿推荐意图还是 RAG 知识问答。"""
    normalized = question.strip().lower()

    # 先用正则检测分数+报考的组合模式。
    for pattern in RECOMMENDATION_PATTERNS:
        if pattern.search(question):
            return "recommendation"

    # 再用关键词兜底。
    if any(keyword.lower() in normalized for keyword in RECOMMENDATION_KEYWORDS):
        return "recommendation"

    return "rag"


class RagQaService:
    """智能问答总编排服务，负责在 RAG 和推荐 Agent 之间路由。"""

    def __init__(self) -> None:
        self._vector_store: ChromaVectorStore | None = None
        self._openai_client: OpenAI | None = None
        self._recommendation_graph: GaokaoAgentGraph | None = None
        # 简单的内存对话上下文：conversation_id → 最近 N 条消息摘要。
        self._conversations: dict[str, list[dict[str, str]]] = {}

    @property
    def vector_store(self) -> ChromaVectorStore:
        if self._vector_store is None:
            self._vector_store = get_shared_vector_store()
        return self._vector_store

    @property
    def openai_client(self) -> OpenAI:
        if self._openai_client is None:
            self._openai_client = build_llm_client()
        return self._openai_client

    @property
    def recommendation_graph(self) -> GaokaoAgentGraph:
        if self._recommendation_graph is None:
            self._recommendation_graph = GaokaoAgentGraph()
        return self._recommendation_graph

    def ask(self, request: QaAskRequest, top_k: int = 4) -> QaAskResponse:
        """统一问答入口。

        业务流程：
        1. 校验 question、province、subject_type 是否为空。
        2. 如果提供了 conversation_id，加载历史上下文。
        3. 调用 classify_question_intent 判断意图。
        4. 推荐类问题调用 _answer_recommendation_question。
        5. 知识类问题调用 _answer_rag_question。
        6. 更新对话历史缓存。
        """
        question = request.question.strip()
        province = request.province.strip()
        subject_type = request.subject_type.strip()
        use_llm = request.use_llm
        conversation_id = (request.conversation_id or "").strip()

        if not question:
            raise ValueError("question cannot be blank.")
        if not province:
            raise ValueError("province cannot be blank.")
        if not subject_type:
            raise ValueError("subject_type cannot be blank.")

        # 加载历史上下文（如果有）。
        history = self._load_conversation_history(conversation_id)

        intent = classify_question_intent(question)

        if intent == "recommendation":
            response = self._answer_recommendation_question(
                question=question,
                fallback_province=province,
                fallback_subject_type=subject_type,
                history=history,
            )
        else:
            response = self._answer_rag_question(
                question=question,
                province=province,
                subject_type=subject_type,
                top_k=top_k,
                use_llm=use_llm,
                history=history,
            )

        # 更新对话缓存。
        if conversation_id:
            self._save_conversation_turn(conversation_id, question, response.answer)

        return response

    # ------------------------------------------------------------------
    # 对话历史管理
    # ------------------------------------------------------------------

    def _load_conversation_history(self, conversation_id: str) -> list[dict[str, str]]:
        if not conversation_id:
            return []
        return self._conversations.get(conversation_id, [])[-6:]  # 保留最近 3 轮。

    def _save_conversation_turn(self, conversation_id: str, question: str, answer: str) -> None:
        if not conversation_id:
            return
        if conversation_id not in self._conversations:
            self._conversations[conversation_id] = []
        self._conversations[conversation_id].append({"q": question, "a": answer[:300]})
        # 超过 20 轮则清理旧记录，防止内存膨胀。
        if len(self._conversations[conversation_id]) > 20:
            self._conversations[conversation_id] = self._conversations[conversation_id][-10:]

    # ------------------------------------------------------------------
    # 推荐意图处理
    # ------------------------------------------------------------------

    def _answer_recommendation_question(
        self,
        *,
        question: str,
        fallback_province: str,
        fallback_subject_type: str,
        history: list[dict[str, str]],
    ) -> QaAskResponse:
        """处理推荐类问题：抽取分数/位次/偏好，并调用推荐 Agent 流程。"""
        slots = extract_recommendation_slots(
            question=question,
            fallback_province=fallback_province,
            fallback_subject_type=fallback_subject_type,
        )

        if slots.score is None:
            # 尝试从历史中找到分数。
            if history:
                for turn in reversed(history):
                    hist_slots = extract_recommendation_slots(
                        question=turn["q"],
                        fallback_province=fallback_province,
                        fallback_subject_type=fallback_subject_type,
                    )
                    if hist_slots.score is not None:
                        slots.score = hist_slots.score
                        slots.rank = hist_slots.rank
                        break

        if slots.score is None:
            return QaAskResponse(
                answer=(
                    "请补充你的高考分数或位次，例如：\n"
                    "• 「广东物理类600分，位次25000，想学计算机，可以报哪些学校？」\n"
                    "• 「四川理科580分能上什么大学？」\n\n"
                    "如果你暂时不知道分数，也可以告诉我你想了解哪个省份、哪个分数段的院校情况，我会尽力提供参考信息。"
                ),
                sources=[_recommendation_source()],
            )

        rank = slots.rank if slots.rank is not None else _estimate_rank_from_score(
            slots.score, slots.province or fallback_province
        )
        state: GaokaoState = {
            "user_id": "qa_user",
            "province": slots.province or fallback_province,
            "subject_type": slots.subject_type or fallback_subject_type,
            "score": slots.score,
            "rank": rank,
            "preferred_provinces": slots.preferred_provinces,
            "preferred_majors": slots.preferred_majors,
            "score_analysis": {},
            "retrieved_schools": [],
            "recommended_choices": {"rush": [], "stable": [], "safe": []},
            "study_plan": "",
            "final_answer": "",
        }

        result = asyncio.run(self.recommendation_graph.generate_recommendation(state))
        return QaAskResponse(
            answer=self._format_recommendation_answer(
                result,
                rank_was_estimated=slots.rank is None,
                province=slots.province or fallback_province,
            ),
            sources=[_recommendation_source()],
        )

    # ------------------------------------------------------------------
    # RAG 知识问答处理
    # ------------------------------------------------------------------

    def _answer_rag_question(
        self,
        *,
        question: str,
        province: str,
        subject_type: str,
        top_k: int,
        use_llm: bool,
        history: list[dict[str, str]],
    ) -> QaAskResponse:
        """处理知识类问题：检索资料、构造 Prompt、调用大模型生成回答。"""
        # 构建增强检索查询 —— 融合历史和省份信息。
        search_query = self._build_search_query(
            question=question, province=province, subject_type=subject_type, history=history
        )

        sources = self._retrieve_sources(
            question=search_query,
            province=province,
            subject_type=subject_type,
            top_k=top_k,
        )

        if not sources or self._is_context_insufficient(sources):
            # 知识库不足时，不直接说"资料不足"，而是给出有引导性的回复。
            return QaAskResponse(
                answer=self._build_insufficient_info_response(question=question, province=province),
                sources=sources,
            )

        if not use_llm:
            return QaAskResponse(answer=self._build_debug_answer(sources), sources=sources)

        prompt = self._build_prompt(
            question=question,
            province=province,
            subject_type=subject_type,
            sources=sources,
            history=history,
        )
        answer = self._generate_answer(prompt)
        return QaAskResponse(answer=answer, sources=sources)

    @staticmethod
    def _build_search_query(
        *,
        question: str,
        province: str,
        subject_type: str,
        history: list[dict[str, str]],
    ) -> str:
        """构建增强检索查询 —— 将省份、科类和历史关键词拼入检索语句。"""
        parts = [question]
        if province:
            parts.append(f"省份：{province}")
        if subject_type:
            parts.append(f"科类：{subject_type}")
        # 将上轮问题的关键词带入检索。
        if history:
            last_q = history[-1].get("q", "")
            if last_q and last_q != question:
                parts.append(f"上文：{last_q[:120]}")
        return "\n".join(parts)

    @staticmethod
    def _build_insufficient_info_response(*, question: str, province: str) -> str:
        """知识库覆盖不到问题时，返回有引导性的回答而非冷冰冰的'资料不足'。"""
        return (
            f"关于「{question[:80]}」，当前知识库暂未收录详细资料。\n\n"
            "你可以尝试：\n"
            f"1. 换一种方式提问，例如更简洁的关键词；\n"
            f"2. 前往「志愿推荐」页面输入你的分数和位次，获取个性化院校推荐；\n"
            f"3. 在「院校查询」页面搜索目标学校，查看近年录取数据；\n"
            f"4. 访问{province}教育考试院官网获取最权威的招生政策文件。\n\n"
            "如果有具体的分数和位次，我也可以帮你做志愿推荐分析。"
        )

    # ------------------------------------------------------------------
    # 检索与生成
    # ------------------------------------------------------------------

    def _retrieve_sources(
        self,
        *,
        question: str,
        province: str,
        subject_type: str,
        top_k: int,
    ) -> list[QaSource]:
        """从 Chroma 检索 top-k 文档片段；向量库为空或失败时使用内置兜底资料。"""
        search_query = f"{question}\n省份：{province}\n科类：{subject_type}"

        try:
            if self.vector_store.count() > 0:
                matches = self.vector_store.similarity_search(search_query, top_k=top_k)
                return [self._match_to_source(match) for match in matches]
        except Exception:
            logger.exception("Chroma retrieval failed; falling back to bundled QA documents.")

        return self._fallback_sources(question=question, top_k=top_k)

    def _generate_answer(self, prompt: str) -> str:
        """调用配置好的大模型，根据 Prompt 生成严格基于资料的回答。"""
        if not self._has_llm_credentials():
            raise ValueError(MISSING_LLM_CONFIG_ERROR)

        response = self.openai_client.chat.completions.create(
            model=settings.resolved_llm_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "你是高考志愿填报助手。你的核心职责是帮助考生和家长理解高考政策、"
                        "院校信息、专业内容和志愿填报策略。\n\n"
                        "回答原则：\n"
                        "1. 优先基于提供的检索资料回答，资料中有的信息可以直接引用。\n"
                        "2. 对于资料中未覆盖的高考常识性问题（如专业简介、政策解释、填报策略等），"
                        "你可以用自身知识做补充说明，但必须标注「以下为通用参考信息，具体以官方文件为准」。\n"
                        f"3. 如果问题和高考志愿完全无关，请礼貌说明你的职责范围。\n"
                        "4. 禁止编造任何具体的分数线、学校排名或录取数据。\n"
                        "5. 回答要条理清晰、分段明确、便于学生和家长阅读。"
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
        )
        content = response.choices[0].message.content
        return content.strip() if content else INSUFFICIENT_INFO_ANSWER

    @staticmethod
    def _build_prompt(
        *,
        question: str,
        province: str,
        subject_type: str,
        sources: list[QaSource],
        history: list[dict[str, str]],
    ) -> str:
        """构造 RAG Prompt，融合检索片段和历史对话。"""
        context_blocks = []
        for index, source in enumerate(sources, start=1):
            label = source.filename or source.title or source.source or f"source-{index}"
            context_blocks.append(f"[资料{index}：{label}]\n{source.content}")

        context = "\n\n".join(context_blocks)

        history_block = ""
        if history:
            recent = history[-4:]
            history_block = "对话历史：\n" + "\n".join(
                f"用户：{turn['q']}\n助手：{turn['a'][:200]}" for turn in recent
            )
            history_block += "\n\n请基于以上对话历史理解用户当前问题（可能是追问）。"

        prompt_parts = [
            f"用户问题：{question}",
            f"考生省份：{province}",
            f"考生科类：{subject_type}",
        ]
        if history_block:
            prompt_parts.append(history_block)
        prompt_parts.append(f"检索资料：\n{context}")
        prompt_parts.append(
            "请根据以上信息回答问题。如果检索资料覆盖了问题，优先引用资料中的信息；"
            "如果资料仅部分覆盖，可以用自身常识补充（标注为参考信息）；"
            "如果问题涉及具体的分数线或录取数据而资料中完全没有，请说明需要查询官方文件。"
        )

        return "\n\n".join(prompt_parts)

    @staticmethod
    def _match_to_source(match: dict[str, Any]) -> QaSource:
        metadata = match.get("metadata") or {}
        chunk_index = metadata.get("chunk_index")
        distance = match.get("distance")
        score = None if distance is None else max(0.0, 1.0 - float(distance))
        return QaSource(
            title=metadata.get("filename"),
            content=str(match.get("content") or ""),
            filename=metadata.get("filename"),
            source=metadata.get("source"),
            chunk_index=int(chunk_index) if chunk_index is not None else None,
            distance=distance,
            score=score,
        )

    @staticmethod
    def _fallback_sources(*, question: str, top_k: int) -> list[QaSource]:
        """当 Chroma 暂无数据时，根据问题关键词对内置资料做简单相关性排序。"""
        normalized_question = question.strip().lower()

        # 更细粒度的关键词匹配。
        keyword_groups: dict[str, list[str]] = {
            "志愿": ["志愿", "填报", "平行志愿", "冲稳保", "投档", "录取规则", "退档", "调剂", "批次"],
            "专业": ["专业", "计算机", "软件", "人工智能", "大数据", "学什么", "课程", "就业"],
            "政策": ["政策", "规则", "规定", "条件", "资格"],
            "计划": ["强基", "专项", "综合评价", "计划", "农村", "自主招生"],
            "位次": ["位次", "分数", "排名", "一分一段", "等效分"],
            "转专业": ["转专业", "换专业", "辅修", "双学位"],
            "考研": ["考研", "保研", "推免", "研究生", "就业", "前景"],
        }

        def score_document(document: dict[str, Any]) -> int:
            content = str(document["content"]).lower()
            total = 0
            for group_keywords in keyword_groups.values():
                if any(kw in normalized_question for kw in group_keywords):
                    if any(kw in content for kw in group_keywords):
                        total += 3
            return total

        ranked_documents = sorted(FALLBACK_RAG_DOCUMENTS, key=score_document, reverse=True)
        return [
            QaSource(
                title=document["filename"],
                content=document["content"],
                filename=document["filename"],
                source=document["source"],
                chunk_index=document["chunk_index"],
                distance=None,
                score=None,
            )
            for document in ranked_documents[:top_k]
        ]

    @staticmethod
    def _format_recommendation_answer(
        result: GaokaoState,
        *,
        rank_was_estimated: bool,
        province: str,
    ) -> str:
        """把 LangGraph 推荐结果整理成自然语言答案。"""
        choices = result["recommended_choices"]
        analysis = result["score_analysis"]

        lines = [
            f"📊 成绩分析：{analysis.get('summary') or analysis.get('level')}",
        ]
        if rank_was_estimated:
            lines.append(
                "⚠️ 说明：你没有提供位次，系统使用分数做了粗略位次估算。"
                "正式填报请务必以省教育考试院一分一段表确认你的准确位次。"
            )

        lines.append("")
        lines.append(_format_choice_group("🔴 冲刺院校（可以尝试，风险较高）", choices.get("rush", [])))
        lines.append("")
        lines.append(_format_choice_group("🟡 稳妥院校（匹配度较高，重点考虑）", choices.get("stable", [])))
        lines.append("")
        lines.append(_format_choice_group("🟢 保底院校（安全边际充足）", choices.get("safe", [])))
        lines.append("")
        lines.append(
            "📋 风险提示：推荐结果基于系统数据库中的历年分数线生成，仅用于辅助参考。"
            "最终填报前务必核对：①当年招生计划和选科要求；②院校最新招生章程；"
            "③本省教育考试院公布的官方投档线和一分一段表。"
        )
        return "\n".join(lines)

    @staticmethod
    def _is_context_insufficient(sources: list[QaSource]) -> bool:
        return not any(source.content.strip() for source in sources)

    @staticmethod
    def _has_llm_credentials() -> bool:
        api_key = settings.resolved_llm_api_key.strip()
        return bool(api_key and api_key != "your-openai-api-key")

    @staticmethod
    def _build_debug_answer(sources: list[QaSource]) -> str:
        excerpts = [source.content.strip() for source in sources if source.content.strip()]
        if not excerpts:
            return INSUFFICIENT_INFO_ANSWER
        preview = "\n\n---\n\n".join(excerpts[:3])
        return f"已关闭 LLM 调用，以下为检索到的参考资料：\n\n{preview}"


# ------------------------------------------------------------------
# 槽位抽取
# ------------------------------------------------------------------

def extract_recommendation_slots(
    *,
    question: str,
    fallback_province: str,
    fallback_subject_type: str,
) -> RecommendationSlots:
    """从自然语言问题中抽取推荐所需槽位：分数、位次、省份、科类和偏好。"""
    slots = RecommendationSlots()
    slots.score = _extract_score(question)
    slots.rank = _extract_rank(question)
    slots.province = _extract_province(question) or fallback_province
    slots.subject_type = _extract_subject_type(question) or fallback_subject_type
    slots.preferred_provinces = _extract_preferred_provinces(question)
    slots.preferred_majors = _extract_preferred_majors(question)
    return slots


def _extract_score(question: str) -> int | None:
    """从"600分""物理600分"等表达中提取高考分数。

    支持格式：
    - "600分"
    - "物理类600分"
    - "分数600"
    - "考了600"
    - "600左右"
    """
    # 先精确匹配 "数字 + 分"。
    match = re.search(r"(?<!\d)([3-7]\d{2})\s*分", question)
    if match:
        score = int(match.group(1))
        return score if 200 <= score <= 750 else None
    # 再尝试 "分数/考了/大约 + 数字"。
    match = re.search(r"(?:分数|考了?|大约|大概|差不多)\s*[:：]?\s*([3-7]\d{2})", question)
    if match:
        score = int(match.group(1))
        return score if 200 <= score <= 750 else None
    # 海南 900 分特殊处理。
    match = re.search(r"(?<!\d)([3-9]\d{2})\s*分", question)
    if match:
        score = int(match.group(1))
        return score if 200 <= score <= 900 else None
    return None


def _extract_rank(question: str) -> int | None:
    """从"位次30000""排名30000""排位30000"等表达中提取位次。"""
    for prefix in ("位次", "排名", "排位", "全省排名", "省排名"):
        match = re.search(rf"{prefix}\s*[:：]?\s*(\d{{3,7}})", question)
        if match:
            rank = int(match.group(1))
            return rank if 1 <= rank <= 3_000_000 else None
    return None


def _extract_province(question: str) -> str | None:
    """提取问题中第一个出现的省份（31 个省级行政区全覆盖）。"""
    for province in sorted(KNOWN_PROVINCES, key=len, reverse=True):
        if province in question:
            return province
    return None


def _extract_preferred_provinces(question: str) -> list[str]:
    """提取问题中提到的全部地区偏好。"""
    return [province for province in KNOWN_PROVINCES if province in question]


def _extract_subject_type(question: str) -> str | None:
    """提取科类，并规范化为物理类/历史类/综合。"""
    for keyword, normalized in SUBJECT_KEYWORDS.items():
        if keyword in question:
            return normalized
    return None


def _extract_preferred_majors(question: str) -> list[str]:
    """根据专业别名词典抽取用户感兴趣的专业（去重）。"""
    majors: list[str] = []
    # 按别名长度降序匹配，优先匹配完整名称再匹配短别名。
    sorted_aliases = sorted(MAJOR_ALIASES.items(), key=lambda x: len(x[0]), reverse=True)
    for alias, normalized in sorted_aliases:
        if alias in question and normalized not in majors:
            majors.append(normalized)
    return majors


def _estimate_rank_from_score(score: int, province: str = "") -> int:
    """用户未提供位次时，用分数做粗略位次估计。

    不同省份考生基数和竞争强度差异大，这里给一个通用近似值。
    实际填报必须用一分一段表确认。
    """
    # 高考大省（河南、广东、山东、四川、河北等）高分密集，同位次对应分数偏高。
    large_provinces = {"河南", "广东", "山东", "四川", "河北", "安徽", "湖南", "湖北", "江苏", "浙江"}
    offset = 0.95 if province in large_provinces else 1.0

    if score >= 680:
        return int(500 * offset)
    if score >= 660:
        return int(2500 * offset)
    if score >= 650:
        return int(5000 * offset)
    if score >= 630:
        return int(10000 * offset)
    if score >= 610:
        return int(20000 * offset)
    if score >= 590:
        return int(35000 * offset)
    if score >= 560:
        return int(60000 * offset)
    if score >= 520:
        return int(100000 * offset)
    if score >= 480:
        return int(150000 * offset)
    return int(220000 * offset)


def _format_choice_group(title: str, items: list[dict[str, Any]]) -> str:
    """格式化一个推荐梯度。"""
    if not items:
        return f"{title}：暂无匹配结果。\n建议调整分数区间或放宽地区/专业偏好后重试。"

    lines = [f"{title}："]
    for index, item in enumerate(items[:5], start=1):
        school_name = item.get("school_name", "未知院校")
        major_name = item.get("major_name", "未知专业")
        min_score = item.get("min_score") or item.get("estimated_min_score")
        min_rank = item.get("min_rank")
        reason = item.get("reason", "")

        rank_info = f"，参考最低位次 {int(min_rank)}" if min_rank is not None else ""
        lines.append(
            f"{index}. **{school_name}** - {major_name}"
            f"（参考最低分 {min_score}{rank_info}）\n   {reason}"
        )
    return "\n".join(lines)


def _recommendation_source() -> QaSource:
    return QaSource(
        title="志愿推荐 Agent",
        content="基于历年分数线、院校专业数据和用户偏好生成推荐",
        source="agent://recommendation",
        chunk_index=None,
        distance=0.0,
        score=1.0,
    )
