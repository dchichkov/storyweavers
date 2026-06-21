#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/appetizer_jolly_stethoscope_reconciliation_fairy_tale.py
=========================================================================================

A small standalone fairy-tale storyworld built from the seed words
"appetizer", "jolly", and "stethoscope", with reconciliation as the core turn.

Premise:
A jolly kitchen sprite prepares a castle supper. A child healer uses a
stethoscope to listen to a worried guest. A misunderstanding over the appetizer
creates a hurt feeling, and then the characters make up by sharing, listening,
and offering a kinder choice.

This world keeps the classical tiny-story shape:
- a concrete place and cast
- a state-driven misunderstanding
- a turn of listening and repair
- a closing image showing the changed relationship

It also includes:
- typed entities with meters and memes
- a reasonableness gate
- inline ASP rules mirroring Python checks
- prompts, story QA, and world-knowledge QA
- --verify smoke checks
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "princess", "woman", "queen"}
        male = {"boy", "prince", "man", "king"}
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
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Setting:
    id: str
    name: str
    mood: str
    affordances: set[str] = field(default_factory=set)

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
class Appetizer:
    id: str
    label: str
    phrase: str
    smell: str
    shares_well: bool = True
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
class Tool:
    id: str
    label: str
    phrase: str
    use: str
    gentle: bool = True
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
class Conflict:
    id: str
    cause: str
    hurt: str
    risk: int
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
class Reconciliation:
    id: str
    action: str
    words: str
    repair: str
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
        clone.facts = dict(self.facts)
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


def _r_hurt(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.meters["hurt"] < THRESHOLD:
            continue
        sig = ("hurt", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["sad"] += 1
        out.append("__hurt__")
    return out


def _r_repair(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes["apology"] < THRESHOLD or e.memes["forgive"] < THRESHOLD:
            continue
        sig = ("repair", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["peace"] += 1
        e.meters["hurt"] = 0.0
        out.append("__repair__")
    return out


CAUSAL_RULES = [Rule("hurt", "social", _r_hurt), Rule("repair", "social", _r_repair)]


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


def act_of_listening(world: World, listener: Entity, speaker: Entity, tool: Tool) -> None:
    listener.memes["care"] += 1
    speaker.memes["seen"] += 1
    world.say(
        f"{listener.id} set down {tool.phrase} and listened closely with the {tool.label}. "
        f"{listener.id} heard what {speaker.id} was afraid of."
    )


def misunderstanding(world: World, hero: Entity, friend: Entity, appetizer: Appetizer, conflict: Conflict) -> None:
    hero.memes["want"] += 1
    hero.memes["jolly"] += 1
    friend.memes["hurt"] += 1
    world.say(
        f"At the castle feast, {hero.id} was quite jolly and reached for the {appetizer.label} first. "
        f"{friend.id} thought the first bite had been taken away, and {friend.pronoun()} grew quiet."
    )
    world.say(
        f'"That feels {conflict.hurt}," said {friend.id}, and the hall suddenly seemed less bright.'
    )


def apology(world: World, hero: Entity, friend: Entity, recon: Reconciliation) -> None:
    hero.memes["apology"] += 1
    friend.memes["forgive"] += 1
    world.say(
        f"{hero.id} bowed their head and said, \"I am sorry. I did not mean to be unkind.\" "
        f'Then {hero.id} offered {recon.repair}, following {recon.words}.'
    )
    propagate(world, narrate=False)


def healing_turn(world: World, healer: Entity, friend: Entity, tool: Tool, appetizer: Appetizer) -> None:
    act_of_listening(world, healer, friend, tool)
    friend.memes["relief"] += 1
    world.say(
        f"{healer.id} held the {tool.label} to {friend.id}'s chest, just like a careful forest doctor. "
        f"\"Your heart sounds brave,\" {healer.id} said, \"and the {appetizer.label} is for sharing.\""
    )


def reconciliation_end(world: World, hero: Entity, friend: Entity, appetizer: Appetizer, recon: Reconciliation) -> None:
    hero.memes["peace"] += 1
    friend.memes["peace"] += 1
    world.say(
        f"Then the two of them sat side by side. They shared the {appetizer.phrase}, and the room filled with {appetizer.smell}. "
        f"{friend.id} smiled again, and {hero.id} smiled back."
    )
    world.say(
        f"By candlelight, the castle felt warm and fair. The friends had turned hurt feelings into {recon.id}, "
        f"and the feast went on jolly and calm."
    )


def tell(setting: Setting, appetizer: Appetizer, tool: Tool, conflict: Conflict, recon: Reconciliation,
         hero_name: str = "Mira", hero_type: str = "girl",
         friend_name: str = "Pip", friend_type: str = "boy") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="host", traits=["jolly"]))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type, role="guest", traits=["gentle"]))
    healer = world.add(Entity(id="Wren", kind="character", type="girl", role="healer", label="the little healer"))
    world.add(Entity(id="feast", kind="thing", type="hall", label=setting.name))
    world.facts["appetizer"] = appetizer
    world.facts["tool"] = tool
    world.facts["conflict"] = conflict
    world.facts["reconciliation"] = recon

    world.say(
        f"Once in a bright little kingdom, {hero.id} lived in {setting.name}, where the mood was always {setting.mood}. "
        f"Everyone knew {hero.id} for being jolly."
    )
    world.say(
        f"That evening, the royal kitchen sent out {appetizer.phrase}, and its {appetizer.smell} drifted through the hall."
    )
    world.para()
    misunderstanding(world, hero, friend, appetizer, conflict)
    world.say(
        f"{friend.id} would not take another chair at the table, and {hero.id}'s smile fell a little."
    )
    world.para()
    healing_turn(world, healer, friend, tool, appetizer)
    apology(world, hero, friend, recon)
    world.para()
    reconciliation_end(world, hero, friend, appetizer, recon)

    world.facts.update(hero=hero, friend=friend, healer=healer, setting=setting, outcome="reconciled")
    return world


