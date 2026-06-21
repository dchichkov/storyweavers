#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/tailed_bottle_broom_sharing_heartwarming.py
============================================================================

A standalone story world for a small heartwarming sharing tale.

Seed words: tailed, bottle, broom
Feature: Sharing
Style: Heartwarming

Premise:
- Two children are making something cozy together in a small room.
- One finds a bottle that seems important.
- A broom is needed after a small spill.
- A tailed pet or tailed friend can be part of the scene, but the core turn is
  about sharing, calming down, and working together.

The world is intentionally tiny and classical:
- typed entities with physical `meters` and emotional `memes`
- a small forward-chained rule engine
- a reasonableness gate
- prompts / story QA / world-knowledge QA
- an inline ASP twin for parity checks

The generated stories are meant to be warm, concrete, and complete.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
    cozy: str
    affords: set[str] = field(default_factory=set)

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
class Item:
    id: str
    label: str
    phrase: str
    kind: str
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
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

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
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone

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


def _r_spill(world: World) -> list[str]:
    out = []
    if world.facts.get("spill") and "floor" in world.entities:
        floor = world.get("floor")
        if floor.meters["messy"] < THRESHOLD and ("spill",) not in world.fired:
            world.fired.add(("spill",))
            floor.meters["messy"] += 1
            out.append("__spill__")
    return out


def _r_shared_help(world: World) -> list[str]:
    out = []
    if world.facts.get("shared") and ("shared_help",) not in world.fired:
        if "helper" in world.entities:
            world.fired.add(("shared_help",))
            helper = world.get("helper")
            helper.memes["warmth"] += 1
            out.append("__shared__")
    return out


CAUSAL_RULES = [Rule("spill", _r_spill), Rule("shared_help", _r_shared_help)]


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


def reasonableness_gate(item: Item, setting: Setting) -> bool:
    return item.id in setting.affords


def has_sharing_path(items: dict[str, Item]) -> bool:
    return "bottle" in items and "broom" in items


def tell(setting: Setting, child1: Entity, child2: Entity, parent: Entity,
         bottle: Item, broom: Item, tail_pet: Entity, shared: bool, spill: bool) -> World:
    world = World(setting)
    a = world.add(child1)
    b = world.add(child2)
    p = world.add(parent)
    pet = world.add(tail_pet)
    bottle_ent = world.add(Entity(id="bottle", kind="thing", type="item", label=bottle.label))
    broom_ent = world.add(Entity(id="broom", kind="thing", type="item", label=broom.label))
    floor = world.add(Entity(id="floor", kind="thing", type="floor", label="the floor"))

    a.memes["hope"] += 1
    b.memes["care"] += 1
    pet.memes["tail_wag"] += 1

    world.say(
        f"On a quiet afternoon, {a.id} and {b.id} were in {setting.place}. "
        f"{setting.cozy} A tailed little pet trotted close behind them, curious about everything."
    )
    world.say(
        f"{a.id} lifted {bottle.phrase} and smiled. \"We can share it,\" {a.id} said, "
        f"while {b.id} reached for {broom.phrase} to help keep the room neat."
    )

    if spill:
        world.para()
        world.say(
            f"Then the bottle tipped a little, and a small splash spread across the floor. "
            f"{b.id} did not blame anyone. {b.id} simply handed over the broom and said, "
            f'\"Let\'s clean it together.\"'
        )
        world.facts["spill"] = True
        propagate(world, narrate=False)
        floor.meters["messy"] = 0.0
        bottle_ent.meters["used"] += 1
        broom_ent.meters["used"] += 1
        a.memes["relief"] += 1
        b.memes["relief"] += 1
        p.memes["pride"] += 1
        world.say(
            f"{a.id} took one side of the room, {b.id} took the other, and the broom swept the splash into a neat little pile. "
            f"The floor shone again, and the pet wagged its tail as if it knew the friends had done something kind."
        )
    else:
        world.facts["spill"] = False
        world.say(
            f"{b.id} held the broom nearby just in case, and the bottle stayed steady in both careful hands. "
            f"The children took turns, passing it back and forth so no one felt left out."
        )

    world.para()
    world.say(
        f"At the end, {a.id} poured the last bit into the project, {b.id} leaned the broom against the wall, "
        f"and the tailed pet curled up at their feet. It was a small day, but it felt warm and shared."
    )

    world.facts.update(
        child1=a, child2=b, parent=p, bottle=bottle_ent, broom=broom_ent, pet=pet,
        setting=setting, shared=shared, spill=spill, outcome="spill" if spill else "steady"
    )
    return world


SETTINGS = {
    "kitchen": Setting("kitchen", "the kitchen", "Sunlight warmed the table, and the room smelled like cookies.", {"bottle", "broom"}),
    "studio": Setting("studio", "the little studio", "Paint cups sat beside a bright window, and the room felt calm and creative.", {"bottle", "broom"}),
    "laundry": Setting("laundry", "the laundry room", "Clean towels were folded in a stack, and everything felt tidy.", {"bottle", "broom"}),
}

