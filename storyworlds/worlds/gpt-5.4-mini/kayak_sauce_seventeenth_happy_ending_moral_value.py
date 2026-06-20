#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/kayak_sauce_seventeenth_happy_ending_moral_value.py
====================================================================================

A standalone story world for a tiny ghost-story-style domain: a child, a spooky
hallway, a missing kayak, a mysterious pot of sauce, and the seventeenth room
door.  The simulation is built around typed entities with physical meters and
emotional memes, a small causal rule engine, a reasonableness gate, and a
state-driven renderer.

The seed asks for: kayak, sauce, seventeenth, Happy Ending, Moral Value,
Suspense, and a style close to a ghost story.

This world keeps the spooky mood, but the moral is gentle: when the children
stop, tell the truth, and ask for help, the mystery turns out safe and warm.
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
SUSPENSE_MIN = 1
MORAL_MIN = 1


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
    dark_place: str
    sound: str
    mood: str

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
class LostItem:
    id: str
    label: str
    phrase: str
    found_in: str
    clue: str
    risky: bool = False

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
class Cause:
    id: str
    sense: int
    power: int
    success: str
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


def _r_suspense(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["missing"] < THRESHOLD:
            continue
        sig = ("suspense", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "hall" in world.entities:
            world.get("hall").meters["spooky"] += 1
        for k in list(world.entities.values()):
            if k.kind == "character":
                k.memes["worry"] += 1
        out.append("__suspense__")
    return out


def _r_truth(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.memes["honest"] < THRESHOLD:
            continue
        sig = ("truth", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "adult" in world.entities:
            world.get("adult").memes["trust"] += 1
        out.append("__truth__")
    return out


def _r_warm(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["found"] < THRESHOLD:
            continue
        sig = ("warm", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["relief"] += 1
        out.append("__warm__")
    return out


CAUSAL_RULES = [
    Rule("suspense", "social", _r_suspense),
    Rule("truth", "social", _r_truth),
    Rule("warm", "social", _r_warm),
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


def hazard_at_risk(item: LostItem) -> bool:
    return item.risky


def sensible_causes() -> list[Cause]:
    return [c for c in CAUSES.values() if c.sense >= SUSPENSE_MIN]


def outcome_power(cause: Cause, item: LostItem, delay: int) -> bool:
    return cause.power >= (1 + delay if item.risky else 1)


def _search(world: World, child: Entity, item: Entity, narrate: bool = True) -> None:
    item.meters["missing"] += 1
    child.memes["worry"] += 1
    propagate(world, narrate=narrate)


def tell(setting: Setting, item: LostItem, cause: Cause, delay: int = 0,
         child_name: str = "Mina", child_type: str = "girl",
         parent_type: str = "mother", helper_name: str = "June") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=child_type, role="helper"))
    adult = world.add(Entity(id="Adult", kind="character", type=parent_type, role="adult", label="the grown-up"))
    hall = world.add(Entity(id="hall", type="hall", label="the long hall"))
    kayak = world.add(Entity(id="kayak", type="thing", label="the red kayak"))
    sauce = world.add(Entity(id="sauce", type="thing", label="the pot of sauce"))
    door = world.add(Entity(id="door17", type="thing", label="the seventeenth door"))

    child.memes["curious"] = 1
    helper.memes["cautious"] = 1
    world.facts["setting"] = setting
    world.facts["item"] = item
    world.facts["cause"] = cause
    world.facts["delay"] = delay

    world.say(
        f"On a windy evening, {child.id} and {helper.id} crept through {setting.place}. "
        f"{setting.sound.capitalize()} {setting.mood} as the lantern light shook."
    )
    world.say(
        f"They had come looking for {item.phrase}, because everyone had whispered it was hidden near {setting.dark_place}."
    )
    world.say(
        f"Then they reached {door.label}. It was the seventeenth door, and the air felt colder there."
    )

    world.para()
    child.memes["bravery"] += 1
    world.say(
        f"{child.id} whispered, 'I can hear something behind the door.' "
        f"{helper.id} pressed close and listened too."
    )
    world.say(
        f"A smell drifted out -- not smoke, but {sauce.label}. That made the mystery stranger, not safer."
    )

    world.para()
    _search(world, child, world.get("kayak"), narrate=False)
    child.memes["honest"] += 1
    world.say(
        f"At last, {child.id} found {world.get('kayak').label} beside the wall, beside {world.get('sauce').label} on a little tray."
    )
    world.say(
        f"{helper.id} noticed the kayak had been moved there for cleaning, and the sauce was for supper, not a spell."
    )

    world.para()
    if outcome_power(cause, item, delay):
        world.say(
            f"Just then the grown-up opened the door, smiled, and said, "
            f"'{cause.success}.'"
        )
        world.get("kayak").meters["found"] += 1
        world.get("sauce").meters["found"] += 1
        world.get("hall").meters["spooky"] = 0.0
        adult.memes["trust"] += 1
        child.memes["relief"] += 1
        helper.memes["relief"] += 1
        world.say(
            f"It was only a surprise supper being carried to the seventh table in the next room. "
            f"The children laughed because the scary hall had been trying to hide an ordinary kindness."
        )
        world.para()
        world.say(
            f"{adult.label_word.capitalize()} told them the moral right away: 'If something feels spooky, "
            f"stop, look, and tell the truth. Most mysteries are smaller when a grown-up can help.'"
        )
        world.say(
            f"So {child.id} and {helper.id} carried the {item.label} together, while the sauce warmed the house instead of frightening it."
        )
    else:
        world.say(
            f"The grown-up came at last, but {cause.fail}."
        )
        world.get("hall").meters["spooky"] += 1
        world.say(
            f"Still, {child.id} spoke honestly, and that honest voice helped the grown-up find the way."
        )
        world.get("kayak").meters["found"] += 1
        world.get("sauce").meters["found"] += 1
        world.get("hall").meters["spooky"] = 0.0
        child.memes["relief"] += 1
        helper.memes["relief"] += 1
        world.say(
            f"In the end, they discovered the kayak had only been tucked away, and the sauce was for a friendly dinner."
        )

    world.facts.update(
        child=child,
        helper=helper,
        adult=adult,
        kayak=world.get("kayak"),
        sauce=world.get("sauce"),
        door=door,
        hall=hall,
        outcome="happy",
    )
    return world


SETTINGS = {
    "old_house": Setting("old_house", "the old house", "the seventeenth door", "the boards sighed", "ghostly"),
    "dock": Setting("dock", "the dock house", "the dark storage room", "the ropes tapped", "quiet"),
    "boathouse": Setting("boathouse", "the boathouse", "the back room", "the windows creaked", "moonlit"),
}

ITEMS = {
    "kayak": LostItem("kayak", "kayak", "the kayak", "the back room", "a wet footprint trail", risky=True),
    "sauce": LostItem("sauce", "sauce", "the pot of sauce", "the kitchen shelf", "a warm smell in the air", risky=False),
    "seventeenth": LostItem("seventeenth", "seventeenth clue", "the seventeenth clue", "the old hall", "a chalk mark on the door", risky=True),
}

CAUSES = {
    "calm": Cause("calm", 2, 2, "it was only supper being carried from the kitchen", "it was too strange to explain at once", "explained that it was only supper and a friendly surprise"),
    "light": Cause("light", 1, 1, "the lantern light showed the way", "the lantern wobbled in the dark", "showed the lantern light was enough to see by"),
    "note": Cause("note", 2, 2, "the note told the truth", "the note was too torn to help", "read the note and found the truth"),
}

GIRL_NAMES = ["Mina", "Lily", "Nora", "Ivy", "Ada", "June"]
BOY_NAMES = ["Theo", "Finn", "Eli", "Noah", "Owen", "Ben"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for iid, item in ITEMS.items():
            if hazard_at_risk(item):
                combos.append((sid, iid, "calm"))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    item: str
    cause: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    parent: str
    delay: int = 0
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
    "kayak": [("What is a kayak?", "A kayak is a small boat that a person can paddle by hand.")],
    "sauce": [("What is sauce?", "Sauce is a tasty liquid or soft food that goes on other food to make it more delicious.")],
    "door": [("Why can a dark door feel scary?", "A dark door can feel scary because you cannot see what is behind it, so your mind guesses.")],
    "truth": [("Why should you tell the truth when you are scared?", "Telling the truth helps a grown-up understand what is happening, so they can help keep everyone safe.")],
    "moral": [("What is a moral in a story?", "A moral is the lesson a story teaches about how to act kindly or wisely.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a ghost-story-style tale for a young child that includes the words "kayak", "sauce", and "seventeenth".',
        f"Tell a spooky-but-kind story where {f['child'].id} searches for a kayak in an old house and learns a moral about telling the truth.",
        f"Write a suspenseful story with a happy ending about a child, a hidden kayak, and a mysterious smell of sauce near the seventeenth door.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    adult = f["adult"]
    item = f["item"]
    qa = [
        ("Who is the story about?", f"It is about {child.id} and {helper.id}, who went into the spooky house looking for a missing kayak."),
        ("Why did the hall feel spooky?", f"The hall felt spooky because the light was shaky and the seventeenth door made the place seem secret. The children also did not know yet that the smell of sauce belonged to an ordinary supper."),
        ("What did the children find near the door?", f"They found the kayak and a pot of sauce. That turned the mystery into something safe and normal."),
        ("What did the grown-up teach them?", f"{adult.label_word.capitalize()} taught them to stop, look, and tell the truth when something feels strange. That moral helped the children understand the mystery instead of being ruled by fear."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"kayak", "sauce", "door", "truth", "moral"}
    out: list[tuple[str, str]] = []
    for tag, items in KNOWLEDGE.items():
        if tag in tags:
            out.extend(items)
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
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("old_house", "kayak", "calm", "Mina", "girl", "June", "girl", "mother", 0),
    StoryParams("boathouse", "seventeenth", "calm", "Theo", "boy", "Finn", "boy", "father", 0),
]


def explain_rejection(item: LostItem) -> str:
    if not item.risky:
        return f"(No story: {item.label} is not mysterious enough for suspense; it would not drive the spooky turn.)"
    return "(No story: this combination does not support a suspenseful but safe story.)"


def outcome_of(params: StoryParams) -> str:
    return "happy"


ASP_RULES = r"""
valid(S, I) :- setting(S), item(I), risky(I).
outcome(happy) :- valid(_, _).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if item.risky:
            lines.append(asp.fact("risky", iid))
    for cid in CAUSES:
        lines.append(asp.fact("cause", cid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp as _asp  # lazy per contract
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH: ASP and Python gate differ.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny ghost-story style story world with kayak, sauce, and the seventeenth door.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], default=0)
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
    if args.item and not ITEMS[args.item].risky:
        raise StoryError(explain_rejection(ITEMS[args.item]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.item is None or c[1] == args.item)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, item, cause = rng.choice(combos)
    child_gender = rng.choice(["girl", "boy"])
    helper_gender = rng.choice(["girl", "boy"])
    child = rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    helper = rng.choice([n for n in (GIRL_NAMES if helper_gender == "girl" else BOY_NAMES) if n != child])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting, item, cause, child, child_gender, helper, helper_gender, parent, args.delay)


def tell(setting: Setting, item: LostItem, cause: Cause, delay: int,
         child_name: str, child_gender: str, helper_name: str, helper_gender: str, parent: str) -> World:
    return _tell_impl(setting, item, cause, delay, child_name, child_gender, helper_name, helper_gender, parent)


def _tell_impl(setting: Setting, item: LostItem, cause: Cause, delay: int,
               child_name: str, child_gender: str, helper_name: str, helper_gender: str, parent: str) -> World:
    return _build_world(setting, item, cause, delay, child_name, child_gender, helper_name, helper_gender, parent)


def _build_world(setting: Setting, item: LostItem, cause: Cause, delay: int,
                 child_name: str, child_gender: str, helper_name: str, helper_gender: str, parent: str) -> World:
    return _story(setting, item, cause, delay, child_name, child_gender, helper_name, helper_gender, parent)


def _story(setting: Setting, item: LostItem, cause: Cause, delay: int,
           child_name: str, child_gender: str, helper_name: str, helper_gender: str, parent: str) -> World:
    return story(setting, item, cause, delay, child_name, child_gender, helper_name, helper_gender, parent)


def story(setting: Setting, item: LostItem, cause: Cause, delay: int,
          child_name: str, child_gender: str, helper_name: str, helper_gender: str, parent: str) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    adult = world.add(Entity(id="Adult", kind="character", type=parent, role="adult", label="the grown-up"))
    world.add(Entity(id="hall", type="place", label="the long hall"))
    world.add(Entity(id="kayak", type="thing", label="the kayak"))
    world.add(Entity(id="sauce", type="thing", label="the sauce"))
    world.add(Entity(id="seventeenth", type="thing", label="the seventeenth door"))

    world.say(
        f"In {setting.place}, {child.id} and {helper.id} slipped along the dark hall. "
        f"{setting.sound.capitalize()} gave the place a ghostly feel."
    )
    world.say(
        f"They were searching for {item.phrase}, and the seventeenth door stood ahead like a secret."
    )
    world.para()
    world.say(
        f"{child.id} stopped when a warm smell of sauce drifted under the door. "
        f"{helper.id} held {helper.pronoun('possessive')} breath and listened."
    )
    child.memes["fear"] += 1
    helper.memes["suspense"] += 1
    world.get("hall").meters["spooky"] += 1
    _search(world, child, world.get("kayak"), narrate=False)
    world.para()
    world.say(
        f"Then they found the kayak tucked safely by the wall, and the sauce on a tray beside it."
    )
    world.say(
        f"The grown-up opened the seventeenth door and smiled, because the mystery had an ordinary answer."
    )
    world.get("kayak").meters["found"] += 1
    world.get("sauce").meters["found"] += 1
    child.memes["honest"] += 1
    adult.memes["trust"] += 1
    propagate(world, narrate=False)
    world.para()
    world.say(
        f"{adult.label_word.capitalize()} said, 'That is the moral: when something feels spooky, stop, tell the truth, and let a grown-up help.'"
    )
    world.say(
        f"So {child.id} and {helper.id} carried the kayak home together, while the sauce warmed the kitchen instead of the hall."
    )
    world.facts.update(child=child, helper=helper, adult=adult, item=item, setting=setting, cause=cause, delay=delay)
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], ITEMS[params.item], CAUSES[params.cause],
                 params.delay, params.child, params.child_gender,
                 params.helper, params.helper_gender, params.parent)
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
        print(asp_program("", "#show valid/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} valid combos.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
