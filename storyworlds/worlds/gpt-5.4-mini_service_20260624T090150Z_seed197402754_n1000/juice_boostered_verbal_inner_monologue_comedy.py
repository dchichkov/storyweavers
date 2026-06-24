#!/usr/bin/env python3
"""
A small comedy storyworld about a character's inner monologue, a glass of juice,
and a boisterous "booster" gadget that helps them speak more bravely than they
feel.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Core model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name_or_label(self) -> str:
        return self.label or self.id


@dataclass
class Setting:
    place: str = "the kitchen"
    affords: set[str] = field(default_factory=set)


@dataclass
class ObjectSpec:
    id: str
    label: str
    phrase: str
    type: str
    kind: str = "thing"
    plural: bool = False


@dataclass
class DeviceSpec:
    id: str
    label: str
    phrase: str
    helper_phrase: str
    makes: str
    helps_with: str
    valid_on: set[str]


@dataclass
class StoryParams:
    setting: str
    object: str
    device: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.events: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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

    def clone(self) -> "World":
        w = World(self.setting)
        w.entities = json.loads(json.dumps({k: asdict(v) for k, v in self.entities.items()}))
        # reconstruct only what we need for prediction
        rebuilt: dict[str, Entity] = {}
        for k, d in w.entities.items():
            rebuilt[k] = Entity(**d)
        w.entities = rebuilt
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "kitchen": Setting(place="the kitchen", affords={"juice"}),
    "picnic": Setting(place="the picnic blanket", affords={"juice"}),
    "cafeteria": Setting(place="the cafeteria", affords={"juice"}),
}

OBJECTS = {
    "shirt": ObjectSpec("shirt", "shirt", "a clean shirt", "shirt"),
    "tie": ObjectSpec("tie", "tie", "a fancy tie", "tie"),
    "notebook": ObjectSpec("notebook", "notebook", "a brand-new notebook", "notebook"),
}

DEVICES = {
    "juice_booster": DeviceSpec(
        id="juice_booster",
        label="juice booster",
        phrase="a juice booster",
        helper_phrase="turn up the juice booster",
        makes="verbal",
        helps_with="bravery",
        valid_on={"shirt", "tie", "notebook"},
    ),
    "straw_hat": DeviceSpec(
        id="straw_hat",
        label="straw hat",
        phrase="a straw hat",
        helper_phrase="put on the straw hat",
        makes="verbal",
        helps_with="timing",
        valid_on={"shirt", "tie"},
    ),
}

GIRL_NAMES = ["Mia", "Lena", "Zoe", "Ada", "Nina", "Pia"]
BOY_NAMES = ["Max", "Finn", "Leo", "Noah", "Eli", "Ben"]
TRAITS = ["brave", "silly", "curious", "shy", "playful"]

KNOWLEDGE = {
    "juice": [
        (
            "What is juice?",
            "Juice is a drink made from fruit. It can taste sweet and come in a cup or a glass.",
        ),
        (
            "Why do people drink juice?",
            "People drink juice because it tastes nice and can feel refreshing.",
        ),
    ],
    "verbal": [
        (
            "What does verbal mean?",
            "Verbal means using words, like talking or speaking out loud.",
        )
    ],
    "booster": [
        (
            "What is a booster?",
            "A booster is something that helps make a feeling or action stronger, like giving a little extra push.",
        )
    ],
    "inner monologue": [
        (
            "What is inner monologue?",
            "Inner monologue is the quiet talking a person does inside their own head.",
        )
    ],
}
KNOWLEDGE_ORDER = ["inner monologue", "juice", "booster", "verbal"]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def risk_of_spill(obj: Entity, device: DeviceSpec) -> bool:
    return obj.type in device.valid_on


def choose_device(obj: Entity) -> Optional[DeviceSpec]:
    for d in DEVICES.values():
        if risk_of_spill(obj, d):
            return d
    return None


def predict_spill(obj: Entity, device: DeviceSpec) -> bool:
    return obj.type == "shirt" or obj.type == "tie"


def tell(setting: Setting, obj_spec: ObjectSpec, dev: DeviceSpec, name: str, gender: str, parent: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=gender, traits=["little"]))
    caretaker = world.add(Entity(id="Parent", kind="character", type=parent, label=f"the {parent}"))
    obj = world.add(Entity(id="thing", type=obj_spec.type, label=obj_spec.label, phrase=obj_spec.phrase))
    device = world.add(Entity(id=dev.id, type="gadget", label=dev.label, phrase=dev.phrase, owner=hero.id))

    hero.memes["nervous"] = 1
    hero.memes["curiosity"] = 1

    world.say(
        f"{name} was a little {random.choice(TRAITS)} {gender} who noticed every strange thing on the table."
    )
    world.say(
        f"On the counter sat {obj.phrase}, and nearby was {dev.phrase}."
    )
    world.say(
        f"{name} had an inner monologue that was very brave in a tiny squeaky voice: "
        f'"Maybe if I just stare at it, I will become a famous speaker."'
    )

    world.para()
    world.say(
        f"One day, {name} went to {setting.place} with {caretaker.name_or_label()}."
    )
    world.say(
        f"{name} wanted to be verbal and say something clever, but {name} also wanted to keep {obj.label} clean."
    )

    if predict_spill(obj, dev):
        world.say(
            f'Inside {name}\'s head, a dramatic announcer whispered, "Danger: snack-level confidence may cause a spill."'
        )
        world.say(
            f"{caretaker.name_or_label().capitalize()} smiled and said, "
            f'"Use the {dev.label} first, then you can speak with a big voice."'
        )
    else:
        world.say(
            f"{name} was so excited that even the inner monologue started clapping quietly."
        )

    world.para()
    hero.memes["joy"] = 1
    hero.memes["confidence"] = 1
    world.say(
        f"{name} took a deep breath and {dev.helper_phrase}."
    )
    world.say(
        f"Then {name} said a very verbal line: 'Hello, world, I am here for the juice!'"
    )
    world.say(
        f"The {obj.label} stayed neat, the juice stayed in the cup, and {name} felt proud of the funny little plan."
    )

    world.facts.update(hero=hero, caretaker=caretaker, obj=obj, device=device, setting=setting, obj_spec=obj_spec, dev_spec=dev)
    return world


# ---------------------------------------------------------------------------
# QA helpers
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    obj = f["obj_spec"]
    dev = f["dev_spec"]
    return [
        f'Write a short comedy story about "{hero.id}" using the words "juice", "{dev.label}", and "verbal".',
        f"Tell a gentle story where a child wants to speak out loud but worries about {obj.phrase}, then finds a funny solution.",
        f"Write a tiny story with an inner monologue, a juice booster, and a happy ending at {world.setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    obj = f["obj"]
    dev = f["device"]
    parent = f["caretaker"]
    return [
        QAItem(
            question=f"What did {hero.id} want to be at {world.setting.place}?",
            answer=f"{hero.id} wanted to be verbal and say something clever, even though {hero.id} felt a little nervous.",
        ),
        QAItem(
            question=f"Why did {parent.name_or_label()} suggest the {dev.label}?",
            answer=f"{parent.name_or_label()} suggested the {dev.label} because it helped {hero.id} speak with more confidence while keeping {obj.label} safe.",
        ),
        QAItem(
            question=f"What stayed clean at the end of the story?",
            answer=f"The {obj.label} stayed clean, the juice stayed in the cup, and {hero.id} ended the day feeling proud.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"inner monologue", "juice", "booster", "verbal"}
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
risk(O,D) :- object(O), device(D), valid_on(D,O).
valid_story(S,O,D) :- setting(S), object(O), device(D), affords(S,juice), risk(O,D).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        lines.append(asp.fact("valid_on", "juice_booster", oid)) if oid in DEVICES["juice_booster"].valid_on else None
        lines.append(asp.fact("valid_on", "straw_hat", oid)) if oid in DEVICES["straw_hat"].valid_on else None
    for did, d in DEVICES.items():
        lines.append(asp.fact("device", did))
        for o in sorted(d.valid_on):
            lines.append(asp.fact("valid_on", did, o))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))

def asp_verify() -> int:
    py = {(s, o, d) for s in SETTINGS for o in OBJECTS for d in DEVICES if s in SETTINGS and risk_of_spill(OBJECTS[o], DEVICES[d])}
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("python-only:", sorted(py - cl))
    print("clingo-only:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld: inner monologue, juice, and a booster.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--device", choices=DEVICES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    setting = args.setting or rng.choice(list(SETTINGS))
    obj = args.object or rng.choice(list(OBJECTS))
    dev = args.device or rng.choice(list(DEVICES))
    if args.object and args.device and not risk_of_spill(OBJECTS[args.object], DEVICES[args.device]):
        raise StoryError("No story: that device does not actually help with that object.")
    if args.gender is None:
        gender = rng.choice(["girl", "boy"])
    else:
        gender = args.gender
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting=setting, object=obj, device=dev, name=name, gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], OBJECTS[params.object], DEVICES[params.device], params.name, params.gender, params.parent)
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
        bits = []
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
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
    StoryParams(setting="kitchen", object="shirt", device="juice_booster", name="Mia", gender="girl", parent="mother"),
    StoryParams(setting="picnic", object="tie", device="juice_booster", name="Finn", gender="boy", parent="father"),
    StoryParams(setting="cafeteria", object="notebook", device="juice_booster", name="Zoe", gender="girl", parent="mother"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_stories())
        return

    base = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base + i
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