SETTINGS = {
    "castle": Setting("castle", "the moonlit castle hall", "golden", {"feast"}),
    "garden": Setting("garden", "the rose garden pavilion", "soft", {"feast"}),
    "tower": Setting("tower", "the high tower room", "quiet", {"feast"}),
}

APPETIZERS = {
    "pie_bites": Appetizer("pie_bites", "appetizer", "little herb pastry appetizers", "buttery", True, {"appetizer"}),
    "fruit_cups": Appetizer("fruit_cups", "appetizer", "sparkling fruit appetizers", "sweet", True, {"appetizer"}),
    "soup_cups": Appetizer("soup_cups", "appetizer", "warm saffron soup appetizers", "savory", True, {"appetizer"}),
}

TOOLS = {
    "stethoscope": Tool("stethoscope", "stethoscope", "a silver stethoscope", "listen to hearts", True, {"stethoscope"}),
    "heartscope": Tool("heartscope", "stethoscope", "a little stethoscope", "hear a worried heart", True, {"stethoscope"}),
}

CONFLICTS = {
    "sharing": Conflict("sharing", "they both wanted the first bite", "left out", 1, {"conflict"}),
    "rudeness": Conflict("rudeness", "one friend spoke too quickly", "hurt", 1, {"conflict"}),
}

RECONCILIATIONS = {
    "apology": Reconciliation("reconciliation", "reconciliation", "kind apology", "a share of the appetizer", {"reconciliation"}),
    "speak_softly": Reconciliation("reconciliation", "reconciliation", "soft words", "a seat beside the friend", {"reconciliation"}),
}

