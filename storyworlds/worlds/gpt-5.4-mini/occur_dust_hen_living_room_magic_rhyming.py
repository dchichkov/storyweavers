#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/occur_dust_hen_living_room_magic_rhyming.py
===========================================================================

A small, standalone storyworld for a rhyming magic-in-the-living-room tale.

Seed words:
- occur
- dust
- hen

Setting:
- living room

Feature:
- Magic

Style:
- Rhyming Story

Premise:
A child and a hen accidentally release a little dust-goblin magic in the
living room. The rhyme-driven world model tracks the mess, the magic, and the
calm fix: a broom, a cloth, and a gentle spell that restores the room.

This script is self-contained and uses only the stdlib plus the shared
storyworlds/results.py containers.
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
RHYMES = {
    "room": "bloom",
    "dust": "must",
    "spark": "dark",
    "shine": "line",
    "bright": "light",
    "song": "long",
    "floor": "more",
    "clean": "gleam",
}


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
class MagicWord:
    id: str
    spell: str
    shimmer: str
    charm: str
    makes_magic: bool = True
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
class DustThing:
    id: str
    label: str
    phrase: str
    settles_on: str
    dusty: bool = True
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
class Fix:
    id: str
    sense: int
    power: int
    line: str
    fail: str
    qa_text: str
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
class Theme:
    id: str
    scene: str
    room_line: str
    song_line: str
    ending: str

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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


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


