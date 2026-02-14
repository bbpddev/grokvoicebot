from pydantic import BaseModel, EmailStr, Field


class KnowledgeSearchInput(BaseModel):
    query: str = Field(min_length=2)


class TicketCreateInput(BaseModel):
    requester_name: str
    requester_email: EmailStr
    title: str
    description: str
    priority: str = "medium"


class TicketStatusInput(BaseModel):
    ticket_id: int


class TicketUpdateInput(BaseModel):
    ticket_id: int
    comment: str
    status: str
    author: str = "voicebot"
