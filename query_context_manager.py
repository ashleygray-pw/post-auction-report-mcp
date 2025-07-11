# query_context_manager.py
from collections import defaultdict
from typing import Any
import re

# Session-scoped context container
default_context_max = 5

class QueryContext:
    def __init__(self, max_history: int = default_context_max):
        self.recent_queries = []
        self.recent_tables = set()
        self.recent_columns = set()
        self.filter_history = {}
        self.join_history = []
        self.max_history = max_history
        self.custom = {}

    def add_query(self, query_info: dict[str, Any]):
        self.recent_queries.append(query_info)
        if len(self.recent_queries) > self.max_history:
            self.recent_queries.pop(0)

        for t in query_info.get("tables", []):
            self.recent_tables.add(t)
        if "table_name" in query_info:
            self.recent_tables.add(query_info["table_name"])

        for c in query_info.get("columns", []):
            self.recent_columns.add(c)

        for col, val in query_info.get("filters", {}).items():
            self.filter_history[col] = val

        if join := query_info.get("join"):
            self.join_history.append(join)
            if len(self.join_history) > self.max_history:
                self.join_history.pop(0)

    def get_relevant_context(self, query_intent: str) -> dict[str, Any]:
        return {
            "recent_tables": list(self.recent_tables),
            "recent_columns": list(self.recent_columns),
            "filter_history": self.filter_history,
            "relevant_joins": self.join_history,
            "recent_queries": self.recent_queries[-3:]
        }
    def get(self, key: str, default=None):
        return self.custom.get(key, default)

    def set(self, key: str, value: Any):
        self.custom[key] = value


# Central registry for per-session contexts
SESSION_CONTEXTS = defaultdict(QueryContext)

def get_context(session_id: str) -> QueryContext:
    return SESSION_CONTEXTS[session_id]