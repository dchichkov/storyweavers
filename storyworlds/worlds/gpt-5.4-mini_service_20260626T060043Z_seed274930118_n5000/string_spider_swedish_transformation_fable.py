#!/usr/bin/env python3
"""
storyworlds/worlds/string_spider_swedish_transformation_fable.py
=================================================================

A small fable-like storyworld about a spider, a string, and a gentle
transformation into something useful and beautiful.

Seed tale:
---
A little spider found a plain string in a quiet shed. It wanted to make a home,
but the string was limp and lonely. A wind tugged at it, and the spider nearly
gave up. Then the spider remembered the old lesson: patient hands can turn a
simple thing into a fine thing. It spun, twisted, and tied until the string
became a bright Swedish ribbon for the nest. The spider smiled, and the shed
felt wiser for it.

World model:
---
    - Entities have physical meters and emotional memes.
    - The spider can gather, twist, and weave string.
    - The string can be plain, tangled, or transformed.
    - Swedish-inspired color and pattern can emerge as a result of patient work.
    - A small tension beat appears when the string tangles or nearly breaks.
    - The resolution is a transformation: plain string -> Swedish ribbon.

Fable beat:
---
    1. Setup: the spider finds string and wants a better home.
    2. Tension: the string tangles in the wind and the spider is discouraged.
    3. Turn: a wiser helper or a remembered lesson encourages patience.
    4. Resolution: the string transforms into a Swedish ribbon, and the nest is made.
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
# World constants
# ---------------------------------------------------------------------------
THRESHOLD = 1.0


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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"spider"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"child", "girl", "boy"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the quiet shed"
    affords: set[str] = field(default_factory=set)


@dataclass
class Material:
    id: str
    label: str
    phrase: str
    kind: str
    pattern: str
    colors: tuple[str, str]
    transformed_label: str
    transformed_phrase: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)
    weather: str = "windy"

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        clone.weather = self.weather
        return clone


@dataclass
class StoryParams:
    place: str
    material: str
    hero_name: str
    seed: Optional[int] = None


SETTINGS = {
    "shed": Setting(place="the quiet shed", affords={"weave", "twist", "transform"}),
    "attic": Setting(place="the dusty attic", affords={"weave", "twist", "transform"}),
    "garden": Setting(place="the small garden bench", affords={"weave", "twist", "transform"}),
}

MATERIALS = {
    "string": Material(
        id="string",
        label="string",
        phrase="a plain length of string",
        kind="string",
        pattern="plain",
        colors=("blue", "yellow"),
        transformed_label="Swedish ribbon",
        transformed_phrase="a bright Swedish ribbon with blue and yellow stripes",
    ),
}

HERO_NAMES = ["Pip", "Mika", "Lina", "Sven", "Nora", "Elsa", "Tove", "Olle"]
HELPER_NAMES = ["Old Owl", "Grandmother Wind", "Wise Beetle"]

TRAITS = ["patient", "gentle", "curious", "thoughtful", "tidy"]

KNOWLEDGE = {
    "string": [
        ("What is string?",
         "String is a long, thin piece of fiber that can be tied, wrapped, or woven into things.")
    ],
    "spider": [
        ("What does a spider do with silk?",
         "A spider uses silk to make webs, hold things together, and build safe little homes.")
    ],
    "swedish": [
        ("What is something Swedish?",
         "Something Swedish comes from Sweden or is inspired by Swedish colors, patterns, or traditions.")
    ],
    "transformation": [
        ("What is a transformation?",
         "A transformation is when one thing changes into another thing in a clear and meaningful way.")
    ],
}

KNOWLEDGE_ORDER = ["string", "spider", "swedish", "transformation"]


class WorldError(StoryError):
    pass


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable world about string, a spider, and transformation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--material", choices=MATERIALS)
    ap.add_argument("--name")
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
    material = args.material or "string"
    if material != "string":
        raise StoryError("This fable world only supports the seed material: string.")
    name = args.name or rng.choice(HERO_NAMES)
    return StoryParams(place=place, material=material, hero_name=name)


def valid_combos() -> list[tuple[str, str]]:
    return [(p, m) for p in SETTINGS for m in MATERIALS]


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("setting", p))
        for a in sorted(SETTINGS[p].affords):
            lines.append(asp.fact("affords", p, a))
    for m in MATERIALS:
        lines.append(asp.fact("material", m))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Material) :- setting(Place), material(Material), affords(Place, weave),
                          affords(Place, twist), affords(Place, transform).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


def _ensure_actor(world: World, hero: Entity, material: Entity) -> None:
    if hero.id not in world.entities or material.id not in world.entities:
        raise StoryError("World is missing required entities.")


def predict_transform(world: World, hero: Entity, material: Entity) -> dict:
    sim = world.copy()
    h = sim.get(hero.id)
    m = sim.get(material.id)
    h.memes["resolve"] = h.memes.get("resolve", 0.0) + 1
    m.meters["twist"] = m.meters.get("twist", 0.0) + 1
    m.meters["transformed"] = 1.0
    return {"transformed": m.meters["transformed"] >= THRESHOLD}


def tell(setting: Setting, material_cfg: Material, hero_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="spider"))
    helper = world.add(Entity(id="Helper", kind="character", type="owl", label="Old Owl"))
    string = world.add(Entity(
        id="string",
        type="string",
        label="string",
        phrase=material_cfg.phrase,
        owner=hero.id,
        meters={"plain": 1.0},
    ))

    world.say(f"{hero.id} was a small spider who lived near {setting.place}.")
    world.say(f"{hero.id} found {string.phrase} and liked how simple and strong it looked.")
    world.say(f"{hero.id} wanted to make a better home from {string.label}, because a wise spider knows that little things can grow into useful things.")

    world.para()
    world.say(f"One windy afternoon, the string tugged and twisted in the breeze.")
    string.meters["tangled"] = 1.0
    hero.memes["worry"] = 1.0
    world.say(f"{hero.id} paused, because the string looked tangled and thin, and for a moment {hero.pronoun()} almost gave up.")
    world.say(f"Then {helper.label} called softly, 'Patience can turn a plain thing into a fine thing.'")

    world.para()
    hero.memes["resolve"] = 1.0
    world.say(f"{hero.id} listened and worked slowly.")
    world.say(f"First {hero.id} twisted the string, then {hero.id} tied it, then {hero.id} wove it with care.")
    string.meters["twist"] = 1.0
    string.meters["woven"] = 1.0
    string.meters["transformed"] = 1.0
    string.label = material_cfg.transformed_label
    string.phrase = material_cfg.transformed_phrase
    world.say(f"In the end, the plain string became {string.phrase}.")
    world.say(f"{hero.id} hung it in the nest like a tiny flag of blue and yellow, and the shed felt brighter, as if it had learned the same lesson.")

    world.facts.update(
        hero=hero,
        helper=helper,
        material=string,
        setting=setting,
        transformed=True,
        color_a=material_cfg.colors[0],
        color_b=material_cfg.colors[1],
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    material = f["material"]
    return [
        f"Write a gentle fable for a child about a spider named {hero.id} who finds {material.phrase} and changes it with patience.",
        f"Tell a short moral story where a spider uses string, listens to a wise helper, and ends with a Swedish ribbon.",
        f"Write a simple fable about transformation: a spider, a string, and a bright blue-and-yellow ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    material = f["material"]
    qa = [
        QAItem(
            question=f"Who found the string in the story?",
            answer=f"{hero.id}, the little spider, found the string in {world.setting.place}.",
        ),
        QAItem(
            question=f"What did the string turn into at the end?",
            answer=f"It transformed into {material.phrase}.",
        ),
        QAItem(
            question=f"Why did {hero.id} not give up when the string tangled?",
            answer=f"{hero.id} remembered that patient work can change a plain thing into a fine thing, so {hero.pronoun()} kept weaving slowly.",
        ),
        QAItem(
            question="What lesson did the story teach?",
            answer="The story taught that patience and careful work can transform something plain into something beautiful and useful.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = []
    for key in KNOWLEDGE_ORDER:
        for q, a in KNOWLEDGE[key]:
            out.append(QAItem(question=q, answer=a))
    return out


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
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], MATERIALS[params.material], params.hero_name)
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
    StoryParams(place="shed", material="string", hero_name="Pip"),
    StoryParams(place="attic", material="string", hero_name="Mika"),
    StoryParams(place="garden", material="string", hero_name="Lina"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/2."))
        print(asp.atoms(model, "valid"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 25):
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
            header = f"### {p.hero_name} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
