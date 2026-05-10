"""院校查询业务服务。

本服务负责院校查询的核心流程：
1. 先尝试读取 Redis 缓存。
2. 缓存未命中时查询 MySQL。
3. MySQL 不可用或结果为空时，使用内置 mock 数据兜底，保证演示页面可用。
4. 查询结果写回 Redis，减少后续重复查询压力。
"""

from decimal import Decimal
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.cache.redis_client import RedisCache


cache = RedisCache(namespace="gaokao-pilot:v2")


MOCK_SCHOOLS: list[dict[str, Any]] = [
    {
        "id": 900001,
        "school_code": "10001",
        "school_name": "北京大学",
        "province": "北京",
        "city": "北京",
        "school_type": "综合类",
        "school_level": "本科",
        "is_985": True,
        "is_211": True,
        "is_double_first_class": True,
        "description": "北京大学是一所综合类研究型大学，适合作为高分段考生的冲刺目标。",
    },
    {
        "id": 900002,
        "school_code": "10003",
        "school_name": "清华大学",
        "province": "北京",
        "city": "北京",
        "school_type": "理工类",
        "school_level": "本科",
        "is_985": True,
        "is_211": True,
        "is_double_first_class": True,
        "description": "清华大学以工科和交叉学科见长，招生竞争非常激烈。",
    },
    {
        "id": 900003,
        "school_code": "10558",
        "school_name": "中山大学",
        "province": "广东",
        "city": "广州",
        "school_type": "综合类",
        "school_level": "本科",
        "is_985": True,
        "is_211": True,
        "is_double_first_class": True,
        "description": "中山大学位于广东，是华南地区综合实力较强的高校。",
    },
    {
        "id": 900004,
        "school_code": "10561",
        "school_name": "华南理工大学",
        "province": "广东",
        "city": "广州",
        "school_type": "理工类",
        "school_level": "本科",
        "is_985": True,
        "is_211": True,
        "is_double_first_class": True,
        "description": "华南理工大学工科特色突出，计算机、软件等专业关注度较高。",
    },
    {
        "id": 900005,
        "school_code": "10559",
        "school_name": "暨南大学",
        "province": "广东",
        "city": "广州",
        "school_type": "综合类",
        "school_level": "本科",
        "is_985": False,
        "is_211": True,
        "is_double_first_class": True,
        "description": "暨南大学是广东地区热门 211 高校，专业覆盖面较广。",
    },
    {
        "id": 900006,
        "school_code": "10574",
        "school_name": "华南师范大学",
        "province": "广东",
        "city": "广州",
        "school_type": "师范类",
        "school_level": "本科",
        "is_985": False,
        "is_211": True,
        "is_double_first_class": True,
        "description": "华南师范大学是广东省重点师范类高校，也有较多非师范专业。",
    },
]


MOCK_SCORE_LINES: list[dict[str, Any]] = [
    {
        "school_id": school_id,
        "year": year,
        "province": "广东",
        "subject_type": "物理类",
        "batch": "本科批",
        "major_name": major_name,
        "min_score": min_score,
        "min_rank": min_rank,
        "avg_score": min_score + 6,
        "max_score": min_score + 16,
    }
    for school_id, major_name, base_score, base_rank in [
        (900001, "计算机科学与技术", 685, 650),
        (900002, "人工智能", 690, 420),
        (900003, "软件工程", 635, 8200),
        (900004, "计算机科学与技术", 628, 10500),
        (900005, "人工智能", 604, 24500),
        (900006, "软件工程", 594, 33500),
    ]
    for year, min_score, min_rank in [
        (2024, base_score, base_rank),
        (2023, base_score - 4, base_rank + 900),
        (2022, base_score - 8, base_rank + 1800),
    ]
]


