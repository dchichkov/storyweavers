#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/means_daycare_room_suspense_flashback_bad_ending.py
==============================================================================================================================

A standalone story world in a daycare room, built from a tiny adventure premise:
a child wants something just out of reach, the room grows suspenseful, a flashback
explains why it matters, and the ending lands badly instead of neatly.

The world is intentionally small and constraint-checked. It includes "means":
objects and methods the child can try. Some means help, some are too risky, and
some fail in a way that produces a bad ending.

Style goals:
- child-facing prose
- adventure feel
- clear suspense
- a flashback beat
- a bad ending that still feels like a complete story

This script follows the Storyworld contract:
- defines StoryParams, parameter registries, build_parser, resolve_params,
  generate, emit, and main
- imports storyworlds/results.py eagerly
- imports storyworlds/asp.py lazily in ASP helpers
- includes an inline ASP_RULES twin and asp_facts()
- supports --verify, --show-asp, --asp, --json, --qa, --trace, --seed, -n, --all
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


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Means:
    id: str
    label: str
    kind: str
    risk: str
    helps: set[str] = field(default_factory=set)
    risky_for: set[str] = field(default_factory=set)
    clue: str = ""
    outcome: str = ""


@dataclass
class Goal:
    id: str
    label: str
    region: str
    trouble: str


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def copy(self) -> "World":
        import copy
        other = World(self.place)
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        other.facts = dict(self.facts)
        return other


GIRL_NAMES = ["Mia", "Lily", "Nora", "Zoe", "Ava", "Ella"]
BOY_NAMES = ["Leo", "Ben", "Finn", "Noah", "Eli", "Max"]
TRAITS = ["curious", "brave", "small", "careful", "playful", "quiet"]


PLACES = {
    "daycare_room": Place(name="the daycare room", affords={"reach", "search", "build", "read"}),
}

MEANS = {
    "stool": Means(
        id="stool",
        label="a little stool",
        kind="stool",
        risk="wobbled",
        helps={"reach"},
        risky_for={"climb"},
        clue="The stool could help reach a shelf, but only if it stayed steady.",
        outcome="the stool tipped",
    ),
    "flashlight": Means(
        id="flashlight",
        label="a tiny flashlight",
        kind="light",
        risk="made shadows jump",
        helps={"search"},
        risky_for=set(),
        clue="The flashlight could help search under the cubbies.",
        outcome="the beam found nothing",
    ),
    "basket_hook": Means(
        id="basket_hook",
        label="a long basket hook",
        kind="tool",
        risk="scraped the wall",
        helps={"reach"},
        risky_for={"grab"},
        clue="The hook could pull a basket down from high up.",
        outcome="the basket slid away",
    ),
    "story_card": Means(
        id="story_card",
        label="a story card with pictures",
        kind="memory",
        risk="made the child remember",
        helps={"read"},
        risky_for=set(),
        clue="The story card could remind the child where the toy was last seen.",
        outcome="the memory hurt more than it helped",
    ),
}

GOALS = {
    "teddy": Goal(
        id="teddy",
        label="a missing teddy",
        region="shelf",
        trouble="It had been left behind after nap time.",
    ),
    "star_crayon": Goal(
        id="star_crayon",
        label="a star-shaped crayon",
        region="bin",
        trouble="It had rolled under the art shelf.",
    ),
    "blue_blanket": Goal(
        id="blue_blanket",
        label="a blue blanket",
        region="cubby",
        trouble="It was folded in the wrong cubby, where nobody looked first.",
    ),
}


@dataclass
class StoryParams:
    place: str
    goal: str
    means: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


