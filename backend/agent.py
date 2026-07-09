import os
import json
from datetime import datetime
from dotenv import load_dotenv
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq

from database import SessionLocal
import models

load_dotenv()

llm = ChatGroq(
    model="openai/gpt-oss-20b",
    api_key=os.getenv("GROQ_API_KEY"),
)

class AgentState(TypedDict):
    user_input: str
    intent: Optional[str]
    extracted_data: Optional[dict]
    reply: Optional[str]
    saved_id: Optional[int]


def router_node(state: AgentState):
    user_text = state["user_input"]

    router_prompt = f"""
Classify the intent of this message from a pharma sales rep. Respond with ONLY one word, no punctuation:
- "log" if they are describing a new HCP interaction/visit to record
- "edit" if they are asking to change/update/correct an existing logged interaction
- "history" if they are asking to see past interactions/history for an HCP
- "suggest" if they are asking what to do next, what to focus on, or for advice on the next visit
- "schedule" if they are asking to schedule, set, or book a follow-up/reminder for a specific date

Message: "{user_text}"
"""
    response = llm.invoke(router_prompt)
    intent = response.content.strip().lower()

    if "edit" in intent:
        return {"intent": "edit"}
    elif "history" in intent:
        return {"intent": "history"}
    elif "suggest" in intent:
        return {"intent": "suggest"}
    elif "schedule" in intent:
        return {"intent": "schedule"}
    return {"intent": "log"}


def route_decision(state: AgentState):
    return state["intent"]


def log_interaction_node(state: AgentState):
    user_text = state["user_input"]

    extraction_prompt = f"""
You are an assistant that extracts structured data from a sales rep's note about visiting a healthcare professional (HCP).

From the text below, extract a JSON object with these fields:
- hcp_id (a number, just guess 1 if not mentioned)
- channel (one of: in-person, virtual, phone — guess "in-person" if not clear)
- products_discussed (short text)
- summary (a 1-2 sentence summary)
- sentiment (one of: positive, neutral, negative)
- follow_up_action (short text, or "None" if not mentioned)

Only output valid JSON, nothing else.

Text: "{user_text}"
"""

    response = llm.invoke(extraction_prompt)
    raw_content = response.content

    try:
        cleaned = raw_content.strip().strip("```json").strip("```").strip()
        extracted = json.loads(cleaned)
    except Exception:
        extracted = {
            "hcp_id": 1,
            "channel": "in-person",
            "products_discussed": "Unknown",
            "summary": user_text,
            "sentiment": "neutral",
            "follow_up_action": "None",
        }

    db = SessionLocal()
    db_interaction = models.Interaction(
        hcp_id=extracted.get("hcp_id", 1),
        channel=extracted.get("channel", "in-person"),
        products_discussed=extracted.get("products_discussed", ""),
        summary=extracted.get("summary", ""),
        sentiment=extracted.get("sentiment", "neutral"),
        follow_up_action=extracted.get("follow_up_action", ""),
        raw_input=user_text,
    )
    db.add(db_interaction)
    db.commit()
    db.refresh(db_interaction)
    saved_id = db_interaction.id
    db.close()

    reply_text = f"Logged interaction #{saved_id}: {extracted.get('summary')}"

    return {"extracted_data": extracted, "reply": reply_text, "saved_id": saved_id}


def edit_interaction_node(state: AgentState):
    user_text = state["user_input"]

    db = SessionLocal()
    all_interactions = db.query(models.Interaction).all()
    interactions_list = [
        {
            "id": i.id,
            "hcp_id": i.hcp_id,
            "products_discussed": i.products_discussed,
            "summary": i.summary,
            "sentiment": i.sentiment,
            "follow_up_action": i.follow_up_action,
        }
        for i in all_interactions
    ]

    edit_prompt = f"""
You are an assistant that decides which interaction record to update and what to change.

Here is the list of existing interactions (as JSON):
{json.dumps(interactions_list)}

The user's edit request is: "{user_text}"

Based on the request, output ONLY a JSON object with:
- id (the integer id of the interaction to update, chosen from the list above)
- fields_to_update (an object containing only the fields that should change, using field names: channel, products_discussed, summary, sentiment, follow_up_action)

Only output valid JSON, nothing else.
"""

    response = llm.invoke(edit_prompt)
    raw_content = response.content

    try:
        cleaned = raw_content.strip().strip("```json").strip("```").strip()
        parsed = json.loads(cleaned)
        target_id = parsed["id"]
        fields_to_update = parsed["fields_to_update"]
    except Exception:
        db.close()
        return {"reply": "Sorry, I couldn't figure out which interaction to edit.", "saved_id": None}

    interaction = db.query(models.Interaction).filter(models.Interaction.id == target_id).first()

    if not interaction:
        db.close()
        return {"reply": f"Couldn't find interaction #{target_id}.", "saved_id": None}

    for field, value in fields_to_update.items():
        if hasattr(interaction, field):
            setattr(interaction, field, value)

    db.commit()
    db.refresh(interaction)
    db.close()

    reply_text = f"Updated interaction #{target_id}: {fields_to_update}"

    return {"reply": reply_text, "saved_id": target_id}


