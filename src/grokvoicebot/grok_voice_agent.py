from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

import websockets

from .config import settings
from .schemas import KnowledgeSearchInput, TicketCreateInput, TicketStatusInput, TicketUpdateInput
from .services import create_ticket, get_ticket_status, search_knowledge, update_ticket

logger = logging.getLogger(__name__)


TOOLS = [
    {
        "name": "search_knowledge",
        "description": "Search IT troubleshooting knowledge articles",
        "parameters": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    },
    {
        "name": "create_ticket",
        "description": "Create an IT support ticket",
        "parameters": {
            "type": "object",
            "properties": {
                "requester_name": {"type": "string"},
                "requester_email": {"type": "string"},
                "title": {"type": "string"},
                "description": {"type": "string"},
                "priority": {"type": "string"},
            },
            "required": ["requester_name", "requester_email", "title", "description"],
        },
    },
    {
        "name": "get_ticket_status",
        "description": "Get current status for an IT support ticket",
        "parameters": {
            "type": "object",
            "properties": {"ticket_id": {"type": "integer"}},
            "required": ["ticket_id"],
        },
    },
    {
        "name": "update_ticket",
        "description": "Update ticket status and leave a note",
        "parameters": {
            "type": "object",
            "properties": {
                "ticket_id": {"type": "integer"},
                "comment": {"type": "string"},
                "status": {"type": "string"},
                "author": {"type": "string"},
            },
            "required": ["ticket_id", "comment", "status"],
        },
    },
]


def _extract_tool_call(message: dict[str, Any]) -> tuple[str, str, dict[str, Any]] | None:
    tool_call = message.get("tool_call") or message.get("call")
    if tool_call and isinstance(tool_call, dict):
        call_id = str(tool_call.get("id", "unknown-call"))
        name = tool_call.get("name")
        args = tool_call.get("arguments", {})
        if isinstance(args, str):
            args = json.loads(args)
        if name:
            return call_id, name, args

    if message.get("type") == "response.tool_call":
        call_id = str(message.get("id", "unknown-call"))
        name = message.get("name")
        args = message.get("arguments", {})
        if isinstance(args, str):
            args = json.loads(args)
        if name:
            return call_id, name, args

    return None


def _execute_tool(name: str, args: dict[str, Any]) -> dict[str, Any]:
    if name == "search_knowledge":
        data = KnowledgeSearchInput.model_validate(args)
        return search_knowledge(data.query)
    if name == "create_ticket":
        data = TicketCreateInput.model_validate(args)
        return create_ticket(**data.model_dump())
    if name == "get_ticket_status":
        data = TicketStatusInput.model_validate(args)
        return get_ticket_status(data.ticket_id)
    if name == "update_ticket":
        data = TicketUpdateInput.model_validate(args)
        return update_ticket(**data.model_dump())
    return {"error": f"Unknown tool {name}"}


async def run_voice_agent() -> None:
    if not settings.grok_api_key:
        raise RuntimeError("Set GROK_API_KEY in environment.")

    headers = {
        "Authorization": f"Bearer {settings.grok_api_key}",
    }

    async with websockets.connect(settings.grok_realtime_url, additional_headers=headers, max_size=8 * 1024 * 1024) as ws:
        logger.info("Connected to Grok Voice API realtime websocket")

        session_update = {
            "type": "session.update",
            "session": {
                "model": settings.grok_model,
                "instructions": (
                    "You are an IT Service Desk voice assistant. Use tools for knowledge retrieval and ticket operations."
                ),
                "tools": TOOLS,
            },
        }
        await ws.send(json.dumps(session_update))

        async for raw in ws:
            try:
                message = json.loads(raw)
            except json.JSONDecodeError:
                logger.warning("Skipping non-JSON frame")
                continue

            logger.debug("Incoming realtime event: %s", message)
            extracted = _extract_tool_call(message)
            if not extracted:
                continue

            call_id, name, args = extracted
            try:
                result = _execute_tool(name, args)
            except Exception as exc:  # safe return to realtime loop
                logger.exception("Tool execution failed")
                result = {"error": str(exc)}

            tool_result_event = {
                "type": "tool.result",
                "tool_call_id": call_id,
                "output": result,
            }
            await ws.send(json.dumps(tool_result_event))


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_voice_agent())


if __name__ == "__main__":
    main()
