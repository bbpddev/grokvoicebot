from __future__ import annotations

import re

from .services import create_ticket, get_ticket_status, search_knowledge, update_ticket


DEFAULT_REQUESTER = {
    "requester_name": "Web User",
    "requester_email": "webuser@example.com",
}


def _format_knowledge(matches: list[dict]) -> str:
    if not matches:
        return "I could not find a matching knowledge article. Please rephrase the issue."
    top = matches[0]
    return f"I found '{top['title']}'. Suggested guidance: {top['content']}"


def handle_assistant_utterance(utterance: str) -> dict:
    text = utterance.strip()
    lowered = text.lower()

    status_match = re.search(r"ticket\s*(?:id\s*)?(\d+)", lowered)
    if ("status" in lowered or "check" in lowered) and status_match:
        ticket_id = int(status_match.group(1))
        result = get_ticket_status(ticket_id)
        if "error" in result:
            return {"action": "ticket_status", "result": result, "response": result["error"]}
        response = (
            f"Ticket {result['ticket_id']} is currently {result['status']} "
            f"with {result['priority']} priority."
        )
        return {"action": "ticket_status", "result": result, "response": response}

    update_match = re.search(r"update\s+ticket\s*(\d+)", lowered)
    if update_match:
        ticket_id = int(update_match.group(1))
        status = "in_progress"
        if "resolved" in lowered:
            status = "resolved"
        elif "open" in lowered:
            status = "open"
        comment = text
        result = update_ticket(ticket_id=ticket_id, status=status, comment=comment, author="web-voicebot")
        if "error" in result:
            return {"action": "ticket_update", "result": result, "response": result["error"]}
        return {
            "action": "ticket_update",
            "result": result,
            "response": f"Done. Ticket {ticket_id} was updated to {status}.",
        }

    if "create" in lowered and "ticket" in lowered:
        priority = "medium"
        if "high" in lowered:
            priority = "high"
        elif "low" in lowered:
            priority = "low"

        title = text
        if "for" in lowered:
            title = text.split("for", 1)[1].strip() or text

        result = create_ticket(
            requester_name=DEFAULT_REQUESTER["requester_name"],
            requester_email=DEFAULT_REQUESTER["requester_email"],
            title=title[:255],
            description=text,
            priority=priority,
        )
        return {
            "action": "ticket_create",
            "result": result,
            "response": f"Ticket {result['ticket_id']} created with {result['priority']} priority.",
        }

    result = search_knowledge(text)
    return {
        "action": "knowledge_search",
        "result": result,
        "response": _format_knowledge(result.get("matches", [])),
    }
