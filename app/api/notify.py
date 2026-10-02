from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.deps import SessionDep, UserDep, audit
from app.models import AlertEvent, AlertRule
from app.schemas import Ok
from app.services import notify

router = APIRouter(prefix="/notify", tags=["notify"])


class ChannelIn(BaseModel):
    name: str
    kind: str
    config: dict


class ChannelUpdate(BaseModel):
    name: str = ""
    config: dict | None = None
    enabled: bool | None = None


class RuleIn(BaseModel):
    name: str = ""
    metric: str
    operator: str = ">"
    threshold: float
    target: str = ""
    channel_id: int | None = None
    cooldown_minutes: int = 60


class RuleUpdate(BaseModel):
    name: str | None = None
    metric: str | None = None
    operator: str | None = None
    threshold: float | None = None
    target: str | None = None
    channel_id: int | None = None
    cooldown_minutes: int | None = None
    enabled: bool | None = None


class MessageIn(BaseModel):
    title: str
    body: str = ""
    channel_id: int | None = None


@router.get("/channels")
def channels(session: SessionDep, user: UserDep):
    return notify.list_channels(session)


@router.post("/channels")
def create_channel(payload: ChannelIn, session: SessionDep, user: UserDep):
    channel = notify.create_channel(session, payload.name, payload.kind, payload.config)
    audit(session, user, "notify.channel.create", channel.name, detail=channel.kind)
    return {**channel.model_dump(exclude={"config"})}


@router.patch("/channels/{channel_id}")
def update_channel(channel_id: int, payload: ChannelUpdate, session: SessionDep, user: UserDep):
    channel = notify.update_channel(session, channel_id, payload.name, payload.config, payload.enabled)
    audit(session, user, "notify.channel.update", channel.name)
    return {**channel.model_dump(exclude={"config"})}


@router.post("/channels/{channel_id}/test")
def test_channel(channel_id: int, session: SessionDep, user: UserDep):
    result = notify.test_channel(session, channel_id)
    audit(session, user, "notify.channel.test", str(channel_id))
    return result


@router.delete("/channels/{channel_id}", response_model=Ok)
def delete_channel(channel_id: int, session: SessionDep, user: UserDep):
    channel = notify.get_channel(session, channel_id)
    name = channel.name
    notify.delete_channel(session, channel_id)
    audit(session, user, "notify.channel.delete", name)
    return Ok(message=f"Channel {name} removed")


@router.get("/metrics")
def metrics(user: UserDep):
    return notify.metrics()


@router.get("/rules", response_model=list[AlertRule])
def rules(session: SessionDep, user: UserDep):
    return notify.list_rules(session)


@router.post("/rules", response_model=AlertRule)
def create_rule(payload: RuleIn, session: SessionDep, user: UserDep):
    rule = notify.create_rule(
        session,
        payload.name,
        payload.metric,
        payload.threshold,
        payload.operator,
        payload.target,
        payload.channel_id,
        payload.cooldown_minutes,
    )
    audit(session, user, "notify.rule.create", rule.name)
    return rule


@router.patch("/rules/{rule_id}", response_model=AlertRule)
def update_rule(rule_id: int, payload: RuleUpdate, session: SessionDep, user: UserDep):
    rule = notify.update_rule(session, rule_id, payload.model_dump())
    audit(session, user, "notify.rule.update", rule.name)
    return rule


@router.delete("/rules/{rule_id}", response_model=Ok)
def delete_rule(rule_id: int, session: SessionDep, user: UserDep):
    rule = notify.get_rule(session, rule_id)
    name = rule.name
    notify.delete_rule(session, rule_id)
    audit(session, user, "notify.rule.delete", name)
    return Ok(message=f"Rule {name} removed")


@router.post("/evaluate")
def evaluate(session: SessionDep, user: UserDep):
    fired = notify.evaluate(session)
    return {"fired": len(fired), "events": [event.model_dump() for event in fired]}


@router.get("/events", response_model=list[AlertEvent])
def events(session: SessionDep, user: UserDep, limit: int = 100):
    return notify.list_events(session, min(limit, 500))


@router.post("/send")
def send(payload: MessageIn, session: SessionDep, user: UserDep):
    event = notify.dispatch(session, payload.title, payload.body, channel_id=payload.channel_id)
    audit(session, user, "notify.send", payload.title)
    return event
