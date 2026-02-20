from pydantic import BaseModel, EmailStr, Field


class KnowledgeSearchInput(BaseModel):
    query: str = Field(min_length=2)


class KnowledgeCreateInput(BaseModel):
    title: str
    category: str = "general"
    content: str
    tags: str = ""
    source: str = "manual"


class TicketCreateInput(BaseModel):
    requester_name: str
    requester_email: EmailStr
    title: str
    description: str
    priority: str = "medium"
    assigned_group: str = "service-desk"


class TicketStatusInput(BaseModel):
    ticket_ref: str


class TicketUpdateInput(BaseModel):
    ticket_ref: str
    comment: str
    status: str
    author: str = "voicebot"


class AssistantUtteranceInput(BaseModel):
    utterance: str = Field(min_length=2)
