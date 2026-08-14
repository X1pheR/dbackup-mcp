from __future__ import annotations

import pytest

from dbackup_mcp.models import JobSourceSpec, JobSpec
from dbackup_mcp.service import DBackupService


class FakeClient:
    def request(self, method, path, *, query=None, body=None):
        if path == "/adapters" and query == {"type": "database", "role": None}:
            return [{"id": "db1", "name": "Postgres", "adapterId": "postgres"}]
        if path == "/adapters" and query == {"type": "storage", "role": "SOURCE"}:
            return [{"id": "src1", "name": "Docker files", "storageRole": "SOURCE"}]
        if path == "/adapters" and query == {"type": "storage", "role": "DESTINATION"}:
            return [{"id": "dst1", "name": "Remote storage", "storageRole": "DESTINATION"}]
        if path == "/adapters/db1/databases":
            return {"success": True, "databases": ["app", "other"]}
        if path == "/adapters/src1/browse":
            return {"success": True, "path": query["path"]}
        raise AssertionError((method, path, query, body))


def spec(**overrides):
    values = dict(
        name="App",
        schedule="0 3 * * *",
        source_id="db1",
        databases=["app"],
        sources=[JobSourceSpec(config_id="src1", path="/appdata/app")],
        destinations=[{"config_id": "dst1"}],
    )
    values.update(overrides)
    return JobSpec(**values)


def test_plan_validates_live_references_and_selected_databases() -> None:
    result = DBackupService(FakeClient()).job_plan(spec())
    assert result["valid"] is True
    assert result["checks"]["databaseSource"] == "db1"
    assert result["checks"]["directorySources"] == ["src1"]
    assert result["checks"]["destinations"] == ["dst1"]


def test_plan_rejects_unknown_destination() -> None:
    with pytest.raises(ValueError, match="destination adapter not found"):
        DBackupService(FakeClient()).job_plan(spec(destinations=[{"config_id": "missing"}]))


def test_plan_rejects_unknown_database() -> None:
    with pytest.raises(ValueError, match="database not available"):
        DBackupService(FakeClient()).job_plan(spec(databases=["missing"]))


def test_plan_rejects_directory_source_that_is_not_source_role() -> None:
    with pytest.raises(ValueError, match="Directory SOURCE adapter not found"):
        DBackupService(FakeClient()).job_plan(spec(sources=[JobSourceSpec(config_id="dst1", path="/data")]))


class JobUpdateClient:
    def __init__(self):
        self.calls = []

    def request(self, method, path, *, query=None, body=None):
        self.calls.append((method, path, query, body))
        return {"id": "job1", "enabled": body.get("enabled") if body else None}


def test_job_set_enabled_sends_only_enabled_field() -> None:
    client = JobUpdateClient()
    service = DBackupService(client)
    service.job_set_enabled("job1", False)
    assert client.calls == [("PUT", "/jobs/job1", None, {"enabled": False})]


def test_plan_does_not_apply_deployment_specific_path_policy() -> None:
    result = DBackupService(FakeClient()).job_plan(
        spec(sources=[JobSourceSpec(config_id="src1", path="/cache/application")])
    )
    assert result["warnings"] == []
