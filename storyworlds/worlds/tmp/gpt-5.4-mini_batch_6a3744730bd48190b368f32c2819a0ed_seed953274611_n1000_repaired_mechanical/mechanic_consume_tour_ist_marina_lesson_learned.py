#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/mechanic_consume_tour_ist_marina_lesson_learned.py
===================================================================================

A small, self-contained storyworld set at a marina, in a folk-tale tone, built
from the seed words mechanic / consume / tour-ist and the narrative features
lesson learned, transformation, and reconciliation.

Domain premise
--------------
A curious tourist comes to the marina with a sweet snack and an urge to consume
it right beside a working boat. The snack attracts gulls, the dock gets messy,
and a patient mechanic must stop the trouble before it spreads. The tourist then
changes from clumsy visitor to helpful dock hand, learns the harbor rule, and
makes peace with the mechanic by helping repair what was spoiled.

This script follows the Storyweavers contract:
- stdlib-only
- imports storyworlds/results.py eagerly
- imports storyworlds/asp.py lazily inside ASP helpers
- defines StoryParams, registries, build_parser, resolve_params, generate, emit,
  and main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)
    edible: bool = False
    messy: bool = False
    tool: bool = False
    repairable: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom"}
        male = {"boy", "man", "father", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class StoryParams:
    marina: str
    snack: str
    tool: str
    tourist: str
    tourist_gender: str
    mechanic: str
    mechanic_gender: str
    elder: str
    elder_gender: str
    lesson: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Marina:
    id: str
    label: str
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    facts: dict = field(default_factory=dict)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Snack:
    id: str
    label: str
    phrase: str
    crumbs: str
    smell: str
    edible: bool = True
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    use: str
    repair: str
    tool: bool = True
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Lesson:
    id: str
    text: str
    change: str
    reconciliation: str
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


class World:
    def __init__(self, marina: Marina) -> None:
        self.marina = marina
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
        w = World(self.marina)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


class Rule:
    def __init__(self, name: str, apply: Callable[[World], list[str]]) -> None:
        self.name = name
        self.apply = apply


def _r_seagulls(world: World) -> list[str]:
    out = []
    tourist = world.get("tourist")
    snack = world.get("snack")
    if tourist.meters["eating"] < THRESHOLD or snack.meters["opened"] < THRESHOLD:
        return out
    sig = ("gulls",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.marina.meters["commotion"] += 1
    tourist.memes["alarm"] += 1
    world.get("dock").meters["mess"] += 1
    out.append("__gulls__")
    return out


def _r_spill(world: World) -> list[str]:
    out = []
    if world.marina.meters["commotion"] < THRESHOLD:
        return out
    sig = ("spill",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("dock").meters["sticky"] += 1
    world.get("mechanic").memes["annoyance"] += 1
    return ["The sweet crumbs drew gulls, and the dock turned sticky with trouble."]


def _r_help(world: World) -> list[str]:
    out = []
    tourist = world.get("tourist")
    mechanic = world.get("mechanic")
    if tourist.memes["shame"] < THRESHOLD or mechanic.memes["kindness"] < THRESHOLD:
        return out
    sig = ("help",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    tourist.memes["helpful"] += 1
    mechanic.memes["trust"] += 1
    out.append("help")
    return out


CAUSAL_RULES = [Rule("seagulls", _r_seagulls), Rule("spill", _r_spill), Rule("help", _r_help)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


def choose_reasonable_combo(snack: Snack, tool: Tool) -> bool:
    return snack.edible and tool.tool


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for marina in MARINAS:
        for snack_id, snack in SNACKS.items():
            for tool_id, tool in TOOLS.items():
                if choose_reasonable_combo(snack, tool):
                    combos.append((marina, snack_id, tool_id))
    return combos


def _do_consume(world: World, narrate: bool = True) -> None:
    tourist = world.get("tourist")
    snack = world.get("snack")
    snack.meters["opened"] += 1
    tourist.meters["eating"] += 1
    tourist.memes["desire"] += 1
    propagate(world, narrate=narrate)


def warn(world: World, elder: Entity, tourist: Entity, snack: Snack, marina: Marina) -> None:
    world.say(
        f'{elder.id} raised a hand. "{tourist.id}, do not consume {snack.label} '
        f'beside the boats. The gulls at {marina.label} have sharp eyes."'
    )


def act(world: World, tourist: Entity, snack: Snack) -> None:
    tourist.memes["boldness"] += 1
    world.say(
        f"{tourist.id} opened the {snack.label} anyway, and {tourist.pronoun()} "
        f"began to consume it in the bright wind."
    )


def trouble(world: World, tourist: Entity) -> None:
    _do_consume(world)
    world.say("At once the gulls cried overhead and swept low across the dock.")


def repair(world: World, mechanic: Entity, tool: Tool) -> None:
    world.get("dock").meters["sticky"] = 0.0
    world.marina.meters["commotion"] = 0.0
    mechanic.memes["kindness"] += 1
    world.say(
        f'{mechanic.label_word.capitalize()} came with {tool.phrase} and used it '
        f'to {tool.repair}. The dock grew quiet again.'
    )


def lesson_and_change(world: World, lesson: Lesson, tourist: Entity, mechanic: Entity) -> None:
    tourist.memes["shame"] += 1
    tourist.memes["lesson"] += 1
    tourist.memes["helpful"] += 1
    tourist.memes["transform"] += 1
    world.say(
        f'{tourist.id} lowered {tourist.pronoun("possessive")} head. "{lesson.text}"'
    )
    world.say(
        f"{tourist.id} changed after that: {tourist.pronoun()} tucked the crumbs "
        f"away, fetched water, and helped {mechanic.id} clean the boards."
    )
    world.say(
        f"The visitor was no longer a careless {tourist.role}; {tourist.id} had "
        f"become a dock helper."
    )


def reconcile(world: World, tourist: Entity, mechanic: Entity, elder: Entity, lesson: Lesson) -> None:
    tourist.memes["love"] += 1
    mechanic.memes["trust"] += 1
    world.say(
        f'{mechanic.label_word.capitalize()} looked at {tourist.id} and nodded. '
        f'"We can begin again," {mechanic.pronoun()} said.'
    )
    world.say(
        f'{tourist.id} bowed and answered, "{lesson.reconciliation}"'
    )
    world.say(
        f'Then {elder.id} smiled, because the lesson had become a bridge between them.'
    )


def tell(marina: Marina, snack: Snack, tool: Tool, tourist_name: str, tourist_gender: str,
         mechanic_name: str, mechanic_gender: str, elder_name: str, elder_gender: str,
         lesson: Lesson) -> World:
    world = World(marina)
    tourist = world.add(Entity(id=tourist_name, kind="character", type=tourist_gender, role="tourist"))
    mechanic = world.add(Entity(id=mechanic_name, kind="character", type=mechanic_gender, role="mechanic"))
    elder = world.add(Entity(id=elder_name, kind="character", type=elder_gender, role="elder"))
    dock = world.add(Entity(id="dock", label="dock", meters=defaultdict(float), memes=defaultdict(float)))
    snack_ent = world.add(Entity(id="snack", label=snack.label, kind="thing", edible=True))
    tool_ent = world.add(Entity(id="tool", label=tool.label, kind="thing", tool=True))
    world.facts.update(tourist=tourist, mechanic=mechanic, elder=elder, snack=snack, tool=tool, lesson=lesson)

    world.say(
        f"At {marina.label}, {tourist.id} came as a small tour-ist with bright eyes "
        f"and a sweet snack in hand."
    )
    world.say(
        f"{mechanic.id} the mechanic kept watch over the boats and their engines, "
        f"while {elder.id} swept the boards and greeted the morning."
    )
    world.say(
        f"{tourist.id} wanted to consume {snack.phrase} beside the water, "
        f"because the breeze smelled like salt and adventure."
    )

    world.para()
    warn(world, elder, tourist, snack, marina)
    act(world, tourist, snack)
    trouble(world, tourist)

    world.para()
    repair(world, mechanic, tool)
    lesson_and_change(world, lesson, tourist, mechanic)
    reconcile(world, tourist, mechanic, elder, lesson)
    world.say(
        f"After that, {tourist.id} ate only at the bench, and the marina stayed "
        f"clean, calm, and kind."
    )

    world.facts.update(
        dock=dock,
        outcome="reconciled",
        transformed=True,
        lessoned=True,
    )
    return world


MARINAS = {
    "harbor": Marina(id="harbor", label="the harbor"),
    "sunwharf": Marina(id="sunwharf", label="Sun Wharf"),
    "shellbay": Marina(id="shellbay", label="Shell Bay"),
}

SNACKS = {
    "apple": Snack(id="apple", label="apple tart", phrase="an apple tart", crumbs="crumbs", smell="sweet"),
    "bun": Snack(id="bun", label="sweet bun", phrase="a sweet bun", crumbs="crumbs", smell="warm"),
    "pear": Snack(id="pear", label="pear pastry", phrase="a pear pastry", crumbs="crumbs", smell="fruity"),
}

TOOLS = {
    "brush": Tool(id="brush", label="long scrub brush", phrase="a long scrub brush", use="scrub", repair="scrub the sticky boards clean"),
    "cloth": Tool(id="cloth", label="oilcloth", phrase="an oilcloth", use="cover", repair="cover the spill and lift it away"),
    "pump": Tool(id="pump", label="hand pump", phrase="a hand pump", use="wash", repair="wash the dock clean"),
}

LESSONS = {
    "harbor_rule": Lesson(id="harbor_rule", text="I see now that a snack belongs at the bench, not by the gulls.", change="dock helper", reconciliation="I will keep my crumbs away from the boats."),
}

TOURIST_NAMES = ["Mira", "Tavi", "Niko", "Lina", "Oren", "Sera", "Pavo", "Iris"]
MECHANIC_NAMES = ["Bram", "Jory", "Mina", "Hale", "Kara", "Dov"]
ELDER_NAMES = ["Nana", "Uncle Reed", "Aunt Sela", "Old Finn"]
TRAITS = ["curious", "bright", "reckless", "gentle", "thoughtful"]


@dataclass
class StoryParams:
    marina: str
    snack: str
    tool: str
    tourist: str
    tourist_gender: str
    mechanic: str
    mechanic_gender: str
    elder: str
    elder_gender: str
    lesson: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a folk-tale style story set at {f["marina"].label} that includes the words '
        f'"mechanic", "consume", and "tour-ist".',
        f"Tell a marina story where {f['tourist'].id} wants to consume a snack near the boats, "
        f"but {f['mechanic'].id} helps turn the mistake into a lesson learned.",
        f"Write a child-facing story of transformation and reconciliation at the marina, with a mechanic, "
        f"a tourist, and a calm ending.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tourist, mechanic, elder, snack = f["tourist"], f["mechanic"], f["elder"], f["snack"]
    lesson: Lesson = f["lesson"]
    return [
        ("Who is the story about?",
         f"It is about {tourist.id}, a {tourist.role}, and {mechanic.id}, the mechanic at the marina. {elder.id} is there too, watching over the dock."),
        ("Why did trouble begin?",
         f"{tourist.id} tried to consume {snack.phrase} beside the boats, and the crumbs drew gulls down to the dock. The busy wings made the place messy and worried everyone."),
        ("How did the tourist change?",
         f"After the warning, {tourist.id} became more helpful and careful. {tourist.id} fetched water, cleaned the boards, and changed from a careless visitor into a dock helper."),
        ("How did they make peace again?",
         f"{mechanic.id} used the scrub brush to clean the dock, and then {tourist.id} apologized. When {tourist.id} said, \"{lesson.reconciliation}\", they both smiled and the marina felt friendly again."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a mechanic?",
         "A mechanic is a person who fixes machines, like engines and boats, so they can work safely again."),
        ("What does consume mean?",
         "To consume means to eat or drink something. It usually means the food or drink is gone afterward."),
        ("What is a tourist?",
         "A tourist is a visitor who comes to see a place for a little while, often with curious eyes and a bag of treats."),
        ("Why can gulls be a problem at a marina?",
         "Gulls can be a problem because they rush toward crumbs and food, which can make a dock noisy and messy."),
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
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
allowed(M, S, T) :- marina(M), snack(S), tool(T).
lesson_learned(Tourist) :- helpful(Tourist), not careless(Tourist).
transformed(Tourist) :- lesson_learned(Tourist).
reconciled(Tourist, Mechanic) :- transformed(Tourist), mechanic(Mechanic).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for mid in MARINAS:
        lines.append(asp.fact("marina", mid))
    for sid, snack in SNACKS.items():
        lines.append(asp.fact("snack", sid))
        if snack.edible:
            lines.append(asp.fact("edible", sid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show allowed/3."))
    return sorted(set(asp.atoms(model, "allowed")))


def asp_verify() -> int:
    rc = 0
    a, b = set(asp_valid_combos()), set(valid_combos())
    if a == b:
        print(f"OK: gate matches valid_combos() ({len(a)} combos).")
    else:
        print("MISMATCH in valid_combos gate:")
        if a - b:
            print("  only in clingo:", sorted(a - b))
        if b - a:
            print("  only in python:", sorted(b - a))
        rc = 1
    try:
        params = resolve_params(argparse.Namespace(marina=None, snack=None, tool=None, tourist=None, tourist_gender=None, mechanic=None, mechanic_gender=None, elder=None, elder_gender=None, lesson=None), random.Random(7))
        sample = generate(params)
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: normal generation smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Marina folk tale storyworld with mechanic, consume, and tour-ist.")
    ap.add_argument("--marina", choices=MARINAS)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--tourist")
    ap.add_argument("--tourist-gender", dest="tourist_gender", choices=["girl", "boy", "woman", "man"])
    ap.add_argument("--mechanic")
    ap.add_argument("--mechanic-gender", dest="mechanic_gender", choices=["girl", "boy", "woman", "man"])
    ap.add_argument("--elder")
    ap.add_argument("--elder-gender", dest="elder_gender", choices=["girl", "boy", "woman", "man"])
    ap.add_argument("--lesson", choices=LESSONS)
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
    marina = args.marina or rng.choice(list(MARINAS))
    snack = args.snack or rng.choice(list(SNACKS))
    tool = args.tool or rng.choice(list(TOOLS))
    if not choose_reasonable_combo(SNACKS[snack], TOOLS[tool]):
        raise StoryError("This marina story needs an edible snack and a real repair tool.")
    tourist_gender = args.tourist_gender or rng.choice(["girl", "boy"])
    mechanic_gender = args.mechanic_gender or rng.choice(["woman", "man"])
    elder_gender = args.elder_gender or rng.choice(["woman", "man"])
    tourist = args.tourist or rng.choice(TOURIST_NAMES)
    mechanic = args.mechanic or rng.choice(MECHANIC_NAMES)
    elder = args.elder or rng.choice(ELDER_NAMES)
    lesson = args.lesson or "harbor_rule"
    return StoryParams(
        marina=marina, snack=snack, tool=tool,
        tourist=tourist, tourist_gender=tourist_gender,
        mechanic=mechanic, mechanic_gender=mechanic_gender,
        elder=elder, elder_gender=elder_gender, lesson=lesson,
    )


def generate(params: StoryParams) -> StorySample:
    if params.marina not in MARINAS or params.snack not in SNACKS or params.tool not in TOOLS or params.lesson not in LESSONS:
        raise StoryError("Invalid params for this marina storyworld.")
    marina = MARINAS[params.marina]
    snack = SNACKS[params.snack]
    tool = TOOLS[params.tool]
    lesson = LESSONS[params.lesson]
    world = tell(marina, snack, tool, params.tourist, params.tourist_gender,
                 params.mechanic, params.mechanic_gender, params.elder, params.elder_gender, lesson)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
    StoryParams(marina="harbor", snack="bun", tool="brush", tourist="Mira", tourist_gender="girl", mechanic="Bram", mechanic_gender="man", elder="Nana", elder_gender="woman", lesson="harbor_rule"),
    StoryParams(marina="sunwharf", snack="apple", tool="pump", tourist="Niko", tourist_gender="boy", mechanic="Kara", mechanic_gender="woman", elder="Uncle Reed", elder_gender="man", lesson="harbor_rule"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show allowed/3."))
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
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
