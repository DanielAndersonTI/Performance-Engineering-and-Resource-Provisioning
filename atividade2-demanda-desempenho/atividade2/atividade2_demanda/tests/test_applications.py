"""Functional tests for the three backend applications.

These assert behaviour only: which profile answers, what a valid request
returns, which inputs are rejected, and that the admission limit holds.

Nothing here asserts latency or throughput. Those depend on the machine and on
the load applied, so they belong to the load experiments under scripts/ and to
the report, never to a pass/fail test.

Run from the activity directory:

    python -m unittest discover -s tests -v
"""

import importlib.util
import json
import socket
import subprocess
import sys
import threading
import time
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


PROJECT_ROOT = Path(__file__).resolve().parents[1]

APPLICATIONS = {
    "cpu": PROJECT_ROOT / "apps" / "cpu" / "server.py",
    "memory": PROJECT_ROOT / "apps" / "memory" / "server.py",
    "io": PROJECT_ROOT / "apps" / "io" / "server.py",
}

# Small enough to keep the suite fast, large enough to exercise the real path.
# The CPU size counts 1 MiB hashes, so even a handful costs real time.
VALID_SIZE = {"cpu": 3, "memory": 1, "io": 64}

INVALID_SIZES = ("0", "-1", "1.5", "not-a-number", "1e3", "999999999", "")


def free_port():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


