# Project Context

When working with this codebase, prioritize readability over cleverness. Ask clarifying questions before making architectural changes or when a requirement is ambiguous. Fix all errors and warnings.

## About This Project

This fullstack ITSM web app gives internal employees an interactive UI to view tickets from received emails in real-time. In addition to the requestor's email and current time, every new ticket has an assigned team and a severity number based on the SLA with that requestor.

## Key Directories

- `frontend/` - Fullstack ITSM app frontend. It is a table of tickets updated in real-time, and there are options to filter the table.
- `backend/` - Fullstack ITSM app backend. Handles HTTP requests and WebSocket connections, and makes queries to database.
- `triage/` - Contains scripts to listen for emails and automatically triage it as either a ticket to the fullstack app or to Jira. 

## Technologies / Languages

- `frontend/` - Vue in TypeScript
- `backend/` - Flask with PostgreSQL database
- `triage/` - Python, Gmail, and Jira