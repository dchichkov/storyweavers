#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/pin_wear_nog_reconciliation_fairy_tale.py
===========================================================================

A standalone storyworld in a fairy-tale style about a child, a pin, a thing to
wear, and a reconciliation with a small grumpy helper named Nog.

The domain is intentionally tiny and classical:
- a cloak or crown needs fixing before a festival
- a sharp pin can prick someone if used carelessly
- Nog, a little forest keeper, becomes upset when the wrong thing is borrowed
- a calm apology, a repaired item, and a shared gift bring reconciliation

The script follows the Storyweavers contract:
- self-contained stdlib script
- imports storyworlds/results.py eagerly
- exposes StoryParams, build_parser, resolve_params, generate, emit, main
- supports --all, -n, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
- includes Python reasonableness gates and an inline ASP twin
- produces world-driven prose and world-grounded Q&A
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    owner: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    torn: bool = False
    sharp: bool = False
    wearable: bool = False
    precious: bool = False
    friend: bool = False

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "queen", "woman", "princess"}
        male = {"boy", "father", "king", "man", "prince", "gnome"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"queen": "queen", "king": "king", "princess": "princess",
                "prince": "prince", "gnome": "Nog"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Setting:
    id: str
    scene: str
    place: str
    quiet: str

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
class Wearable:
    id: str
    label: str
    phrase: str
    purpose: str
    fit: str
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
class Pin:
    id: str
    label: str
    phrase: str
    sharp_word: str
    careless_word: str
    tags: set[str] = field(default_factory=set)
    sharp: bool = True

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
class Nog:
    id: str
    type: str
    label: str
    mood_line: str
    gift_line: str
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
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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


def _r_spoil(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["poked"] < THRESHOLD:
            continue
        sig = ("spoil", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if e.role == "wearable":
            e.meters["torn"] += 1
            out.append(f"The {e.label} was nicked and had to be mended.")
    return out


def _r_resent(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.memes["hurt"] < THRESHOLD or e.memes["hurt"].is_integer() is False:
            pass
        if e.memes["hurt"] < THRESHOLD:
            continue
        sig = ("resent", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["upset"] += 1
        out.append("")
    return out


CAUSAL_RULES = [Rule("spoil", "physical", _r_spoil), Rule("resent", "social", _r_resent)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def wear_at_risk(pin: Pin, item: Wearable) -> bool:
    return pin.sharp and item.fit in {"cloak", "crown", "dress"}


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def is_reconciled(response: Response, delay: int) -> bool:
    return response.power >= (1 + delay)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for pid, pin in PINS.items():
            for wid, wear in WEARABLES.items():
                if wear_at_risk(pin, wear):
                    combos.append((sid, pid, wid))
    return combos


def setup(world: World, child: Entity, nog: Entity, item: Entity, pin: Entity) -> None:
    child.memes["hope"] += 1
    nog.memes["grumpy"] += 1
    world.say(
        f"On a still evening in {world.setting.scene}, {child.id} found a fine "
        f"{item.label} that was meant to be worn at the feast."
    )
    world.say(
        f"Near the old gate, {nog.label} sat in his mossy nook, guarding a little "
        f"bundle of berries and a silver {pin.label}."
    )


def want_wear(world: World, child: Entity, item: Entity) -> None:
    child.memes["desire"] += 1
    world.say(
        f'{child.id} wanted to wear the {item.label} at once, for it shone like '
        f"a moonbeam. {child.pronoun().capitalize()} lifted it carefully."
    )


def borrow_pin(world: World, child: Entity, pin: Entity, item: Entity) -> None:
    world.say(
        f'{child.id} borrowed the {pin.label} to fasten the {item.label}, '
        f"hoping to look bright for the feast."
    )


def prick(world: World, child: Entity, pin: Entity, item: Entity) -> None:
    child.meters["pricked"] += 1
    child.memes["hurt"] += 1
    item.meters["poked"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But the {pin.label} slipped. {child.id} gave a tiny yelp, and the sharp "
        f"little point pricked a finger before the clasp could hold."
    )


def nog_worries(world: World, nog: Entity, child: Entity, item: Entity) -> None:
    nog.memes["sad"] += 1
    world.say(
        f"{nog.label} frowned beneath the willow. \"That {pin.label} is mine,\" "
        f"he muttered. \"And the {item.label} should be worn kindly, not rushed.\""
    )
    world.say(
        f"{child.id} looked down, feeling the wrongness of it at once."
    )


def apology(world: World, child: Entity, nog: Entity, pin: Pin) -> None:
    child.memes["ashamed"] += 1
    child.memes["kind"] += 1
    nog.memes["soft"] += 1
    world.say(
        f'{child.id} bowed low. \"I am sorry, Nog. I should have asked before I '
        f"took the {pin.label}.\""
    )
    world.say(
        f'Nog blinked, and the hard look left his face. \"Aye,\" he said more '
        f"gently, \"that was a brave sorry.\""
    )


def mend(world: World, child: Entity, nog: Entity, item: Entity, response: Response) -> None:
    item.meters["torn"] = 0.0
    body = response.text.replace("{target}", item.label)
    world.say(
        f"Together they {body}, and the little tear disappeared like a secret in "
        f"the grass."
    )
    world.say(
        f"{nog.label} nodded, and {child.id} smiled, for the {item.label} was whole "
        f"again."
    )


def gift(world: World, child: Entity, nog: Entity, item: Entity) -> None:
    child.memes["joy"] += 1
    nog.memes["joy"] += 1
    world.say(
        f"To mend the hurt in the heart as well as the cloth, {child.id} tucked "
        f"the silver {item.label} back into Nog's hand, and Nog gave a sprig of "
        f"wild mint in return."
    )
    world.say(
        f"Then they walked to the feast together, reconciled, with no grudge left "
        f"between them."
    )


def fail_delay(world: World, child: Entity, nog: Entity, item: Entity) -> None:
    world.say(
        f"The tear stayed open, and the feast bells rang too soon. {child.id} had "
        f"to go on without the bright {item.label}, sad and sorry."
    )


SETTING_REGISTRY = {
    "forest": Setting("forest", "a moonlit forest", "the old gate", "soft and still"),
    "castle": Setting("castle", "a castle courtyard", "the courtyard well", "bright and echoing"),
    "meadow": Setting("meadow", "a wildflower meadow", "the stone bench", "golden and wide"),
}

WEARABLES = {
    "cloak": Wearable("cloak", "cloak", "a velvet cloak", "to wear at the feast", "cloak", {"cloak"}),
    "crown": Wearable("crown", "crown", "a little gilded crown", "to wear at the welcome song", "crown", {"crown"}),
    "dress": Wearable("dress", "dress", "a blue dancing dress", "to wear at dusk", "dress", {"dress"}),
}

PINS = {
    "silverpin": Pin("silverpin", "silver pin", "a silver pin", "sharp as a thimble thorn", "careless as a dropped needle", {"pin"}),
    "rosepin": Pin("rosepin", "rose pin", "a rose-tipped pin", "sharp as a briar", "quick and prickly", {"pin"}),
}

NOGS = {
    "nog": Nog("nog", "gnome", "Nog", "Nog wore a frown like a cap.", "Nog smiled and shared his mint.", {"nog"}),
}

RESPONSES = {
    "steady": Response("steady", 3, 3, "mended the {target} with a steady stitch", "tried to mend the {target}, but it stayed broken", "mended the {target} with a steady stitch", {"mend"}),
    "gentle": Response("gentle", 2, 2, "patched the {target} with gentle care", "patched the {target}, but the work came undone", "patched the {target} with gentle care", {"mend"}),
    "goldthread": Response("goldthread", 3, 4, "repaired the {target} with gold thread", "repaired the {target}, yet the tears were too stubborn", "repaired the {target} with gold thread", {"mend"}),
}

GIRL_NAMES = ["Ava", "Mina", "Elin", "Sara", "Iris"]
BOY_NAMES = ["Finn", "Evan", "Theo", "Oren", "Perrin"]
TRAITS = ["curious", "kind", "brave", "gentle", "patient"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    wearable: str
    pin: str
    nog: str
    child: str
    child_gender: str
    trait: str
    response: str
    delay: int = 0
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


def tell(params: StoryParams) -> World:
    world = World(SETTING_REGISTRY[params.setting])
    child = world.add(Entity(id=params.child, kind="character", type=params.child_gender, role="child", traits=[params.trait]))
    nog = world.add(Entity(id="Nog", kind="character", type="gnome", role="friend", label="Nog", traits=["grumpy"]))
    item = world.add(Entity(id=params.wearable, type="thing", label=WEARABLES[params.wearable].label, role="wearable", wearable=True, torn=False))
    pin = world.add(Entity(id=params.pin, type="thing", label=PINS[params.pin].label, role="pin", sharp=True))
    setup(world, child, nog, item, pin)
    world.para()
    want_wear(world, child, item)
    borrow_pin(world, child, pin, item)
    prick(world, child, pin, item)
    nog_worries(world, nog, child, item)
    world.para()
    apology(world, child, nog, PINS[params.pin])
    if is_reconciled(RESPONSES[params.response], params.delay):
        mend(world, child, nog, item, RESPONSES[params.response])
        gift(world, child, nog, item)
        outcome = "reconciled"
    else:
        fail_delay(world, child, nog, item)
        outcome = "unfixed"
    world.facts.update(child=child, nog=nog, item=item, pin=pin, outcome=outcome, response=RESPONSES[params.response], delay=params.delay)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child, item = f["child"], f["item"]
    return [
        f'Write a fairy tale for a young child that includes the words "pin", "wear", and "nog".',
        f"Tell a gentle story about {child.id} who wants to wear a {item.label} and has to make peace with Nog after borrowing a pin.",
        f"Write a small reconciliation story in a fairy-tale style where a child apologizes, mends a worn thing, and ends the day friends again.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, nog, item = f["child"], f["nog"], f["item"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id} and Nog, who meet in a little fairy-tale forest. The child wants to wear a beautiful {item.label}, and the day turns on how they treat each other."),
        (f"What did {child.id} want to do?",
         f"{child.id} wanted to wear the {item.label} at the feast. That wish is what led them to borrow a pin and try to fasten it."),
        (f"Why did Nog feel upset?",
         f"Nog felt upset because his pin was taken without asking. He wanted the child to speak kindly and use the pin carefully."),
    ]
    if f["outcome"] == "reconciled":
        qa.append((
            "How did they become friends again?",
            f"{child.id} apologized, and Nog softened. Then they mended the {item.label} together and shared a little mint, so the hurt was healed as well as the tear."
        ))
    else:
        qa.append((
            "How did the story end?",
            f"The child said sorry, but the mending did not finish in time. The friendship was not fully mended before the feast bells rang."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["pin"].tags) | set(world.facts["item"].traits if hasattr(world.facts["item"], "traits") else [])
    tags |= {"pin", "nog"}
    items = []
    if "pin" in tags:
        items.append(("What is a pin?", "A pin is a very small sharp tool. People use it to fasten cloth, but it must be handled carefully so it does not prick anyone."))
    if "nog" in tags:
        items.append(("Who is Nog?", "Nog is a little forest gnome in this story. He begins grumpy, but he can become gentle again when someone apologizes and makes things right."))
    items.append(("What does reconcile mean?", "To reconcile means to make peace after a hurt or a quarrel. People listen, apologize, and then choose kindness again."))
    return items


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
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


def explain_rejection(pin: Pin, wear: Wearable) -> str:
    return f"(No story: the {pin.label} and the {wear.label} fit a risky tale, but this tiny world only tells stories where the pin can prick the thing worn.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    return f"(Refusing response '{rid}': it scores too low on common sense (sense={r.sense} < {SENSE_MIN}).)"


def hazard_ok(pin: Pin, wear: Wearable) -> bool:
    return pin.sharp and wear.fit in {"cloak", "crown", "dress"}


def outcome_of(params: StoryParams) -> str:
    return "reconciled" if is_reconciled(RESPONSES[params.response], params.delay) else "unfixed"


CURATED = [
    StoryParams("forest", "cloak", "silverpin", "nog", "Ava", "girl", "kind", "steady", 0),
    StoryParams("castle", "crown", "rosepin", "nog", "Finn", "boy", "gentle", "goldthread", 0),
    StoryParams("meadow", "dress", "silverpin", "nog", "Mina", "girl", "brave", "gentle", 1),
]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, p, w) for s in SETTING_REGISTRY for p in PINS for w in WEARABLES if hazard_ok(PINS[p], WEARABLES[w])]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale storyworld about a pin, a thing to wear, and reconciliation with Nog.")
    ap.add_argument("--setting", choices=SETTING_REGISTRY)
    ap.add_argument("--wearable", choices=WEARABLES)
    ap.add_argument("--pin", choices=PINS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.pin is None or c[1] == args.pin)
              and (args.wearable is None or c[2] == args.wearable)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, pin, wear = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in RESPONSES.values() if r.sense >= SENSE_MIN))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 1)
    return StoryParams(setting, wear, pin, "nog", name, gender, trait, response, delay)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


ASP_RULES = r"""
hazard(P, W) :- sharp(P), wearable(W).
valid(S, P, W) :- setting(S), pin(P), wear(W), hazard(P, W).
reconciled(R) :- response(R), sense(R, S), sense_min(M), S >= M.
outcome(reconciled) :- chosen_response(R), reconciled(R).
outcome(unfixed) :- chosen_response(R), response(R), not reconciled(R).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTING_REGISTRY:
        lines.append(asp.fact("setting", sid))
    for pid, p in PINS.items():
        lines.append(asp.fact("pin", pid))
        if p.sharp:
            lines.append(asp.fact("sharp", pid))
    for wid in WEARABLES:
        lines.append(asp.fact("wear", wid))
        lines.append(asp.fact("wearable", wid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
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
        print("MISMATCH in gate")
    sample = generate(CURATED[0])
    if not sample.story.strip():
        rc = 1
        print("MISMATCH: empty story")
    else:
        print("OK: generate() smoke test produced story text.")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show reconciled/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for s, p, w in asp_valid_combos():
            print(f"  {s:8} {p:10} {w}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
