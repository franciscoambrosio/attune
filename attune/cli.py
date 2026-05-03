import logging
import subprocess
import sys
import time
from datetime import datetime
from typing import List

import click
from dotenv import load_dotenv

load_dotenv()

from attune.agent.judge import TriageAgent
from attune.connectors.calendar import fetch_calendar_context
from attune.connectors.gmail import fetch_emails_since, fetch_todays_emails
from attune.models.email import Email, TriageLabel
from attune.monitor import load_state, save_state, update_state

log = logging.getLogger("attune")

LABEL_ICON = {
    TriageLabel.URGENT: "🔴",
    TriageLabel.SOON:   "🟡",
    TriageLabel.LATER:  "🔵",
    TriageLabel.IGNORE: "⚪",
}
LABEL_ORDER = [TriageLabel.URGENT, TriageLabel.SOON, TriageLabel.LATER, TriageLabel.IGNORE]


def _build_history(emails: List[Email], history_days: int, use_mock: bool) -> dict[str, List[Email]]:
    """Build email history once, return a mapping of email_id -> relevant past emails."""
    try:
        from attune.cache import init_cache, get_cached_emails
        from attune.retrieval import embed_and_cache_emails, retrieve_similar_emails

        init_cache()
        cached = get_cached_emails()

        if not use_mock:
            from attune.connectors.gmail import fetch_emails_since_date
            fresh = fetch_emails_since_date(days=history_days, max_results=100)
            cached_ids = {e.id for e, _ in cached}
            new_emails = [e for e in fresh if e.id not in cached_ids]
            new_embeddings = embed_and_cache_emails(new_emails)
            all_with_embeddings = cached + new_embeddings
        else:
            all_with_embeddings = embed_and_cache_emails(emails)

        history = {}
        for email in emails:
            candidates = [(e, emb) for e, emb in all_with_embeddings if e.id != email.id]
            if not candidates:
                history[email.id] = []
                continue
            past_list = [e for e, _ in candidates]
            past_emb = [emb for _, emb in candidates]
            history[email.id] = retrieve_similar_emails(email, past_list, past_emb, top_k=3)

        return history
    except Exception as exc:
        log.warning("Email history retrieval failed: %s", exc)
        return {}


@click.group()
def cli():
    pass


@cli.command()
@click.option("--max", "max_emails", default=30, help="Max emails to fetch")
@click.option("--mock", is_flag=True, help="Use mock emails and calendar (no Google auth needed)")
@click.option("--history-days", default=30, help="Days of history to use for context retrieval")
def digest(max_emails, mock, history_days):
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

    click.echo("Building email history...")
    history = _build_history(emails, history_days, use_mock=mock)

    results = []
    with click.progressbar(emails, label="Triaging") as bar:
        for email in bar:
            past_emails = history.get(email.id, [])
            result = agent.triage(email, context, past_emails=past_emails)
            results.append((email, result))

    results.sort(key=lambda x: LABEL_ORDER.index(x[1].label))

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


@cli.command()
@click.option("--interval", default=5, show_default=True, help="Poll interval in minutes")
@click.option("--mock", is_flag=True, help="Use mock data (runs one pass then idles)")
@click.option("--history-days", default=30, help="Days of history to use for context retrieval")
def watch(interval, mock, history_days):
    """Watch inbox continuously and notify on URGENT emails."""
    agent = TriageAgent()
    state = load_state()

    click.echo(f"\n  Attune watch started — polling every {interval}m")
    click.echo(f"  Last checked: {datetime.fromtimestamp(state['last_checked_ts']).strftime('%H:%M:%S')}")
    click.echo(f"  Press Ctrl+C to stop.\n")

    if mock:
        from attune.connectors.mock import mock_emails, mock_calendar_context
        emails = mock_emails()
        context = mock_calendar_context()
        history = _build_history(emails, history_days, use_mock=True)
        _watch_pass(agent, emails, context, history)
        click.echo("\n  Mock mode: no further emails to poll. Ctrl+C to exit.")
        while True:
            time.sleep(60)
        return

    try:
        while True:
            now_str = datetime.now().strftime("%H:%M:%S")
            try:
                emails  = fetch_emails_since(after_ts=state["last_checked_ts"])
                context = fetch_calendar_context()
                new     = [e for e in emails if e.id not in state["seen_ids"]]

                if new:
                    history = _build_history(new, history_days, use_mock=False)
                    _watch_pass(agent, new, context, history)
                else:
                    click.echo(f"  [{now_str}] No new emails.", err=False)

                state = update_state(state, [e.id for e in new])
                save_state(state)

            except Exception as exc:
                click.echo(f"  [{now_str}] Error: {exc}", err=True)

            time.sleep(interval * 60)

    except KeyboardInterrupt:
        click.echo("\n  Watch stopped.")


def _watch_pass(agent, emails, context, history):
    now_str = datetime.now().strftime("%H:%M:%S")
    click.echo(f"  [{now_str}] {len(emails)} new email(s):")

    for email in emails:
        try:
            past_emails = history.get(email.id, [])
            result = agent.triage(email, context, past_emails=past_emails)
        except Exception as exc:
            click.echo(f"    ✗ triage failed for {email.id}: {exc}", err=True)
            continue

        icon   = LABEL_ICON[result.label]
        sender = email.sender.split("<")[0].strip() or email.sender
        click.echo(f"\n    {icon} {result.label:<7}  {sender}")
        click.echo(f"             {email.subject[:50]}")
        click.echo(f"             → {result.reasoning}")

        if result.label == TriageLabel.URGENT:
            _notify(f"URGENT: {email.subject}", result.reasoning)


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
