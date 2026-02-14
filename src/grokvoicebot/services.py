from __future__ import annotations

from sqlalchemy import or_, select

from .db import KnowledgeArticle, SessionLocal, Ticket, TicketUpdate


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
                    content=(
                        "Open Entra admin center, search user, require re-register MFA, "
                        "and instruct user to re-pair Microsoft Authenticator app."
                    ),
                ),
                KnowledgeArticle(
                    title="VPN not connecting",
                    category="network",
                    tags="vpn,network,remote",
                    content=(
                        "Validate internet access, confirm certificate validity, "
                        "re-enter VPN profile, and check endpoint posture agent status."
                    ),
                ),
            ]
        )
        session.commit()


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
            .limit(3)
        ).all()

        return {
            "query": query,
            "matches": [
                {
                    "id": r.id,
                    "title": r.title,
                    "category": r.category,
                    "content": r.content,
                }
                for r in rows
            ],
        }


def create_ticket(requester_name: str, requester_email: str, title: str, description: str, priority: str) -> dict:
    with SessionLocal() as session:
        ticket = Ticket(
            requester_name=requester_name,
            requester_email=requester_email,
            title=title,
            description=description,
            priority=priority,
            status="open",
        )
        session.add(ticket)
        session.flush()
        session.add(TicketUpdate(ticket_id=ticket.id, author="voicebot", comment="Ticket created via voicebot", status="open"))
        session.commit()
        return {
            "ticket_id": ticket.id,
            "status": ticket.status,
            "priority": ticket.priority,
            "title": ticket.title,
            "created_at": ticket.created_at.isoformat(),
        }


def get_ticket_status(ticket_id: int) -> dict:
    with SessionLocal() as session:
        ticket = session.get(Ticket, ticket_id)
        if not ticket:
            return {"error": f"Ticket {ticket_id} not found"}
        return {
            "ticket_id": ticket.id,
            "status": ticket.status,
            "priority": ticket.priority,
            "title": ticket.title,
            "updated_at": ticket.updated_at.isoformat() if ticket.updated_at else None,
        }


def update_ticket(ticket_id: int, comment: str, status: str, author: str = "voicebot") -> dict:
    with SessionLocal() as session:
        ticket = session.get(Ticket, ticket_id)
        if not ticket:
            return {"error": f"Ticket {ticket_id} not found"}

        ticket.status = status
        update = TicketUpdate(ticket_id=ticket_id, author=author, comment=comment, status=status)
        session.add(update)
        session.commit()
        return {
            "ticket_id": ticket.id,
            "status": ticket.status,
            "last_comment": comment,
        }
