#!/usr/bin/env python3
"""
storyworlds/worlds/adult_mischievous_efficient_moral_value_suspense_rhyming.py
==============================================================================

A tiny, self-contained story world for a rhyming tale about an adult who is
mischievous, efficient, and pushed toward a moral choice under suspense.

The story is built from a short simulated domain:
- an adult protagonist with a nimble mind and a playful streak,
- a small task or temptation,
- a moral test involving honesty, kindness, or fairness,
- a suspense beat where something is briefly uncertain,
- a clean resolution that proves what changed.

The prose aims to read like a short rhyming story for children while still being
driven by world state rather than a frozen template.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    visible: bool = True
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ("worry", "suspense", "mess", "tired", "help", "order", "risk"):
            self.meters.setdefault(key, 0.0)
        for key in ("mischief", "efficiency", "honesty", "kindness", "patience", "relief"):
            self.memes.setdefault(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"woman", "girl", "mother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"man", "boy", "father", "uncle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    id: str
    label: str
    indoors: bool
    ambience: str
    hidden_spots: list[str]


@dataclass
class Goal:
    id: str
    name: str
    verb: str
    clue: str
    risk_text: str
    moral: str
    suspense_text: str
    solution: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    goal: str
    name: str
    gender: str
    role: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
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

    def copy(self) -> "World":
        import copy as _copy

        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


ACTIONS = {
    "search": "search for",
    "return": "return",
    "share": "share",
    "fix": "fix",
}

PLACES = {
    "night_market": Place(
        id="night_market",
        label="the night market",
        indoors=False,
        ambience="The stalls glowed gold, and the air smelled sweet.",
        hidden_spots=["behind a crate", "under a cloth", "near a lantern"],
    ),
    "library": Place(
        id="library",
        label="the library",
        indoors=True,
        ambience="The rooms were hushed, and the shelves stood like towers.",
        hidden_spots=["between books", "under a chair", "behind a stack"],
    ),
    "harbor": Place(
        id="harbor",
        label="the harbor",
        indoors=False,
        ambience="The water winked silver, and ropes tapped the docks.",
        hidden_spots=["by a barrel", "under a plank", "near a net"],
    ),
}

GOALS = {
    "lost_note": Goal(
        id="lost_note",
        name="a lost note",
        verb="find",
        clue="a little note",
        risk_text="someone might miss the note dearly",
        moral="honesty",
        suspense_text="the note was hidden where no one could see",
        solution="return it to the right hand",
        tags={"honesty", "lost", "paper"},
    ),
    "dropped_key": Goal(
        id="dropped_key",
        name="a dropped key",
        verb="find",
        clue="a tiny brass key",
        risk_text="a door might stay shut until the key came home",
        moral="kindness",
        suspense_text="the key had slipped into a dark crack",
        solution="give it back before evening",
        tags={"kindness", "key", "metal"},
    ),
    "stolen_cookie": Goal(
        id="stolen_cookie",
        name="a stolen cookie",
        verb="stop",
        clue="a warm cookie",
        risk_text="a hungry child might cry if it vanished",
        moral="fairness",
        suspense_text="the cookie was almost out of sight",
        solution="share it fairly",
        tags={"fairness", "food"},
    ),
}


def ensure_valid(place: Place, goal: Goal) -> None:
    if not place.indoors and goal.id == "stolen_cookie":
        return
    if place.indoors and goal.id == "stolen_cookie":
        return
    if place.indoors and goal.id == "dropped_key":
        return
    if not place.indoors and goal.id == "lost_note":
        return


def rhyming_opening(hero: Entity, place: Place, goal: Goal) -> str:
    return (
        f"{hero.id} was an adult with a clever wink, "
        f"and {hero.pronoun('possessive')} plans were quick as a blink. "
        f"{hero.pronoun().capitalize()} liked a small prank, a tiny sly joke, "
        f"yet {hero.pronoun('possessive')} heart stayed kind like a warm camp smoke."
    )


def rhyming_setup(hero: Entity, place: Place, goal: Goal) -> str:
    return (
        f"At {place.label}, {place.ambience} "
        f"{hero.id} spotted {goal.clue}, and {hero.pronoun('subject')} did not stay still. "
        f"To get it done fast, with a clever small grin, {hero.pronoun('subject')} rushed in."
    )


def rhyming_tension(hero: Entity, goal: Goal) -> str:
    return (
        f"But the sight brought a tug, a hush, and a test: "
        f"{goal.suspense_text}. "
        f"{hero.id} felt a flutter of worry and thrill, "
        f"for doing the right thing would need steady will."
    )


def rhyming_turn(hero: Entity, goal: Goal) -> str:
    return (
        f"{hero.id} chose not to be sly for a gain, "
        f"and listened for clues in the wind and the rain. "
        f"With calm little steps and efficient speed, "
        f"{hero.pronoun('subject')} followed the trail to the one in need."
    )


def rhyming_end(hero: Entity, goal: Goal) -> str:
    return (
        f"At last came the moment, so bright and so clear: "
        f"{hero.id} put things right and made the trouble disappear. "
        f"The lost thing was home, the waiting hearts sighed, "
        f"and {hero.id} walked on with a proud kind stride."
    )


def simulate(world: World, hero: Entity, goal: Goal) -> None:
    hero.memes["mischief"] += 1.0
    hero.memes["efficiency"] += 1.0
    hero.meters["suspense"] += 1.0
    hero.meters["risk"] += 1.0

    world.say(rhyming_opening(hero, world.place, goal))
    world.para()
    world.say(rhyming_setup(hero, world.place, goal))

    world.para()
    hero.meters["worry"] += 1.0
    world.say(rhyming_tension(hero, goal))

    world.para()
    hero.memes["honesty"] += 1.0
    hero.memes["kindness"] += 1.0
    hero.meters["suspense"] = 0.0
    hero.meters["risk"] = 0.0
    hero.meters["help"] += 1.0
    hero.meters["order"] += 1.0
    world.say(rhyming_turn(hero, goal))
    world.say(
        f"{goal.solution.capitalize()}, and that made the day feel light. "
        f"{hero.id} smiled, because the moral felt right."
    )

    world.para()
    hero.memes["relief"] += 1.0
    hero.meters["worry"] = 0.0
    world.say(rhyming_end(hero, goal))

    world.facts.update(hero=hero, place=world.place, goal=goal)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    goal: Goal = f["goal"]
    place: Place = f["place"]
    return [
        f'Write a short rhyming story about an adult named {hero.id} at {place.label} who faces {goal.name}.',
        f"Tell a gentle suspense story with a moral choice, using the clue {goal.clue!r} and a clever adult hero.",
        f"Write a child-friendly rhyming tale where {hero.id} is mischievous but chooses {goal.moral} at {place.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    goal: Goal = f["goal"]
    place: Place = f["place"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, an adult who is mischievous and efficient, but still chooses to do the right thing.",
        ),
        QAItem(
            question=f"What was the tricky thing {hero.id} noticed at {place.label}?",
            answer=f"{hero.id} noticed {goal.clue} at {place.label}, and that led to a suspenseful choice.",
        ),
        QAItem(
            question=f"What moral value did {hero.id} show in the end?",
            answer=f"{hero.id} showed {goal.moral} by choosing to {goal.solution}.",
        ),
        QAItem(
            question=f"How did the suspense end?",
            answer=f"The suspense ended when {hero.id} acted carefully, solved the problem, and made things right.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "honesty": (
        "What is honesty?",
        "Honesty means telling the truth and not trying to trick others.",
    ),
    "kindness": (
        "What is kindness?",
        "Kindness means helping others and caring about their feelings.",
    ),
    "fairness": (
        "What is fairness?",
        "Fairness means giving people an equal and reasonable chance.",
    ),
    "suspense": (
        "What does suspense mean in a story?",
        "Suspense is the feeling that makes you wonder what will happen next.",
    ),
    "mischief": (
        "What is mischief?",
        "Mischief is playful trouble that is small and usually not mean.",
    ),
    "efficient": (
        "What does efficient mean?",
        "Efficient means doing a job well and without wasting time or effort.",
    ),
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    goal: Goal = f["goal"]
    tags = set(goal.tags) | {"suspense", "mischief", "efficient"}
    out: list[QAItem] = []
    for key, pair in WORLD_KNOWLEDGE.items():
        if key in tags:
            q, a = pair
            out.append(QAItem(question=q, answer=a))
    return out


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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def build_story(hero_name: str, gender: str, role: str, place_key: str, goal_key: str) -> StorySample:
    place = PLACES[place_key]
    goal = GOALS[goal_key]
    ensure_valid(place, goal)
    world = World(place)

    hero_type = "woman" if gender == "woman" else "man"
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=role))
    world.add(Entity(id="goal", kind="thing", type=goal.id, label=goal.name, owner=hero.id))

    simulate(world, hero, goal)
    params = StoryParams(place=place_key, goal=goal_key, name=hero_name, gender=gender, role=role)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def valid_combos() -> list[tuple[str, str]]:
    return [(p, g) for p in PLACES for g in GOALS]


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.indoors:
            lines.append(asp.fact("indoors", pid))
        for h in place.hidden_spots:
            lines.append(asp.fact("hides", pid, h))
    for gid, goal in GOALS.items():
        lines.append(asp.fact("goal", gid))
        lines.append(asp.fact("moral", gid, goal.moral))
        for tag in sorted(goal.tags):
            lines.append(asp.fact("tag", gid, tag))
    return "\n".join(lines)


ASP_RULES = r"""
valid_combo(P, G) :- place(P), goal(G).

#show valid_combo/2.
"""


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in ASP:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming story world about adult mischief, efficiency, suspense, and moral choice.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["man", "woman"])
    ap.add_argument("--role", choices=["baker", "clerk", "gardener", "neighbor", "porter"], default="neighbor")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.goal:
        combos = [c for c in combos if c[1] == args.goal]
    if not combos:
        raise StoryError("No valid story matches the chosen place and goal.")
    place, goal = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["man", "woman"])
    name = args.name or rng.choice(["Mara", "Jonah", "Celia", "Rowan", "Drew", "Nina"])
    role = args.role
    return StoryParams(place=place, goal=goal, name=name, gender=gender, role=role)


def generate(params: StoryParams) -> StorySample:
    return build_story(params.name, params.gender, params.role, params.place, params.goal)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(place="night_market", goal="lost_note", name="Mara", gender="woman", role="clerk"),
    StoryParams(place="library", goal="dropped_key", name="Jonah", gender="man", role="porter"),
    StoryParams(place="harbor", goal="stolen_cookie", name="Nina", gender="woman", role="neighbor"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for p, g in combos:
            print(f"  {p:12} {g}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
