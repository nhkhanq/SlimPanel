from __future__ import annotations

import re
from collections import Counter
from datetime import datetime
from pathlib import Path

from sqlmodel import Session

from app.config import settings
from app.errors import NotFound
from app.services.sites import get_site

# nginx's combined format, which is what SlimPanel's vhosts write.
COMBINED = re.compile(
    r'^(?P<ip>\S+) \S+ \S+ \[(?P<time>[^\]]+)\] "(?P<method>[A-Z]+) (?P<path>[^ "]*)[^"]*" '
    r"(?P<status>\d{3}) (?P<bytes>\d+|-)"
    r'(?: "(?P<referer>[^"]*)" "(?P<agent>[^"]*)")?'
)

SPIDERS = {
    "Googlebot": "Google",
    "bingbot": "Bing",
    "Baiduspider": "Baidu",
    "YandexBot": "Yandex",
    "DuckDuckBot": "DuckDuckGo",
    "Sogou": "Sogou",
    "360Spider": "360",
    "facebookexternalhit": "Facebook",
    "Twitterbot": "Twitter",
    "AhrefsBot": "Ahrefs",
    "SemrushBot": "Semrush",
    "MJ12bot": "Majestic",
    "GPTBot": "OpenAI",
    "ClaudeBot": "Anthropic",
    "PetalBot": "Petal",
    "Applebot": "Apple",
}


def _log_path(session: Session, site_id: int, kind: str) -> Path:
    site = get_site(session, site_id)
    suffix = ".error.log" if kind == "error" else ".log"
    return settings.log_root / f"{site.name}{suffix}"


def _read_tail(path: Path, max_lines: int) -> list[str]:
    if not path.is_file():
        raise NotFound(f"{path} not found")
    block = 1 << 20
    size = path.stat().st_size
    chunks: list[bytes] = []
    with path.open("rb") as handle:
        remaining = size
        while remaining > 0 and sum(chunk.count(b"\n") for chunk in chunks) <= max_lines:
            step = min(block, remaining)
            remaining -= step
            handle.seek(remaining)
            chunks.insert(0, handle.read(step))
    return b"".join(chunks).decode("utf-8", errors="replace").splitlines()[-max_lines:]


def _parse_time(raw: str) -> datetime | None:
    try:
        return datetime.strptime(raw.split()[0], "%d/%b/%Y:%H:%M:%S")
    except (ValueError, IndexError):
        return None


def analyse(session: Session, site_id: int, max_lines: int = 50000, top: int = 20) -> dict:
    """Summarise a site's access log: the numbers aaPanel's log report shows."""
    path = _log_path(session, site_id, "access")
    lines = _read_tail(path, max_lines)

    ips: Counter[str] = Counter()
    paths: Counter[str] = Counter()
    statuses: Counter[str] = Counter()
    methods: Counter[str] = Counter()
    referers: Counter[str] = Counter()
    agents: Counter[str] = Counter()
    spiders: Counter[str] = Counter()
    hours: Counter[str] = Counter()
    traffic_by_path: Counter[str] = Counter()

    parsed = 0
    total_bytes = 0
    first_time = last_time = None

    for line in lines:
        match = COMBINED.match(line)
        if not match:
            continue
        parsed += 1
        data = match.groupdict()

        ips[data["ip"]] += 1
        request_path = (data["path"] or "/").split("?", 1)[0]
        paths[request_path] += 1
        statuses[data["status"]] += 1
        methods[data["method"]] += 1

        size = 0 if data["bytes"] in {"-", None} else int(data["bytes"])
        total_bytes += size
        traffic_by_path[request_path] += size

        referer = (data.get("referer") or "").strip()
        if referer and referer != "-":
            referers[referer] += 1

        agent = (data.get("agent") or "").strip()
        if agent and agent != "-":
            agents[agent[:120]] += 1
            for needle, label in SPIDERS.items():
                if needle.lower() in agent.lower():
                    spiders[label] += 1
                    break

        stamp = _parse_time(data["time"])
        if stamp:
            hours[stamp.strftime("%Y-%m-%d %H:00")] += 1
            first_time = stamp if first_time is None else min(first_time, stamp)
            last_time = stamp if last_time is None else max(last_time, stamp)

    def rows(counter: Counter, label: str) -> list[dict]:
        return [{label: key, "count": value} for key, value in counter.most_common(top)]

    error_rate = 0.0
    if parsed:
        errors = sum(count for code, count in statuses.items() if code.startswith(("4", "5")))
        error_rate = round(100 * errors / parsed, 2)

    return {
        "path": str(path),
        "lines_read": len(lines),
        "parsed": parsed,
        "unique_visitors": len(ips),
        "total_bytes": total_bytes,
        "error_rate": error_rate,
        "from": first_time.isoformat() if first_time else "",
        "to": last_time.isoformat() if last_time else "",
        "top_ips": rows(ips, "ip"),
        "top_paths": rows(paths, "path"),
        "top_referers": rows(referers, "referer"),
        "top_agents": rows(agents, "agent"),
        "statuses": [{"status": k, "count": v} for k, v in sorted(statuses.items())],
        "methods": [{"method": k, "count": v} for k, v in methods.most_common()],
        "spiders": [{"spider": k, "count": v} for k, v in spiders.most_common()],
        "hourly": [{"hour": k, "count": v} for k, v in sorted(hours.items())][-48:],
        "heaviest_paths": [
            {"path": k, "bytes": v} for k, v in traffic_by_path.most_common(top)
        ],
    }


