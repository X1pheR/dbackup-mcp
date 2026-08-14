from __future__ import annotations

from dbackup_mcp.models import NotificationLogsInput
from dbackup_mcp.service import DBackupService


class RecordingClient:
    def __init__(self):
        self.calls = []

    def request(self, method, path, *, query=None, body=None):
        self.calls.append((method, path, query, body))
        return {"success": True}


def test_adapter_version_history_request_shape() -> None:
    client = RecordingClient()
    DBackupService(client).adapter_version_history("adapter1", 75)
    assert client.calls == [("GET", "/adapters/adapter1/version-history", {"limit": 75}, None)]


def test_notification_logs_request_shape() -> None:
    client = RecordingClient()
    args = NotificationLogsInput(page=2, page_size=25, adapter_id="notify1", event_type="FAILED", status="ERROR", execution_id="exec1")
    DBackupService(client).notification_logs(args)
    assert client.calls == [("GET", "/notification-logs", {"page": 2, "pageSize": 25, "adapterId": "notify1", "eventType": "FAILED", "status": "ERROR", "executionId": "exec1"}, None)]


def test_notification_log_get_request_shape() -> None:
    client = RecordingClient()
    DBackupService(client).notification_log_get("log1")
    assert client.calls == [("GET", "/notification-logs/log1", None, None)]


def test_storage_history_request_shape() -> None:
    client = RecordingClient()
    DBackupService(client).storage_history("storage1", 90)
    assert client.calls == [("GET", "/storage/storage1/history", {"days": 90}, None)]


def test_storage_check_path_request_shape() -> None:
    client = RecordingClient()
    DBackupService(client).storage_check_path("storage1", "restore-test")
    assert client.calls == [("POST", "/storage/storage1/check-path", None, {"path": "restore-test"})]


def test_capabilities_describes_supported_contract_without_secrets() -> None:
    result = DBackupService(RecordingClient()).capabilities()
    assert result["dbackupContract"] == "3.2.0"
    assert result["apiBoundary"]
    assert "credential_reveal" in result["excludedTools"]


class HistoryClient:
    def request(self, method, path, *, query=None, body=None):
        if path == "/history":
            return {"executions": [{"id": str(i)} for i in range(10)], "systemTimezone": "UTC"}
        if path == "/executions/exec1":
            return {"success": True, "data": {"id": "exec1", "logs": [{"n": i} for i in range(10)]}}
        raise AssertionError((method, path, query, body))


def test_history_list_enforces_requested_limit_on_dbackup_response() -> None:
    result = DBackupService(HistoryClient()).history_list(3)
    assert [item["id"] for item in result["executions"]] == ["0", "1", "2"]


def test_execution_get_bounds_model_visible_logs() -> None:
    result = DBackupService(HistoryClient()).execution_get("exec1", 3)
    assert result["data"]["logs"] == [{"n": 7}, {"n": 8}, {"n": 9}]


def test_execution_get_can_omit_logs() -> None:
    result = DBackupService(HistoryClient()).execution_get("exec1", 0)
    assert "logs" not in result["data"]


class BackupListClient:
    def __init__(self):
        self.calls = []

    def request(self, method, path, *, query=None, body=None):
        self.calls.append((method, path, query, body))
        return [{"path": f"backup-{i}"} for i in range(20)]


def test_backups_list_bounds_model_visible_results_and_forwards_type_filter() -> None:
    client = BackupListClient()
    result = DBackupService(client).backups_list("storage1", limit=3, type_filter="directory")
    assert [item["path"] for item in result] == ["backup-0", "backup-1", "backup-2"]
    assert client.calls == [("GET", "/storage/storage1/files", {"typeFilter": "directory"}, None)]
