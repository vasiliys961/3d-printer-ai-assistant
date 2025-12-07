"""
Метрики производительности для приложения
"""
import time
from typing import Dict, Any, Optional
from functools import wraps
from dataclasses import dataclass, field
from datetime import datetime
from utils.logger import logger


@dataclass
class PerformanceMetrics:
    """Метрики производительности"""
    request_id: str
    endpoint: str
    method: str
    execution_time_ms: float
    timestamp: datetime = field(default_factory=datetime.now)
    user_id: Optional[int] = None
    session_id: Optional[int] = None
    llm_calls: int = 0
    llm_tokens_used: int = 0
    rag_searches: int = 0
    rag_results_count: int = 0
    db_queries: int = 0
    status_code: int = 200
    error: Optional[str] = None


class MetricsCollector:
    """Сборщик метрик производительности"""
    
    def __init__(self):
        self.metrics: list[PerformanceMetrics] = []
        self._request_metrics: Dict[str, Dict[str, Any]] = {}
    
    def start_request(self, request_id: str, endpoint: str, method: str) -> str:
        """Начать отслеживание запроса"""
        self._request_metrics[request_id] = {
            "endpoint": endpoint,
            "method": method,
            "start_time": time.time(),
            "llm_calls": 0,
            "llm_tokens": 0,
            "rag_searches": 0,
            "rag_results": 0,
            "db_queries": 0
        }
        return request_id
    
    def end_request(
        self,
        request_id: str,
        status_code: int = 200,
        user_id: Optional[int] = None,
        session_id: Optional[int] = None,
        error: Optional[str] = None
    ) -> PerformanceMetrics:
        """Завершить отслеживание запроса и вернуть метрики"""
        if request_id not in self._request_metrics:
            logger.warning(f"Request {request_id} not found in metrics")
            return None
        
        metrics_data = self._request_metrics.pop(request_id)
        execution_time = (time.time() - metrics_data["start_time"]) * 1000  # в миллисекундах
        
        metric = PerformanceMetrics(
            request_id=request_id,
            endpoint=metrics_data["endpoint"],
            method=metrics_data["method"],
            execution_time_ms=execution_time,
            user_id=user_id,
            session_id=session_id,
            llm_calls=metrics_data["llm_calls"],
            llm_tokens_used=metrics_data["llm_tokens"],
            rag_searches=metrics_data["rag_searches"],
            rag_results_count=metrics_data["rag_results"],
            db_queries=metrics_data["db_queries"],
            status_code=status_code,
            error=error
        )
        
        self.metrics.append(metric)
        
        # Логируем метрики
        logger.info(
            f"Request {request_id} completed: {execution_time:.2f}ms | "
            f"LLM calls: {metrics_data['llm_calls']} ({metrics_data['llm_tokens']} tokens) | "
            f"RAG searches: {metrics_data['rag_searches']} ({metrics_data['rag_results']} results) | "
            f"DB queries: {metrics_data['db_queries']}"
        )
        
        return metric
    
    def record_llm_call(self, request_id: str, tokens_used: int = 0):
        """Записать вызов LLM"""
        if request_id in self._request_metrics:
            self._request_metrics[request_id]["llm_calls"] += 1
            self._request_metrics[request_id]["llm_tokens"] += tokens_used
    
    def record_rag_search(self, request_id: str, results_count: int = 0):
        """Записать поиск RAG"""
        if request_id in self._request_metrics:
            self._request_metrics[request_id]["rag_searches"] += 1
            self._request_metrics[request_id]["rag_results"] += results_count
    
    def record_db_query(self, request_id: str):
        """Записать запрос к БД"""
        if request_id in self._request_metrics:
            self._request_metrics[request_id]["db_queries"] += 1
    
    def get_stats(self, limit: int = 100) -> Dict[str, Any]:
        """Получить статистику по последним метрикам"""
        recent_metrics = self.metrics[-limit:] if len(self.metrics) > limit else self.metrics
        
        if not recent_metrics:
            return {}
        
        avg_time = sum(m.execution_time_ms for m in recent_metrics) / len(recent_metrics)
        avg_llm_calls = sum(m.llm_calls for m in recent_metrics) / len(recent_metrics)
        avg_tokens = sum(m.llm_tokens_used for m in recent_metrics) / len(recent_metrics)
        avg_rag_searches = sum(m.rag_searches for m in recent_metrics) / len(recent_metrics)
        
        return {
            "total_requests": len(recent_metrics),
            "avg_execution_time_ms": round(avg_time, 2),
            "avg_llm_calls": round(avg_llm_calls, 2),
            "avg_tokens_per_request": round(avg_tokens, 2),
            "avg_rag_searches": round(avg_rag_searches, 2),
            "total_errors": sum(1 for m in recent_metrics if m.error)
        }


# Глобальный экземпляр сборщика метрик
metrics_collector = MetricsCollector()


def track_performance(func):
    """Декоратор для отслеживания производительности функции"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            execution_time = (time.time() - start_time) * 1000
            logger.debug(f"{func.__name__} executed in {execution_time:.2f}ms")
            return result
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"{func.__name__} failed after {execution_time:.2f}ms: {e}", exc_info=True)
            raise
    return wrapper