# The parts of an nginx error line that differ on every occurrence of the same
# fault: the timestamp, the worker pid, the connection serial, and the request
# particulars. Stripping them is what lets one fault read as one row.
_ERROR_NOISE = (
    (re.compile(r"^\d{4}/\d\d/\d\d \d\d:\d\d:\d\d "), ""),
    (re.compile(r"\b\d+#\d+: "), ""),
    (re.compile(r"\*\d+ "), ""),
    (re.compile(r'(?:, )?request: "[^"]*"'), ""),
    (re.compile(r"(?:, )?client: \S+?(?=,|$)"), ""),
    (re.compile(r"(?:, )?(?:host|server|upstream|referrer): \S+?(?=,|$)"), ""),
    (re.compile(r"\s+"), " "),
)


def normalise_error(line: str) -> str:
    """Reduce one error line to the fault it describes."""
    message = line
    for pattern, replacement in _ERROR_NOISE:
        message = pattern.sub(replacement, message)
    return message.strip().rstrip(",").strip()


def errors(session: Session, site_id: int, lines: int = 200) -> dict:
    """Group the error log by message, so a repeated fault reads as one row."""
    path = _log_path(session, site_id, "error")
    if not path.is_file():
        return {"path": str(path), "entries": [], "lines": []}

    body = _read_tail(path, max(lines, 2000))
    grouped: Counter[str] = Counter()
    for line in body:
        if not line.strip():
            continue
        grouped[normalise_error(line)[:200]] += 1

    return {
        "path": str(path),
        "lines": body[-lines:],
        "entries": [{"message": k, "count": v} for k, v in grouped.most_common(40)],
    }


def rotate(session: Session, site_id: int, kind: str = "access") -> dict:
    """Cut the log, keeping the previous content beside it."""
    path = _log_path(session, site_id, kind)
    if not path.is_file():
        raise NotFound(f"{path} not found")

    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    archive = path.with_name(f"{path.name}.{stamp}")
    size = path.stat().st_size
    archive.write_bytes(path.read_bytes())
    path.write_bytes(b"")

    from app.services import nginx

    nginx.reload_config()
    return {"path": str(path), "archive": str(archive), "bytes": size}


def truncate(session: Session, site_id: int, kind: str = "access") -> dict:
    path = _log_path(session, site_id, kind)
    if not path.is_file():
        raise NotFound(f"{path} not found")
    size = path.stat().st_size
    path.write_bytes(b"")
    return {"path": str(path), "freed": size}


def sizes(session: Session) -> list[dict]:
    """Every site's log footprint, so the biggest offender is obvious."""
    from app.services.sites import list_sites

    rows = []
    for site in list_sites(session):
        entry = {"site": site.name, "id": site.id, "access": 0, "error": 0}
        for kind, suffix in (("access", ".log"), ("error", ".error.log")):
            path = settings.log_root / f"{site.name}{suffix}"
            if path.is_file():
                entry[kind] = path.stat().st_size
        entry["total"] = entry["access"] + entry["error"]
        rows.append(entry)
    rows.sort(key=lambda row: row["total"], reverse=True)
    return rows
