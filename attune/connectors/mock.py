from datetime import datetime, timedelta

from attune.models.context import CalendarContext, DayBusyness, Milestone
from attune.models.email import Email

_TODAY = datetime.now().strftime("%Y-%m-%d")


def mock_emails() -> list[Email]:
    return [
        Email(
            id="mock-001",
            sender="Prof. Martinez <supervisor@university.edu>",
            subject="Chapter 3 feedback — please revise before Thursday",
            body=(
                "Hi,\n\n"
                "I've reviewed Chapter 3. There are some significant issues with the "
                "methodology section that need to be addressed before I can sign off. "
                "The committee meets on Friday and I need the revised version by Thursday "
                "morning at the latest. Please fix the statistical analysis in section 3.2 "
                "and clarify the assumptions in 3.4.\n\n"
                "This is important — the defense is coming up fast.\n\nBest,\nProf. Martinez"
            ),
            timestamp=_TODAY,
        ),
        Email(
            id="mock-002",
            sender="Research Foundation <noreply@researchcouncil.org>",
            subject="Veni Grant Application — portal closes in 48 hours",
            body=(
                "Dear Applicant,\n\n"
                "This is a reminder that the Veni grant application portal closes in 48 hours. "
                "Please ensure your application is complete and submitted before the deadline. "
                "Late submissions will not be accepted under any circumstances.\n\n"
                "Portal: apply.researchcouncil.org\n\nResearch Foundation Grants Team"
            ),
            timestamp=_TODAY,
        ),
        Email(
            id="mock-003",
            sender="Jamie <jamie@collaborator.io>",
            subject="Attune — idea for the reranker architecture",
            body=(
                "Hey,\n\n"
                "Had some more thoughts on the reranker approach for Attune. "
                "What if we trained a small cross-encoder on synthetic data generated "
                "from goals + emails pairs? Could be surprisingly good with even a few "
                "hundred examples. I can generate the dataset on my side this weekend.\n\n"
                "Let me know what you think. Also — swim Saturday?\n\nJamie"
            ),
            timestamp=_TODAY,
        ),
        Email(
            id="mock-004",
            sender="University Library <library@university.edu>",
            subject="Your loan is due in 3 days",
            body=(
                "Dear Student,\n\n"
                "The following items are due in 3 days:\n"
                "- Deep Learning (Goodfellow et al.) — due May 4\n\n"
                "Please return or renew online at library.university.edu.\n\n"
                "University Library"
            ),
            timestamp=_TODAY,
        ),
        Email(
            id="mock-005",
            sender="Medium Daily Digest <noreply@medium.com>",
            subject="5 AI papers you should read this week",
            body=(
                "This week in AI:\n"
                "1. Are LLMs actually reasoning?\n"
                "2. The death of RAG\n"
                "3. Why your embeddings are wrong\n"
                "4. Mamba vs Transformers: a year later\n"
                "5. Open-source models catch up to GPT-4\n\n"
                "Read more on medium.com"
            ),
            timestamp=_TODAY,
        ),
        Email(
            id="mock-006",
            sender="PhD Committee <committee@university.edu>",
            subject="Defense date confirmed — July 14, 2026",
            body=(
                "Dear Candidate,\n\n"
                "We are pleased to confirm your PhD defense date: July 14, 2026 at 14:00 "
                "in Room A1.04. Please confirm receipt of this email and ensure your "
                "final thesis is submitted to the secretariat no later than June 28.\n\n"
                "Best regards,\nPhD Committee Secretariat"
            ),
            timestamp=_TODAY,
        ),
        Email(
            id="mock-007",
            sender="GitHub <noreply@github.com>",
            subject="[attune] Pull request merged: fix typo in README",
            body="Pull request #2 was merged into main.\n\nView: github.com/user/attune",
            timestamp=_TODAY,
        ),
        Email(
            id="mock-008",
            sender="Dr. Sarah Chen <s.chen@research.institute.edu>",
            subject="Postdoc position — still interested?",
            body=(
                "Hi,\n\n"
                "We spoke at NeurIPS in December about a potential postdoc position in our group. "
                "We have an opening starting October 2026 and I wanted to check if you're still "
                "interested. If so, could you send an updated CV and a brief research statement "
                "by end of next week?\n\nBest,\nSarah"
            ),
            timestamp=_TODAY,
        ),
    ]


def mock_calendar_context() -> CalendarContext:
    today = datetime.now()

    def day(offset: int, hours: float, titles: list[str]) -> DayBusyness:
        d = (today + timedelta(days=offset)).strftime("%Y-%m-%d")
        if hours < 2:
            busyness = "light"
        elif hours < 5:
            busyness = "moderate"
        else:
            busyness = "heavy"
        return DayBusyness(date=d, busyness=busyness, hours_blocked=hours, events=titles)

    return CalendarContext(
        today=day(0, 3.5, ["10:00 Thesis writing session", "14:00 Lab meeting", "16:00 Supervisor check-in"]),
        week_ahead=[
            day(1, 1.0, ["11:00 Coffee with collaborator"]),
            day(2, 6.0, ["09:00 Department seminar", "11:00 Methods consultation", "14:00 Grant writing", "16:30 Progress meeting"]),
            day(3, 0.0, []),
            day(4, 2.5, ["10:00 Thesis committee pre-meeting", "15:00 Swim"]),
            day(5, 0.5, ["10:00 Weekly standup"]),
            day(6, 0.0, []),
            day(7, 0.0, []),
        ],
        upcoming_milestones=[
            Milestone(name="Veni grant deadline", days_away=2),
            Milestone(name="Chapter 3 revised submission", days_away=3),
            Milestone(name="Thesis committee review", days_away=18),
            Milestone(name="Final thesis submission", days_away=58),
            Milestone(name="PhD defense", days_away=74),
        ],
    )
