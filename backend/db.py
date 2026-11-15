import os

from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

# dict rows + FastAPI's encoder (Decimal -> float/int, date -> ISO string) means
# routes can return query rows directly.
pool = ConnectionPool(conninfo=os.environ["DATABASE_URL"], open=True, kwargs={"row_factory": dict_row})
