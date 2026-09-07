import asyncio
import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import neptls
from neptls.fingerprints import generate
from neptls.pow import Challenge, solve, verify


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = json.dumps({"path": self.path, "user_agent": self.headers.get("User-Agent")}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)
        self.send_response(201)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_):
        pass


class CoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.thread.join()

    def test_sync_client(self):
        response = neptls.get(self.url, params={"q": "one"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["path"], "/?q=one")

    def test_json_post(self):
        response = neptls.post(self.url, json={"hello": "world"})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json(), {"hello": "world"})

    def test_async_client(self):
        async def run():
            async with neptls.AsyncClient() as client:
                return await client.get(self.url)

        self.assertEqual(asyncio.run(run()).status_code, 200)

    def test_fingerprint_and_pow(self):
        profile = generate(seed=1)
        self.assertTrue(profile.validate().to_json())
        result = solve(Challenge("test", difficulty=2))
        self.assertTrue(verify(Challenge("test", difficulty=2), result.nonce))
