"""
Edition Matching Service
Phase 8: AI Book Import Pipeline

负责将识别的文本与元数据候选进行匹配
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import asyncio

from app.services.metadata.service import MetadataService
from app.services.ai.llm_provider import LLMProvider
from app.services.ai.mock_providers import MockLLMProvider


class EditionMatchResult:
    """匹配结果"""
    def __init__(
        self,
        candidate_index: int,
        confidence: float,
        reason: str,
        is_reliable: bool = False,
    ):
        self.candidate_index = candidate_index
        self.confidence = confidence
        self.reason = reason
        self.is_reliable = is_reliable

    def to_dict(self) -> Dict[str, Any]:
        return {
            "candidate_index": self.candidate_index,
            "confidence": self.confidence,
            "reason": self.reason,
            "is_reliable": self.is_reliable,
        }


class EditionMatchingService:
    """
    版本匹配服务

    流程:
    1. 使用 detected_text 搜索元数据
    2. 获取候选列表
    3. 使用 LLM 匹配最佳候选
    4. 返回匹配结果
    """

    def __init__(
        self,
        metadata_service: Optional[MetadataService] = None,
        llm_provider: Optional[LLMProvider] = None,
    ):
        self.metadata = metadata_service or MetadataService()
        self.llm = llm_provider or MockLLMProvider()

    async def search_and_match(
        self,
        detected_text: str,
        min_confidence: float = 0.5,
    ) -> Dict[str, Any]:
        """
        搜索并匹配版本

        Args:
            detected_text: OCR 识别的文本
            min_confidence: 最小置信度阈值

        Returns:
            {
                "success": bool,
                "detected_text": str,
                "candidates": List[Dict],
                "matched_index": Optional[int],
                "match_confidence": Optional[float],
                "reason": str,
                "status": "matched" | "needs_review" | "no_candidates" | "error",
            }
        """
        result = {
            "success": False,
            "detected_text": detected_text,
            "candidates": [],
            "matched_index": None,
            "match_confidence": None,
            "reason": "",
            "status": "error",
        }

        try:
            # 1. 清理查询文本
            query = self._clean_query(detected_text)
            result["search_query"] = query

            # 2. 搜索元数据
            search_result = await self.metadata.search(query, max_results=5)
            candidates = search_result.candidates

            if not candidates:
                result["status"] = "no_candidates"
                result["reason"] = "未找到匹配的图书"
                return result

            result["candidates"] = [
                {
                    "source": c.source,
                    "source_id": c.source_id,
                    "title": c.title,
                    "subtitle": c.subtitle,
                    "authors": c.authors,
                    "publisher": c.publisher,
                    "publish_year": c.publish_year,
                    "isbn13": c.isbn13,
                    "isbn10": c.isbn10,
                    "cover_url": c.cover_url,
                    "description": c.description,
                }
                for c in candidates
            ]
            result["candidates_count"] = len(candidates)

            # 3. 使用 LLM 匹配最佳候选
            match_result = await self._match_with_llm(query, candidates)

            if match_result:
                result["matched_index"] = match_result.candidate_index
                result["match_confidence"] = match_result.confidence
                result["match_reason"] = match_result.reason

                # 判断是否需要人工审核
                if match_result.is_reliable and match_result.confidence >= min_confidence:
                    result["status"] = "matched"
                    result["success"] = True
                else:
                    result["status"] = "needs_review"
                    result["reason"] = f"置信度较低 ({match_result.confidence:.2f})，需要人工确认"
            else:
                result["status"] = "needs_review"
                result["reason"] = "无法确定最佳匹配"

        except Exception as e:
            result["status"] = "error"
            result["reason"] = str(e)

        return result

    def _clean_query(self, detected_text: str) -> str:
        """清理查询文本"""
        # 移除常见噪声
        query = detected_text.strip()

        # 如果是 [未识别] 标记，返回空
        if query.startswith("[") and query.endswith("]"):
            return ""

        # 移除 ISBN 格式（如果有）
        import re
        # 保留 ISBN 用于后续搜索
        isbn_match = re.search(r'\d{9}[\dX]|\d{13}', query.replace("-", ""))
        if isbn_match:
            return isbn_match.group()

        # 移除多余空格和特殊字符
        query = re.sub(r'\s+', ' ', query)
        query = re.sub(r'[^\w\s\-一-鿿]', '', query)

        return query[:100]  # 限制长度

    async def _match_with_llm(
        self,
        query: str,
        candidates: List[Any],
    ) -> Optional[EditionMatchResult]:
        """使用 LLM 匹配最佳候选"""
        try:
            # 准备候选数据
            candidate_dicts = [
                {
                    "index": i,
                    "title": c.title,
                    "authors": c.authors,
                    "publisher": c.publisher,
                    "year": c.publish_year,
                }
                for i, c in enumerate(candidates)
            ]

            # 构建提示
            prompt = self._build_matching_prompt(query, candidate_dicts)

            # 调用 LLM (使用 mock classify_book)
            # 这里简化处理，实际应该调用专门的匹配方法
            classification = await self.llm.classify_book(
                title=query,
                author=candidates[0].authors[0] if candidates[0].authors else None,
            )

            # 根据置信度选择最佳候选
            # 简化逻辑：选择第一个高置信度候选
            for i, c in enumerate(candidates):
                # 计算简单相似度
                title_sim = self._title_similarity(query, c.title)

                if title_sim > 0.8:
                    return EditionMatchResult(
                        candidate_index=i,
                        confidence=title_sim,
                        reason=f"标题高度相似 ({title_sim:.2f})",
                        is_reliable=title_sim >= 0.9,
                    )

            # 如果没有高相似度，返回第一个候选（低置信度）
            if candidates:
                return EditionMatchResult(
                    candidate_index=0,
                    confidence=0.5,
                    reason="无高度匹配，返回最佳候选",
                    is_reliable=False,
                )

            return None

        except Exception as e:
            print(f"LLM matching error: {e}")
            return None

    def _build_matching_prompt(self, query: str, candidates: List[Dict]) -> str:
        """构建匹配提示"""
        prompt = f"""根据用户的查询，选择最匹配的图书版本。

