import io


def test_list_dir(client, www_root):
    (www_root / "listme").mkdir(exist_ok=True)
    response = client.get("/api/files/list", params={"path": str(www_root)})
    assert response.status_code == 200
    assert "listme" in [entry["name"] for entry in response.json()["entries"]]


def test_write_then_read(client, www_root):
    target = www_root / "note.txt"
    written = client.post("/api/files/write", json={"path": str(target), "content": "hello"})
    assert written.status_code == 200

    read = client.get("/api/files/read", params={"path": str(target)})
    assert read.json()["content"] == "hello"


def test_traversal_is_blocked(client, www_root):
    response = client.get("/api/files/read", params={"path": f"{www_root}/../../etc/passwd"})
    assert response.status_code == 403


def test_reading_outside_root_is_blocked(client):
    assert client.get("/api/files/read", params={"path": "/etc/passwd"}).status_code == 403


def test_mkdir_move_copy_delete(client, www_root):
    base = str(www_root / "ops")
    assert client.post("/api/files/mkdir", json={"path": base, "content": ""}).status_code == 200

    client.post("/api/files/write", json={"path": f"{base}/a.txt", "content": "a"})
    assert client.post(
        "/api/files/copy", json={"source": f"{base}/a.txt", "target": f"{base}/b.txt"}
    ).status_code == 200
    assert client.post(
        "/api/files/move", json={"source": f"{base}/b.txt", "target": f"{base}/c.txt"}
    ).status_code == 200

    names = [e["name"] for e in client.get("/api/files/list", params={"path": base}).json()["entries"]]
    assert sorted(names) == ["a.txt", "c.txt"]

    assert client.delete("/api/files", params={"path": f"{base}/c.txt"}).status_code == 200


def test_chmod(client, www_root):
    target = www_root / "perm.txt"
    client.post("/api/files/write", json={"path": str(target), "content": "x"})
    response = client.post("/api/files/chmod", json={"path": str(target), "mode": "640"})
    assert response.json()["mode"] == "640"

    bad = client.post("/api/files/chmod", json={"path": str(target), "mode": "oops"})
    assert bad.status_code == 400


def test_compress_and_extract(client, www_root):
    src = www_root / "archive-src"
    src.mkdir(exist_ok=True)
    (src / "inner.txt").write_text("content")

    archive = str(www_root / "bundle.zip")
    assert client.post(
        "/api/files/compress", json={"paths": [str(src)], "target": archive}
    ).status_code == 200

    out = str(www_root / "unpacked")
    assert client.post(
        "/api/files/extract", json={"archive": archive, "target": out}
    ).status_code == 200
    assert (www_root / "unpacked" / "archive-src" / "inner.txt").read_text() == "content"


def test_upload_and_download(client, www_root):
    response = client.post(
        "/api/files/upload",
        data={"path": str(www_root)},
        files={"upload_file": ("uploaded.txt", io.BytesIO(b"payload"), "text/plain")},
    )
    assert response.status_code == 200
    assert (www_root / "uploaded.txt").read_bytes() == b"payload"

    download = client.get("/api/files/download", params={"path": str(www_root / "uploaded.txt")})
    assert download.content == b"payload"


def test_tail(client, www_root):
    target = www_root / "tail.log"
    target.write_text("\n".join(f"line {i}" for i in range(500)))
    lines = client.get("/api/files/tail", params={"path": str(target), "lines": 10}).json()["lines"]
    assert len(lines) == 10
    assert lines[-1] == "line 499"


def test_roots_are_exposed(client, www_root):
    roots = client.get("/api/files/roots").json()["roots"]
    assert str(www_root) in roots
