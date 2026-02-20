from __future__ import annotations

import re

from .services import create_ticket, get_ticket_details, get_ticket_status, search_knowledge, update_ticket


DEFAULT_REQUESTER = {
    "requester_name": "Web User",
    "requester_email": "webuser@example.com",
}


TICKET_REF_RE = re.compile(r"(itsd-\d{8}-\d{4}|\d+)", re.IGNORECASE)


def _extract_ticket_ref(text: str) -> str | None:
    match = TICKET_REF_RE.search(text)
    if not match:
        return None
    ref = match.group(1)
    return ref.upper() if ref.lower().startswith("itsd-") else ref


def _format_knowledge(matches: list[dict]) -> str:
    if not matches:
        return "I could not find a matching knowledge article. Please rephrase the issue."
    top = matches[0]
    return f"I found '{top['title']}'. Suggested guidance: {top['content']}"


def handle_assistant_utterance(utterance: str) -> dict:
    text = utterance.strip()
    lowered = text.lower()

    ticket_ref = _extract_ticket_ref(lowered)
    if ("status" in lowered or "check" in lowered) and ticket_ref:
        result = get_ticket_status(ticket_ref)
        if "error" in result:
            return {"action": "ticket_status", "result": result, "response": result["error"]}
        response = (
            f"Ticket {result['ticket_number']} is currently {result['status']} "
            f"with {result['priority']} priority."
        )
        return {"action": "ticket_status", "result": result, "response": response}

    if "details" in lowered and ticket_ref:
        result = get_ticket_details(ticket_ref)
        if "error" in result:
            return {"action": "ticket_details", "result": result, "response": result["error"]}
        response = (
            f"Ticket {result['ticket_number']} is {result['status']} and has "
            f"{len(result['updates'])} update entries."
        )
        return {"action": "ticket_details", "result": result, "response": response}

    if "update" in lowered and ticket_ref:
        status = "in_progress"
        if "resolved" in lowered:
            status = "resolved"
        elif "open" in lowered:
            status = "open"
        comment = text
        result = update_ticket(ticket_ref=ticket_ref, status=status, comment=comment, author="web-voicebot")
        if "error" in result:
            return {"action": "ticket_update", "result": result, "response": result["error"]}
        return {
            "action": "ticket_update",
            "result": result,
            "response": f"Done. Ticket {result['ticket_number']} was updated to {status}.",
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
            "response": f"Ticket {result['ticket_number']} created with {result['priority']} priority.",
        }

    result = search_knowledge(text)
    return {
        "action": "knowledge_search",
        "result": result,
        "response": _format_knowledge(result.get("matches", [])),
    }
