"""
Tests for FIFO serialization of command-submission HTTP POSTs.

The printer's HTTP API expects one command at a time. The client serializes
command POSTs (/control, /product, /printGcode) through one asyncio.Lock, so
concurrent callers run one at a time, in submission order. Uploads and
read/poll POSTs stay outside the lock, so a long upload never delays a
pause or stop command.

These tests use a fake HTTP session. It records when each POST starts and
stops. From that record, the tests check two invariants:

- No overlap: at most one command POST is in flight at any moment.
- No leak: a command sent after a failing one still runs. The ``wait_for``
  timeouts turn a leaked lock into a test failure instead of a hang.
"""

import asyncio

from flashforge.client import FlashForgeClient

_PRODUCT_BODY = {
    "code": 0,
    "message": "ok",
    "product": {
        "chamberTempCtrlState": 1,
        "externalFanCtrlState": 1,
        "internalFanCtrlState": 1,
        "lightCtrlState": 1,
        "nozzleTempCtrlState": 1,
        "platformTempCtrlState": 1,
    },
}


class _RequestTracker:
    """Records the start and stop of each fake POST, and the overlap count."""

    def __init__(self) -> None:
        self.events: list[tuple[str, str]] = []
        self.active = 0
        self.max_active = 0

    def started(self, name: str) -> None:
        self.active += 1
        self.max_active = max(self.max_active, self.active)
        self.events.append(("start", name))

    def stopped(self, name: str) -> None:
        self.active -= 1
        self.events.append(("stop", name))

    def starts(self) -> list[str]:
        """Return the POST names in the order their requests began."""
        return [name for kind, name in self.events if kind == "start"]


class _FakeResponse:
    """Minimal stand-in for an ``aiohttp`` response object."""

    def __init__(self, body: dict) -> None:
        self.status = 200
        self._body = body

    async def json(self) -> dict:
        return self._body


class _FakePost:
    """Async context manager that mimics ``session.post(...)``."""

    def __init__(self, tracker: _RequestTracker, name: str, body: dict) -> None:
        self._tracker = tracker
        self._name = name
        self._body = body

    async def __aenter__(self) -> _FakeResponse:
        self._tracker.started(self._name)
        # Hold the request open for a moment. Without this delay, a second
        # command could start and finish before the first one is even
        # scheduled, and the test would pass even with no lock at all.
        await asyncio.sleep(0.02)
        return _FakeResponse(self._body)

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        self._tracker.stopped(self._name)
        return False


class _FailingPost(_FakePost):
    """A POST that fails while the request is in flight."""

    async def __aenter__(self) -> _FakeResponse:
        self._tracker.started(self._name)
        await asyncio.sleep(0.02)
        # ``__aexit__`` does not run when ``__aenter__`` raises, so record the
        # stop here. A failed request is no longer in flight.
        self._tracker.stopped(self._name)
        raise RuntimeError("simulated transport failure")


class _FakeSession:
    """Stand-in for the shared ``aiohttp`` session, routed through the tracker."""

    closed = False

    def __init__(self, tracker: _RequestTracker, fail_first_command: str | None = None) -> None:
        self._tracker = tracker
        self._fail_first_command = fail_first_command
        self._already_failed = False

    def post(self, url: str, json: dict | None = None, headers: dict | None = None):
        name = self._request_name(url, json)
        if name == self._fail_first_command and not self._already_failed:
            self._already_failed = True
            return _FailingPost(self._tracker, name, {})
        return _FakePost(self._tracker, name, self._body_for(url))

    @staticmethod
    def _request_name(url: str, payload: dict | None) -> str:
        """Derive a readable name for a request from its URL and payload."""
        if isinstance(payload, dict) and isinstance(payload.get("payload"), dict):
            return str(payload["payload"].get("cmd", url))
        return url.rstrip("/").rsplit("/", 1)[-1]

    @staticmethod
    def _body_for(url: str) -> dict:
        if url.endswith("/product"):
            return _PRODUCT_BODY
        if url.endswith("/gcodeList"):
            return {"code": 0, "gcodeList": ["a.gcode"]}
        return {"code": 0, "message": "ok"}


