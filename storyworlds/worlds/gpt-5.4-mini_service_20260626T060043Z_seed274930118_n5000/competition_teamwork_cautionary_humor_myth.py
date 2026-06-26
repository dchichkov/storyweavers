#!/usr/bin/env python3
"""
A myth-style storyworld about a friendly competition that can only be won by
teamwork, with a cautionary humorsome turn.

Premise:
- Two small teams enter a sacred contest for a prize.
- Each team can try a selfish shortcut, but the shortcut backfires in a funny,
  cautionary way.
- The only reasonable victory is earned by cooperating, sharing tools, and
  respecting a small taboo.

The world is deliberately small and constraint-driven:
- typed entities with meters and memes
- state changes drive the prose
- invalid combinations raise StoryError
- inline ASP mirrors the Python reasonableness gate
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Entities and world model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    team: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ("glow", "dust", "tired", "won"):
            self.meters.setdefault(k, 0.0)
        for k in ("pride", "fear", "cheer", "greed", "trust", "warning"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"hero", "sister", "maiden", "huntress"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"brother", "hero-boy", "hunter"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    omen: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Contest:
    id: str
    title: str
    verb: str
    danger: str
    shortcut: str
    teamwork: str
    caution: str
    prize: str
    prize_phrase: str
    taboo: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    team_use: str
    guards: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place, contest: Contest) -> None:
        self.place = place
        self.contest = contest
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        w = World(self.place, self.contest)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "ridge": Place("the moonlit ridge", "silver wind", {"race", "harp", "berry"}),
    "grove": Place("the old grove", "hushed leaves", {"race", "harp", "berry"}),
    "shore": Place("the bright shore", "salt spray", {"race", "harp", "berry"}),
}

CONTESTS = {
    "moonberry": Contest(
        id="moonberry",
        title="the Moonberry Contest",
        verb="gather moonberries",
        danger="the berries would spill into the brambles",
        shortcut="push ahead alone",
        teamwork="share the basket and climb together",
        caution="the wise never seize a sacred fruit by greed",
        prize="moonberry crown",
        prize_phrase="a wreath of moonberries and white flowers",
        taboo="never shake the elder branch",
        tags={"competition", "teamwork", "cautionary", "humor", "myth"},
    ),
    "harp": Contest(
        id="harp",
        title="the Echo-Harp Trial",
        verb="play the echo-harp",
        danger="the harp strings would snap if tugged too hard",
        shortcut="pluck the loudest note at once",
        teamwork="listen for the answer and play in turns",
        caution="a boastful song can wake the wrong spirit",
        prize="echo harp",
        prize_phrase="a bronze harp with a silver string",
        taboo="never shout into the echo cave",
        tags={"competition", "teamwork", "cautionary", "humor", "myth"},
    ),
    "river": Contest(
        id="river",
        title="the River Lantern Run",
        verb="carry lanterns across the river",
        danger="the water would douse every flame",
        shortcut="dash across without a bridge",
        teamwork="build a raft and guard the flames",
        caution="even a brave lantern looks foolish when wet",
        prize="river torch",
        prize_phrase="a torch that burns with blue fire",
        taboo="never race the floodmoon",
        tags={"competition", "teamwork", "cautionary", "humor", "myth"},
    ),
}

TOOLS = [
    Tool("basket", "a reed basket", "a woven reed basket", "share the basket", {"berry"}),
    Tool("ladder", "a cedar ladder", "a cedar ladder", "climb together", {"berry"}),
    Tool("reed", "a tuning reed", "a tuning reed", "play in turns", {"harp"}),
    Tool("mask", "a river mask", "a river mask", "guard the flames", {"river"}),
]

HERO_NAMES = ["Lina", "Orin", "Mira", "Taro", "Nessa", "Pavo", "Sela", "Kiro"]
TEAM_NAMES = ["Dawn", "Ash", "Brine", "Grove"]


@dataclass
class StoryParams:
    place: str
    contest: str
    hero1: str
    hero2: str
    team1: str
    team2: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def contest_requires_teamwork(contest: Contest) -> bool:
    return True


def valid_combo(place: str, contest: str) -> bool:
    return place in PLACES and contest in CONTESTS


def select_tool(contest: Contest) -> Optional[Tool]:
    for tool in TOOLS:
        if contest.id in tool.guards:
            return tool
    return None


def explain_rejection(place: str, contest: str) -> str:
    if place not in PLACES or contest not in CONTESTS:
        return "(No story: the requested place or contest is unknown.)"
    c = CONTESTS[contest]
    if select_tool(c) is None:
        return f"(No story: no tool in this world can reasonably support {c.title}.)"
    return "(No story: the combination does not make a plausible mythic contest.)"


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def predict_failure(world: World, winner: Entity, loser: Entity, tool: Tool) -> dict[str, bool]:
    sim = world.copy()
    sim.get(winner.id).memes["greed"] += 1
    sim.get(loser.id).memes["warning"] += 1
    if tool.id == "basket":
        return {"spill": True, "laugh": True}
    if tool.id == "reed":
        return {"snap": True, "laugh": True}
    return {"wet": True, "laugh": True}


def intro(world: World, a: Entity, b: Entity) -> None:
    world.say(
        f"In {world.place.name}, {a.id} and {b.id} were young champions of two small houses."
    )
    world.say(
        f"They both wanted the honor of {world.contest.verb} in {world.contest.title}."
    )


def omen(world: World) -> None:
    world.say(
        f"That day, {world.place.omen} moved through the stones, as if the hill itself were watching."
    )


def rivalry(world: World, a: Entity, b: Entity) -> None:
    a.memes["pride"] += 1
    b.memes["pride"] += 1
    a.memes["fear"] += 0.5
    b.memes["fear"] += 0.5
    world.say(
        f"{a.id} boasted that {a.pronoun('subject')} could {world.contest.shortcut}, "
        f"and {b.id} answered with a louder boast."
    )
    world.say(
        f"But the old song said, '{world.contest.caution}.'"
    )


def warning(world: World, a: Entity, b: Entity) -> None:
    a.memes["warning"] += 1
    b.memes["warning"] += 1
    world.say(
        f"The elder at the gate warned them: '{world.contest.taboo.capitalize()}.'"
    )


def mishap(world: World, a: Entity, b: Entity) -> None:
    a.meters["dust"] += 1
    b.meters["dust"] += 1
    world.say(
        f"They tried the selfish way anyway, and at once the path answered with a comic mishap."
    )
    world.say(
        f"{world.contest.danger.capitalize()}, and the two champions looked very small beside the laughing reeds."
    )


def teamwork_turn(world: World, a: Entity, b: Entity, tool: Tool) -> None:
    a.memes["trust"] += 1
    b.memes["trust"] += 1
    a.memes["greed"] = 0
    b.memes["greed"] = 0
    world.say(
        f"Then {a.id} and {b.id} remembered the better way: {world.contest.teamwork}."
    )
    world.say(
        f"They chose {tool.phrase}, because the old task could only be done by two careful hands."
    )


def win(world: World, a: Entity, b: Entity, tool: Tool) -> None:
    a.meters["won"] += 1
    b.meters["won"] += 1
    world.say(
        f"Side by side, they finished {world.contest.verb}, and the prize was given to both houses together."
    )
    world.say(
        f"By sunset, {a.id} and {b.id} carried {world.contest.prize_phrase}, and no one could tell which one had smiled first."
    )


def tell(params: StoryParams) -> World:
    world = World(PLACES[params.place], CONTESTS[params.contest])
    a = world.add(Entity(id=params.hero1, kind="character", type="hero"))
    b = world.add(Entity(id=params.hero2, kind="character", type="hero"))
    a.team = params.team1
    b.team = params.team2

    intro(world, a, b)
    world.para()
    omen(world)
    rivalry(world, a, b)
    warning(world, a, b)
    mishap(world, a, b)
    world.para()
    tool = select_tool(world.contest)
    if tool is None:
        raise StoryError(explain_rejection(params.place, params.contest))
    teamwork_turn(world, a, b, tool)
    win(world, a, b, tool)

    world.facts.update(hero1=a, hero2=b, tool=tool, contest=world.contest, place=world.place)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    c = world.contest
    return [
        f'Write a short myth about a competition called "{c.title}" where two young heroes learn teamwork.',
        f"Tell a cautionary, humorous story in a mythic voice about {c.verb} and avoiding a foolish shortcut.",
        f"Write a child-friendly legend where pride causes trouble, but cooperation wins the prize.",
    ]


def story_qa(world: World) -> list[QAItem]:
    a = world.get(world.facts["hero1"].id)
    b = world.get(world.facts["hero2"].id)
    c = world.contest
    tool: Tool = world.facts["tool"]
    return [
        QAItem(
            question=f"Who were the two young champions in {c.title}?",
            answer=f"They were {a.id} and {b.id}, two heroes from different houses who both wanted to win the contest.",
        ),
        QAItem(
            question=f"What went wrong when they tried the selfish shortcut?",
            answer=f"They tried to {c.shortcut}, but that made the task stumble into a comic mishap instead of helping them win.",
        ),
        QAItem(
            question=f"How did they finally succeed?",
            answer=f"They succeeded by choosing {tool.phrase} and working together, so they could {c.verb} without ruining the chance for the prize.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    c = world.contest
    qa = [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help one another and use their different strengths together to finish a job.",
        ),
        QAItem(
            question="What does caution mean?",
            answer="Caution means being careful and thinking ahead so you do not make a foolish mistake.",
        ),
        QAItem(
            question="Why can competition be fun?",
            answer="Competition can be fun when everyone tries hard, follows the rules, and learns something even if they do not win.",
        ),
    ]
    if "harp" in c.tags:
        qa.append(
            QAItem(
                question="What is a harp?",
                answer="A harp is a stringed instrument that makes bright music when its strings are plucked.",
            )
        )
    if "berry" in c.tags:
        qa.append(
            QAItem(
                question="What is a berry?",
                answer="A berry is a small fruit, and many berries are sweet and soft to eat.",
            )
        )
    if "river" in c.tags:
        qa.append(
            QAItem(
                question="What happens if a lantern gets wet?",
                answer="A wet lantern can go out, because water can put the flame out.",
            )
        )
    return qa


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
competitor(A) :- hero(A).
teamwork_needed(C) :- contest(C).

shortcut_fails(C) :- contest(C), risky_shortcut(C).
has_tool(C) :- contest(C), tool(T), helps(T, C).

valid_place(P, C) :- place(P), contest(C), affords(P, C), has_tool(C).
valid_story(P, C) :- valid_place(P, C), teamwork_needed(C), shortcut_fails(C).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for cid, c in CONTESTS.items():
        lines.append(asp.fact("contest", cid))
        lines.append(asp.fact("risky_shortcut", cid))
    for t in TOOLS:
        lines.append(asp.fact("tool", t.id))
        for g in sorted(t.guards):
            lines.append(asp.fact("helps", t.id, g))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))

def asp_verify() -> int:
    import asp
    py = sorted((p, c) for p in PLACES for c in CONTESTS if valid_combo(p, c) and select_tool(CONTESTS[c]))
    cl = asp_valid_stories()
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} stories).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("python:", py)
    print("asp:", cl)
    return 1


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mythic competition world with teamwork and cautionary humor.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--contest", choices=CONTESTS)
    ap.add_argument("--hero1")
    ap.add_argument("--hero2")
    ap.add_argument("--team1", choices=TEAM_NAMES)
    ap.add_argument("--team2", choices=TEAM_NAMES)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    contest = args.contest or rng.choice(list(CONTESTS))
    if not valid_combo(place, contest):
        raise StoryError(explain_rejection(place, contest))
    h1 = args.hero1 or rng.choice(HERO_NAMES)
    h2 = args.hero2 or rng.choice([n for n in HERO_NAMES if n != h1])
    t1 = args.team1 or rng.choice(TEAM_NAMES)
    t2 = args.team2 or rng.choice([t for t in TEAM_NAMES if t != t1])
    return StoryParams(place=place, contest=contest, hero1=h1, hero2=h2, team1=t1, team2=t2)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(
            f"  {e.id}: kind={e.kind} type={e.type} team={e.team} "
            f"meters={{{', '.join(f'{k}={v}' for k, v in e.meters.items() if v)}}} "
            f"memes={{{', '.join(f'{k}={v}' for k, v in e.memes.items() if v)}}}"
        )
    return "\n".join(lines)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        combos = []
        for place in PLACES:
            for contest in CONTESTS:
                if valid_combo(place, contest):
                    combos.append((place, contest))
        for i, (place, contest) in enumerate(combos):
            rng = random.Random(base_seed + i)
            params = StoryParams(
                place=place,
                contest=contest,
                hero1=rng.choice(HERO_NAMES),
                hero2=rng.choice([n for n in HERO_NAMES if n != params.hero1]) if HERO_NAMES else "Orin",
                team1=rng.choice(TEAM_NAMES),
                team2=rng.choice(TEAM_NAMES),
                seed=base_seed + i,
            )
            if params.hero2 == params.hero1:
                params.hero2 = next(n for n in HERO_NAMES if n != params.hero1)
            if params.team2 == params.team1:
                params.team2 = next(t for t in TEAM_NAMES if t != params.team1)
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
