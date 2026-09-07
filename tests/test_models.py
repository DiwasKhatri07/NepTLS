import unittest

from neptls.profiles import get_profile
from neptls.tls import TLSConfig, TLSFingerprint
from neptls.user_agents import parse


class ModelTests(unittest.TestCase):
    def test_tls_fingerprint_diff(self):
        left = TLSFingerprint.from_config(TLSConfig())
        right = TLSFingerprint.from_config(TLSConfig(alpn_protocols=("h2",)))
        self.assertFalse(left.compare(right))
        self.assertIn("alpn", left.diff(right))

    def test_profile_round_trip(self):
        profile = get_profile("chrome")
        restored = profile.from_dict(profile.to_dict())
        self.assertEqual(restored.browser, "chrome")

    def test_user_agent_parse(self):
        parsed = parse(get_profile("firefox").user_agent)
        self.assertEqual(parsed.browser, "firefox")
