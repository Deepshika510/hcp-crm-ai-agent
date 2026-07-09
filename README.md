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

- **Frontend:** React UI, Google Inter font
- **State Management:** Redux
- **Backend:** Python + FastAPI
- **AI Agent Framework:** LangGraph
- **LLM Provider:** Groq
- **Primary LLM:** `openai/gpt-oss-20b` on Groq
- **Database:** SQLite via SQLAlchemy ORM for local development; schema is portable to PostgreSQL/MySQL by updating the SQLAlchemy connection string in `database.py`

## Note on Model Choice

The original assignment specified **Groq gemma2-9b-it** and mentioned **llama-3.3-70b-versatile** as a possible contextual alternative. During implementation, these originally referenced models were not consistently available in the current Groq environment used for testing. To keep the project runnable on Groq while preserving the required **LangGraph + Groq-based LLM workflow**, the implementation uses **`openai/gpt-oss-20b` via Groq** as a currently supported model.

The architecture is model-agnostic at the service layer, so the configured model can be switched back to **`gemma2-9b-it`** or another supported Groq model by changing the model name in the LLM configuration.

## LangGraph Agent & Tools

The core of this project is a LangGraph agent that routes a user's natural-language message to one of 5 tools based on classified intent:

1. **log_interaction** — Extracts structured fields (HCP ID, channel, products discussed, summary, sentiment, follow-up action) from free-text input using the LLM, and saves a new interaction record to the database.
2. **edit_interaction** — Given an edit request, identifies the target interaction record (by matching against existing records) and the fields to update, then applies the update to the database.
3. **fetch_hcp_history** — Retrieves all past interactions for a specified HCP, useful for reps preparing for an upcoming visit.
4. **suggest_next_action** — Analyzes an HCP's interaction history and generates a specific, practical recommendation for what the rep should focus on during their next visit.
5. **schedule_follow_up** — Extracts a follow-up task/date from a request and attaches it to the most relevant interaction record.

A router node (also LLM-powered) classifies each incoming chat message into one of: `log`, `edit`, `history`, `suggest`, or `schedule`, and routes to the corresponding tool node.

## Log Interaction Screen Features

The Log Interaction Screen supports two modes of capturing HCP engagement data:

### 1. Structured Form Mode

Allows the field representative to manually enter interaction details such as:
- HCP identifier / name
- interaction date and channel
- products discussed
- key discussion notes
- follow-up actions
- sentiment / outcome summary

### 2. Conversational Chat Mode

Allows the representative to describe the visit in natural language. The LangGraph agent then:
- classifies the user’s intent
- extracts structured interaction fields
- summarizes the visit
- identifies follow-up tasks
- persists the interaction in the CRM database
## Project Structure

```text
backend/
  agent.py
  database.py
  main.py
  models.py
  requirements.txt
  schemas.py
  test_agent.py
  test_groq.py

frontend/
  package.json
  package-lock.json
  public/
  src/

README.md
.gitignore

