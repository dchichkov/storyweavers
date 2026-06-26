#!/usr/bin/env python3
"""
storyworlds/worlds/whatchamacallit_shock_deport_twist_moral_value_fable.py
===========================================================================

A compact fable-style story world about a curious little problem, a sharp
shock, a mistaken deportation, and a Twist that reveals a Moral Value.

Seed tale sketch:
---
In a quiet meadow, a careful rabbit found a strange whatchamacallit near the
old oak. The meadow folk were shocked, and the fox guessed it must be trouble.
He ordered the whatchamacallit deported beyond the hill. But the hedgehog saw
a tiny name tag under the leaves: the whatchamacallit belonged to the lost
librarian mole. The fox apologized, sent it home instead of away, and learned
that quick anger can make a fool out of a clever face.

World premise:
- A small fable-like place with animal neighbors, a curious object, and an
  authority who tries to solve trouble too fast.
- The tension comes from shock and a hasty deportation order.
- The Twist reveals the object is harmless and belongs to someone innocent.
- The Moral Value is narrated explicitly at the end, as in a traditional fable.

The story is state-driven:
- people can be shocked, worried, proud, relieved
- the object can be carried, hidden, confiscated, or returned
- a false judgment can lead to deportation
- the twist clears the misunderstanding and restores calm
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    name: str
    features: set[str] = field(default_factory=set)
    allows: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    hero: str
    authority: str
    object: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "meadow": Place(
        id="meadow",
        name="the meadow",
        features={"oak", "path", "moss"},
        allows={"find", "gather", "talk"},
    ),
    "market": Place(
        id="market",
        name="the market",
        features={"stall", "cart", "bell"},
        allows={"find", "gather", "talk"},
    ),
    "riverbank": Place(
        id="riverbank",
        name="the riverbank",
        features={"reed", "mud", "bridge"},
        allows={"find", "gather", "talk"},
    ),
}

HEROES = {
    "rabbit": {"type": "rabbit", "label": "rabbit", "name": "Pip"},
    "fox": {"type": "fox", "label": "fox", "name": "Milo"},
    "hedgehog": {"type": "hedgehog", "label": "hedgehog", "name": "Tess"},
    "mole": {"type": "mole", "label": "mole", "name": "Morrow"},
}

AUTHORITY = {
    "mayor": {"type": "mayor", "label": "mayor"},
    "keeper": {"type": "keeper", "label": "keeper"},
    "elder": {"type": "elder", "label": "elder"},
}

WHATCHAMACALLIT = {
    "lantern": {
        "label": "whatchamacallit",
        "phrase": "a brass whatchamacallit with a tiny bell",
        "true_name": "lantern",
        "owner": "mole",
        "clue": "a name tag under the moss",
        "use": "light the library path",
    },
    "seedbox": {
        "label": "whatchamacallit",
        "phrase": "a little whatchamacallit with a lid of bark",
        "true_name": "seedbox",
        "owner": "rabbit",
        "clue": "a ribbon tied in a careful knot",
        "use": "carry flower seeds",
    },
    "musicbox": {
        "label": "whatchamacallit",
        "phrase": "a painted whatchamacallit that hummed softly",
        "true_name": "musicbox",
        "owner": "hedgehog",
        "clue": "a carved initials mark",
        "use": "play a bedtime tune",
    },
}

LOCATIONS = {
    "meadow": "near the old oak",
    "market": "beside the berry stall",
    "riverbank": "under the reed arch",
}

MORALS = [
    "A quick judgment can travel faster than the truth.",
    "A sharp tongue is no lantern in the dark.",
    "Ask first, and the answer may save a friend.",
]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for hero in HEROES:
            for obj_id, obj in WHATCHAMACALLIT.items():
                if hero == obj["owner"]:
                    combos.append((place, hero, obj_id))
                elif hero in {"fox", "mayor", "keeper", "elder"}:
                    combos.append((place, hero, obj_id))
    return combos


def explain_rejection(place: str, hero: str, obj: str) -> str:
    return (
        f"(No story: the chosen role would not create a believable fable here. "
        f"Try a judge-like character such as the fox, mayor, keeper, or elder, "
        f"or choose the whatchamacallit's real owner.)"
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid(P,H,O) :- place(P), hero(H), object(O), owner(O,H).
valid(P,H,O) :- place(P), hero(H), object(O), judge(H).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES.values():
        lines.append(asp.fact("place", p.id))
    for h in HEROES:
        lines.append(asp.fact("hero", h))
        if h in {"fox", "mayor", "keeper", "elder"}:
            lines.append(asp.fact("judge", h))
    for oid, obj in WHATCHAMACALLIT.items():
        lines.append(asp.fact("object", oid))
        lines.append(asp.fact("owner", oid, obj["owner"]))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))

def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place)
    hero_cfg = HEROES[params.hero]
    auth_cfg = AUTHORITY[params.authority]
    obj_cfg = WHATCHAMACALLIT[params.object]

    hero = world.add(Entity(id=params.hero, kind="character", type=hero_cfg["type"], label=hero_cfg["label"]))
    authority = world.add(Entity(id=params.authority, kind="character", type=auth_cfg["type"], label=auth_cfg["label"]))
    obj = world.add(Entity(
        id=params.object,
        kind="thing",
        type=obj_cfg["true_name"],
        label=obj_cfg["label"],
        phrase=obj_cfg["phrase"],
        owner=obj_cfg["owner"],
    ))

    world.facts.update(hero=hero, authority=authority, obj=obj, obj_cfg=obj_cfg, place=place)
    return world


def tell(world: World) -> None:
    hero: Entity = world.facts["hero"]
    authority: Entity = world.facts["authority"]
    obj: Entity = world.facts["obj"]
    obj_cfg = world.facts["obj_cfg"]
    place: Place = world.facts["place"]

    world.say(
        f"In {place.name}, a small {hero.type} named {hero.id.capitalize()} found {obj.phrase} "
        f"{LOCATIONS[place.id]}."
    )
    world.say(
        f"{hero.id.capitalize()} turned it over and wondered what a whatchamacallit could do."
    )

    world.para()
    world.say(
        f"Then the crowd gave a sharp shock, because nobody knew whose whatchamacallit it was."
    )
    world.say(
        f"The {authority.label} feared trouble and ordered the whatchamacallit deported at once."
    )
    obj.memes["fear"] = 1.0
    authority.memes["certainty"] = 1.0
    hero.memes["worry"] = 1.0

    world.para()
    world.say(
        f"But {hero.id.capitalize()} looked again and noticed {obj_cfg['clue']} tucked beneath the leaves."
    )
    world.say(
        f"That was the Twist: the whatchamacallit belonged to the lost {obj_cfg['owner']}."
    )
    hero.memes["relief"] = 1.0
    authority.memes["shame"] = 1.0
    obj.memes["fear"] = 0.0

    world.para()
    world.say(
        f"The {authority.label} called back the order, returned the whatchamacallit home, "
        f"and thanked {hero.id.capitalize()} for caring enough to look twice."
    )
    world.say(
        f"By sunset, the little {hero.type} had learned that truth is kinder than haste."
    )
    world.say(f"Moral Value: {random.choice(MORALS)}")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fable about a {f["hero"].type} who finds a whatchamacallit in {f["place"].name}.',
        f"Tell a child-friendly fable with a shock, a mistaken deportation, a Twist, and a Moral Value.",
        f'Write a simple story where a {f["authority"].type} learns not to judge a "whatchamacallit" too quickly.',
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    authority: Entity = world.facts["authority"]
    obj_cfg = world.facts["obj_cfg"]
    place: Place = world.facts["place"]
    return [
        QAItem(
            question=f"What did {hero.id.capitalize()} find in {place.name}?",
            answer=f"{hero.id.capitalize()} found a whatchamacallit {LOCATIONS[place.id]}. It looked strange at first, but it was just {obj_cfg['phrase']}."
        ),
        QAItem(
            question=f"Why was there a shock in the story?",
            answer="There was a shock because nobody knew who owned the whatchamacallit, so the meadow folk worried it might cause trouble."
        ),
        QAItem(
            question=f"What did the {authority.label} try to do with the whatchamacallit?",
            answer=f"The {authority.label} tried to deport the whatchamacallit before asking enough questions."
        ),
        QAItem(
            question="What was the Twist?",
            answer=f"The Twist was that the whatchamacallit belonged to the lost {obj_cfg['owner']}, so it was not trouble at all."
        ),
        QAItem(
            question="What lesson did the story leave behind?",
            answer="It showed that looking carefully and asking kindly can prevent a mistake."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    place: Place = world.facts["place"]
    obj_cfg = world.facts["obj_cfg"]
    return [
        QAItem(
            question="What is a fable?",
            answer="A fable is a short story that often uses animals and ends with a lesson."
        ),
        QAItem(
            question="What does shock mean?",
            answer="A shock is a sudden surprise that makes people stop and pay attention."
        ),
        QAItem(
            question="What does deport mean?",
            answer="To deport something or someone means to send them away from a place, often by authority."
        ),
        QAItem(
            question="What is a moral value in a story?",
            answer="A moral value is the helpful lesson the story wants you to remember."
        ),
        QAItem(
            question="What is a whatchamacallit?",
            answer=f"A whatchamacallit is an object whose exact name is being left out on purpose; in this story, it was {obj_cfg['phrase']}."
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fable-style story world with a whatchamacallit, shock, deport, Twist, and Moral Value.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--authority", choices=AUTHORITY)
    ap.add_argument("--object", choices=WHATCHAMACALLIT)
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
    combos = [c for c in combos
              if (args.place is None or c[0] == args.place)
              and (args.hero is None or c[1] == args.hero)
              and (args.object is None or c[2] == args.object)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    if args.hero and args.object and args.hero != WHATCHAMACALLIT[args.object]["owner"] and args.hero not in {"fox", "mayor", "keeper", "elder"}:
        raise StoryError(explain_rejection(args.place or "meadow", args.hero, args.object))
    place, hero, obj = rng.choice(sorted(combos))
    authority = args.authority or rng.choice(list(AUTHORITY))
    return StoryParams(place=place, hero=hero, authority=authority, object=obj)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        if e.kind == "thing":
            bits.append(f"owner={e.owner}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
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


CURATED = [
    StoryParams(place="meadow", hero="fox", authority="elder", object="lantern"),
    StoryParams(place="market", hero="mayor", authority="keeper", object="seedbox"),
    StoryParams(place="riverbank", hero="hedgehog", authority="fox", object="musicbox"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:")
        for t in triples:
            print(" ", t)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} / {p.object} / {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