class Navigator:
    def __init__(self, world: World, hero: Entity, helper: Entity, goal: Goal, means: Means):
        self.world = world
        self.hero = hero
        self.helper = helper
        self.goal = goal
        self.means = means

    def setup(self) -> None:
        self.hero.memes["want"] = 1
        self.world.say(
            f"{self.hero.id} was a {self.hero.memes.get('trait_word', 'small')} "
            f"{self.hero.type} who loved adventures in {self.world.place.name}."
        )
        self.world.say(
            f"One day, {self.hero.id} needed {self.goal.label}, and {self.goal.trouble}"
        )

    def suspense(self) -> None:
        self.hero.memes["worry"] = 1
        self.world.para()
        self.world.say(
            f"The room felt quiet and tense. {self.hero.id} peeked under chairs, "
            f"but the missing thing was still not there."
        )
        self.world.say(
            f"{self.helper.pronoun().capitalize()} held up {self.means.label} and said "
            f"it might help, though it might also {self.means.risk}."
        )

    def flashback(self) -> None:
        self.world.say(
            f"Then {self.hero.id} remembered an earlier day: the {self.goal.label} "
            f"had been put away in a hurry, and nobody had checked the right spot."
        )
        self.hero.memes["memory"] = 1

    def bad_ending(self) -> None:
        self.world.para()
        self.hero.memes["sad"] = 1
        self.world.say(
            f"{self.hero.id} tried the {self.means.kind}, but {self.means.outcome}."
        )
        self.world.say(
            f"In the end, {self.goal.label} stayed lost, and the daycare room still "
            f"felt too big and too quiet."
        )

    def run(self) -> None:
        self.setup()
        self.world.para()
        self.suspense()
        self.flashback()
        self.bad_ending()


def valid_story_combo(goal: Goal, means: Means) -> bool:
    return bool(goal.region and means.helps and goal.id in {"teddy", "star_crayon", "blue_blanket"})


def choose_means(goal: Goal, means: Means) -> bool:
    if goal.id == "teddy":
        return means.id in {"flashlight", "story_card"}
    if goal.id == "star_crayon":
        return means.id in {"flashlight", "stool", "basket_hook"}
    if goal.id == "blue_blanket":
        return means.id in {"stool", "basket_hook", "story_card"}
    return False


def format_goal(goal: Goal) -> str:
    return goal.label


