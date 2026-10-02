from __future__ import annotations

import json
import smtplib
import ssl
import urllib.error
import urllib.request
from datetime import timedelta
from email.message import EmailMessage

from sqlmodel import Session, select

from app.config import settings
from app.errors import NotFound, PanelError
from app.models import AlertEvent, AlertRule, Certificate, MonitorSample, NotifyChannel, utcnow

KINDS = {"webhook", "email", "telegram", "dingtalk", "wecom", "slack"}
METRICS = {
    "cpu": "CPU usage %",
    "memory": "Memory usage %",
    "swap": "Swap usage %",
    "disk": "Root disk usage %",
    "load": "1-minute load average",
    "cert_expiry": "Days until a certificate expires",
    "service_down": "A managed service is not active",
}
OPERATORS = {">", ">=", "<", "<=", "=="}

REQUIRED_FIELDS = {
    "webhook": ["url"],
    "slack": ["url"],
    "dingtalk": ["url"],
    "wecom": ["url"],
    "telegram": ["token", "chat_id"],
    "email": ["host", "port", "username", "password", "to"],
}


# ------------------------------------------------------------------- channels


def list_channels(session: Session) -> list[dict]:
    rows = []
    for row in session.exec(select(NotifyChannel).order_by(NotifyChannel.id)).all():
        rows.append({**row.model_dump(), "config": _redact(row)})
    return rows


def _redact(channel: NotifyChannel) -> dict:
    config = _config(channel)
    return {
        key: ("********" if key in {"password", "token", "secret"} else value)
        for key, value in config.items()
    }


def _config(channel: NotifyChannel) -> dict:
    try:
        parsed = json.loads(channel.config or "{}")
    except ValueError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def get_channel(session: Session, channel_id: int) -> NotifyChannel:
    channel = session.get(NotifyChannel, channel_id)
    if not channel:
        raise NotFound("Notification channel not found")
    return channel


def create_channel(session: Session, name: str, kind: str, config: dict) -> NotifyChannel:
    if kind not in KINDS:
        raise PanelError(f"Channel kind must be one of {', '.join(sorted(KINDS))}")
    missing = [field for field in REQUIRED_FIELDS[kind] if not str(config.get(field, "")).strip()]
    if missing:
        raise PanelError(f"{kind} needs: {', '.join(missing)}")

    channel = NotifyChannel(name=name.strip() or kind, kind=kind, config=json.dumps(config))
    session.add(channel)
    session.commit()
    session.refresh(channel)
    return channel


def update_channel(session: Session, channel_id: int, name: str = "", config: dict | None = None,
                   enabled: bool | None = None) -> NotifyChannel:
    channel = get_channel(session, channel_id)
    if name:
        channel.name = name.strip()
    if config is not None:
        merged = _config(channel)
        for key, value in config.items():
            # The UI sends masked placeholders back for secrets it never saw.
            if value == "********":
                continue
            merged[key] = value
        channel.config = json.dumps(merged)
    if enabled is not None:
        channel.enabled = enabled

    session.add(channel)
    session.commit()
    session.refresh(channel)
    return channel


def delete_channel(session: Session, channel_id: int) -> None:
    channel = get_channel(session, channel_id)
    for rule in session.exec(select(AlertRule).where(AlertRule.channel_id == channel.id)).all():
        rule.channel_id = None
        session.add(rule)
    session.delete(channel)
    session.commit()


# ------------------------------------------------------------------- delivery


def _post_json(url: str, payload: dict, timeout: int = 15) -> str:
    if not url.startswith(("http://", "https://")):
        raise PanelError("Webhook URL must start with http:// or https://")
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "User-Agent": "SlimPanel"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310
        return response.read(4096).decode(errors="replace")


