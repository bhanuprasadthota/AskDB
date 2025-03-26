import psycopg2  # PostgreSQL
import pymysql  # MySQL
import sqlite3  # SQLite
from pymongo import MongoClient  # MongoDB
from transformers import T5Tokenizer, T5ForConditionalGeneration
from fuzzywuzzy import fuzz, process  # Fuzzy matching for column names


class AskDB:
    def __init__(self, db_type, database_name, host="localhost", port=None, username=None, password=None, collection_name=None, uri=None):
        """
        Initializes the AskDB class to support multiple database types.

        Supported Databases: PostgreSQL, MySQL, SQLite, MongoDB.
        """
        self.db_type = db_type.lower()
        self.database_name = database_name
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.collection_name = collection_name
        self.uri = uri  # Only for MongoDB
        self.connection = None  # Placeholder for the connection object

        # ✅ Automatically set default ports for known databases
        self.set_default_ports()

        # ✅ Establish connection
        self.connect()

        # ✅ Load fine-tuned T5 Model
        self.tokenizer = T5Tokenizer.from_pretrained("ThotaBhanu/t5_sql_askdb")
        self.model = T5ForConditionalGeneration.from_pretrained("ThotaBhanu/t5_sql_askdb")

    def set_default_ports(self):
        """Assigns default ports based on the database type."""
        if self.db_type == "postgresql":
            self.port = self.port or 5432
        elif self.db_type == "mysql":
            self.port = self.port or 3306
        elif self.db_type == "mongodb":
            self.port = self.port or 27017
        elif self.db_type == "sqlite":
            self.host = None  # SQLite doesn't use host/port
            self.port = None
            self.username = None
            self.password = None

    def connect(self):
        """Creates a connection to the specified database."""
        try:
            if self.db_type == "postgresql":
                self.connection = psycopg2.connect(
                    host=self.host,
                    port=self.port,
                    user=self.username,
                    password=self.password,
                    dbname=self.database_name
                )
            elif self.db_type == "mysql":
                self.connection = pymysql.connect(
                    host=self.host,
                    port=self.port,
                    user=self.username,
                    password=self.password,
                    database=self.database_name
                )
            elif self.db_type == "mongodb":
                self.connection = MongoClient(self.uri or f"mongodb://{self.username}:{self.password}@{self.host}:{self.port}")
                print(f"✅ Connected to MongoDB database: {self.database_name}")
                return  # MongoDB does not use a cursor like SQL-based DBs
            elif self.db_type == "sqlite":
                self.connection = sqlite3.connect(self.database_name)  # Just the file path
            else:
                raise ValueError(f"❌ Unsupported database type: {self.db_type}")

            print(f"✅ Connected to {self.db_type} database: {self.database_name}")

        except Exception as e:
            print(f"❌ Connection failed: {str(e)}")

    def get_schema(self, table_name):
        """Retrieves the table schema from the database."""
        if not self.connection:
            print("❌ Error: No active database connection.")
            return None

        try:
            cursor = self.connection.cursor()

            if self.db_type == "sqlite":
                cursor.execute(f"PRAGMA table_info({table_name})")  # ✅ SQLite Schema Query
                schema = [(row[1], row[2]) for row in cursor.fetchall()]  # (column_name, data_type)
            elif self.db_type == "postgresql":
                cursor.execute(f"""
                    SELECT column_name, data_type
                    FROM information_schema.columns
                    WHERE table_name = '{table_name}'
                """)
                schema = cursor.fetchall()
            elif self.db_type == "mysql":
                cursor.execute(f"DESCRIBE {table_name}")
                schema = [(row[0], row[1]) for row in cursor.fetchall()]
            else:
                print("❌ Schema fetching is not supported for MongoDB.")
                return None

            cursor.close()
            print(f"✅ Retrieved schema for `{table_name}`: {schema}")
            return schema

        except Exception as e:
            print(f"❌ Error retrieving schema: {str(e)}")
            return None

    def match_columns(self, user_query, table_name):
        """Matches user query words with table column names using fuzzy matching."""
        schema = self.get_schema(table_name)
        if not schema:
            return None
    
        column_names = [col[0] for col in schema]  # Extract column names
    
        matched_columns = set()  # Use a set to prevent duplicates
        query_words = user_query.lower().split()  # Convert query to lowercase for better matching
    
        for word in query_words:
            best_match, score = process.extractOne(word, column_names)
            if score > 60:  # Acceptable fuzzy matching threshold
                matched_columns.add(best_match)  # Use set to ensure unique column matches
    
        matched_columns = list(matched_columns)  # Convert set back to list
    
        print(f"🔍 Matched Columns: {matched_columns}")
        return matched_columns


    def generate_sql(self, user_query, table_name):
        """
        Generates an SQL query from a natural language query.
        """
        if not self.connection:
            print("❌ Error: No active database connection.")
            return None
    
        # 🔍 Retrieve schema
        schema = self.get_schema(table_name)
        if not schema:
            print("❌ Failed to retrieve schema.")
            return None
    
        print(f"✅ Retrieved schema for `{table_name}`: {schema}")
    
        # 🔍 Match columns
        matched_columns = self.match_columns(user_query, table_name)
        print(f"🔍 Matched Columns: {matched_columns}")
    
        if not matched_columns:
            print("❌ No relevant columns matched. SQL generation may be inaccurate.")
        
        # ✅ Explicitly format column names to prevent misinterpretation
        schema_info = ", ".join([f"{col[0]} ({col[1]})" for col in schema])  # Include column names + types
        matched_info = ", ".join(matched_columns) if matched_columns else schema_info  # Use best-matched columns
    
        # ✅ Construct a strict schema-aware prompt
        prompt = (
            f"Convert this natural language query into a SQL query:\n"
            f"User Query: {user_query}\n"
            f"Table Name: {table_name}\n"
            f"Available Columns: {schema_info}\n"
            f"Use only these columns in the SQL query."
        )
    
        # 🔍 Debugging: Print the final prompt being sent to the model
        print(f"🚀 **Final Prompt:** {prompt}")
    
        # 🔥 Generate SQL
        input_ids = self.tokenizer(prompt, return_tensors="pt").input_ids
        output = self.model.generate(input_ids, max_new_tokens=50)
        generated_sql = self.tokenizer.decode(output[0], skip_special_tokens=True)
    
        # 🔍 Print SQL before execution
        print(f"🛠 **Generated SQL:** {generated_sql}")
    
        return generated_sql




    def close_connection(self):
        """Closes the database connection."""
        if self.connection:
            self.connection.close()
            print("🔌 Database connection closed.")


# --------------------- ✅ Usage Example ---------------------

# ✅ 1️⃣ SQLite Example (Testing)
askdb_sqlite = AskDB(
    db_type="SQLite",
    database_name="/Users/bhanuprasadthota/Downloads/example_db.sqlite"
)

# ✅ 2️⃣ Run SQL Generation
user_query = "Find all employees who joined in 2020"
print(askdb_sqlite.generate_sql(user_query, table_name="employees"))

# ✅ Close Connection
askdb_sqlite.close_connection()

