#!/usr/bin/env python3
"""A small superhero story about a vote, kindness, and a neighborhood conflict."""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
from dataclasses import asdict, dataclass, field
import itertools
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from results import QAItem, StoryError, StorySample


HEROES = ("Luna", "Milo", "Zara")
PROJECTS = ("garden", "playground", "reading_cabin")
CONFLICTS = ("noise", "space", "fairness")
VOICES = ("bright", "gentle", "bold")
MAX_ACTIONS = 20


@dataclass
class StoryParams:
    hero: str = "Luna"
    project: str = "garden"
    conflict: str = "fairness"
    voice: str = "bright"
    world_seed: int = 777
    prose_seed: int = 42


@dataclass
class Person:
    id: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    location: str = "square"


@dataclass(frozen=True)
class Event:
    id: int
    kind: str
    actor: str
    data: dict
    facts: tuple[str, ...]
    causes: tuple[int, ...]
    state: dict


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.people: dict[str, Person] = {}
        self.votes: dict[str, str] = {}
        self.history: list[Event] = []
        self.fact_events: dict[str, int] = {}
        self.outcome = ""
        self.action_count = 0

    def snapshot(self) -> dict:
        return {
            "people": {key: asdict(value) for key, value in self.people.items()},
            "votes": dict(self.votes),
            "outcome": self.outcome,
        }

    def record(self, kind: str, actor: str, *, facts=(), needs=(), **data):
        missing = [fact for fact in needs if fact not in self.fact_events]
        if missing:
            raise StoryError(f"{kind} needs earlier facts: {', '.join(missing)}.")
        event_id = len(self.history)
        causes = tuple(sorted({self.fact_events[fact] for fact in needs}))
        self.history.append(
            Event(
                id=event_id,
                kind=kind,
                actor=actor,
                data=data,
                facts=tuple(facts),
                causes=causes,
                state=self.snapshot(),
            )
        )
        for fact in facts:
            self.fact_events[fact] = event_id


def validate_params(p: StoryParams):
    if p.hero not in HEROES:
        raise StoryError(f"Unknown hero: {p.hero!r}.")
    if p.project not in PROJECTS:
        raise StoryError(f"Unknown project: {p.project!r}.")
    if p.conflict not in CONFLICTS:
        raise StoryError(f"Unknown conflict: {p.conflict!r}.")
    if p.voice not in VOICES:
        raise StoryError(f"Unknown voice: {p.voice!r}.")
    if type(p.world_seed) is not int or type(p.prose_seed) is not int:
        raise StoryError("Seeds must be integers.")


def build_world(p: StoryParams) -> World:
    validate_params(p)
    w = World(p)
    w.people = {
        "hero": Person(
            "hero",
            p.hero,
            meters={"courage": 3, "listening": 3},
            memes={"kindness": 3, "worry": 1},
        ),
        "mayor": Person(
            "mayor",
            "Mayor Vale",
            meters={"voice": 2},
            memes={"fairness": 2, "worry": 2},
        ),
        "jo": Person(
            "jo",
            "Jo",
            meters={"voice": 2},
            memes={"fairness": 2, "frustration": 2},
        ),
        "pax": Person(
            "pax",
            "Pax",
            meters={"voice": 2},
            memes={"fairness": 2, "frustration": 1},
        ),
        "children": Person(
            "children",
            "the children",
            meters={"voice": 3},
            memes={"hope": 2},
        ),
    }
    w.record(
        "opening",
        "hero",
        facts=("meeting_called", "conflict_seen"),
        project=p.project,
        conflict=p.conflict,
    )
    return w


def tally(w: World) -> dict[str, int]:
    result = {"yes": 0, "no": 0}
    for value in w.votes.values():
        result[value] += 1
    return result


def choose_action(w: World) -> str:
    if "ending" in w.fact_events:
        return "close"
    if "kindness_shared" not in w.fact_events:
        return "listen"
    if "plan_changed" not in w.fact_events:
        return "offer_plan"
    if "vote_cast" not in w.fact_events:
        return "vote"
    if "result_announced" not in w.fact_events:
        return "announce"
    return "close"


