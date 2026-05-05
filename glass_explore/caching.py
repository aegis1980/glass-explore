#(c)2026 Jon Robinson. All Rights Reserved.

import os
from uuid import uuid4
from dash import CeleryManager, DiskcacheManager
import diskcache
from glass_explore import CACHE_PATH,DF_GLASS_TABLE, PARQUET_GLASS_PATH

# 1. Use an absolute path for the cache
# If on Railway, this should ideally be in your /igdb volume to persist
os.makedirs(CACHE_PATH, exist_ok=True)

# 2. Initialise a single diskcache instance
cache = diskcache.Cache(CACHE_PATH)


def _glass_table_cache_token():
    stat = os.stat(PARQUET_GLASS_PATH)
    return f"{stat.st_mtime_ns}_{stat.st_size}"

def background_callback_manager():
    launch_uid = uuid4()
    if 'REDIS_URL' in os.environ:
        from celery import Celery
        celery_app = Celery(__name__, broker=os.environ['REDIS_URL'], backend=os.environ['REDIS_URL'])
        return CeleryManager(celery_app, cache_by=[lambda: launch_uid], expire=60)
    else:
        return DiskcacheManager(cache, cache_by=[lambda: launch_uid], expire=120)


def thickness_cached_df(thickness):
    cache_key = f"thickness_{_glass_table_cache_token()}_{thickness}"
    result = cache.get(cache_key)
    if result is None:
        result = DF_GLASS_TABLE[DF_GLASS_TABLE['Thickness'].between(thickness - 0.95, thickness + 0.95)]
        cache.set(cache_key, result, expire=3600) # Cache for 1 hour
    return result

