"""Tests for QA intent routing between RAG and recommendation agents."""

from app.models.qa_schema import QaAskRequest
from app.services.rag_qa_service import (
    RagQaService,
    _extract_score,
    classify_question_intent,
    extract_recommendation_slots,
)


class ReadyVectorStore:
    """Small fake vector store for RAG path tests."""

    def count(self) -> int:
        return 1

    def similarity_search(self, query: str, top_k: int = 4):
        if "计算机" in query:
            content = "计算机科学与技术主要学习程序设计、数据结构、操作系统、数据库和计算机网络。"
            filename = "major_computer_science.md"
        else:
            content = "平行志愿遵循分数优先、遵循志愿、一次投档的原则。"
            filename = "gaokao_parallel_volunteer.md"
        return [
            {
                "content": content,
                "metadata": {"filename": filename, "source": filename, "chunk_index": 0},
                "distance": 0.1,
            }
        ]


def test_classify_question_intent() -> None:
    """Knowledge questions should use RAG and recommendation questions should use agents."""
    assert classify_question_intent("平行志愿是什么意思？") == "rag"
    assert classify_question_intent("我的分数是物理600分，请给我推荐可以报考的学校") == "recommendation"


def test_extract_recommendation_slots_full_question() -> None:
    """Extractor should parse score, rank, province, subject, majors, and province preferences."""
    slots = extract_recommendation_slots(
        question="广东物理类600分，位次30000，想学软件工程和人工智能，可以报哪些学校？",
        fallback_province="广东",
        fallback_subject_type="物理类",
    )

    assert slots.score == 600
    assert slots.rank == 30000
    assert slots.province == "广东"
    assert slots.subject_type == "物理类"
    assert "Software Engineering" in slots.preferred_majors
    assert "Artificial Intelligence" in slots.preferred_majors
    assert "广东" in slots.preferred_provinces


def test_qa_parallel_volunteer_uses_rag(monkeypatch) -> None:
    """Policy question should continue to use RAG knowledge QA."""
    service = RagQaService()
    service._vector_store = ReadyVectorStore()  # type: ignore[assignment]
    monkeypatch.setattr(RagQaService, "_generate_answer", lambda self, prompt: "平行志愿是按分数优先并遵循志愿顺序投档。")

    response = service.ask(
        QaAskRequest(question="平行志愿是什么意思？", province="广东", subject_type="物理类")
    )

    assert "平行志愿" in response.answer
    assert response.sources[0].filename == "gaokao_parallel_volunteer.md"


def test_qa_computer_major_uses_rag(monkeypatch) -> None:
    """Major intro question should continue to use RAG knowledge QA."""
    service = RagQaService()
    service._vector_store = ReadyVectorStore()  # type: ignore[assignment]
    monkeypatch.setattr(RagQaService, "_generate_answer", lambda self, prompt: "计算机专业主要学习编程、数据结构和操作系统等课程。")

    response = service.ask(
        QaAskRequest(question="计算机科学与技术专业主要学什么？", province="广东", subject_type="物理类")
    )

    assert "计算机" in response.answer
    assert response.sources[0].filename == "major_computer_science.md"


def test_qa_score_question_uses_recommendation_agent() -> None:
    """Score-based school question should call recommendation agent."""
    service = RagQaService()
    response = service.ask(
        QaAskRequest(
            question="我的分数是物理600分，请给我推荐可以报考的学校",
            province="广东",
            subject_type="物理类",
            use_llm=False,
        )
    )

    assert "成绩分析" in response.answer
    assert "冲刺院校" in response.answer
    assert response.sources[0].title == "志愿推荐 Agent"
    assert response.sources[0].score == 1.0


def test_qa_full_recommendation_question_uses_agent() -> None:
    """Detailed recommendation question should extract rank and major preferences."""
    service = RagQaService()
    response = service.ask(
        QaAskRequest(
            question="广东物理类600分，位次30000，想学软件工程和人工智能，可以报哪些学校？",
            province="广东",
            subject_type="物理类",
            use_llm=False,
        )
    )

    assert "稳妥院校" in response.answer or "保底院校" in response.answer
    assert "风险提示" in response.answer
    assert response.sources[0].source == "agent://recommendation"


def test_classify_intent_with_new_keywords() -> None:
    """New recommendation keywords should be recognized."""
    assert classify_question_intent("我能上什么大学") == "recommendation"
    assert classify_question_intent("600分可以报什么学校") == "recommendation"
    assert classify_question_intent("位次25000推荐什么学校") == "recommendation"
    assert classify_question_intent("帮我看看能不能上北大") == "recommendation"
    assert classify_question_intent("稳不稳这个分数") == "recommendation"


def test_classify_intent_keeps_rag_for_knowledge() -> None:
    """Knowledge questions should still route to RAG."""
    assert classify_question_intent("强基计划需要什么条件") == "rag"
    assert classify_question_intent("大学转专业难不难") == "rag"
    assert classify_question_intent("什么是征集志愿") == "rag"
    assert classify_question_intent("软件工程就业前景怎么样") == "rag"


def test_extract_score_from_various_formats() -> None:
    """Score extraction should handle multiple natural language formats."""
    assert _extract_score("我考了620分") == 620
    assert _extract_score("分数大概580") == 580
    assert _extract_score("差不多650左右") == 650  # "差不多" prefix is supported
    assert _extract_score("560分左右能上什么") == 560


def test_extract_expanded_major_aliases() -> None:
    """New major aliases should be recognized."""
    from app.services.rag_qa_service import _extract_preferred_majors

    majors = _extract_preferred_majors("我想学大数据和物联网")
    assert "Data Science and Big Data Technology" in majors
    assert "Internet of Things Engineering" in majors

    majors = _extract_preferred_majors("法学和会计哪个好")
    assert "Law" in majors
    assert "Accounting" in majors

    majors = _extract_preferred_majors("对临床医学和口腔医学感兴趣")
    assert "Clinical Medicine" in majors
    assert "Stomatology" in majors


def test_extract_all_provinces() -> None:
    """All 31 provinces should be extractable."""
    from app.services.rag_qa_service import _extract_province

    assert _extract_province("新疆考生能报什么学校") == "新疆"
    assert _extract_province("内蒙古理科500分") == "内蒙古"
    assert _extract_province("西藏有哪些好大学") == "西藏"
    assert _extract_province("宁夏的分数线") == "宁夏"


def test_qa_with_conversation_id() -> None:
    """QA should accept conversation_id without errors."""
    service = RagQaService()
    response = service.ask(
        QaAskRequest(
            question="平行志愿是什么意思？",
            province="广东",
            subject_type="物理类",
            conversation_id="test-conv-001",
        )
    )
    assert "平行志愿" in response.answer


def test_recommendation_without_score_gives_helpful_prompt() -> None:
    """Questions hinting at recommendation but missing score should return helpful guidance."""
    service = RagQaService()
    response = service.ask(
        QaAskRequest(
            question="能上什么大学",
            province="广东",
            subject_type="物理类",
            use_llm=False,
        )
    )
    assert "分数" in response.answer or "位次" in response.answer
