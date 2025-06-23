from typing import Any
from mcp.server.fastmcp import FastMCP
import databricks.sql
import os
from dotenv import load_dotenv
from difflib import get_close_matches
from functools import lru_cache
import inspect
from fastapi import Request
from query_context_manager import get_context
import re
from sqlglot import parse_one
from sqlglot.expressions import Column

load_dotenv()
mcp = FastMCP("databricks")
try:
    from starlette.requests import Request as StarletteRequest
    if isinstance(request := mcp.current_request, StarletteRequest):
        session_id = request.headers.get("x-session-id", "default")
    else:
        session_id = "default"
except Exception:
    session_id = "default"

context = get_context(session_id)

# Load credentials
server_hostname = os.getenv("DATABRICKS_HOST")
http_path = os.getenv("DATABRICKS_HTTP_PATH")
access_token = os.getenv("DATABRICKS_TOKEN")

if not all([server_hostname, http_path, access_token]):
    raise EnvironmentError("Missing Databricks credentials in environment variables.")

def get_connection():
    return databricks.sql.connect(
        server_hostname=server_hostname,
        http_path=http_path,
        access_token=access_token,
    )
    
# ✅ Guardrail
ALLOWED_VIEWS = {
    "item_basics", "item_account_bidding", "people_master",
}

@lru_cache
def get_allowed_views() -> set[str]:
    query = """
        SELECT DISTINCT EXPLODE(table_view) AS full_view_name
        FROM main.ai_data_assets.all_column_metadata
        WHERE table_view IS NOT NULL
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query)
        # Normalize by stripping schema prefix
        return {row[0].split('.')[-1].lower() for row in cursor.fetchall()}

registered_tools = {}

def track_tool(func):
    signature = inspect.signature(func)
    doc = inspect.getdoc(func)
    param_info = {
        param: str(info.annotation) if info.annotation != inspect._empty else "Any"
        for param, info in signature.parameters.items()
    }
    registered_tools[func.__name__] = {
        "parameters": param_info,
        "doc": doc
    }
    return func

original_tool = mcp.tool

def tracked_tool(*args, **kwargs):
    def wrapper(func):
        tracked_func = track_tool(func)
        return original_tool(*args, **kwargs)(tracked_func)
    return wrapper

mcp.tool = tracked_tool

@lru_cache
def get_valid_columns_for(table_name: str) -> set[str]:
    query = """
        SELECT DISTINCT column_name
        FROM main.ai_data_assets.all_column_metadata
        WHERE source_table = ?
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, [table_name])
        return {row[0] for row in cursor.fetchall()}
    
def extract_filters(where_clause: str | None) -> dict[str, str]:
    """
    Extract filters from a WHERE clause string.
    Returns a dictionary of column names and their corresponding values.
    """
    if not where_clause:
        return {}
    filters = {}
    for clause in re.split(r'\s+AND\s+', where_clause, flags=re.IGNORECASE):
        if '=' in clause:
            key, val = clause.split('=', 1)
            filters[key.strip()] = val.strip().strip("'\"")
    return filters   