def send(channel: NotifyChannel, title: str, body: str) -> str:
    if settings.dry_run:
        return f"dry-run: would notify {channel.kind}"

    config = _config(channel)
    text = f"{title}\n\n{body}"

    try:
        if channel.kind == "webhook":
            return _post_json(config["url"], {"title": title, "body": body, "source": "SlimPanel"})
        if channel.kind == "slack":
            return _post_json(config["url"], {"text": text})
        if channel.kind == "dingtalk":
            return _post_json(
                config["url"], {"msgtype": "text", "text": {"content": f"SlimPanel: {text}"}}
            )
        if channel.kind == "wecom":
            return _post_json(config["url"], {"msgtype": "text", "text": {"content": text}})
        if channel.kind == "telegram":
            url = f"https://api.telegram.org/bot{config['token']}/sendMessage"
            return _post_json(url, {"chat_id": config["chat_id"], "text": text})
        if channel.kind == "email":
            return _send_email(config, title, body)
    except (urllib.error.URLError, OSError, KeyError, ValueError) as exc:
        raise PanelError(f"Delivery to {channel.name} failed: {exc}") from exc

    raise PanelError(f"Unknown channel kind '{channel.kind}'")


def _send_email(config: dict, title: str, body: str) -> str:
    message = EmailMessage()
    message["Subject"] = f"[SlimPanel] {title}"
    message["From"] = config.get("from") or config["username"]
    message["To"] = config["to"]
    message.set_content(body)

    port = int(config["port"])
    host = config["host"]
    if port == 465:
        with smtplib.SMTP_SSL(host, port, timeout=20, context=ssl.create_default_context()) as client:
            client.login(config["username"], config["password"])
            client.send_message(message)
    else:
        with smtplib.SMTP(host, port, timeout=20) as client:
            if config.get("starttls", True):
                client.starttls(context=ssl.create_default_context())
            client.login(config["username"], config["password"])
            client.send_message(message)
    return f"sent to {config['to']}"


def test_channel(session: Session, channel_id: int) -> dict:
    channel = get_channel(session, channel_id)
    detail = send(channel, "Test notification", "SlimPanel can reach this channel.")
    return {"ok": True, "detail": detail[:1000]}


def dispatch(session: Session, title: str, body: str, rule_id: int | None = None,
             channel_id: int | None = None) -> AlertEvent:
    """Record the alert, then try to deliver it. A failed send is still recorded."""
    event = AlertEvent(rule_id=rule_id, title=title, body=body)
    targets: list[NotifyChannel] = []
    if channel_id:
        channel = session.get(NotifyChannel, channel_id)
        if channel and channel.enabled:
            targets = [channel]
    else:
        targets = list(
            session.exec(select(NotifyChannel).where(NotifyChannel.enabled == True)).all()  # noqa: E712
        )

    notes = []
    for channel in targets:
        try:
            notes.append(f"{channel.name}: {send(channel, title, body)}")
            event.delivered = True
        except PanelError as exc:
            notes.append(f"{channel.name}: {exc.message}")
    if not targets:
        notes.append("no enabled channel")

    event.detail = "\n".join(notes)[:2000]
    session.add(event)
    session.commit()
    session.refresh(event)
    return event


# ----------------------------------------------------------------- alert rules


def list_rules(session: Session) -> list[AlertRule]:
    return list(session.exec(select(AlertRule).order_by(AlertRule.id)).all())


def get_rule(session: Session, rule_id: int) -> AlertRule:
    rule = session.get(AlertRule, rule_id)
    if not rule:
        raise NotFound("Alert rule not found")
    return rule


def metrics() -> list[dict]:
    return [{"key": key, "label": label} for key, label in METRICS.items()]


def create_rule(
    session: Session,
    name: str,
    metric: str,
    threshold: float,
    operator: str = ">",
    target: str = "",
    channel_id: int | None = None,
    cooldown_minutes: int = 60,
) -> AlertRule:
    if metric not in METRICS:
        raise PanelError(f"Metric must be one of {', '.join(METRICS)}")
    if operator not in OPERATORS:
        raise PanelError(f"Operator must be one of {', '.join(sorted(OPERATORS))}")
    if channel_id:
        get_channel(session, channel_id)

    rule = AlertRule(
        name=name.strip() or f"{metric} {operator} {threshold}",
        metric=metric,
        operator=operator,
        threshold=float(threshold),
        target=target.strip(),
        channel_id=channel_id,
        cooldown_minutes=max(1, cooldown_minutes),
    )
    session.add(rule)
    session.commit()
    session.refresh(rule)
    return rule


