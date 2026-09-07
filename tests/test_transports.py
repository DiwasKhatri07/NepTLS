import asyncio
import sys
import types
import unittest
from unittest.mock import patch

import neptls
from neptls.models import Response
from neptls.tls import TLSConfig
from neptls.transports import HTTPXTransport, normalize_transport
from neptls.exceptions import TransportUnavailableError


class TransportTests(unittest.TestCase):
    def test_transport_aliases_and_capabilities(self):
        self.assertEqual(normalize_transport("h2"), "http2")
        self.assertEqual(normalize_transport("http/3"), "http3")
        self.assertTrue(neptls.transport_available("http1"))
        with self.assertRaises(ValueError):
            normalize_transport("spdy")

    def test_missing_native_backend_is_explicit(self):
        for transport, extra in (("http2", "http2"), ("http3", "http3")):
            if neptls.transport_available(transport):
                continue
            with self.assertRaises(neptls.TransportUnavailableError) as error:
                neptls.Client(transport=transport)
            self.assertIn(f"neptls[{extra}]", str(error.exception))

    def test_unavailable_native_backend_can_explicitly_fall_back(self):
        with patch(
            "neptls.client.create_transport",
            side_effect=TransportUnavailableError("optional backend missing"),
        ):
            client = neptls.Client(transport="http2", fallback_transport="http1")
        self.assertEqual(client.requested_transport, "http2")
        self.assertEqual(client.transport, "http1")
        self.assertEqual(client.fallback_transport, "http1")
        client.close()

    def test_http1_response_reports_actual_protocol(self):
        response = Response(
            status_code=200,
            reason="OK",
            url="http://example.test/",
            headers={},
        )
        self.assertEqual(response.http_version, "HTTP/1.1")
        self.assertEqual(response.protocol, "http/1.1")
        self.assertEqual(response.negotiated_protocol, "http/1.1")

    def test_tls_transport_alpn_is_added_without_losing_preferences(self):
        config = TLSConfig(alpn_protocols=("http/1.1",))
        h2 = config.for_transport("http2")
        h3 = config.for_transport("http3")
        self.assertEqual(h2.alpn_protocols, ("h2", "http/1.1"))
        self.assertEqual(h3.alpn_protocols, ("h3", "http/1.1"))
        self.assertEqual(config.for_transport("http1").alpn_protocols, ("http/1.1",))
        self.assertEqual(config.alpn_protocols, ("http/1.1",))

    def test_http2_adapter_reports_negotiated_version(self):
        class FakeResponse:
            status_code = 200
            reason_phrase = "OK"
            url = "https://example.test/"
            headers = {"content-type": "text/plain"}
            content = b"ok"
            http_version = "HTTP/2"

        class FakeHTTPXClient:
            def __init__(self, **options):
                self.options = options

            def request(self, *args, **kwargs):
                return FakeResponse()

            def close(self):
                pass

        fake_httpx = types.SimpleNamespace(Client=FakeHTTPXClient)
        fake_h2 = types.ModuleType("h2")
        with patch.dict(sys.modules, {"httpx": fake_httpx, "h2": fake_h2}):
            transport = HTTPXTransport(
                verify=True,
                headers={},
                cookies=None,
                proxy=None,
                follow_redirects=True,
            )
            response = transport.request(
                "GET",
                "https://example.test/",
                headers={},
                body=None,
                timeout=1,
            )
            transport.close()
        self.assertEqual(response.http_version, "HTTP/2")
        self.assertEqual(response.content, b"ok")

    def test_async_client_keeps_transport_selector(self):
        async def run():
            async with neptls.AsyncClient(transport="http1") as client:
                return client.transport, client.native_transport_available

        self.assertEqual(asyncio.run(run()), ("http1", True))