def execute(w: World, action: str):
    w.action_count += 1
    if w.action_count > MAX_ACTIONS:
        raise StoryError("The neighborhood meeting did not reach a decision.")

    if action == "listen":
        w.people["hero"].memes["worry"] = 0
        w.people["jo"].memes["frustration"] = 0.5
        w.record(
            "listen",
            "hero",
            facts=("kindness_shared", "needs_known"),
            needs=("meeting_called", "conflict_seen"),
            needs_of="neighbors",
        )
    elif action == "offer_plan":
        if "kindness_shared" not in w.fact_events:
            raise StoryError("Luna must listen before offering a plan.")
        w.people["mayor"].memes["fairness"] = 3
        w.record(
            "offer_plan",
            "hero",
            facts=("plan_changed",),
            needs=("kindness_shared", "needs_known"),
            project=w.params.project,
            conflict=w.params.conflict,
        )
    elif action == "vote":
        if "plan_changed" not in w.fact_events:
            raise StoryError("The plan must respond to the conflict before the vote.")
        w.votes = {"jo": "yes", "pax": "yes", "children": "yes", "mayor": "yes"}
        if w.params.conflict == "space":
            w.votes["pax"] = "no"
        elif w.params.conflict == "noise":
            w.votes["jo"] = "no"
        w.votes["hero"] = "yes"
        w.record(
            "vote",
            "hero",
            facts=("vote_cast",),
            needs=("plan_changed",),
            votes=dict(w.votes),
        )
    elif action == "announce":
        if "vote_cast" not in w.fact_events:
            raise StoryError("The vote must happen before its result is announced.")
        counts = tally(w)
        if counts["yes"] > counts["no"]:
            w.outcome = "approved"
        elif counts["yes"] == counts["no"]:
            w.outcome = "revised"
        else:
            w.outcome = "rejected"
        w.record(
            "announce",
            "mayor",
            facts=("result_announced",),
            needs=("vote_cast",),
            yes=counts["yes"],
            no=counts["no"],
            outcome=w.outcome,
        )
    elif action == "close":
        if "result_announced" not in w.fact_events:
            raise StoryError("There is no announced result to close the story.")
        w.record(
            "close",
            "hero",
            facts=("ending",),
            needs=("result_announced",),
            outcome=w.outcome,
        )
    else:
        raise StoryError(f"Unknown action: {action}.")


def simulate(p: StoryParams) -> World:
    w = build_world(p)
    while "ending" not in w.fact_events:
        execute(w, choose_action(w))
    validate_world(w)
    return w


def validate_world(w: World):
    if not w.outcome or "ending" not in w.fact_events:
        raise StoryError("The story must end with a resolved community decision.")
    if "kindness_shared" not in w.fact_events or "plan_changed" not in w.fact_events:
        raise StoryError("The decision must be shaped by listening and kindness.")
    if not w.votes:
        raise StoryError("The neighborhood must cast a vote.")
    for event in w.history:
        if any(parent >= event.id for parent in event.causes):
            raise StoryError("An event cannot depend on a future event.")


def project_name(value: str) -> str:
    return {
        "garden": "community garden",
        "playground": "quiet playground",
        "reading_cabin": "reading cabin",
    }[value]


def conflict_name(value: str) -> str:
    return {
        "noise": "the playground was too noisy",
        "space": "there was not enough room",
        "fairness": "some families felt left out",
    }[value]