def tell(place: Place, goal: Goal, means: Means, hero_name: str, hero_type: str,
         hero_traits: Optional[list[str]] = None, parent_type: str = "teacher") -> World:
    world = World(place)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        meters={},
        memes={"trait_word": 1},
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=parent_type,
        label="the teacher",
    ))
    world.add(Entity(
        id="Goal",
        type=goal.id,
        label=goal.label,
        phrase=goal.label,
        owner=hero.id,
        caretaker=helper.id,
    ))
    hero.memes["trait_word"] = 1
    if hero_traits:
        hero.memes["traits"] = len(hero_traits)
    nav = Navigator(world, hero, helper, goal, means)
    nav.run()
    world.facts.update(hero=hero, helper=helper, goal=goal, means=means, place=place)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    goal = f["goal"]
    means = f["means"]
    return [
        f'Write a short adventure story for a young child set in a daycare room, '
        f'using the word "means" and involving {hero.id} trying to find {goal.label}.',
        f"Tell a suspenseful daycare-room story where {hero.id} uses {means.label} "
        f"to search for {goal.label}, but the plan ends badly.",
        f'Write a simple story with a flashback, a tense search, and a bad ending '
        f'about {goal.label} in a daycare room.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    goal = f["goal"]
    means = f["means"]
    return [
        QAItem(
            question=f"What was {hero.id} trying to find in the daycare room?",
            answer=f"{hero.id} was trying to find {goal.label}, which had gone missing in the daycare room.",
        ),
        QAItem(
            question=f"What means did the helper offer to help search?",
            answer=f"The helper offered {means.label} as a means to search, even though it might not work well.",
        ),
        QAItem(
            question=f"Why did the story feel suspenseful?",
            answer=(
                f"It felt suspenseful because {hero.id} kept searching and the room stayed quiet, "
                f"so it seemed like the missing {goal.label} might stay hidden."
            ),
        ),
        QAItem(
            question=f"What did {hero.id} remember in the flashback?",
            answer=(
                f"{hero.id} remembered that the {goal.label} had been put away in a hurry earlier, "
                f"which explained why nobody found it right away."
            ),
        ),
        QAItem(
            question="How did the story end?",
            answer=(
                f"It ended badly: {hero.id} tried the {means.kind}, but it did not solve the problem, "
                f"and the missing {goal.label} stayed lost."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a means?",
            answer="A means is a way of doing something or a tool you use to try to solve a problem.",
        ),
        QAItem(
            question="What is a daycare room?",
            answer="A daycare room is a place where young children play, learn, and rest with helpers nearby.",
        ),
        QAItem(
            question="What does suspense mean in a story?",
            answer="Suspense means the story makes you wonder what will happen next and feel a little tense.",
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is a story moment that looks back to something that happened before.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.kind:
            bits.append(f"kind={e.kind}")
        if e.type:
            bits.append(f"type={e.type}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id}: " + ", ".join(bits))
    lines.append(f"  place: {world.place.name}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="daycare_room", goal="teddy", means="flashlight", name="Mia", gender="girl", parent="teacher", trait="curious"),
    StoryParams(place="daycare_room", goal="star_crayon", means="stool", name="Leo", gender="boy", parent="teacher", trait="brave"),
    StoryParams(place="daycare_room", goal="blue_blanket", means="story_card", name="Nora", gender="girl", parent="teacher", trait="quiet"),
]


def explain_rejection(goal: Goal, means: Means) -> str:
    return (
        f"(No story: {means.label} is not a sensible means for {goal.label} in this daycare room. "
        f"Try a different means that fits the search.)"
    )


ASP_RULES = r"""
valid_means(goal(teddy), flashlight).
valid_means(goal(teddy), story_card).
valid_means(goal(star_crayon), flashlight).
valid_means(goal(star_crayon), stool).
valid_means(goal(star_crayon), basket_hook).
valid_means(goal(blue_blanket), stool).
valid_means(goal(blue_blanket), basket_hook).
valid_means(goal(blue_blanket), story_card).

story(goal(G), means(M)) :- valid_means(goal(G), M).
#show story/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("place", "daycare_room"))
    for gid, goal in GOALS.items():
        lines.append(asp.fact("goal", gid))
        lines.append(asp.fact("region", gid, goal.region))
    for mid, means in MEANS.items():
        lines.append(asp.fact("means", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show story/2."))
    return sorted(set(asp.atoms(model, "story")))


def asp_verify() -> int:
    asp_set = set(asp_valid_combos())
    py_set = set((g, m) for g in GOALS for m in MEANS if choose_means(GOALS[g], MEANS[m]))
    if asp_set == py_set:
        print(f"OK: clingo gate matches python gate ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and python gates:")
    print("only in asp:", sorted(asp_set - py_set))
    print("only in python:", sorted(py_set - asp_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Daycare-room adventure story world with suspense, flashback, and a bad ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--means", choices=MEANS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["teacher"])
    ap.add_argument("--name")
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
    goals = list(GOALS)
    means_ids = list(MEANS)
    combos = [(g, m) for g in goals for m in means_ids if choose_means(GOALS[g], MEANS[m])]
    if args.goal and args.means:
        if not choose_means(GOALS[args.goal], MEANS[args.means]):
            raise StoryError(explain_rejection(GOALS[args.goal], MEANS[args.means]))
    filtered = [
        (g, m) for g, m in combos
        if (args.goal is None or g == args.goal) and (args.means is None or m == args.means)
    ]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    goal_id, means_id = rng.choice(sorted(filtered))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(
        place="daycare_room",
        goal=goal_id,
        means=means_id,
        name=name,
        gender=gender,
        parent="teacher",
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place],
        GOALS[params.goal],
        MEANS[params.means],
        params.name,
        params.gender,
        [params.trait],
        params.parent,
    )
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible goal/means combos:\n")
        for g, m in combos:
            print(f"  {g[0].upper() + g[1:]:14} {m}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.goal} using {p.means}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
