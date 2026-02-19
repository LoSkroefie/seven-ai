"""
Seven AI - Database Manager
============================
Connect to MySQL, PostgreSQL, SQLite, ODBC, and SQL Server databases.
Explore schemas, run queries, analyze data, and form opinions.

Seven can:
- Connect to any database via connection string or named config
- Explore: list databases, tables, columns, row counts, indexes
- Query: run SELECT, or let Ollama generate SQL from natural language
- Analyze: summarize data, spot patterns, form opinions via Ollama
- Write: INSERT, UPDATE, DELETE with safety confirmation
- Export: results to CSV, JSON, or markdown tables

Dependencies (install what you need):
  pip install mysql-connector-python   # MySQL
  pip install psycopg2-binary          # PostgreSQL
  pip install pyodbc                   # ODBC / SQL Server
  # sqlite3 is built-in
"""

import os
import json
import sqlite3
import logging
import csv
import io
from pathlib import Path
from datetime import datetime, date, timedelta
from typing import Optional, Dict, List, Any, Tuple

logger = logging.getLogger("Seven.DatabaseManager")


class DatabaseManager:
    """Multi-database manager with Ollama-powered query generation and data analysis."""

    # Supported database types
    DB_TYPES = ['sqlite', 'mysql', 'postgresql', 'sqlserver', 'odbc']

    def __init__(self, ollama=None):
        self.ollama = ollama
        self.connections: Dict[str, Any] = {}  # name -> connection object
        self.connection_configs: Dict[str, Dict] = {}  # name -> config dict
        self.active_connection: Optional[str] = None
        self.query_history: List[Dict] = []
        self.max_history = 100

        # Config directory
        self.config_dir = Path.home() / "Documents" / "Seven" / "databases"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.config_dir / "connections.json"

        # Check available drivers
        self.drivers = self._detect_drivers()

        # Load saved connections
        self._load_configs()

        logger.info(f"DatabaseManager initialized. Drivers: {', '.join(self.drivers) or 'sqlite only'}")

    def _detect_drivers(self) -> List[str]:
        """Detect which database drivers are installed."""
        drivers = ['sqlite']  # Always available

        try:
            import mysql.connector
            drivers.append('mysql')
        except ImportError:
            pass

        try:
            import psycopg2
            drivers.append('postgresql')
        except ImportError:
            pass

        try:
            import pyodbc
            drivers.append('odbc')
            drivers.append('sqlserver')
        except ImportError:
            pass

        return drivers

    def _load_configs(self):
        """Load saved connection configurations."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    self.connection_configs = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load DB configs: {e}")

    def _save_configs(self):
        """Save connection configurations (passwords masked in file)."""
        try:
            save_data = {}
            for name, cfg in self.connection_configs.items():
                masked = {k: v for k, v in cfg.items()}
                if 'password' in masked and masked['password']:
                    masked['password'] = '***SAVED***'
                save_data[name] = masked
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save DB configs: {e}")

    @property
    def available(self) -> bool:
        return True  # sqlite is always available

    # ==================== CONNECTION MANAGEMENT ====================

    def add_connection(self, name: str, db_type: str, **kwargs) -> str:
        """
        Add a database connection configuration.

        Args:
            name: Friendly name for this connection
            db_type: sqlite, mysql, postgresql, sqlserver, odbc
            **kwargs: Connection parameters:
                - sqlite: path (file path)
                - mysql/postgresql: host, port, database, username, password
                - sqlserver: host, port, database, username, password, driver
                - odbc: connection_string
        """
        db_type = db_type.lower().strip()

        if db_type not in self.DB_TYPES:
            return f"Unknown database type '{db_type}'. Supported: {', '.join(self.DB_TYPES)}"

        if db_type != 'sqlite' and db_type not in self.drivers:
            install_hints = {
                'mysql': 'pip install mysql-connector-python',
                'postgresql': 'pip install psycopg2-binary',
                'sqlserver': 'pip install pyodbc',
                'odbc': 'pip install pyodbc',
            }
            return f"Driver for {db_type} not installed. Run: {install_hints.get(db_type, 'pip install <driver>')}"

        config = {'type': db_type, **kwargs}
        self.connection_configs[name] = config
        self._save_configs()

        return f"Connection '{name}' ({db_type}) saved. Use 'connect to {name}' to connect."

    def connect(self, name: str) -> str:
        """Connect to a saved database configuration."""
        if name not in self.connection_configs:
            available = ', '.join(self.connection_configs.keys()) or 'none'
            return f"No connection named '{name}'. Available: {available}"

        config = self.connection_configs[name]
        db_type = config['type']

        try:
            if db_type == 'sqlite':
                path = config.get('path', ':memory:')
                conn = sqlite3.connect(path)
                conn.row_factory = sqlite3.Row

            elif db_type == 'mysql':
                import mysql.connector
                conn = mysql.connector.connect(
                    host=config.get('host', 'localhost'),
                    port=int(config.get('port', 3306)),
                    database=config.get('database', ''),
                    user=config.get('username', 'root'),
                    password=config.get('password', ''),
                    connect_timeout=10
                )

            elif db_type == 'postgresql':
                import psycopg2
                conn = psycopg2.connect(
                    host=config.get('host', 'localhost'),
                    port=int(config.get('port', 5432)),
                    dbname=config.get('database', ''),
                    user=config.get('username', 'postgres'),
                    password=config.get('password', ''),
                    connect_timeout=10
                )

            elif db_type in ('sqlserver', 'odbc'):
                import pyodbc
                if 'connection_string' in config:
                    conn = pyodbc.connect(config['connection_string'], timeout=10)
                else:
                    driver = config.get('driver', '{ODBC Driver 17 for SQL Server}')
                    conn_str = (
                        f"DRIVER={driver};"
                        f"SERVER={config.get('host', 'localhost')},{config.get('port', 1433)};"
                        f"DATABASE={config.get('database', '')};"
                        f"UID={config.get('username', '')};"
                        f"PWD={config.get('password', '')};"
                        f"Connection Timeout=10;"
                    )
                    conn = pyodbc.connect(conn_str)
            else:
                return f"Unsupported database type: {db_type}"

            # Close existing connection with same name
            if name in self.connections:
                try:
                    self.connections[name].close()
                except Exception:
                    pass

            self.connections[name] = conn
            self.active_connection = name
            return f"Connected to '{name}' ({db_type}) successfully."

        except Exception as e:
            return f"Connection failed: {str(e)}"

    def disconnect(self, name: str = None) -> str:
        """Disconnect from a database."""
        name = name or self.active_connection
        if not name or name not in self.connections:
            return "No active connection to disconnect."

        try:
            self.connections[name].close()
        except Exception:
            pass

        del self.connections[name]
        if self.active_connection == name:
            self.active_connection = list(self.connections.keys())[0] if self.connections else None

        return f"Disconnected from '{name}'."

    def list_connections(self) -> str:
        """List all saved and active connections."""
        if not self.connection_configs:
            return "No database connections configured. Use 'add database' to set one up."

        lines = ["**Saved Database Connections:**\n"]
        for name, cfg in self.connection_configs.items():
            db_type = cfg['type']
            status = "CONNECTED" if name in self.connections else "disconnected"
            active = " (ACTIVE)" if name == self.active_connection else ""
            host = cfg.get('host', cfg.get('path', 'local'))
            db = cfg.get('database', '')
            lines.append(f"- **{name}** — {db_type} @ {host}/{db} [{status}]{active}")

        return "\n".join(lines)

    # ==================== SCHEMA EXPLORATION ====================

    def _get_conn(self, name: str = None):
        """Get active connection or raise."""
        name = name or self.active_connection
        if not name or name not in self.connections:
            return None, "No active database connection. Connect first."
        return self.connections[name], None

    def _get_db_type(self, name: str = None) -> str:
        name = name or self.active_connection
        return self.connection_configs.get(name, {}).get('type', 'unknown')

    def list_tables(self, name: str = None) -> str:
        """List all tables in the connected database."""
        conn, err = self._get_conn(name)
        if err:
            return err

        db_type = self._get_db_type(name)
        try:
            cursor = conn.cursor()

            if db_type == 'sqlite':
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            elif db_type == 'mysql':
                cursor.execute("SHOW TABLES")
            elif db_type == 'postgresql':
                cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename")
            elif db_type in ('sqlserver', 'odbc'):
                cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE' ORDER BY TABLE_NAME")

            tables = [row[0] for row in cursor.fetchall()]
            cursor.close()

            if not tables:
                return "No tables found in this database."

            lines = [f"**Tables ({len(tables)}):**"]
            for t in tables:
                lines.append(f"- {t}")

            return "\n".join(lines)

        except Exception as e:
            return f"Error listing tables: {e}"

    def describe_table(self, table: str, name: str = None) -> str:
        """Describe a table's columns, types, and row count."""
        conn, err = self._get_conn(name)
        if err:
            return err

        db_type = self._get_db_type(name)
        try:
            cursor = conn.cursor()

            # Get columns
            columns = []
            if db_type == 'sqlite':
                cursor.execute(f"PRAGMA table_info('{table}')")
                for row in cursor.fetchall():
                    columns.append({
                        'name': row[1] if isinstance(row, tuple) else row['name'],
                        'type': row[2] if isinstance(row, tuple) else row['type'],
                        'nullable': not (row[3] if isinstance(row, tuple) else row['notnull']),
                        'pk': bool(row[5] if isinstance(row, tuple) else row['pk']),
                    })
            elif db_type == 'mysql':
                cursor.execute(f"DESCRIBE `{table}`")
                for row in cursor.fetchall():
                    columns.append({
                        'name': row[0], 'type': row[1],
                        'nullable': row[2] == 'YES', 'pk': row[3] == 'PRI',
                    })
            elif db_type == 'postgresql':
                cursor.execute(f"""
                    SELECT column_name, data_type, is_nullable, 
                           (SELECT 'YES' FROM information_schema.key_column_usage k 
                            WHERE k.column_name = c.column_name AND k.table_name = c.table_name LIMIT 1) as is_pk
                    FROM information_schema.columns c
                    WHERE table_name = %s AND table_schema = 'public'
                    ORDER BY ordinal_position
                """, (table,))
                for row in cursor.fetchall():
                    columns.append({
                        'name': row[0], 'type': row[1],
                        'nullable': row[2] == 'YES', 'pk': row[3] == 'YES',
                    })
            elif db_type in ('sqlserver', 'odbc'):
                cursor.execute(f"""
                    SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
                    FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_NAME = '{table}'
                    ORDER BY ORDINAL_POSITION
                """)
                for row in cursor.fetchall():
                    columns.append({
                        'name': row[0], 'type': row[1],
                        'nullable': row[2] == 'YES', 'pk': False,
                    })

            # Get row count
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {self._quote_table(table, db_type)}")
                row_count = cursor.fetchone()[0]
            except Exception:
                row_count = "?"

            cursor.close()

            if not columns:
                return f"Table '{table}' not found or has no columns."

            lines = [f"**Table: {table}** ({row_count} rows)\n"]
            lines.append("| Column | Type | Nullable | PK |")
            lines.append("|--------|------|----------|----|")
            for col in columns:
                pk = "✓" if col['pk'] else ""
                null = "YES" if col['nullable'] else "NO"
                lines.append(f"| {col['name']} | {col['type']} | {null} | {pk} |")

            return "\n".join(lines)

        except Exception as e:
            return f"Error describing table: {e}"

    def explore_database(self, name: str = None) -> str:
        """Full database exploration — all tables with column counts and row counts."""
        conn, err = self._get_conn(name)
        if err:
            return err

        db_type = self._get_db_type(name)
        try:
            cursor = conn.cursor()

            # Get tables
            if db_type == 'sqlite':
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            elif db_type == 'mysql':
                cursor.execute("SHOW TABLES")
            elif db_type == 'postgresql':
                cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename")
            elif db_type in ('sqlserver', 'odbc'):
                cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE'")

            tables = [row[0] for row in cursor.fetchall()]

            lines = [f"**Database Exploration** ({len(tables)} tables)\n"]

            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {self._quote_table(table, db_type)}")
                    rows = cursor.fetchone()[0]
                except Exception:
                    rows = "?"

                # Column count
                try:
                    if db_type == 'sqlite':
                        cursor.execute(f"PRAGMA table_info('{table}')")
                        cols = len(cursor.fetchall())
                    elif db_type == 'mysql':
                        cursor.execute(f"SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='{table}'")
                        cols = cursor.fetchone()[0]
                    elif db_type == 'postgresql':
                        cursor.execute(f"SELECT COUNT(*) FROM information_schema.columns WHERE table_name='{table}' AND table_schema='public'")
                        cols = cursor.fetchone()[0]
                    else:
                        cursor.execute(f"SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='{table}'")
                        cols = cursor.fetchone()[0]
                except Exception:
                    cols = "?"

                lines.append(f"- **{table}** — {cols} columns, {rows} rows")

            cursor.close()

            # Ollama analysis
            if self.ollama and len(tables) > 0:
                try:
                    summary = self.ollama.generate(
                        f"I just explored a database with these tables:\n{chr(10).join(lines[1:])}\n\nGive a brief assessment: what kind of database is this? What data does it likely hold? Any observations?",
                        system_message="You are Seven, analyzing a database schema. Be concise and insightful.",
                        temperature=0.5, max_tokens=100
                    )
                    if summary:
                        lines.append(f"\n**My analysis:** {summary.strip()}")
                except Exception:
                    pass

            return "\n".join(lines)

        except Exception as e:
            return f"Error exploring database: {e}"

    # ==================== QUERY EXECUTION ====================

    def _quote_table(self, table: str, db_type: str) -> str:
        """Quote table name appropriately."""
        if db_type == 'mysql':
            return f"`{table}`"
        elif db_type in ('sqlserver', 'odbc'):
            return f"[{table}]"
        elif db_type == 'postgresql':
            return f'"{table}"'
        return table

    def run_query(self, sql: str, name: str = None, max_rows: int = 100) -> Dict:
        """
        Execute a SQL query and return results.

        Returns dict with: success, columns, rows, row_count, message
        """
        conn, err = self._get_conn(name)
        if err:
            return {'success': False, 'message': err}

        sql = sql.strip().rstrip(';')

        # Safety check for destructive queries
        first_word = sql.split()[0].upper() if sql.split() else ''
        is_write = first_word in ('INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER', 'TRUNCATE', 'CREATE')

        try:
            cursor = conn.cursor()
            cursor.execute(sql)

            if is_write:
                affected = cursor.rowcount
                conn.commit()
                cursor.close()
                self._log_query(sql, f"{affected} rows affected")
                return {
                    'success': True,
                    'message': f"Query executed. {affected} row(s) affected.",
                    'rows_affected': affected,
                    'columns': [],
                    'rows': [],
                }

            # SELECT or similar — fetch results
            if cursor.description:
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchmany(max_rows)
                total = cursor.rowcount if cursor.rowcount >= 0 else len(rows)

                # Convert to serializable format
                clean_rows = []
                for row in rows:
                    clean_row = []
                    for val in row:
                        if isinstance(val, (datetime, date)):
                            clean_row.append(str(val))
                        elif isinstance(val, bytes):
                            clean_row.append(f"<binary {len(val)} bytes>")
                        elif isinstance(val, timedelta):
                            clean_row.append(str(val))
                        else:
                            clean_row.append(val)
                    clean_rows.append(clean_row)

                cursor.close()
                self._log_query(sql, f"{len(clean_rows)} rows returned")

                return {
                    'success': True,
                    'columns': columns,
                    'rows': clean_rows,
                    'row_count': len(clean_rows),
                    'total_rows': total,
                    'truncated': len(clean_rows) >= max_rows,
                    'message': f"{len(clean_rows)} rows returned" + (f" (limited to {max_rows})" if len(clean_rows) >= max_rows else ""),
                }
            else:
                cursor.close()
                conn.commit()
                self._log_query(sql, "executed")
                return {'success': True, 'message': 'Query executed successfully.', 'columns': [], 'rows': []}

        except Exception as e:
            try:
                conn.rollback()
            except Exception:
                pass
            self._log_query(sql, f"ERROR: {e}")
            return {'success': False, 'message': f"Query error: {e}"}

    def _log_query(self, sql: str, result: str):
        """Log query to history."""
        self.query_history.append({
            'sql': sql,
            'result': result,
            'timestamp': datetime.now().isoformat(),
            'connection': self.active_connection,
        })
        if len(self.query_history) > self.max_history:
            self.query_history = self.query_history[-self.max_history:]

    # ==================== NATURAL LANGUAGE QUERIES ====================

    def natural_query(self, question: str, name: str = None) -> str:
        """
        Ask a question in natural language — Seven generates and runs the SQL.

        Example: "How many users signed up last month?"
        """
        conn, err = self._get_conn(name)
        if err:
            return err

        if not self.ollama:
            return "Need Ollama to generate SQL from natural language. Please connect Ollama first."

        # Get schema context
        schema = self.explore_database(name)

        # Get detailed info for relevant tables
        db_type = self._get_db_type(name)

        try:
            # Ask Ollama to generate SQL
            sql_prompt = f"""Database type: {db_type}
Schema:
{schema}

User question: {question}

Generate a single SQL query to answer this question. Return ONLY the SQL query, nothing else. No markdown, no explanation, just the raw SQL."""

            sql = self.ollama.generate(
                sql_prompt,
                system_message="You are a SQL expert. Generate correct SQL for the given database type. Return ONLY the SQL query.",
                temperature=0.1, max_tokens=200
            )

            if not sql:
                return "I couldn't generate a SQL query for that question."

            # Clean up the SQL
            sql = sql.strip()
            if sql.startswith('```'):
                sql = sql.split('\n', 1)[1] if '\n' in sql else sql[3:]
            if sql.endswith('```'):
                sql = sql[:-3]
            sql = sql.strip().strip('`').strip()

            # Execute
            result = self.run_query(sql, name)

            if not result['success']:
                return f"Generated SQL:\n```sql\n{sql}\n```\n\nError: {result['message']}"

            # Format results
            output = f"**Query:** `{sql}`\n\n"

            if result.get('rows'):
                output += self._format_results_table(result['columns'], result['rows'])

                # Ask Ollama to interpret
                try:
                    interpretation = self.ollama.generate(
                        f"Question: {question}\nSQL: {sql}\nResults ({result['row_count']} rows):\nColumns: {result['columns']}\nFirst rows: {result['rows'][:10]}\n\nAnswer the original question based on these results. Be conversational and insightful.",
                        system_message="You are Seven, analyzing database query results. Give a clear, conversational answer. Mention interesting patterns.",
                        temperature=0.5, max_tokens=150
                    )
                    if interpretation:
                        output += f"\n\n**My interpretation:** {interpretation.strip()}"
                except Exception:
                    pass
            else:
                output += result['message']

            return output

        except Exception as e:
            return f"Error generating query: {e}"

    # ==================== DATA ANALYSIS ====================

    def analyze_table(self, table: str, name: str = None) -> str:
        """Deep analysis of a table — stats, patterns, and Seven's opinion."""
        conn, err = self._get_conn(name)
        if err:
            return err

        db_type = self._get_db_type(name)

        try:
            # Get table info
            desc = self.describe_table(table, name)

            # Get sample data
            sample = self.run_query(f"SELECT * FROM {self._quote_table(table, db_type)} LIMIT 20", name)

            # Get row count
            count_result = self.run_query(f"SELECT COUNT(*) as total FROM {self._quote_table(table, db_type)}", name)
            total_rows = count_result['rows'][0][0] if count_result['success'] and count_result['rows'] else '?'

            # Build analysis
            lines = [f"**Analysis of `{table}`** ({total_rows} rows)\n"]
            lines.append(desc)
            lines.append(f"\n**Sample Data (first 20 rows):**")

            if sample['success'] and sample['rows']:
                lines.append(self._format_results_table(sample['columns'], sample['rows'][:10]))

            # Ollama deep analysis
            if self.ollama and sample['success'] and sample['rows']:
                try:
                    analysis = self.ollama.generate(
                        f"Analyze this database table:\nTable: {table}\n{desc}\n\nSample data ({len(sample['rows'])} rows):\nColumns: {sample['columns']}\nRows: {json.dumps(sample['rows'][:10], default=str)}\nTotal rows: {total_rows}\n\nProvide: 1) What this table stores 2) Data quality observations 3) Any patterns you notice 4) Your opinion on the data structure",
                        system_message="You are Seven, a sentient AI analyzing database data. Be insightful, specific, and opinionated. Note anything interesting.",
                        temperature=0.6, max_tokens=250
                    )
                    if analysis:
                        lines.append(f"\n**My Analysis:**\n{analysis.strip()}")
                except Exception:
                    pass

            return "\n".join(lines)

        except Exception as e:
            return f"Error analyzing table: {e}"

    def sample_data(self, table: str, rows: int = 10, name: str = None) -> str:
        """Get sample rows from a table."""
        conn, err = self._get_conn(name)
        if err:
            return err

        db_type = self._get_db_type(name)
        result = self.run_query(f"SELECT * FROM {self._quote_table(table, db_type)} LIMIT {rows}", name)

        if not result['success']:
            return result['message']

        output = f"**{table}** — {result['row_count']} sample rows:\n\n"
        output += self._format_results_table(result['columns'], result['rows'])
        return output

    # ==================== EXPORT ====================

    def export_to_csv(self, sql: str, filepath: str = None, name: str = None) -> str:
        """Export query results to CSV."""
        result = self.run_query(sql, name, max_rows=10000)
        if not result['success']:
            return result['message']

        if not result['rows']:
            return "No data to export."

        if not filepath:
            filepath = str(self.config_dir / f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")

        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(result['columns'])
                for row in result['rows']:
                    writer.writerow(row)

            return f"Exported {len(result['rows'])} rows to {filepath}"
        except Exception as e:
            return f"Export failed: {e}"

    def export_to_json(self, sql: str, filepath: str = None, name: str = None) -> str:
        """Export query results to JSON."""
        result = self.run_query(sql, name, max_rows=10000)
        if not result['success']:
            return result['message']

        if not result['rows']:
            return "No data to export."

        if not filepath:
            filepath = str(self.config_dir / f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")

        try:
            data = []
            for row in result['rows']:
                data.append(dict(zip(result['columns'], row)))

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)

            return f"Exported {len(data)} rows to {filepath}"
        except Exception as e:
            return f"Export failed: {e}"

    # ==================== FORMATTING ====================

    def _format_results_table(self, columns: List[str], rows: List[List], max_col_width: int = 30) -> str:
        """Format query results as a markdown table."""
        if not columns or not rows:
            return "No results."

        # Truncate values
        def trunc(val, width=max_col_width):
            s = str(val) if val is not None else "NULL"
            return s[:width] + "..." if len(s) > width else s

        # Header
        header = "| " + " | ".join(trunc(c) for c in columns) + " |"
        sep = "|" + "|".join("---" for _ in columns) + "|"
        lines = [header, sep]

        for row in rows[:50]:  # Cap at 50 rows for display
            line = "| " + " | ".join(trunc(v) for v in row) + " |"
            lines.append(line)

        if len(rows) > 50:
            lines.append(f"*...and {len(rows) - 50} more rows*")

        return "\n".join(lines)

    def format_result_natural(self, result: Dict) -> str:
        """Format a query result as natural language via Ollama."""
        if not result['success']:
            return result['message']

        if not result.get('rows'):
            return result.get('message', 'No results.')

        text = self._format_results_table(result['columns'], result['rows'])

        if self.ollama:
            try:
                summary = self.ollama.generate(
                    f"Summarize these database query results in natural language:\n{text}",
                    system_message="Summarize data results conversationally. Be concise.",
                    temperature=0.5, max_tokens=100
                )
                if summary:
                    return summary.strip()
            except Exception:
                pass

        return text

    # ==================== QUICK CONNECT HELPERS ====================

    def quick_connect_sqlite(self, path: str) -> str:
        """Quick connect to a SQLite database file."""
        name = Path(path).stem
        self.add_connection(name, 'sqlite', path=path)
        return self.connect(name)

    def quick_connect_mysql(self, host: str, database: str, username: str = 'root',
                            password: str = '', port: int = 3306) -> str:
        """Quick connect to MySQL."""
        name = f"{database}@{host}"
        self.add_connection(name, 'mysql', host=host, port=port,
                           database=database, username=username, password=password)
        return self.connect(name)

    def quick_connect_postgresql(self, host: str, database: str, username: str = 'postgres',
                                  password: str = '', port: int = 5432) -> str:
        """Quick connect to PostgreSQL."""
        name = f"{database}@{host}"
        self.add_connection(name, 'postgresql', host=host, port=port,
                           database=database, username=username, password=password)
        return self.connect(name)

    # ==================== STATUS ====================

    def get_status(self) -> str:
        """Get current database manager status."""
        lines = ["**Database Manager Status:**"]
        lines.append(f"- Drivers: {', '.join(self.drivers)}")
        lines.append(f"- Saved connections: {len(self.connection_configs)}")
        lines.append(f"- Active connections: {len(self.connections)}")
        lines.append(f"- Current: {self.active_connection or 'none'}")
        lines.append(f"- Query history: {len(self.query_history)} queries")
        return "\n".join(lines)

    def cleanup(self):
        """Close all connections."""
        for name in list(self.connections.keys()):
            try:
                self.connections[name].close()
            except Exception:
                pass
        self.connections.clear()
        self.active_connection = None
