from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from sqlmodel import Session, select

from app.bootstrap import ensure_admin
from app.config import settings
from app.db import engine, init_db
from app.errors import PanelError
from app.models import User
from app.security import hash_password
from app.services import importer


def _session() -> Session:
    init_db()
    return Session(engine, expire_on_commit=False)


def cmd_serve(args: argparse.Namespace) -> int:
    import uvicorn

    uvicorn.run("app.main:app", host=args.host or settings.host, port=args.port or settings.port)
    return 0


def cmd_inspect(args: argparse.Namespace) -> int:
    source = importer.Source(panel_dir=Path(args.panel_dir), cron_dir=Path(args.cron_dir))
    print(json.dumps(importer.inspect(source), indent=2))
    return 0


def cmd_import(args: argparse.Namespace) -> int:
    source = importer.Source(panel_dir=Path(args.panel_dir), cron_dir=Path(args.cron_dir))
    with _session() as session:
        ensure_admin(session)
        report = importer.apply(session, source, args.activate) if args.apply else importer.plan(session, source)

    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
        return 0

    mode = "APPLIED" if args.apply else "DRY RUN (nothing written)"
    print(f"aaPanel import - {mode}\n")
    for kind in ("site", "database", "cron"):
        items = report.of(kind)
        if not items:
            continue
        print(f"{kind}s ({len(items)}):")
        for item in items:
            mark = "+" if item.action == "import" else "-"
            note = f"  # {item.reason}" if item.reason else ""
            print(f"  {mark} {item.name}{note}")
        print()

    print("summary:", json.dumps(report.summary()))
    if not args.apply:
        print("\nRe-run with --apply to write these into SlimPanel.")
    elif not args.activate:
        print("\nSites were imported parked. Start them once you switch nginx over to SlimPanel.")
    return 0


def cmd_set_password(args: argparse.Namespace) -> int:
    with _session() as session:
        user = session.exec(select(User).where(User.username == args.username)).first()
        if not user:
            print(f"user not found: {args.username}", file=sys.stderr)
            return 1
        user.password_hash = hash_password(args.password)
        session.add(user)
        session.commit()
    print(f"password updated for {args.username}")
    return 0


def cmd_create_user(args: argparse.Namespace) -> int:
    with _session() as session:
        if session.exec(select(User).where(User.username == args.username)).first():
            print(f"user already exists: {args.username}", file=sys.stderr)
            return 1
        session.add(User(username=args.username, password_hash=hash_password(args.password)))
        session.commit()
    print(f"created user {args.username}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="slimpanel")
    sub = parser.add_subparsers(dest="command", required=True)

    serve = sub.add_parser("serve", help="run the panel")
    serve.add_argument("--host")
    serve.add_argument("--port", type=int)
    serve.set_defaults(func=cmd_serve)

    for name, handler, help_text in (
        ("inspect-aapanel", cmd_inspect, "print the aaPanel database schema"),
        ("import-aapanel", cmd_import, "import sites, databases and cron jobs from aaPanel"),
    ):
        command = sub.add_parser(name, help=help_text)
        command.add_argument("--panel-dir", default=str(importer.DEFAULT_PANEL_DIR))
        command.add_argument("--cron-dir", default=str(importer.DEFAULT_CRON_DIR))
        command.set_defaults(func=handler)

    import_cmd = sub.choices["import-aapanel"]
    import_cmd.add_argument("--apply", action="store_true", help="write the changes")
    import_cmd.add_argument("--activate", action="store_true", help="serve imported sites immediately")
    import_cmd.add_argument("--json", action="store_true")

    password = sub.add_parser("set-password", help="set a panel user password")
    password.add_argument("username")
    password.add_argument("password")
    password.set_defaults(func=cmd_set_password)

    create = sub.add_parser("create-user", help="create a panel user")
    create.add_argument("username")
    create.add_argument("password")
    create.set_defaults(func=cmd_create_user)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except PanelError as exc:
        print(f"error: {exc.message}", file=sys.stderr)
        if exc.detail:
            print(exc.detail, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