def fetch_hcp_history_node(state: AgentState):
    user_text = state["user_input"]

    db = SessionLocal()
    all_interactions = db.query(models.Interaction).all()
    interactions_list = [
        {
            "id": i.id,
            "hcp_id": i.hcp_id,
            "products_discussed": i.products_discussed,
            "summary": i.summary,
            "sentiment": i.sentiment,
        }
        for i in all_interactions
    ]
    db.close()

    id_prompt = f"""
Here is a list of interactions: {json.dumps(interactions_list)}

The user asked: "{user_text}"

Which hcp_id are they asking about? Respond with ONLY the number.
"""
    response = llm.invoke(id_prompt)
    try:
        target_hcp_id = int(response.content.strip())
    except Exception:
        target_hcp_id = 1

    matching = [i for i in interactions_list if i["hcp_id"] == target_hcp_id]

    if not matching:
        return {"reply": f"No history found for HCP #{target_hcp_id}.", "saved_id": None}

    summary_lines = "\n".join(
        [f"- #{m['id']}: {m['products_discussed']} ({m['sentiment']}) — {m['summary']}" for m in matching]
    )
    reply_text = f"History for HCP #{target_hcp_id}:\n{summary_lines}"

    return {"reply": reply_text, "saved_id": None}


def suggest_next_action_node(state: AgentState):
    user_text = state["user_input"]

    db = SessionLocal()
    all_interactions = db.query(models.Interaction).all()
    interactions_list = [
        {
            "id": i.id,
            "hcp_id": i.hcp_id,
            "products_discussed": i.products_discussed,
            "summary": i.summary,
            "sentiment": i.sentiment,
            "follow_up_action": i.follow_up_action,
        }
        for i in all_interactions
    ]
    db.close()

    id_prompt = f"""
Here is a list of interactions: {json.dumps(interactions_list)}

The user asked: "{user_text}"

Which hcp_id are they asking about? Respond with ONLY the number.
"""
    id_response = llm.invoke(id_prompt)
    try:
        target_hcp_id = int(id_response.content.strip())
    except Exception:
        target_hcp_id = 1

    matching = [i for i in interactions_list if i["hcp_id"] == target_hcp_id]

    if not matching:
        return {"reply": f"No history found for HCP #{target_hcp_id}, so no suggestion available.", "saved_id": None}

    suggestion_prompt = f"""
You are a life sciences sales advisor. Here is the interaction history for an HCP:
{json.dumps(matching)}

Based on this history, suggest in 2-3 sentences what the sales rep should focus on for their NEXT visit with this HCP. Be specific and practical.
"""
    suggestion_response = llm.invoke(suggestion_prompt)
    suggestion_text = suggestion_response.content.strip()

    reply_text = f"Suggested next action for HCP #{target_hcp_id}: {suggestion_text}"

    return {"reply": reply_text, "saved_id": None}


def schedule_follow_up_node(state: AgentState):
    user_text = state["user_input"]

    db = SessionLocal()
    all_interactions = db.query(models.Interaction).all()
    interactions_list = [
        {
            "id": i.id,
            "hcp_id": i.hcp_id,
            "products_discussed": i.products_discussed,
            "summary": i.summary,
        }
        for i in all_interactions
    ]

    schedule_prompt = f"""
Today's date is {datetime.utcnow().strftime('%Y-%m-%d')}.

Here is a list of interactions: {json.dumps(interactions_list)}

The user's scheduling request is: "{user_text}"

Determine:
- id: the integer id of the most relevant interaction to attach this follow-up to (pick the most recent/relevant one for the mentioned HCP)
- follow_up_action: a short text description of the follow-up task, including any date mentioned (e.g. "Call Dr Sharma next Friday about trial data")

Output ONLY a JSON object with "id" and "follow_up_action". Nothing else.
"""

    response = llm.invoke(schedule_prompt)
    raw_content = response.content

    try:
        cleaned = raw_content.strip().strip("```json").strip("```").strip()
        parsed = json.loads(cleaned)
        target_id = parsed["id"]
        follow_up_text = parsed["follow_up_action"]
    except Exception:
        db.close()
        return {"reply": "Sorry, I couldn't figure out the follow-up details.", "saved_id": None}

    interaction = db.query(models.Interaction).filter(models.Interaction.id == target_id).first()

    if not interaction:
        db.close()
        return {"reply": f"Couldn't find interaction #{target_id} to attach the follow-up.", "saved_id": None}

    interaction.follow_up_action = follow_up_text
    db.commit()
    db.refresh(interaction)
    db.close()

    reply_text = f"Follow-up scheduled on interaction #{target_id}: {follow_up_text}"

    return {"reply": reply_text, "saved_id": target_id}


graph = StateGraph(AgentState)
graph.add_node("router", router_node)
graph.add_node("log_interaction", log_interaction_node)
graph.add_node("edit_interaction", edit_interaction_node)
graph.add_node("fetch_hcp_history", fetch_hcp_history_node)
graph.add_node("suggest_next_action", suggest_next_action_node)
graph.add_node("schedule_follow_up", schedule_follow_up_node)

graph.set_entry_point("router")
graph.add_conditional_edges("router", route_decision, {
    "log": "log_interaction",
    "edit": "edit_interaction",
    "history": "fetch_hcp_history",
    "suggest": "suggest_next_action",
    "schedule": "schedule_follow_up",
})
graph.add_edge("log_interaction", END)
graph.add_edge("edit_interaction", END)
graph.add_edge("fetch_hcp_history", END)
graph.add_edge("suggest_next_action", END)
graph.add_edge("schedule_follow_up", END)

agent_app = graph.compile()