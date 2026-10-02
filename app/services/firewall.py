from __future__ import annotations

import ipaddress
import re
import shutil

from sqlmodel import Session, select

from app.config import settings
from app.errors import NotFound, PanelError
from app.models import FirewallRule, IpRule
from app.services import shell

PORT_PATTERN = re.compile(r"^\d{1,5}(?::\d{1,5})?$")
PROTOCOLS = {"tcp", "udp", "both"}
ACTIONS = {"accept", "drop"}


def backend() -> str:
    """ufw, firewalld or iptables, whichever this host actually runs."""
    configured = (settings.firewall_backend or "auto").strip().lower()
    if configured and configured != "auto":
        return configured
    if shutil.which("ufw"):
        return "ufw"
    if shutil.which("firewall-cmd"):
        return "firewalld"
    if shutil.which("iptables"):
        return "iptables"
    return "none"


def validate_port(port: str) -> str:
    cleaned = port.strip().replace("-", ":")
    if not PORT_PATTERN.match(cleaned):
        raise PanelError("Port must be 80 or a range like 8000:8100")
    for part in cleaned.split(":"):
        if not 1 <= int(part) <= 65535:
            raise PanelError("Port out of range")
    return cleaned


def validate_source(source: str) -> str:
    cleaned = source.strip()
    if not cleaned:
        return ""
    try:
        ipaddress.ip_network(cleaned, strict=False)
    except ValueError as exc:
        raise PanelError(f"'{cleaned}' is not an IP address or CIDR block") from exc
    return cleaned


def status() -> dict:
    kind = backend()
    if kind == "ufw":
        result = shell.run(["ufw", "status", "verbose"], timeout=20)
        active = "Status: active" in result.stdout
    elif kind == "firewalld":
        result = shell.run(["firewall-cmd", "--state"], timeout=20)
        active = "running" in result.output
    elif kind == "iptables":
        result = shell.run(["iptables", "-S"], timeout=20)
        active = result.ok
    else:
        return {"backend": "none", "active": False, "raw": "No firewall tool found on this host"}
    return {"backend": kind, "active": active, "raw": result.output[:8000]}


def toggle(enabled: bool) -> shell.Result:
    kind = backend()
    if kind == "ufw":
        return shell.run(["ufw", "--force", "enable" if enabled else "disable"], timeout=60)
    if kind == "firewalld":
        action = "start" if enabled else "stop"
        return shell.run([settings.systemctl_bin, action, "firewalld"], timeout=60)
    raise PanelError(f"The {kind} backend has no enable switch the panel can flip safely")


def _protocols(rule: FirewallRule) -> list[str]:
    return ["tcp", "udp"] if rule.protocol == "both" else [rule.protocol]


def _apply_rule(rule: FirewallRule, remove: bool = False) -> list[str]:
    kind = backend()
    outputs = []
    for protocol in _protocols(rule):
        if kind == "ufw":
            verb = "delete " if remove else ""
            action = "allow" if rule.action == "accept" else "deny"
            if rule.source:
                command = f"ufw {verb}{action} from {rule.source} to any port {rule.port} proto {protocol}"
            else:
                command = f"ufw {verb}{action} {rule.port}/{protocol}"
            outputs.append(shell.run(command, timeout=30).output)
        elif kind == "firewalld":
            flag = "--remove-port" if remove else "--add-port"
            port = rule.port.replace(":", "-")
            if rule.source:
                rich = (
                    f'rule family="ipv4" source address="{rule.source}" '
                    f'port port="{port}" protocol="{protocol}" '
                    f'{"accept" if rule.action == "accept" else "drop"}'
                )
                flag = "--remove-rich-rule" if remove else "--add-rich-rule"
                outputs.append(
                    shell.run(["firewall-cmd", "--permanent", f"{flag}={rich}"], timeout=30).output
                )
            else:
                outputs.append(
                    shell.run(
                        ["firewall-cmd", "--permanent", f"{flag}={port}/{protocol}"], timeout=30
                    ).output
                )
            shell.run(["firewall-cmd", "--reload"], timeout=30)
        elif kind == "iptables":
            flag = "-D" if remove else "-I"
            argv = ["iptables", flag, "INPUT", "-p", protocol]
            if rule.source:
                argv += ["-s", rule.source]
            argv += ["--dport", rule.port.replace(":", ":"), "-j", "ACCEPT" if rule.action == "accept" else "DROP"]
            outputs.append(shell.run(argv, timeout=30).output)
        else:
            outputs.append("no firewall backend available")
    return outputs


def list_rules(session: Session) -> list[FirewallRule]:
    return list(session.exec(select(FirewallRule).order_by(FirewallRule.id)).all())


def get_rule(session: Session, rule_id: int) -> FirewallRule:
    rule = session.get(FirewallRule, rule_id)
    if not rule:
        raise NotFound("Firewall rule not found")
    return rule


def create_rule(
    session: Session,
    port: str,
    protocol: str = "tcp",
    action: str = "accept",
    source: str = "",
    name: str = "",
) -> FirewallRule:
    if protocol not in PROTOCOLS:
        raise PanelError("Protocol must be tcp, udp or both")
    if action not in ACTIONS:
        raise PanelError("Action must be accept or drop")

    rule = FirewallRule(
        name=name.strip(),
        port=validate_port(port),
        protocol=protocol,
        action=action,
        source=validate_source(source),
    )
    if session.exec(
        select(FirewallRule).where(
            FirewallRule.port == rule.port,
            FirewallRule.protocol == rule.protocol,
            FirewallRule.source == rule.source,
        )
    ).first():
        raise PanelError("An identical rule already exists")

    session.add(rule)
    session.commit()
    session.refresh(rule)
    _apply_rule(rule)
    return rule


