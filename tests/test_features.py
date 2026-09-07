import gzip
import json
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import neptls
from neptls import BasicAuth, BearerAuth
from neptls.cookies import cookie_header, jar_snapshot, parse_set_cookie
from neptls.crypto import (
    base32decode,
    base32encode,
    digest,
    hash_file,
    urlsafe_b64decode,
    urlsafe_b64encode,
)
from neptls.pow import Challenge, benchmark, solve_parallel, verify
from neptls.urltools import build_url, normalize_url, query_params


class FeatureHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/gzip":
            body = gzip.compress(b"compressed response")
            self.send_response(200)
            self.send_header("Content-Encoding", "gzip")
        else:
            body = b"ok"
            self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        payload = {
            "authorization": self.headers.get("Authorization"),
            "content_length": self.headers.get("Content-Length"),
        }
        body = json.dumps(payload).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_):
        pass


class FeatureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), FeatureHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.thread.join()

    def test_user_agent_helpers_match_documented_api(self):
        self.assertIn("Chrome/", neptls.ua.chrome())
        self.assertIn("Firefox/", neptls.ua.firefox())
        self.assertIn("Mobile", neptls.ua.mobile())
        self.assertEqual(neptls.user_agents.parse(neptls.ua.edge()).browser, "edge")

    def test_hash_and_encoding_helpers(self):
        self.assertEqual(digest("hello", "sha256"), neptls.crypto.sha256("hello"))
        with tempfile.NamedTemporaryFile() as handle:
            handle.write(b"hello")
            handle.flush()
            self.assertEqual(hash_file(handle.name), neptls.crypto.sha256("hello"))
        self.assertEqual(urlsafe_b64decode(urlsafe_b64encode("hello")), b"hello")
        self.assertEqual(base32decode(base32encode("hello")), b"hello")

    def test_auth_and_compression(self):
        with neptls.Client() as client:
            basic = client.post(self.url, auth=BasicAuth("user", "pass")).json()
            bearer = client.post(self.url, auth=BearerAuth("secret")).json()
            compressed = client.get(f"{self.url}/gzip")
        self.assertTrue(basic["authorization"].startswith("Basic "))
        self.assertEqual(bearer["authorization"], "Bearer secret")
        self.assertEqual(compressed.text, "compressed response")

    def test_parallel_pow_and_benchmark(self):
        challenge = Challenge("parallel", difficulty=2, algorithm="sha512")
        result = solve_parallel(challenge, workers=2, max_attempts=100_000)
        self.assertTrue(verify(challenge, result.nonce))
        self.assertGreater(benchmark(challenge, attempts=10)["attempts"], 0)

    def test_chrome_compatibility_alias_and_hints(self):
        client = neptls.Client(impersonate="chrome")
        self.assertEqual(client.profile.name, "chrome")
        self.assertIn("Sec-CH-UA", client.profile.headers)
        self.assertIn("Sec-Fetch-Mode", client.profile.headers)
        with self.assertRaises(ValueError):
            neptls.Client(profile="chrome", impersonate="chrome")

    def test_url_and_cookie_helpers(self):
        url = build_url("https://example.com?a=1", {"b": "two"})
        self.assertEqual(query_params(url)["b"], "two")
        self.assertEqual(normalize_url("example.com"), "https://example.com")
        self.assertEqual(parse_set_cookie("session=abc; Path=/")["session"], "abc")
        self.assertEqual(cookie_header({"a": "1", "b": "2"}), "a=1; b=2")
        with neptls.Client(cookies={"session": "abc"}) as client:
            self.assertEqual(jar_snapshot(client.cookies)["session"], "abc")