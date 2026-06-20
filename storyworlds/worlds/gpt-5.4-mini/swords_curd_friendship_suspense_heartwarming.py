#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/swords_curd_friendship_suspense_heartwarming.py
===============================================================================

A small standalone story world about two friends, toy swords, and a bowl of curd.
The stories are built from simulated state: a playful setup, a suspenseful wobble,
a careful turn, and a warm ending where friendship makes the moment feel safe.

The domain is intentionally tiny:
- two children are playing together
- toy swords are part of the pretend game
- curd is a shared snack that can wobble or spill
- a small scare or near-miss leads to a kinder, safer choice

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/swords_curd_friendship_suspense_heartwarming.py
    python storyworlds/worlds/gpt-5.4-mini/swords_curd_friendship_suspense_heartwarming.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4-mini/swords_curd_friendship_suspense_heartwarming.py --all
    python storyworlds/worlds/gpt-5.4-mini/swords_curd_friendship_suspense_heartwarming.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/swords_curd_friendship_suspense_heartwarming.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)
    delicate: bool = False
    edible: bool = False
    toy_weapon: bool = False

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
    details: str
    supports: set[str] = field(default_factory=set)

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
class Prop:
    id: str
    label: str
    phrase: str
    shine: str
    safe: bool = True
    toy_weapon: bool = False

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
class Snack:
    id: str
    label: str
    phrase: str
    texture: str
    spill_word: str
    delicate: bool = True

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
class Resolution:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str

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
    def __init__(self) -> None:
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
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


