from datetime import datetime, timedelta

from attune.models.context import CalendarContext, DayBusyness, Milestone
from attune.models.email import Email

_TODAY = datetime.now().strftime("%Y-%m-%d")


def mock_emails() -> list[Email]:
    return [
        # --- Clearly URGENT ---
        Email(
            id="mock-001",
            sender="Prof. Martinez <supervisor@university.edu>",
            subject="Chapter 3 feedback — revise before Thursday or we miss the committee slot",
            body=(
                "Hi,\n\n"
                "I've reviewed Chapter 3. The methodology section has significant issues "
                "that need fixing before I can sign off. The committee meets Friday — I need "
                "your revised version Thursday morning at the latest, or we lose the slot.\n\n"
                "Specifically: fix the statistical analysis in 3.2 and clarify assumptions in 3.4. "
                "This is non-negotiable given the defense timeline.\n\nBest,\nProf. Martinez"
            ),
            timestamp=_TODAY,
        ),
        Email(
            id="mock-002",
            sender="Research Foundation <noreply@researchcouncil.org>",
            subject="REMINDER: Veni grant portal closes in 48 hours — action required",
            body=(
                "Dear Applicant,\n\n"
                "The Veni grant application portal closes in exactly 48 hours. "
                "Incomplete applications will not be reviewed. Late submissions cannot be accepted.\n\n"
                "Current status of your application: draft saved, not yet submitted.\n\n"
                "Submit at: apply.researchcouncil.org\n\nResearch Foundation"
            ),
            timestamp=_TODAY,
        ),

        # --- Clearly SOON ---
        Email(
            id="mock-003",
            sender="Dr. Sarah Chen <s.chen@research.institute.edu>",
            subject="Postdoc position — still interested? Need to know by Friday",
            body=(
                "Hi,\n\n"
                "Following up on our conversation at NeurIPS. We have a postdoc opening "
                "starting October 2026. I need to know by Friday if you're still interested — "
                "we're moving quickly on this. If yes, please send an updated CV and a short "
                "research statement (1 page max).\n\nBest,\nSarah"
            ),
            timestamp=_TODAY,
        ),
        Email(
            id="mock-004",
            sender="Prof. Kim <p.kim@university.edu>",
            subject="Re: Thesis committee — question about your methods section",
            body=(
                "Hi,\n\n"
                "I had a chance to look at the draft. Quick question on section 3.2: "
                "why did you choose a random effects model rather than fixed effects? "
                "Please clarify before the committee meeting on Friday — it'll come up.\n\nBest,\nProf. Kim"
            ),
            timestamp=_TODAY,
        ),
        Email(
            id="mock-005",
            sender="ICML 2026 <submissions@icml.cc>",
            subject="Paper submission deadline reminder — 5 days remaining",
            body=(
                "Dear Author,\n\n"
                "This is a reminder that the ICML 2026 submission deadline is in 5 days. "
                "The system will close at 23:59 AoE on May 6. "
                "Please ensure all authors have registered and your submission is complete.\n\n"
                "Submit: openreview.net/group?id=ICML.cc/2026"
            ),
            timestamp=_TODAY,
        ),
        Email(
            id="mock-006",
            sender="PhD Committee Secretariat <committee@university.edu>",
            subject="Defense date confirmed — July 14, 2026 — please confirm receipt",
            body=(
                "Dear Candidate,\n\n"
                "Your PhD defense is confirmed for July 14, 2026 at 14:00 in Room A1.04. "
                "Please confirm receipt of this email and submit your final thesis to the "
                "secretariat no later than June 28. Failure to do so will require rescheduling.\n\n"
                "PhD Committee Secretariat"
            ),
            timestamp=_TODAY,
        ),
        Email(
            id="mock-007",
            sender="Journal of Machine Learning Research <jmlr@jmlr.org>",
            subject="Review request: manuscript #4821 — response needed within 3 weeks",
            body=(
                "Dear Reviewer,\n\n"
                "You have been invited to review manuscript #4821: "
                "'Scalable Bayesian Inference for Large Language Models'. "
                "The review deadline is May 22. Please accept or decline within 3 days.\n\n"
                "Accept: jmlr.org/review/accept/4821\nDecline: jmlr.org/review/decline/4821"
            ),
            timestamp=_TODAY,
        ),

        # --- LATER ---
        Email(
            id="mock-008",
            sender="Jamie <jamie@collaborator.io>",
            subject="Attune — reranker idea, worth discussing this week?",
            body=(
                "Hey,\n\n"
                "Had more thoughts on the cross-encoder approach. Synthetic data generation "
                "might be simpler than we think — could probably bootstrap from the goals YAML "
                "directly. No rush, but worth a call this week if you have 30 min?\n\nJamie"
            ),
            timestamp=_TODAY,
        ),
        Email(
            id="mock-009",
            sender="University Library <library@university.edu>",
            subject="Loan reminder: 3 items due in 5 days",
            body=(
                "Dear Student,\n\n"
                "The following items are due in 5 days:\n"
                "- Deep Learning (Goodfellow et al.)\n"
                "- Pattern Recognition and Machine Learning (Bishop)\n"
                "- The Elements of Statistical Learning\n\n"
                "Renew online: library.university.edu/renew"
            ),
            timestamp=_TODAY,
        ),
        Email(
            id="mock-010",
            sender="Marcus Roth <m.roth@university.edu>",
            subject="Lab social — drinks Friday evening?",
            body=(
                "Hey everyone,\n\n"
                "Thinking of organizing lab drinks Friday around 18:00 at the usual spot. "
                "Who's in? Reply or just show up.\n\nMarcus"
            ),
            timestamp=_TODAY,
        ),
        Email(
            id="mock-011",
            sender="Department of CS <cs-announce@university.edu>",
            subject="Distinguished Lecture: Prof. Yoshua Bengio — next Tuesday 15:00",
            body=(
                "Dear all,\n\n"
                "We are pleased to announce a distinguished lecture by Prof. Yoshua Bengio "
                "on 'Consciousness and Machine Learning' next Tuesday at 15:00 in Auditorium B. "
                "All are welcome. No registration required.\n\nDepartment of Computer Science"
            ),
            timestamp=_TODAY,
        ),
        Email(
            id="mock-012",
            sender="NeurIPS 2026 <info@neurips.cc>",
            subject="NeurIPS 2026 — abstract registration opens May 15",
            body=(
                "Dear Researcher,\n\n"
                "Abstract registration for NeurIPS 2026 opens May 15. "
                "Full paper submission deadline: May 22. "
                "The conference will be held in Vancouver, December 8-14.\n\nNeurIPS Foundation"
            ),
            timestamp=_TODAY,
        ),
        Email(
            id="mock-013",
            sender="Anna Kowalski <a.kowalski@partner-uni.edu>",
            subject="Re: Collaboration on causal inference — catching up",
            body=(
                "Hi,\n\n"
                "Hope the thesis is going well! I wanted to follow up on our discussion "
                "about joint work on causal inference methods. Would you be open to a call "
                "sometime in the next two weeks to see if there's a paper there?\n\nAnna"
            ),
            timestamp=_TODAY,
        ),
        Email(
            id="mock-014",
            sender="IT Services <it@university.edu>",
            subject="Scheduled maintenance: university VPN — Sunday 02:00–06:00",
            body=(
                "Dear User,\n\n"
                "The university VPN will undergo scheduled maintenance this Sunday "
                "from 02:00 to 06:00. Access to university systems will be unavailable "
                "during this window.\n\nIT Services"
            ),
            timestamp=_TODAY,
        ),
        Email(
            id="mock-015",
            sender="ResearchGate <noreply@researchgate.net>",
            subject="Your paper has 3 new citations this week",
            body=(
                "Hi,\n\n"
                "Your paper 'Variational Inference for Sparse Gaussian Processes' "
                "received 3 new citations this week. View who cited your work on ResearchGate.\n\n"
                "researchgate.net/profile/your-paper"
            ),
            timestamp=_TODAY,
        ),
        Email(
            id="mock-016",
            sender="Grants Office <grants@university.edu>",
            subject="Travel grant — application window open until May 31",
            body=(
                "Dear Researcher,\n\n"
                "The departmental travel grant for conference attendance is open for applications "
                "until May 31. Awards of up to €1,500 are available. Apply via the research portal.\n\n"
                "Grants Office"
            ),
            timestamp=_TODAY,
        ),

        # --- IGNORE ---
        Email(
            id="mock-017",
            sender="Medium Daily Digest <noreply@medium.com>",
            subject="5 AI papers you should read this week",
            body=(
                "This week in AI:\n"
                "1. Are LLMs actually reasoning?\n"
                "2. The death of RAG\n"
                "3. Why your embeddings are wrong\n"
                "4. Mamba vs Transformers: a year later\n"
                "5. Open-source models catch up to GPT-4"
            ),
            timestamp=_TODAY,
        ),
        Email(
            id="mock-018",
            sender="GitHub <noreply@github.com>",
            subject="[attune] Dependabot: bump pydantic from 2.7.0 to 2.7.1",
            body="Dependabot opened pull request #5: bump pydantic from 2.7.0 to 2.7.1 in /requirements.txt",
            timestamp=_TODAY,
        ),
        Email(
            id="mock-019",
            sender="LinkedIn <messages@linkedin.com>",
            subject="You appeared in 14 searches this week",
            body="Your profile appeared in 14 searches this week. See who's looking at your profile.",
            timestamp=_TODAY,
        ),
        Email(
            id="mock-020",
            sender="Overleaf <noreply@overleaf.com>",
            subject="Your Overleaf subscription renews in 30 days",
            body=(
                "Hi,\n\nYour Overleaf Professional subscription renews on June 1 for €119/year. "
                "No action needed if you'd like to continue.\n\nOverleaf Team"
            ),
            timestamp=_TODAY,
        ),
        Email(
            id="mock-021",
            sender="Arxiv Mailing List <arxiv@arxiv.org>",
            subject="cs.LG new submissions — 47 new papers",
            body="47 new submissions in cs.LG (Machine Learning). View at arxiv.org/list/cs.LG/new",
            timestamp=_TODAY,
        ),
        Email(
            id="mock-022",
            sender="Canteen Services <canteen@university.edu>",
            subject="This week's lunch menu",
            body="Monday: Pasta Bolognese / Vegetarian curry\nTuesday: Grilled chicken / Falafel wrap\n...",
            timestamp=_TODAY,
        ),
        Email(
            id="mock-023",
            sender="Slack <feedback@slack.com>",
            subject="Try Slack AI — summarize channels instantly",
            body="Introducing Slack AI. Catch up on missed conversations with AI-powered summaries.",
            timestamp=_TODAY,
        ),
        Email(
            id="mock-024",
            sender="Google Scholar <scholaralerts-noreply@google.com>",
            subject="New citations for 'Variational Inference for Sparse GPs'",
            body="1 new article cites your work. View at scholar.google.com/citations",
            timestamp=_TODAY,
        ),
        Email(
            id="mock-025",
            sender="Zoom <no-reply@zoom.us>",
            subject="Cloud recording available: Lab meeting — Apr 30",
            body="Your cloud recording from Lab meeting on April 30 is now available. View: zoom.us/recording/...",
            timestamp=_TODAY,
        ),
    ]


