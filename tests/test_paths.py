import pytest

from app.errors import UnsafePath
from app.services.paths import resolve_for_create, resolve_managed, safe_identifier, safe_site_name


def test_resolve_inside_root(www_root):
    target = www_root / "site-a"
    target.mkdir()
    assert resolve_managed(str(target)) == target.resolve()


def test_traversal_is_rejected(www_root):
    with pytest.raises(UnsafePath):
        resolve_managed(f"{www_root}/../../etc/passwd")


def test_absolute_outside_root_is_rejected():
    with pytest.raises(UnsafePath):
        resolve_managed("/etc/shadow")


def test_relative_path_is_rejected():
    with pytest.raises(UnsafePath):
        resolve_managed("wwwroot/site")


def test_null_byte_is_rejected(www_root):
    with pytest.raises(UnsafePath):
        resolve_managed(f"{www_root}/a\x00b")


def test_resolve_for_create_requires_managed_parent(www_root):
    assert resolve_for_create(f"{www_root}/new.txt").name == "new.txt"
    with pytest.raises(UnsafePath):
        resolve_for_create("/etc/new.txt")


def test_symlink_escape_is_rejected(www_root, tmp_root):
    outside = tmp_root / "outside"
    outside.mkdir(exist_ok=True)
    link = www_root / "escape"
    if not link.exists():
        link.symlink_to(outside)
    with pytest.raises(UnsafePath):
        resolve_managed(str(link))


@pytest.mark.parametrize("name", ["", "../etc", "Site Name", "a" * 300, ".hidden", "-lead"])
def test_invalid_site_names(name):
    with pytest.raises(UnsafePath):
        safe_site_name(name)


def test_valid_site_name():
    assert safe_site_name("Example.COM") == "example.com"


@pytest.mark.parametrize("name", ["", "drop table", "db-name", "a;b", "`x`"])
def test_invalid_identifiers(name):
    with pytest.raises(UnsafePath):
        safe_identifier(name)


def test_valid_identifier():
    assert safe_identifier("my_db1") == "my_db1"