def render_story(w: World, p: StoryParams) -> tuple[str, list[QAItem]]:
    hero = p.hero
    project = project_name(p.project)
    conflict = conflict_name(p.conflict)
    paragraphs: list[str] = []
    qa: list[QAItem] = []
    rng = random.Random(p.prose_seed)

    opening = {
        "bright": f"{hero} wore a silver cape over her school coat because even neighborhood meetings needed a superhero. At sunset, everyone gathered in the town square to vote on a new {project}.",
        "gentle": f"When the town bell rang, {hero} tucked her silver cape around her shoulders and joined the neighbors in the square. They had come to vote on a new {project}.",
        "bold": f"{hero} flew over the rooftops and landed beside the town square fountain. Tonight, the neighbors would vote on a new {project}.",
    }
    paragraphs.append(opening[p.voice])
    paragraphs.append(
        f"But there was a conflict: {conflict}. Jo folded her arms, Pax frowned, and the excited children began talking all at once."
    )
    paragraphs.append(
        f'"We cannot choose a plan until we hear everyone," {hero} said. "What would make this fair?"'
    )
    if p.conflict == "noise":
        paragraphs.append(
            '"The little ones need a place to play," said Jo, "but the library needs quiet." '
            '"Then the playground can close before reading hour," Pax replied.'
        )
    elif p.conflict == "space":
        paragraphs.append(
            '"The square is already crowded," said Pax. "We need room to move." '
            '"Then we can use the empty lot beside the fountain," Jo answered.'
        )
    else:
        paragraphs.append(
            '"Only a few families helped write the first plan," said Jo. '
            '"Let us invite every family to choose what belongs in it," Pax replied.'
        )
    paragraphs.append(
        f"{hero} listened carefully. She heard that everyone wanted the town to feel safe and welcoming, so she changed the plan for the {project}."
    )
    if p.project == "garden":
        paragraphs.append(
            "The garden would have wide paths, a quiet bench, and planting boxes low enough for every neighbor to reach."
        )
    elif p.project == "playground":
        paragraphs.append(
            "The playground would have a calm corner, a clear closing bell, and a wide path for wheelchairs and wagons."
        )
    else:
        paragraphs.append(
            "The reading cabin would have bright windows, a small story stage, and shelves that children could reach themselves."
        )
    paragraphs.append(
        f'"Kindness is not picking one side," {hero} told the crowd. "It is making room for people to belong." '
        f'"And we can vote on that," said Mayor Vale.'
    )
    paragraphs.append(
        "One by one, the neighbors raised their hands. The votes were counted in the open so everyone could see the same result."
    )
    counts = tally(w)
    if w.outcome == "approved":
        paragraphs.append(
            f"The plan passed, {counts['yes']} votes to {counts['no']}. Jo and Pax shook hands, and the children cheered."
        )
    elif w.outcome == "revised":
        paragraphs.append(
            f"The vote tied, {counts['yes']} to {counts['no']}, so the neighbors agreed to test the plan for one week and vote again."
        )
    else:
        paragraphs.append(
            f"The plan was not ready, losing {counts['yes']} votes to {counts['no']}. The neighbors kept the kinder parts and promised to try again."
        )
    paragraphs.append(
        f"That night, {hero} looked over the square. The real superpower was not her cape; it was the kindness that helped every voice enter the vote."
    )

    qa.append(
        QAItem(
            question="What conflict did the neighbors need to solve?",
            answer=f"They needed to solve the problem that {conflict}.",
        )
    )
    qa.append(
        QAItem(
            question="How did kindness change the decision?",
            answer=f"{hero} listened to the neighbors and changed the {project} plan so more people could belong.",
        )
    )
    qa.append(
        QAItem(
            question="What happened in the vote?",
            answer=f"The neighbors voted openly, and the result was {w.outcome}.",
        )
    )
    if rng.random() < 0:
        paragraphs.append("")
    return "\n\n".join(paragraphs), qa


ASP_RULES = """
eligible(yes) :- kindness, conflict, vote.
eligible(no) :- kindness, conflict, vote.
approved :- yes_votes > no_votes.
revised :- yes_votes = no_votes.
rejected :- yes_votes < no_votes.
#show eligible/1.
#show approved/0.
#show revised/0.
#show rejected/0.
"""


def asp_facts():
    from asp import fact
    return "\n".join(
        [
            fact("kindness"),
            fact("conflict"),
            fact("vote"),
            "yes_votes=4.",
            "no_votes=0.",
        ]
    )


def asp_outcome():
    from asp import atoms, one_model
    model = one_model(asp_facts() + "\n" + ASP_RULES)
    return set(atoms(model, "eligible")), bool(atoms(model, "approved"))


