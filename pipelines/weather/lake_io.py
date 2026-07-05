"""Generic Delta Lake writer shared by the weather and air-quality ingests.

Idempotent per (area, date-range): re-running a range overwrites those rows
rather than duplicating. Local by default; delta-rs writes S3 natively when the
table path is s3:// and AWS_* creds are in the env.
"""
import pandas as pd
import pyarrow as pa
from deltalake import DeltaTable, write_deltalake

from config import PARTITION_BY


def _exists(path):
    try:
        DeltaTable(path)
        return True
    except Exception:
        return False


def write_partitioned(df, table_path, numeric_cols):
    """df must carry area_id, year, date columns. numeric_cols are coerced to
    float so the parquet schema stays stable even if a source omitted a field."""
    if df is None or df.empty:
        return 0
    df = df.reset_index(drop=True)
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors="coerce")
    # preserve_index=False avoids the stray __index_level_0__ column.
    table = pa.Table.from_pandas(df, preserve_index=False)

    if _exists(table_path):
        dt = DeltaTable(table_path)
        for aid, g in df.groupby("area_id"):
            dmin, dmax = g["date"].min(), g["date"].max()
            dt.delete(f"area_id = '{aid}' AND date >= '{dmin}' AND date <= '{dmax}'")
        write_deltalake(table_path, table, mode="append")
    else:
        write_deltalake(table_path, table, mode="append", partition_by=PARTITION_BY)
    return len(df)
