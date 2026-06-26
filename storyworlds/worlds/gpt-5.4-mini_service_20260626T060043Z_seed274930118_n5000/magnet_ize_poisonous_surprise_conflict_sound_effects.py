#!/usr/bin/env python3
"""
A small whodunit-style story world about a puzzling surprise, a conflict, and
the sound effects that help reveal who moved what.

The generated stories stay in one tiny domain:
- a child or small protagonist notices something strange
- a suspicious object has been magnet-ized
- a poisonous item must be kept away
- surprise and conflict create tension
- sound effects become clues that lead to a safe resolution

The world is intentionally compact and constraint-checked so every story can be
made as a complete little mystery.
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
# World model
# ---------------------------------------------------------------------------

@dataclass
class Character:
    id: str
    kind: str = "character"
    type: str = "child"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: {"distance": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"surprise": 0.0, "conflict": 0.0})

    def name(self) -> str:
        return self.label or self.id

    def pronoun(self) -> str:
        return "they"

    def possessive(self) -> str:
        return "their"


@dataclass
class ObjectItem:
    id: str
    kind: str = "thing"
    label: str = ""
    poisonous: bool = False
    magnetized: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: {"distance": 0.0, "danger": 0.0})
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str
    affordances: set[str] = field(default_factory=set)
    soundscape: list[str] = field(default_factory=list)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, entity):
        self.entities[entity.id] = entity
        return entity

    def get(self, eid: str):
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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "workbench": Setting(
        place="the workbench",
        affordances={"inspect", "clean", "listen"},
        soundscape=["clink", "tap", "whirr"],
    ),
    "kitchen": Setting(
        place="the kitchen counter",
        affordances={"inspect", "clean", "listen"},
        soundscape=["clink", "thump", "drip"],
    ),
    "shed": Setting(
        place="the garden shed",
        affordances={"inspect", "clean", "listen"},
        soundscape=["rattle", "clang", "creak"],
    ),
}

CHARACTER_TRAITS = ["careful", "curious", "brave", "quiet", "sharp-eyed"]
CHILD_NAMES = ["Mina", "Toby", "Noor", "Jules", "Iris", "Eli", "Pia", "Kai"]
ADULT_NAMES = ["Mira", "Jon", "Sam", "Lena", "Ravi", "Nia"]

ITEMS = {
    "spoon": {
        "label": "metal spoon",
        "poisonous": False,
        "magnetized": True,
        "clue_sound": "clink",
    },
    "jar": {
        "label": "shiny jar",
        "poisonous": True,
        "magnetized": False,
        "clue_sound": "tap",
    },
    "box": {
        "label": "tin box",
        "poisonous": False,
        "magnetized": True,
        "clue_sound": "clang",
    },
    "bottle": {
        "label": "blue bottle",
        "poisonous": True,
        "magnetized": False,
        "clue_sound": "drip",
    },
    "key": {
        "label": "little key",
        "poisonous": False,
        "magnetized": True,
        "clue_sound": "jingle",
    },
}

# A "whodunit" twist is that the clue is the wrong thing sticking to the magnet.
SURPRISE_WORDS = [
    "surprise", "suddenly", "unexpectedly", "to everyone's surprise"
]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    hero: str
    helper: str
    item: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------

def is_reasonable(setting: Setting, item_key: str) -> bool:
    return setting.place and item_key in ITEMS


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affordances):
            lines.append(asp.fact("affords", sid, a))
        for sfx in s.soundscape:
            lines.append(asp.fact("sound", sid, sfx))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if item["poisonous"]:
            lines.append(asp.fact("poisonous", iid))
        if item["magnetized"]:
            lines.append(asp.fact("magnetized", iid))
        lines.append(asp.fact("sound_clue", iid, item["clue_sound"]))
    return "\n".join(lines)


ASP_RULES = r"""
magnet_clue(I) :- magnetized(I).
danger(I) :- poisonous(I).
mystery(I) :- magnetized(I), poisonous(J), I != J.
safe_end(I) :- magnet_clue(I), danger(J).
#show mystery/1.
#show safe_end/1.
"""


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def verify_asp_parity() -> int:
    import asp
    model = asp.one_model(asp_program())
    mystery = set(asp.atoms(model, "mystery"))
    safe_end = set(asp.atoms(model, "safe_end"))
    py_mystery = {("spoon",), ("box",), ("key",)}  # magnetized items with poisonous somewhere else
    py_safe = {("spoon",), ("box",), ("key",)}
    ok = mystery == py_mystery and safe_end == py_safe
    if ok:
        print("OK: ASP parity verified.")
        return 0
    print("MISMATCH:")
    print(" ASP mystery:", sorted(mystery))
    print(" PY mystery:", sorted(py_mystery))
    print(" ASP safe:", sorted(safe_end))
    print(" PY safe:", sorted(py_safe))
    return 1


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    hero = world.add(Character(id=params.hero, type="child", label=params.hero, traits=[random.choice(CHARACTER_TRAITS)]))
    helper = world.add(Character(id=params.helper, type="adult", label=params.helper, traits=["helpful"]))
    item_def = ITEMS[params.item]
    item = world.add(ObjectItem(
        id=params.item,
        label=item_def["label"],
        poisonous=item_def["poisonous"],
        magnetized=item_def["magnetized"],
        owner=helper.id,
        meters={"distance": 2.0 if item_def["poisonous"] else 1.0, "danger": 1.0 if item_def["poisonous"] else 0.0},
    ))

    # Act 1: setup
    world.say(
        f"{hero.name()} was a {hero.traits[0]} kid who liked to solve little puzzles."
    )
    world.say(
        f"At {world.setting.place}, {hero.name()} noticed a {item.label} on the table and a soft {world.setting.soundscape[0]} in the room."
    )
    world.say(
        f"Then came a {random.choice(SURPRISE_WORDS)}: the {item.label} was {('poisonous' if item.poisonous else 'ordinary')}, and it had been {('magnet-ized' if item.magnetized else 'left alone')}."
    )

    # Act 2: conflict
    world.para()
    hero.memes["surprise"] += 1
    hero.memes["conflict"] += 1
    helper.memes["conflict"] += 1
    world.say(
        f"{hero.name()} stepped back. The room had gone very still, except for a tiny {item_def['clue_sound']} from the table."
    )
    world.say(
        f"{helper.name()} frowned and said the {item.label} should not be touched, because poison and magnets made a tricky mix."
    )
    world.say(
        f"{hero.name()} wanted to help, but the worry felt big and prickly."
    )

    # The clue: sound effects reveal movement.
    world.say(
        f"Then, {item_def['clue_sound']}! The sound came again from the tool drawer, as if something metal had been pulled close."
    )

    # Act 3: resolution
    world.para()
    hero.memes["conflict"] = 0.0
    helper.memes["conflict"] = 0.0
    item.meters["distance"] = 0.0
    world.say(
        f"{hero.name()} listened carefully and found the clue: a {ITEMS['spoon']['label']} had stuck to the magnet strip, making the noise."
    )
    world.say(
        f"{helper.name()} moved the poisonous {item.label} into a safe box, far from the magnet."
    )
    world.say(
        f"In the end, the surprise became a solved case, and the room settled down to one last quiet {world.setting.soundscape[-1]}."
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        item=item,
        setting=params.setting,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    item = f["item"]
    return [
        f'Write a short whodunit story for young children about a {item.label} that is magnet-ized and poisonous.',
        f"Tell a mystery where {f['hero'].name()} hears a strange sound effect, notices a surprise, and helps keep the poisonous item safe.",
        f"Write a small detective story with a conflict, a clue sound, and a safe ending at {world.setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    item = f["item"]
    setting = world.setting.place
    return [
        QAItem(
            question=f"Where did the mystery happen?",
            answer=f"It happened at {setting}, where {hero.name()} spotted the strange {item.label}.",
        ),
        QAItem(
            question=f"What made the situation surprising?",
            answer=f"It was surprising because the {item.label} was poisonous and had been magnet-ized, so everyone had to be careful.",
        ),
        QAItem(
            question=f"What sound helped solve the mystery?",
            answer=f"The sound clue was a little {ITEMS[item.id]['clue_sound']}, which led {hero.name()} to the magnet strip.",
        ),
        QAItem(
            question=f"How was the conflict solved?",
            answer=f"{helper.name()} moved the poisonous item into a safe box, and {hero.name()} used the clue to understand what made the noise.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does poisonous mean?",
            answer="Poisonous means something can make people or animals sick if they touch it or eat it, so it must be handled carefully.",
        ),
        QAItem(
            question="What is a magnet used for?",
            answer="A magnet can pull some metal things close to it, which is why it can make keys, spoons, or boxes stick together.",
        ),
        QAItem(
            question="Why are sound effects useful in a mystery?",
            answer="Sound effects can be clues, because a tiny clink, clang, or tap may tell a detective where something moved.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for p in sample.prompts:
        out.append(f"- {p}")
    out.append("")
    out.append("== Story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for ent in world.entities.values():
        if isinstance(ent, Character):
            lines.append(f"{ent.id}: surprise={ent.memes.get('surprise', 0)} conflict={ent.memes.get('conflict', 0)}")
        else:
            lines.append(
                f"{ent.id}: poisonous={ent.poisonous} magnetized={ent.magnetized} distance={ent.meters.get('distance', 0)} danger={ent.meters.get('danger', 0)}"
            )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Story API
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit story world with surprise, conflict, and sound effects.")
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--item", choices=sorted(ITEMS))
    ap.add_argument("--hero")
    ap.add_argument("--helper")
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
    item = args.item or rng.choice(list(ITEMS))
    if not is_reasonable(SETTINGS[setting], item):
        raise StoryError("The chosen setting and item do not make a plausible mystery.")
    hero = args.hero or rng.choice(CHILD_NAMES)
    helper = args.helper or rng.choice(ADULT_NAMES)
    if hero == helper:
        helper = rng.choice([n for n in ADULT_NAMES if n != hero])
    return StoryParams(setting=setting, hero=hero, helper=helper, item=item)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
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
        print(format_qa(sample))


CURATED = [
    StoryParams(setting="workbench", hero="Mina", helper="Ravi", item="spoon"),
    StoryParams(setting="kitchen", hero="Toby", helper="Lena", item="jar"),
    StoryParams(setting="shed", hero="Noor", helper="Jon", item="box"),
]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "mystery")))


def asp_verify() -> int:
    return verify_asp_parity()


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        vals = sorted(set(asp.atoms(model, "mystery")))
        print(f"{len(vals)} mystery-combos:")
        for v in vals:
            print(v)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
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
