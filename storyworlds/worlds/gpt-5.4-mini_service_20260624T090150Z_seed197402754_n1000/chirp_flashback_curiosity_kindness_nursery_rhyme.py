#!/usr/bin/env python3
"""
A small standalone storyworld: chirp, flashback curiosity, and kindness,
told in a gentle nursery-rhyme style.

The world model tracks a little bird, a place, a curiosity-driven detour,
a flashback that changes the choice, and a kind act that resolves the story.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"distance": 0.0, "comfort": 0.0}
        if not self.memes:
            self.memes = {"curiosity": 0.0, "kindness": 0.0, "worry": 0.0, "flashback": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "bird", "chick", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    label: str
    sound: str
    shelter: str
    at_home: bool = False


@dataclass
class Goal:
    id: str
    name: str
    verb: str
    noun: str
    risk: str
    gentle_fix: str


@dataclass
class StoryParams:
    place: str
    goal: str
    name: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict[str, object] = {}

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
        import copy
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


def make_places() -> dict[str, Place]:
    return {
        "nest": Place("nest", "the nest", "soft chirps", "warm reeds", at_home=True),
        "garden": Place("garden", "the garden", "leafy rustles", "a hedge nook"),
        "orchard": Place("orchard", "the orchard", "apple-bud breezes", "a tree branch"),
    }


def make_goals() -> dict[str, Goal]:
    return {
        "seed": Goal("seed", "a shiny seed", "peck at", "seed", "it might roll away", "share it kindly"),
        "bell": Goal("bell", "a little bell", "follow", "bell", "it might lead the chick too far", "carry it home together"),
        "butterfly": Goal("butterfly", "a bright butterfly", "watch", "butterfly", "it might fly out of reach", "watch it from the path"),
    }


PLACES = make_places()
GOALS = make_goals()

NAMES = ["Pip", "Lulu", "Mimi", "Toto", "Nina", "Bibi", "Coco", "Daisy"]
TRAITS = ["tiny", "bright", "brave", "gentle", "curious", "merry"]


def reasoning_gate(place: Place, goal: Goal) -> bool:
    return True if place and goal else False


def flashback_hint(world: World, hero: Entity, goal: Goal) -> bool:
    if hero.memes["curiosity"] < THRESHOLD:
        return False
    hero.memes["flashback"] += 1
    world.say(
        f"{hero.id} paused and thought of another day, when a curious step had brought {hero.pronoun('object')} far from the nest."
    )
    return True


def predict_risk(world: World, hero: Entity, goal: Goal) -> bool:
    sim = world.copy()
    sim.get(hero.id).meters["distance"] += 1
    sim.get(hero.id).memes["curiosity"] += 1
    return goal.risk != ""


def tell_story(place: Place, goal: Goal, name: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=name, kind="character", type="bird", traits=["little", random.choice(TRAITS)]))
    helper = world.add(Entity(id="Helper", kind="character", type="bird", traits=["kind"]))
    item = world.add(Entity(id="Item", type=goal.id, label=goal.noun, phrase=goal.name, owner=hero.id))

    hero.memes["curiosity"] += 1
    hero.memes["kindness"] += 0
    helper.memes["kindness"] += 1

    world.say(
        f"Little {hero.id} in {place.label} was a {hero.traits[1]} bird, and every morning {hero.pronoun()} liked to chirp."
    )
    world.say(
        f"{place.label.capitalize()} answered with {place.sound}, and {hero.id} wondered what sweet thing was making the tune."
    )
    world.say(
        f"Then {hero.id} saw {item.phrase} and wanted to {goal.verb} it, though {goal.risk}."
    )

    world.para()
    hero.meters["distance"] += 1
    hero.memes["curiosity"] += 1
    world.say(
        f"Curiosity made {hero.id} hop along the path, chirp-chirp-chirping, and the little feet got farther from home."
    )
    flashback_hint(world, hero, goal)

    if predict_risk(world, hero, goal):
        hero.memes["worry"] += 1
        world.say(
            f"Then {hero.id} remembered the old trouble and felt a small worry in the chest."
        )
        world.say(
            f"Kind {helper.id} came near and said, 'Easy now, little one; we can {goal.gentle_fix}.'"
        )
        hero.memes["kindness"] += 1
        helper.memes["kindness"] += 1
        hero.memes["curiosity"] = max(0.0, hero.memes["curiosity"] - 1)
        hero.meters["distance"] = 0.0
        world.para()
        world.say(
            f"So {hero.id} turned back with {helper.id}, and together they {goal.verb} {item.label} the gentle way."
        )
        world.say(
            f"At last {hero.id} was near the nest again, chirping softly, while the morning stayed warm and bright."
        )

    world.facts.update(hero=hero, helper=helper, item=item, goal=goal, place=place)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    goal = f["goal"]
    place = f["place"]
    return [
        f'Write a short nursery-rhyme-style story about {hero.id} in {place.label} and the word "chirp".',
        f"Tell a gentle story where a little bird's curiosity leads away from home, then kindness brings {hero.id} back.",
        f"Write a child-friendly story about a flashback, a small worry, and a kind helper near {place.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    goal: Goal = f["goal"]
    place: Place = f["place"]
    return [
        QAItem(
            question=f"Who is the little bird in the story?",
            answer=f"The little bird is {hero.id}, and {hero.pronoun()} loves to chirp in {place.label}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do when {hero.id} saw {goal.noun}?",
            answer=f"{hero.id} wanted to {goal.verb} the {goal.noun}, but the story showed that {goal.risk}.",
        ),
        QAItem(
            question=f"Who helped {hero.id} choose the gentle way?",
            answer=f"{helper.id} helped {hero.id}, and {helper.id} was kind and calm.",
        ),
        QAItem(
            question="What did the flashback remind the bird about?",
            answer="The flashback reminded the bird that wandering too far could cause trouble, so the bird slowed down and chose home again.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does chirping sound like?",
            answer="Chirping is a light, quick bird sound, like tiny music in the morning.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is wanting to know more and to see what something is or where it goes.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means helping gently, sharing, and making another creature feel safe.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when the story remembers something that happened before.",
        ),
    ]


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(f"{i+1}. {p}" for i, p in enumerate(sample.prompts))
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


ASP_RULES = r"""
place(nest). place(garden). place(orchard).
goal(seed). goal(bell). goal(butterfly).