查询: "{query}"

候选版本:
"""
        for c in candidates:
            prompt += f"\n[{c['index']}] {c['title']}"
            if c['authors']:
                prompt += f" - {', '.join(c['authors'])}"
            if c['publisher']:
                prompt += f" ({c['publisher']}"
                if c['year']:
                    prompt += f", {c['year']}"
                prompt += ")"

        prompt += "\n\n请输出最佳匹配的索引 (0-{}) 和置信度 (0-1):".format(len(candidates) - 1)
        return prompt

    def _title_similarity(self, query: str, title: str) -> float:
        """计算标题相似度（简化版）"""
        q = query.lower().strip()
        t = title.lower().strip()

        # 完全匹配
        if q == t:
            return 1.0

        # 包含匹配
        if q in t or t in q:
            return 0.9

        # 简单字符重叠
        q_set = set(q)
        t_set = set(t)
        if q_set and t_set:
            overlap = len(q_set & t_set) / len(q_set | t_set)
            return 0.5 + overlap * 0.3

        return 0.0


class BatchImportService:
    """
    批量导入服务

    处理多个 ScanItem 的批量导入
    """

    def __init__(
        self,
        matching_service: Optional[EditionMatchingService] = None,
    ):
        self.matching = matching_service or EditionMatchingService()

    async def process_batch(
        self,
        scan_items: List[Any],
        auto_import_threshold: float = 0.9,
    ) -> Dict[str, Any]:
        """
        批量处理扫描项

        Args:
            scan_items: ScanItem 列表
            auto_import_threshold: 自动导入的置信度阈值

        Returns:
            {
                "total": int,
                "auto_matched": int,
                "needs_review": int,
                "failed": int,
                "results": List[Dict],
            }
        """
        results = {
            "total": len(scan_items),
            "auto_matched": 0,
            "needs_review": 0,
            "failed": 0,
            "results": [],
        }

        for item in scan_items:
            try:
                # 跳过低置信度识别
                if item.confidence < 0.3:
                    results["failed"] += 1
                    results["results"].append({
                        "scan_item_id": item.id,
                        "status": "skipped",
                        "reason": "识别置信度过低",
                    })
                    continue

                # 搜索并匹配
                match_result = await self.matching.search_and_match(item.detected_text)

                if match_result["status"] == "matched":
                    if match_result["match_confidence"] >= auto_import_threshold:
                        results["auto_matched"] += 1
                    else:
                        results["needs_review"] += 1
                elif match_result["status"] == "needs_review":
                    results["needs_review"] += 1
                else:
                    results["failed"] += 1

                results["results"].append({
                    "scan_item_id": item.id,
                    "status": match_result["status"],
                    "detected_text": item.detected_text,
                    "candidates_count": match_result.get("candidates_count", 0),
                    "matched_index": match_result.get("matched_index"),
                    "match_confidence": match_result.get("match_confidence"),
                })

            except Exception as e:
                results["failed"] += 1
                results["results"].append({
                    "scan_item_id": item.id,
                    "status": "error",
                    "reason": str(e),
                })

        return results
