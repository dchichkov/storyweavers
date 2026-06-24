#!/usr/bin/env python3
"""
storyworlds/worlds/bridge_top_conflict_bad_ending_teamwork_adventure.py
=======================================================================

A small adventure storyworld about a group crossing a bridge to reach the top
of a hill. The world has one main tension: a wrong choice can lead to a bad
ending, but teamwork turns it into a safe, satisfying trip.

The simulated model tracks:
- physical meters: distance to the top, bridge stability, storm pressure
- emotional memes: worry, confidence, teamwork, conflict

The story is generated from state changes, not from a frozen template.
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
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def they(self) -> str:
        return "they" if self.plural else self.pronoun("subject")

    def them(self) -> str:
        return "them" if self.plural else self.pronoun("object")

    def their(self) -> str:
        return "their" if self.plural else self.pronoun("possessive")


@dataclass
class Place:
    id: str
    label: str
    affords: set[str]
    risky: bool = False


@dataclass
class Goal:
    id: str
    label: str
    phrase: str
    top_word: str = "top"


@dataclass
class Tool:
    id: str
    label: str
    help_text: str
    guards: set[str]


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.story: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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

    def copy(self) -> "World":
        import copy
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "riverbank": Place("riverbank", "the riverbank", {"cross_bridge", "climb_top"}, risky=True),
    "trail": Place("trail", "the winding trail", {"climb_top"}, risky=False),
    "camp": Place("camp", "the forest camp", {"cross_bridge", "climb_top"}, risky=False),
}

GOALS = {
    "hill_top": Goal("hill_top", "the hill top", "reach the top of the hill", top_word="top"),
    "watch_tower_top": Goal("watch_tower_top", "the tower top", "reach the top of the tower", top_word="top"),
}

TOOLS = {
    "rope": Tool("rope", "a long rope", "tie the group together across the bridge", {"fall"}),
    "lantern": Tool("lantern", "a bright lantern", "light the path when the clouds get dark", {"dark"}),
    "map": Tool("map", "a folded map", "show the safest way toward the top", {"lost"}),
}

NAMES = ["Nora", "Milo", "Ari", "Tia", "Lena", "Owen", "Pip", "Zane"]
TYPES = {"girl": ["Nora", "Tia", "Lena"], "boy": ["Milo", "Ari", "Owen", "Pip", "Zane"]}
TRAITS = ["curious", "brave", "restless", "clever", "cheerful"]


@dataclass
class StoryParams:
    place: str
    goal: str
    hero: str
    gender: str
    friend: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness and simulation
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str]]:
    return [(p, g) for p, place in PLACES.items() for g in GOALS if "cross_bridge" in place.affords and "climb_top" in place.affords]


def aspire(world: World, hero: Entity, friend: Entity, goal: Goal) -> None:
    world.say(
        f"{hero.id} and {friend.id} wanted to {goal.phrase}, and the idea felt like a real adventure."
    )
    hero.memes["hope"] = hero.memes.get("hope", 0) + 1
    friend.memes["hope"] = friend.memes.get("hope", 0) + 1


def arrive(world: World, hero: Entity, friend: Entity, goal: Goal) -> None:
    world.say(
        f"One morning, {hero.id} and {friend.id} came to {world.place.label}, where an old bridge led toward {goal.label}."
    )


def conflict(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    friend.memes["worry"] = friend.memes.get("worry", 0) + 1
    hero.memes["conflict"] = hero.memes.get("conflict", 0) + 1
    world.say(
        f"{hero.id} wanted to rush ahead, but {friend.id} wanted to check every plank, and their different ideas caused a small conflict."
    )


def bad_ending_check(world: World, hero: Entity) -> bool:
    return hero.memes.get("conflict", 0) >= 1 and world.place.risky


def teamwork_fix(world: World, hero: Entity, friend: Entity, goal: Goal) -> Tool:
    tool = TOOLS["rope"]
    hero.memes["teamwork"] = hero.memes.get("teamwork", 0) + 1
    friend.memes["teamwork"] = friend.memes.get("teamwork", 0) + 1
    hero.memes["conflict"] = 0
    friend.memes["conflict"] = 0
    world.say(
        f"Then they chose teamwork: {hero.id} held {friend.id}'s hand, and {friend.id} used {tool.label} to keep them steady."
    )
    world.say(
        f"Together, they crossed the bridge, found the last climb, and reached {goal.label} without a bad ending."
    )
    return tool


def tell_story(world: World, params: StoryParams) -> World:
    hero = world.add(Entity(id=params.hero, kind="character", type=params.gender))
    friend_name = params.friend
    friend_type = "boy" if params.gender == "girl" else "girl"
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type))
    goal = GOALS[params.goal]

    aspire(world, hero, friend, goal)
    world.para()
    arrive(world, hero, friend, goal)
    conflict(world, hero, friend)

    if bad_ending_check(world, hero):
        world.say(
            f"If they kept arguing, the bridge would have felt scary and the trip might have ended badly."
        )
    world.para()
    teamwork_fix(world, hero, friend, goal)

    world.facts.update(hero=hero, friend=friend, goal=goal, tool=TOOLS["rope"])
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short adventure story for a young child about {f["hero"].id} and {f["friend"].id} crossing a bridge to reach {f["goal"].label}.',
        f"Tell a story where a small conflict on a bridge is solved by teamwork and the friends still reach the top.",
        f'Write a gentle adventure story that includes the words "bridge" and "top" and ends happily after teamwork.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, goal = f["hero"], f["friend"], f["goal"]
    return [
        QAItem(
            question=f"Who went on the adventure to reach {goal.label}?",
            answer=f"{hero.id} and {friend.id} went together on the adventure to reach {goal.label}.",
        ),
        QAItem(
            question="What caused the conflict on the bridge?",
            answer=f"The conflict happened because {hero.id} wanted to hurry and {friend.id} wanted to check the bridge more carefully.",
        ),
        QAItem(
            question="How did they fix the bad ending?",
            answer="They fixed it by choosing teamwork, holding on, and using a rope to stay steady across the bridge.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bridge for?",
            answer="A bridge helps people cross over water, a road, or another gap safely.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other and work together toward the same goal.",
        ),
        QAItem(
            question="What is the top of a hill?",
            answer="The top of a hill is the highest place on the hill.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story questions ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== World knowledge ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(P) :- place_fact(P).
goal(G) :- goal_fact(G).
valid(P,G) :- place_fact(P), goal_fact(G), good_place(P), good_goal(G).
good_place(riverbank).
good_place(trail).
good_place(camp).
good_goal(hill_top).
good_goal(watch_tower_top).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place_fact", pid))
    for gid in GOALS:
        lines.append(asp.fact("goal_fact", gid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(p, g) for p in PLACES for g in GOALS if p in PLACES and g in GOALS}
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(cl)} combos).")
        return 0
    print("Mismatch between ASP and Python.")
    print("only in python:", sorted(py - cl))
    print("only in asp:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Generate / emit
# ---------------------------------------------------------------------------
def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place not in PLACES:
        raise StoryError("Unknown place.")
    if args.goal and args.goal not in GOALS:
        raise StoryError("Unknown goal.")
    place = args.place or rng.choice(list(PLACES))
    goal = args.goal or rng.choice(list(GOALS))
    gender = args.gender or rng.choice(["girl", "boy"])
    hero = args.name or rng.choice(TYPES[gender])
    friend_pool = [n for n in NAMES if n != hero]
    friend = args.friend or rng.choice(friend_pool)
    if hero == friend:
        raise StoryError("Hero and friend must be different characters.")
    return StoryParams(place=place, goal=goal, hero=hero, gender=gender, friend=friend)


def generate(params: StoryParams) -> StorySample:
    world = World(PLACES[params.place])
    world = tell_story(world, params)
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
        print("--- trace ---")
        for e in sample.world.entities.values():
            print(e.id, e.meters, e.memes)
    if qa:
        print()
        print(format_qa(sample))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bridge-and-top adventure storyworld with conflict and teamwork.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--gender", choices=["girl", "boy"])
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid place/goal combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("riverbank", "hill_top", "Nora", "girl", "Milo"),
            StoryParams("camp", "watch_tower_top", "Owen", "boy", "Tia"),
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
            except StoryError as e:
                print(e)
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
