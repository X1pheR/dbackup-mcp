from __future__ import annotations

from dbackup_mcp.models import ArchiveBrowseInput, RestoreFilesInput
from dbackup_mcp.service import DBackupService


class RecordingClient:
    def __init__(self):
        self.calls = []

    def request(self, method, path, *, query=None, body=None):
        self.calls.append((method, path, query, body))
        return {"success": True}


def test_archive_browse_uses_v32_job_source_and_prefix_contract() -> None:
    client = RecordingClient()
    service = DBackupService(client)
    args = ArchiveBrowseInput(id="storage1", file="job/backup.tar.gz", job_source_id="source-link", prefix="subdir")
    service.archive_browse(args)
    assert client.calls[-1] == (
        "POST",
        "/storage/storage1/browse-archive",
        None,
        {"file": "job/backup.tar.gz", "jobSourceId": "source-link", "prefix": "subdir"},
    )


def test_restore_files_uses_v32_selection_and_storage_target_contract() -> None:
    client = RecordingClient()
    service = DBackupService(client)
    args = RestoreFilesInput(
        id="storage1",
        file="job/backup.tar.gz",
        selections=[{"src": "source-link", "paths": ["folder/file.txt"]}],
        target_config_id="restore-target",
        target_base_path="restore-test",
        confirm=True,
    )
    service.restore_files(args)
    assert client.calls[-1] == (
        "POST",
        "/storage/storage1/restore-files",
        None,
        {
            "file": "job/backup.tar.gz",
            "selections": [{"src": "source-link", "paths": ["folder/file.txt"]}],
            "target": {"kind": "storage", "configId": "restore-target", "basePath": "restore-test"},
        },
    )


def test_restore_files_dry_run_does_not_require_confirmation() -> None:
    client = RecordingClient()
    service = DBackupService(client)
    args = RestoreFilesInput(
        id="storage1",
        file="job/backup.tar.gz",
        selections=[{"src": "source-link"}],
        target_config_id="restore-target",
        target_base_path="restore-test",
        dry_run=True,
    )
    service.restore_files(args)
    assert client.calls[-1][3]["dryRun"] is True
