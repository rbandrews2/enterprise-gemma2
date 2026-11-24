import json
import tempfile
import unittest
from pathlib import Path

import httpx

from services.v2.knowledge.models import load_catalog
from services.v2.knowledge.research import Links, run, targets


class ResearchTests(unittest.TestCase):
    def test_catalog_scope(self):
        sources = targets(load_catalog())
        self.assertLessEqual(len(sources), 16)
        self.assertTrue(all(s.origin == "official" for s in sources))
        self.assertFalse(any("specs" in s.id or "rb-vol" in s.id for s in sources))

    def test_discovery_does_not_follow_untrusted_links(self):
        parser = Links("https://www.vdot.virginia.gov/manual/")
        parser.feed('<a href="/new.pdf">new</a><a href="https://evil.example/x">x</a>'
                    '<a href="http://127.0.0.1/x">x</a><a href="javascript:alert(1)">x</a>')
        self.assertEqual(parser.links, {"https://www.vdot.virginia.gov/new.pdf"})

    def test_change_failure_and_daily_guard(self):
        source = next(s for s in targets(load_catalog()) if s.kind == "html")
        body = b'<html><a href="/new.pdf">update</a></html>'
        status = 200
        calls = []
        def respond(request):
            calls.append(str(request.url))
            return httpx.Response(status, content=body, headers={"Content-Type": "text/html"})
        with tempfile.TemporaryDirectory() as tmp, httpx.Client(transport=httpx.MockTransport(respond)) as client:
            root = Path(tmp)
            first = run(root, [source], client, now=100000)
            self.assertEqual(first["results"][0]["status"], "baseline_unreviewed")
            self.assertEqual(run(root, [source], client, now=100001)["status"], "not_due")
            self.assertEqual(len(calls), 1)
            same = run(root, [source], client, now=200000)
            self.assertEqual(same["results"][0]["status"], "unchanged")
            body = b'<html>new revision</html>'
            change = run(root, [source], client, now=300000)
            self.assertEqual(change["results"][0]["status"], "changed_pending_review")
            state = json.loads((root / "state.json").read_text())["sources"]
            status = 503
            failed = run(root, [source], client, now=400000)
            self.assertEqual(failed["results"][0]["status"], "check_failed")
            self.assertEqual(state, json.loads((root / "state.json").read_text())["sources"])
            self.assertEqual(len(list(root.glob("candidates/*/*/discovery.json"))), 2)
            self.assertFalse((root / "running.lock").exists())

    def test_redirect_and_size_rejected(self):
        source = targets(load_catalog())[0]
        for response in [httpx.Response(302, headers={"Location": "https://evil.example/manual.pdf"}),
                         httpx.Response(200, headers={"Content-Type": "application/pdf"}, content=b"%PDF-123456789")]:
            with tempfile.TemporaryDirectory() as tmp, httpx.Client(transport=httpx.MockTransport(lambda _: response)) as client:
                result = run(Path(tmp), [source], client, now=100000, max_bytes=8)
                self.assertEqual(result["results"][0]["status"], "check_failed")

    def test_overlap_lock(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "running.lock").touch()
            self.assertEqual(run(root, [], None)["status"], "already_running")
            self.assertTrue((root / "running.lock").exists())


if __name__ == "__main__":
    unittest.main()
