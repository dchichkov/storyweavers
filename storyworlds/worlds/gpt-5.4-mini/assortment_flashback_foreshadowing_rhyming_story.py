#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/assortment_flashback_foreshadowing_rhyming_story.py
===================================================================================

A standalone tiny storyworld for an assortment tale with flashback, foreshadowing,
and a light rhyming-story style.

This world models a child who wants to make a colorful assortment for a small
display or gift. A remembered lesson from the past helps them choose the right
items, a foreshadowing beat warns that a tiny problem may grow, and the ending
shows the finished assortment in a concrete, changed state.

The domain is intentionally small:
- a child sorts an assortment of items into a tray or box
- some items are fragile or easily mixed up
- a helper remembers a past lesson
- a foresight beat warns about a likely spill or mix-up
- the child makes a tidy final arrangement

The prose leans lyrical and rhyming, but still follows real world state changes.
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

CHILDREN = ["Mila", "Nina", "Arlo", "Toby", "Lena", "Owen", "Iris", "Eli"]
HELPERS = ["Mom", "Dad", "Grandma", "Grandpa"]
TRAITS = ["careful", "curious", "gentle", "bright", "thoughtful", "patient"]


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

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandma"}
        male = {"boy", "father", "dad", "man", "grandpa"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mom": "mom", "dad": "dad", "grandma": "grandma", "grandpa": "grandpa"}.get(self.type, self.type)



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
    rhyme_word: str
    surface: str
    light: str

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
class Assortment:
    id: str
    label: str
    phrase: str
    items: list[str]
    bright: bool = False
    fragile: bool = False
    tags: set[str] = field(default_factory=set)

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
class Container:
    id: str
    label: str
    phrase: str
    keeps_order: bool
    can_close: bool
    tags: set[str] = field(default_factory=set)

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
class Risk:
    id: str
    label: str
    phrase: str
    bad: str
    cause: str
    spread: int = 1
    messy: bool = True
    tags: set[str] = field(default_factory=set)

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
class Memory:
    id: str
    label: str
    phrase: str
    lesson: str
    tags: set[str] = field(default_factory=set)

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
        clone = World(self.setting)
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
    child = world.get("child")
    if child.meters["rush"] < THRESHOLD:
        return out
    sig = ("spill",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    risk = world.get("risk")
    risk.meters["spilled"] += 1
    child.memes["worry"] += 1
    out.append("__spill__")
    return out


def _r_order(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    tray = world.get("tray")
    if tray.meters["open"] < THRESHOLD:
        return out
    if child.memes["calm"] < THRESHOLD:
        return out
    sig = ("order",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    tray.meters["order"] += 1
    out.append("__order__")
    return out


CAUSAL_RULES = [Rule("spill", "physical", _r_spill), Rule("order", "physical", _r_order)]


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


def risky(risk: Risk, assortment: Assortment, container: Container) -> bool:
    return assortment.fragile and not container.can_close


def sensible_fixes() -> list[str]:
    return [r.id for r in RISKS.values() if r.spread >= SENSE_MIN]


def fix_power(fid: str) -> int:
    return FIXES[fid].power


def fire_like_world(delay: int, spread: int) -> int:
    return delay + spread


def contained(risk: Risk, fix: str, delay: int) -> bool:
    return fix_power(fix) >= fire_like_world(delay, risk.spread)


def predict(world: World, delay: int) -> dict:
    sim = world.copy()
    sim.get("child").meters["rush"] += 1
    _r_spill(sim)
    return {"spilled": sim.get("risk").meters["spilled"] >= THRESHOLD}


def start(world: World, child: Entity, helper: Entity, assortment: Assortment, container: Container, setting: Setting) -> None:
    child.memes["joy"] += 1
    world.say(
        f"On a bright day by {setting.place}, {child.id} gathered an assortment "
        f"so neat and light, a rainbow row to make things right. "
        f"{assortment.phrase} rested near {container.phrase}, sweet as a song, "
        f"small and bright."
    )
    world.say(
        f"{child.id} smiled and hummed, \"This little mix will shine and sing; "
        f"a tidy tray is such a nice thing.\""
    )


def flashback(world: World, helper: Entity, memory: Memory) -> None:
    helper.memes["remember"] += 1
    world.say(
        f"Then {helper.id} paused and gave a grin, remembering a day long gone. "
        f"{memory.phrase} had tipped and tumbled in, but {helper.id} had learned "
        f"{memory.lesson} before too long."
    )


def foreshadow(world: World, risk: Risk, setting: Setting) -> None:
    world.say(
        f"But the breeze began to nibble and tease, and a tiny wobble wiggled "
        f"free. {risk.phrase} looked ready to slip like seas, as if trouble might "
        f"grow beneath the tree."
    )
    world.facts["foreshadowed"] = risk.label


def caution(world: World, helper: Entity, child: Entity, risk: Risk, container: Container, assortment: Assortment) -> None:
    pred = predict(world, 1)
    world.facts["predicted_spill"] = pred["spilled"]
    world.say(
        f'"{child.id}, keep it snug," {helper.id} softly said. "{risk.bad}. '
        f"If we leave it loose, the mix may slide from bed."
    )


def act_open(world: World, child: Entity, container: Container) -> None:
    child.meters["rush"] += 1
    container.meters["open"] += 1
    world.say(f"{child.id} reached to run, but slowed instead, and opened the tray with careful tread.")


def resolve(world: World, helper: Entity, child: Entity, assortment: Assortment, container: Container, memory: Memory) -> None:
    child.memes["calm"] += 1
    container.meters["order"] += 1
    world.say(
        f"Together they tucked each piece in place, from red to blue to gold. "
        f"{memory.lesson} stayed in mind, a little hand to hold."
    )


def ending(world: World, child: Entity, container: Container, assortment: Assortment, setting: Setting) -> None:
    world.say(
        f"Now the assortment sat all snug and true, a shining row in morning dew. "
        f"{child.id} laughed, \"So small a fix, so grand a view -- a tidy little "
        f"mix came through!\""
    )
    world.say(
        f"And by {setting.place}, the day felt bright; the tray was closed, the colors right."
    )


def tell(setting: Setting, assortment: Assortment, container: Container, risk: Risk, memory: Memory,
         child_name: str = "Mila", child_gender: str = "girl", helper_name: str = "Grandma",
         helper_gender: str = "grandma", trait: str = "careful") -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child", traits=[trait]))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    tray = world.add(Entity(id="tray", type="container", label=container.label))
    risk_ent = world.add(Entity(id="risk", type="risk", label=risk.label))

    start(world, child, helper, assortment, container, setting)
    world.para()
    flashback(world, helper, memory)
    foreshadow(world, risk, setting)
    caution(world, helper, child, risk, container, assortment)
    act_open(world, child, container)
    world.para()
    resolve(world, helper, child, assortment, container, memory)
    ending(world, child, container, assortment, setting)

    world.facts.update(child=child, helper=helper, tray=tray, risk=risk_ent, assortment=assortment,
                       container=container, memory=memory, setting=setting, outcome="tidy")
    return world


SETTINGS = {
    "sunroom": Setting("sunroom", "the sunroom", "chime", "table", "sunlight"),
    "porch": Setting("porch", "the porch", "rhyme", "bench", "daylight"),
    "kitchen": Setting("kitchen", "the kitchen", "glow", "counter", "lamplight"),
}

ASSORTMENTS = {
    "buttons": Assortment("buttons", "button assortment", "an assortment of buttons",
                          ["red", "blue", "yellow", "green"], tags={"assortment", "buttons"}),
    "shells": Assortment("shells", "shell assortment", "an assortment of shells",
                         ["white", "pink", "tan", "gold"], bright=True, tags={"assortment", "shells"}),
    "berries": Assortment("berries", "berry assortment", "an assortment of berries",
                          ["berry"], fragile=True, tags={"assortment", "berries"}),
}

CONTAINERS = {
    "tray": Container("tray", "tray", "a shallow tray", keeps_order=True, can_close=True, tags={"tray"}),
    "basket": Container("basket", "basket", "a wicker basket", keeps_order=True, can_close=False, tags={"basket"}),
    "box": Container("box", "box", "a little box", keeps_order=True, can_close=True, tags={"box"}),
}

RISKS = {
    "breeze": Risk("breeze", "breeze", "the breeze", "the assortment might slide apart", "keep it snug", spread=2, tags={"breeze"}),
    "jostle": Risk("jostle", "jostle", "a bump", "the pieces could scatter", "hold it steady", spread=1, tags={"jostle"}),
    "spill": Risk("spill", "spill", "a spill", "the whole mix could tumble", "close the lid", spread=3, tags={"spill"}),
}

MEMORIES = {
    "lesson": Memory("lesson", "lesson", "A long-ago tray had tipped in the rain.", "keep things snug and close", tags={"flashback"}),
}

FIXES = {
    "tray_lid": type("Fix", (), {"id": "tray_lid", "label": "close the tray lid", "power": 4})(),
    "basket_cover": type("Fix", (), {"id": "basket_cover", "label": "cover the basket with a cloth", "power": 2})(),
    "steady_hands": type("Fix", (), {"id": "steady_hands", "label": "hold it with two steady hands", "power": 3})(),
}

# Include the seed word explicitly in registries for QA.
WORDS = ["assortment"]



@dataclass
class StoryParams:
    setting: str
    assortment: str
    container: str
    risk: str
    memory: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    trait: str
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
    ("sunroom", "buttons", "tray", "breeze", "lesson", "Mila", "girl", "Grandma", "grandma", "careful"),
    ("porch", "shells", "box", "jostle", "lesson", "Owen", "boy", "Grandpa", "grandpa", "thoughtful"),
    ("kitchen", "berries", "tray", "spill", "lesson", "Iris", "girl", "Mom", "mom", "patient"),
]



def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid, s in SETTINGS.items():
        for aid, a in ASSORTMENTS.items():
            for cid, c in CONTAINERS.items():
                for rid, r in RISKS.items():
                    if risky(r, a, c):
                        combos.append((sid, aid, cid, rid))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a rhyming story for a little child that uses the word "assortment" and includes a flashback.',
        f"Tell a gentle story where {f['child'].id} makes an assortment, remembers an old lesson, and notices a warning before a problem grows.",
        f'Write a lyrical story with foreshadowing where a child keeps an assortment safe by choosing the right container.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, helper, assortment, container, risk, memory = f["child"], f["helper"], f["assortment"], f["container"], f["risk"], f["memory"]
    qa = [
        ("What was the child making?",
         f"{child.id} was making {assortment.phrase}, a small colorful set of pieces put together with care."),
        ("Who remembered the old lesson?",
         f"{helper.id} remembered the old lesson from {memory.phrase}. That flashback helped the child stay careful."),
        ("What problem was foreshadowed?",
         f"The story foreshadowed {risk.phrase}. That warning mattered because loose pieces can slide or scatter."),
        ("How did the child finish the task?",
         f"{child.id} kept the assortment safe in {container.phrase} and ended with everything neat and shining.")
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is an assortment?",
         "An assortment is a mixed group of different things gathered together. People make assortments to sort, show, or share items they like."),
        ("What is a flashback in a story?",
         "A flashback is when a story briefly remembers something that happened earlier. It helps explain why a character acts a certain way now."),
        ("What is foreshadowing?",
         "Foreshadowing is a clue that hints something may happen later. It helps readers notice danger, trouble, or an important change before it arrives."),
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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
risky(A, C) :- fragile(A), open_container(C).
valid(S, A, C, R) :- setting(S), assortment(A), container(C), risk(R), risky(R, A, C).
flashback_needed(M) :- memory(M).
foreshadow_needed(R) :- risk(R).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for aid, a in ASSORTMENTS.items():
        lines.append(asp.fact("assortment", aid))
        if a.fragile:
            lines.append(asp.fact("fragile", aid))
    for cid, c in CONTAINERS.items():
        lines.append(asp.fact("container", cid))
        if not c.can_close:
            lines.append(asp.fact("open_container", cid))
    for rid in RISKS:
        lines.append(asp.fact("risk", rid))
    for mid in MEMORIES:
        lines.append(asp.fact("memory", mid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in gate.")
        rc = 1
    # smoke test
    sample = generate(CURATED[0] and StoryParams(*CURATED[0]))
    if not sample.story.strip():
        print("MISMATCH: empty story from smoke test.")
        rc = 1
    else:
        print("OK: generate() smoke test produced story text.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world sketch: assortment, flashback, foreshadowing, and rhyme.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--assortment", choices=ASSORTMENTS)
    ap.add_argument("--container", choices=CONTAINERS)
    ap.add_argument("--risk", choices=RISKS)
    ap.add_argument("--memory", choices=MEMORIES)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["mom", "dad", "grandma", "grandpa"])
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.assortment is None or c[1] == args.assortment)
              and (args.container is None or c[2] == args.container)
              and (args.risk is None or c[3] == args.risk)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, assortment, container, risk = rng.choice(sorted(combos))
    memory = args.memory or "lesson"
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(CHILDREN)
    helper_gender = args.helper_gender or rng.choice(["mom", "dad", "grandma", "grandpa"])
    helper = args.helper or rng.choice(HELPERS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting, assortment, container, risk, memory, child, child_gender, helper, helper_gender, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], ASSORTMENTS[params.assortment], CONTAINERS[params.container], RISKS[params.risk], MEMORIES[params.memory],
                 params.child, params.child_gender, params.helper, params.helper_gender, params.trait)
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
        print(asp_program("", "#show valid/4."))
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
        samples = [generate(StoryParams(*c, "lesson", "Mila", "girl", "Grandma", "grandma", "careful")) for c in CURATED]
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