def _r_wobble(world: World) -> list[str]:
    out: list[str] = []
    sword = world.get("sword")
    bowl = world.get("curd")
    if sword.meters["swing"] < THRESHOLD:
        return out
    sig = ("wobble",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    bowl.meters["wobble"] += 1
    world.get("table").meters["tension"] += 1
    out.append("__wobble__")
    return out


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    bowl = world.get("curd")
    if bowl.meters["wobble"] < THRESHOLD:
        return out
    sig = ("spill",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if bowl.meters["steady"] < THRESHOLD:
        bowl.meters["spilled"] += 1
        world.get("table").meters["mess"] += 1
        for ent in list(world.entities.values()):
            if ent.kind == "character":
                ent.memes["surprise"] += 1
        out.append("__spill__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("wobble", "physical", _r_wobble),
    Rule("spill", "physical", _r_spill),
]


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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for pid in PROPS:
            for nid in SNACKS:
                if sid in {"picnic", "garden", "kitchen"} and pid == "swords" and nid == "curd":
                    combos.append((sid, pid, nid))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    prop: str
    snack: str
    friend1: str
    friend1_gender: str
    friend2: str
    friend2_gender: str
    helper: str
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


SETTINGS = {
    "picnic": Setting("picnic", "the sunny picnic blanket", "The blanket lay under an apple tree, and the grass was soft.", {"play", "snack"}),
    "garden": Setting("garden", "the little garden", "The garden was bright, with flowers leaning toward the table.", {"play", "snack"}),
    "kitchen": Setting("kitchen", "the cozy kitchen", "The kitchen smelled warm and sweet, and a low table sat near the window.", {"play", "snack"}),
}

PROPS = {
    "swords": Prop("swords", "toy swords", "two toy swords", "shone like tiny silver moons", safe=True, toy_weapon=True),
    "flags": Prop("flags", "paper flags", "bright paper flags", "fluttered in the breeze", safe=True),
}

SNACKS = {
    "curd": Snack("curd", "curd", "a bowl of curd", "soft and creamy", "wobbled", delicate=True),
    "berries": Snack("berries", "berries", "a bowl of berries", "bright and juicy", "tipped", delicate=True),
}

RESOLUTIONS = {
    "steady": Resolution(
        "steady", 2, 2,
        "slid the bowl to the middle of the blanket and set a hand beside it until it was still again",
        "tried to move the bowl, but it tipped and the snack was lost",
        "slid the bowl to the middle and steadied it until it was safe",
    ),
    "pause": Resolution(
        "pause", 3, 3,
        "paused the sword game, took a careful breath, and carried the bowl with two hands to the table",
        "waited too long, and the bowl slipped before anyone could help",
        "paused the game and carried the bowl safely to the table",
    ),
}

GIRL_NAMES = ["Mira", "Lina", "Iris", "Nora", "Asha", "Tala"]
BOY_NAMES = ["Ben", "Omar", "Theo", "Ravi", "Jude", "Noah"]
HELPERS = ["mother", "father", "grandma"]
TRAITS = ["gentle", "cheerful", "careful", "kind"]


KNOWLEDGE = {
    "swords": [("What are toy swords?", "Toy swords are pretend play things. They are for make-believe adventures, not for hurting anyone." )],
    "curd": [("What is curd?", "Curd is a soft, creamy food made from milk. People eat it cold or with other foods." )],
    "spoil": [("Why is spilled food a problem?", "Spilled food can make a mess, waste a snack, and make the floor slippery." )],
    "share": [("What does it mean to share?", "Sharing means letting someone else enjoy part of something with you. It can make friends feel close and happy." )],
    "careful": [("What does careful mean?", "Careful means moving gently and paying attention so nothing gets hurt or broken." )],
}
KNOWLEDGE_ORDER = ["swords", "curd", "spoil", "share", "careful"]


def setting_line(setting: Setting) -> str:
    return f"{setting.details}"


def predict_spill(world: World) -> dict:
    sim = world.copy()
    sim.get("sword").meters["swing"] += 1
    propagate(sim, narrate=False)
    return {
        "spill": sim.get("curd").meters["spilled"] >= THRESHOLD,
        "mess": sim.get("table").meters["mess"],
    }


def intro(world: World, a: Entity, b: Entity, setting: Setting, prop: Prop, snack: Snack) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"{a.id} and {b.id} were best friends, and they had a little game that felt like a brave adventure. "
        f"They were in {setting.place}, where {setting.details.lower()}"
    )
    world.say(
        f"On the table were {prop.phrase} and {snack.phrase}. {prop.shine.capitalize()}, and the {snack.label} smelled soft and fresh."
    )


def start_play(world: World, a: Entity, b: Entity, prop: Prop) -> None:
    a.meters["swing"] += 1
    b.memes["trust"] += 1
    world.say(
        f"{a.id} lifted one of the swords and grinned. {b.id} held the other one and laughed. "
        f'"We are the bravest pair in the whole garden!"'
    )


def suspense(world: World, b: Entity, snack: Snack, helper: Entity) -> None:
    pred = predict_spill(world)
    if pred["spill"]:
        b.memes["worry"] += 1
        world.facts["predicted_mess"] = pred["mess"]
        world.say(
            f"Then {snack.label} began to {snack.spill_word} near the edge of the table. "
            f"{b.id} saw it first and bit {b.pronoun('possessive')} lip."
        )
        world.say(
            f'"Careful," {b.id} whispered. "If it falls, {helper.label_word} will have more work, and our snack will be gone."'
        )


def choose_turn(world: World, a: Entity, b: Entity, snack: Snack, helper: Entity, resolution: Resolution) -> None:
    a.memes["care"] += 1
    b.memes["care"] += 1
    if resolution.id == "steady":
        world.say(
            f"{a.id} stopped the sword game for a second, and {b.id} reached out together with {a.pronoun('object')}. "
            f"They {resolution.text}."
        )
    else:
        world.say(
            f"{a.id} and {b.id} looked at each other, then both nodded. Together they {resolution.text}."
        )


def end_warm(world: World, a: Entity, b: Entity, helper: Entity, snack: Snack, prop: Prop) -> None:
    a.memes["love"] += 1
    b.memes["love"] += 1
    world.say(
        f"{helper.label_word.capitalize()} smiled at the two friends. \"That was kind of you,\" {helper.pronoun()} said. "
        f"\"You kept the {snack.label} safe and kept each other safe too.\""
    )
    world.say(
        f"So {a.id} and {b.id} sat shoulder to shoulder, shared the {snack.label}, and laid the swords across the blanket like sleeping stars."
    )


def tell(setting: Setting, prop: Prop, snack: Snack, helper_type: str,
         friend1: str, friend1_gender: str, friend2: str, friend2_gender: str) -> World:
    world = World()
    a = world.add(Entity(friend1, kind="character", type=friend1_gender, role="friend"))
    b = world.add(Entity(friend2, kind="character", type=friend2_gender, role="friend"))
    helper = world.add(Entity("Helper", kind="character", type=helper_type, role="helper", label=f"the {helper_type}"))
    world.add(Entity("sword", type="thing", label=prop.label, toy_weapon=prop.toy_weapon))
    curd = world.add(Entity("curd", type="thing", label=snack.label, delicate=snack.delicate, edible=True))
    world.add(Entity("table", type="thing", label="the little table"))

    intro(world, a, b, setting, prop, snack)
    world.para()
    start_play(world, a, b, prop)
    suspense(world, b, snack, helper)
    world.para()
    resolution = RESOLUTIONS["pause"] if snack.id == "curd" else RESOLUTIONS["steady"]
    choose_turn(world, a, b, snack, helper, resolution)
    if curd.meters["spilled"] >= THRESHOLD:
        world.say("But the snack was already gone, and the friends felt sad.")
    else:
        end_warm(world, a, b, helper, snack, prop)

    world.facts.update(
        a=a, b=b, helper=helper, setting=setting, prop=prop, snack=snack,
        outcome="safe" if curd.meters["spilled"] < THRESHOLD else "spilled",
        resolved=curd.meters["spilled"] < THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a, b = f["a"], f["b"]
    return [
        f'Write a heartwarming story for a young child that includes the words "swords" and "curd" and features two friends who stay kind to each other.',
        f"Tell a suspenseful but gentle story where {a.id} and {b.id} play with swords near a bowl of curd, notice a small danger, and solve it together.",
        f'Write a short friendship story with a tense little moment around curd and a happy ending where the children share and feel close again.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a, b, helper, snack = f["a"], f["b"], f["helper"], f["snack"]
    qa = [
        ("Who is the story about?", f"It is about {a.id} and {b.id}, two friends who were playing together. Their helper also joined in at the end, so the moment felt safe and warm."),
        ("What were the children playing with?", f"They were playing with {f['prop'].phrase}. The swords made the game feel brave, but the children still had to be careful near the snack."),
        ("Why was there suspense?", f"The {snack.label} began to wobble near the edge, so it looked like it might spill. That tiny danger made the friends stop and pay attention."),
    ]
    if f["resolved"]:
        qa.append(("How did they fix the problem?", f"They moved slowly, steadied the {snack.label}, and chose the safer plan before anything spilled. Because they worked together, the snack stayed ready to share."))
        qa.append(("How did the story end?", f"It ended with the two friends sharing the {snack.label} and resting their swords on the blanket. The ending proves they cared about the food and about each other."))
    else:
        qa.append(("How did the story end?", f"It ended with a spill, which made everyone sad for a moment. Even then, the friends stayed together and learned to be more careful next time."))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {world.facts["prop"].id, world.facts["snack"].id, "share", "careful"}
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
        if e.delicate:
            bits.append("flags=['delicate']")
        if e.toy_weapon:
            bits.append("flags=['toy_weapon']")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("picnic", "swords", "curd", "Mira", "girl", "Jude", "boy", "mother"),
    StoryParams("garden", "swords", "curd", "Theo", "boy", "Nora", "girl", "father"),
    StoryParams("kitchen", "swords", "curd", "Asha", "girl", "Omar", "boy", "grandma"),
]


def explain_rejection(setting: Setting, prop: Prop, snack: Snack) -> str:
    return f"(No story: this world only supports toy swords and curd in a gentle shared-play setting like {setting.place}. Try the default combo.)"


ASP_RULES = r"""
% A tiny declarative twin of the Python reasoner.
% valid story combos are the supported setting/prop/snack triples.
valid(S, P, N) :- setting(S), prop(P), snack(N), supports_play(S), toy_weapon(P), delicate(N).

% The ending is safe when the bowl is steadied before the spill.
safe_end(P) :- resolution(P), power(P, Pow), Pow >= 2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if "play" in s.supports:
            lines.append(asp.fact("supports_play", sid))
    for pid, p in PROPS.items():
        lines.append(asp.fact("prop", pid))
        if p.toy_weapon:
            lines.append(asp.fact("toy_weapon", pid))
    for nid, n in SNACKS.items():
        lines.append(asp.fact("snack", nid))
        if n.delicate:
            lines.append(asp.fact("delicate", nid))
    for rid, r in RESOLUTIONS.items():
        lines.append(asp.fact("resolution", rid))
        lines.append(asp.fact("power", rid, r.power))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world sketch: swords, curd, friendship, suspense, and a heartwarming ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--friend1")
    ap.add_argument("--friend1-gender", choices=["girl", "boy"])
    ap.add_argument("--friend2")
    ap.add_argument("--friend2-gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father", "grandma"])
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


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    options = [n for n in pool if n != avoid]
    return rng.choice(options)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.prop and args.snack:
        if (args.setting, args.prop, args.snack) not in valid_combos():
            raise StoryError(explain_rejection(SETTINGS[args.setting], PROPS[args.prop], SNACKS[args.snack]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.prop is None or c[1] == args.prop)
              and (args.snack is None or c[2] == args.snack)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, prop, snack = rng.choice(sorted(combos))
    g1 = args.friend1_gender or rng.choice(["girl", "boy"])
    g2 = args.friend2_gender or ("boy" if g1 == "girl" and rng.random() < 0.5 else "girl")
    friend1 = args.friend1 or _pick_name(rng, g1)
    friend2 = args.friend2 or _pick_name(rng, g2, avoid=friend1)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(setting, prop, snack, friend1, g1, friend2, g2, helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], PROPS[params.prop], SNACKS[params.snack], params.helper,
                 params.friend1, params.friend1_gender, params.friend2, params.friend2_gender)
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible (setting, prop, snack) combos:")
        for row in asp_valid_combos():
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.friend1} & {p.friend2}: {p.prop} near {p.snack} ({p.setting})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
