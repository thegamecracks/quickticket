import threading
from collections.abc import Generator
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from fastapi.datastructures import State
from obstore.store import MemoryStore, S3Store

from quickticket.dependencies.store import get_object_store
from quickticket.settings import S3Settings, Settings

_LIST_RESPONSE = b"""<?xml version="1.0" encoding="UTF-8"?>
<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
  <Name>quickticket</Name>
  <Prefix></Prefix>
  <KeyCount>0</KeyCount>
  <MaxKeys>1000</MaxKeys>
  <IsTruncated>false</IsTruncated>
</ListBucketResult>
"""
_DELETE_RESPONSE = b"""<?xml version="1.0" encoding="UTF-8"?>
<DeleteResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
  <Deleted><Key>banners/x.jpg</Key></Deleted>
</DeleteResult>
"""


def _s3_settings(url: str) -> Settings:
    return Settings(
        _env_file=None,
        s3=S3Settings(
            url=url,
            region="garage",
            access_key="test-access-key",
            secret_key="test-secret-key",  # noqa: S106
        ),
    )


@contextmanager
def _s3_server() -> Generator[tuple[str, list[tuple[str, str]]]]:
    """Run a minimal S3-compatible server that records request paths."""
    requests: list[tuple[str, str]] = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            requests.append(("GET", self.path))
            if "list-type=2" in self.path:
                self._respond(_LIST_RESPONSE, "application/xml")
            else:
                self._respond(b"data", "application/octet-stream")

        def do_PUT(self) -> None:
            requests.append(("PUT", self.path))
            self._read_body()
            self.send_response(200)
            self.send_header("ETag", '"etag"')
            self.send_header("Content-Length", "0")
            self.end_headers()

        def do_POST(self) -> None:
            requests.append(("POST", self.path))
            self._read_body()
            self._respond(_DELETE_RESPONSE, "application/xml")

        def log_message(self, format: str, *args: object) -> None:  # noqa: A002
            pass

        def _read_body(self) -> None:
            length = int(self.headers.get("Content-Length") or 0)
            if length:
                self.rfile.read(length)

        def _respond(self, body: bytes, content_type: str) -> None:
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"127.0.0.1:{server.server_port}", requests
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


async def test_memory_store_from_url() -> None:
    settings = _s3_settings("memory:///")

    store = await get_object_store(settings=settings, state=State())
    assert isinstance(store, MemoryStore)


@pytest.mark.parametrize(
    ("url", "endpoint", "allow_http"),
    [
        ("s3+http://s3:3900/quickticket", "http://s3:3900", "true"),
        (
            "s3+https://s3.thegamecracks.xyz/quickticket",
            "https://s3.thegamecracks.xyz",
            "false",
        ),
        (
            "s3+https://garage-dev-qt.aerosol.dev:2459/quickticket",
            "https://garage-dev-qt.aerosol.dev:2459",
            "false",
        ),
    ],
)
async def test_s3_custom_endpoint_uses_bucket_path_and_bare_origin(
    url: str,
    endpoint: str,
    allow_http: str,
) -> None:
    store = await get_object_store(settings=_s3_settings(url), state=State())

    assert isinstance(store, S3Store)
    assert store.prefix is None
    assert store.config["bucket"] == "quickticket"
    assert store.config["endpoint"] == endpoint
    assert store.config["virtual_hosted_style_request"] == "false"
    assert store.client_options == {"allow_http": allow_http}


async def test_s3_custom_endpoint_does_not_double_the_bucket_path() -> None:
    with _s3_server() as (host, requests):
        settings = _s3_settings(f"s3+http://{host}/quickticket")
        store = await get_object_store(settings=settings, state=State())

        await store.put_async("banners/x.jpg", b"data")
        get_result = await store.get_async("banners/x.jpg")
        assert bytes(await get_result.bytes_async()) == b"data"
        await store.delete_async("banners/x.jpg")
        _ = [batch async for batch in store.list_async()]

    assert requests == [
        ("PUT", "/quickticket/banners/x.jpg"),
        ("GET", "/quickticket/banners/x.jpg"),
        ("POST", "/quickticket?delete"),
        ("GET", "/quickticket?list-type=2"),
    ]
