import pandas as pd
from sqlalchemy import text

def muat_pengecualian(engine):
    with engine.connect() as conn:
        return pd.read_sql_query(text("SELECT kode_diagnosis, kode_tindakan, keterangan FROM pengecualian_layanan"), conn)