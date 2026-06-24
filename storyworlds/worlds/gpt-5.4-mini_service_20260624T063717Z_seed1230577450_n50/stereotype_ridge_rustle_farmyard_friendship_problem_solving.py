#!/usr/bin/env python3
"""
storyworlds/worlds/stereotype_ridge_rustle_farmyard_friendship_problem_solving.py
=================================================================================

A small, self-contained storyworld about a farmyard misunderstanding that gets
solved with kindness, friendship, and problem solving.

Seed image:
- A child hears a rustle on the ridge in the farmyard and assumes a stereotype
  about what it means.
- The friend helps investigate.
- The solution is funny, concrete, and kind.

The world is built to produce short, child-facing comedy stories with a clear
problem and a warm resolution.
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
# World model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the farmyard"
    ridge: str = "the ridge"
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    sound: str
    topic: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    phrase: str
    location: str
    mishap: str
    fix_hint: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    tool: str
    action: str
    outcome: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "farmyard": Setting(place="the farmyard", ridge="the ridge", affords={"rustle"}),
}

ACTIVITIES = {
    "rustle": Activity(
        id="rustle",
        verb="follow the rustle",
        gerund="following the rustle",
        rush="dash toward the ridge",
        sound="rustle",
        topic="rustle",
        tags={"rustle", "ridge"},
    ),
}

PROBLEMS = {
    "haystack": Problem(
        id="haystack",
        label="haystack",
        phrase="a tall haystack near the ridge",
        location="the ridge",
        mishap="was only a rabbit wiggling in the hay",
        fix_hint="look closely",
        tags={"ridge", "rustle"},
    ),
    "basket": Problem(
        id="basket",
        label="basket",
        phrase="a tipped-over basket by the gate",
        location="the gate",
        mishap="had dropped apples and made a silly clatter",
        fix_hint="pick up the apples together",
        tags={"rustle"},
    ),
}

HELPERS = {
    "friend": Helper(
        id="friend",
        label="best friend",
        tool="a little lantern",
        action="shine the lantern on the spot",
        outcome="see the truth and laugh",
        tags={"friendship", "kindness", "problem_solving"},
    ),
}

NAMES = ["Milo", "Ada", "Pip", "Nia", "Toby", "Luna", "Bea", "Otis"]
FRIEND_NAMES = ["June", "Ezra", "Ruby", "Sam", "Ivy", "Noah"]
TRAITS = ["cheerful", "curious", "silly", "brave", "helpful"]
STEREOTYPES = [
    "a sneaky fox",
    "a grumpy wolf",
    "a giant monster",
    "a naughty goose",
]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    activity: str
    problem: str
    name: str
    friend_name: str
    trait: str
    stereotype: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness and ASP twin
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            for prob_id, prob in PROBLEMS.items():
                if {"rustle", "ridge"} & prob.tags:
                    combos.append((place, act_id, prob_id))
    return combos


ASP_RULES = r"""
% A story is valid when the farmyard supports the activity and the chosen
% problem is plausibly connected to the rustle/ridge misunderstanding.
valid(Place, Act, Prob) :- affords(Place, Act), activity(Act), problem(Prob),
                           connects(Prob, Act).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for prob_id, prob in PROBLEMS.items():
        lines.append(asp.fact("problem", prob_id))
        for tag in sorted(prob.tags):
            lines.append(asp.fact("connects", prob_id, tag))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    p = set(valid_combos())
    a = set(asp_valid_combos())
    if p == a:
        print(f"OK: clingo gate matches valid_combos() ({len(p)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - p:
        print("  only in clingo:", sorted(a - p))
    if p - a:
        print("  only in python:", sorted(p - a))
    return 1


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Farmyard comedy storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--name")
    ap.add_argument("--friend-name")
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--stereotype", choices=STEREOTYPES)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place and args.place not in SETTINGS:
        raise StoryError("Unknown place.")
    if args.activity and args.activity not in ACTIVITIES:
        raise StoryError("Unknown activity.")
    if args.problem and args.problem not in PROBLEMS:
        raise StoryError("Unknown problem.")

    filtered = [
        c for c in combos
        if (args.place is None or c[0] == args.place)
        and (args.activity is None or c[1] == args.activity)
        and (args.problem is None or c[2] == args.problem)
    ]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, problem = rng.choice(filtered)
    return StoryParams(
        place=place,
        activity=activity,
        problem=problem,
        name=args.name or rng.choice(NAMES),
        friend_name=args.friend_name or rng.choice(FRIEND_NAMES),
        trait=args.trait or rng.choice(TRAITS),
        stereotype=args.stereotype or rng.choice(STEREOTYPES),
    )


def introduce(world: World, hero: Entity, friend: Entity, act: Activity) -> None:
    world.say(
        f"{hero.id} was a {hero.traits[0]} child who loved {act.gerund} at {world.setting.place}. "
        f"{friend.id} was {hero.id}'s best friend, and the two of them liked to solve tiny troubles together."
    )


def build_problem_line(world: World, prob: Problem, stereotype: str) -> None:
    world.say(
        f"One day, a rustle came from {prob.location}, and {world.facts['hero'].id} blurted, "
        f'"It must be {stereotype}!"'
    )


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.place]
    activity = ACTIVITIES[params.activity]
    problem = PROBLEMS[params.problem]
    world = World(setting)

    hero = world.add(Entity(id=params.name, kind="character", type="child", traits=[params.trait, "kind"]))
    friend = world.add(Entity(id=params.friend_name, kind="character", type="child", traits=["friendly", "helpful"]))

    world.facts.update(hero=hero, friend=friend, activity=activity, problem=problem, params=params)

    introduce(world, hero, friend, activity)
    world.para()
    world.say(
        f"The {activity.sound} from the ridge made {hero.id} stare wide-eyed."
    )
    build_problem_line(world, problem, params.stereotype)
    world.say(
        f"{friend.id} did not laugh at the guess. Instead, {friend.id} said, "
        f'"Let us {problem.fix_hint} and see."'
    )
    world.para()
    world.say(
        f"The two friends went to {problem.location}. {friend.id} held up {HELPERS['friend'].tool}, "
        f"{HELPERS['friend'].action}, and soon they could {HELPERS['friend'].outcome}."
    )
    world.say(
        f"It was only {problem.mishap}, not a monster at all. {hero.id} laughed so hard that the hens looked offended."
    )
    world.say(
        f"Then {hero.id} and {friend.id} fixed the little mess together, proving that friendship, kindness, and problem solving can tame even the silliest surprise."
    )

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    p: StoryParams = world.facts["params"]
    return [
        f"Write a funny farmyard story about {p.name} hearing a rustle on the ridge.",
        f"Tell a comedy for young children where {p.name} and {p.friend_name} use kindness to solve a problem.",
        f"Make a simple story that includes the words stereotype, ridge, and rustle.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    hero: Entity = world.facts["hero"]
    friend: Entity = world.facts["friend"]
    problem: Problem = world.facts["problem"]
    activity: Activity = world.facts["activity"]
    return [
        QAItem(
            question=f"Who heard the rustle on the ridge?",
            answer=f"{hero.id} heard it first, then {friend.id} helped make sense of it.",
        ),
        QAItem(
            question=f"What did {hero.id} think the rustle was?",
            answer=f"{hero.id} guessed it was {p.stereotype}. That guess was funny, but it was wrong.",
        ),
        QAItem(
            question=f"How did {hero.id} and {friend.id} solve the problem?",
            answer=f"They went to {problem.location}, looked closely, and fixed the little trouble together.",
        ),
        QAItem(
            question=f"What good features showed up in the story?",
            answer="Friendship, kindness, and problem solving helped turn the scare into a joke.",
        ),
        QAItem(
            question=f"What was the sound word in the story?",
            answer=f"The sound word was {activity.sound}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is friendship?",
            answer="Friendship is when people care about each other, help each other, and enjoy being together.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means thinking carefully and trying different ideas until a problem is fixed.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means being gentle, helpful, and thoughtful to someone else.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for x in sample.prompts:
        lines.append(x)
    lines.append("")
    lines.append("== Story QA ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} traits={e.traits}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("farmyard", "rustle", "haystack", "Milo", "June", "curious", "a sneaky fox"),
            StoryParams("farmyard", "rustle", "basket", "Ada", "Ruby", "cheerful", "a grumpy wolf"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 40, 40):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
