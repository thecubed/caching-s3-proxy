import os
import tempfile
from proxy import CachingS3Proxy

def application(environ, start_response):
    bucket = os.environ.get('BUCKET')
    no_cache = True if os.environ.get('NO_CACHE') else False
    capacity = int(os.environ.get('CAPACITY', 1000000000))
    cache_dir = os.environ.get('CACHEDIR', tempfile.gettempdir())
    auth_config = {
        "username": os.environ.get('AUTH_USER', ''),
        "password": os.environ.get('AUTH_PASS', '')
    } if os.environ.get('USE_AUTH') else None
    p = CachingS3Proxy(bucket, no_cache, capacity, cache_dir, auth_config)
    return p.proxy_s3_bucket(environ, start_response)
