import httplib2
try:
    import json
except ImportError:
    import simplejson as json

import cloudservers
from . import exceptions

class CloudServersClient(httplib2.Http):
    
    AUTH_URL = 'https://auth.api.rackspacecloud.com/v1.0'
    USER_AGENT = 'python-cloudservers/%s' % cloudservers.__version__
    
    def __init__(self, user, apikey):
        super(CloudServersClient, self).__init__()
        self.user = user
        self.apikey = apikey
        
        self.management_url = None
        self.auth_token = None
        
        # httplib2 overrides
        self.force_exception_to_status_code = True

    def request(self, *args, **kwargs):
        kwargs.setdefault('headers', {})
        kwargs['headers']['User-Agent'] = self.USER_AGENT
        if 'body' in kwargs:
            kwargs['headers']['Content-Type'] = 'application/json'
            kwargs['body'] = json.dumps(kwargs['body'])
            
        resp, body = super(CloudServersClient, self).request(*args, **kwargs)
        body = json.loads(body) if body else None

        if resp.status in (400, 401, 403, 404, 413, 500):
            raise exceptions.from_response(resp, body)

        return resp, body

    def _cs_request(self, url, method, **kwargs):
        if not self.management_url:
            self.authenticate()

        # Perform the request once. If we get a 401 back then it
        # might be because the auth token expired, so try to
        # re-authenticate and try again. If it still fails, bail.
        try:
            kwargs.setdefault('headers', {})['X-Auth-Token'] = self.auth_token
            resp, body = self.request(self.management_url + url, method, **kwargs)
            return resp, body
        except exceptions.Unauthorized, ex:
            try:
                self.authenticate()
                resp, body = self.request(self.management_url + url, method, **kwargs)
                return resp, body
            except exceptions.Unauthorized:
                raise ex

    def get(self, url, **kwargs):
        # The Rackspace API returns cached results by default.
        # We like our responses nice and fresh, though, so we
        # stick a fake GET parameter on the URL.
        if not '?' in url:
            url += '?fresh'
        return self._cs_request(url, 'GET', **kwargs)
    
    def post(self, url, **kwargs):
        return self._cs_request(url, 'POST', **kwargs)
    
    def put(self, url, **kwargs):
        return self._cs_request(url, 'PUT', **kwargs)
    
    def delete(self, url, **kwargs):
        return self._cs_request(url, 'DELETE', **kwargs)

    def authenticate(self):
        headers = {'X-Auth-User': self.user, 'X-Auth-Key': self.apikey}
        resp, body = self.request(self.AUTH_URL, 'GET', headers=headers)
        self.management_url = resp['x-server-management-url']
        self.auth_token = resp['x-auth-token']
