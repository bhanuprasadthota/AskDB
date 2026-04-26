from __future__ import annotations

import sqlite3
from typing import Any, List, Optional, Tuple

from fuzzywuzzy import process
from transformers import T5ForConditionalGeneration, T5Tokenizer

_SUPPORTED_DBS = {"sqlite", "postgresql", "mysql", "mongodb"}
_DEFAULT_PORTS = {"postgresql": 5432, "mysql": 3306, "mongodb": 27017}


class AskDB:
    """Natural language to SQL query engine with multi-database support.

    Supports SQLite, PostgreSQL, MySQL, and MongoDB. Uses a fine-tuned T5
    model (ThotaBhanu/t5_sql_askdb) with schema-aware generation and fuzzy
    column matching to produce accurate SQL from plain English questions.

    Example:
        with AskDB("sqlite", "my_database.db") as db:
            results = db.ask("Find all employees with salary above 50000", "employees")
    """

    def __init__(
        self,
        db_type: str,
        database_name: str,
        host: str = "localhost",
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        uri: Optional[str] = None,
        model_name: str = "ThotaBhanu/t5_sql_askdb",
    ):
        """
        Args:
            db_type: One of 'sqlite', 'postgresql', 'mysql', 'mongodb'.
            database_name: Database name or SQLite file path.
            host: Database host (not used for SQLite).
            port: Database port. Defaults to the standard port for each DB type.
            username: Database username.
            password: Database password.
            uri: MongoDB connection URI (overrides host/port/credentials).
            model_name: HuggingFace model ID for SQL generation.
        """
        self.db_type = db_type.lower()
        if self.db_type not in _SUPPORTED_DBS:
            raise ValueError(
                f"Unsupported database type '{db_type}'. "
                f"Supported: {sorted(_SUPPORTED_DBS)}"
            )

        self.database_name = database_name
        self.host = host
        self.port = port or _DEFAULT_PORTS.get(self.db_type)
        self.username = username
        self.password = password
        self.uri = uri
        self.connection = None

        self._connect()
        self.tokenizer = T5Tokenizer.from_pretrained(model_name)
        self.model = T5ForConditionalGeneration.from_pretrained(model_name)

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------

    def _connect(self) -> None:
        try:
            if self.db_type == "sqlite":
                self.connection = sqlite3.connect(self.database_name)

            elif self.db_type == "postgresql":
                try:
                    import psycopg2
                except ImportError:
                    raise ImportError(
                        "psycopg2 is required for PostgreSQL. "
                        "Install with: pip install askdb[postgresql]"
                    )
                self.connection = psycopg2.connect(
                    host=self.host, port=self.port,
                    user=self.username, password=self.password,
                    dbname=self.database_name,
                )

            elif self.db_type == "mysql":
                try:
                    import pymysql
                except ImportError:
                    raise ImportError(
                        "pymysql is required for MySQL. "
                        "Install with: pip install askdb[mysql]"
                    )
                self.connection = pymysql.connect(
                    host=self.host, port=self.port,
                    user=self.username, password=self.password,
                    database=self.database_name,
                )

            elif self.db_type == "mongodb":
                try:
                    from pymongo import MongoClient
                except ImportError:
                    raise ImportError(
                        "pymongo is required for MongoDB. "
                        "Install with: pip install askdb[mongodb]"
                    )
                conn_str = self.uri or (
                    f"mongodb://{self.username}:{self.password}@{self.host}:{self.port}"
                )
                self.connection = MongoClient(conn_str)

        except (ImportError, ValueError):
            raise
        except Exception as exc:
            raise ConnectionError(
                f"Failed to connect to {self.db_type} '{self.database_name}': {exc}"
            ) from exc

    def close(self) -> None:
        """Close the database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None

    def __enter__(self) -> "AskDB":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    # ------------------------------------------------------------------
    # Schema introspection
    # ------------------------------------------------------------------

    def get_schema(self, table_name: str) -> List[Tuple[str, str]]:
        """Return the schema of a table as (column_name, data_type) tuples.

        Args:
            table_name: Name of the table to introspect.
        """
        if not self.connection:
            raise RuntimeError("No active database connection.")
        if self.db_type == "mongodb":
            raise NotImplementedError("Schema introspection is not supported for MongoDB.")

        cursor = self.connection.cursor()
        try:
            if self.db_type == "sqlite":
                cursor.execute(f"PRAGMA table_info({table_name})")
                return [(row[1], row[2]) for row in cursor.fetchall()]

            elif self.db_type == "postgresql":
                cursor.execute(
                    "SELECT column_name, data_type "
                    "FROM information_schema.columns WHERE table_name = %s",
                    (table_name,),
                )
                return cursor.fetchall()

            elif self.db_type == "mysql":
                cursor.execute(f"DESCRIBE {table_name}")
                return [(row[0], row[1]) for row in cursor.fetchall()]
        finally:
            cursor.close()

    def _match_columns(self, query: str, schema: List[Tuple[str, str]]) -> List[str]:
        """Fuzzy-match query words to column names (similarity threshold: 60)."""
        column_names = [col[0] for col in schema]
        matched: set = set()
        for word in query.lower().split():
            best, score = process.extractOne(word, column_names)
            if score > 60:
                matched.add(best)
        return list(matched)

    # ------------------------------------------------------------------
    # SQL generation
    # ------------------------------------------------------------------

    def generate_sql(self, question: str, table_name: str) -> str:
        """Convert a natural language question to a SQL query string.

        Retrieves the table schema, fuzzy-matches relevant columns, and
        feeds a structured prompt into the T5 model to generate SQL.

        Args:
            question: Plain English question (e.g. "Show users from New York").
            table_name: The target table name.

        Returns:
            Generated SQL query string.
        """
        schema = self.get_schema(table_name)
        schema_info = ", ".join(f"{col} ({dtype})" for col, dtype in schema)

        prompt = (
            f"Convert this natural language query into a SQL query:\n"
            f"User Query: {question}\n"
            f"Table Name: {table_name}\n"
            f"Available Columns: {schema_info}\n"
            f"Use only these columns in the SQL query."
        )

        input_ids = self.tokenizer(prompt, return_tensors="pt").input_ids
        output = self.model.generate(
            input_ids,
            max_new_tokens=128,
            num_beams=4,
            early_stopping=True,
        )
        sql = self.tokenizer.decode(output[0], skip_special_tokens=True)

        # Strip structured output artifacts occasionally produced by T5 models
        for marker in ("'human_readable':", "', 'sel'", "'sel'"):
            if marker in sql:
                idx = 1 if marker == "'human_readable':" else 0
                sql = sql.split(marker)[idx].strip(" '\"{},\n")

        return sql

    # ------------------------------------------------------------------
    # Query execution
    # ------------------------------------------------------------------

    def execute(self, sql: str) -> List[Any]:
        """Execute a raw SQL string and return all results.

        Args:
            sql: Valid SQL query string.
        """
        if not self.connection:
            raise RuntimeError("No active database connection.")
        cursor = self.connection.cursor()
        try:
            cursor.execute(sql)
            return cursor.fetchall()
        finally:
            cursor.close()

    def ask(self, question: str, table_name: str) -> List[Any]:
        """Translate a natural language question to SQL and execute it.

        This is the primary interface for AskDB — combines generate_sql()
        and execute() in a single call.

        Args:
            question: Plain English question about the data.
            table_name: The table to query against.

        Returns:
            List of rows returned by the generated SQL query.

        Example:
            results = db.ask("Show all users who signed up this year", "users")
        """
        sql = self.generate_sql(question, table_name)
        return self.execute(sql)