GIRL_NAMES = ["Mira", "Luna", "Elin", "Nia", "Tessa"]
BOY_NAMES = ["Pip", "Theo", "Owen", "Bram", "Joss"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for a in APPETIZERS:
            for c in CONFLICTS:
                combos.append((s, a, c))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    appetizer: str
    conflict: str
    tool: str
    reconciliation: str
    hero_name: str
    hero_type: str
    friend_name: str
    friend_type: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fairy-tale story for a small child that includes the words "appetizer", "jolly", and "stethoscope".',
        f"Tell a castle story where {f['hero'].id} is jolly, a misunderstanding happens over the appetizer, and then the friends reconcile with help from a stethoscope.",
        f"Write a gentle reconciliation tale set in {f['setting'].name} with a healer, an appetizer, and a happy ending.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, friend, healer = f["hero"], f["friend"], f["healer"]
    app, tool, conf, recon = f["appetizer"], f["tool"], f["conflict"], f["reconciliation"]
    return [
        ("Who is the story about?",
         f"It is about {hero.id}, {friend.id}, and {healer.id}. They meet in a castle hall, and the whole tale turns on a small hurt that gets mended."),
        ("Why did the friends get upset?",
         f"They both wanted the first bite of the {app.label}. That caused the misunderstanding, and {friend.id} felt left out for a moment."),
        ("How did the healer help?",
         f"{healer.id} used the {tool.label} to listen carefully and calm the worry. Listening gave everyone time to speak softly instead of acting cross."),
        ("How did the story end?",
         f"It ended with reconciliation. {hero.id} apologized, {friend.id} forgave them, and they shared the appetizer together.")
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is an appetizer?",
         "An appetizer is a small food served before the main meal. It is meant to be shared and enjoyed before supper."),
        ("What is a stethoscope?",
         "A stethoscope is a listening tool doctors use to hear heartbeats and breathing. It helps them check whether someone is okay."),
        ("What does jolly mean?",
         "Jolly means cheerful, merry, and full of good feeling. A jolly person brings a bright mood to the room."),
        ("What is reconciliation?",
         "Reconciliation means making up after a disagreement. It happens when hurt feelings are repaired and people are friendly again."),
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
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("castle", "pie_bites", "sharing", "stethoscope", "apology", "Mira", "girl", "Pip", "boy"),
    StoryParams("garden", "fruit_cups", "rudeness", "heartscope", "speak_softly", "Luna", "girl", "Theo", "boy"),
    StoryParams("tower", "soup_cups", "sharing", "stethoscope", "apology", "Tessa", "girl", "Bram", "boy"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.reconciliation and args.reconciliation not in RECONCILIATIONS:
        raise StoryError("(Unknown reconciliation choice.)")
    setting = args.setting or rng.choice(list(SETTINGS))
    appetizer = args.appetizer or rng.choice(list(APPETIZERS))
    conflict = args.conflict or rng.choice(list(CONFLICTS))
    tool = args.tool or rng.choice(list(TOOLS))
    reconciliation = args.reconciliation or rng.choice(list(RECONCILIATIONS))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    friend_type = args.friend_type or ("boy" if hero_type == "girl" else "girl")
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    friend_name = args.friend_name or rng.choice([n for n in (BOY_NAMES if friend_type == "boy" else GIRL_NAMES) if n != hero_name])
    return StoryParams(setting, appetizer, conflict, tool, reconciliation, hero_name, hero_type, friend_name, friend_type)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        APPETIZERS[params.appetizer],
        TOOLS[params.tool],
        CONFLICTS[params.conflict],
        RECONCILIATIONS[params.reconciliation],
        params.hero_name,
        params.hero_type,
        params.friend_name,
        params.friend_type,
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale reconciliation storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--appetizer", choices=APPETIZERS)
    ap.add_argument("--conflict", choices=CONFLICTS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--reconciliation", choices=RECONCILIATIONS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-type", choices=["girl", "boy"])
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


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for a in APPETIZERS:
        lines.append(asp.fact("appetizer", a))
    for t in TOOLS:
        lines.append(asp.fact("tool", t))
    for c in CONFLICTS:
        lines.append(asp.fact("conflict", c))
    for r in RECONCILIATIONS:
        lines.append(asp.fact("reconciliation", r))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, A, C) :- setting(S), appetizer(A), conflict(C).
outcome(reconciled) :- valid(_, _, _).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python.")
        if py - cl:
            print("  only in python:", sorted(py - cl))
        if cl - py:
            print("  only in asp:", sorted(cl - py))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate() smoke test produced a story.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def resolve_choices(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for combo in asp_valid_combos():
            print("  ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_choices(args, random.Random(seed))
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
            header = f"### {p.hero_name} and {p.friend_name} ({p.setting})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
