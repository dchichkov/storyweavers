#!/usr/bin/env python3
"""
A standalone story world for a small adventure in a mansion, where kindness and
bravery matter and something poisonous creates the tension.

Premise:
- A child enters an old mansion with a careful guide.
- The child finds a frightened animal and a dangerous poisonous bottle.
- Kindness helps the child protect the animal and bravery helps them choose the
  safe path.

The model tracks:
- physical meters: danger, closeness, rescue, poison risk, safety
- emotional memes: kindness, bravery, fear, relief, trust

The story is generated from state updates, not from a frozen paragraph.
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
    kind: str = "thing"  # character | thing | creature
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["danger", "safety", "poison", "rescue", "closeness"]:
            self.meters.setdefault(k, 0.0)
        for k in ["kindness", "bravery", "fear", "relief", "trust"]:
            self.memes.setdefault(k, 0.0)

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

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    name: str
    title: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Dilemma:
    id: str
    danger: str
    turn: str
    ending: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    guard: set[str]
    helps: set[str]
    prep: str
    tail: str


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.path: list[str] = []

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
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.path = list(self.path)
        return c


def _r_poison(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.meters["danger"] < THRESHOLD:
            continue
        sig = ("poison", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.meters["poison"] += 1
        actor.memes["fear"] += 1
        out.append(f"The poisonous smell made {actor.id} hold {actor.pronoun('possessive')} breath.")
    return out


def _r_kindness(world: World) -> list[str]:
    out = []
    child = world.get("child")
    if child.memes["kindness"] < THRESHOLD:
        return out
    sig = ("kindness",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.meters["rescue"] += 1
    child.memes["trust"] += 1
    out.append("Kindness gave the child a steady heart.")
    return out


def _r_bravery(world: World) -> list[str]:
    out = []
    child = world.get("child")
    if child.memes["bravery"] < THRESHOLD:
        return out
    sig = ("bravery",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.meters["safety"] += 1
    child.memes["relief"] += 1
    out.append("Bravery helped the child choose the safe door.")
    return out


CAUSAL_RULES = [_r_poison, _r_kindness, _r_bravery]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            s = rule(world)
            if s:
                changed = True
                produced.extend(s)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def build_story_world(hero_name: str, companion_name: str) -> World:
    place = PLACE
    world = World(place)
    child = world.add(Entity(id="child", kind="character", type="girl", label=hero_name))
    guide = world.add(Entity(id="guide", kind="character", type="woman", label=companion_name))
    cat = world.add(Entity(id="cat", kind="creature", type="cat", label="a small cat"))
    vial = world.add(Entity(id="vial", kind="thing", type="bottle", label="a poisonous vial"))
    map_piece = world.add(Entity(id="map", kind="thing", type="map", label="a torn map"))

    world.facts.update(child=child, guide=guide, cat=cat, vial=vial, map_piece=map_piece)

    child.memes["kindness"] += 1
    child.memes["bravery"] += 1

    world.say(f"{hero_name} stepped into the {place.title} with {companion_name}, and the old halls waited in silence.")
    world.say(f"Inside the mansion, a torn map pointed toward a bright window and a locked door.")
    world.para()

    world.say(f"Then {hero_name} heard a tiny meow behind a velvet curtain.")
    cat.meters["closeness"] += 1
    world.say(f"A small cat was trembling near {map_piece.label}, and beside it sat {vial.label}.")
    world.say("The bottle looked dangerous, and everyone knew poisonous things had to be left alone.")
    world.para()

    world.say(f"{hero_name} wanted to help, but the hallway felt dark and strange.")
    child.memes["fear"] += 1
    child.meters["danger"] += 1
    propagate(world, narrate=True)
    world.say(f"{companion_name} whispered that bravery did not mean rushing; it meant doing the right thing even when the room felt scary.")
    world.say(f"So {hero_name} took a careful step, wrapped the cat in a soft scarf, and moved the poisonous vial away from the floor.")
    child.meters["rescue"] += 1
    cat.meters["safety"] += 1
    child.memes["kindness"] += 1
    child.memes["bravery"] += 1
    propagate(world, narrate=True)
    world.para()

    world.say(f"At last, the cat stopped shaking and rubbed against {hero_name}'s sleeve.")
    world.say(f"The mansion no longer felt like a trap. It felt like an adventure with a safe ending and a grateful friend.")
    world.say(f"{hero_name} smiled, because kindness had rescued the cat and bravery had carried {hero_name} through the poisonous worry.")
    world.facts["resolved"] = True
    return world


PLACE = Place(
    name="mansion",
    title="mansion",
    affords={"explore", "rescue", "avoid"},
)

DILEMMAS = {
    "poisonous": Dilemma(
        id="poisonous",
        danger="poisonous",
        turn="careful rescue",
        ending="safe and grateful",
        keyword="poisonous",
        tags={"poison", "danger"},
    )
}

TOOLS = [
    Tool(
        id="scarf",
        label="soft scarf",
        guard={"poison"},
        helps={"rescue"},
        prep="wrap the cat in a soft scarf",
        tail="moved the poisonous vial away",
    ),
    Tool(
        id="lantern",
        label="small lantern",
        guard={"dark"},
        helps={"explore"},
        prep="carry a small lantern",
        tail="lit the way through the hallway",
    ),
]


@dataclass
class StoryParams:
    place: str
    dilemma: str
    hero_name: str
    guide_name: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(place="mansion", dilemma="poisonous", hero_name="Mina", guide_name="Aunt Rose", seed=1),
    StoryParams(place="mansion", dilemma="poisonous", hero_name="Talia", guide_name="Mrs. June", seed=2),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mansion adventure with poisonous danger, kindness, and bravery.")
    ap.add_argument("--place", choices=[PLACE.name], default=None)
    ap.add_argument("--dilemma", choices=list(DILEMMAS), default=None)
    ap.add_argument("--name")
    ap.add_argument("--guide")
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
    place = args.place or PLACE.name
    dilemma = args.dilemma or "poisonous"
    if place != PLACE.name:
        raise StoryError("This world only takes place in the mansion.")
    if dilemma not in DILEMMAS:
        raise StoryError("Unknown dilemma.")
    return StoryParams(
        place=place,
        dilemma=dilemma,
        hero_name=args.name or rng.choice(["Mina", "Talia", "Lina", "Rose", "Ivy"]),
        guide_name=args.guide or rng.choice(["Aunt Rose", "Mrs. June", "Nora", "Mira"]),
        seed=args.seed,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a short adventure story in a mansion where kindness and bravery help a child handle something poisonous.",
        f"Tell a child-friendly story about {f['child'].label} and {f['guide'].label} exploring the mansion and finding a poisonous danger.",
        "Write a gentle adventure ending with a safe rescue and a feeling of bravery.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    guide = world.facts["guide"]
    return [
        QAItem(
            question=f"Where did {child.label} go with {guide.label}?",
            answer=f"{child.label} went with {guide.label} into the mansion.",
        ),
        QAItem(
            question="What dangerous thing did they find?",
            answer="They found a poisonous vial.",
        ),
        QAItem(
            question=f"What helped {child.label} rescue the cat?",
            answer="Kindness helped the child care about the cat, and bravery helped the child act carefully.",
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended safely, with the cat rescued and the poisonous danger moved away.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does poisonous mean?",
            answer="Poisonous means something can make people or animals sick, so it must be handled with care.",
        ),
        QAItem(
            question="What is a mansion?",
            answer="A mansion is a very large house with many rooms.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means being gentle, helpful, and caring toward others.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery means doing the right thing even when you feel scared.",
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:8}) meters={meters} memes={memes}")
    lines.append(f"  path: {world.path}")
    lines.append(f"  fired: {sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
poison_risk(C) :- danger(C), poisonous(V).
brave(C) :- bravery(C).
kind(C) :- kindness(C).
safe_rescue(C) :- kind(C), brave(C), not poison_risk(C).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("place", PLACE.name),
        asp.fact("affords", PLACE.name, "explore"),
        asp.fact("affords", PLACE.name, "rescue"),
        asp.fact("affords", PLACE.name, "avoid"),
        asp.fact("dilemma", "poisonous"),
        asp.fact("danger_word", "poisonous"),
        asp.fact("feature", "kindness"),
        asp.fact("feature", "bravery"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show place/1."))
    ok = any(a.name == "place" and a.arguments[0].string == PLACE.name for a in model)
    if ok:
        print("OK: ASP twin is wired.")
        return 0
    print("MISMATCH: ASP twin did not return the expected place.")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = build_story_world(params.hero_name, params.guide_name)
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
        print(asp_program("#show place/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params_list = CURATED
    else:
        params_list = []
        for i in range(args.n):
            params_list.append(resolve_params(args, random.Random(base_seed + i)))

    for i, p in enumerate(params_list):
        p.seed = p.seed if p.seed is not None else base_seed + i
        samples.append(generate(p))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, s in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(s, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
