# SQL Lineage Analysis：SQL 血缘分析 Skill

## 解决什么问题

复杂 SQL 里的表关系和字段来源经常藏在 CTE、子查询、JOIN、聚合、窗口函数和 `INSERT/CREATE TABLE AS SELECT` 语句里。人工排查时很容易漏掉字段转换、过滤条件、目标表和中间节点，尤其是做数据治理、影响分析、字段口径排查时。

SQL Lineage Analysis 用于分析 SQL 的表级血缘和字段级血缘。它会结合 `sqlglot` AST 解析和 Agent 的人工校验，识别目标表、上游表、字段来源、转换逻辑、JOIN/FILTER 影响条件、CTE 中间节点，并输出带 Mermaid 图形的 Markdown 血缘文档。

适合场景：
- SQL 血缘分析、字段血缘分析、表血缘分析
- 数据治理、元数据梳理、影响分析
- 分析 dbt model、ETL SQL、视图 SQL、离线数仓任务 SQL
- 排查某个目标字段由哪些源表字段加工而来
- 生成可沉淀到数据治理文档里的血缘说明

## Agent 如何使用

**触发方式：**

在 Codex 中输入 `/sql-lineage-analysis` 激活，或在对话中自然触发（当用户提到"SQL血缘分析"、"字段血缘"、"表血缘"、"血缘图"、"上游/下游关系"、"impact analysis"、"source-to-target mapping" 等表述时自动触发）。

**使用示例：**

```text
/sql-lineage-analysis 分析这段 SQL，输出 Markdown 文档，并包含表和字段血缘图：

create table mart.user_orders as
select u.id as user_id, u.name, count(o.id) as order_cnt
from ods.users u
left join ods.orders o on u.id = o.user_id
where u.status = 'active'
group by u.id, u.name;
```

```text
帮我分析 models/user_payment.sql 的表级和字段级血缘，输出 md 文档
```

```text
这个 SQL 影响哪些下游字段？请给我血缘关系和 Mermaid 图
```

**处理流程：**

1. Agent 读取 SQL 原文或 SQL 文件，判断 SQL 方言（Spark、BigQuery、Snowflake、Hive、Postgres 等）
2. 优先运行 `scripts/sql_lineage.py`，用 `sqlglot` 解析目标表、上游表、字段表达式、CTE、JOIN 和过滤条件
3. Agent 人工复核 AST 结果，补充脚本难以完全判断的内容，如 `SELECT *`、动态 SQL、宏、未限定字段、窗口函数和复杂表达式
4. 按 `references/output-format.md` 的结构生成 Markdown 文档
5. 在 Markdown 中输出表格血缘和 Mermaid 图形血缘

## 输出什么结果

输出一个 `.md` Markdown 文档，而不是只在聊天里给简短结论。

**文档内容包括：**

- 摘要：目标对象、上游对象、主要处理逻辑、分析完整性
- 表级血缘关系表：目标表、上游表、关系类型、关键逻辑、置信度
- 表级血缘图：Mermaid `flowchart LR`
- 字段级血缘关系表：目标字段、来源字段、转换逻辑、影响条件、置信度
- 字段级血缘图：Mermaid `flowchart LR`
- 中间节点：CTE、子查询、临时视图、别名
- 关键处理逻辑：JOIN、WHERE、GROUP BY、窗口函数、CASE、MERGE 等
- 不确定性说明：缺失 schema、`SELECT *`、动态 SQL、宏、解析失败等

**输出特征：**

- 同时覆盖表级和字段级血缘
- 不只列来源字段，还说明转换逻辑和过滤影响
- 用 Mermaid 图形展示血缘路径，便于放进文档或治理平台说明
- 明确标注置信度，不强行编造缺失 schema 下无法确认的字段
- 对 CTE 和中间节点保留路径，方便排查复杂 SQL

---

## 安装

```bash
npx skills add https://github.com/Peng-666/sql-lineage-analysis.git
```

或手动复制整个 `sql-lineage-analysis` 目录到 `~/.codex/skills/sql-lineage-analysis/`。
