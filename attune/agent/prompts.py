from attune.models.email import Email

SYSTEM_PROMPT = """You are Attune, a personal message triage assistant.

Your job: decide how urgently the user needs to act on each email, \
given their current goals and calendar context.

USER GOALS:
{goals}

TRIAGE LABELS:
- URGENT: stop what you're doing — action required AND delay has real cost \
given deadline proximity. Reserve for 0-2 emails per day maximum.
- SOON: read today and respond before end of day
- LATER: read this week, no immediate pressure
- IGNORE: not worth the user's time

Rules for URGENT: only assign if BOTH conditions hold:
1. The email requires an action from the user (not just informational)
2. Waiting even a day has meaningful negative consequences given upcoming milestones

When RELEVANT HISTORY is provided, use it to inform your judgment:
- If a prior email shows the task is already completed, downgrade urgency.
- If a follow-up is escalating on the same thread, maintain or raise urgency.
- Confirmation receipts after completed actions are LATER or IGNORE.

Respond with valid JSON only:
{{"label": "URGENT|SOON|LATER|IGNORE", "reasoning": "one sentence referencing a specific goal or deadline"}}"""


def format_email_summary(email: Email) -> str:
    date_str = email.timestamp.split("T")[0] if "T" in email.timestamp else email.timestamp
    subject = email.subject[:60] + "..." if len(email.subject) > 60 else email.subject
    sender_name = email.sender.split("<")[0].strip() if "<" in email.sender else email.sender
    return f"From: {sender_name} on {date_str}: {subject}"


def format_user_prompt(email, context, past_emails=None) -> str:
    week = " · ".join(
        f"{d.date[5:]}:{d.busyness[0].upper()}" for d in context.week_ahead
    )
    milestones = (
        ", ".join(f"{m.name} in {m.days_away}d" for m in context.upcoming_milestones)
        or "none"
    )

    parts = [
        f"CALENDAR CONTEXT:\n"
        f"  Today ({context.today.date}): {context.today.busyness} — {context.today.hours_blocked}h blocked\n"
        f"  Events: {', '.join(context.today.events) or 'none'}\n"
        f"  Week ahead: {week}\n"
        f"  Upcoming milestones: {milestones}\n"
    ]

    if past_emails:
        history_lines = [f"  - {format_email_summary(e)}" for e in past_emails]
        parts.append("RELEVANT HISTORY:\n" + "\n".join(history_lines) + "\n")

    parts.append(
        f"FROM: {email.sender}\n"
        f"SUBJECT: {email.subject}\n"
        f"BODY:\n"
        f"{email.body[:1500]}"
    )

    return "\n".join(parts)
