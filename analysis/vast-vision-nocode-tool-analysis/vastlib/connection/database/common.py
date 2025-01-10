import re
import datetime
import time
from dateutil.relativedelta import relativedelta
import pytz
from tzlocal import get_localzone
import psycopg2
from psycopg2 import sql
import psycopg2.extras
import threading
import itertools

from logging import getLogger
logger = getLogger(__name__)


# Get DB Connection
def get_connection(db_info: dict, *, rdbms: str = 'postgresql'):
    # postgresql://{username}:{password}@{hostname}:{port}/{database}
    # dsn = '{}://{}:{}@{}:{}/{}'.format(rdbms, db_info['db_name'], db_info['user'],
    #                                    db_info['ip_address'], db_info['port'], db_info['password'])
    dsn = '{}://{}:{}@{}:{}/{}'.format(
        rdbms, db_info['user'],
        db_info['password'],
        db_info['ip_address'],
        db_info['port'],
        db_info['db_name']
    )
    return psycopg2.connect(dsn)


def query_filter(data: dict, *, flg_where=True):
    query = ""
    if data is not None:
        filter_arr = []
        for k, v in data.items():
            if v is None:
                filter_arr.append(
                    f"{k} is null"
                )
            else:
                if isinstance(v, list) or isinstance(v, tuple) or isinstance(v, dict):
                    _v = tuple(v)
                    filter_arr.append(
                        f"{k} in {_v}"
                    )
                else:
                    filter_arr.append(
                        f"{k} = {_v}"
                    )
        if filter_arr != []:
            if flg_where:
                query = f"WHERE {' AND '.join(filter_arr)}"
            else:
                query = f"AND {' AND '.join(filter_arr)}"
    return query


def get_data(db_info, query, various):
    with get_connection(db_info) as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql.SQL(query), various)
            rows = cur.fetchall()
    return rows


def commit_data(db_info, query, various):
    with get_connection(db_info) as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            try:
                if isinstance(various, list):
                    psycopg2.extras.execute_values(cur, query, various)
                    conn.commit()
                    res = {'code': 0, 'message': "SUCCESS"}
                else:
                    cur.execute(query, various)
                    conn.commit()
                    res = {'code': 0, 'message': "SUCCESS"}
            except Exception as e:
                logger.warning(e)
                conn.rollback()
                res = {'code': 20122, 'message': str(e)}
    return res












