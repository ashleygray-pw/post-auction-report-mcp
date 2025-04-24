from typing import Any
from mcp.server.fastmcp import FastMCP
import databricks.sql
import os
from dotenv import load_dotenv
from difflib import get_close_matches
from functools import lru_cache
import inspect

load_dotenv()
mcp = FastMCP("databricks")

# Load credentials
server_hostname = os.getenv("DATABRICKS_HOST")
http_path = os.getenv("DATABRICKS_HTTP_PATH")
access_token = os.getenv("DATABRICKS_TOKEN")

if not all([server_hostname, http_path, access_token]):
    raise EnvironmentError("❌ Missing Databricks credentials in environment variables.")

def get_connection():
    return databricks.sql.connect(
        server_hostname=server_hostname,
        http_path=http_path,
        access_token=access_token,
    )
# ✅ Guardrail
ALLOWED_VIEWS = {
    "item_details", "item_buyer_info", "item_sale_status",
    "item_tracking_dates_durations", "item_location", "item_financials",
    "item_auction_details", "item_opportunity_info", "item_capture_and_content",
    "item_seller_info", "item_bidding_and_engagement"
}
@lru_cache
def get_allowed_views() -> set[str]:
    query = """
        SELECT DISTINCT EXPLODE(table_view) AS full_view_name
        FROM main.ai_data_assets.item_views_column_metadata
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
        FROM main.ai_data_assets.item_views_column_metadata
        WHERE array_contains(table_view, ?)
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, [table_name])
        return {row[0] for row in cursor.fetchall()}
    
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
    "view": "item_details",
    "description": "Identifying and descriptive information for each item, including identifiers (item_id, ims_item_id, item_icn), make/model details, VIN, and classification taxonomy (industry, family, category).",
    "usage": "Use to classify or filter items by physical or categorical attributes. Ideal for public listings or analytic segmentations."
  },
  {
    "view": "item_sale_status",
    "description": "Current and historical sale status flags for each item, such as whether it's published, sold, closed, or halted. Includes time-on-market (days_online).",
    "usage": "Use to understand item lifecycle status (sold, active, removed). Useful for forecasting and lifecycle analytics."
  },
  {
    "view": "item_tracking_dates_durations",
    "description": "Lifecycle and operational timestamps, including pickup dates, title receipt/distribution, and timing metrics between creation and publication.",
    "usage": "Use for timeline analysis of operational processes, bottleneck detection, and time-to-market metrics."
  },
  {
    "view": "item_location",
    "description": "Geospatial and organizational information about item location: full address, coordinates, region/district/territory, and associated TM/DD names.",
    "usage": "Use for mapping, routing, or geographic analysis of inventory and personnel assignment."
  },
  {
    "view": "item_auction_details",
    "description": "Auction-related metadata for the item including auction ID, workspace, title, end time, fiscal year/quarter, and category.",
    "usage": "Use when filtering by auction event or analyzing auction cadence and timing by fiscal period."
  },
  {
    "view": "item_financials",
    "description": "All financial outcomes and fee structures for the item. Includes hammer price, contract price, fees, taxes, invoice and settlement IDs and dates.",
    "usage": "Use to evaluate profitability, fees collected, and for computing metrics like average lot value (via `safe_for_avg_lot_value_calc`)."
  },
  {
    "view": "item_bidding_and_engagement",
    "description": "Bidding metrics (e.g., count of bids, bidders) and user interaction data (views, watchlist adds, video views).",
    "usage": "Use for interest modeling, bid competitiveness analysis, and marketing performance reviews."
  },
  {
    "view": "item_buyer_info",
    "description": "Comprehensive buyer details including location, contact info, segment codes, buyer join date, and distance from item.",
    "usage": "Use for buyer demographic analysis, CRM segmentation, and assessing geographic reach of auctions."
  },
  {
    "view": "item_seller_info",
    "description": "Seller’s company data, geographic info, engagement metadata, and classification tags. Includes sales team assignment.",
    "usage": "Use to evaluate seller behavior, territory performance, and account management insights."
  },
  {
    "view": "item_opportunity_info",
    "description": "CRM opportunity metadata linked to the item. Includes pipeline status, segment, region, and sales rep assignment.",
    "usage": "Use to assess funnel quality, territory productivity, and CRM pipeline coverage."
  },
  {
    "view": "item_capture_and_content",
    "description": "Data capture and content generation details, including form creator, image/video/doc counts, and submission dates.",
    "usage": "Use to analyze listing completeness, FOS contributions, and content lifecycle timing."
  }
]

@mcp.tool()
def get_table_views_metadata(
     table_views: list[str], 
     limit: int = 200) -> list[dict[str, Any]]:
    """
    Return column names and descriptions for one or more table views, defined in list_available_views(),
    from `main.ai_data_assets.item_views_column_metadata`. Includes fallback.
    """
    allowed_views = ALLOWED_VIEWS
    for table_name in table_views:
        if table_name not in allowed_views:
            return [f"❌ Invalid table name: {table_name}"]

    qualified_views = [f"main.ai_data_assets.{v}" for v in table_views]

    try:
        placeholders = ', '.join(['?'] * len(qualified_views))
        query = f"""
            SELECT
                column_name,
                description,
                data_type,
                llm_notes,
                example_value
            FROM (
                SELECT
                    column_name,
                    description,
                    data_type,
                    llm_notes,
                    example_value,
                    EXPLODE(table_view) AS tv
                FROM main.ai_data_assets.item_views_column_metadata
            ) exploded
            WHERE tv IN ({placeholders})
            GROUP BY column_name, description, data_type, llm_notes, example_value
            LIMIT ?
        """

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, qualified_views + [limit])
            results = cursor.fetchall()

        if results:
            return [
                {
                    "column_name": row[0] if len(row) > 0 else None,
                    "description": row[1] if len(row) > 1 else None,
                    "data_type": row[2] if len(row) > 2 else None,
                    "llm_notes": row[3] if len(row) > 3 else None,
                    "example_value": row[4] if len(row) > 4 else None,
                }
                for row in results
            ]
        else:
            fallback_table = table_views[0]
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"SHOW COLUMNS IN main.ai_data_assets.{fallback_table}")
                cols = cursor.fetchall()
            return [
                {
                    "column_name": c[0],
                    "description": "N/A",
                    "data_type": c[1],
                    "llm_notes": None,
                    "example_value": None
                } for c in cols
            ]

    except Exception as e:
        return [{"error": f"Error fetching metadata: {e}"}]

@mcp.tool()
def query_table(
    table_name: str,
    columns: list[str],
    where_clause: str | None = None,
    limit: int = 50
) -> str:
    """
    Query any single allowed table with optional WHERE clause.
    Columns must be explicitly named. Use get_valid_columns_for to validate before call.
    """
    if table_name not in ALLOWED_VIEWS:
        return f"❌ Invalid table name: {table_name}"
    full_table_name = f"main.ai_data_assets.{table_name}"
    valid_columns = get_valid_columns_for(full_table_name)

    if columns == ["*"]:
        columns = list(valid_columns)
    else:
        invalid = [col for col in columns if col not in valid_columns]
        if invalid:
            suggestions = [get_close_matches(col, valid_columns, n=3) for col in invalid]
            return f"❌ Invalid columns: {invalid} — Suggestions: {suggestions}"

    try:
        col_str = ", ".join(columns)
        query = f"SELECT {col_str} FROM main.ai_data_assets.{table_name}"
        if where_clause:
            query += f" WHERE {where_clause}"
        query += f" LIMIT {limit}"

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            results = cursor.fetchall()

        return "\n".join(str(row) for row in results) if results else "No results found."

    except Exception as e:
        return f"❌ Error querying {table_name}: {e}"

@mcp.tool()
def join_views_on_item_id(
    select_columns: list[str],
    from_table: str,
    join_tables: list[str],
    where_clause: str | None = None
) -> str:
    """
    Join allowed item views on item_id and return selected columns.
    """
    allowed_views = ALLOWED_VIEWS
    if from_table not in allowed_views:
        return f"❌ Invalid base table: {from_table}"
    if any(tbl not in allowed_views for tbl in join_tables):
        return f"❌ One or more join tables are invalid."

    try:
        select_str = ", ".join(select_columns)
        query = f"SELECT {select_str} FROM main.ai_data_assets.{from_table}"

        for join_table in join_tables:
            if join_table == from_table:
                continue
            query += f" INNER JOIN main.ai_data_assets.{join_table} ON {from_table}.item_id = {join_table}.item_id"

        if where_clause:
            query += f" WHERE {where_clause}"

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            results = cursor.fetchall()

        return "\n".join(str(row) for row in results) if results else "No results found."

    except Exception as e:
        return f"❌ Error performing join: {e}"

@mcp.tool()
def list_available_tools() -> list[dict[str, Any]]:
    return [
        {
            "tool": name,
            "parameters": data["parameters"],
            "doc": data["doc"]
        }
        for name, data in registered_tools.items()
    ]

if __name__ == "__main__":
    mcp.run(transport="stdio")