@mcp.tool()
def list_available_views() -> list[dict[str, str]]:
    """
    Use this tool at the beginning of each session to get a list of available views. 
    Once you have the context of the table views, identify the ones that are most relevant to the user question. 
    Use get_table_views_metadata to retrieve the column metadata for those views.
    This will help you understand the data structure and what columns are available for querying.
    If the data needed is not avaliable in the originally selected views, select additional views to query.
    If the data needed is not available in any of the views, inform the user that the data is not available and suggest alternative approaches based on the data that is avaliable.
    """
    return [
  {
    "view": "item_basics",
    "description": "Our complete inventory -- past, present and future -- of item sold or selling on PurpleWave.com.  Rows are built out to include lots of info you would want on an item, including identifiers (item_id, ims_item_id, item_icn), make/model details, VIN/serial number, and classification taxonomy (industry, family, category).",
    "usage": "Use to retrieve basic item details such as auction grouping, auction start and end time, item identifiers, make/model, classification taxonomy, and winning bidder and seller information."
  },
  {
    "view": "item_account_bidding",
    "description": "The table contains data related to bidding metrics at the item and account level. It includes information such as the bidder's account, bid dates, bid amounts, and whether the bidder is considered serious. This data can be used to analyze bidding patterns, assess bidder engagement, and evaluate the competitiveness of bids over time.",
    "usage": "Use to understand bidding dynamics and auction participant behavior."
  },
  {
    "view": "people_master",
    "description": "Stores entities (accounts, contacts and companies) all unioned together into one big file.  This [mostly] works because these entities have so many fields in common. The table contains information about various accounts that interact with item, including individuals and companies. It records details such as names, addresses, and identifiers, along with timestamps for when the records were created. This data can be used for tracking entity activity over time, analyzing demographic information, and understanding entity relationships within the system. Possible use cases include customer segmentation, marketing analysis, and reporting on entity engagement",
    "usage": "Use to retrieve information about people and companies associated with items, including their names, addresses, and identifiers. This can help in understanding the entities involved in the auction process."
  }
]
def ensure_table_metadata(table_views: list[str]):
    """Load column metadata for the given views and store it in session context if not already present."""
    context_table_meta = context.get("table_metadata", {})

    missing = [view for view in table_views if view not in context_table_meta]
    if not missing:
        return  # nothing to do

    results = get_table_views_metadata(missing)

    for result in results:
        if "view" in result and "columns" in result:
            context_table_meta[result["view"]] = [
                col["column_name"] for col in result["columns"] if "column_name" in col
            ]

    context.set("table_metadata", context_table_meta)


@mcp.tool()
def get_table_views_metadata(
    table_views: list[str],
    limit: int = 200
) -> list[dict[str, Any]]:
    """
    Return structured column metadata (column name, description, type, notes, examples) for one or more table views.
    Each result groups columns under its corresponding view name. Falls back to `SHOW COLUMNS` if metadata is missing.
    """
    allowed_views = ALLOWED_VIEWS
    output = []

    for view in table_views:
        if view not in allowed_views:
            output.append({"view": view, "error": f"Invalid table name: {view}"})
            continue

        qualified_view = f"main.prod_gold.{view}"

        try:
            query = """
                SELECT
                    column_name,
                    description,
                    data_type,
                    example_value
                FROM main.ai_data_assets.all_column_metadata
                WHERE source_table = ?
                GROUP BY column_name, description, data_type, example_value
                LIMIT ?
            """

            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, [view, limit])
                rows = cursor.fetchall()

            if rows:
                output.append({
                    "view": view,
                    "columns": [
                        {
                            "column_name": row[0],
                            "description": row[1],
                            "data_type": row[2],
                            "example_value": row[3],
                        }
                        for row in rows
                    ]
                })
            else:
                # fallback to SHOW COLUMNS
                with get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(f"SHOW COLUMNS IN {qualified_view}")
                    fallback_rows = cursor.fetchall()

                output.append({
                    "view": view,
                    "columns": [
                        {
                            "column_name": c[0],
                            "description": "N/A",
                            "data_type": c[1],
                            "example_value": None
                        }
                        for c in fallback_rows
                    ]
                })

        except Exception as e:
            output.append({
                "view": view,
                "error": f"Error fetching metadata: {e}"
            })
    context_table_meta = context.get("table_metadata", {})
    for result in output:
        if "view" in result and "columns" in result:
            context_table_meta[result["view"]] = [
                col["column_name"] for col in result["columns"] if "column_name" in col
            ]
    context.set("table_metadata", context_table_meta)

    return output


def extract_groupable_columns(select_columns: list[str]) -> list[str]:
    """
    Extracts columns that are not aggregate expressions for use in GROUP BY.
    Strips aliases and functions to return clean column references.
    """
    groupable = []
    aggregate_pattern = re.compile(r"\b(COUNT|SUM|AVG|MIN|MAX)\s*\(", re.IGNORECASE)
    alias_pattern = re.compile(r"(?i)\s+AS\s+\w+$")

    for col in select_columns:
        if not aggregate_pattern.search(col):
            col_clean = alias_pattern.sub("", col.strip())
            groupable.append(col_clean)
    return groupable


