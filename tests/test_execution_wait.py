from __future__ import annotations

import asyncio

import pytest
from pydantic import ValidationError

from dbackup_mcp.models import ExecutionWaitInput
from dbackup_mcp.server import list_tools
from dbackup_mcp.service import DBackupService


class SequenceClient:
    def __init__(self, states):
        self.states = list(states)
        self.calls = []

    def request(self, method, path, *, query=None, body=None):
        self.calls.append((method, path, query, body))
        if not self.states:
            raise AssertionError("unexpected extra execution poll")
        state = self.states.pop(0)
        return {
            "success": True,
            "data": {
                "id": "exec-1",
                "type": state.get("type", "Backup"),
                "status": state["status"],
                "stage": state.get("stage", state["status"]),
                "startedAt": "2026-09-29T12:00:00Z",
                "endedAt": state.get("endedAt"),
                "logs": [{"n": i, "password": "must-not-leak"} for i in range(5)],
            },
        }


class FakeClock:
    def __init__(self):
        self.now = 0.0
        self.sleeps = []

    def monotonic(self):
        return self.now

    async def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.now += seconds


def wait(service, *, max_wait_seconds=10.0, log_limit=2, clock=None):
    clock = clock or FakeClock()
    return asyncio.run(
        service.execution_wait_terminal(
            "exec-1",
            max_wait_seconds=max_wait_seconds,
            poll_interval_seconds=1.0,
            log_limit=log_limit,
            sleep=clock.sleep,
            monotonic=clock.monotonic,
        )
    )


def test_wait_running_to_success_uses_only_read_calls_and_bounds_logs():
    client = SequenceClient([
        {"status": "Running"},
        {"status": "Success", "endedAt": "2026-09-29T12:00:03Z"},
    ])
    result = wait(DBackupService(client))
    assert result["terminal"] is True
    assert result["timedOut"] is False
    assert result["execution"]["status"] == "Success"
    assert result["polls"] == 2
    assert result["execution"]["logs"] == [{"n": 3}, {"n": 4}]
    assert all(method == "GET" for method, *_ in client.calls)


@pytest.mark.parametrize("status", ["Failed", "Partial", "Cancelled"])
def test_wait_running_to_other_terminal_states(status):
    client = SequenceClient([
        {"status": "Running"},
        {"status": status, "endedAt": "2026-09-29T12:00:04Z"},
    ])
    result = wait(DBackupService(client))
    assert result["terminal"] is True
    assert result["execution"]["status"] == status


def test_wait_times_out_bounded_while_execution_is_still_running():
    client = SequenceClient([
        {"status": "Running"},
        {"status": "Running"},
        {"status": "Running"},
    ])
    clock = FakeClock()
    result = wait(DBackupService(client), max_wait_seconds=2.0, clock=clock)
    assert result["terminal"] is False
    assert result["timedOut"] is True
    assert result["execution"]["status"] == "Running"
    assert result["polls"] == 3
    assert sum(clock.sleeps) == 2.0


def test_wait_returns_already_terminal_execution_immediately():
    client = SequenceClient([
        {"status": "Success", "endedAt": "2026-09-29T12:00:00Z"},
    ])
    clock = FakeClock()
    result = wait(DBackupService(client), clock=clock)
    assert result["terminal"] is True
    assert result["polls"] == 1
    assert clock.sleeps == []


@pytest.mark.parametrize("execution_type", ["Backup", "Restore"])
def test_wait_supports_backup_and_restore_executions(execution_type):
    client = SequenceClient([
        {"status": "Success", "type": execution_type, "endedAt": "2026-09-29T12:00:00Z"},
    ])
    result = wait(DBackupService(client))
    assert result["execution"]["type"] == execution_type
    assert result["terminal"] is True


def test_repeated_wait_is_idempotent_and_never_mutates_execution():
    client = SequenceClient([
        {"status": "Success", "endedAt": "2026-09-29T12:00:00Z"},
        {"status": "Success", "endedAt": "2026-09-29T12:00:00Z"},
    ])
    service = DBackupService(client)
    first = wait(service)
    second = wait(service)
    assert first["execution"]["id"] == second["execution"]["id"] == "exec-1"
    assert [method for method, *_ in client.calls] == ["GET", "GET"]


def test_wait_input_is_strictly_bounded():
    args = ExecutionWaitInput(id="exec-1", max_wait_seconds=90, poll_interval_seconds=1, log_limit=20)
    assert args.max_wait_seconds == 90
    with pytest.raises(ValidationError):
        ExecutionWaitInput(id="exec-1", max_wait_seconds=91)


def test_wait_tool_is_read_only_and_idempotent():
    tools = {tool.name: tool for tool in asyncio.run(list_tools())}
    wait_tool = tools["execution_wait_terminal"]
    assert wait_tool.annotations is not None
    assert wait_tool.annotations.readOnlyHint is True
    assert wait_tool.annotations.destructiveHint is False
    assert wait_tool.annotations.idempotentHint is True
