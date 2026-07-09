# AI-First CRM — HCP Log Interaction Module

An AI-first CRM module for pharmaceutical sales representatives to log and manage interactions with Healthcare Professionals (HCPs). Reps can log visits either through a structured form or a natural-language chat interface powered by an LLM agent.

## Project Overview

This project implements the "Log Interaction Screen" for an HCP module, allowing sales reps to:
- Log HCP interactions via a structured form
- Log HCP interactions via a conversational chat assistant
- Edit existing interactions
- View interaction history for a specific HCP
- Get AI-suggested next actions for upcoming visits
- Schedule follow-ups tied to specific interactions

## Tech Stack

- **Frontend:** React (with hooks-based state management), Google Inter font
- **Backend:** Python, FastAPI
- **AI Agent Framework:** LangGraph
- **LLM Provider:** Groq (using `openai/gpt-oss-20b` — see Note on Model Choice below)
- **Database:** SQLite (via SQLAlchemy ORM; can be swapped to PostgreSQL/MySQL by changing the connection string in `database.py`)

## Note on Model Choice

The original assignment specified `gemma2-9b-it`. As of testing, Groq has decommissioned this model (and its initially suggested replacement, `llama-3.1-8b-instant`/`llama-3.3-70b-versatile`) in favor of newer models. This project uses `openai/gpt-oss-20b`, per Groq's official migration guidance, since it's a currently supported, actively maintained model on the platform.

## LangGraph Agent & Tools

The core of this project is a LangGraph agent that routes a user's natural-language message to one of 5 tools based on classified intent:

1. **log_interaction** — Extracts structured fields (HCP ID, channel, products discussed, summary, sentiment, follow-up action) from free-text input using the LLM, and saves a new interaction record to the database.
2. **edit_interaction** — Given an edit request, identifies the target interaction record (by matching against existing records) and the fields to update, then applies the update to the database.
3. **fetch_hcp_history** — Retrieves all past interactions for a specified HCP, useful for reps preparing for an upcoming visit.
4. **suggest_next_action** — Analyzes an HCP's interaction history and generates a specific, practical recommendation for what the rep should focus on during their next visit.
5. **schedule_follow_up** — Extracts a follow-up task/date from a request and attaches it to the most relevant interaction record.

A router node (also LLM-powered) classifies each incoming chat message into one of: `log`, `edit`, `history`, `suggest`, or `schedule`, and routes to the corresponding tool node.

## Project Structure