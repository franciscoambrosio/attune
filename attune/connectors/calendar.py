from datetime import datetime, timedelta, timezone

from googleapiclient.discovery import build

from attune.connectors.gmail import _get_credentials
from attune.models.context import CalendarContext, DayBusyness, Milestone

MILESTONE_KEYWORDS = [
    "defense", "viva", "deadline", "submission", "exam",
    "interview", "conference", "grant", "review", "defense",
]


def fetch_calendar_context(goal_keywords: list[str] | None = None) -> CalendarContext:
    creds = _get_credentials()
    service = build("calendar", "v3", credentials=creds)

    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    window_end = today_start + timedelta(days=60)

    result = service.events().list(
        calendarId="primary",
        timeMin=today_start.isoformat(),
        timeMax=window_end.isoformat(),
        singleEvents=True,
        orderBy="startTime",
        maxResults=200,
    ).execute()

    events = result.get("items", [])
    keywords = (goal_keywords or []) + MILESTONE_KEYWORDS

    day_map: dict[str, list[dict]] = {}
    milestones: list[Milestone] = []

    for event in events:
        start = event.get("start", {})
        date_str = start.get("date") or start.get("dateTime", "")[:10]
        title = event.get("summary", "")

        day_map.setdefault(date_str, []).append(event)

        # detect milestones
        if any(kw.lower() in title.lower() for kw in keywords):
            event_date = datetime.fromisoformat(date_str)
            days_away = (event_date.date() - now.date()).days
            if days_away >= 0:
                milestones.append(Milestone(name=title, days_away=days_away))

    today_str = today_start.strftime("%Y-%m-%d")
    today_busyness = _compute_day(today_str, day_map.get(today_str, []))

    week_ahead = []
    for i in range(1, 8):
        d = (today_start + timedelta(days=i)).strftime("%Y-%m-%d")
        week_ahead.append(_compute_day(d, day_map.get(d, [])))

    # deduplicate milestones, keep closest occurrence per name
    seen: dict[str, Milestone] = {}
    for m in sorted(milestones, key=lambda x: x.days_away):
        key = m.name.lower()
        if key not in seen:
            seen[key] = m
    milestones = list(seen.values())

    return CalendarContext(
        today=today_busyness,
        week_ahead=week_ahead,
        upcoming_milestones=milestones[:10],
    )


def _compute_day(date_str: str, events: list[dict]) -> DayBusyness:
    hours = 0.0
    titles = []
    for e in events:
        title = e.get("summary", "")
        start = e.get("start", {})
        end = e.get("end", {})
        if "dateTime" in start and "dateTime" in end:
            s = datetime.fromisoformat(start["dateTime"])
            en = datetime.fromisoformat(end["dateTime"])
            hours += (en - s).seconds / 3600
            titles.append(f"{s.strftime('%H:%M')} {title}")
        elif "date" in start:
            titles.append(title)

    if hours < 2:
        busyness = "light"
    elif hours < 5:
        busyness = "moderate"
    else:
        busyness = "heavy"

    return DayBusyness(
        date=date_str,
        busyness=busyness,
        hours_blocked=round(hours, 1),
        events=titles,
    )