def update_rule(session: Session, rule_id: int, values: dict) -> AlertRule:
    rule = get_rule(session, rule_id)
    for field, value in values.items():
        if value is None or field not in {
            "name", "metric", "operator", "threshold", "target", "channel_id",
            "cooldown_minutes", "enabled",
        }:
            continue
        if field == "metric" and value not in METRICS:
            raise PanelError(f"Metric must be one of {', '.join(METRICS)}")
        if field == "operator" and value not in OPERATORS:
            raise PanelError("Invalid operator")
        setattr(rule, field, value)

    session.add(rule)
    session.commit()
    session.refresh(rule)
    return rule


def delete_rule(session: Session, rule_id: int) -> None:
    session.delete(get_rule(session, rule_id))
    session.commit()


def list_events(session: Session, limit: int = 100) -> list[AlertEvent]:
    return list(
        session.exec(select(AlertEvent).order_by(AlertEvent.id.desc()).limit(limit)).all()
    )


def _compare(value: float, operator: str, threshold: float) -> bool:
    return {
        ">": value > threshold,
        ">=": value >= threshold,
        "<": value < threshold,
        "<=": value <= threshold,
        "==": value == threshold,
    }[operator]


def _metric_value(session: Session, rule: AlertRule, latest: MonitorSample | None) -> tuple[float, str] | None:
    if rule.metric in {"cpu", "memory", "swap", "load", "disk"}:
        if not latest:
            return None
        value = {
            "cpu": latest.cpu,
            "memory": latest.memory,
            "swap": latest.swap,
            "load": latest.load1,
            "disk": latest.disk_percent,
        }[rule.metric]
        return float(value), f"{METRICS[rule.metric]} is {value}"

    if rule.metric == "cert_expiry":
        rows = session.exec(select(Certificate).where(Certificate.not_after != None)).all()  # noqa: E711
        soonest, label = None, ""
        for cert in rows:
            if rule.target and rule.target not in cert.domains:
                continue
            days = (cert.not_after - utcnow()).days
            if soonest is None or days < soonest:
                soonest, label = days, cert.domains
        if soonest is None:
            return None
        return float(soonest), f"{label} expires in {soonest} days"

    if rule.metric == "service_down":
        from app.services import system

        name = rule.target or "nginx"
        states = {row["name"]: row["state"] for row in system.services()}
        down = 0.0 if states.get(name) == "active" else 1.0
        return down, f"{name} is {states.get(name, 'unknown')}"

    return None


def evaluate(session: Session, latest: MonitorSample | None = None) -> list[AlertEvent]:
    """Check every enabled rule against the newest sample. Called by the sampler."""
    if latest is None:
        latest = session.exec(
            select(MonitorSample).order_by(MonitorSample.id.desc()).limit(1)
        ).first()

    fired = []
    now = utcnow()
    for rule in list_rules(session):
        if not rule.enabled:
            continue
        if rule.last_fired_at and now - rule.last_fired_at < timedelta(minutes=rule.cooldown_minutes):
            continue

        measured = _metric_value(session, rule, latest)
        if measured is None:
            continue
        value, description = measured
        if not _compare(value, rule.operator, rule.threshold):
            continue

        event = dispatch(
            session,
            title=f"{rule.name}",
            body=f"{description}\nRule: {rule.metric} {rule.operator} {rule.threshold}",
            rule_id=rule.id,
            channel_id=rule.channel_id,
        )
        rule.last_fired_at = now
        session.add(rule)
        session.commit()
        fired.append(event)
    return fired
