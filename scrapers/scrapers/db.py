"""Database connection and helpers for scrapers — HTTP API."""
import os
import json
import httpx
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.environ["TURSO_DATABASE_URL"].replace("libsql://", "https://")
DB_TOKEN = os.environ["TURSO_AUTH_TOKEN"]

_client = None  # type: httpx.Client | None

def get_client() -> httpx.Client:
    global _client
    if _client is None:
        _client = httpx.Client(
            base_url=DB_URL,
            headers={"Authorization": f"Bearer {DB_TOKEN}"},
            timeout=30,
        )
    return _client

def _pipeline(requests: list[dict]) -> list[dict]:
    """Send a batch of requests via Turso HTTP pipeline API."""
    resp = get_client().post("/v2/pipeline", json={"requests": requests})
    resp.raise_for_status()
    data = resp.json()
    results = []
    for r in data.get("results", []):
        if r["type"] == "ok":
            results.append(r["response"])
        elif r["type"] == "error":
            raise Exception(f"Turso error: {r['error']}")
    return results

def execute(sql: str, params=None):
    """Execute a SQL statement (INSERT/UPDATE/DELETE)."""
    args = []
    if params:
        for p in params:
            if p is None:
                args.append({"type": "null"})
            elif isinstance(p, int):
                args.append({"type": "integer", "value": str(p)})
            elif isinstance(p, float):
                args.append({"type": "float", "value": p})
            else:
                args.append({"type": "text", "value": str(p)})

    result = _pipeline([{
        "type": "execute",
        "stmt": {"sql": sql, "args": args} if args else {"sql": sql},
    }])
    return result[0]["result"]

def batch_execute(statements: list[tuple[str, list]]):
    """Execute multiple SQL statements in a transaction."""
    requests = []
    for sql, params in statements:
        args = []
        if params:
            for p in params:
                if p is None:
                    args.append({"type": "null"})
                elif isinstance(p, int):
                    args.append({"type": "integer", "value": str(p)})
                elif isinstance(p, float):
                    args.append({"type": "float", "value": p})
                else:
                    args.append({"type": "text", "value": str(p)})
        requests.append({
            "type": "execute",
            "stmt": {"sql": sql, "args": args} if args else {"sql": sql},
        })
    results = _pipeline(requests)
    return [r["result"] for r in results]

def query(sql: str, params=None):
    """Run a SELECT query and return rows as dicts."""
    args = []
    if params:
        for p in params:
            if p is None:
                args.append({"type": "null"})
            elif isinstance(p, int):
                args.append({"type": "integer", "value": str(p)})
            elif isinstance(p, float):
                args.append({"type": "float", "value": p})
            else:
                args.append({"type": "text", "value": str(p)})

    result = _pipeline([{
        "type": "execute",
        "stmt": {"sql": sql, "args": args} if args else {"sql": sql},
    }])
    exec_result = result[0]["result"]
    columns = [col["name"] for col in exec_result.get("cols", [])]
    rows = []
    for row in exec_result.get("rows", []):
        values = []
        for cell in row:
            val = cell.get("value")
            # Convert numeric strings to actual numbers
            if cell.get("type") in ("integer",):
                try:
                    val = int(val)
                except (TypeError, ValueError):
                    pass
            elif cell.get("type") in ("float",):
                try:
                    val = float(val)
                except (TypeError, ValueError):
                    pass
            values.append(val)
        rows.append(dict(zip(columns, values)))
    return rows
