import json
import socket
import subprocess
import sys
import time
import unittest
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from proof.core import ROOT


class DashboardBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
            cls.port = s.getsockname()[1]
        cls.base = f"http://127.0.0.1:{cls.port}"
        cls.proc = subprocess.Popen([sys.executable, "-m", "proof", "serve", "--port", str(cls.port)], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(100):
            try:
                with urlopen(cls.base + "/api/state", timeout=1) as r:
                    cls.state = json.load(r)
                break
            except (URLError, OSError):
                time.sleep(.1)
        else:
            cls.proc.terminate();cls.proc.wait()
            raise RuntimeError("Test server did not start")

    @classmethod
    def tearDownClass(cls):
        cls.proc.terminate();cls.proc.wait(timeout=5)

    def test_mutation_requires_local_session_token(self):
        req = Request(self.base + "/api/run", data=b"{}", method="POST", headers={"Content-Type": "application/json"})
        with self.assertRaises(HTTPError) as cm:
            urlopen(req)
        self.assertEqual(cm.exception.code, 403)
        cm.exception.close()

    def test_external_host_is_refused(self):
        req = Request(self.base + "/api/state", headers={"Host": "attacker.invalid"})
        with self.assertRaises(HTTPError) as cm:
            urlopen(req)
        self.assertEqual(cm.exception.code, 403)
        cm.exception.close()

    def test_foreign_origin_is_refused_even_with_token(self):
        req = Request(self.base + "/api/run", data=b"{}", method="POST", headers={"X-Scout-Token": self.state["token"], "Origin": "https://attacker.invalid"})
        with self.assertRaises(HTTPError) as cm:
            urlopen(req)
        self.assertEqual(cm.exception.code, 403)
        cm.exception.close()

    def test_preflight_returns_actionable_model_failure(self):
        config = {**self.state["info"]["defaults"], "model": "/nonexistent/offline-proof-model"}
        req = Request(self.base + "/api/preflight", data=json.dumps(config).encode(), method="POST", headers={"X-Scout-Token": self.state["token"]})
        with urlopen(req) as r:
            result = json.load(r)
        self.assertTrue(any(c["label"] == "Local model folder" and not c["passed"] for c in result["checks"]))

    def test_static_asset_paths_are_allowlisted(self):
        with self.assertRaises(HTTPError) as cm:
            urlopen(self.base + "/../requirements.lock")
        self.assertEqual(cm.exception.code, 404)
        cm.exception.close()


if __name__ == "__main__":
    unittest.main()
