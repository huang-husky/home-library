"""
AI Classification Service
Phase 9: 基于中图法的 AI 辅助分类

重要原则：
- LLM 不允许自由生成分类号
- 必须从预定义的分类树中选择
- 后端验证分类号必须存在
"""
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Category


@dataclass
class ClassificationCandidate:
    """分类候选"""
    category_code: str
    category_name: str
    confidence: float
    reason: str


class ClassificationService:
    """
    图书分类服务

    流程：
    Book Metadata → 加载分类树 → LLM 选择 → 验证 → 结果
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self._category_cache: Optional[List[Category]] = None

    async def _load_categories(self) -> List[Category]:
        """加载所有分类到缓存"""
        if self._category_cache is None:
            result = await self.db.execute(
                select(Category).order_by(Category.code)
            )
            self._category_cache = list(result.scalars().all())
        return self._category_cache

    async def classify_book(
        self,
        title: str,
        subtitle: Optional[str] = None,
        authors: Optional[List[str]] = None,
        publisher: Optional[str] = None,
        description: Optional[str] = None,
        top_k: int = 3,
    ) -> Dict[str, Any]:
        """
        对图书进行分类

        Args:
            title: 书名
            subtitle: 副标题
            authors: 作者列表
            publisher: 出版社
            description: 简介
            top_k: 返回前 k 个候选

        Returns:
            {
                "success": bool,
                "suggestions": List[ClassificationCandidate],
                "requires_confirmation": bool,
            }
        """
        # 1. 加载所有可用分类
        categories = await self._load_categories()

        if not categories:
            return {
                "success": False,
                "suggestions": [],
                "requires_confirmation": True,
                "message": "分类库为空，请先导入中图法数据",
            }

        # 2. 根据规则预筛选候选分类
        candidates = self._pre_filter_categories(
            categories, title, subtitle, description
        )

        # 3. 计算匹配分数
        scored_candidates = self._score_categories(
            candidates, title, subtitle, authors, publisher, description
        )

        # 4. 排序并选择 top_k
        scored_candidates.sort(key=lambda x: x.confidence, reverse=True)
        top_candidates = scored_candidates[:top_k]

        # 5. 判断是否需要人工确认
        requires_confirmation = True
        if top_candidates and top_candidates[0].confidence >= 0.85:
            requires_confirmation = False

        return {
            "success": len(top_candidates) > 0,
            "suggestions": [
                {
                    "category_code": c.category_code,
                    "category_name": c.category_name,
                    "confidence": c.confidence,
                    "reason": c.reason,
                }
                for c in top_candidates
            ],
            "requires_confirmation": requires_confirmation,
            "message": None if top_candidates else "无法确定合适的分类",
        }

    def _pre_filter_categories(
        self,
        categories: List[Category],
        title: str,
        subtitle: Optional[str],
        description: Optional[str],
    ) -> List[Category]:
        """预筛选候选分类（基于关键词匹配）"""
        # 合并文本
        text = f"{title} {subtitle or ''} {description or ''}".lower()

        # 关键词到分类的映射
        keyword_mapping = {
            # 文学
            "小说": ["I247", "I712", "I561"],
            "文学": ["I", "H319"],
            "诗歌": ["I227", "H319.4"],
            "散文": ["I267", "I16"],

            # 计算机
            "计算机": ["TP3", "TP39"],
            "编程": ["TP311", "TP312"],
            "程序": ["TP311", "TP312"],
            "算法": ["TP301.6", "TP312"],
            "人工智能": ["TP18", "TP391"],
            "机器学习": ["TP181", "TP391"],
            "深度学习": ["TP181", "TP391.413"],
            "数据": ["TP311.13", "TP274"],
            "网络": ["TP393", "TP393.09"],
            "安全": ["TP309", "TP393.08"],

            # 科学
            "数学": ["O1", "O17", "O29"],
            "物理": ["O4", "O57"],
            "化学": ["O6", "O64"],
            "生物": ["Q", "Q1"],

            # 历史
            "历史": ["K", "K2", "K89"],
            "中国": ["K2", "K892"],
            "世界": ["K1", "K10"],

            # 经济
            "经济": ["F", "F0"],
            "金融": ["F83", "F830"],
            "管理": ["F27", "C93"],
            "营销": ["F713.5", "F274"],

            # 哲学/心理
            "哲学": ["B", "B0"],
            "心理": ["B84", "B845"],
            "社会": ["C91", "C912"],

            # 艺术
            "艺术": ["J", "J2", "J6"],
            "音乐": ["J6", "J605"],
            "绘画": ["J2", "J21"],
            "摄影": ["J4", "J41"],

            # 语言
            "英语": ["H31", "H319"],
            "日语": ["H36", "H369"],
            "语言": ["H", "H0"],

            # 教育
            "教育": ["G4", "G62"],
            "考试": ["G424.7", "G642.4"],

            # 医学
            "医学": ["R", "R4"],
            "健康": ["R161", "R395"],
        }

        # 收集匹配的分类代码
        matched_codes = set()
        for keyword, codes in keyword_mapping.items():
            if keyword in text:
                matched_codes.update(codes)

        # 如果没有关键词匹配，返回所有一级和二级分类
        if not matched_codes:
            return [c for c in categories if c.level <= 2]

        # 筛选匹配的分类
        result = []
        for cat in categories:
            # 直接匹配
            if any(cat.code.startswith(code) for code in matched_codes):
                result.append(cat)
            # 或者是这些分类的父分类
            elif cat.level == 1:
                result.append(cat)

        return result if result else categories[:20]  # 至少返回前20个

    def _score_categories(
        self,
        categories: List[Category],
        title: str,
        subtitle: Optional[str],
        authors: Optional[List[str]],
        publisher: Optional[str],
        description: Optional[str],
    ) -> List[ClassificationCandidate]:
        """为候选分类打分"""
        candidates = []
        text = f"{title} {subtitle or ''} {description or ''}".lower()

        # 出版社到分类的映射
        publisher_mapping = {
            "人民邮电出版社": ["TP", "TM"],
            "电子工业出版社": ["TP", "TN"],
            "机械工业出版社": ["TH", "TP"],
            "清华大学出版社": ["TP", "O", "H"],
            "高等教育出版社": ["O", "H", "G"],
            "人民文学出版社": ["I"],
            "商务印书馆": ["H", "B", "C"],
            "中华书局": ["K", "I"],
        }

        for cat in categories:
            score = 0.0
            reasons = []

            # 1. 名称匹配
            cat_name_lower = cat.name.lower()
            if cat_name_lower in text:
                score += 0.4
                reasons.append(f"分类名 '{cat.name}' 匹配")

            # 2. 关键词匹配（更细粒度）
            keywords = self._extract_keywords(cat.name, cat.description)
            matched_keywords = [k for k in keywords if k in text]
            if matched_keywords:
                score += 0.2 * len(matched_keywords)
                reasons.append(f"关键词匹配: {', '.join(matched_keywords[:3])}")

            # 3. 出版社匹配
            if publisher:
                for pub, codes in publisher_mapping.items():
                    if pub in publisher and any(cat.code.startswith(c) for c in codes):
                        score += 0.15
                        reasons.append(f"出版社 '{pub}' 偏向此分类")
                        break

            # 4. 层级惩罚（倾向于更具体的分类）
            if cat.level == 3:
                score += 0.1
            elif cat.level == 1:
                score -= 0.1

            # 5. 特定规则
            score += self._apply_specific_rules(cat, title, subtitle, description)

            # 确保分数在合理范围内
            score = max(0.1, min(0.95, score))

            if score > 0.2:  # 只返回有一定置信度的
                candidates.append(ClassificationCandidate(
                    category_code=cat.code,
                    category_name=cat.name,
                    confidence=round(score, 3),
                    reason="; ".join(reasons) if reasons else "基于内容分析",
                ))

        return candidates

    def _extract_keywords(self, name: Optional[str], description: Optional[str]) -> List[str]:
        """从分类名和描述中提取关键词"""
        text = f"{name or ''} {description or ''}".lower()

        # 常见技术关键词
        tech_keywords = [
            "程序", "软件", "系统", "网络", "数据库", "算法",
            "人工智能", "机器学习", "深度学习", "数据", "安全",
            "开发", "设计", "架构", "前端", "后端", "移动",
            "python", "java", "javascript", "c++", "go", "rust",
        ]

        # 常见文学关键词
        lit_keywords = [
            "小说", "故事", "传记", "历史", "科幻", "悬疑",
            "言情", "武侠", "现代", "当代", "古典", "名著",
        ]

        # 常见科学关键词
        sci_keywords = [
            "数学", "物理", "化学", "生物", "天文", "地理",
            "工程", "技术", "应用", "理论", "实验",
        ]

        all_keywords = tech_keywords + lit_keywords + sci_keywords
        return [k for k in all_keywords if k in text]

    def _apply_specific_rules(
        self,
        category: Category,
        title: str,
        subtitle: Optional[str],
        description: Optional[str],
    ) -> float:
        """应用特定规则调整分数"""
        score = 0.0
        text = f"{title} {subtitle or ''} {description or ''}".lower()

        # 计算机类特定规则
        if category.code.startswith("TP"):
            if any(kw in text for kw in ["python", "java", "c++", "编程", "程序"]):
                if category.code.startswith("TP312") or category.code.startswith("TP311"):
                    score += 0.2

            if any(kw in text for kw in ["机器学习", "深度学习", "ai", "人工智能"]):
                if category.code.startswith("TP18"):
                    score += 0.3

            if any(kw in text for kw in ["数据", "大数据", "数据分析"]):
                if category.code.startswith("TP274") or category.code.startswith("TP311.13"):
                    score += 0.2

        # 文学类特定规则
        if category.code.startswith("I"):
            if "中国" in text and category.code.startswith("I2"):
                score += 0.15
            if "外国" in text and category.code.startswith("I3"):
                score += 0.15
            if "小说" in text and ("247" in category.code or "712" in category.code):
                score += 0.15

        # 历史类特定规则
        if category.code.startswith("K"):
            if "中国" in text and category.code.startswith("K2"):
                score += 0.2
            if "世界" in text and category.code.startswith("K1"):
                score += 0.2

        return score

    async def validate_category_code(self, code: str) -> Optional[Category]:
        """验证分类号是否存在"""
        result = await self.db.execute(
            select(Category).where(Category.code == code)
        )
        return result.scalar_one_or_none()

    async def get_classification_path(self, code: str) -> List[Dict[str, Any]]:
        """获取分类的完整路径"""
        path = []
        current = await self.validate_category_code(code)

        while current:
            path.append({
                "id": current.id,
                "code": current.code,
                "name": current.name,
                "level": current.level,
            })

            if current.parent_id:
                result = await self.db.execute(
                    select(Category).where(Category.id == current.parent_id)
                )
                current = result.scalar_one_or_none()
            else:
                current = None

        return list(reversed(path))


class BatchClassificationService:
    """批量分类服务"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.classifier = ClassificationService(db)

    async def classify_books(
        self,
        books_data: List[Dict[str, Any]],
        auto_assign_threshold: float = 0.85,
    ) -> Dict[str, Any]:
        """
        批量分类图书

        Args:
            books_data: 图书数据列表
            auto_assign_threshold: 自动分配的置信度阈值

        Returns:
            {
                "total": int,
                "auto_assigned": int,
                "needs_review": int,
                "failed": int,
                "results": List[Dict],
            }
        """
        results = {
            "total": len(books_data),
            "auto_assigned": 0,
            "needs_review": 0,
            "failed": 0,
            "results": [],
        }

        for book_data in books_data:
            try:
                result = await self.classifier.classify_book(
                    title=book_data.get("title", ""),
                    subtitle=book_data.get("subtitle"),
                    authors=book_data.get("authors", []),
                    publisher=book_data.get("publisher"),
                    description=book_data.get("description"),
                )

                if result["success"]:
                    top_suggestion = result["suggestions"][0] if result["suggestions"] else None

                    if top_suggestion and top_suggestion["confidence"] >= auto_assign_threshold:
                        results["auto_assigned"] += 1
                        status = "auto_assigned"
                    else:
                        results["needs_review"] += 1
                        status = "needs_review"

                    results["results"].append({
                        "book_id": book_data.get("id"),
                        "title": book_data.get("title"),
                        "status": status,
                        "suggestions": result["suggestions"],
                    })
                else:
                    results["failed"] += 1
                    results["results"].append({
                        "book_id": book_data.get("id"),
                        "title": book_data.get("title"),
                        "status": "failed",
                        "message": result.get("message", "分类失败"),
                    })

            except Exception as e:
                results["failed"] += 1
                results["results"].append({
                    "book_id": book_data.get("id"),
                    "title": book_data.get("title"),
                    "status": "error",
                    "message": str(e),
                })

        return results