def generate(p: StoryParams) -> StorySample:
    world = simulate(p)
    story, qa = render_story(world, p)
    return StorySample(
        params=p,
        story=story,
        prompts=[
            f"Write a {p.voice} superhero story about {p.hero}, kindness, conflict, and a community vote."
        ],
        story_qa=qa,
        world_qa=[
            QAItem(
                question="What makes a community vote fair?",
                answer="A community vote is fair when people can hear one another, understand the plan, and see the result openly.",
            )
        ],
        world=world,
    )


def verify():
    for hero, project, conflict, voice in itertools.product(
        HEROES, PROJECTS, CONFLICTS, VOICES
    ):
        params = StoryParams(hero=hero, project=project, conflict=conflict, voice=voice)
        sample = generate(params)
        if "vote" not in sample.story.lower():
            raise StoryError("A generated story omitted the required vote.")
        if "kindness" not in sample.story.lower():
            raise StoryError("A generated story omitted kindness.")
        if "conflict" not in sample.story.lower():
            raise StoryError("A generated story omitted conflict.")
        if len(sample.story_qa) < 3:
            raise StoryError("Each story needs grounded questions.")
    eligible, approved = asp_outcome()
    if eligible != {("yes",), ("no",)} or not approved:
        raise StoryError("Python and ASP disagree about the voting world.")
    print("OK: all superhero configurations resolve with kindness, conflict, and a vote.")


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", "--world-seed", dest="world_seed", type=int, default=777)
    parser.add_argument("--prose-seed", type=int, default=42)
    parser.add_argument("--hero", choices=HEROES)
    parser.add_argument("--project", choices=PROJECTS)
    parser.add_argument("--conflict", choices=CONFLICTS)
    parser.add_argument("--voice", choices=VOICES, default="bright")
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args, rng: random.Random, index=0, *, sample=False):
    return StoryParams(
        hero=args.hero or (rng.choice(HEROES) if sample else "Luna"),
        project=args.project or (rng.choice(PROJECTS) if sample else "garden"),
        conflict=args.conflict or (rng.choice(CONFLICTS) if sample else "fairness"),
        voice=args.voice,
        world_seed=args.world_seed + index,
        prose_seed=args.prose_seed + index,
    )


def emit(sample: StorySample, *, trace=False, qa=False, header=""):
    if header:
        print(header)
    print(sample.story)
    if qa:
        for item in sample.story_qa:
            print(f"\nQ: {item.question}\nA: {item.answer}")
    if trace:
        print("\nTRACE")
        print(
            json.dumps(
                {
                    "state": sample.world.snapshot(),
                    "history": [asdict(event) for event in sample.world.history],
                },
                indent=2,
            )
        )


def main():
    parser = build_parser()
    args = parser.parse_args()
    try:
        if args.n < 1:
            raise StoryError("-n must be positive.")
        if args.show_asp:
            print(asp_facts() + "\n" + ASP_RULES)
            return 0
        if args.verify:
            verify()
            return 0
        if args.asp:
            eligible, approved = asp_outcome()
            print(json.dumps({"eligible": sorted(eligible), "approved": approved}))
            return 0

        rng = random.Random(args.world_seed)
        if args.all:
            params = []
            for hero, project, conflict in itertools.product(
                HEROES, PROJECTS, CONFLICTS
            ):
                if args.hero and args.hero != hero:
                    continue
                if args.project and args.project != project:
                    continue
                if args.conflict and args.conflict != conflict:
                    continue
                params.append(
                    StoryParams(
                        hero=hero,
                        project=project,
                        conflict=conflict,
                        voice=args.voice,
                        world_seed=args.world_seed + len(params),
                        prose_seed=args.prose_seed + len(params),
                    )
                )
        else:
            params = [
                resolve_params(args, rng, index, sample=args.n > 1)
                for index in range(args.n)
            ]

        if args.json:
            rows = [generate(params_item).to_dict() for params_item in params]
            print(json.dumps(rows[0] if len(rows) == 1 else rows, ensure_ascii=False, indent=2))
        else:
            for index, params_item in enumerate(params):
                emit(
                    generate(params_item),
                    trace=args.trace,
                    qa=args.qa,
                    header=f"\n### Story {index + 1}\n" if len(params) > 1 else "",
                )
        return 0
    except StoryError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
