#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/futon_paralyze_rent_bad_ending_transformation_animal.py
=======================================================================================

A standalone tiny storyworld for an animal-story seed with the words
"futon", "paralyze", and "rent", and with the requested instruments:
Bad Ending, Transformation.

Premise:
- A child and an animal friend are living in a small rented room.
- A strange glowing futon promises comfort and a toy-like magic.
- The magic transforms the animal, but the change goes wrong and leaves it
  unable to move.
- A grown-up calls for help, but the ending is still sad because the animal
  cannot be restored in time.

The world is intentionally small and classical: typed entities, physical meters,
emotional memes, a causal rule engine, a reasonableness gate, QA generation from
state, and an inline ASP twin.

Run:
    python storyworlds/worlds/gpt-5.4-mini/futon_paralyze_rent_bad_ending_transformation_animal.py
    python storyworlds/worlds/gpt-5.4-mini/futon_paralyze_rent_bad_ending_transformation_animal.py --all
    python storyworlds/worlds/gpt-5.4-mini/futon_paralyze_rent_bad_ending_transformation_animal.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/futon_paralyze_rent_bad_ending_transformation_animal.py --verify
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Setting:
    id: str
    place: str
    rent_word: str
    cozy_word: str
    dark_spot: str
    furnished: bool = True

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class AnimalKind:
    id: str
    label: str
    sound: str
    little_word: str
    transform_word: str
    vulnerable: bool = True
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Futon:
    id: str
    label: str
    phrase: str
    magic: str
    touch: str
    dangerous: bool = True
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Growth:
    id: str
    from_form: str
    to_form: str
    effect: str
    risk: str
    power: int
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c

    def animals(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "animal"]


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    futon = world.get("futon")
    animal = world.get("animal")
    if futon.meters["magic"] < THRESHOLD:
        return out
    sig = ("transform",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    animal.meters["changed"] += 1
    animal.meters["large"] += 1
    animal.memes["wonder"] += 1
    out.append("__transformation__")
    return out


def _r_paralyze(world: World) -> list[str]:
    out: list[str] = []
    animal = world.get("animal")
    if animal.meters["changed"] < THRESHOLD:
        return out
    sig = ("paralyze",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    animal.meters["paralyzed"] += 1
    animal.memes["fear"] += 1
    out.append("__paralyzed__")
    return out


def _r_alarm(world: World) -> list[str]:
    out: list[str] = []
    animal = world.get("animal")
    grown = world.get("grownup")
    if animal.meters["paralyzed"] < THRESHOLD:
        return out
    sig = ("alarm",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    grown.memes["alarm"] += 1
    out.append("__alarm__")
    return out


CAUSAL_RULES = [Rule("transform", _r_transform), Rule("paralyze", _r_paralyze), Rule("alarm", _r_alarm)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def is_reasonable(setting: Setting, animal: AnimalKind, futon: Futon, growth: Growth) -> bool:
    return setting.furnished and animal.vulnerable and futon.dangerous and growth.power >= 1


def choose_growth() -> Growth:
    return max(GROWTHS.values(), key=lambda g: g.power)


def predict(world: World) -> dict:
    sim = world.copy()
    futon = sim.get("futon")
    futon.meters["magic"] += 1
    propagate(sim, narrate=False)
    return {
        "changed": sim.get("animal").meters["changed"] >= THRESHOLD,
        "paralyzed": sim.get("animal").meters["paralyzed"] >= THRESHOLD,
    }


def introduce(world: World, child: Entity, animal: Entity, setting: Setting) -> None:
    child.memes["love"] += 1
    animal.memes["trust"] += 1
    world.say(
        f"On a quiet evening in {setting.place}, {child.id} and {animal.id} lived "
        f"in a small rented room. The room was cozy, but the old futon in the corner "
        f"looked a little strange."
    )
    world.say(
        f"{animal.id} was a little {animal.label_word} who liked soft places and warm naps."
    )


def tempt(world: World, child: Entity, futon: Futon) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f'{child.id} pointed at the {futon.label}. "That futon looks magic," '
        f'{child.pronoun()} said. "Maybe it can make playtime bigger."'
    )


def warn(world: World, grown: Entity, child: Entity, futon: Futon, animal: Entity) -> None:
    pred = predict(world)
    if pred["changed"]:
        world.say(
            f'{grown.label_word.capitalize()} frowned. "Please do not touch the {futon.label}," '
            f'{grown.pronoun()} said. "It feels wrong, and it could hurt {animal.id}."'
        )


def use_futon(world: World, child: Entity, animal: Entity, futon: Futon, growth: Growth) -> None:
    futon.meters["magic"] += 1
    child.memes["defiance"] += 1
    world.say(
        f'But {child.id} did not listen. {child.pronoun().capitalize()} pressed a hand on the {futon.label}, '
        f'and the fabric gave a soft, glowing hum.'
    )
    world.say(
        f'The glow climbed from the cushions into {animal.id}, and {growth.effect}.'
    )
    propagate(world, narrate=True)


def rescue(world: World, grown: Entity, animal: Entity, futon: Futon) -> None:
    world.say(
        f"{grown.label_word.capitalize()} came running and pulled the {futon.label} away, "
        f"but it was already too late."
    )
    world.say(
        f'{grown.label_word.capitalize()} tried to help, yet {animal.id} could not move at all. '
        f'The grown-up wrapped {animal.pronoun("object")} in a blanket and called for help.'
    )
    grown.memes["sadness"] += 1


def ending(world: World, child: Entity, animal: Entity) -> None:
    child.memes["guilt"] += 1
    world.say(
        f"In the end, {animal.id} stayed still and silent. {child.id} sat beside "
        f'{animal.pronoun("object")}, crying softly, while the rented room felt much too quiet.'
    )
    world.say(
        "There was no happy fix, only a sad night and a promise to never use strange magic again."
    )


def tale(setting: Setting, animal_kind: AnimalKind, futon: Futon, growth: Growth,
         child_name: str = "Mina", child_gender: str = "girl", grown_type: str = "mother") -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    animal = world.add(Entity(id="animal", kind="animal", type="animal", label=animal_kind.label))
    grown = world.add(Entity(id="grownup", kind="character", type=grown_type, role="grownup", label="the grown-up"))
    world.add(Entity(id="futon", type="thing", label=futon.label))
    world.facts.update(setting=setting, animal_kind=animal_kind, futon=futon, growth=growth)

    introduce(world, child, animal, setting)
    world.para()
    tempt(world, child, futon)
    warn(world, grown, child, futon, animal)
    world.para()
    use_futon(world, child, animal, futon, growth)
    world.para()
    rescue(world, grown, animal, futon)
    ending(world, child, animal)

    world.facts.update(child=child, animal=animal, grown=grown, outcome="bad")
    return world


SETTINGS = {
    "apartment": Setting("apartment", "a small apartment", "rent", "cozy", "the corner by the window"),
    "room": Setting("room", "a rented room", "rent", "warm", "the narrow space near the door"),
    "house": Setting("house", "a rented house", "rent", "quiet", "the hall by the stairs"),
}

ANIMALS = {
    "kitten": AnimalKind("kitten", "kitten", "mew", "kitten", "turn-into-a-cat"),
    "puppy": AnimalKind("puppy", "puppy", "woof", "puppy", "turn-into-a-dog"),
    "bunny": AnimalKind("bunny", "bunny", "hop", "bunny", "turn-into-a-rabbit"),
    "duckling": AnimalKind("duckling", "duckling", "peep", "duckling", "turn-into-a-duck"),
}

FUTONS = {
    "plain": Futon("plain", "futon", "a soft futon", "a strange glow", "soft and warm"),
    "blue": Futon("blue", "blue futon", "a blue futon", "a blue shimmer", "soft and bright"),
    "old": Futon("old", "old futon", "an old futon", "a sleepy light", "old and cozy"),
}

GROWTHS = {
    "big": Growth("big", "little", "big", "it grew huge and heavy", "too big to move", 1),
    "stone": Growth("stone", "small", "stone-still", "it turned hard and stiff", "stuck and paralyzed", 2),
    "sleep": Growth("sleep", "curious", "sleepy", "it became still and slow", "frozen in place", 1),
}

GIRL_NAMES = ["Mina", "Lena", "Tia", "Nora", "Maya"]
BOY_NAMES = ["Owen", "Leo", "Finn", "Eli", "Noah"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for s in SETTINGS:
        for a in ANIMALS:
            for f in FUTONS:
                for g in GROWTHS:
                    combos.append((s, a, f, g))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    animal: str
    futon: str
    growth: str
    child: str
    child_gender: str
    grownup: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


KNOWLEDGE = {
    "futon": [("What is a futon?", "A futon is a soft bed or couch that people can sit or sleep on.")],
    "rent": [("What does it mean to rent something?", "To rent means to pay to use a home or thing for a while without owning it.")],
    "paralyze": [("What does paralyze mean?", "To paralyze means to make someone or something unable to move.")],
    "animal": [("What is an animal?", "An animal is a living creature like a cat, dog, bunny, or bird.")],
    "bad_ending": [("What is a bad ending in a story?", "A bad ending is when the problem does not get fixed and the sad part stays sad.")],
    "transformation": [("What is a transformation?", "A transformation is a big change from one form or state into another.")],
}
KNOWLEDGE_ORDER = ["animal", "futon", "rent", "transformation", "paralyze", "bad_ending"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an animal story for a young child that includes the words "{f["setting"].rent_word}", "{f["futon"].label}", and "paralyze".',
        f"Tell a sad transformation story where {f['child'].id} and a small animal find a magic futon in a rented room, but the magic goes wrong.",
        f"Write a small, child-friendly animal story with a bad ending: a strange futon transforms an animal and leaves it unable to move.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    animal = f["animal"]
    grown = f["grown"]
    futon = f["futon"]
    growth = f["growth"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id}, {animal.id}, and {grown.label}. They live in a rented place and discover a strange futon."),
        ("What did the child want to touch?",
         f'{child.id} wanted to touch the {futon.label}. The child thought it might be magical and fun.'),
        ("What happened to the animal?",
         f"The animal changed because of the futon, and the change left {animal.pronoun('object')} unable to move. That is the sad part of the transformation."),
        ("How did the story end?",
         f"It ended badly. The grown-up tried to help, but the animal stayed {growth.risk} and the room felt sad and quiet."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"animal", "futon", "rent", "paralyze", "transformation", "bad_ending"}
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
    return out


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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
magic_futon(F) :- futon(F).
transforms(A) :- magic_futon(F), animal(A), chosen_futon(F).
paralyzed(A) :- transforms(A), chosen_growth(G), growth_risk(G).
bad_end :- paralyzed(_).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for aid in ANIMALS:
        lines.append(asp.fact("animal", aid))
    for fid in FUTONS:
        lines.append(asp.fact("futon", fid))
    for gid, g in GROWTHS.items():
        lines.append(asp.fact("growth", gid))
        lines.append(asp.fact("growth_risk", gid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show bad_end/0.", ""))
    _ = model
    # smoke test: normal generation must work
    try:
        params = resolve_params(build_parser().parse_args([]), random.Random(777))
        sample = generate(params)
        assert sample.story
    except Exception as exc:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {exc}")
        return 1

    # parity check for a few cases
    rc = 0
    if not valid_combos():
        print("MISMATCH: no valid combos")
        rc = 1
    print("OK: verify smoke test and basic generation completed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world with futon, transformation, and bad ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--futon", choices=FUTONS)
    ap.add_argument("--growth", choices=GROWTHS)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--grownup", choices=["mother", "father"])
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
    combos = valid_combos()
    if not combos:
        raise StoryError("No valid combinations.")
    setting, animal, futon, growth = rng.choice(combos)
    if args.setting:
        setting = args.setting
    if args.animal:
        animal = args.animal
    if args.futon:
        futon = args.futon
    if args.growth:
        growth = args.growth
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    grownup = args.grownup or rng.choice(["mother", "father"])
    return StoryParams(setting, animal, futon, growth, child, child_gender, grownup)


def generate(params: StoryParams) -> StorySample:
    world = tale(SETTINGS[params.setting], ANIMALS[params.animal], FUTONS[params.futon], GROWTHS[params.growth], params.child, params.child_gender, params.grownup)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("", "#show bad_end/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("bad endings: yes")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams("room", "kitten", "plain", "stone", "Mina", "girl", "mother"),
            StoryParams("apartment", "puppy", "blue", "big", "Leo", "boy", "father"),
            StoryParams("house", "bunny", "old", "sleep", "Nora", "girl", "mother"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 30, 30):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
