from pydantic import BaseModel


class DayBusyness(BaseModel):
    date: str
    busyness: str        # light | moderate | heavy
    hours_blocked: float
    events: list[str]


class Milestone(BaseModel):
    name: str
    days_away: int


class CalendarContext(BaseModel):
    today: DayBusyness
    week_ahead: list[DayBusyness]
    upcoming_milestones: list[Milestone]