def extract_column_names(sql_expr: str) -> set[str]:
    try:
        tree = parse_one(sql_expr)
        return {
            c.sql(dialect='ansi').replace("`", "")
            for c in tree.find_all(Column)
        }
    except Exception:
        return set()

def is_valid_sql_column(col_expr: str, valid_columns: set[str], allowed_tables: list[str]) -> bool:
    cols = extract_column_names(col_expr)
    for col in cols:
        if "." in col:
            if not any(col.startswith(f"{tbl}.") for tbl in allowed_tables):
                return False
        elif col not in valid_columns:
            return False
    return True
def clean_where_clause(where: str) -> str:
    """Strip quotes around entire clause and remove escaping for quotes."""
    where = where.strip()
    if where.startswith(("'", '"')) and where.endswith(("'", '"')):
        where = where[1:-1]
    where = where.encode().decode('unicode_escape')  # unescape escaped quotes
    return where

def disambiguate_column(expr: str, preferred_table: str) -> str:
    """
    Disambiguate column references in SQL expressions by setting the preferred table for item_id.
    This is useful when item_id is used without a table prefix.
    """
    try:
        tree = parse_one(expr)
        for col in tree.find_all(Column):
            if col.name.upper() == "ITEM_ID" and col.table is None:
                col.set("this", "item_id")
                col.set("table", preferred_table)
        return tree.sql()
    except Exception:
        return expr  # fallback to original if parsing fails

@mcp.tool()
def query_single_view(
    table_name: str,
    columns: list[str] = ["*"],
    where_clause: str | None = None,
    group_by: list[str] | None = None,
    order_by: str | None = None,
    limit: int = 200
) -> str:
    """
    Query a single table view using filters, grouping, and aggregation logic. 
    Use this when a join is not required and the data resides in a single view.
    """
    if isinstance(group_by, str):
        try:
            group_by = json.loads(group_by)
        except Exception:
            group_by = [group_by]
    if isinstance(order_by, str):
        try:
            order_by = json.loads(order_by)
        except Exception:
            pass

    if table_name not in ALLOWED_VIEWS:
        return f"Invalid table name: {table_name}"

    full_table_name = f"main.prod_gold.{table_name}"
    ensure_table_metadata([table_name])
    valid_columns = set(context.get("table_metadata", {}).get(table_name, []))

    #valid_columns = get_valid_columns_for(full_table_name)

    if columns == ["*"]:
        columns = list(valid_columns)
    else:
        invalid = [col for col in columns if not is_valid_sql_column(col, valid_columns, [table_name])]
        if invalid:
            suggestions = [get_close_matches(col, valid_columns, n=3) for col in invalid]
            return f"Invalid columns: {invalid} — Suggestions: {suggestions}"

    if where_clause and any(kw in where_clause.lower() for kw in ["limit", "order by", "group by"]):
        return "Do not include LIMIT, ORDER BY, or GROUP BY in the where_clause. Use the respective parameters."

    try:
        col_str = ", ".join(columns)
        query = f"SELECT {col_str} FROM {full_table_name}"
        if where_clause:
            where_clause = clean_where_clause(where_clause)
            query += f" WHERE {where_clause}"

        has_aggregates = any(re.search(r"\b(COUNT|SUM|AVG|MIN|MAX)\s*\(", col, re.IGNORECASE) for col in columns)
        group_by_final = set(group_by or []) | (set(extract_groupable_columns(columns)) if has_aggregates else set())
        if has_aggregates and group_by_final:
            query += f" GROUP BY {', '.join(group_by_final)}"

        if order_by:
            query += f" ORDER BY {order_by}"
        query += f" LIMIT {limit}"

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            results = cursor.fetchall()

        context.add_query({
            "table_name": table_name,
            "columns": columns,
            "filters": extract_filters(where_clause),
            "sql": query,
        })

        return "\n".join(str(row) for row in results) if results else "No results found."

    except Exception as e:
        return f"Error querying {table_name}: {e}"