class SchoolService:
    """封装院校、院校详情、历年分数线相关查询。"""

    SCHOOL_DETAIL_TTL_SECONDS = 3600
    SCHOOL_SEARCH_TTL_SECONDS = 600
    SCORE_LINES_TTL_SECONDS = 1800
    EMPTY_RESULT_TTL_SECONDS = 300

    @staticmethod
    def search_schools(
        db: Session,
        *,
        school_name: str | None,
        province: str | None,
        school_level: str | None,
        is_985: bool | None,
        is_211: bool | None,
        page: int,
        page_size: int,
    ) -> tuple[int, list[dict[str, Any]]]:
        """分页搜索院校。

        业务流程：
        1. 根据查询条件构造 Redis key。
        2. 如果缓存命中，直接返回缓存的 total 和 items。
        3. 如果缓存未命中，动态拼接安全 SQL 条件并查询 MySQL。
        4. 如果 MySQL 查询异常或没有结果，则走 mock 数据兜底。
        5. 将最终结果写入 Redis，设置短 TTL，适合高频搜索。
        """
        cache_key = cache.build_key(
            "schools",
            "search",
            school_name,
            province,
            school_level,
            is_985,
            is_211,
            page,
            page_size,
        )
        hit, cached_value = cache.get_json(cache_key)
        if hit:
            return int(cached_value["total"]), cached_value["items"]

        try:
            where_sql, params = SchoolService._build_school_filters(
                school_name=school_name,
                province=province,
                school_level=school_level,
                is_985=is_985,
                is_211=is_211,
            )
            params["limit"] = page_size
            params["offset"] = (page - 1) * page_size

            total = db.execute(
                text(f"SELECT COUNT(*) FROM school {where_sql}"),
                params,
            ).scalar_one()

            rows = db.execute(
                text(
                    f"""
                    SELECT
                      id,
                      name AS school_name,
                      province,
                      city,
                      school_type,
                      education_level AS school_level,
                      is_985,
                      is_211,
                      is_double_first_class
                    FROM school
                    {where_sql}
                    ORDER BY is_985 DESC, is_211 DESC, name ASC
                    LIMIT :limit OFFSET :offset
                    """
                ),
                params,
            ).mappings()
            items = [SchoolService._normalize_school_row(row) for row in rows]
        except SQLAlchemyError:
            total, items = SchoolService._search_mock_schools(
                school_name=school_name,
                province=province,
                school_level=school_level,
                is_985=is_985,
                is_211=is_211,
                page=page,
                page_size=page_size,
            )
        else:
            if int(total) == 0:
                total, items = SchoolService._search_mock_schools(
                    school_name=school_name,
                    province=province,
                    school_level=school_level,
                    is_985=is_985,
                    is_211=is_211,
                    page=page,
                    page_size=page_size,
                )
        cache.set_json(
            cache_key,
            {"total": int(total), "items": items},
            SchoolService.SCHOOL_SEARCH_TTL_SECONDS,
        )
        return int(total), items

    @staticmethod
    def get_school_detail(db: Session, school_id: int) -> dict[str, Any] | None:
        """根据院校 ID 查询详情。

        业务流程：
        1. 先查 Redis 中的 school:{school_id}。
        2. 未命中时查 MySQL school 表。
        3. 当前表没有 description 字段，所以用院校基础信息拼一个简介。
        4. 数据库不可用或未查到时，用 mock 院校详情兜底。
        """
        cache_key = cache.build_key("school", school_id)
        hit, cached_value = cache.get_json(cache_key)
        if hit:
            return cached_value

        try:
            row = db.execute(
                text(
                    """
                    SELECT
                      id,
                      school_code,
                      name AS school_name,
                      province,
                      city,
                      school_type,
                      education_level AS school_level,
                      is_985,
                      is_211,
                      is_double_first_class
                    FROM school
                    WHERE id = :school_id
                    """
                ),
                {"school_id": school_id},
            ).mappings().first()
        except SQLAlchemyError:
            school = SchoolService._get_mock_school_detail(school_id)
            cache.set_json(cache_key, school, SchoolService.SCHOOL_DETAIL_TTL_SECONDS)
            return school

        if row is None:
            school = SchoolService._get_mock_school_detail(school_id)
            cache.set_json(cache_key, school, SchoolService.EMPTY_RESULT_TTL_SECONDS)
            return school

        school = SchoolService._normalize_school_row(row)
        school["description"] = SchoolService._build_school_description(school)
        cache.set_json(cache_key, school, SchoolService.SCHOOL_DETAIL_TTL_SECONDS)
        return school

    @staticmethod
    def get_school_score_lines(
        db: Session,
        *,
        school_id: int,
        province: str | None,
        year: int | None,
        subject_type: str | None,
        major_name: str | None,
    ) -> list[dict[str, Any]]:
        """查询某所院校的历年分数线。

        业务流程：
        1. 查询参数会参与缓存 key，确保不同省份、年份、科类互不串用。
        2. 根据可选参数动态追加 SQL 条件。
        3. 查询 score_line，并左连接 major 拿到专业名称。
        4. 没有结果或数据库不可用时，返回 mock 分数线，方便页面演示。
        """
        cache_key = cache.build_key(
            "score_lines",
            school_id,
            province,
            year,
            subject_type,
            major_name,
        )
        hit, cached_value = cache.get_json(cache_key)
        if hit:
            return cached_value

        params: dict[str, Any] = {"school_id": school_id}
        conditions = ["sl.school_id = :school_id"]
        if province:
            conditions.append("sl.province = :province")
            params["province"] = province
        if year is not None:
            conditions.append("sl.year = :year")
            params["year"] = year
        if subject_type:
            conditions.append("sl.subject_type = :subject_type")
            params["subject_type"] = subject_type
        if major_name:
            conditions.append("m.name LIKE :major_name")
            params["major_name"] = f"%{major_name}%"
        where_sql = " AND ".join(conditions)

        try:
            rows = db.execute(
                text(
                    f"""
                    SELECT
                      sl.year,
                      sl.province,
                      sl.subject_type,
                      sl.batch,
                      m.name AS major_name,
                      sl.min_score,
                      sl.min_rank,
                      sl.avg_score,
                      sl.max_score
                    FROM score_line sl
                    LEFT JOIN major m ON m.id = sl.major_id
                    WHERE {where_sql}
                    ORDER BY sl.year DESC, sl.min_score DESC
                    LIMIT 50
                    """
                ),
                params,
            ).mappings()
            score_lines = [SchoolService._normalize_score_line_row(row) for row in rows]
        except SQLAlchemyError:
            score_lines = SchoolService._get_mock_score_lines(
                school_id=school_id,
                province=province,
                year=year,
                subject_type=subject_type,
                major_name=major_name,
            )
        else:
            if not score_lines:
                score_lines = SchoolService._get_mock_score_lines(
                    school_id=school_id,
                    province=province,
                    year=year,
                    subject_type=subject_type,
                    major_name=major_name,
                )
        ttl = SchoolService.SCORE_LINES_TTL_SECONDS if score_lines else SchoolService.EMPTY_RESULT_TTL_SECONDS
        cache.set_json(cache_key, score_lines, ttl)
        return score_lines

    @staticmethod
    def school_exists(db: Session, school_id: int) -> bool:
        """判断院校是否存在；数据库不可用时也会检查 mock 数据。"""
        try:
            exists = db.execute(
                text("SELECT 1 FROM school WHERE id = :school_id"),
                {"school_id": school_id},
            ).scalar_one_or_none()
            return exists is not None or SchoolService._get_mock_school_detail(school_id) is not None
        except SQLAlchemyError:
            return SchoolService._get_mock_school_detail(school_id) is not None

    @staticmethod
    def _build_school_filters(
        *,
        school_name: str | None,
        province: str | None,
        school_level: str | None,
        is_985: bool | None,
        is_211: bool | None,
    ) -> tuple[str, dict[str, Any]]:
        """根据搜索条件构造 SQL WHERE 片段和绑定参数，避免字符串拼接注入。"""
        conditions: list[str] = []
        params: dict[str, Any] = {}

        if school_name:
            conditions.append("name LIKE :school_name")
            params["school_name"] = f"%{school_name}%"
        if province:
            conditions.append("province = :province")
            params["province"] = province
        if school_level:
            conditions.append("education_level = :school_level")
            params["school_level"] = school_level
        if is_985 is not None:
            conditions.append("is_985 = :is_985")
            params["is_985"] = int(is_985)
        if is_211 is not None:
            conditions.append("is_211 = :is_211")
            params["is_211"] = int(is_211)

        if not conditions:
            return "", params
        return "WHERE " + " AND ".join(conditions), params

    @staticmethod
    def _normalize_school_row(row: Any) -> dict[str, Any]:
        """把 MySQL tinyint 标签字段转换成前端更好理解的 bool。"""
        data = dict(row)
        data["is_985"] = bool(data["is_985"])
        data["is_211"] = bool(data["is_211"])
        data["is_double_first_class"] = bool(data["is_double_first_class"])
        return data

    @staticmethod
    def _normalize_score_line_row(row: Any) -> dict[str, Any]:
        """把 SQLAlchemy 行数据转换成 JSON 友好的普通 Python 类型。"""
        data = dict(row)
        for key, value in list(data.items()):
            if isinstance(value, Decimal):
                data[key] = float(value)
        return data

    @staticmethod
    def _build_school_description(school: dict[str, Any]) -> str:
        """当前 school 表没有简介字段，这里根据基础信息生成一段兜底简介。"""
        return (
            f"{school['school_name']}位于{school['province']}{school.get('city') or ''}，"
            f"是一所{school.get('school_type') or '综合'}院校，可结合历年分数线和专业计划进一步评估。"
        )

    @staticmethod
    def _search_mock_schools(
        *,
        school_name: str | None,
        province: str | None,
        school_level: str | None,
        is_985: bool | None,
        is_211: bool | None,
        page: int,
        page_size: int,
    ) -> tuple[int, list[dict[str, Any]]]:
        """当 MySQL 未准备好或暂无数据时，按同样条件过滤 mock 院校。"""
        filtered = []
        for school in MOCK_SCHOOLS:
            if school_name and school_name not in school["school_name"]:
                continue
            if province and school["province"] != province:
                continue
            if school_level and school["school_level"] != school_level:
                continue
            if is_985 is not None and school["is_985"] != is_985:
                continue
            if is_211 is not None and school["is_211"] != is_211:
                continue
            filtered.append({key: value for key, value in school.items() if key != "description"})

        start = (page - 1) * page_size
        end = start + page_size
        return len(filtered), filtered[start:end]

    @staticmethod
    def _get_mock_school_detail(school_id: int) -> dict[str, Any] | None:
        """根据 ID 返回一条 mock 院校详情。"""
        for school in MOCK_SCHOOLS:
            if school["id"] == school_id:
                return dict(school)
        return None

    @staticmethod
    def _get_mock_score_lines(
        *,
        school_id: int,
        province: str | None,
        year: int | None,
        subject_type: str | None,
        major_name: str | None,
    ) -> list[dict[str, Any]]:
        """用与真实查询相同的参数过滤 mock 分数线。"""
        rows = []
        for line in MOCK_SCORE_LINES:
            if line["school_id"] != school_id:
                continue
            if province and line["province"] != province:
                continue
            if year is not None and line["year"] != year:
                continue
            if subject_type and line["subject_type"] != subject_type:
                continue
            if major_name and major_name not in (line["major_name"] or ""):
                continue
            rows.append({key: value for key, value in line.items() if key != "school_id"})
        return rows
