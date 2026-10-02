from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.deps import SessionDep, UserDep, audit
from app.models import FirewallRule, IpRule
from app.schemas import Ok
from app.services import firewall, safety, sshd

router = APIRouter(prefix="/security", tags=["security"])


class PortRule(BaseModel):
    port: str
    protocol: str = "tcp"
    action: str = "accept"
    source: str = ""
    name: str = ""


class IpRuleIn(BaseModel):
    address: str
    action: str = "drop"
    scope: str = "server"
    note: str = ""


class SshValues(BaseModel):
    values: dict[str, str]


class SshRaw(BaseModel):
    content: str


class SshKey(BaseModel):
    public_key: str
    user: str = "root"


# ------------------------------------------------------------------- firewall


@router.get("/firewall")
def firewall_status(user: UserDep):
    return firewall.status()


@router.post("/firewall/toggle", response_model=Ok)
def firewall_toggle(enabled: bool, session: SessionDep, user: UserDep):
    result = firewall.toggle(enabled)
    audit(session, user, "firewall.toggle", str(enabled), success=result.ok, detail=result.output)
    return Ok(ok=result.ok, message=result.output[:1000])


@router.get("/firewall/rules", response_model=list[FirewallRule])
def list_rules(session: SessionDep, user: UserDep):
    return firewall.list_rules(session)


@router.post("/firewall/rules", response_model=FirewallRule)
def create_rule(payload: PortRule, session: SessionDep, user: UserDep):
    rule = firewall.create_rule(
        session, payload.port, payload.protocol, payload.action, payload.source, payload.name
    )
    audit(session, user, "firewall.rule.create", f"{rule.port}/{rule.protocol}")
    return rule


@router.post("/firewall/rules/{rule_id}/enabled", response_model=FirewallRule)
def set_rule_enabled(rule_id: int, enabled: bool, session: SessionDep, user: UserDep):
    rule = firewall.set_rule_enabled(session, rule_id, enabled)
    audit(session, user, "firewall.rule.toggle", rule.port, detail=str(enabled))
    return rule


@router.delete("/firewall/rules/{rule_id}", response_model=Ok)
def delete_rule(rule_id: int, session: SessionDep, user: UserDep):
    rule = firewall.get_rule(session, rule_id)
    label = f"{rule.port}/{rule.protocol}"
    firewall.delete_rule(session, rule_id)
    audit(session, user, "firewall.rule.delete", label)
    return Ok(message=f"Rule {label} removed")


@router.post("/firewall/sync")
def sync_firewall(session: SessionDep, user: UserDep):
    result = firewall.sync(session)
    audit(session, user, "firewall.sync", detail=str(result))
    return result


@router.get("/firewall/ports")
def listening_ports(user: UserDep):
    return firewall.listening_ports()


# ------------------------------------------------------------------- ip rules


@router.get("/ip-rules", response_model=list[IpRule])
def list_ip_rules(session: SessionDep, user: UserDep, scope: str = ""):
    return firewall.list_ip_rules(session, scope)


@router.post("/ip-rules", response_model=IpRule)
def create_ip_rule(payload: IpRuleIn, session: SessionDep, user: UserDep):
    rule = firewall.create_ip_rule(
        session, payload.address, payload.action, payload.scope, payload.note
    )
    audit(session, user, "firewall.ip.create", rule.address, detail=f"{rule.action}/{rule.scope}")
    return rule


@router.delete("/ip-rules/{rule_id}", response_model=Ok)
def delete_ip_rule(rule_id: int, session: SessionDep, user: UserDep):
    firewall.delete_ip_rule(session, rule_id)
    audit(session, user, "firewall.ip.delete", str(rule_id))
    return Ok(message="IP rule removed")


@router.get("/ping")
def ping_status(user: UserDep):
    return {"enabled": firewall.ping_enabled()}


@router.post("/ping", response_model=Ok)
def set_ping(enabled: bool, session: SessionDep, user: UserDep):
    result = firewall.set_ping(enabled)
    audit(session, user, "firewall.ping", str(enabled), success=result.ok)
    return Ok(ok=result.ok, message=result.output[:500])


# ------------------------------------------------------------------------ ssh


@router.get("/ssh")
def ssh_config(user: UserDep):
    return sshd.read_config()


@router.post("/ssh")
def set_ssh(payload: SshValues, session: SessionDep, user: UserDep):
    info = sshd.set_values(payload.values)
    audit(session, user, "ssh.config", detail=", ".join(f"{k}={v}" for k, v in payload.values.items()))
    return info


@router.post("/ssh/raw")
def write_ssh(payload: SshRaw, session: SessionDep, user: UserDep):
    info = sshd.write_config(payload.content)
    audit(session, user, "ssh.config.raw")
    return info


@router.post("/ssh/restart", response_model=Ok)
def restart_ssh(session: SessionDep, user: UserDep):
    result = sshd.restart()
    audit(session, user, "ssh.restart", success=result.ok, detail=result.output)
    return Ok(ok=result.ok, message=result.output[:500])


@router.get("/ssh/keys")
def ssh_keys(user: UserDep, username: str = "root"):
    return sshd.list_keys(username)


@router.post("/ssh/keys")
def add_ssh_key(payload: SshKey, session: SessionDep, user: UserDep):
    keys = sshd.add_key(payload.public_key, payload.user)
    audit(session, user, "ssh.key.add", payload.user)
    return keys


@router.delete("/ssh/keys/{index}")
def remove_ssh_key(index: int, session: SessionDep, user: UserDep, username: str = "root"):
    keys = sshd.remove_key(index, username)
    audit(session, user, "ssh.key.remove", f"{username}#{index}")
    return keys


@router.get("/ssh/activity")
def ssh_activity(user: UserDep):
    return safety.ssh_overview()


# ----------------------------------------------------------------- audit/scan


@router.get("/audit")
def audit_report(session: SessionDep, user: UserDep):
    return safety.audit(session)


@router.get("/kernel")
def kernel(user: UserDep):
    return safety.kernel_hardening()


@router.get("/panel-files")
def panel_files(user: UserDep):
    return safety.panel_file_permissions()


@router.get("/login-attempts")
def login_attempts(session: SessionDep, user: UserDep):
    return safety.blocked_addresses(session)


@router.delete("/login-attempts/{ip}", response_model=Ok)
def clear_attempts(ip: str, session: SessionDep, user: UserDep):
    safety.clear_attempts(session, ip)
    audit(session, user, "security.unblock", ip)
    return Ok(message=f"{ip} unblocked")


@router.get("/scan/{site_id}")
def scan_site(site_id: int, session: SessionDep, user: UserDep, limit: int = 4000):
    report = safety.scan_site(session, site_id, min(limit, 20000))
    audit(session, user, "security.scan", report["site"], detail=f"{len(report['findings'])} findings")
    return report
