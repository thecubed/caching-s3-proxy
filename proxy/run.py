#!/usr/bin/env python
import os
from proxy import CachingS3Proxy
import tempfile
import shutil
from wsgiref.simple_server import make_server


def main():
    bucket = os.environ.get('BUCKET')
    no_cache = True if os.environ.get('NO_CACHE') else False
    capacity = int(os.environ.get('CAPACITY', 1000000000))
    cache_dir = os.environ.get('CACHEDIR', tempfile.mkdtemp(prefix='s3cache-'))
    auth_config = {
        "username": os.environ.get('AUTH_USER', ''),
        "password": os.environ.get('AUTH_PASS', '')
    } if os.environ.get('USE_AUTH') else None

    p = CachingS3Proxy(bucket, no_cache, capacity, cache_dir, auth_config)
    port = int(os.environ.get('PORT', 8000))
    httpd = make_server('', port, p.proxy_s3_bucket)
    print 'Serving HTTP on port %s...' % port
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print "Shutting down!"
        httpd.shutdown()
        print "Deleting cache dir"
        shutil.rmtree(cache_dir)

if __name__ == '__main__':
    main()
