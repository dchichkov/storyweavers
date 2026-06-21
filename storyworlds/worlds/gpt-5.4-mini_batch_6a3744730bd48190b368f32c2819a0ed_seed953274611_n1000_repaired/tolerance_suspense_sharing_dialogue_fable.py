#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/tolerance_suspense_sharing_dialogue_fable.py
=============================================================================

A tiny fable storyworld about two forest neighbors, one scarce resource, a tense
moment, a choice to share, and a lesson in tolerance. The world is designed to
generate small, complete stories with suspense, dialogue, and an ending image
that proves what changed.

Premise
-------
A dry summer makes one clear pool the only water left in a shared glade. Two
animals want the same drinking spot. One of them is faster and bolder; the other
is calmer and better at noticing signs. A close call, a conversation, and a
choice to share lead to a fable-style lesson about tolerance.

This file is standalone and uses only the Python standard library plus the
shared storyworld results API. ASP support is inline and imported lazily.
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
SUSPENSE_AT = 1.0


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
        if self.type in {"rabbit", "mouse", "fox", "crow"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"hare", "badger", "deer"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class CharacterSpec:
    id: str
    type: str
    label: str
    trait: str
    role: str
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


@dataclass
class WaterSource:
    id: str
    label: str
    sparkle: str
    hidden: bool = False
    shared: bool = True
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


@dataclass
class Need:
    id: str
    label: str
    reason: str
    urgency: int
    satisfied_by_sharing: bool = True
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


@dataclass
class Response:
    id: str
    sense: int
    kindness: int
    power: int
    text: str
    fail: str
    qa_text: str
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
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class StoryParams:
    grove: str
    hero: str
    hero_type: str
    hero_trait: str
    challenger: str
    challenger_type: str
    challenger_trait: str
    source: str
    need: str
    response: str
    secret: bool
    delay: int = 0
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
class Rule:
    name: str
    apply: Callable[[World], list[str]]
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


def _r_tension(world: World) -> list[str]:
    out: list[str] = []
    source = world.get("source")
    if source.meters["hidden"] < THRESHOLD:
        return out
    for cid in ("hero", "challenger"):
        c = world.get(cid)
        sig = ("tension", cid)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        c.memes["unease"] += 1
        world.get("glade").meters["tension"] += 1
        out.append("")
    return out


def _r_share(world: World) -> list[str]:
    if world.get("bowl").meters["shared"] < THRESHOLD:
        return []
    sig = ("share",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("glade").meters["peace"] += 1
    world.get("hero").memes["tolerance"] += 1
    world.get("challenger").memes["tolerance"] += 1
    return []


CAUSAL_RULES = [Rule("tension", _r_tension), Rule("share", _r_share)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    changed = True
    out: list[str] = []
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            got = rule.apply(world)
            if got:
                changed = True
                out.extend(got)
    if narrate:
        for s in out:
            world.say(s)
    return out


def hazard_at_risk(source: WaterSource, need: Need) -> bool:
    return source.shared and need.satisfied_by_sharing


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def need_urgency(delay: int, secret: bool) -> int:
    return 2 + delay + (1 if secret else 0)


def outcome_of(params: StoryParams) -> str:
    resp = RESPONSES[params.response]
    urgency = need_urgency(params.delay, params.secret)
    return "shared" if resp.power >= urgency else "lost"


def predict_sharing(world: World, delay: int, resp: Response) -> dict:
    sim = world.copy()
    sim.get("source").meters["hidden"] = 1
    sim.get("bowl").meters["shared"] = 1 if resp.power >= need_urgency(delay, True) else 0
    propagate(sim, narrate=False)
    return {
        "peace": sim.get("glade").meters["peace"],
        "tension": sim.get("glade").meters["tension"],
    }


def setup(world: World, hero: Entity, challenger: Entity, grove: str, source: WaterSource, need: Need) -> None:
    hero.memes["hope"] += 1
    challenger.memes["hope"] += 1
    world.add(Entity(id="glade", type="place", label=grove))
    world.add(Entity(id="source", type="thing", label=source.label))
    world.add(Entity(id="bowl", type="thing", label="the shared bowl"))
    world.say(
        f"At the edge of the {grove}, {hero.id} and {challenger.id} found {source.label}, "
        f"the only cool water left in the dry land."
    )
    world.say(
        f"Both were thirsty, because {need.reason}. The pool looked small, and the day felt long."
    )


def suspense(world: World, hero: Entity, challenger: Entity, source: WaterSource) -> None:
    world.get("source").meters["hidden"] = 1
    hero.memes["worry"] += 1
    challenger.memes["worry"] += 1
    world.say(
        f"Then the water slipped under reeds and showed only one bright mouth of the pool. "
        f"{hero.id} stepped closer, and {challenger.id} held back."
    )
    world.say(
        f'"If you drink first, there may be none for me," {challenger.id} said softly.'
    )
    if source.hidden:
        world.say(
            f"The little pool shimmered, as if it were hiding a secret under the grass."
        )


def dialog(world: World, hero: Entity, challenger: Entity, response: Response) -> None:
    hero.memes["listening"] += 1
    challenger.memes["listening"] += 1
    world.say(
        f'"We can be patient," {hero.id} answered. "Or we can make the water last for both of us."'
    )
    world.say(
        f'"A fair share is kinder than a quick sip," {challenger.id} replied. '
        f'"That is the way of tolerance."'
    )


def choose_share(world: World, response: Response) -> None:
    world.get("bowl").meters["shared"] += 1
    world.say(
        f"Together they chose {response.text}."
    )


def share_success(world: World, hero: Entity, challenger: Entity, response: Response) -> None:
    world.get("glade").meters["peace"] += 1
    hero.memes["tolerance"] += 1
    challenger.memes["tolerance"] += 1
    world.say(
        f"The {response.qa_text}."
    )
    world.say(
        f"At once the dry hush around them felt smaller. {hero.id} drank first, then {challenger.id}, "
        f"and neither was left out."
    )
    world.say(
        f"By sunset they walked away side by side, and the little pool still had water reflecting the reeds."
    )


def share_fail(world: World, hero: Entity, challenger: Entity, response: Response) -> None:
    world.get("glade").meters["fear"] += 1
    world.say(
        f"But when they tried, {response.fail}."
    )
    world.say(
        f"The pool went quiet, and the waiting turned into regret."
    )


def tell(params: StoryParams) -> World:
    world = World()
    hero = world.add(Entity(
        id=params.hero, kind="character", type=params.hero_type, role="first",
        traits=[params.hero_trait],
    ))
    challenger = world.add(Entity(
        id=params.challenger, kind="character", type=params.challenger_type, role="second",
        traits=[params.challenger_trait],
    ))
    source = WATER_SOURCES[params.source]
    need = NEEDS[params.need]
    response = RESPONSES[params.response]
    setup(world, hero, challenger, params.grove, source, need)
    world.para()
    suspense(world, hero, challenger, source)
    dialog(world, hero, challenger, response)
    world.para()
    choose_share(world, response)
    if response.power >= need_urgency(params.delay, params.secret):
        share_success(world, hero, challenger, response)
        outcome = "shared"
    else:
        share_fail(world, hero, challenger, response)
        outcome = "lost"
    world.facts.update(
        hero=hero, challenger=challenger, source=source, need=need, response=response,
        grove=params.grove, outcome=outcome, delay=params.delay, secret=params.secret,
    )
    return world


WATER_SOURCES = {
    "pool": WaterSource(id="pool", label="a small pool", sparkle="shone like a silver coin", hidden=True, shared=True),
    "spring": WaterSource(id="spring", label="a spring in the rocks", sparkle="glittered under the moss", hidden=False, shared=True),
    "well": WaterSource(id="well", label="an old well", sparkle="winked in the shade", hidden=False, shared=True),
}

NEEDS = {
    "thirst": Need(id="thirst", label="thirst", reason="they had walked under the hot sun for hours", urgency=2),
    "journey": Need(id="journey", label="journey", reason="their journey back to the hill would be long", urgency=3),
    "garden": Need(id="garden", label="garden work", reason="they had been tending the thirsty garden all morning", urgency=2),
}

RESPONSES = {
    "share_odd": Response(
        id="share_odd", sense=3, kindness=4, power=2,
        text="they tipped the bowl back and forth, taking odd little turns",
        fail="the bowl tipped too fast, and one child drank while the other waited too long",
        qa_text="they shared the water in careful turns",
    ),
    "share_equal": Response(
        id="share_equal", sense=4, kindness=5, power=4,
        text="they filled the bowl and took equal sips from it",
        fail="the bowl was not enough for both, and the second sip came too late",
        qa_text="they shared the water equally",
    ),
    "share_ladle": Response(
        id="share_ladle", sense=5, kindness=5, power=5,
        text="they used a leaf like a ladle and passed it back and forth",
        fail="the leaf cracked, and the water spilled before both could drink",
        qa_text="they shared the water with a leaf ladle",
    ),
    "refuse": Response(
        id="refuse", sense=1, kindness=1, power=1,
        text="one of them tried to keep the water for one alone",
        fail="one of them kept the water, and the other was left dry",
        qa_text="they did not share at all",
    ),
}

SENSE_MIN = 2

GROVES = ["elm grove", "thorn grove", "oak hollow"]
CHARACTERS = [
    CharacterSpec(id="Mara", type="hare", label="Mara the hare", trait="quick", role="first"),
    CharacterSpec(id="Tobin", type="badger", label="Tobin the badger", trait="careful", role="second"),
    CharacterSpec(id="Nella", type="deer", label="Nella the deer", trait="gentle", role="first"),
    CharacterSpec(id="Pip", type="crow", label="Pip the crow", trait="watchful", role="second"),
]
CURATED = [
    StoryParams(grove="elm grove", hero="Mara", hero_type="hare", hero_trait="quick", challenger="Tobin", challenger_type="badger", challenger_trait="careful", source="pool", need="thirst", response="share_equal", secret=True, delay=0),
    StoryParams(grove="thorn grove", hero="Nella", hero_type="deer", hero_trait="gentle", challenger="Pip", challenger_type="crow", challenger_trait="watchful", source="spring", need="journey", response="share_ladle", secret=False, delay=1),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for g in WATER_SOURCES:
        for n in NEEDS:
            for r in RESPONSES:
                if hazard_at_risk(WATER_SOURCES[g], NEEDS[n]) and RESPONSES[r].sense >= SENSE_MIN:
                    combos.append((g, n, r))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny fable world about tolerance, suspense, sharing, and dialogue.")
    ap.add_argument("--grove", choices=WATER_SOURCES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type")
    ap.add_argument("--challenger")
    ap.add_argument("--challenger-type")
    ap.add_argument("--source", choices=WATER_SOURCES)
    ap.add_argument("--need", choices=NEEDS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], default=0)
    ap.add_argument("--secret", action="store_true")
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
        raise StoryError(f"(Refusing response '{args.response}': it is too weak for a fable of tolerance.)")
    combos = [c for c in valid_combos()
              if (args.grove is None or c[0] == args.grove)
              and (args.need is None or c[1] == args.need)
              and (args.source is None or c[0] == args.source)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    grove, need, response = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(["Mara", "Nella", "Fenn", "Lina"])
    challenger = args.challenger or rng.choice([n for n in ["Tobin", "Pip", "Orin", "Sela"] if n != hero])
    hero_type = args.hero_type or rng.choice(["hare", "deer", "mouse"])
    challenger_type = args.challenger_type or rng.choice(["badger", "crow", "fox"])
    source = args.source or grove if grove in WATER_SOURCES else "pool"
    secret = bool(args.secret or rng.choice([True, False]))
    return StoryParams(
        grove=grove, hero=hero, hero_type=hero_type, hero_trait="gentle",
        challenger=challenger, challenger_type=challenger_type, challenger_trait="careful",
        source=source, need=need, response=args.response or response,
        secret=secret, delay=args.delay,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fable for a young child that uses the word "tolerance" and includes suspense, sharing, and dialogue.',
        f"Tell a short animal story set in {f['grove']} where {f['hero'].id} and {f['challenger'].id} must share water and learn tolerance.",
        f"Write a gentle fable where two forest neighbors speak kindly, wait through a tense moment, and finish by sharing a scarce pool.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    return [
        ("Who was in the story?",
         f"It was about {f['hero'].id} and {f['challenger'].id}, two forest neighbors who both wanted the same water."),
        ("Why was the moment suspenseful?",
         f"The pool looked too small for both of them, so each one feared there might not be enough. That made the glade feel quiet and tense for a moment."),
        ("What did they do instead of arguing?",
         f"They talked to each other and chose to share the water. Their words slowed the moment down and helped them act with tolerance."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is tolerance?", "Tolerance means being patient and fair with someone else, even when you want the same thing. It helps two sides live together peacefully."),
        ("Why is sharing important?", "Sharing helps everyone get what they need without fighting. It is one way to be kind when something is scarce."),
        ("What is suspense?", "Suspense is the feeling that something important may happen soon. It makes a story feel tense because the result is not known yet."),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


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
    return "\n".join(lines)


ASP_RULES = r"""
shared_possible(G, N, R) :- grove(G), need(N), response(R),
                            source_shared(G), need_satisfiable(N), sensible(R).
outcome(shared) :- shared_possible(_, _, R), power(R, P), need_urgency(_, U), P >= U.
outcome(lost) :- shared_possible(_, _, R), power(R, P), need_urgency(_, U), P < U.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for g in WATER_SOURCES:
        lines.append(asp.fact("grove", g))
        lines.append(asp.fact("source_shared", g))
    for n in NEEDS:
        lines.append(asp.fact("need", n))
        lines.append(asp.fact("need_satisfiable", n))
    for r, resp in RESPONSES.items():
        lines.append(asp.fact("response", r))
        lines.append(asp.fact("sense", r, resp.sense))
        lines.append(asp.fact("power", r, resp.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show shared_possible/3."))
    return sorted(set(asp.atoms(model, "shared_possible")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([asp.fact("need_urgency", params.delay, need_urgency(params.delay, params.secret))])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    try:
        python = set(valid_combos())
        clingo = set(asp_valid_combos())
        ok = clingo == python
        sample = generate(CURATED[0])
        if not sample.story:
            ok = False
        if ok:
            print(f"OK: ASP gate matches valid_combos() ({len(python)} combos).")
            print("OK: normal story generation smoke test passed.")
            return 0
        print("Mismatch between ASP and Python gate.")
        return 1
    except Exception as err:
        print(f"VERIFY FAILED: {err}")
        return 1


def generate(params: StoryParams) -> StorySample:
    if params.response not in RESPONSES:
        raise StoryError("Unknown response.")
    if params.need not in NEEDS or params.source not in WATER_SOURCES:
        raise StoryError("Unknown source or need.")
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show shared_possible/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combinations.")
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
