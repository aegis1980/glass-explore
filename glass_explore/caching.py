#(c)2026 Jon Robinson. All Rights Reserved.

import os
from uuid import uuid4

from dash import CeleryManager, DiskcacheManager
from data_cache import pandas_cache

from glass_explore import DF_GLASS_TABLE,DF_READABLE_GLASS_TABLE

# You should change 'test' to your preferred folder.
CACHE_DIR = os.path.join('cache')

# If cache folder doesn't exist, then create it.
if not os.path.isdir(CACHE_DIR):
    os.makedirs(CACHE_DIR)

# Set CACHE_PATH env var for pandas_cache
os.environ['CACHE_PATH'] = os.path.join('cache','pandas_cache')


def background_callback_manager():
    """
    Refer 
    """
    launch_uid = uuid4()

    if 'REDIS_URL' in os.environ:
        # Use Redis & Celery if REDIS_URL set as an env variable
        from celery import Celery
        celery_app = Celery(__name__, broker=os.environ['REDIS_URL'], backend=os.environ['REDIS_URL'])
        background_callback_manager = CeleryManager(
            celery_app, cache_by=[lambda: launch_uid], expire=60
        )

    else:
        # Diskcache for non-production apps when developing locally
        import diskcache
        cache = diskcache.Cache("./cache")
        background_callback_manager = DiskcacheManager(
            cache, cache_by=[lambda: launch_uid], expire=120
        )

    return background_callback_manager


@pandas_cache
def thickness_cached_df(thickness):
    return DF_GLASS_TABLE[DF_GLASS_TABLE['Thickness'].between(thickness - 0.75, thickness + 0.75)]


@pandas_cache
def thickness_cached_readable_df(thickness):
    return DF_READABLE_GLASS_TABLE[DF_READABLE_GLASS_TABLE['Thickness'].between(thickness - 0.75, thickness + 0.75)]