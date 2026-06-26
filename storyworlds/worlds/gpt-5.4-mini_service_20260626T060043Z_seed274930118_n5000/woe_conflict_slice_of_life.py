#!/usr/bin/env python3
"""
storyworlds/worlds/woe_conflict_slice_of_life.py
================================================

A small slice-of-life story world about a gentle daily woe:
a child wants a shared thing, faces a minor conflict, and finds a calm,
reasonable way forward.

Seed idea:
---
A child has a quiet plan for an afternoon, but someone else is already using
the shared item. The child feels woe, there is a small conflict, and then they
choose turns, teamwork, or a trade that lets everyone settle down again.

This world keeps the action close to home-life details: a table, a nook, a rug,
a bench, a shared object, and a simple compromise.
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
# Entities and world state
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing | place
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    user: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    cozy: str
    affords: set[str] = field(default_factory=set)


@dataclass
class ObjectCfg:
    id: str
    label: str
    phrase: str
    category: str
    can_share: bool
    can_trade: bool
    tag: str


@dataclass
class BeatCfg:
    id: str
    verb: str
    gerund: str
    noun: str
    turn: str
    risk: str
    woe: str
    social: str
    tag: str


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

        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "kitchen": Place("kitchen", "the kitchen table", "warm and bright", {"draw", "puzzle", "bake"}),
    "living": Place("living", "the living room rug", "soft and calm", {"build", "read", "puzzle"}),
    "porch": Place("porch", "the porch bench", "sunny and breezy", {"draw", "snack", "read"}),
    "nook": Place("nook", "the window nook", "small and quiet", {"read", "write", "draw"}),
}

BEATS = {
    "draw": BeatCfg(
        id="draw",
        verb="draw with the shared crayons",
        gerund="drawing with the shared crayons",
        noun="crayons",
        turn="take turns with the crayons",
        risk="the blue crayon would be used up before the picture was finished",
        woe="felt woe in the chest",
        social="the other child wanted the same box",
        tag="crayons",
    ),
    "puzzle": BeatCfg(
        id="puzzle",
        verb="work on the shared puzzle",
        gerund="putting the puzzle together",
        noun="puzzle",
        turn="fit the last pieces one by one",
        risk="the middle pieces would get mixed and hard to find",
        woe="felt woe from the stalled pieces",
        social="someone had kept the corner piece",
        tag="puzzle",
    ),
    "read": BeatCfg(
        id="read",
        verb="read in the quiet spot",
        gerund="reading by the window",
        noun="book",
        turn="share the cozy corner",
        risk="the quiet would be broken by too much noise",
        woe="felt woe because the room was too busy",
        social="a sibling wanted to chat right there",
        tag="book",
    ),
    "build": BeatCfg(
        id="build",
        verb="build a tall block tower",
        gerund="stacking blocks into a tower",
        noun="blocks",
        turn="build two towers side by side",
        risk="the blocks would be taken for a second project",
        woe="felt woe when the tower wobbled",
        social="another child had grabbed half the blocks",
        tag="blocks",
    ),
    "bake": BeatCfg(
        id="bake",
        verb="help mix the cookie dough",
        gerund="stirring the dough",
        noun="mixing bowl",
        turn="share the spoon and the bowl",
        risk="the spoon would be busy in someone else's hand",
        woe="felt woe from waiting at the counter",
        social="the parent was already measuring flour",
        tag="bowl",
    ),
}

OBJECTS = {
    "crayons": ObjectCfg("crayons", "a box of crayons", "the crayon box", "art", True, True, "crayons"),
    "puzzle": ObjectCfg("puzzle", "a wooden puzzle", "the puzzle board", "game", False, True, "puzzle"),
    "book": ObjectCfg("book", "a picture book", "the picture book", "book", True, False, "book"),
    "blocks": ObjectCfg("blocks", "a basket of blocks", "the block basket", "toy", True, True, "blocks"),
    "bowl": ObjectCfg("bowl", "a blue mixing bowl", "the mixing bowl", "kitchen", False, False, "bowl"),
}

NAMES = ["Mina", "Leo", "Noah", "Ivy", "Tara", "Ben", "Maya", "Owen"]
KINDS = [("girl", "mother"), ("boy", "father"), ("girl", "mother"), ("boy", "father")]
TRAITS = ["gentle", "curious", "quiet", "patient", "bright", "small"]


@dataclass
class StoryParams:
    place: str
    beat: str
    obj: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for beat_id in place.affords:
            for obj_id, obj in OBJECTS.items():
                if obj.tag == BEATS[beat_id].tag:
                    combos.append((place_id, beat_id, obj_id))
    return combos


def reason_reject(beat: BeatCfg, obj: ObjectCfg, place: Optional[Place] = None) -> str:
    if place and beat.id not in place.affords:
        return f"(No story: {place.label} does not really fit {beat.gerund}.)"
    return (
        f"(No story: this world only uses a shared object that matches the scene. "
        f"{beat.gerund.capitalize()} needs {beat.noun}, not {obj.label}.)"
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place_all(P) :- place(P).
beat_all(B) :- beat(B).
obj_all(O) :- obj(O).

fits(P,B,O) :- affords(P,B), matches(B,O).
valid_story(P,B,O) :- fits(P,B,O).

shared_scene(B,O) :- beat(B), obj(O), matches(B,O).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for b in sorted(p.affords):
            lines.append(asp.fact("affords", pid, b))
    for bid, b in BEATS.items():
        lines.append(asp.fact("beat", bid))
        lines.append(asp.fact("matches", bid, b.tag))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("obj", oid))
        lines.append(asp.fact("tagged", oid, o.tag))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    ap = set(asp_valid_combos())
    if py == ap:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python gates:")
    print(" only in python:", sorted(py - ap))
    print(" only in clingo:", sorted(ap - py))
    return 1


# ---------------------------------------------------------------------------
# World model actions
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity, parent: Entity, beat: BeatCfg, obj: Entity) -> None:
    world.say(
        f"{hero.id} was a little {next(t for t in hero.memes if False)}"
    )


def build_story(world: World, hero: Entity, parent: Entity, beat: BeatCfg, obj: Entity) -> None:
    hero.memes["love"] += 1
    world.say(
        f"{hero.id} liked quiet afternoons at {world.place.label}. "
        f"{hero.pronoun().capitalize()} wanted to {beat.verb}."
    )
    world.say(
        f"The favorite thing was {obj.phrase}, because it fit the day just right."
    )


def set_scene(world: World, hero: Entity, parent: Entity, beat: BeatCfg, obj: Entity) -> None:
    world.say(
        f"One afternoon, {hero.id} and {hero.pronoun('possessive')} {parent.type} were at {world.place.label}, "
        f"and the room felt {world.place.cozy}."
    )
    world.say(f"{hero.id} noticed {obj.phrase} and hoped it would be available.")


def conflict(world: World, hero: Entity, parent: Entity, beat: BeatCfg, obj: Entity) -> None:
    hero.memes["woe"] += 1
    hero.memes["want"] += 1
    hero.memes["conflict"] += 1
    obj.user = "other"
    world.say(
        f"{hero.id} reached for {obj.phrase}, but {beat.social}. "
        f"That made {hero.id} {beat.woe}."
    )
    world.say(
        f"{hero.id} wanted to {beat.verb}, yet {obj.phrase} was not free."
    )


def turn(world: World, hero: Entity, parent: Entity, beat: BeatCfg, obj: Entity) -> bool:
    if not obj:
        return False
    if beat.id in {"read", "bake"}:
        world.say(
            f"{hero.pronoun('possessive').capitalize()} {parent.type} noticed the problem and suggested {beat.turn}."
        )
    else:
        world.say(
            f"{hero.pronoun('possessive').capitalize()} {parent.type} said they could {beat.turn} instead."
        )
    return True


def resolve(world: World, hero: Entity, parent: Entity, beat: BeatCfg, obj: Entity) -> None:
    hero.memes["woe"] = max(0.0, hero.memes["woe"] - 1)
    hero.memes["conflict"] = 0.0
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    obj.user = hero.id
    world.say(
        f"{hero.id} nodded, and the small knot of {beat.id} eased. "
        f"After that, they {beat.turn}."
    )
    if beat.id == "build":
        world.say(
            f"Two block towers stood together on the rug, one for each child, and nobody had to wait anymore."
        )
    elif beat.id == "draw":
        world.say(
            f"The crayons stayed in one neat box, and the bright picture got finished with a tiny blue sun."
        )
    elif beat.id == "read":
        world.say(
            f"The window nook grew quiet again, and {hero.id} curled up with the book while the noise drifted away."
        )
    elif beat.id == "puzzle":
        world.say(
            f"The last piece clicked in, and the puzzle picture looked calm and complete on the table."
        )
    elif beat.id == "bake":
        world.say(
            f"The spoon made slow circles in the bowl, and the kitchen smelled warm and sweet."
        )


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------
def tell(place: Place, beat: BeatCfg, obj_cfg: ObjectCfg,
         name: str, gender: str, parent_type: str, trait: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=name, kind="character", type=gender, memes={"woe": 0.0, "conflict": 0.0, "joy": 0.0, "want": 0.0}))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type))
    obj = world.add(Entity(id=obj_cfg.id, kind="thing", type=obj_cfg.category, label=obj_cfg.label, phrase=obj_cfg.phrase, owner=hero.id))

    world.say(
        f"{hero.id} was a little {trait} {hero.type} who loved calm afternoons."
    )
    world.say(
        f"At {world.place.label}, {hero.id} hoped to use {obj.phrase} for a small plan."
    )
    world.para()
    set_scene(world, hero, parent, beat, obj)
    conflict(world, hero, parent, beat, obj)
    world.para()
    turn(world, hero, parent, beat, obj)
    resolve(world, hero, parent, beat, obj)
    world.facts.update(hero=hero, parent=parent, obj=obj, beat=beat, place=place)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    beat = f["beat"]
    obj = f["obj"]
    return [
        f'Write a slice-of-life story about {hero.id} who wants to {beat.verb} but cannot at first because {obj.phrase} is already in use.',
        f'Tell a gentle story where a child feels woe, has a small conflict, and then finds a calm way to {beat.turn}.',
        f'Write a short home-life story that includes the word "woe" and ends with a peaceful ordinary moment.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    beat = f["beat"]
    obj = f["obj"]
    place = f["place"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do at {place.label}?",
            answer=f"{hero.id} wanted to {beat.verb} with {obj.phrase}.",
        ),
        QAItem(
            question=f"Why did {hero.id} feel woe?",
            answer=f"{hero.id} felt woe because {beat.social} and the plan had to wait for a moment.",
        ),
        QAItem(
            question=f"How did {hero.id} and the parent solve the conflict?",
            answer=f"They solved it by {beat.turn}, which let everyone settle down again.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, the conflict was gone and {hero.id} could enjoy the day more peacefully at {place.label}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    beat = f["beat"]
    items = [
        QAItem(
            question="What does woe mean?",
            answer="Woe means a feeling of sadness, trouble, or being upset about something.",
        ),
        QAItem(
            question="What is a compromise?",
            answer="A compromise is a choice where people each give a little so they can agree and move on together.",
        ),
    ]
    if beat.id == "read":
        items.append(QAItem(
            question="Why is a window nook a nice place to read?",
            answer="A window nook is nice for reading because it is often small, cozy, and quieter than the rest of the room.",
        ))
    if beat.id == "build":
        items.append(QAItem(
            question="Why do block towers fall over sometimes?",
            answer="Block towers can fall over if they are too tall, bumped by a hand, or built on a wobbly base.",
        ))
    return items


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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in world.entities.values():
        m = {k: v for k, v in e.meters.items() if v}
        em = {k: v for k, v in e.memes.items() if v}
        bits = []
        if m:
            bits.append(f"meters={m}")
        if em:
            bits.append(f"memes={em}")
        if e.phrase:
            bits.append(f"phrase={e.phrase!r}")
        if e.user:
            bits.append(f"user={e.user}")
        out.append(f"  {e.id:8} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life story world about a small woe and a gentle conflict.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--beat", choices=BEATS)
    ap.add_argument("--obj", choices=OBJECTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.place and args.beat and args.obj:
        if (args.place, args.beat, args.obj) not in valid_combos():
            raise StoryError(reason_reject(BEATS[args.beat], OBJECTS[args.obj], PLACES[args.place]))
    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.beat is None or c[1] == args.beat)
        and (args.obj is None or c[2] == args.obj)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, beat, obj = rng.choice(sorted(combos))
    if args.gender:
        gender = args.gender
    else:
        gender = rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    parent = args.parent or (KINS[0][1] if gender == "girl" else KINS[1][1])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, beat=beat, obj=obj, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], BEATS[params.beat], OBJECTS[params.obj],
                 params.name, params.gender, params.parent, params.trait)
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
    StoryParams("living", "build", "blocks", "Mina", "girl", "mother", "patient"),
    StoryParams("nook", "read", "book", "Leo", "boy", "father", "quiet"),
    StoryParams("kitchen", "draw", "crayons", "Ivy", "girl", "mother", "gentle"),
    StoryParams("porch", "puzzle", "puzzle", "Ben", "boy", "father", "curious"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        triples = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(triples)} compatible combos:\n")
        for t in triples:
            print("  ", t)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.beat} at {p.place} ({p.obj})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
