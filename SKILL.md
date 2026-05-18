---
name: sql-lineage-analysis
description: Analyze SQL table lineage and column-level lineage from one SQL statement, multiple SQL statements, dbt models, ETL scripts, views, INSERT/CREATE AS SELECT/MERGE queries, CTE-heavy SQL, or stored SQL files, then produce a Markdown lineage document with relationship tables and Mermaid lineage diagrams. Use when the user asks for SQL血缘分析, 数据血缘, 字段血缘, 表血缘, 血缘图, 上游/下游关系, impact analysis, source-to-target mapping, column mapping, SQL解析, or wants to know which source tables and columns produce each output table or column. Prefer this skill even when the user only provides raw SQL and says "帮我看这个SQL".
---

# SQL Lineage Analysis

Analyze SQL as a static lineage artifact: identify target datasets, upstream datasets, column mappings, transformations, filters, joins, aggregations, and confidence limits. Produce a Markdown document containing both tabular lineage details and graphical lineage diagrams. Be explicit about what is derived from AST parsing versus human inference.

## Workflow

1. Capture the SQL exactly as provided. If the SQL is in a file, read the file; if there are multiple files or dbt models, analyze them in dependency order when obvious.
2. Identify dialect hints from the prompt, file names, syntax, or project context. Common dialects include `bigquery`, `snowflake`, `spark`, `databricks`, `hive`, `postgres`, `mysql`, `tsql`, and `oracle`. If unknown, use `sqlglot` default parsing and state the uncertainty.
3. Run `scripts/sql_lineage.py` when Python is available. Use it for structured AST-derived evidence:

   ```bash
   python3 <skill-dir>/scripts/sql_lineage.py --sql-file query.sql --dialect spark
   ```

   For inline SQL, write the SQL to a temporary file outside the skill folder and pass `--sql-file`.
4. Read `references/output-format.md` before producing the final answer. Follow its report structure.
5. Manually review the SQL after the script. The script is a helper, not the source of truth. Correct obvious parser misses, especially around dialect-specific functions, macros, dynamic SQL, CTE reuse, `SELECT *`, window functions, and ambiguous unqualified columns.
6. Create a Markdown file for the final report, unless the user explicitly asks for inline output only. Use a clear filename such as `sql-lineage-report.md` or `<target-table>-lineage.md`.
7. Output the lineage report in Chinese unless the user asks for another language. In the chat response, provide the Markdown file path and a short summary.

## Analysis Rules

- Separate table-level lineage from column-level lineage.
- Treat CTEs, subqueries, temp views, and intermediate aliases as internal nodes. Show both the simplified source-to-target lineage and the detailed path through intermediate nodes when useful.
- For `CREATE TABLE AS SELECT`, `CREATE VIEW`, `INSERT INTO`, `INSERT OVERWRITE`, and `MERGE`, infer the target table. For plain `SELECT`, use `RESULT_SET` as the target.
- For each output column, identify:
  - direct source columns
  - transformation expression
  - aggregation or window logic
  - join/filter dependencies that affect row inclusion but do not directly produce the value
  - confidence level: high, medium, low
- Do not invent schemas. If `SELECT *` or unqualified columns require schema knowledge that is absent, mark the lineage as incomplete and explain what schema metadata is needed.
- Include parser errors and assumptions in the final report instead of hiding them.
- Include Mermaid diagrams in the Markdown document:
  - table-level lineage graph
  - column-level lineage graph
  - optional CTE/intermediate-node graph when it improves clarity
- Keep Mermaid node IDs ASCII-safe. Put readable table/column names in labels.

## Resource Guide

- `scripts/sql_lineage.py`: AST-based helper for extracting target tables, source tables, CTEs, joins, filters, and best-effort column lineage. Prefer running it before manual analysis.
- `references/output-format.md`: Required Markdown report structure, Mermaid graph guidance, and confidence rules.