@mcp.tool()
def query_joined_views(
    select_columns: list[str],
    from_table: str,
    join_tables: list[str],
    where_clause: str | None = None,
    group_by: list[str] | None = None,
    order_by: str | None = None,
    limit: int = 200
) -> str:
    """Perform inner joins across multiple views using item_id as the join key. 
    Supports filtering, grouping, and selecting columns across views."""
    if isinstance(group_by, str):
        try:
            group_by = json.loads(group_by)
        except Exception:
            group_by = [group_by]
    if isinstance(order_by, str):
        try:
            order_by = json.loads(order_by)
        except Exception:
            pass

    if from_table not in ALLOWED_VIEWS:
        return f"Invalid base table: {from_table}"
    if any(tbl not in ALLOWED_VIEWS for tbl in join_tables):
        return f"One or more join tables are invalid."

    full_table_name = f"main.prod_gold.{from_table}"
    #valid_columns = get_valid_columns_for(full_table_name)
    ensure_table_metadata([from_table] + join_tables)
    context_table_meta = context.get("table_metadata", {})
    valid_columns = set()
    for view in [from_table] + join_tables:
        valid_columns.update(context_table_meta.get(view, []))

    invalid = [col for col in select_columns if not is_valid_sql_column(col, valid_columns, join_tables + [from_table])]

    if invalid:
        return f"Invalid select columns: {invalid}"

    try:
        select_columns = [disambiguate_column(col, from_table) for col in select_columns]
        select_str = ", ".join(select_columns)
        query = f"SELECT {select_str} FROM {full_table_name}"

        for join_table in join_tables:
            if join_table == from_table:
                continue
            query += f" INNER JOIN main.prod_gold.{join_table} ON {from_table}.item_id = {join_table}.item_id"

        if where_clause:
            where_clause = clean_where_clause(where_clause)
            query += f" WHERE {where_clause}"

        has_aggregates = any(re.search(r"\b(COUNT|SUM|AVG|MIN|MAX)\s*\(", col, re.IGNORECASE) for col in select_columns)
        group_by_final = set(group_by or []) | (set(extract_groupable_columns(select_columns)) if has_aggregates else set())
        if has_aggregates and group_by_final:
            query += f" GROUP BY {', '.join(group_by_final)}"

        if order_by:
            query += f" ORDER BY {order_by}"
        query += f" LIMIT {limit}"

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            results = cursor.fetchall()

        context.add_query({
            "tables": [from_table] + join_tables,
            "columns": select_columns,
            "filters": extract_filters(where_clause),
            "join": f"{from_table} + {join_tables}",
            "sql": query,
        })

        return "\n".join(str(row) for row in results) if results else "No results found."

    except Exception as e:
        return f"Error performing join: {e}"

@mcp.tool()
def list_table_relationships(source_table: str) -> list[dict[str, str]]:
    query = """
        SELECT source_table, foreign_key, primary_key_table, primary_key, relationship
        FROM main.ai_data_assets.key_relationships
        WHERE source_table = ?
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, [source_table])
        rows = cursor.fetchall()
    return [
        {
            "source_table": row[0],
            "foreign_key": row[1],
            "primary_key_table": row[2],
            "primary_key": row[3],
            "relationship": row[4]
        }
        for row in rows
    ]



@mcp.tool()
def fetch_recent_query_context(
    max_queries: int = 3
) -> dict[str, Any]:
    """
    Return the current session’s recent query context — including views, columns, filters, 
    joins, and SQLs — to help the assistant generate follow-up queries that build on prior interactions.
    """
    return context.get_relevant_context("default") | {
        "recent_queries": context.recent_queries[-max_queries:]
    }


@mcp.tool()
def list_available_tools() -> list[dict[str, Any]]:
    """List all available tools for querying and analyzing the dataset. Use this if you're unsure what tools are supported."""
    return [
        {
            "tool": name,
            "parameters": data["parameters"],
            "doc": data["doc"]
        }
        for name, data in registered_tools.items()
    ]

import sys

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "http":
        mcp.run(transport="http")
    else:
        mcp.run(transport="stdio")