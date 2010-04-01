import mock
import httplib2
from cloudservers.client import CloudServersClient
from nose.tools import assert_equal

fake_response = httplib2.Response({"status": 200})
fake_body = '{"hi": "there"}'
mock_request = mock.Mock(return_value=(fake_response, fake_body))

def client():
    cl = CloudServersClient("username", "apikey")
    cl.management_url = "http://example.com"
    cl.auth_token = "token"
    return cl

def test_get():
    cl = client()
    with mock.patch_object(httplib2.Http, "request", mock_request):
        resp, body = cl.get("/hi")
        mock_request.assert_called_with("http://example.com/hi?fresh", "GET", 
            headers={"X-Auth-Token": "token", "User-Agent": cl.USER_AGENT})
        # Automatic JSON parsing
        assert_equal(body, {"hi":"there"})

def test_post():
    cl = client()
    with mock.patch_object(httplib2.Http, "request", mock_request):
        cl.post("/hi", body=[1, 2, 3])
        mock_request.assert_called_with("http://example.com/hi", "POST", 
            headers = {
                "X-Auth-Token": "token",
                "Content-Type": "application/json",
                "User-Agent": cl.USER_AGENT},
            body = '[1, 2, 3]'
        )
