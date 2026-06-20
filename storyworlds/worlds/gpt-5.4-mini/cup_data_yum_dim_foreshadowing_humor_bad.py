#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/cup_data_yum_dim_foreshadowing_humor_bad.py
=============================================================================

A small folk-tale style story world about a curious child, a cup, a bit of
data, and a dim warning that turns out to matter.  The world supports a single
tiny domain: a village errand, a mysterious cup, a helpful-looking "data" slip,
a funny foreshadowing beat, and a bad ending where the trouble grows too big.

The story stays close to folk tale style:
- simple village setting
- a clear wish and warning
- a comic misunderstanding
- a foreshadowed danger
- a bad ending that still feels complete

This script is standalone and stdlib-only.
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
        if self.type in {"girl", "woman", "mother", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "grandfather"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id



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
    mood: str
    sign: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Cup:
    id: str
    label: str
    phrase: str
    material: str
    holds: str
    fragile: bool = True

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class DataSlip:
    id: str
    label: str
    phrase: str
    oddity: str
    foreshadows: str
    humor: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class YumDim:
    id: str
    label: str
    phrase: str
    aroma: str
    warmth: str
    spills: bool = True

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Warning:
    id: str
    text: str
    seriousness: int
    sense: int

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
    out: list[str] = []
    cup = world.get("cup")
    stew = world.get("yumdim")
    if cup.meters["broken"] < THRESHOLD:
        return out
    sig = ("spill",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    stew.meters["spilled"] += 1
    stew.meters["wasted"] += 1
    world.get("village").meters["trouble"] += 1
    out.append("__spill__")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.meters["fear"] < THRESHOLD:
        return out
    sig = ("worry",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("grandmother").memes["worry"] += 1
    out.append("__worry__")
    return out


CAUSAL_RULES = [Rule("spill", _r_spill), Rule("worry", _r_worry)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            got = rule.apply(world)
            if got:
                changed = True
                produced.extend(x for x in got if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_break(world: World) -> dict:
    sim = world.copy()
    break_cup(sim, narrate=False)
    return {
        "broken": sim.get("cup").meters["broken"] >= THRESHOLD,
        "trouble": sim.get("village").meters["trouble"],
    }


def break_cup(world: World, narrate: bool = True) -> None:
    world.get("cup").meters["broken"] += 1
    propagate(world, narrate=narrate)


def setup(world: World, setting: Setting, child: Entity, grandmother: Entity, cup: Cup, data: DataSlip, yumdim: YumDim) -> None:
    world.say(
        f"In the old village of {setting.place}, where the {setting.sign} leaned "
        f"like a sleepy crow, {child.id} lived with {grandmother.id}. "
        f"The days were plain, but the tales were never quite plain."
    )
    world.say(
        f"One morning, {grandmother.id} set out {cup.phrase}, {data.phrase}, and "
        f"{yumdim.phrase} on the table."
    )
    child.memes["curiosity"] += 1
    child.memes["joy"] += 1


def foreshadow(world: World, child: Entity, data: DataSlip, cup: Cup, yumdim: YumDim, warning: Warning) -> None:
    child.memes["attention"] += 1
    world.say(
        f"{child.id} peered at {data.label} and laughed. '{data.humor}'"
    )
    world.say(
        f"But the {data.label} had a strange mark on it: {data.foreshadows}. "
        f"Even the {cup.label} seemed to wait and listen."
    )
    world.say(
        f"{grandmother_name(world).capitalize()} gave a small warning: "
        f"'{warning.text}'"
    )


def grandmother_name(world: World) -> str:
    return world.get("grandmother").id


def mishap(world: World, child: Entity, cup: Cup, yumdim: YumDim) -> None:
    child.memes["defiance"] += 1
    world.say(
        f"But {child.id} thought the cup was only a cup, and the data only a joke. "
        f"So {child.id} reached for the cup, hoping to sip the {yumdim.label} first."
    )
    world.say(
        f"The {cup.label} gave a tiny crack, the sort of crack that sounds small "
        f"only when it is too late."
    )
    break_cup(world)


def ending_bad(world: World, child: Entity, grandmother: Entity, cup: Cup, yumdim: YumDim, warning: Warning) -> None:
    child.memes["fear"] += 2
    grandmother.memes["worry"] += 2
    world.say(
        f"At once, the {cup.label} split open. The {yumdim.label} slid across the floor "
        f"like a brown river, and the bright little {data_label(world)} went soggy in the mess."
    )
    world.say(
        f"{grandmother.id} hurried to save what she could, but the spill had already "
        f"reached the rug. 'I said the cup was fragile,' {grandmother.pronoun()} sighed."
    )
    world.say(
        f"{child.id} looked down at the ruined lunch and felt the joke turn heavy. "
        f"The village cats licked one drop, then sneezed, as if even they knew the tale had gone dim."
    )
    world.say(
        f"After that, nobody in the house forgot the warning: {warning.text}"
    )


def data_label(world: World) -> str:
    return world.get("data").label


def tell(setting: Setting, cup: Cup, data: DataSlip, yumdim: YumDim, warning: Warning,
         child_name: str = "Milo", child_type: str = "boy",
         grandmother_name_: str = "Grandmother", grandmother_type: str = "woman") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child"))
    grandmother = world.add(Entity(id=grandmother_name_, kind="character", type=grandmother_type, role="elder"))
    world.add(Entity(id="village", kind="place", type="place", label=setting.place))
    world.add(Entity(id="cup", label=cup.label))
    world.add(Entity(id="data", label=data.label))
    world.add(Entity(id="yumdim", label=yumdim.label))

    setup(world, setting, child, grandmother, cup, data, yumdim)
    world.para()
    foreshadow(world, child, data, cup, yumdim, warning)
    world.para()
    mishap(world, child, cup, yumdim)
    world.para()
    ending_bad(world, child, grandmother, cup, yumdim, warning)

    world.facts.update(
        child=child, grandmother=grandmother, setting=setting, cup=cup, data=data,
        yumdim=yumdim, warning=warning, outcome="bad", broken=True, spilled=True
    )
    return world


SETTINGS = {
    "hill_village": Setting("hill_village", "Hollow Hill", "soft and windy", "old gate"),
    "river_village": Setting("river_village", "River Bend", "bright and damp", "green bridge"),
    "orchard_village": Setting("orchard_village", "Apple Orchard", "warm and sleepy", "leaning barn"),
}

CUPS = {
    "wooden": Cup("wooden", "wooden cup", "a wooden cup with a tiny chip", "wood", "porridge"),
    "blue": Cup("blue", "blue cup", "a blue cup with a painted bird", "clay", "tea"),
    "tin": Cup("tin", "tin cup", "a tin cup that rang like a bell", "tin", "water"),
}

DATA = {
    "note": DataSlip("note", "data slip", "a folded data slip", "a crooked list of numbers", "one corner was stained with a thumbprint", "It looked official enough to be funny"),
    "ledger": DataSlip("ledger", "data page", "a data page from an old ledger", "three lines of neat marks", "the last line had a hole right through it", "It was so serious it nearly winked"),
    "receipt": DataSlip("receipt", "data receipt", "a data receipt tied with string", "a bright stamp", "the stamp was upside down", "It announced important business with a squeak"),
}

YUMDIMS = {
    "soup": YumDim("soup", "yum-dim", "a bowl of yum-dim soup", "sweet steam", "warm as a bedtime song"),
    "stew": YumDim("stew", "yum-dim", "a pot of yum-dim stew", "pepper and onion", "thick and kindly"),
    "broth": YumDim("broth", "yum-dim", "a cup of yum-dim broth", "herbs and smoke", "thin but fragrant"),
}

WARNINGS = {
    "careful": Warning("careful", "A cup can break when it is hurried.", 3, 3),
    "spilled": Warning("spilled", "What starts as a joke can end as a mess.", 4, 3),
    "listen": Warning("listen", "When the old ones warn you, listen well.", 5, 4),
}



@dataclass
class StoryParams:
    setting: str
    cup: str
    data: str
    yumdim: str
    warning: str
    child_name: str
    child_type: str
    elder_name: str
    elder_type: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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

CURATED = [
    StoryParams("hill_village", "wooden", "note", "soup", "careful", "Milo", "boy", "Grandmother", "woman", seed=1),
    StoryParams("river_village", "blue", "ledger", "stew", "spilled", "Tessa", "girl", "Grandmother", "woman", seed=2),
    StoryParams("orchard_village", "tin", "receipt", "broth", "listen", "Jon", "boy", "Grandmother", "woman", seed=3),
]



def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for c in CUPS:
            for d in DATA:
                combos.append((s, c, d))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk tale story world with a cup, data, yum-dim, foreshadowing, humor, and a bad ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--cup", choices=CUPS)
    ap.add_argument("--data", choices=DATA)
    ap.add_argument("--yumdim", choices=YUMDIMS)
    ap.add_argument("--warning", choices=WARNINGS)
    ap.add_argument("--child")
    ap.add_argument("--adult")
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
    combo = [c for c in valid_combos()
             if (args.setting is None or c[0] == args.setting)
             and (args.cup is None or c[1] == args.cup)
             and (args.data is None or c[2] == args.data)]
    if not combo:
        raise StoryError("(No valid combination matches the given options.)")
    setting, cup, data = rng.choice(sorted(combo))
    yumdim = args.yumdim or rng.choice(sorted(YUMDIMS))
    warning = args.warning or rng.choice(sorted(WARNINGS))
    child_name = args.child or rng.choice(["Milo", "Tessa", "Jon", "Lina", "Pip"])
    child_type = "girl" if child_name in {"Tessa", "Lina"} else "boy"
    adult = args.adult or "Grandmother"
    return StoryParams(setting, cup, data, yumdim, warning, child_name, child_type, adult, "woman")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a folk tale for a child that includes the words "cup", "data", and "yum-dim".',
        f"Tell a short story where {f['child'].id} laughs at a strange piece of data, but an old warning about the cup turns out to matter later.",
        f"Write a story with foreshadowing and a bad ending in a simple village style, where a {f['cup'].label} and yum-dim are both important.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    elder = f["grandmother"]
    cup = f["cup"]
    data = f["data"]
    yumdim = f["yumdim"]
    warning = f["warning"]
    return [
        QAItem(
            question="Who was the story about?",
            answer=f"It was about {child.id} and {elder.id} in a small village. The tale followed their day from the first meal to the last spill."
        ),
        QAItem(
            question="Why was the data funny?",
            answer=f"The data looked serious, but it had a crooked little mark and an upside-down feel to it. That made {child.id} laugh, even though the mark was also a warning sign."
        ),
        QAItem(
            question=f"What did the warning say about the {cup.label}?",
            answer=f"It said, '{warning.text}' That mattered because the cup was fragile and could crack if someone grabbed it too fast."
        ),
        QAItem(
            question="What caused the bad ending?",
            answer=f"{child.id} reached for the cup, the cup broke, and the yum-dim spilled across the floor. The broken cup turned the meal into a mess that nobody could easily fix."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cup used for?",
            answer="A cup is used for holding a drink or other liquid so people can carry it without spilling."
        ),
        QAItem(
            question="What is data?",
            answer="Data is information. It can be numbers, marks, or notes that help people keep track of things."
        ),
        QAItem(
            question="What is yum-dim in this story?",
            answer="Yum-dim is the warm food or drink the family planned to enjoy. It is a tasty thing that can make a good meal."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
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
        lines.append(f"  {e.id}: {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, C, D) :- setting(S), cup(C), data(D).
broken(C) :- chosen_cup(C), fragile(C).
spill :- broken(_).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for c in CUPS.values():
        lines.append(asp.fact("cup", c.id))
        if c.fragile:
            lines.append(asp.fact("fragile", c.id))
    for d in DATA.values():
        lines.append(asp.fact("data", d.id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos")
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate() smoke test succeeded.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"MISMATCH: generation smoke test failed: {exc}")
    return rc


def tell_world(params: StoryParams) -> World:
    world = World()
    setting = SETTINGS[params.setting]
    cup = CUPS[params.cup]
    data = DATA[params.data]
    yumdim = YUMDIMS[params.yumdim]
    warning = WARNINGS[params.warning]
    world.add(Entity(id="village", kind="place", type="place", label=setting.place))
    world.add(Entity(id="child", kind="character", type=params.child_type))
    world.add(Entity(id="grandmother", kind="character", type=params.elder_type))
    world.add(Entity(id="cup", label=cup.label))
    world.add(Entity(id="data", label=data.label))
    world.add(Entity(id="yumdim", label=yumdim.label))
    world.facts.update(setting=setting, cup=cup, data=data, yumdim=yumdim, warning=warning)
    return tell(setting, cup, data, yumdim, warning, params.child_name, params.child_type, params.elder_name, params.elder_type)


def tell(setting: Setting, cup: Cup, data: DataSlip, yumdim: YumDim, warning: Warning,
         child_name: str, child_type: str, elder_name: str, elder_type: str) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child"))
    grandmother = world.add(Entity(id=elder_name, kind="character", type=elder_type, role="elder"))
    world.add(Entity(id="village", kind="place", type="place", label=setting.place))
    world.add(Entity(id="cup", label=cup.label))
    world.add(Entity(id="data", label=data.label))
    world.add(Entity(id="yumdim", label=yumdim.label))
    world.say(f"In {setting.place}, where the {setting.sign} leaned in the wind, {child.id} lived with {grandmother.id}.")
    world.say(f"One morning, {grandmother.id} set out {cup.phrase}, {data.phrase}, and {yumdim.phrase}.")
    world.para()
    world.say(f"{child.id} laughed at the {data.label} because {data.humor}.")
    world.say(f"Yet the note said {data.foreshadows}, and even the {cup.label} seemed to wait.")
    world.say(f"'{warning.text}' {grandmother.id} warned.")
    world.para()
    world.say(f"But {child.id} wanted to be clever and lift the cup before anyone could stop {child.pronoun()}.")
    break_cup(world)
    world.para()
    world.say(f"The {cup.label} split, the {yumdim.label} spilled, and the neat meal became a sticky mess.")
    world.say(f"{grandmother.id} sighed, and the village cats sneezed at the steam.")
    world.say(f"So the tale ended badly, with the warning proved true and the lunch lost.")
    world.facts.update(child=child, grandmother=grandmother, cup=cup, data=data, yumdim=yumdim, warning=warning)
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], CUPS[params.cup], DATA[params.data], YUMDIMS[params.yumdim], WARNINGS[params.warning], params.child_name, params.child_type, params.elder_name, params.elder_type)
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
