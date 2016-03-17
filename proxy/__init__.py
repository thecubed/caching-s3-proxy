import boto
from boto.s3.key import Key
import hashlib
import logging
from proxy.cache import LRUCache
import tempfile
from base64 import b64decode
import mimetypes


class CachingS3Proxy(object):
    def __init__(self, bucket=None, no_cache=False, capacity=(10*10**9), cache_dir=tempfile.gettempdir(), auth=None):
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        self.bucket = bucket
        self.no_cache = no_cache
        if self.no_cache:
            self.logger.info("Cache disabled!")
        self.cache = LRUCache(capacity, cache_dir)
        self.auth = auth

    def proxy_s3_bucket(self, environ, start_response):
        """proxy private s3 buckets"""
        path_info = environ.get('PATH_INFO', '')

        if path_info == '/':
            status = '200 OK'
            response_headers = [('Content-type', 'text/plain')]
            start_response(status, response_headers)
            return ['Caching S3 Proxy']

        if self.auth and not self.check_auth(environ.get('HTTP_AUTHORIZATION')):
            start_response('401 Authentication Required',
                       [('Content-Type', 'text/plain'),
                        ('WWW-Authenticate', 'Basic realm="Login"')])
            return ['Login']

        path_info = path_info.lstrip('/')

        if self.bucket:
            bucket = self.bucket
            key = path_info
        else:
            (bucket, key) = path_info.split('/', 1)

        if key[-1:] == '/':
            key += 'index.html'

        s3_result = self.fetch_s3_object(bucket, key)
        if s3_result:
            status = '200 OK'
            type = mimetypes.guess_type(key)[0]
            response_headers = [('Content-type', type)] if type else []
            start_response(status, response_headers)
            return [s3_result]
        else:
            status = '404 NOT FOUND'
            response_headers = [('Content-type', 'text/plain')]
            start_response(status, response_headers)
            return ['404 Not Found']

    def check_auth(self, header):
        if not header:
            return False

        _, encoded = header.split(None, 1)
        decoded = b64decode(encoded).decode('UTF-8')
        username, password = decoded.split(':', 1)

        return username == self.auth.get('username', '') and password == self.auth.get('password', '')

    def fetch_s3_object(self, bucket, key):
        if not self.no_cache:
            m = hashlib.md5()
            m.update(bucket+key)
            cache_key = m.hexdigest()

            if cache_key in self.cache:
                self.logger.debug('cache hit for %s' % cache_key)
                return self.cache[cache_key]
            else:
                self.logger.debug('cache miss for %s' % cache_key)

            conn = boto.connect_s3()
            b = conn.get_bucket(bucket)
            k = b.get_key(key)
            if k:
                obj = k.get_contents_as_string()
                self.cache[cache_key] = obj
                return obj
            else:
                return None
        else:
            conn = boto.connect_s3()
            k = conn.get_bucket(bucket).get_key(key)
            if k:
                return k.get_contents_as_string()
            else:
                return None
