import tarfile


def test_site_backup_creates_archive(client, www_root):
    site = client.post(
        "/api/sites", json={"name": "backup.test", "site_type": "static", "domains": ["backup.test"]}
    ).json()
    (www_root / "backup.test" / "data.txt").write_text("payload")

    record = client.post(f"/api/backups/site/{site['id']}").json()
    assert record["kind"] == "site"
    assert record["size"] > 0

    with tarfile.open(record["filename"]) as archive:
        assert "backup.test/data.txt" in archive.getnames()


def test_backup_listing_and_download(client):
    site = client.post(
        "/api/sites", json={"name": "dl.test", "site_type": "static", "domains": ["dl.test"]}
    ).json()
    record = client.post(f"/api/backups/site/{site['id']}").json()

    listing = client.get("/api/backups").json()
    assert len(listing) == 1

    download = client.get(f"/api/backups/{record['id']}/download")
    assert download.status_code == 200
    assert len(download.content) == record["size"]


def test_backup_delete_removes_file(client):
    site = client.post(
        "/api/sites", json={"name": "rm.test", "site_type": "static", "domains": ["rm.test"]}
    ).json()
    record = client.post(f"/api/backups/site/{site['id']}").json()

    assert client.delete(f"/api/backups/{record['id']}").status_code == 200
    assert client.get("/api/backups").json() == []
    assert client.get(f"/api/backups/{record['id']}/download").status_code == 404


def test_prune_keeps_latest(client):
    site = client.post(
        "/api/sites", json={"name": "prune.test", "site_type": "static", "domains": ["prune.test"]}
    ).json()
    for _ in range(3):
        client.post(f"/api/backups/site/{site['id']}")

    client.post("/api/backups/prune", params={"keep": 1})
    assert len(client.get("/api/backups").json()) == 1


def test_database_create_and_drop_in_dry_run(client):
    created = client.post("/api/databases", json={"name": "app_db", "note": "demo"})
    assert created.status_code == 200, created.text
    record = created.json()
    assert record["username"] == "app_db"

    credentials = client.get(f"/api/databases/{record['id']}/credentials").json()
    assert len(credentials["password"]) == 16

    assert client.post("/api/databases", json={"name": "app_db"}).status_code == 409
    assert client.post("/api/databases", json={"name": "bad-name"}).status_code == 403

    assert client.delete(f"/api/databases/{record['id']}").status_code == 200
    assert client.get("/api/databases").json() == []


def test_operation_log_records_actions(client):
    client.post(
        "/api/sites", json={"name": "logged.test", "site_type": "static", "domains": ["logged.test"]}
    )
    actions = [row["action"] for row in client.get("/api/logs/operations").json()]
    assert "site.create" in actions