def _client_with_fake_session(
    tracker: _RequestTracker, fail_first_command: str | None = None
) -> FlashForgeClient:
    """Build a client whose HTTP session is the recording fake."""
    client = FlashForgeClient("192.168.1.120", "SN123", "CODE123")
    client._http_session = _FakeSession(tracker, fail_first_command)
    return client


async def test_concurrent_control_commands_never_overlap():
    """Two control commands sent together run strictly one after the other."""
    tracker = _RequestTracker()
    client = _client_with_fake_session(tracker)

    results = await asyncio.wait_for(
        asyncio.gather(
            client.control.send_control_command("printCtl_cmd", {"speed": 100}),
            client.control.send_control_command("lightCtrl_cmd", {"status": "open"}),
        ),
        timeout=5,
    )

    assert results == [True, True]
    assert tracker.max_active == 1
    assert sorted(tracker.starts()) == ["lightCtrl_cmd", "printCtl_cmd"]


async def test_commands_run_in_submission_order():
    """Commands queued behind a busy lock run in the order callers sent them."""
    tracker = _RequestTracker()
    client = _client_with_fake_session(tracker)

    async with client.command_lock:
        # Stand in for a command in flight. Queue two commands behind the
        # lock: they must run in the order they were submitted, not in some
        # scheduler-chosen order.
        second = asyncio.create_task(client.control.send_control_command("cmd_second", {}))
        await asyncio.sleep(0)
        third = asyncio.create_task(client.control.send_control_command("cmd_third", {}))
        await asyncio.sleep(0)

    await asyncio.wait_for(asyncio.gather(second, third), timeout=5)

    assert tracker.starts() == ["cmd_second", "cmd_third"]
    assert tracker.max_active == 1


async def test_failing_command_releases_the_lock():
    """A command sent after a failing one still runs; the lock does not leak."""
    tracker = _RequestTracker()
    client = _client_with_fake_session(tracker, fail_first_command="cmd_boom")

    results = await asyncio.wait_for(
        asyncio.gather(
            client.control.send_control_command("cmd_boom", {}),
            client.control.send_control_command("cmd_ok", {}),
        ),
        timeout=5,
    )

    assert results == [False, True]
    assert tracker.starts() == ["cmd_boom", "cmd_ok"]
    assert tracker.max_active == 1


async def test_control_and_print_start_share_one_lock():
    """A /control command and a /printGcode start cannot be in flight together."""
    tracker = _RequestTracker()
    client = _client_with_fake_session(tracker)

    results = await asyncio.wait_for(
        asyncio.gather(
            client.control.send_control_command("printCtl_cmd", {}),
            client.job_control.print_local_file("a.gcode", False),
        ),
        timeout=5,
    )

    assert results == [True, True]
    assert tracker.max_active == 1
    assert sorted(tracker.starts()) == ["printCtl_cmd", "printGcode"]


async def test_product_command_shares_the_lock():
    """The /product command queues behind a /control command, and vice versa."""
    tracker = _RequestTracker()
    client = _client_with_fake_session(tracker)

    results = await asyncio.wait_for(
        asyncio.gather(
            client.send_product_command(),
            client.control.send_control_command("lightCtrl_cmd", {"status": "open"}),
        ),
        timeout=5,
    )

    assert results == [True, True]
    assert tracker.max_active == 1
    assert sorted(tracker.starts()) == ["lightCtrl_cmd", "product"]


async def test_reads_do_not_wait_for_the_command_lock():
    """A read/poll POST runs while the command lock is held by someone else."""
    tracker = _RequestTracker()
    client = _client_with_fake_session(tracker)

    async with client.command_lock:
        # Stand in for a command in flight. The file-list read must not queue
        # behind the lock: if it did, the wait_for timeout below would fire.
        files = await asyncio.wait_for(client.files.get_recent_file_list(), timeout=5)

    assert [f.gcode_file_name for f in files] == ["a.gcode"]
    assert tracker.starts() == ["gcodeList"]
