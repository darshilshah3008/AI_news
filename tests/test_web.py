from io import BytesIO

from aisignal.web import app


def call_app(path: str):
    status_holder = {}

    def start_response(status, headers):
        status_holder["status"] = status
        status_holder["headers"] = headers

    environ = {
        "REQUEST_METHOD": "GET",
        "PATH_INFO": path,
        "QUERY_STRING": "",
        "CONTENT_LENGTH": "0",
        "wsgi.input": BytesIO(b""),
    }
    body = b"".join(app(environ, start_response)).decode("utf-8")
    return status_holder["status"], body


def test_landing_page_loads():
    status, body = call_app("/")
    assert status.startswith("200")
    assert "AI Signal OS" in body
