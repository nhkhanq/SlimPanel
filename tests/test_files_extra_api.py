"""Recycle bin, search, ownership, archives and upload streaming."""
from __future__ import annotations

import io
import tarfile
import zipfile
from pathlib import Path

import pytest

from app.config import settings


def test_roots_report_the_recycle_bin_state(client):
    body = client.get("/api/files/roots").json()
    assert body["recycle_bin"] is True
    assert body["www_root"]


def test_read_reports_an_editor_mode(client, www_root):
    (www_root / "site.conf").write_text("server {}")
    body = client.get("/api/files/read", params={"path": str(www_root / "site.conf")}).json()
    assert body["mode"] == "nginx"
    assert body["stat"]["name"] == "site.conf"


@pytest.mark.parametrize(
    "name,mode",
    [("a.py", "python"), ("a.ts", "typescript"), ("Dockerfile", "shell"), (".env", "ini"),
     ("a.unknown", "text")],
)
def test_editor_modes_cover_the_common_cases(client, www_root, name, mode):
    (www_root / name).write_text("x")
    body = client.get("/api/files/read", params={"path": str(www_root / name)}).json()
    assert body["mode"] == mode


def test_delete_moves_to_the_recycle_bin_and_restores(client, www_root):
    target = www_root / "bin-me.txt"
    target.write_text("keep me")

    deleted = client.delete("/api/files", params={"path": str(target)})
    assert deleted.status_code == 200
    assert "recycle bin" in deleted.json()["message"]
    assert not target.exists()

    items = client.get("/api/recycle").json()
    assert len(items) == 1
    assert items[0]["original_path"] == str(target)

    restored = client.post(f"/api/recycle/{items[0]['id']}/restore")
    assert restored.status_code == 200
    assert target.read_text() == "keep me"
    assert client.get("/api/recycle").json() == []


def test_force_delete_skips_the_bin(client, www_root):
    target = www_root / "gone.txt"
    target.write_text("x")

    body = client.delete("/api/files", params={"path": str(target), "force": True}).json()
    assert "Deleted" in body["message"]
    assert client.get("/api/recycle").json() == []


def test_restoring_over_an_existing_file_needs_overwrite(client, www_root):
    target = www_root / "clash.txt"
    target.write_text("original")
    client.delete("/api/files", params={"path": str(target)})

    target.write_text("new content")
    item = client.get("/api/recycle").json()[0]

    assert client.post(f"/api/recycle/{item['id']}/restore").status_code == 409
    assert client.post(
        f"/api/recycle/{item['id']}/restore", params={"overwrite": True}
    ).status_code == 200
    assert target.read_text() == "original"


def test_a_binned_directory_keeps_its_contents(client, www_root):
    directory = www_root / "tree"
    (directory / "deep").mkdir(parents=True)
    (directory / "deep" / "file.txt").write_text("nested")

    client.delete("/api/files", params={"path": str(directory)})
    item = client.get("/api/recycle").json()[0]
    assert item["is_dir"] is True
    assert item["size"] == len("nested")

    client.post(f"/api/recycle/{item['id']}/restore")
    assert (directory / "deep" / "file.txt").read_text() == "nested"


def test_emptying_the_bin_removes_the_stored_copies(client, www_root):
    for index in range(3):
        target = www_root / f"junk{index}.txt"
        target.write_text("x")
        client.delete("/api/files", params={"path": str(target)})

    usage = client.get("/api/recycle/usage").json()
    assert usage["count"] == 3

    body = client.delete("/api/recycle").json()
    assert "Emptied 3" in body["message"]
    assert not any(settings.recycle_dir.iterdir())


def test_usage_accounts_for_orphaned_copies(client, www_root):
    """A stored copy whose row is gone still takes disk, so it has to be visible."""
    stray = settings.recycle_dir / "deadbeef_orphan.txt"
    stray.write_text("x" * 128)

    usage = client.get("/api/recycle/usage").json()
    assert usage["orphans"] == 1
    assert usage["orphan_bytes"] == 128

    client.delete("/api/recycle")
    assert not stray.exists()


def test_batch_delete_reports_each_path(client, www_root):
    good = www_root / "one.txt"
    good.write_text("x")

    results = client.post(
        "/api/files/delete-many",
        json={"paths": [str(good), "/etc/shadow", str(www_root / "missing.txt")]},
    ).json()

    assert results[0]["ok"] is True
    assert results[1]["ok"] is False  # outside the managed roots
    assert results[2]["ok"] is False  # does not exist


def test_search_matches_by_name_and_content(client, www_root):
    directory = www_root / "searchme"
    directory.mkdir()
    (directory / "a.php").write_text("needle in here")
    (directory / "b.php").write_text("nothing")
    (directory / "c.txt").write_text("needle")

    by_name = client.post(
        "/api/files/search", json={"root": str(directory), "pattern": "*.php"}
    ).json()
    assert {Path(m["path"]).name for m in by_name["matches"]} == {"a.php", "b.php"}

    by_both = client.post(
        "/api/files/search", json={"root": str(directory), "pattern": "*.php", "contains": "needle"}
    ).json()
    assert {Path(m["path"]).name for m in by_both["matches"]} == {"a.php"}


def test_search_needs_something_to_match_on(client, www_root):
    response = client.post("/api/files/search", json={"root": str(www_root)})
    assert response.status_code == 400


def test_search_stays_inside_the_managed_roots(client):
    response = client.post("/api/files/search", json={"root": "/etc", "pattern": "*"})
    assert response.status_code == 403


