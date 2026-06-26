#!/usr/bin/env python3
"""
A fable-style storyworld about a small harbor, a plastic prize, a brave helper,
and a misunderstanding that turns into a surprise.

Seed words: plastic, fantastic, scallywag
Features: Bravery, Surprise, Misunderstanding
Style: Fable
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

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
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        male = {"boy", "man", "father", "king", "fox", "crow"}
        female = {"girl", "woman", "mother", "queen"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    water: bool = False
    market: bool = False
    quiet: bool = False


@dataclass
class ObjectItem:
    id: str
    label: str
    phrase: str
    type: str
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    fragile: bool = False
    shiny: bool = False
    allowed: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    place: str
    treasure: str
    hero_name: str
    hero_type: str
    trickster_name: str
    trickster_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.objects: dict[str, ObjectItem] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add_entity(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def add_object(self, o: ObjectItem) -> ObjectItem:
        self.objects[o.id] = o
        return o

    def get_entity(self, eid: str) -> Entity:
        return self.entities[eid]

    def get_object(self, oid: str) -> ObjectItem:
        return self.objects[oid]

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
        w = World(copy.deepcopy(self.place))
        w.entities = copy.deepcopy(self.entities)
        w.objects = copy.deepcopy(self.objects)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------

PLACES = {
    "harbor": Place(name="the harbor", water=True, market=True),
    "village": Place(name="the village square", market=True, quiet=True),
    "orchard": Place(name="the orchard", quiet=True),
}

HERO_TYPES = ["mouse", "girl", "boy", "hedgehog", "rabbit"]
TRICKSTER_TYPES = ["fox", "crow", "goose", "cat"]

TREASURES = {
    "boat": ObjectItem(
        id="boat",
        label="plastic boat",
        phrase="a little plastic boat",
        type="boat",
        fragile=False,
        shiny=True,
        allowed={"harbor"},
    ),
    "cup": ObjectItem(
        id="cup",
        label="plastic cup",
        phrase="a bright plastic cup",
        type="cup",
        fragile=False,
        shiny=True,
        allowed={"harbor", "village", "orchard"},
    ),
    "crown": ObjectItem(
        id="crown",
        label="plastic crown",
        phrase="a fantastic plastic crown",
        type="crown",
        fragile=False,
        shiny=True,
        allowed={"village"},
    ),
}

# ---------------------------------------------------------------------------
# Narration helpers
# ---------------------------------------------------------------------------

def place_opening(place: Place) -> str:
    if place.water:
        return f"The harbor was full of salt air, and little waves tapped the wooden posts."
    if place.market:
        return f"The square was busy, and the baskets and stalls made a cheerful ring."
    return f"The orchard was green and still, and the leaves whispered softly in the trees."


def hero_intro(hero: Entity) -> str:
    return f"There once was a small {hero.type} named {hero.id}, and {hero.pronoun('subject')} was known for a kind heart."


def trickster_intro(trickster: Entity) -> str:
    return f"Near {trickster.id} lived a sly {trickster.type}, a scallywag who liked to tease and dash away."


def treasure_sentence(hero: Entity, treasure: ObjectItem) -> str:
    return f"{hero.id} loved the {treasure.label} because it looked {('fantastic' if treasure.shiny else 'plain')} in the sun."


def desire_sentence(hero: Entity, treasure: ObjectItem) -> str:
    return f"{hero.id} carried the {treasure.label} everywhere, as if no day was complete without {hero.pronoun('possessive')} little prize."


def warn_sentence(hero: Entity, trickster: Entity, treasure: ObjectItem) -> str:
    return (
        f"The scallywag {trickster.id} watched the {treasure.label} and grinned. "
        f"'{hero.id}, that shiny thing is too easy to lose,' {trickster.pronoun('subject')} said."
    )


def bravery_sentence(hero: Entity) -> str:
    hero.memes["bravery"] = hero.memes.get("bravery", 0.0) + 1.0
    return f"But {hero.id} was brave and would not hide behind fear."


def misunderstanding_sentence(hero: Entity, trickster: Entity) -> str:
    hero.memes["misunderstanding"] = hero.memes.get("misunderstanding", 0.0) + 1.0
    trickster.memes["misunderstanding"] = trickster.memes.get("misunderstanding", 0.0) + 1.0
    return (
        f"Still, {hero.id} misunderstood the warning and thought {trickster.id} meant to mock {hero.pronoun('object')}."
    )


def surprise_sentence(hero: Entity, trickster: Entity, treasure: ObjectItem) -> str:
    hero.memes["surprise"] = hero.memes.get("surprise", 0.0) + 1.0
    trickster.memes["surprise"] = trickster.memes.get("surprise", 0.0) + 1.0
    return (
        f"Then came a surprise: {trickster.id} had only been warning {hero.id}, because a tide splash had already nudged the {treasure.label} toward the dock."
    )


def resolution_sentence(hero: Entity, trickster: Entity, treasure: ObjectItem) -> str:
    hero.memes["peace"] = hero.memes.get("peace", 0.0) + 1.0
    trickster.memes["peace"] = trickster.memes.get("peace", 0.0) + 1.0
    return (
        f"{hero.id} and {trickster.id} reached together, and brave hands saved the {treasure.label} before it drifted away."
    )


def ending_sentence(hero: Entity, trickster: Entity, treasure: ObjectItem) -> str:
    return (
        f"In the end, the harbor was calm again, and the {treasure.label} stayed safe with {hero.id}, while even the scallywag {trickster.id} smiled."
    )


# ---------------------------------------------------------------------------
# Mechanics
# ---------------------------------------------------------------------------

def predict_loss(world: World, hero: Entity, trickster: Entity, treasure: ObjectItem) -> bool:
    sim = world.copy()
    sim.facts["tide"] = True
    sim.facts["treasure_moved"] = True
    return treasure.label.startswith("plastic") and sim.place.water and trickster.type in {"fox", "crow", "goose", "cat"}


def do_tide(world: World, treasure: ObjectItem) -> None:
    treasure.meters["moved"] = treasure.meters.get("moved", 0.0) + 1.0


def tell_story(world: World, hero: Entity, trickster: Entity, treasure: ObjectItem) -> None:
    world.say(place_opening(world.place))
    world.say(hero_intro(hero))
    world.say(trickster_intro(trickster))
    world.say(treasure_sentence(hero, treasure))
    world.para()
    world.say(desire_sentence(hero, treasure))
    world.say(warn_sentence(hero, trickster, treasure))
    world.say(bravery_sentence(hero))
    world.say(misunderstanding_sentence(hero, trickster))
    world.para()
    do_tide(world, treasure)
    if predict_loss(world, hero, trickster, treasure):
        world.say(surprise_sentence(hero, trickster, treasure))
        world.say(resolution_sentence(hero, trickster, treasure))
    world.para()
    world.say(ending_sentence(hero, trickster, treasure))


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fable about a brave {f["hero"].type} named {f["hero"].id}, a scallywag {f["trickster"].type}, and a {f["treasure"].label}.',
        f"Tell a child-friendly story that includes the words plastic, fantastic, and scallywag, and shows bravery after a misunderstanding.",
        f"Write a fable set at {world.place.name} where a surprise helps two animals save a shiny prize.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    trickster: Entity = f["trickster"]
    treasure: ObjectItem = f["treasure"]
    return [
        QAItem(
            question=f"Who was brave in the story?",
            answer=f"{hero.id} was brave and chose to face the trouble instead of running away.",
        ),
        QAItem(
            question=f"Why did {hero.id} think {trickster.id} was teasing {hero.pronoun('object')}?",
            answer=f"{hero.id} misunderstood the warning and thought the scallywag {trickster.id} meant to laugh at {hero.pronoun('object')}.",
        ),
        QAItem(
            question=f"What surprise changed the story at {world.place.name}?",
            answer=f"The surprise was that the tide had already nudged the {treasure.label} toward the dock, so the warning was really help.",
        ),
        QAItem(
            question=f"What happened to the {treasure.label} at the end?",
            answer=f"{hero.id} and {trickster.id} saved the {treasure.label}, and it stayed safe at the harbor.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does plastic mean?",
            answer="Plastic is a light material made by people. It can be molded into many shapes, like cups, toys, and boats.",
        ),
        QAItem(
            question="What is a fable?",
            answer="A fable is a short story that often uses animals or simple characters to teach a lesson.",
        ),
        QAItem(
            question="What does scallywag mean?",
            answer="A scallywag is a playful word for a mischievous person or animal who causes trouble.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    lines.append(f"place: {world.place.name}")
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} memes={dict(e.memes)} meters={dict(e.meters)}")
    for o in world.objects.values():
        lines.append(f"{o.id}: label={o.label} meters={dict(o.meters)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
#show valid_story/4.

place(harbor). place(village). place(orchard).
water(harbor). market(harbor). market(village). quiet(village). quiet(orchard).

hero_type(mouse). hero_type(girl). hero_type(boy). hero_type(hedgehog). hero_type(rabbit).
trickster_type(fox). trickster_type(crow). trickster_type(goose). trickster_type(cat).

treasure(boat). treasure(cup). treasure(crown).
label(boat,"plastic boat"). label(cup,"plastic cup"). label(crown,"plastic crown").
allowed(boat,harbor). allowed(cup,harbor). allowed(cup,village). allowed(cup,orchard). allowed(crown,village).

brave(hero).
scallywag(trickster).

valid_story(P,T,H,R) :- allowed(T,P), place(P), treasure(T), hero_type(H), trickster_type(R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.water:
            lines.append(asp.fact("water", pid))
        if place.market:
            lines.append(asp.fact("market", pid))
        if place.quiet:
            lines.append(asp.fact("quiet", pid))
    for tid in HERO_TYPES:
        lines.append(asp.fact("hero_type", tid))
    for tid in TRICKSTER_TYPES:
        lines.append(asp.fact("trickster_type", tid))
    for tid, t in TREASURES.items():
        lines.append(asp.fact("treasure", tid))
        lines.append(asp.fact("label", tid, t.label))
        for p in sorted(t.allowed):
            lines.append(asp.fact("allowed", tid, p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} stories).")
        return 0
    print("MISMATCH between ASP and Python.")
    print("only in python:", sorted(py - cl))
    print("only in asp:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Validation and generation
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for place in PLACES:
        for treasure in TREASURES:
            if place in TREASURES[treasure].allowed:
                for hero in HERO_TYPES:
                    for trickster in TRICKSTER_TYPES:
                        out.append((place, treasure, hero, trickster))
    return out


CURATED = [
    StoryParams(place="harbor", treasure="boat", hero_name="Milo", hero_type="mouse", trickster_name="Crisp", trickster_type="fox"),
    StoryParams(place="village", treasure="crown", hero_name="Nina", hero_type="girl", trickster_name="Wren", trickster_type="crow"),
    StoryParams(place="orchard", treasure="cup", hero_name="Pip", hero_type="hedgehog", trickster_name="Taffy", trickster_type="cat"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fable storyworld with bravery, surprise, and misunderstanding.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--trickster-name")
    ap.add_argument("--trickster-type", choices=TRICKSTER_TYPES)
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
    if args.treasure:
        combos = [c for c in combos if c[1] == args.treasure]
    if args.hero_type:
        combos = [c for c in combos if c[2] == args.hero_type]
    if args.trickster_type:
        combos = [c for c in combos if c[3] == args.trickster_type]
    if not combos:
        raise StoryError("No valid story matches those options.")
    place, treasure, hero_type, trickster_type = rng.choice(sorted(combos))
    hero_name = args.hero_name or rng.choice(["Milo", "Nina", "Pip", "Luna", "Bram", "Tess"])
    trickster_name = args.trickster_name or rng.choice(["Crisp", "Wren", "Taffy", "Rook", "Murk"])
    return StoryParams(place=place, treasure=treasure, hero_name=hero_name, hero_type=hero_type, trickster_name=trickster_name, trickster_type=trickster_type)


def generate(params: StoryParams) -> StorySample:
    place = PLACES[params.place]
    world = World(place)
    hero = world.add_entity(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    trickster = world.add_entity(Entity(id=params.trickster_name, kind="character", type=params.trickster_type))
    treasure = world.add_object(copy.deepcopy(TREASURES[params.treasure]))
    treasure.owner = hero.id
    treasure.caretaker = hero.id
    world.facts = {"hero": hero, "trickster": trickster, "treasure": treasure}

    tell_story(world, hero, trickster, treasure)

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
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/4."))
        stories = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(stories)} compatible stories:")
        for t in stories:
            print("  ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
