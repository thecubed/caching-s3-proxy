#!/usr/bin/env python
import os
from proxy import CachingS3Proxy
import tempfile
from wsgiref.simple_server import make_server


def main():
    bucket = os.environ.get('BUCKET')
    capacity = int(os.environ.get('CAPACITY', 1000000000))
    cache_dir = os.environ.get('CACHEDIR', tempfile.gettempdir())
    auth_config = {
        "username": os.environ.get('AUTH_USER', ''),
        "password": os.environ.get('AUTH_PASS', '')
    } if os.environ.get('USE_AUTH') else None

    p = CachingS3Proxy(bucket, capacity, cache_dir, auth_config)
    port = int(os.environ.get('PORT', 8000))
    httpd = make_server('', port, p.proxy_s3_bucket)
    print 'Serving HTTP on port %s...' % port
    httpd.serve_forever()

if __name__ == '__main__':
    main()