curiosity_drives(Place,Goal) :- place(Place), goal(Goal).
kindness_helps(Place,Goal) :- curiosity_drives(Place,Goal).
valid_story(Place,Goal) :- curiosity_drives(Place,Goal), kindness_helps(Place,Goal).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES.values():
        lines.append(asp.fact("place", p.id))
    for g in GOALS.values():
        lines.append(asp.fact("goal", g.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(p.id, g.id) for p in PLACES.values() for g in GOALS.values() if reasoning_gate(p, g)}
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches python ({len(py)} stories).")
        return 0
    print("MISMATCH between clingo and python:")
    print("python only:", sorted(py - cl))
    print("clingo only:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A nursery-rhyme storyworld about chirp, flashback, curiosity, and kindness.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--name", choices=NAMES)
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
    goal = args.goal or rng.choice(list(GOALS))
    if place not in PLACES or goal not in GOALS:
        raise StoryError("Unknown place or goal.")
    return StoryParams(place=place, goal=goal, name=args.name or rng.choice(NAMES))


def generate(params: StoryParams) -> StorySample:
    world = tell_story(PLACES[params.place], GOALS[params.goal], params.name)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


CURATED = [
    StoryParams(place="nest", goal="seed", name="Pip"),
    StoryParams(place="garden", goal="bell", name="Lulu"),
    StoryParams(place="orchard", goal="butterfly", name="Mimi"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} valid stories:")
        for item in stories:
            print(" ", item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
