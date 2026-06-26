#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/absorb_guinea_flashback_fable.py
============================================================================================================

A small fable-style storyworld about a guinea and a lesson about helping.

Premise:
- A little guinea cares about a thirsty patch of ground and wants to absorb
  spilled water before it reaches a bird's nest.

Flashback:
- The story looks back to a time when the guinea once let a spill spread and
  felt sorry afterward, which motivates the careful action now.

Turn:
- The guinea tries to do the right thing, but the absorbent cloth is too small.

Resolution:
- A helper brings a wider mat, and the guinea absorbs the spill before it
  causes trouble.

Style note:
- This is written as a fable: concrete animal characters, a simple moral turn,
  and an ending that proves the lesson changed the world.
"""

from __future__ import annotations

import argparse
import copy
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"spill": 0.0, "dryness": 0.0, "risk": 0.0}
        if not self.memes:
            self.memes = {"care": 0.0, "regret": 0.0, "hope": 0.0, "pride": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"guinea", "bird", "mouse", "hare", "fox"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    features: set[str] = field(default_factory=set)
    afford: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    absorbency: float
    capacity: float
    covers: set[str] = field(default_factory=set)
    plural: bool = False


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.items: dict[str, Item] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.timeline: list[str] = []

    def add_entity(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_item(self, item: Item) -> Item:
        self.items[item.id] = item
        return item

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.timeline.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.items = copy.deepcopy(self.items)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    hero: str
    helper: str
    seed: Optional[int] = None


PLACES = {
    "orchard": Place(name="the orchard", features={"tree", "path", "nest"}, afford={"spill"}),
    "barnyard": Place(name="the barnyard", features={"bucket", "path", "nest"}, afford={"spill"}),
    "meadow": Place(name="the meadow", features={"grass", "stone", "nest"}, afford={"spill"}),
}

HEROES = {
    "guinea": ("guinea", "a small guinea"),
}

HELPERS = {
    "rabbit": ("rabbit", "a quick rabbit"),
    "mole": ("mole", "a careful mole"),
    "sparrow": ("sparrow", "a bright sparrow"),
}

TOOLS = {
    "cloth": Item(id="cloth", label="little cloth", absorbency=1.0, capacity=1.0),
    "mat": Item(id="mat", label="wide mat", absorbency=3.0, capacity=3.0),
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable-style storyworld about a guinea and a helpful absorbent rescue.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--helper", choices=HELPERS)
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
    hero = args.hero or "guinea"
    helper = args.helper or rng.choice(list(HELPERS))
    if hero != "guinea":
        raise StoryError("This world only tells the fable of the guinea.")
    return StoryParams(place=place, hero=hero, helper=helper)


def _spill_risk(world: World) -> float:
    return world.get("guinea").meters["spill"]


def _absorb(world: World, actor: Entity, item: Entity, tool: Item, amount: float) -> str:
    taken = min(amount, tool.absorbency)
    actor.meters["spill"] = max(0.0, actor.meters["spill"] - taken)
    item.meters["dryness"] += taken
    if actor.meters["spill"] < THRESHOLD:
        actor.memes["hope"] += 1
    return f"{actor.id} used the {item.label} to absorb the spill."


def tell(place: Place, hero_id: str, helper_id: str) -> World:
    world = World(place)
    hero = world.add_entity(Entity(id=hero_id, kind="character", type="guinea", label="guinea", traits=["small", "kind"]))
    helper = world.add_entity(Entity(id=helper_id, kind="character", type=helper_id, label=helper_id))
    cloth = world.add_entity(Entity(id="cloth", kind="thing", type="cloth", label="little cloth", owner=hero.id))
    mat = world.add_entity(Entity(id="mat", kind="thing", type="mat", label="wide mat", owner=helper.id))

    world.add_item(copy.deepcopy(TOOLS["cloth"]))
    world.add_item(copy.deepcopy(TOOLS["mat"]))

    # Setup
    world.say("Once, in the orchard, a small guinea watched a spilled cup soak toward a bird's nest.")
    world.say("The guinea was gentle and believed every little bit of water should be put to use.")
    world.say("A flashback came to mind: once before, the guinea had let a spill spread, and the bees had slipped.")
    hero.memes["regret"] += 1
    hero.memes["care"] += 1
    world.facts["flashback"] = True

    world.para()

    # Tension
    world.say("This time, the guinea hurried to stop the water before it touched the nest.")
    hero.meters["spill"] = 2.0
    world.say("But the little cloth was too small, and the wet edge kept widening along the path.")
    hero.meters["risk"] = 1.0

    # Resolution attempt with helper
    world.para()
    helper.memes["hope"] += 1
    world.say(f"{helper.label.capitalize()} saw the trouble and brought the wide mat.")
    world.say("Together they pressed it to the ground, and the mat drank up the water at once.")
    _absorb(world, hero, cloth, world.items["cloth"], 0.5)
    _absorb(world, helper, mat, world.items["mat"], 1.5)
    hero.meters["spill"] = 0.0
    hero.memes["pride"] += 1
    hero.memes["regret"] = 0.0

    world.say("The path stayed dry, the bird kept its nest, and the guinea felt proud to have learned the wiser way.")
    world.say("And the lesson was clear: it is better to absorb trouble early than to let it spread.")

    world.facts.update(
        hero=hero,
        helper=helper,
        cloth=cloth,
        mat=mat,
        place=place,
        resolved=True,
        flashback=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    return [
        "Write a short fable about a guinea who learns to absorb a spill before it spreads.",
        f"Tell a child-friendly story in which {hero.label} remembers a past mistake in a flashback and then does better.",
        f"Write a simple moral tale where {helper.label} helps {hero.label} find a larger way to absorb water.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    return [
        QAItem(
            question="What did the guinea remember in the flashback?",
            answer="The guinea remembered a past time when a spill was let alone, and it spread farther than it should have.",
        ),
        QAItem(
            question="Why did the guinea hurry to the wet path?",
            answer="The guinea hurried because it wanted to stop the water before it reached the bird's nest.",
        ),
        QAItem(
            question=f"Who brought help when {hero.label} could not fix the spill with the little cloth?",
            answer=f"{helper.label.capitalize()} brought a wide mat that could absorb much more water.",
        ),
        QAItem(
            question="How did the story end?",
            answer="The water was absorbed, the path stayed dry, and the guinea felt wiser and proud.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does absorb mean?",
            answer="To absorb means to soak up a liquid so it does not spread.",
        ),
        QAItem(
            question="What is a guinea pig?",
            answer="A guinea pig is a small rodent that people keep as a gentle pet.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a part of a story that goes back to an earlier time to show something that happened before.",
        ),
    ]


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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    lines.append(f"place={world.place.name}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(guinea).
helper(rabbit).
helper(mole).
helper(sparrow).

absorbent(cloth).
absorbent(mat).

better_than(mat, cloth).

can_absorb(guinea, cloth) :- absorbent(cloth).
can_absorb(guinea, mat) :- absorbent(mat).

good_outcome(guinea) :- can_absorb(guinea, mat).
valid_story(guinea) :- good_outcome(guinea).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("hero", "guinea")]
    for name in HELPERS:
        lines.append(asp.fact("helper", name))
    for item in TOOLS.values():
        lines.append(asp.fact("absorbent", item.id))
    lines.append(asp.fact("better_than", "mat", "cloth"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    asp_ok = set(asp.atoms(model, "valid_story"))
    py_ok = {("guinea",)}
    if asp_ok == py_ok:
        print("OK: ASP and Python agree on the guinea story gate.")
        return 0
    print("MISMATCH:")
    print("ASP:", sorted(asp_ok))
    print("PY:", sorted(py_ok))
    return 1


def build_story(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], params.hero, params.helper)
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


CURATED = [
    StoryParams(place="orchard", hero="guinea", helper="rabbit"),
    StoryParams(place="barnyard", hero="guinea", helper="mole"),
    StoryParams(place="meadow", hero="guinea", helper="sparrow"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/1."))
        vals = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(vals)} valid story(s):")
        for v in vals:
            print(v)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [build_story(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
                return
            params.seed = base_seed + i
            sample = build_story(params)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.place} / {p.hero} / {p.helper}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
