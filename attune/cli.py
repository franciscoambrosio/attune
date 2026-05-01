import subprocess
import sys
from datetime import datetime

import click
from dotenv import load_dotenv

load_dotenv()

from attune.agent.judge import TriageAgent
from attune.connectors.calendar import fetch_calendar_context
from attune.connectors.gmail import fetch_todays_emails
from attune.models.email import TriageLabel

LABEL_ICON = {
    TriageLabel.URGENT: "🔴",
    TriageLabel.SOON:   "🟡",
    TriageLabel.LATER:  "🔵",
    TriageLabel.IGNORE: "⚪",
}
LABEL_ORDER = [TriageLabel.URGENT, TriageLabel.SOON, TriageLabel.LATER, TriageLabel.IGNORE]


@click.group()
def cli():
    pass


@cli.command()
@click.option("--max", "max_emails", default=30, help="Max emails to fetch")
@click.option("--mock", is_flag=True, help="Use mock emails and calendar (no Google auth needed)")
def digest(max_emails, mock):
    """Fetch today's Gmail and triage against your goals."""
    if mock:
        from attune.connectors.mock import mock_emails, mock_calendar_context
        click.echo("Using mock data...")
        emails = mock_emails()
        context = mock_calendar_context()
    else:
        click.echo("Fetching emails and calendar...")
        emails = fetch_todays_emails(max_results=max_emails)
        context = fetch_calendar_context()

    agent = TriageAgent()

    if not emails:
        click.echo("No unread emails today.")
        return

    results = []
    with click.progressbar(emails, label="Triaging") as bar:
        for email in bar:
            result = agent.triage(email, context)
            results.append((email, result))

    # sort by label priority
    results.sort(key=lambda x: LABEL_ORDER.index(x[1].label))

    # header
    today = datetime.now().strftime("%a %b %-d")
    week = " ".join(d.busyness[0].upper() for d in context.week_ahead)
    milestones = "  ·  ".join(
        f"{m.name} in {m.days_away}d" for m in context.upcoming_milestones
    ) or "none"

    width = 58
    click.echo(f"\n{'─' * width}")
    click.echo(f"  TODAY'S DIGEST ({today})")
    click.echo(f"  Today: {context.today.busyness}  ·  Week ahead: {week}")
    if context.upcoming_milestones:
        click.echo(f"  Milestones: {milestones}")
    click.echo(f"{'─' * width}")

    for email, result in results:
        icon = LABEL_ICON[result.label]
        sender = email.sender.split("<")[0].strip() or email.sender
        subject = email.subject[:42]
        click.echo(f"\n  {icon} {result.label:<7}  {sender}")
        click.echo(f"           {subject}")
        click.echo(f"           → {result.reasoning}")

        if result.label == TriageLabel.URGENT:
            _notify(f"URGENT: {email.subject}", result.reasoning)

    # summary
    counts = {l: sum(1 for _, r in results if r.label == l) for l in LABEL_ORDER}
    parts = []
    if counts[TriageLabel.URGENT]:
        parts.append(f"{counts[TriageLabel.URGENT]} urgent")
    if counts[TriageLabel.SOON]:
        parts.append(f"{counts[TriageLabel.SOON]} read today")
    if counts[TriageLabel.LATER]:
        parts.append(f"{counts[TriageLabel.LATER]} this week")
    if counts[TriageLabel.IGNORE]:
        parts.append(f"{counts[TriageLabel.IGNORE]} ignored")

    click.echo(f"\n{'─' * width}")
    click.echo(f"  {len(emails)} emails  ·  {' · '.join(parts)}")
    click.echo(f"{'─' * width}\n")


def _notify(title: str, body: str):
    try:
        if sys.platform == "darwin":
            subprocess.run(
                ["osascript", "-e",
                 f'display notification "{body}" with title "{title}"'],
                check=False,
            )
        elif sys.platform.startswith("linux"):
            subprocess.run(["notify-send", title, body], check=False)
    except FileNotFoundError:
        pass
