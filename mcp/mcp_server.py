from os import getenv

import requests
from dotenv import load_dotenv
from mcp.server import MCPServer

load_dotenv()

BACKEND_URL = getenv("BACKEND_URL", "http://localhost:4000").rstrip("/")
MCP_USERNAME = getenv("MCP_USERNAME")
MCP_PASSWORD = getenv("MCP_PASSWORD")

mcp = MCPServer("Ticket Triage MCP")

_token: str | None = None

def _login() -> str:
    global _token
    response = requests.post(
        f"{BACKEND_URL}/login",
        json={"username": MCP_USERNAME, "password": MCP_PASSWORD},
    )
    response.raise_for_status()
    token = response.json()["token"]
    _token = token
    return token


def _request(method: str, path: str, **kwargs) -> requests.Response:
    global _token
    if _token is None:
        _login()

    response = requests.request(
        method, f"{BACKEND_URL}{path}",
        headers={"Authorization": f"Bearer {_token}"},
        **kwargs,
    )
    if response.status_code == 403:
        _login()
        response = requests.request(
            method, f"{BACKEND_URL}{path}",
            headers={"Authorization": f"Bearer {_token}"},
            **kwargs,
        )

    response.raise_for_status()
    return response


@mcp.tool()
def get_departments() -> list[dict]:
    """Get every department (team) a ticket can be assigned to, with its ID and name."""
    response = _request("GET", "/departments")
    return response.json()


@mcp.tool()
def get_severities() -> list[dict]:
    """Get every ticket severity level, with its ID, name, and SLA response/resolve times in hours."""
    response = _request("GET", "/severities")
    return response.json()


@mcp.tool()
def create_ticket(
    requestor_email: str,
    assigned_team_id: int,
    sev_id: int,
    email_subject: str | None = None,
    email_body: str | None = None,
    ai_explaination: str | None = None,
) -> dict:
    """Create a new ticket.

    Args:
        requestor_email: Email address of the person who submitted the ticket.
        assigned_team_id: ID of the department the ticket is assigned to.
        sev_id: ID of the ticket's severity level.
        email_subject: Subject line of the originating email, if any.
        email_body: Body of the originating email, if any.
        ai_explaination: Explanation of why the ticket was triaged this way, if any.
    """
    response = _request("POST", "/tickets", json={
        "requestor_email": requestor_email,
        "assigned_team_id": assigned_team_id,
        "sev_id": sev_id,
        "email_subject": email_subject,
        "email_body": email_body,
        "ai_explaination": ai_explaination,
    })
    return response.json()


@mcp.tool()
def get_tickets(
    team: str | None = None,
    severity: str | None = None,
    requestor_email: str | None = None,
    replied: bool | None = None,
    created_after: str | None = None,
    created_before: str | None = None,
    page: int = 1,
    per_page: int = 25,
) -> dict:
    """Get tickets, optionally filtered.

    Args:
        team: Filter by assigned team/department name.
        severity: Filter by severity name.
        requestor_email: Filter by the requestor's email address.
        replied: Filter by whether the ticket has been replied.
        created_after: Only include tickets created at or after this ISO 8601 timestamp.
        created_before: Only include tickets created at or before this ISO 8601 timestamp.
        page: Page number to return.
        per_page: Number of tickets per page (max 100).
    """
    params = {
        "team": team,
        "severity": severity,
        "requestor_email": requestor_email,
        "created_after": created_after,
        "created_before": created_before,
        "page": page,
        "per_page": per_page,
    }
    if replied is not None:
        params["resolved"] = str(replied).lower()

    response = _request("GET", "/tickets", params=params)
    return response.json()


@mcp.tool()
def get_ticket_audit_log(ticket_id: int) -> list[dict]:
    """Get the audit log entries for a specific ticket, oldest first.

    Args:
        ticket_id: ID of the ticket to get the audit log for.
    """
    response = _request("GET", f"/tickets/{ticket_id}/audit")
    return response.json()


@mcp.tool()
def update_ticket(
    ticket_id: int,
    assigned_team_id: int | None = None,
    sev_id: int | None = None,
    mark_replied: bool = False,
    mark_resolved: bool = False,
) -> dict:
    """Update a ticket's team, severity, and/or mark it as replied to or resolved.

    At least one of assigned_team_id, sev_id, mark_replied, or mark_resolved must
    be provided. Each requested change is applied as a separate update, and the
    ticket state after the last applied change is returned.

    Args:
        ticket_id: ID of the ticket to update.
        assigned_team_id: New department ID to assign the ticket to.
        sev_id: New severity ID for the ticket.
        mark_replied: If true, mark the ticket as replied to.
        mark_resolved: If true, mark the ticket as resolved.
    """
    if assigned_team_id is None and sev_id is None and not mark_replied and not mark_resolved:
        raise ValueError(
            "At least one of assigned_team_id, sev_id, mark_replied, or mark_resolved is required"
        )

    response = None

    if assigned_team_id is not None:
        response = _request("PATCH", f"/tickets/{ticket_id}/team", json={"assigned_team_id": assigned_team_id})

    if sev_id is not None:
        response = _request("PATCH", f"/tickets/{ticket_id}/severity", json={"sev_id": sev_id})

    if mark_replied:
        response = _request("PATCH", f"/tickets/{ticket_id}/reply")

    if mark_resolved:
        response = _request("PATCH", f"/tickets/{ticket_id}/resolve")

    assert response is not None
    return response.json()


if __name__ == "__main__":
    mcp.run(transport="stdio")
