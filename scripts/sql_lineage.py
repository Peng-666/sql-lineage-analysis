#!/usr/bin/env python3
"""Best-effort SQL lineage extraction using sqlglot.

This script intentionally returns evidence for an agent to review, not a final
authoritative lineage report.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any


def _load_sqlglot():
    try:
        import sqlglot
        from sqlglot import exp
    except ImportError:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": "Missing dependency: sqlglot. Install with `python3 -m pip install sqlglot` or perform manual SQL lineage analysis.",
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        sys.exit(2)
    return sqlglot, exp


def expression_sql(node: Any, dialect: str | None) -> str:
    try:
        return node.sql(dialect=dialect) if dialect else node.sql()
    except Exception:
        return str(node)


def table_name(table: Any) -> str:
    parts = [p for p in [getattr(table, "catalog", None), getattr(table, "db", None), getattr(table, "name", None)] if p]
    return ".".join(parts) if parts else str(table)


def target_from_expression(tree: Any, exp: Any, dialect: str | None) -> dict[str, Any]:
    target = None
    operation = tree.key

    if isinstance(tree, exp.Create):
        target = expression_sql(tree.this, dialect)
        operation = "create"
    elif isinstance(tree, exp.Insert):
        target = expression_sql(tree.this, dialect)
        operation = "insert"
    elif isinstance(tree, exp.Merge):
        target = expression_sql(tree.this, dialect)
        operation = "merge"
    elif isinstance(tree, exp.Update):
        target = expression_sql(tree.this, dialect)
        operation = "update"
    elif isinstance(tree, exp.Delete):
        target = expression_sql(tree.this, dialect)
        operation = "delete"

    return {"target": target or "RESULT_SET", "operation": operation}


def extract_select_outputs(tree: Any, exp: Any, dialect: str | None) -> list[dict[str, Any]]:
    outputs: list[dict[str, Any]] = []
    select = tree.find(exp.Select)
    if not select:
        return outputs

    for index, projection in enumerate(select.expressions, start=1):
        alias = projection.alias_or_name or f"_col_{index}"
        columns = sorted(
            {
                expression_sql(col, dialect)
                for col in projection.find_all(exp.Column)
            }
        )
        outputs.append(
            {
                "target_column": alias,
                "expression": expression_sql(projection, dialect),
                "source_columns": columns,
                "has_star": bool(list(projection.find_all(exp.Star))),
            }
        )
    return outputs


def analyze_statement(tree: Any, exp: Any, dialect: str | None) -> dict[str, Any]:
    target = target_from_expression(tree, exp, dialect)
    tables = []
    ctes = []
    joins = []
    filters = []

    for table in tree.find_all(exp.Table):
        tables.append(
            {
                "name": table_name(table),
                "alias": table.alias,
                "sql": expression_sql(table, dialect),
            }
        )

    for cte in tree.find_all(exp.CTE):
        ctes.append(
            {
                "name": cte.alias_or_name,
                "sql": expression_sql(cte, dialect),
                "source_tables": sorted({table_name(t) for t in cte.find_all(exp.Table)}),
            }
        )

    for join in tree.find_all(exp.Join):
        joins.append(
            {
                "kind": join.args.get("kind") or "JOIN",
                "table": expression_sql(join.this, dialect) if join.this else None,
                "on": expression_sql(join.args["on"], dialect) if join.args.get("on") else None,
            }
        )

    for where in tree.find_all(exp.Where):
        filters.append({"type": "where", "condition": expression_sql(where.this, dialect)})
    for having in tree.find_all(exp.Having):
        filters.append({"type": "having", "condition": expression_sql(having.this, dialect)})

    cte_names = {cte["name"] for cte in ctes}
    target_name = target["target"]
    source_tables = sorted(
        {
            t["name"]
            for t in tables
            if t["name"] not in cte_names and t["name"] != target_name
        }
    )

    return {
        **target,
        "source_tables": source_tables,
        "all_table_references": tables,
        "ctes": ctes,
        "joins": joins,
        "filters": filters,
        "output_columns": extract_select_outputs(tree, exp, dialect),
        "statement_sql": expression_sql(tree, dialect),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract best-effort SQL lineage as JSON.")
    parser.add_argument("--sql-file", required=True, help="Path to a file containing SQL.")
    parser.add_argument("--dialect", default=None, help="Optional sqlglot dialect, e.g. spark, bigquery, snowflake.")
    args = parser.parse_args()

    sqlglot, exp = _load_sqlglot()

    with open(args.sql_file, "r", encoding="utf-8") as f:
        sql = f.read()

    try:
        statements = sqlglot.parse(sql, read=args.dialect)
    except Exception as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": f"Parse failed: {exc}",
                    "dialect": args.dialect,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1

    result = {
        "ok": True,
        "dialect": args.dialect,
        "statement_count": len(statements),
        "statements": [analyze_statement(stmt, exp, args.dialect) for stmt in statements if stmt],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
