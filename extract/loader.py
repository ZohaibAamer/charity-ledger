import duckdb
import polars as pl

from extract.config import DUCKDB_PATH


def get_connection() -> duckdb.DuckDBPyConnection:
    DUCKDB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(DUCKDB_PATH))


def load_to_bronze(df: pl.DataFrame, table_name: str, mode: str = "replace") -> int:
    """Load a Polars DataFrame into a bronze table in DuckDB.

    Returns the number of rows loaded.
    """
    con = get_connection()
    schema = "bronze"
    con.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
    con.register("df_view", df)

    full_table = f"{schema}.{table_name}"

    if mode == "replace":
        con.execute(f"DROP TABLE IF EXISTS {full_table}")
        con.execute(
            f"CREATE TABLE {full_table} AS SELECT * FROM df_view"
        )
    elif mode == "append":
        try:
            con.execute(f"INSERT INTO {full_table} SELECT * FROM df_view")
        except duckdb.CatalogException:
            con.execute(
                f"CREATE TABLE {full_table} AS SELECT * FROM df_view"
            )

    count = con.execute(f"SELECT count(*) FROM {full_table}").fetchone()[0]
    con.close()
    return count


def read_watermark(source_name: str) -> str | None:
    """Read the last-loaded watermark for incremental loads."""
    con = get_connection()
    con.execute("CREATE SCHEMA IF NOT EXISTS meta")
    con.execute(
        "CREATE TABLE IF NOT EXISTS meta.watermarks "
        "(source_name VARCHAR PRIMARY KEY, watermark VARCHAR, updated_at TIMESTAMP DEFAULT current_timestamp)"
    )
    row = con.execute(
        "SELECT watermark FROM meta.watermarks WHERE source_name = ?",
        [source_name],
    ).fetchone()
    con.close()
    return row[0] if row else None


def write_watermark(source_name: str, watermark: str) -> None:
    con = get_connection()
    con.execute("CREATE SCHEMA IF NOT EXISTS meta")
    con.execute(
        "CREATE TABLE IF NOT EXISTS meta.watermarks "
        "(source_name VARCHAR PRIMARY KEY, watermark VARCHAR, updated_at TIMESTAMP DEFAULT current_timestamp)"
    )
    con.execute(
        "INSERT OR REPLACE INTO meta.watermarks (source_name, watermark, updated_at) "
        "VALUES (?, ?, current_timestamp)",
        [source_name, watermark],
    )
    con.close()