def test_disk_usage_ranks_the_biggest_children(client, www_root):
    directory = www_root / "usage"
    directory.mkdir()
    (directory / "small").mkdir()
    (directory / "small" / "f").write_text("x" * 10)
    (directory / "big").mkdir()
    (directory / "big" / "f").write_text("x" * 5000)

    body = client.get("/api/files/usage", params={"path": str(directory)}).json()
    assert body["entries"][0]["name"] == "big"
    assert body["total"] == 5010


def test_zip_and_tar_archives_both_work(client, www_root):
    directory = www_root / "arch"
    directory.mkdir()
    (directory / "a.txt").write_text("alpha")
    (directory / "b.txt").write_text("beta")

    for name, opener in (("out.zip", zipfile.ZipFile), ("out.tar.gz", tarfile.open)):
        created = client.post(
            "/api/files/compress",
            json={"paths": [str(directory / "a.txt"), str(directory / "b.txt")],
                  "target": str(www_root / name)},
        )
        assert created.status_code == 200, created.text
        assert (www_root / name).is_file()

        listing = client.get("/api/files/archive", params={"path": str(www_root / name)}).json()
        assert {Path(entry["name"]).name for entry in listing["entries"]} == {"a.txt", "b.txt"}


def test_an_unknown_archive_suffix_is_refused(client, www_root):
    (www_root / "x.txt").write_text("x")
    response = client.post(
        "/api/files/compress", json={"paths": [str(www_root / "x.txt")], "target": str(www_root / "a.rar")}
    )
    assert response.status_code == 400


def test_compressing_nothing_is_refused(client, www_root):
    response = client.post(
        "/api/files/compress", json={"paths": [], "target": str(www_root / "empty.zip")}
    )
    assert response.status_code == 400


def test_tar_extraction_refuses_an_escaping_entry(client, www_root):
    evil = www_root / "evil.tar"
    with tarfile.open(evil, "w") as archive:
        payload = io.BytesIO(b"pwned")
        info = tarfile.TarInfo("../../escaped.txt")
        info.size = len(payload.getvalue())
        archive.addfile(info, payload)

    response = client.post(
        "/api/files/extract", json={"archive": str(evil), "target": str(www_root / "out")}
    )
    assert response.status_code == 403
    assert not (www_root.parent / "escaped.txt").exists()


def test_tar_extraction_refuses_a_link_entry(client, www_root):
    evil = www_root / "link.tar"
    with tarfile.open(evil, "w") as archive:
        info = tarfile.TarInfo("sneaky")
        info.type = tarfile.SYMTYPE
        info.linkname = "/etc/passwd"
        archive.addfile(info)

    response = client.post(
        "/api/files/extract", json={"archive": str(evil), "target": str(www_root / "out2")}
    )
    assert response.status_code == 403


def test_extracting_a_plain_file_is_refused(client, www_root):
    (www_root / "notanarchive.bin").write_bytes(b"\x00\x01\x02")
    response = client.post(
        "/api/files/extract",
        json={"archive": str(www_root / "notanarchive.bin"), "target": str(www_root / "out3")},
    )
    assert response.status_code == 400


def test_duplicate_picks_a_free_name(client, www_root):
    original = www_root / "dup.txt"
    original.write_text("content")

    first = client.post("/api/files/duplicate", params={"path": str(original)}).json()
    assert first["name"] == "dup_copy.txt"

    second = client.post("/api/files/duplicate", params={"path": str(original)}).json()
    assert second["name"] == "dup_copy2.txt"


def test_chown_rejects_an_unknown_user(client, www_root):
    (www_root / "owned.txt").write_text("x")
    response = client.post(
        "/api/files/chown",
        json={"path": str(www_root / "owned.txt"), "owner": "nosuchuser-xyz"},
    )
    assert response.status_code == 400


def test_remote_download_only_takes_http(client, www_root):
    for url in ("file:///etc/passwd", "ftp://host/x", "javascript:x"):
        response = client.post(
            "/api/files/remote-download", json={"path": str(www_root), "url": url}
        )
        assert response.status_code == 400, url


def test_remote_download_filename_cannot_escape(client, www_root):
    response = client.post(
        "/api/files/remote-download",
        json={"path": str(www_root), "url": "http://example.test/x", "filename": "../evil"},
    )
    assert response.status_code == 403


def test_upload_streams_to_disk(client, www_root):
    body = b"x" * (3 * 1024 * 1024)  # larger than one chunk
    response = client.post(
        "/api/files/upload",
        data={"path": str(www_root)},
        files={"upload_file": ("big.bin", body, "application/octet-stream")},
    )
    assert response.status_code == 200, response.text
    assert (www_root / "big.bin").stat().st_size == len(body)


def test_upload_filename_cannot_escape(client, www_root):
    response = client.post(
        "/api/files/upload",
        data={"path": str(www_root)},
        files={"upload_file": ("../escape.txt", b"x", "text/plain")},
    )
    assert response.status_code == 403
    assert not (www_root.parent / "escape.txt").exists()


def test_write_many_reports_per_entry(client, www_root):
    results = client.post(
        "/api/files/write-many",
        json={"entries": [
            {"path": str(www_root / "ok.txt"), "content": "fine"},
            {"path": "/etc/nope.txt", "content": "no"},
        ]},
    ).json()
    assert results[0]["ok"] is True
    assert results[1]["ok"] is False