BOTTLES = {
    "soap": Item("soap", "soap bottle", "a blue bottle of soap", "bottle", {"sharing", "clean"}),
    "juice": Item("juice", "juice bottle", "a small bottle of juice", "bottle", {"sharing", "drink"}),
}

BROOMS = {
    "red": Item("red", "broom", "a little red broom", "broom", {"clean"}),
    "blue": Item("blue", "broom", "a blue-handled broom", "broom", {"clean"}),
}

PETS = {
    "cat": Entity(id="Mimi", kind="character", type="cat", label="the cat"),
    "dog": Entity(id="Taffy", kind="character", type="dog", label="the dog"),
}

NAMES = ["Maya", "Noah", "Lila", "Eli", "Rosa", "Theo", "Ada", "Finn"]
TRAITS = ["gentle", "patient", "thoughtful", "kind"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    bottle: str
    broom: str
    child1: str
    child1_gender: str
    child2: str
    child2_gender: str
    parent: str
    parent_gender: str
    pet: str
    spill: bool = True
    shared: bool = True
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


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, b, r) for s in SETTINGS for b in BOTTLES for r in BROOMS if reasonableness_gate(BOTTLES[b], SETTINGS[s])]


ASP_RULES = r"""
valid(S, B, R) :- setting(S), bottle(B), broom(R).
shared_story(S, B, R) :- valid(S, B, R).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for bid in BOTTLES:
        lines.append(asp.fact("bottle", bid))
    for rid in BROOMS:
        lines.append(asp.fact("broom", rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming sharing storyworld with a bottle and a broom.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--bottle", choices=BOTTLES)
    ap.add_argument("--broom", choices=BROOMS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.bottle is None or c[1] == args.bottle)
              and (args.broom is None or c[2] == args.broom)]
    if not combos:
        curated = globals().get("CURATED", [])
        explicit = [
            v for k, v in vars(args).items()
            if k not in {"n", "seed", "all", "trace", "qa", "json", "asp", "verify", "show_asp"}
            and v is not None
            and v is not False
        ]
        if curated and not explicit:
            choice = rng.choice(curated)
            return choice if isinstance(choice, StoryParams) else StoryParams(*choice)
        raise StoryError("(No valid combination matches the given options.)")
    setting, bottle, broom = rng.choice(sorted(combos))
    c1 = rng.choice(NAMES)
    c2 = rng.choice([n for n in NAMES if n != c1])
    parent = rng.choice(NAMES)
    pet = rng.choice(list(PETS))
    return StoryParams(setting, bottle, broom, c1, "girl", c2, "boy", parent, "adult", pet, spill=True, shared=True)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a heartwarming story for a young child that includes the words "tailed", "bottle", and "broom".',
        f"Tell a sharing story where {f['child1'].id} and {f['child2'].id} calmly share a bottle and use a broom together.",
        f"Write a gentle story set in {f['setting'].place} about helping, sharing, and cleaning up a small mess.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a, b, p = f["child1"], f["child2"], f["parent"]
    return [
        ("Who is the story about?",
         f"It is about {a.id} and {b.id}, who were sharing things and helping each other."),
        ("What did they share?",
         f"They shared a bottle and a broom, so the work and the fun both belonged to both of them."),
        ("What happened when the bottle tipped?",
         f"A small splash got on the floor, but the children stayed calm and cleaned it together. Sharing the broom made the cleanup feel easy and kind."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a broom?",
         "A broom is a tool with bristles that people use to sweep up dirt and small messes from the floor."),
        ("Why is sharing kind?",
         "Sharing is kind because it lets more than one person enjoy something or use it fairly, and it helps people work together."),
        ("What does a tailed pet mean?",
         "A tailed pet is an animal with a tail, and tails can wiggle, wag, or swish when the animal is happy or curious."),
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.label:
            bits.append(f"label={e.label}")
        if bits:
            lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        Entity(id=params.child1, kind="character", type=params.child1_gender, role="child"),
        Entity(id=params.child2, kind="character", type=params.child2_gender, role="child"),
        Entity(id=params.parent, kind="character", type=params.parent_gender, role="parent"),
        BOTTLES[params.bottle],
        BROOMS[params.broom],
        PETS[params.pet],
        params.shared,
        params.spill,
    )
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


CURATED = [
    StoryParams("kitchen", "soap", "red", "Maya", "girl", "Noah", "boy", "Iris", "woman", "cat", True, True),
    StoryParams("studio", "juice", "blue", "Lila", "girl", "Eli", "boy", "Ben", "man", "dog", True, True),
]


def explain_rejection() -> str:
    return "(No story: this little world only supports settings where sharing a bottle and using a broom make sense.)"


def asp_verify() -> int:
    import storyworlds.asp as asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    rc = 0
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in the gate:")
        print("  only in python:", sorted(py - cl))
        print("  only in clingo:", sorted(cl - py))
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"FAIL: generation smoke test crashed: {exc}")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for row in combos:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()