def _r_dust(world: World) -> list[str]:
    out: list[str] = []
    if world.get("room").meters["dusty"] < THRESHOLD:
        return out
    sig = ("dust_spread",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("room").meters["foggy"] += 1
    world.get("hen").memes["sneezy"] += 1
    out.append("__dust__")
    return out


def _r_magic(world: World) -> list[str]:
    out: list[str] = []
    if world.get("spell").meters["spark"] < THRESHOLD:
        return out
    sig = ("magic_bloom",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("room").meters["shimmer"] += 1
    world.get("child").memes["wonder"] += 1
    out.append("__magic__")
    return out


CAUSAL_RULES = [Rule("dust", "physical", _r_dust), Rule("magic", "social", _r_magic)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(s for s in lines if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def rhyme(word: str) -> str:
    return RHYMES.get(word, word)


def reasonable_fix() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= SENSE_MIN]


def best_fix() -> Fix:
    return max(FIXES.values(), key=lambda f: f.sense)


def hazard(magic: MagicWord, dust: DustThing) -> bool:
    return magic.makes_magic and dust.dusty


def severity(dust: DustThing, delay: int) -> int:
    return 1 + delay


def contained(fix: Fix, dust: DustThing, delay: int) -> bool:
    return fix.power >= severity(dust, delay)


def _do_magic(world: World, spell: Entity, dust: Entity, narrate: bool = True) -> None:
    spell.meters["spark"] += 1
    dust.meters["dusty"] += 1
    propagate(world, narrate=narrate)


def tell(theme: Theme, magic: MagicWord, dust: DustThing, fix: Fix,
         child_name: str = "Mina", child_gender: str = "girl",
         hen_name: str = "Dot", delay: int = 0, parent_name: str = "Mom") -> World:
    w = World()
    child = w.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    hen = w.add(Entity(id=hen_name, kind="character", type="hen", role="helper"))
    parent = w.add(Entity(id=parent_name, kind="character", type="mother", role="parent", label="mom"))
    room = w.add(Entity(id="room", type="room", label="living room"))
    spell = w.add(Entity(id="spell", type="spell", label=magic.spell))
    dust_ent = w.add(Entity(id="dust", type="dust", label=dust.label))
    child.memes["joy"] = 1
    hen.memes["curious"] = 1
    w.say(f"In the living room, {child.id} and {hen.id} began a merry play.")
    w.say(f"{theme.room_line} {theme.song_line}")
    w.say(f'Then {child.id} whispered "{magic.spell}," and wondered what magic might occur.')
    w.para()
    child.memes["curiosity"] += 1
    if not hazard(magic, dust):
        raise StoryError("No story: this spell does not make enough magic for dust to matter.")
    w.say(
        f"From the rug came a little swirl of dust, as light as a puff of flour, "
        f"and soon it danced and spun."
    )
    w.say(f"{hen.id} clucked and fluffed {hen.pronoun('possessive')} wings.")
    w.say(f'"It is getting dusty," {hen.pronoun()} seemed to say, ' f'"and that is no fun for any play."')
    w.para()
    w.say(
        f'{child.id} reached for the magic word again, but {parent.label_word} '
        f"noticed the dust and the spark before things could grow rough."
    )
    delay_severity = severity(dust, delay)
    fixed = contained(fix, dust, delay)
    if fixed:
        _do_magic(w, spell, dust_ent)
        w.say(
            f"{parent.label_word.capitalize()} smiled, swept once, and used {fix.qa_text}. "
            f"The dust settled down, and the room began to gleam."
        )
        w.say(
            f"Then {hen.id} pecked at a crumb, {child.id} laughed, and the living room "
            f"ended in a bright little bloom."
        )
    else:
        _do_magic(w, spell, dust_ent)
        room.meters["dusty"] += delay_severity
        w.say(
            f"{parent.label_word.capitalize()} tried {fix.fail}, but the dust kept whirling "
            f"and the room went dim and gray."
        )
        w.say(
            f"So {child.id} and {hen.id} opened the window, took a careful step back, "
            f"and let the magic fade away."
        )
    w.facts.update(
        child=child,
        hen=hen,
        parent=parent,
        room=room,
        spell=spell,
        dust=dust_ent,
        theme=theme,
        magic=magic,
        dust_cfg=dust,
        fix=fix,
        delay=delay,
        outcome="contained" if fixed else "drifted",
        settled=fixed,
    )
    return w


THEMES = {
    "living_room": Theme(
        "living_room",
        "The cushions made a soft nest, the lamp made a warm hush, and the carpet looked like a stage.",
        "On the shelf a silver spoon could shine, and the clock made a tick-tock line.",
        "A hen in the room can make a tune, if you keep the magic gentle and soon.",
        "The room was tidy again, with a gleam in the seams."
    ),
}

MAGIC_WORDS = {
    "occur": MagicWord(
        "occur", "occur", "silver shimmer", "a tiny rhyme that makes a surprise appear",
        True, {"magic", "occur"}
    ),
    "gleam": MagicWord(
        "gleam", "gleam", "moonbeam gleam", "a sparkle that can clean and charm",
        True, {"magic"}
    ),
    "twirl": MagicWord(
        "twirl", "twirl", "whirlwind twirl", "a turning word that stirs the dust",
        True, {"magic"}
    ),
}

DUST_THINGS = {
    "dust": DustThing("dust", "dust", "a soft little dust puff", "the rug", True, {"dust"}),
    "dusty_cushion": DustThing("dusty_cushion", "cushion dust", "dust on the cushion", "the sofa", True, {"dust"}),
    "crumb": DustThing("crumb", "crumb dust", "a crumb of dust", "the floor", True, {"dust"}),
}

FIXES = {
    "broom": Fix(
        "broom", 3, 4,
        "swept the dust into a neat small pile",
        "swept once, but the dust kept floating about",
        "swept the dust into a neat small pile",
        {"clean", "dust"},
    ),
    "cloth": Fix(
        "cloth", 2, 3,
        "wiped the shelf with a soft cloth",
        "wiped the shelf, but the dust still drifted in the air",
        "wiped the shelf with a soft cloth",
        {"clean", "dust"},
    ),
    "vacuum": Fix(
        "vacuum", 3, 5,
        "used the little vacuum and hummed until every speck was gone",
        "used the little vacuum, but the dust had already spread too far",
        "used the little vacuum and hummed until every speck was gone",
        {"clean", "dust"},
    ),
    "water": Fix(
        "water", 1, 1,
        "sprinkled water on the sparkle",
        "sprinkled water on the sparkle, but that did not help the dust",
        "sprinkled water on the sparkle",
        {"weak"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Ivy", "Zoe"]
BOY_NAMES = ["Noah", "Theo", "Ben", "Max", "Eli"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    if not reasonable_fix():
        return combos
    for tid in THEMES:
        for mid in MAGIC_WORDS:
            for did in DUST_THINGS:
                if hazard(MAGIC_WORDS[mid], DUST_THINGS[did]):
                    combos.append((tid, mid, did))
    return combos


@dataclass
@dataclass
class StoryParams:
    theme: str
    magic: str
    dust: str
    fix: str
    child: str
    child_gender: str
    hen: str
    delay: int = 0
    parent: str = "mother"
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


KNOWLEDGE = {
    "dust": [("What is dust?", "Dust is made of tiny bits from fabric, dirt, and skin. It can gather on shelves, rugs, and windowsills.")],
    "hen": [("What is a hen?", "A hen is a grown female chicken. Hens cluck, peck, and scratch the ground.")],
    "magic": [("What is magic in a story?", "Magic in a story is pretend power that makes unusual things happen. It can be helpful, tricky, or sparkly.")],
    "broom": [("What is a broom for?", "A broom helps sweep dirt and dust into a pile so it can be cleaned up.")],
    "cloth": [("What does a cloth do?", "A cloth can wipe up dust from a table or shelf and leave it cleaner.")],
    "vacuum": [("What does a vacuum do?", "A vacuum sucks up dust and crumbs. It is useful when the mess is too big for a cloth.")],
}

KNOWLEDGE_ORDER = ["magic", "hen", "dust", "broom", "cloth", "vacuum"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a rhyming story for a young child that includes the words "{f["magic"].spell}", "dust", and "hen".',
        f"Tell a living-room magic story where {f['child'].id} and {f['hen'].id} make dust occur, then clean it up with a calm rhyme.",
        f'Write a child-friendly rhyming story about a little spell that can make dust appear in a living room, and end with a neat clean room.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    hen = f["hen"]
    parent = f["parent"]
    fix = f["fix"]
    dust = f["dust_cfg"]
    qa = [
        ("Who is the story about?", f"It is about {child.id}, {hen.id}, and {parent.label_word}. They share a tiny magic mishap in the living room."),
        ("What word made the magic happen?", f'The magic word was "{f["magic"].spell}". It called up a little shimmer and made the dust move and twirl.'),
        ("What got messy?", f"The dust got messy in the living room. It swirled onto the rug and made the room feel less neat."),
    ]
    if f["outcome"] == "contained":
        qa.append((
            "How did they fix the mess?",
            f"They used {fix.qa_text}. That helped the dust settle so the living room could gleam again."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with a clean, bright living room and a happy hen. The magic stayed gentle, and the room looked ready for more play."
        ))
    else:
        qa.append((
            "What happened when the fix was not enough?",
            f"{parent.label_word.capitalize()} tried to help, but the dust kept floating. So they stepped back, opened the window, and let the magic fade."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["magic"].tags) | set(world.facts["dust_cfg"].tags) | set(world.facts["fix"].tags)
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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def explain_rejection(magic: MagicWord, dust: DustThing) -> str:
    return f"(No story: {magic.spell} can make magic, but {dust.label} is not dusty enough for the living room rhyme.)"


def explain_fix(rid: str) -> str:
    fx = FIXES[rid]
    better = ", ".join(sorted(f.id for f in reasonable_fix()))
    return f"(Refusing fix '{rid}': it is too weak for this rhyme-world. Try: {better}.)"


ASP_RULES = r"""
hazard(M, D) :- makes_magic(M), dusty(D).
reasonable(F) :- fix(F), sense(F, S), sense_min(M), S >= M.
valid(T, M, D) :- theme(T), magic_word(M), dust_item(D), hazard(M, D), reasonable_fix_exists.
reasonable_fix_exists :- reasonable(_).
contained(F, D, Delay) :- power(F, P), severity(D, Delay, S), P >= S.
outcome(celebrate) :- contained(F, D, Delay), valid(_, _, _).
outcome(drift) :- hazard(M, D), not contained(_, D, Delay).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for mid, m in MAGIC_WORDS.items():
        lines.append(asp.fact("magic_word", mid))
        if m.makes_magic:
            lines.append(asp.fact("makes_magic", mid))
    for did, d in DUST_THINGS.items():
        lines.append(asp.fact("dust_item", did))
        if d.dusty:
            lines.append(asp.fact("dusty", did))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("sense", fid, f.sense))
        lines.append(asp.fact("power", fid, f.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH: ASP gate differs from valid_combos().")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(
            theme=None, magic=None, dust=None, fix=None, child=None,
            child_gender=None, hen=None, delay=None, parent=None
        ), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test succeeded.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming living-room magic storyworld.")
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--magic", choices=MAGIC_WORDS)
    ap.add_argument("--dust", choices=DUST_THINGS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--hen")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
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
    if args.magic and args.dust and not hazard(MAGIC_WORDS[args.magic], DUST_THINGS[args.dust]):
        raise StoryError(explain_rejection(MAGIC_WORDS[args.magic], DUST_THINGS[args.dust]))
    if args.fix and FIXES[args.fix].sense < SENSE_MIN:
        raise StoryError(explain_fix(args.fix))
    combos = [c for c in valid_combos()
              if (args.theme is None or c[0] == args.theme)
              and (args.magic is None or c[1] == args.magic)
              and (args.dust is None or c[2] == args.dust)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    theme, magic, dust = rng.choice(sorted(combos))
    fix = args.fix or rng.choice(sorted(f.id for f in reasonable_fix()))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(["Mina", "Lila", "Theo", "Noah", "Ivy", "Eli"])
    hen = args.hen or rng.choice(["Dot", "Pip", "Nell", "Feather"])
    parent = args.parent or rng.choice(["mother", "father"])
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(theme, magic, dust, fix, child, child_gender, hen, delay, parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(THEMES[params.theme], MAGIC_WORDS[params.magic], DUST_THINGS[params.dust], FIXES[params.fix],
                 params.child, params.child_gender, params.hen, params.delay, params.parent)
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
    StoryParams("living_room", "occur", "dust", "broom", "Mina", "girl", "Dot", 0, "mother"),
    StoryParams("living_room", "gleam", "dusty_cushion", "cloth", "Theo", "boy", "Pip", 0, "father"),
    StoryParams("living_room", "twirl", "crumb", "vacuum", "Ivy", "girl", "Nell", 1, "mother"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for t, m, d in combos:
            print(f"  {t:12} {m:10} {d}")
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
                p = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            p.seed = seed
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

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
            header = f"### {p.child} and {p.hen}: {p.magic} over {p.dust}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
