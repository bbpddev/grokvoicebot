from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from .db import init_db
from .assistant import handle_assistant_utterance
from .schemas import AssistantUtteranceInput, KnowledgeSearchInput, TicketCreateInput, TicketStatusInput, TicketUpdateInput
from .services import create_ticket, get_ticket_status, search_knowledge, seed_knowledge, update_ticket

app = FastAPI(title="Grok ITSD Voicebot Service")


@app.on_event("startup")
def startup() -> None:
    init_db()
    seed_knowledge()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/knowledge/search")
def knowledge_search(payload: KnowledgeSearchInput) -> dict:
    return search_knowledge(payload.query)


@app.post("/tickets")
def tickets_create(payload: TicketCreateInput) -> dict:
    return create_ticket(**payload.model_dump())


@app.post("/tickets/status")
def tickets_status(payload: TicketStatusInput) -> dict:
    return get_ticket_status(payload.ticket_id)


@app.post("/tickets/update")
def tickets_update(payload: TicketUpdateInput) -> dict:
    return update_ticket(**payload.model_dump())


@app.post("/assistant/respond")
def assistant_respond(payload: AssistantUtteranceInput) -> dict:
    return handle_assistant_utterance(payload.utterance)

@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    static_file = Path(__file__).parent / "static" / "index.html"
    return FileResponse(static_file)
