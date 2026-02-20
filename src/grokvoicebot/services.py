from __future__ import annotations

from datetime import datetime
import re

from sqlalchemy import or_, select

from .db import KnowledgeArticle, SessionLocal, Ticket, TicketUpdate


TICKET_PREFIX = "ITSD"


def _next_ticket_number(session) -> str:
    today = datetime.utcnow().strftime("%Y%m%d")
    prefix = f"{TICKET_PREFIX}-{today}-"
    last = session.scalars(
        select(Ticket.ticket_number)
        .where(Ticket.ticket_number.like(f"{prefix}%"))
        .order_by(Ticket.ticket_number.desc())
        .limit(1)
    ).first()

    if not last:
        return f"{prefix}0001"

    try:
        seq = int(last.split("-")[-1]) + 1
    except ValueError:
        seq = 1
    return f"{prefix}{seq:04d}"


def _find_ticket(session, ticket_ref: str) -> Ticket | None:
    if re.fullmatch(r"\d+", ticket_ref):
        return session.get(Ticket, int(ticket_ref))
    return session.scalar(select(Ticket).where(Ticket.ticket_number == ticket_ref))


def seed_knowledge() -> None:
    with SessionLocal() as session:
        existing = session.scalar(select(KnowledgeArticle.id).limit(1))
        if existing:
            return
        session.add_all(
            [
                KnowledgeArticle(
                    title="Reset MFA for Microsoft 365",
                    category="identity",
                    tags="mfa,microsoft,authenticator",
                    source="itsd-runbook",
                    content=(
                        "Open Entra admin center, search user, require re-register MFA, "
                        "and instruct user to re-pair Microsoft Authenticator app."
                    ),
                ),
                KnowledgeArticle(
                    title="VPN not connecting",
                    category="network",
                    tags="vpn,network,remote",
                    source="itsd-runbook",
                    content=(
                        "Validate internet access, confirm certificate validity, "
                        "re-enter VPN profile, and check endpoint posture agent status."
                    ),
                ),
            ]
        )
        session.commit()


def seed_dummy_data() -> dict:
    with SessionLocal() as session:
        existing_dummy_knowledge = session.scalar(
            select(KnowledgeArticle.id).where(KnowledgeArticle.source == "dummy-seed").limit(1)
        )
        existing_dummy_tickets = session.scalar(
            select(Ticket.id).where(Ticket.requester_email.like("dummy.user%@example.com")).limit(1)
        )

        knowledge_created = 0
        tickets_created = 0

        if not existing_dummy_knowledge:
            knowledge_rows = [
                KnowledgeArticle(
                    title="Outlook profile corruption fix",
                    category="email",
                    tags="outlook,email,profile",
                    source="dummy-seed",
                    content="Create a new Outlook profile from Control Panel Mail and set it as default.",
                ),
                KnowledgeArticle(
                    title="Printer offline troubleshooting",
                    category="print",
                    tags="printer,spooler,offline",
                    source="dummy-seed",
                    content="Restart Print Spooler, verify queue is clear, and re-add printer using IP port.",
                ),
                KnowledgeArticle(
                    title="Blue screen after update",
                    category="endpoint",
                    tags="bsod,windows,driver",
                    source="dummy-seed",
                    content="Boot into Safe Mode, roll back latest driver update, and run DISM + SFC.",
                ),
            ]
            session.add_all(knowledge_rows)
            knowledge_created = len(knowledge_rows)

        if not existing_dummy_tickets:
            ticket_payloads = [
                {
                    "requester_name": "Dummy User 1",
                    "requester_email": "dummy.user1@example.com",
                    "title": "VPN prompts for certificate every login",
                    "description": "User cannot connect to VPN consistently after password reset.",
                    "priority": "high",
                    "assigned_group": "network-operations",
                    "status": "in_progress",
                    "updates": [
                        ("voicebot", "open", "Ticket created via dummy seed"),
                        ("netops.agent", "in_progress", "Collected VPN client logs and cert chain details"),
                    ],
                },
                {
                    "requester_name": "Dummy User 2",
                    "requester_email": "dummy.user2@example.com",
                    "title": "Cannot print to finance floor printer",
                    "description": "Printer appears offline for one workstation only.",
                    "priority": "medium",
                    "assigned_group": "eu-deskside",
                    "status": "open",
                    "updates": [
                        ("voicebot", "open", "Ticket created via dummy seed"),
                    ],
                },
                {
                    "requester_name": "Dummy User 3",
                    "requester_email": "dummy.user3@example.com",
                    "title": "Outlook crashes when opening shared mailbox",
                    "description": "Crash observed after Office patching, impacts customer support queue.",
                    "priority": "high",
                    "assigned_group": "messaging-team",
                    "status": "resolved",
                    "updates": [
                        ("voicebot", "open", "Ticket created via dummy seed"),
                        ("messaging.agent", "in_progress", "Reproduced issue and rebuilt user profile"),
                        ("messaging.agent", "resolved", "Applied hotfix and confirmed stable behavior"),
                    ],
                },
            ]

            for payload in ticket_payloads:
                ticket = Ticket(
                    ticket_number=_next_ticket_number(session),
                    requester_name=payload["requester_name"],
                    requester_email=payload["requester_email"],
                    title=payload["title"],
                    description=payload["description"],
                    priority=payload["priority"],
                    assigned_group=payload["assigned_group"],
                    status=payload["status"],
                )
                session.add(ticket)
                session.flush()
                for author, status, comment in payload["updates"]:
                    session.add(
                        TicketUpdate(
                            ticket_id=ticket.id,
                            author=author,
                            status=status,
                            comment=comment,
                        )
                    )
                tickets_created += 1

        session.commit()
        return {
            "knowledge_created": knowledge_created,
            "tickets_created": tickets_created,
            "note": "Dummy data inserted only if not already present.",
        }


