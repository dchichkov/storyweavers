#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/prong_magic_sharing_foreshadowing_comedy.py
============================================================================

A small comedic storyworld about a child, a magical prong, sharing, and a
foreshadowed mishap that turns into a funny, gentle ending.

The domain premise:
- A child finds a tiny magic prong in the kitchen.
- Magic makes ordinary snack-sharing go a little wrong in advance: the prong
  predicts or causes a silly spill if used carelessly.
- A sibling or friend warns about it, sharing becomes part of the solution, and
  the ending proves the lesson with a laugh.

This script is standalone, stdlib-only, and follows the Storyweavers contract.
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
COMEDY_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
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
class Setting:
    id: str
    place: str
    surface: str
    food: str
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
class MagicProng:
    id: str
    label: str
    noun: str
    sparkle: str
    predicts: str
    shares: bool = True
    foreshadows: bool = True
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
class Snack:
    id: str
    label: str
    noun: str
    spillable: bool
    sticky: bool = False
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


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["sly_magic"] < THRESHOLD:
            continue
        sig = ("spill", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "table" in world.entities:
            world.get("table").meters["mess"] += 1
        for ch in list(world.entities.values()):
            if ch.kind == "character":
                ch.memes["surprise"] += 1
        out.append("__spill__")
    return out


def _r_share(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.memes["sharing"] < THRESHOLD:
            continue
        sig = ("share", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["joy"] += 1
        out.append("__share__")
    return out


CAUSAL_RULES = [Rule("spill", "physical", _r_spill), Rule("share", "social", _r_share)]


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


def reasonableness_gate(prong: MagicProng, snack: Snack) -> bool:
    return prong.foreshadows and prong.shares and snack.spillable


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= COMEDY_MIN]


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def predict_splash(world: World, prong_id: str) -> dict:
    sim = world.copy()
    sim.get(prong_id).meters["sly_magic"] += 1
    propagate(sim, narrate=False)
    return {
        "mess": sim.get("table").meters["mess"] if "table" in sim.entities else 0,
        "surprise": sum(e.memes["surprise"] for e in sim.entities.values()),
    }


def _use_prong(world: World, prong: Entity) -> None:
    prong.meters["sly_magic"] += 1
    propagate(world, narrate=False)


def setup(world: World, kid: Entity, other: Entity, setting: Setting) -> None:
    kid.memes["curiosity"] += 1
    other.memes["warmth"] += 1
    world.say(
        f"At {setting.place}, {kid.id} spotted {setting.surface} and a tiny snack table "
        f"waiting beside it. {setting.mood.capitalize()}, the room felt ready for a joke."
    )
    world.say(
        f'{kid.id} whispered, "What if I try the magic prong?" and {other.id} looked up at once.'
    )


def tempt(world: World, kid: Entity, prong: MagicProng, snack: Snack) -> None:
    kid.memes["giddiness"] += 1
    world.say(
        f'{kid.id} held up the {prong.label}. It had {prong.sparkle}, '
        f'and everybody could tell it wanted to do something silly with the {snack.label}.'
    )
    world.say(f'The prong even seemed to hint that a mess might happen before anyone finished smiling.')


def warn(world: World, other: Entity, kid: Entity, prong: MagicProng, snack: Snack) -> None:
    pred = predict_splash(world, "prong")
    other.memes["caution"] += 1
    world.facts["predicted_mess"] = pred["mess"]
    world.say(
        f'{other.id} frowned a tiny bit. "That {prong.noun} looks magical, but if you wave it over '
        f'the {snack.label}, I think the snack will go flying. Maybe share first, then sparkle later."'
    )


def do_magic(world: World, kid: Entity, prong: MagicProng) -> None:
    world.say(f'{kid.id} grinned, touched the {prong.label}, and the whole thing went zzzip!')


def spill_scene(world: World, snack: Snack) -> None:
    if "table" in world.entities:
        world.get("table").meters["mess"] += 1
    world.say(
        f'Then the {snack.label} flipped, a little splash of {snack.noun} landed on the table, '
        f'and the magic prong made a proud little twang as if that had been the plan all along.'
    )
    world.say("For a second everyone stared. Then everybody laughed, because the prong had been right in the funniest way.")


def share_fix(world: World, kid: Entity, other: Entity, snack: Snack, prong: MagicProng) -> None:
    kid.memes["sharing"] += 1
    other.memes["sharing"] += 1
    kid.memes["joy"] += 1
    other.memes["joy"] += 1
    world.say(
        f'{other.id} slid the plate closer. "{prong.label} can have a bite too," {other.id} said. '
        f'{kid.id} split the snack into neat pieces and shared them instead of showing off.'
    )
    world.say(
        f'This time the {prong.noun} only sparkled. No flying crumbs, no extra mess, just two happy kids and a very relieved table.'
    )


def ending(world: World, kid: Entity, other: Entity, setting: Setting, snack: Snack, prong: MagicProng) -> None:
    world.say(
        f"By the end, {kid.id} kept the {prong.label} in one hand and the shared snack in the other. "
        f"{setting.place.capitalize()} stayed cheerful, and the funniest magic of all was that sharing fixed the whole scene."
    )


def tell(setting: Setting, prong: MagicProng, snack: Snack,
         kid_name: str = "Nora", kid_gender: str = "girl",
         other_name: str = "Milo", other_gender: str = "boy",
         parent_type: str = "mother", response: Response | None = None) -> World:
    world = World()
    kid = world.add(Entity(id=kid_name, kind="character", type=kid_gender, role="curious"))
    other = world.add(Entity(id=other_name, kind="character", type=other_gender, role="helper"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    table = world.add(Entity(id="table", type="thing", label="the snack table"))
    p = world.add(Entity(id="prong", type="thing", label=prong.label))
    s = world.add(Entity(id="snack", type="thing", label=snack.label))
    response = response or best_response()

    setup(world, kid, other, setting)
    world.para()
    tempt(world, kid, prong, snack)
    warn(world, other, kid, prong, snack)

    if reasonableness_gate(prong, snack):
        do_magic(world, kid, p)
        spill_scene(world, snack)
        world.para()
        if response.power >= 1:
            kid.memes["relief"] += 1
            other.memes["relief"] += 1
            world.say(
                f"{parent.label_word.capitalize()} came in laughing and wiped the table with a napkin in one sweep. "
                f'{parent.pronoun().capitalize()} said the mess was small enough to joke about.'
            )
            world.say(
                f'"Next time," {parent.label_word} said, "share the snack first, and let the prong do magic on an empty plate."'
            )
            share_fix(world, kid, other, snack, prong)
        else:
            world.say(f"{parent.label_word.capitalize()} came in, but the joke had already gotten too sticky to clean up quickly.")
    else:
        world.say("The story refused to wobble, because this setup had no honest magic-mess to make.")

    world.para()
    ending(world, kid, other, setting, snack, prong)
    world.facts.update(
        kid=kid, other=other, parent=parent, setting=setting, prong_cfg=prong,
        snack_cfg=snack, table=table, response=response,
        mess=table.meters["mess"] >= THRESHOLD,
        shared=kid.memes["sharing"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "kitchen": Setting("kitchen", "the kitchen", "the shiny table", "a plate of crackers", "bright"),
    "sunroom": Setting("sunroom", "the sunroom", "the round table", "a bowl of grapes", "sunny"),
    "picnic": Setting("picnic", "the picnic blanket", "the blanket", "a basket of cookies", "breezy"),
}

PRONGS = {
    "fork": MagicProng("fork", "magic fork", "fork", "a glittery wobble", "it could predict a splash"),
    "prong": MagicProng("prong", "magic prong", "prong", "a tiny blue spark", "it could foresee a crumb storm"),
    "tuning": MagicProng("tuning", "magic tuning prong", "prong", "a musical shimmer", "it knew when snacks were about to tip"),
}

SNACKS = {
    "crackers": Snack("crackers", "crackers", "crumbs", True),
    "grapes": Snack("grapes", "grapes", "juice", True),
    "cookies": Snack("cookies", "cookies", "crumbs", True, sticky=False),
}

RESPONSES = {
    "napkin": Response("napkin", 3, 3, "wiped the table with a napkin and rescued the snack from the spill",
                       "tried to wipe the table, but the mess was too funny to stop",
                       "wiped the table with a napkin"),
    "plate_share": Response("plate_share", 2, 2, "moved the snack into two plates and shared it neatly",
                            "moved too slowly to beat the crumbs",
                            "moved the snack into two plates and shared it"),
    "laugh": Response("laugh", 2, 1, "laughed first, then cleaned up with a smile",
                      "laughed, but the crumbs stayed put",
                      "laughed first, then cleaned up"),
}

GIRL_NAMES = ["Nora", "Lily", "Mia", "Zoe", "Ava", "Ella", "Ruby", "Maya"]
BOY_NAMES = ["Milo", "Finn", "Theo", "Ben", "Leo", "Sam", "Eli", "Noah"]
TRAITS = ["curious", "silly", "gentle", "chatty", "clever"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid in SETTINGS:
        for pid in PRONGS:
            for snack in SNACKS:
                if reasonableness_gate(PRONGS[pid], SNACKS[snack]):
                    out.append((sid, pid, snack))
    return out


@dataclass
@dataclass
class StoryParams:
    setting: str
    prong: str
    snack: str
    kid: str
    kid_gender: str
    other: str
    other_gender: str
    parent: str
    trait: str
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
    "fork": [("What is a fork?", "A fork is a tool with prongs that people use to pick up food.")],
    "prong": [("What is a prong?", "A prong is one pointy part of a fork or similar tool.")],
    "crumbs": [("What are crumbs?", "Crumbs are little pieces of dry food that fall off snacks like crackers and cookies.")],
    "juice": [("What is juice?", "Juice is a sweet drink made from fruit, and it can spill easily.")],
    "sharing": [("Why is sharing nice?", "Sharing is nice because it lets more than one person enjoy something and can make people feel included.")],
    "magic": [("What makes something magical in a story?", "In a story, magic is something surprising that seems impossible but still feels fun and playful.")],
}

KNOWLEDGE_ORDER = ["prong", "fork", "crumbs", "juice", "sharing", "magic"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a comedy story for a young child that includes the word "prong" and a magic object that causes a foreshadowed snack mishap.',
        f"Tell a funny story where {f['kid'].id} wants to use a magic prong near {f['snack_cfg'].label}, but a friend warns about what will happen and they end up sharing instead.",
        f"Write a playful story with foreshadowing, magic, and sharing where the first spark points to a silly spill and the ending proves everyone can laugh about it.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    kid, other, parent = f["kid"], f["other"], f["parent"]
    snack, prong, setting = f["snack_cfg"], f["prong_cfg"], f["setting"]
    qa = [
        ("Who is the story about?",
         f"It is about {kid.id} and {other.id}, who are playing near the snack table. Their grown-up comes in to help when the magic gets silly."),
        ("What did the child want to use?",
         f"{kid.id} wanted to use the {prong.label}. It looked sparkly and promising, which made it tempting to try near the snack."),
        ("What did the friend warn about?",
         f"{other.id} warned that the {prong.noun} might send the snack flying and make a mess. That warning was the story's foreshadowing, because it happened almost right away."),
    ]
    if f["mess"]:
        qa.append((
            "What happened when the prong was used?",
            f"The snack tipped and made a little mess on the table. The funny part is that the warning was right, so everyone could laugh after the surprise."
        ))
    if f["shared"]:
        qa.append((
            "How did they fix the problem?",
            f"They shared the snack into neat pieces and cleaned the table together. That turned the whole joke into a happy ending instead of a bigger mess."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with {kid.id} holding the magic prong and sharing the snack, while {setting.place} stayed cheerful. The ending proves the comedy was about choosing sharing over showing off."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {world.facts["prong_cfg"].id, world.facts["snack_cfg"].id, "sharing", "magic"}
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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("kitchen", "prong", "crackers", "Nora", "girl", "Milo", "boy", "mother", "curious"),
    StoryParams("sunroom", "fork", "grapes", "Lily", "girl", "Theo", "boy", "father", "silly"),
    StoryParams("picnic", "tuning", "cookies", "Ben", "boy", "Mia", "girl", "mother", "gentle"),
]


def explain_rejection(prong: MagicProng, snack: Snack) -> str:
    return f"(No story: this prong and snack do not make a good comic foreshadowing problem.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, p in PRONGS.items():
        lines.append(asp.fact("prong", pid))
        if p.foreshadows:
            lines.append(asp.fact("foreshadows", pid))
        if p.shares:
            lines.append(asp.fact("shares", pid))
    for sid, s in SNACKS.items():
        lines.append(asp.fact("snack", sid))
        if s.spillable:
            lines.append(asp.fact("spillable", sid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", COMEDY_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, P, N) :- setting(S), prong(P), snack(N), foreshadows(P), shares(P), spillable(N).
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in gate")
    if set(asp_sensible()) == {r.id for r in sensible_responses()}:
        print("OK: sensible responses match.")
    else:
        rc = 1
        print("MISMATCH in sensible responses")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, prong=None, snack=None, kid=None, kid_gender=None, other=None, other_gender=None, parent=None, trait=None), random.Random(7)))
        _ = sample.story
        print("OK: story generation smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld about a magic prong, sharing, and foreshadowed snack chaos.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--prong", choices=PRONGS)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--kid")
    ap.add_argument("--kid-gender", choices=["girl", "boy"])
    ap.add_argument("--other")
    ap.add_argument("--other-gender", choices=["girl", "boy"])
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


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.prong and args.snack and not reasonableness_gate(PRONGS[args.prong], SNACKS[args.snack]):
        raise StoryError(explain_rejection(PRONGS[args.prong], SNACKS[args.snack]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.prong is None or c[1] == args.prong)
              and (args.snack is None or c[2] == args.snack)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, prong, snack = rng.choice(sorted(combos))
    kg = args.kid_gender or rng.choice(["girl", "boy"])
    og = args.other_gender or ("boy" if kg == "girl" and rng.random() < 0.5 else "girl")
    kid = args.kid or _pick_name(rng, kg)
    other = args.other or _pick_name(rng, og)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(setting, prong, snack, kid, kg, other, og, parent, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], PRONGS[params.prong], SNACKS[params.snack],
                 params.kid, params.kid_gender, params.other, params.other_gender,
                 params.parent)
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
        print(asp_program(show="#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        for s, p, n in asp_valid_combos():
            print(f"  {s:8} {p:8} {n}")
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
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.kid} & {p.other}: {p.prong} with {p.snack} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