def mock_calendar_context() -> CalendarContext:
    today = datetime.now()
    weekday = today.weekday()  # 0=Mon, 6=Sun

    def day(offset: int, hours: float, titles: list[str]) -> DayBusyness:
        d = (today + timedelta(days=offset)).strftime("%Y-%m-%d")
        dow = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][(weekday + offset) % 7]
        labeled = [f"[{dow}] {t}" if offset > 0 else t for t in titles]
        if hours < 2:
            busyness = "light"
        elif hours < 5:
            busyness = "moderate"
        else:
            busyness = "heavy"
        return DayBusyness(date=d, busyness=busyness, hours_blocked=hours, events=labeled)

    return CalendarContext(
        today=day(0, 3.5, [
            "10:00 Thesis writing block",
            "14:00 Lab meeting",
            "16:00 Supervisor check-in",
        ]),
        week_ahead=[
            day(1, 1.0, ["11:00 Coffee with collaborator"]),
            day(2, 6.5, [
                "09:00 Department seminar",
                "11:00 Methods consultation",
                "13:00 Grant writing block",
                "15:30 Progress review",
                "17:00 Visiting researcher talk",
            ]),
            day(3, 2.0, [
                "10:00 Admin + email catchup",
                "14:00 Writing block",
            ]),
            day(4, 4.0, [
                "09:30 Thesis committee pre-meeting",
                "11:00 Methods Q&A with Prof. Kim",
                "15:00 Swim",
            ]),
            day(5, 0.5, ["10:00 Weekly standup"]),
            day(6, 0.0, []),   # Saturday — free
            day(7, 1.0, ["10:00 Gym"]),  # Sunday — light
        ],
        upcoming_milestones=[
            Milestone(name="Veni grant deadline", days_away=2),
            Milestone(name="Chapter 3 revised submission", days_away=3),
            Milestone(name="ICML submission deadline", days_away=5),
            Milestone(name="Postdoc application (Dr. Chen)", days_away=4),
            Milestone(name="Thesis committee review", days_away=18),
            Milestone(name="Final thesis submission", days_away=58),
            Milestone(name="PhD defense", days_away=74),
        ],
    )
