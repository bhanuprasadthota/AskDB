# AskDB

**Convert plain English questions into SQL — no SQL knowledge required.**

AskDB is an open-source Python library that lets developers query any database using natural language. Powered by a fine-tuned T5 model ([ThotaBhanu/t5_sql_askdb](https://huggingface.co/ThotaBhanu/t5_sql_askdb)) with schema-aware generation and fuzzy column matching for accurate, context-aware SQL output.

```python
from askdb import AskDB

with AskDB("sqlite", "company.db") as db:
    results = db.ask("Show all employees with salary above 50000", "employees")
    print(results)
```

---

## Features

- **Natural language to SQL** — ask questions in plain English, get query results back
- **Multi-database support** — SQLite, PostgreSQL, MySQL, MongoDB
- **Schema-aware generation** — reads your table schema to produce accurate SQL
- **Fuzzy column matching** — handles typos and informal column references
- **Fine-tuned model** — uses a custom T5 model trained specifically for text-to-SQL
- **Context manager support** — clean connection handling with `with` statements

---

## Installation

**Core (SQLite support included):**
```bash
pip install askdb
```

**With PostgreSQL:**
```bash
pip install askdb[postgresql]
```

**With MySQL:**
```bash
pip install askdb[mysql]
```

**With MongoDB:**
```bash
pip install askdb[mongodb]
```

**All database drivers:**
```bash
pip install askdb[all]
```

---

## Quick Start

### SQLite
```python
from askdb import AskDB

with AskDB("sqlite", "my_database.db") as db:
    # Generate SQL without executing
    sql = db.generate_sql("Find all orders placed in January", "orders")
    print(sql)  # SELECT * FROM orders WHERE ...

    # Generate SQL and execute in one call
    results = db.ask("Show top 10 customers by total spend", "customers")
    print(results)
```

### PostgreSQL
```python
from askdb import AskDB

db = AskDB(
    db_type="postgresql",
    database_name="my_db",
    host="localhost",
    username="postgres",
    password="secret",
)

results = db.ask("List all products with less than 5 units in stock", "products")
db.close()
```

### MySQL
```python
from askdb import AskDB

with AskDB(
    db_type="mysql",
    database_name="ecommerce",
    host="localhost",
    username="root",
    password="secret",
) as db:
    results = db.ask("Which users have not logged in for 30 days?", "users")
```

### Execute raw SQL
```python
with AskDB("sqlite", "data.db") as db:
    results = db.execute("SELECT COUNT(*) FROM employees WHERE department = 'Engineering'")
```

---

## API Reference

### `AskDB(db_type, database_name, ...)`

| Parameter | Type | Description |
|-----------|------|-------------|
| `db_type` | `str` | One of `'sqlite'`, `'postgresql'`, `'mysql'`, `'mongodb'` |
| `database_name` | `str` | Database name or SQLite file path |
| `host` | `str` | Database host (default: `'localhost'`) |
| `port` | `int` | Port number (defaults: PostgreSQL=5432, MySQL=3306, MongoDB=27017) |
| `username` | `str` | Database username |
| `password` | `str` | Database password |
| `uri` | `str` | MongoDB connection URI (overrides host/port/credentials) |
| `model_name` | `str` | HuggingFace model ID (default: `ThotaBhanu/t5_sql_askdb`) |

### Methods

| Method | Description |
|--------|-------------|
| `ask(question, table_name)` | Translate question to SQL and execute — returns query results |
| `generate_sql(question, table_name)` | Translate question to SQL string without executing |
| `execute(sql)` | Execute a raw SQL string and return results |
| `get_schema(table_name)` | Return table schema as `[(column_name, data_type), ...]` |
| `close()` | Close the database connection |

---

## How It Works

1. **Schema retrieval** — AskDB reads your table's column names and data types directly from the database
2. **Fuzzy column matching** — query keywords are matched to column names using fuzzy string similarity (threshold: 60%), so informal references still resolve correctly
3. **Prompt construction** — a structured prompt combining the question, table name, and schema is sent to the T5 model
4. **SQL generation** — the fine-tuned T5 model ([ThotaBhanu/t5_sql_askdb](https://huggingface.co/ThotaBhanu/t5_sql_askdb)) generates a SQL query grounded in the actual schema
5. **Execution** — the generated SQL is executed against your database and results are returned

---

## Supported Databases

| Database | Support | Extra Install |
|----------|---------|---------------|
| SQLite | Built-in | None |
| PostgreSQL | Full | `pip install askdb[postgresql]` |
| MySQL | Full | `pip install askdb[mysql]` |
| MongoDB | Connection only | `pip install askdb[mongodb]` |

---

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes and open a Pull Request

---

## License

MIT License — see [LICENSE](LICENSE) for details.