def delete_rule(session: Session, rule_id: int) -> None:
    rule = get_rule(session, rule_id)
    _apply_rule(rule, remove=True)
    session.delete(rule)
    session.commit()


def set_rule_enabled(session: Session, rule_id: int, enabled: bool) -> FirewallRule:
    rule = get_rule(session, rule_id)
    _apply_rule(rule, remove=not enabled)
    rule.enabled = enabled
    session.add(rule)
    session.commit()
    session.refresh(rule)
    return rule


def sync(session: Session) -> dict:
    """Re-apply every enabled rule. Useful after a reboot or a backend change."""
    applied = 0
    for rule in list_rules(session):
        if rule.enabled:
            _apply_rule(rule)
            applied += 1
    return {"backend": backend(), "applied": applied}


def _apply_ip(rule: IpRule, remove: bool = False) -> str:
    kind = backend()
    if kind == "ufw":
        verb = "delete " if remove else ""
        action = "allow" if rule.action == "accept" else "deny"
        return shell.run(f"ufw {verb}{action} from {rule.address}", timeout=30).output
    if kind == "firewalld":
        if rule.action == "accept":
            flag = "--remove-source" if remove else "--add-source"
            return shell.run(
                ["firewall-cmd", "--permanent", "--zone=trusted", f"{flag}={rule.address}"], timeout=30
            ).output
        rich = f'rule family="ipv4" source address="{rule.address}" drop'
        flag = "--remove-rich-rule" if remove else "--add-rich-rule"
        output = shell.run(["firewall-cmd", "--permanent", f"{flag}={rich}"], timeout=30).output
        shell.run(["firewall-cmd", "--reload"], timeout=30)
        return output
    if kind == "iptables":
        flag = "-D" if remove else "-I"
        return shell.run(
            ["iptables", flag, "INPUT", "-s", rule.address, "-j", "ACCEPT" if rule.action == "accept" else "DROP"],
            timeout=30,
        ).output
    return "no firewall backend available"


def list_ip_rules(session: Session, scope: str = "") -> list[IpRule]:
    statement = select(IpRule).order_by(IpRule.id.desc())
    if scope:
        statement = statement.where(IpRule.scope == scope)
    return list(session.exec(statement).all())


def create_ip_rule(
    session: Session, address: str, action: str = "drop", scope: str = "server", note: str = ""
) -> IpRule:
    if action not in ACTIONS:
        raise PanelError("Action must be accept or drop")
    if scope not in {"server", "panel"}:
        raise PanelError("Scope must be server or panel")

    rule = IpRule(address=validate_source(address), action=action, scope=scope, note=note)
    if not rule.address:
        raise PanelError("An IP address is required")
    if session.exec(
        select(IpRule).where(IpRule.address == rule.address, IpRule.scope == scope)
    ).first():
        raise PanelError("That address already has a rule in this scope")

    session.add(rule)
    session.commit()
    session.refresh(rule)
    if scope == "server":
        _apply_ip(rule)
    return rule


def delete_ip_rule(session: Session, rule_id: int) -> None:
    rule = session.get(IpRule, rule_id)
    if not rule:
        raise NotFound("IP rule not found")
    if rule.scope == "server":
        _apply_ip(rule, remove=True)
    session.delete(rule)
    session.commit()


def panel_blocklist(session: Session) -> tuple[set[str], set[str]]:
    """Addresses the panel itself should refuse or allow, as CIDR strings."""
    allow, deny = set(), set()
    for rule in list_ip_rules(session, scope="panel"):
        (allow if rule.action == "accept" else deny).add(rule.address)
    return allow, deny


def ping_enabled() -> bool:
    result = shell.run(["sysctl", "-n", "net.ipv4.icmp_echo_ignore_all"], timeout=10)
    return result.stdout.strip() != "1"


def set_ping(enabled: bool) -> shell.Result:
    value = "0" if enabled else "1"
    result = shell.run(["sysctl", "-w", f"net.ipv4.icmp_echo_ignore_all={value}"], timeout=10)
    if result.ok and not settings.dry_run:
        _persist_sysctl("net.ipv4.icmp_echo_ignore_all", value)
    return result


def _persist_sysctl(key: str, value: str) -> None:
    from pathlib import Path

    target = Path("/etc/sysctl.d/99-slimpanel.conf")
    lines = []
    if target.exists():
        lines = [line for line in target.read_text().splitlines() if not line.startswith(f"{key}")]
    lines.append(f"{key} = {value}")
    try:
        target.write_text("\n".join(lines) + "\n")
    except OSError:
        pass


def listening_ports() -> list[dict]:
    """Which ports are actually open, so a rule list can be checked against reality."""
    import psutil

    rows = {}
    for conn in psutil.net_connections(kind="inet"):
        if conn.status != psutil.CONN_LISTEN or not conn.laddr:
            continue
        name = ""
        if conn.pid:
            try:
                name = psutil.Process(conn.pid).name()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                name = ""
        key = (conn.laddr.port, name)
        rows[key] = {
            "port": conn.laddr.port,
            "address": conn.laddr.ip,
            "pid": conn.pid or 0,
            "process": name,
            "family": "ipv6" if ":" in conn.laddr.ip else "ipv4",
        }
    return sorted(rows.values(), key=lambda row: row["port"])
