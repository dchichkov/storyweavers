#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/technology_roof_extract_warehouse_aisle_twist_surprise.py
=========================================================================================

A small fable-style story world set in a warehouse aisle. A clever child and a
patient helper use technology to reach a roof beam, twist a stuck latch, and
extract a surprise prize without causing a mess. The turn is driven by simulated
state: the tool they choose, the height of the roof shelf, the stubbornness of
the latch, and whether the surprise is reachable safely.

This world keeps the story child-facing and concrete. It includes the requested
seed words and instruments:
- technology
- roof
- extract
- Twist
- Surprise
- warehouse aisle
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
SMART_MIN = 2

# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
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
class Tool:
    id: str
    label: str
    phrase: str
    where: str
    sense: int
    helps: set[str] = field(default_factory=set)

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
class ObjectTarget:
    id: str
    label: str
    phrase: str
    height: str
    extractable: bool = True
    risky: bool = False
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
class Twist:
    id: str
    label: str
    cue: str
    action: str
    success: str
    fail: str
    sense: int
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


@dataclass
class Surprise:
    id: str
    label: str
    phrase: str
    ending: str
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
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        return c


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


# ---------------------------------------------------------------------------
# World rules
# ---------------------------------------------------------------------------
def _r_weight(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.meters["lifted"] < THRESHOLD:
            continue
        sig = ("weight", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["hope"] += 1
        out.append("__hope__")
    return out


def _r_stuck(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.meters["stuck"] < THRESHOLD:
            continue
        sig = ("stuck", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.get("child").memes["worry"] += 1
        out.append("__worry__")
    return out


CAUSAL_RULES = [Rule("weight", "physical", _r_weight), Rule("stuck", "physical", _r_stuck)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            items = rule.apply(world)
            if items:
                changed = True
                produced.extend(i for i in items if not i.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
@dataclass
@dataclass
class StoryParams:
    setting: str
    tool: str
    target: str
    twist: str
    surprise: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    helper_role: str
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
    "warehouse_aisle": "a warehouse aisle lined with tall boxes and bright labels",
}

TOOLS = {
    "scanner": Tool("scanner", "scanner", "a handheld scanner", "on a cart", 3, {"find"}),
    "tablet": Tool("tablet", "tablet", "a small tablet", "in a pocket", 3, {"see"}),
    "drone": Tool("drone", "drone", "a tiny drone with a little lamp", "on a shelf", 4, {"reach", "see"}),
}

TARGETS = {
    "roof_beam": ObjectTarget("roof_beam", "roof beam", "the roof beam", "up near the roof", True, False, {"roof"}),
    "top_crate": ObjectTarget("top_crate", "top crate", "the top crate", "on the highest shelf", True, False, {"roof"}),
    "sealed_box": ObjectTarget("sealed_box", "sealed box", "the sealed box", "on the top rack", True, True, {"extract"}),
}

TWISTS = {
    "twist_latch": Twist("twist_latch", "Twist", "a twisted latch", "twisted the latch", "the latch turned open", "the latch would not budge", 3, 3, {"twist"}),
    "twist_cap": Twist("twist_cap", "Twist", "a tight cap", "twisted the cap", "the cap popped loose", "the cap stayed stuck", 3, 2, {"twist"}),
}

SURPRISES = {
    "songbird": Surprise("songbird", "Surprise", "a tiny wind-up songbird", "It chirped a cheerful tune", {"surprise"}),
    "map": Surprise("map", "Surprise", "a folded map with a gold star", "It pointed to a kinder path", {"surprise"}),
    "seed_packet": Surprise("seed_packet", "Surprise", "a packet of flower seeds", "It promised something lovely to grow", {"surprise"}),
}

GIRL_NAMES = ["Mia", "Lina", "Ava", "Nora", "Zoe", "Ella"]
BOY_NAMES = ["Eli", "Theo", "Sam", "Noah", "Finn", "Leo"]
TRAITS = ["careful", "curious", "kind", "patient", "clever"]


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos = []
    for s in SETTINGS:
        for t in TOOLS:
            if TOOLS[t].sense < SMART_MIN:
                continue
            for tg in TARGETS:
                if not TARGETS[tg].extractable:
                    continue
                for tw in TWISTS:
                    for sp in SURPRISES:
                        combos.append((s, t, tg, tw, sp))
    return combos


# ---------------------------------------------------------------------------
# Reasoning helpers
# ---------------------------------------------------------------------------
def tool_can_help(tool: Tool, target: ObjectTarget) -> bool:
    return bool(tool.helps) and ("reach" in tool.helps or not target.risky)


def twist_can_work(twist: Twist, target: ObjectTarget) -> bool:
    if target.id == "roof_beam":
        return False
    return twist.power >= 2


def predict_extraction(world: World, target_id: str, twist_id: str, tool_id: str) -> dict:
    sim = world.copy()
    _perform_extraction(sim, sim.get("child"), TOOLS[tool_id], TARGETS[target_id], TWISTS[twist_id], narrate=False)
    return {"succeeded": sim.get(target_id).meters["opened"] >= THRESHOLD}


# ---------------------------------------------------------------------------
# Story verbs
# ---------------------------------------------------------------------------
def _perform_extraction(world: World, child: Entity, tool: Tool, target: ObjectTarget, twist: Twist, narrate: bool = True) -> None:
    child.meters["lifted"] += 1
    if target.risky:
        child.meters["stuck"] += 1
    if tool_can_help(tool, target) and twist_can_work(twist, target):
        target.meters["opened"] += 1
    else:
        target.meters["stuck"] += 1
    propagate(world, narrate=narrate)


def opening(world: World, child: Entity, helper: Entity) -> None:
    world.say(
        f"On a bright morning, {child.id} and {helper.id} walked through a warehouse aisle where the boxes reached almost to the roof."
    )
    world.say(
        f"{child.id} loved technology, especially anything with a button, a light, or a tiny screen."
    )


def ask(world: World, child: Entity, target: ObjectTarget) -> None:
    world.say(
        f"{child.id} peered up at {target.phrase}. “If I can get that down, we might find a useful little surprise,” {child.pronoun()} said."
    )


def warn(world: World, helper: Entity, child: Entity, target: ObjectTarget, twist: Twist) -> None:
    world.say(
        f"{helper.id} looked at the roof line and frowned gently. “That one is high, and the {twist.label.lower()} might be stubborn. Let’s use our heads first,” {helper.pronoun()} said."
    )


def tool_use(world: World, child: Entity, tool: Tool) -> None:
    child.memes["hope"] += 1
    world.say(
        f"{child.id} held up {tool.phrase}. The little machine glowed, and the aisle felt a bit less lonely."
    )


def twist_action(world: World, child: Entity, twist: Twist) -> None:
    child.memes["determination"] += 1
    world.say(
        f"Then came the {twist.label}: {child.id} {twist.action} with small careful hands."
    )


def success(world: World, child: Entity, target: ObjectTarget, twist: Twist) -> None:
    target.meters["opened"] = 1
    world.say(
        f"This time, {twist.success}, and the prize at the roof edge came free without a tumble."
    )


def failure(world: World, helper: Entity, target: ObjectTarget, twist: Twist) -> None:
    world.say(
        f"{twist.fail}, so {helper.id} steadied the box and asked {helper.pronoun('object')} to try again more slowly."
    )


def reveal(world: World, surprise: Surprise, tool: Tool) -> None:
    world.say(
        f"Inside was {surprise.phrase}. {surprise.ending}."
    )
    world.say(
        f"{tool.label.capitalize()} had helped them extract the hidden thing, and the warehouse aisle suddenly felt like a storybook path."
    )


def lesson(world: World, child: Entity, helper: Entity, tool: Tool, target: ObjectTarget) -> None:
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"{helper.id} smiled and said, “Big things are safest when you ask for help and use the right tool.”"
    )
    world.say(
        f"{child.id} nodded, glad the roof was still calm and the box was still in one piece."
    )


def tell(setting: str, tool: Tool, target: ObjectTarget, twist: Twist, surprise: Surprise,
         hero: str = "Mia", hero_gender: str = "girl", helper: str = "Leo", helper_gender: str = "boy",
         helper_role: str = "helper") -> World:
    world = World()
    child = world.add(Entity(id=hero, kind="character", type=hero_gender, role="hero", traits=["curious"]))
    helper_ent = world.add(Entity(id=helper, kind="character", type=helper_gender, role=helper_role, traits=["patient"]))
    world.add(Entity(id="roof", type="place", label="the roof line"))
    world.add(Entity(id="target", type="thing", label=target.label, attrs={"kind": target.id}))
    opening(world, child, helper_ent)
    world.para()
    ask(world, child, target)
    warn(world, helper_ent, child, target, twist)
    tool_use(world, child, tool)
    twist_action(world, child, twist)
    _perform_extraction(world, child, tool, target, twist, narrate=False)
    world.para()
    if world.get("target").meters["opened"] >= THRESHOLD:
        success(world, child, target, twist)
        reveal(world, surprise, tool)
        lesson(world, child, helper_ent, tool, target)
    else:
        failure(world, helper_ent, target, twist)
        world.say(
            f"After that, they chose a steadier way, and the roof beam stayed safe while they found a better angle."
        )
        reveal(world, surprise, tool)
        lesson(world, child, helper_ent, tool, target)
    world.facts.update(child=child, helper=helper_ent, tool=tool, target=target, twist=twist, surprise=surprise, setting=setting)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "technology": [("What is technology?", "Technology is a tool or machine made to help people do things more easily or more carefully.")],
    "roof": [("What is a roof?", "A roof is the top part of a building. It keeps rain and sun off the inside.")],
    "extract": [("What does extract mean?", "To extract something means to take it out of where it was held or hidden.")],
    "twist": [("What does twist mean?", "To twist means to turn something around, usually with your hand.")],
    "surprise": [("What is a surprise?", "A surprise is something you did not expect. It can make a story more exciting.")],
    "warehouse": [("What is a warehouse?", "A warehouse is a big building where many boxes and goods are stored.")],
    "aisle": [("What is an aisle?", "An aisle is a narrow path between rows of shelves or seats.")],
}
KNOWLEDGE_ORDER = ["technology", "warehouse", "aisle", "roof", "extract", "twist", "surprise"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fable-style story set in a warehouse aisle that includes the words "technology", "roof", and "extract".',
        f'Tell a child-friendly fable where {f["child"].id} uses technology to reach a roof-high prize, then twists something open and extracts a surprise.',
        f'Write a short moral story about a clever child, a helper, and a surprise hidden high on a shelf in a warehouse aisle.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, helper = f["child"], f["helper"]
    target, twist, surprise = f["target"], f["twist"], f["surprise"]
    qa = [
        ("Who is the story about?", f"It is about {child.id} and {helper.id}, who walked through a warehouse aisle together."),
        ("What did the child love?", f"{child.id} loved technology, especially tools with lights, buttons, and clever little parts."),
        ("What was high up near the roof?", f"{target.phrase} was high up near the roof line, so they had to think carefully before trying to get it."),
        ("What did they try to do?", f"They tried to extract {surprise.phrase} by using technology and then making a careful twist."),
    ]
    if world.get("target").meters["opened"] >= THRESHOLD:
        qa.append((
            "How did the story end?",
            f"They got the surprise out safely, and the aisle ended with a happy, useful discovery. The roof stayed calm because they used the right tool and a careful twist."
        ))
    else:
        qa.append((
            "How did they solve the problem?",
            f"They slowed down, kept the roof safe, and tried again more carefully until the hidden thing could be extracted. The helper's patience made the difference."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["target"].tags) | set(world.facts["twist"].tags) | set(world.facts["surprise"].tags) | {"technology", "roof", "extract"}
    out = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid_combo(S, T, TG, TW, SP) :- setting(S), tool(T), target(TG), twist(TW), surprise(SP), smart(T).
smart(T) :- sense(T, S), sense_min(M), S >= M.
success(TG, TW, T) :- tool(T), target(TG), twist(TW), tool_helps_reach(T), twist_power(TW, P), P >= 2, not risky_target(TG).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("sense", tid, t.sense))
        for h in sorted(t.helps):
            lines.append(asp.fact("tool_helps_reach", tid))
    for tg in TARGETS:
        lines.append(asp.fact("target", tg))
        if TARGETS[tg].risky:
            lines.append(asp.fact("risky_target", tg))
    for twid, tw in TWISTS.items():
        lines.append(asp.fact("twist", twid))
        lines.append(asp.fact("twist_power", twid, tw.power))
    for sp in SURPRISES:
        lines.append(asp.fact("surprise", sp))
    lines.append(asp.fact("sense_min", SMART_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/5."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in ASP gate")
    # smoke test normal generation
    try:
        p = CURATED[0]
        s = generate(p)
        if not s.story.strip():
            raise RuntimeError("empty story")
        print("OK: normal generate smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    return rc


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fable-style warehouse aisle story world with technology, roof, extract, Twist, and Surprise.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-role", default="helper")
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
              and (args.tool is None or c[1] == args.tool)
              and (args.target is None or c[2] == args.target)
              and (args.twist is None or c[3] == args.twist)
              and (args.surprise is None or c[4] == args.surprise)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, tool, target, twist, surprise = rng.choice(combos)
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if hero_gender == "girl" else "girl")
    hero = args.hero or (rng.choice(GIRL_NAMES) if hero_gender == "girl" else rng.choice(BOY_NAMES))
    helper = args.helper or (rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != hero]))
    return StoryParams(setting, tool, target, twist, surprise, hero, hero_gender, helper, helper_gender, args.helper_role)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        params.setting,
        TOOLS[params.tool],
        TARGETS[params.target],
        TWISTS[params.twist],
        SURPRISES[params.surprise],
        params.hero,
        params.hero_gender,
        params.helper,
        params.helper_gender,
        params.helper_role,
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
    StoryParams("warehouse_aisle", "drone", "sealed_box", "twist_latch", "songbird", "Mia", "girl", "Leo", "boy", "helper"),
    StoryParams("warehouse_aisle", "scanner", "top_crate", "twist_cap", "map", "Eli", "boy", "Nora", "girl", "helper"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_combo/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