def create_knowledge_article(title: str, category: str, content: str, tags: str = "", source: str = "manual") -> dict:
    with SessionLocal() as session:
        row = KnowledgeArticle(title=title, category=category, content=content, tags=tags, source=source)
        session.add(row)
        session.commit()
        return {
            "id": row.id,
            "title": row.title,
            "category": row.category,
            "source": row.source,
        }


def search_knowledge(query: str) -> dict:
    q = f"%{query.lower()}%"
    with SessionLocal() as session:
        rows = session.scalars(
            select(KnowledgeArticle).where(
                or_(
                    KnowledgeArticle.title.ilike(q),
                    KnowledgeArticle.content.ilike(q),
                    KnowledgeArticle.tags.ilike(q),
                    KnowledgeArticle.category.ilike(q),
                )
            )
            .limit(5)
        ).all()

        return {
            "query": query,
            "matches": [
                {
                    "id": r.id,
                    "title": r.title,
                    "category": r.category,
                    "content": r.content,
                    "source": r.source,
                }
                for r in rows
            ],
        }


def create_ticket(
    requester_name: str,
    requester_email: str,
    title: str,
    description: str,
    priority: str,
    assigned_group: str = "service-desk",
) -> dict:
    with SessionLocal() as session:
        ticket = Ticket(
            ticket_number=_next_ticket_number(session),
            requester_name=requester_name,
            requester_email=requester_email,
            title=title,
            description=description,
            priority=priority,
            assigned_group=assigned_group,
            status="open",
        )
        session.add(ticket)
        session.flush()
        session.add(
            TicketUpdate(
                ticket_id=ticket.id,
                author="voicebot",
                comment="Ticket created via voicebot",
                status="open",
            )
        )
        session.commit()
        return {
            "ticket_id": ticket.id,
            "ticket_number": ticket.ticket_number,
            "status": ticket.status,
            "priority": ticket.priority,
            "title": ticket.title,
            "assigned_group": ticket.assigned_group,
            "created_at": ticket.created_at.isoformat(),
        }


def get_ticket_status(ticket_ref: str) -> dict:
    with SessionLocal() as session:
        ticket = _find_ticket(session, ticket_ref)
        if not ticket:
            return {"error": f"Ticket {ticket_ref} not found"}
        return {
            "ticket_id": ticket.id,
            "ticket_number": ticket.ticket_number,
            "status": ticket.status,
            "priority": ticket.priority,
            "title": ticket.title,
            "assigned_group": ticket.assigned_group,
            "updated_at": ticket.updated_at.isoformat() if ticket.updated_at else None,
        }


def get_ticket_details(ticket_ref: str) -> dict:
    with SessionLocal() as session:
        ticket = _find_ticket(session, ticket_ref)
        if not ticket:
            return {"error": f"Ticket {ticket_ref} not found"}

        updates = [
            {
                "author": u.author,
                "status": u.status,
                "comment": u.comment,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in sorted(ticket.updates, key=lambda x: x.created_at)
        ]

        return {
            "ticket_id": ticket.id,
            "ticket_number": ticket.ticket_number,
            "requester_name": ticket.requester_name,
            "requester_email": ticket.requester_email,
            "title": ticket.title,
            "description": ticket.description,
            "status": ticket.status,
            "priority": ticket.priority,
            "assigned_group": ticket.assigned_group,
            "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
            "updated_at": ticket.updated_at.isoformat() if ticket.updated_at else None,
            "updates": updates,
        }


def update_ticket(ticket_ref: str, comment: str, status: str, author: str = "voicebot") -> dict:
    with SessionLocal() as session:
        ticket = _find_ticket(session, ticket_ref)
        if not ticket:
            return {"error": f"Ticket {ticket_ref} not found"}

        ticket.status = status
        update = TicketUpdate(ticket_id=ticket.id, author=author, comment=comment, status=status)
        session.add(update)
        session.commit()
        return {
            "ticket_id": ticket.id,
            "ticket_number": ticket.ticket_number,
            "status": ticket.status,
            "last_comment": comment,
        }
