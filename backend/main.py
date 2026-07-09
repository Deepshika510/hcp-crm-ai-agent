from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel

import models
import schemas
from database import engine, SessionLocal
from agent import agent_app

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"message": "Hello, HCP CRM backend is running"}

@app.post("/interactions", response_model=schemas.InteractionResponse)
def create_interaction(interaction: schemas.InteractionCreate, db: Session = Depends(get_db)):
    db_interaction = models.Interaction(**interaction.dict())
    db.add(db_interaction)
    db.commit()
    db.refresh(db_interaction)
    return db_interaction

@app.get("/interactions", response_model=List[schemas.InteractionResponse])
def read_interactions(db: Session = Depends(get_db)):
    return db.query(models.Interaction).all()


class ChatMessage(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str
    intent: str | None = None
    saved_id: int | None = None


@app.post("/chat", response_model=ChatResponse)
def chat_with_agent(chat_message: ChatMessage):
    result = agent_app.invoke({
        "user_input": chat_message.message,
        "intent": None,
        "extracted_data": None,
        "reply": None,
        "saved_id": None,
    })

    return ChatResponse(
        reply=result.get("reply", "Sorry, something went wrong."),
        intent=result.get("intent"),
        saved_id=result.get("saved_id"),
    )