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

Respond with valid JSON only:
{{"label": "URGENT|SOON|LATER|IGNORE", "reasoning": "one sentence referencing a specific goal or deadline"}}"""


def format_user_prompt(email, context) -> str:
    week = " · ".join(
        f"{d.date[5:]}:{d.busyness[0].upper()}" for d in context.week_ahead
    )
    milestones = (
        ", ".join(f"{m.name} in {m.days_away}d" for m in context.upcoming_milestones)
        or "none"
    )

    return f"""CALENDAR CONTEXT:
  Today ({context.today.date}): {context.today.busyness} — {context.today.hours_blocked}h blocked
  Events: {", ".join(context.today.events) or "none"}
  Week ahead: {week}
  Upcoming milestones: {milestones}

FROM: {email.sender}
SUBJECT: {email.subject}
BODY:
{email.body[:1500]}"""
