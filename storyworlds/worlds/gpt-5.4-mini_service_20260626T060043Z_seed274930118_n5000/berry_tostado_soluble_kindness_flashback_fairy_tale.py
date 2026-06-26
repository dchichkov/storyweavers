#!/usr/bin/env python3
"""
A small fairy-tale storyworld about a berry, something tostado, and a soluble
mix-up that is resolved by kindness and a brief flashback.
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
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "princess", "queen", "witch"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "prince", "king", "knight"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class StoryParams:
    name: str
    role: str
    place: str
    object: str
    seed: Optional[int] = None


@dataclass
class Setting:
    place: str
    indoors: bool = False


@dataclass
class ObjectSpec:
    label: str
    phrase: str
    region: str
    soluble: bool = False
    toasted: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
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
        other = World(self.setting)
        other.entities = copy.deepcopy(self.entities)
        other.paragraphs = [[]]
        other.facts = dict(self.facts)
        other.fired = set(self.fired)
        return other


SETTINGS = {
    "berrygrove": Setting("the berry grove", indoors=False),
    "castlekitchen": Setting("the castle kitchen", indoors=True),
    "springwell": Setting("the spring well", indoors=False),
}

OBJECTS = {
    "berry": ObjectSpec("berry", "a bright red berry", "bowl", soluble=True),
    "tostado": ObjectSpec("tostado", "a warm tostado cake", "tray", toasted=True),
    "soluble": ObjectSpec("soluble", "a tiny soluble sugar charm", "pouch", soluble=True),
}

ROLES = {
    "girl": "girl",
    "boy": "boy",
    "princess": "princess",
    "prince": "prince",
    "witch": "witch",
    "knight": "knight",
}

NAMES = ["Ayla", "Mina", "Lio", "Nero", "Faye", "Tarin", "Elin", "Rosa"]
TRAITS = ["gentle", "brave", "curious", "kind", "lively"]

ASP_RULES = r"""
#show valid/3.
at_risk(O, P) :- object(O), worn_on(P, R), splashes(O, R).
helpful(O, P) :- at_risk(O, P), soluble(O).
valid(S, O, P) :- setting(S), object(O), prize(P), at_risk(O, P), helpful(O, P).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for oid, spec in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        if spec.soluble:
            lines.append(asp.fact("soluble", oid))
        if spec.toasted:
            lines.append(asp.fact("tostado", oid))
        lines.append(asp.fact("worn_on", oid, spec.region))
        lines.append(asp.fact("splashes", oid, spec.region))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for o in OBJECTS:
            combos.append((s, o, "kindness"))
    return combos

def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(""))
    return sorted(set(asp.atoms(model, "valid")))

def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("Mismatch.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy tale storyworld with berry, tostado, soluble, kindness, and flashback.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--name")
    ap.add_argument("--role", choices=ROLES)
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
    place = args.place or rng.choice(list(SETTINGS))
    obj = args.object or rng.choice(list(OBJECTS))
    role = args.role or rng.choice(list(ROLES))
    name = args.name or rng.choice(NAMES)
    if place == "springwell" and obj == "tostado":
        raise StoryError("The toasted cake would not stay pleasant at the spring well.")
    return StoryParams(name=name, role=role, place=place, object=obj)


def story_text(world: World) -> str:
    return world.render()

def make_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=params.role, label=params.name))
    helper = world.add(Entity(id="helper", kind="character", type="queen", label="the queen"))
    obj = world.add(Entity(
        id="obj",
        type=params.object,
        label=OBJECTS[params.object].label,
        phrase=OBJECTS[params.object].phrase,
        region=OBJECTS[params.object].region,
    ))
    world.facts.update(hero=hero, helper=helper, obj=obj, params=params)

    trait = rng_trait(params.name)
    world.say(f"Once upon a time, {params.name} was a {trait} {params.role} who loved wandering by {setting.place}.")
    if params.object == "berry":
        world.say(f"{params.name} found a berry so bright it looked like a little ruby caught in the grass.")
    elif params.object == "tostado":
        world.say(f"{params.name} found a tostado cake with a golden crust and a sweet smell that filled the air.")
    else:
        world.say(f"{params.name} carried a soluble charm, a tiny treasure that melted kindly in warm water.")

    world.para()
    world.say(f"At first, {params.name} wanted to keep {obj.phrase} all to {hero.pronoun('possessive')}self and rush on.")
    world.say(f"But in the {setting.place}, a problem stirred: a spill of stream-water could touch {obj.label} and change it.")
    world.say(f"{params.name} frowned, because if the {obj.label} were soaked, it might not stay the same.")

    world.para()
    world.say(f"Then came a flashback.")
    world.say(f"Long ago, {params.name} had once shared bread with a hungry bird, and the bird had bowed its tiny head in thanks.")
    world.say(f"That memory returned like a lantern in the mind, and {params.name} remembered how good kindness felt.")

    world.para()
    world.say(f"So {params.name} called to the queen for help, and together they chose the gentle way.")
    world.say(f"They set {obj.phrase} on a dry stone, away from the water, and {params.name} shared a smaller treat with a friend instead.")
    world.say(f"Because kindness was stronger than greed, the day stayed sweet.")
    world.say(f"In the end, {params.name} kept {obj.label} safe, and the whole grove seemed to smile.")

    world.facts["resolved"] = True
    world.facts["flashback"] = True
    return world

def rng_trait(name: str) -> str:
    return random.choice(TRAITS)

def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f"Write a fairy tale about {p.name}, a {p.role}, in {world.setting.place}, featuring a berry, tostado, or soluble thing.",
        f"Tell a short magical story where kindness helps {p.name} remember a good deed from before.",
        f"Write a child-friendly tale in which a flashback changes how a {p.role} handles a small problem.",
    ]

def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    obj: Entity = world.facts["obj"]
    return [
        QAItem(
            question=f"Who is the fairy-tale story about?",
            answer=f"The story is about {p.name}, a {p.role} who visits {world.setting.place}.",
        ),
        QAItem(
            question=f"What problem could happen to the {obj.label}?",
            answer=f"The water could reach the {obj.label} and change it, so {p.name} wanted to keep it safe.",
        ),
        QAItem(
            question="What did the flashback remind the hero of?",
            answer=f"The flashback reminded {p.name} of an old kind act: sharing bread with a hungry bird.",
        ),
        QAItem(
            question="How was the problem solved?",
            answer=f"{p.name} chose kindness, asked the queen for help, and kept the {obj.label} dry and safe.",
        ),
    ]

def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean if something is soluble?",
            answer="If something is soluble, it can dissolve in water and seem to disappear into it.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a scene that remembers something from earlier time in the story or before it.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means acting gently and helping someone instead of being mean or greedy.",
        ),
    ]

def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id} ({e.type}) label={e.label!r} meters={e.meters} memes={e.memes}")
    lines.append(f"  facts={world.facts.keys()}")
    return "\n".join(lines)

def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    return StorySample(
        params=params,
        story=story_text(world),
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
        for i, q in enumerate(sample.story_qa, 1):
            print(f"Q{i}: {q.question}")
            print(f"A{i}: {q.answer}")
        for i, q in enumerate(sample.world_qa, 1):
            print(f"W{i}: {q.question}")
            print(f"A{i}: {q.answer}")

CURATED = [
    StoryParams(name="Ayla", role="girl", place="berrygrove", object="berry"),
    StoryParams(name="Mina", role="princess", place="castlekitchen", object="tostado"),
    StoryParams(name="Lio", role="boy", place="springwell", object="soluble"),
]

def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        print(sorted(set(asp.atoms(model, "valid"))))
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