def load_server_module():
    """Import apps/server.py by path, under a name that cannot collide."""
    path = PROJECT_ROOT / "apps" / "server.py"
    spec = importlib.util.spec_from_file_location("profile_server_under_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ApplicationContractTests(unittest.TestCase):
    """Each application answers as its own profile and validates its input."""

    @classmethod
    def setUpClass(cls):
        cls.processes = {}
        cls.ports = {}
        for profile, script in APPLICATIONS.items():
            port = free_port()
            cls.processes[profile] = subprocess.Popen(
                [sys.executable, str(script), "--port", str(port)],
                cwd=PROJECT_ROOT,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
            )
            cls.ports[profile] = port
        for profile in APPLICATIONS:
            cls._await_health(profile)

    @classmethod
    def tearDownClass(cls):
        for process in cls.processes.values():
            if process.poll() is None:
                process.terminate()
        for process in cls.processes.values():
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
            process.stderr.close()

    @classmethod
    def _await_health(cls, profile):
        process = cls.processes[profile]
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise AssertionError(
                    f"{profile} exited during startup:\n{process.stderr.read()}"
                )
            try:
                with urlopen(cls._url(profile, "/health"), timeout=0.5) as response:
                    if response.status == 200:
                        return
            except (OSError, URLError):
                time.sleep(0.05)
        raise AssertionError(f"{profile} did not become healthy within 10 seconds")

    @classmethod
    def _url(cls, profile, path):
        return f"http://127.0.0.1:{cls.ports[profile]}{path}"

    def get_json(self, profile, path, timeout=20):
        try:
            with urlopen(self._url(profile, path), timeout=timeout) as response:
                return response.status, json.load(response)
        except HTTPError as error:
            return error.code, json.load(error)

    def test_health_identifies_each_profile(self):
        for profile in APPLICATIONS:
            with self.subTest(profile=profile):
                status, body = self.get_json(profile, "/health")

                self.assertEqual(status, 200)
                self.assertEqual(body, {"status": "ok", "profile": profile})

    def test_work_returns_the_result_shape_of_its_profile(self):
        for profile in APPLICATIONS:
            with self.subTest(profile=profile):
                size = VALID_SIZE[profile]
                status, body = self.get_json(profile, f"/work?size={size}")

                self.assertEqual(status, 200)
                self.assertEqual(body["profile"], profile)
                self.assertGreater(body["duration_seconds"], 0)

                result = body["result"]
                if profile == "cpu":
                    self.assertEqual(result["iterations"], size)
                    self.assertRegex(result["sha256"], r"^[0-9a-f]{64}$")
                elif profile == "memory":
                    self.assertEqual(result["allocated_mib"], size)
                    self.assertIsInstance(result["checksum"], int)
                else:
                    self.assertEqual(result["bytes_written"], size * 1024)
                    self.assertEqual(result["bytes_read"], size * 1024)

    def test_work_is_deterministic(self):
        first = self.get_json("cpu", "/work?size=3")[1]["result"]["sha256"]
        second = self.get_json("cpu", "/work?size=3")[1]["result"]["sha256"]

        self.assertEqual(first, second)

    def test_work_uses_a_default_size_when_none_is_given(self):
        status, body = self.get_json("cpu", "/work")

        self.assertEqual(status, 200)
        self.assertEqual(body["result"]["iterations"], 10)

    def test_work_rejects_invalid_sizes(self):
        for profile in APPLICATIONS:
            for size in INVALID_SIZES:
                with self.subTest(profile=profile, size=size):
                    status, body = self.get_json(profile, f"/work?size={size}")

                    self.assertEqual(status, 400)
                    self.assertIn("error", body)

    def test_unknown_path_returns_not_found(self):
        status, body = self.get_json("cpu", "/nope")

        self.assertEqual(status, 404)
        self.assertIn("error", body)

    def test_shared_entry_point_still_selects_a_profile(self):
        """apps/server.py --profile is the documented fallback path."""
        port = free_port()
        process = subprocess.Popen(
            [
                sys.executable,
                str(PROJECT_ROOT / "apps" / "server.py"),
                "--profile",
                "memory",
                "--port",
                str(port),
            ],
            cwd=PROJECT_ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    self.fail(f"exited during startup:\n{process.stderr.read()}")
                try:
                    with urlopen(
                        f"http://127.0.0.1:{port}/health", timeout=0.5
                    ) as response:
                        body = json.load(response)
                    break
                except (OSError, URLError):
                    time.sleep(0.05)
            else:
                self.fail("did not become healthy within 10 seconds")

            self.assertEqual(body, {"status": "ok", "profile": "memory"})
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
            process.stderr.close()

    def test_unknown_profile_is_rejected(self):
        module = load_server_module()

        with self.assertRaises(ValueError):
            module.serve("gpu", free_port())


class AdmissionControlTests(unittest.TestCase):
    """The work-slot limit is what keeps a load experiment from driving the
    machine into uncontrolled resource use, so it gets a direct test."""

    def test_request_is_rejected_while_every_work_slot_is_busy(self):
        module = load_server_module()
        work_started = threading.Event()
        release_work = threading.Event()

        def blocking_compute(iterations):
            work_started.set()
            if not release_work.wait(timeout=5):
                raise AssertionError("the test never released the first request")
            return {"sha256": "0" * 64, "iterations": iterations}

        handler = type(
            "SingleSlotHandler",
            (module.WorkRequestHandler,),
            {"profile": "cpu", "work_slots": threading.BoundedSemaphore(1)},
        )
        server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        serving = threading.Thread(target=server.serve_forever, daemon=True)
        serving.start()
        base = f"http://127.0.0.1:{server.server_port}"
        first_response = {}

        def send_first_request():
            try:
                with urlopen(f"{base}/work?size=1", timeout=5) as response:
                    first_response["status"] = response.status
            except OSError as error:  # recorded so the failure is diagnosable
                first_response["error"] = error

        try:
            with patch.object(module, "compute_cpu", blocking_compute):
                first_client = threading.Thread(target=send_first_request)
                first_client.start()
                self.assertTrue(
                    work_started.wait(timeout=5), "the first request never started"
                )

                try:
                    with urlopen(f"{base}/work?size=1", timeout=5) as response:
                        second_status = response.status
                except HTTPError as error:
                    second_status = error.code

                release_work.set()
                first_client.join(timeout=5)

            self.assertEqual(first_response.get("status"), 200)
            self.assertEqual(second_status, 503)
        finally:
            release_work.set()
            server.shutdown()
            server.server_close()
            serving.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
