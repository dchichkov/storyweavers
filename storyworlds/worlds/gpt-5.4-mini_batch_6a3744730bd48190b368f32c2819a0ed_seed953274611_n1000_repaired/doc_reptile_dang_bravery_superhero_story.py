#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/doc_reptile_dang_bravery_superhero_story.py
============================================================================

A standalone story world for a tiny superhero tale:

A brave kid and a small doctor visit a reptile rescue room. A loose reptile
creates a "dang" moment, but bravery, quick thinking, and a safe helper tool
turn the scare into a rescue and a proud ending.

Seed words: doc, reptile, dang
Feature: bravery
Style: superhero story
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
    role: str
    bravery: int = 0
    cautious: int = 0
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
class PlaceSpec:
    id: str
    label: str
    scene: str
    dark_spot: str
    afford: set[str] = field(default_factory=set)
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
class HazardSpec:
    id: str
    label: str
    phrase: str
    risk: str
    makes_problem: bool = True
    tags: set[str] = field(default_factory=set)
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


@dataclass
class ReptileSpec:
    id: str
    label: str
    phrase: str
    fact: str
    tags: set[str] = field(default_factory=set)
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


@dataclass
class ToolSpec:
    id: str
    label: str
    phrase: str
    effect: str
    power: int
    tags: set[str] = field(default_factory=set)
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


@dataclass
class StoryParams:
    place: str
    hero: str
    hero_type: str
    sidekick: str
    sidekick_type: str
    doc: str
    reptile: str
    hazard: str
    tool: str
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


PLACES = {
    "clinic": PlaceSpec(
        id="clinic",
        label="the clinic",
        scene="a bright rescue room with posters of capes on the wall",
        dark_spot="the corner behind the supply cart",
        afford={"snake", "lizard"},
    ),
    "museum": PlaceSpec(
        id="museum",
        label="the museum",
        scene="a shiny reptile show with glass cases and a silver stage",
        dark_spot="the space under the exhibit lamp",
        afford={"snake", "turtle"},
    ),
    "park": PlaceSpec(
        id="park",
        label="the park",
        scene="a pop-up hero fair with tents, banners, and a tiny stage",
        dark_spot="the shadow under the snack table",
        afford={"lizard", "turtle"},
    ),
}

HEROES = {
    "Mia": CharacterSpec("Mia", "girl", "Mia", "hero", bravery=6),
    "Noah": CharacterSpec("Noah", "boy", "Noah", "hero", bravery=6),
    "Zoe": CharacterSpec("Zoe", "girl", "Zoe", "hero", bravery=7),
    "Eli": CharacterSpec("Eli", "boy", "Eli", "hero", bravery=7),
}

SIDES = {
    "doc": CharacterSpec("Doc", "woman", "doc", "doctor", bravery=5, cautious=8),
    "dr_doc": CharacterSpec("Dr. Ray", "man", "Dr. Ray", "doctor", bravery=5, cautious=8),
    "doc_bloom": CharacterSpec("Doc Bloom", "woman", "Doc Bloom", "doctor", bravery=6, cautious=7),
}

REPTILES = {
    "lizard": ReptileSpec("lizard", "little lizard", "the lizard", "its tail can slip fast", {"lizard", "reptile"}),
    "snake": ReptileSpec("snake", "striped snake", "the snake", "its body can slide under things", {"snake", "reptile"}),
    "turtle": ReptileSpec("turtle", "tiny turtle", "the turtle", "its shell makes it slow but sturdy", {"turtle", "reptile"}),
}

HAZARDS = {
    "dang_stumble": HazardSpec("dang_stumble", "a loose step", "dang", "one bad step can make someone tumble", True, {"dang"}),
    "dang_slip": HazardSpec("dang_slip", "a slick floor", "dang", "a slick floor can send feet skidding", True, {"dang"}),
}

TOOLS = {
    "rope": ToolSpec("rope", "soft rope", "a soft rope", "safely guide the reptile", 3, {"rope"}),
    "shield": ToolSpec("shield", "hero shield", "a little hero shield", "block the path and keep everyone back", 4, {"shield"}),
    "carrier": ToolSpec("carrier", "rescue carrier", "a rescue carrier", "lift the reptile gently and close it up", 5, {"carrier"}),
}

CURATED = [
    StoryParams(
        place="clinic",
        hero="Mia",
        hero_type="girl",
        sidekick="Doc",
        sidekick_type="woman",
        doc="doc",
        reptile="lizard",
        hazard="dang_stumble",
        tool="carrier",
    ),
    StoryParams(
        place="museum",
        hero="Noah",
        hero_type="boy",
        sidekick="Dr. Ray",
        sidekick_type="man",
        doc="doc",
        reptile="snake",
        hazard="dang_slip",
        tool="shield",
    ),
    StoryParams(
        place="park",
        hero="Zoe",
        hero_type="girl",
        sidekick="Doc Bloom",
        sidekick_type="woman",
        doc="doc",
        reptile="turtle",
        hazard="dang_stumble",
        tool="rope",
    ),
]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place_id, place in PLACES.items():
        for reptile_id in REPTILES:
            if reptile_id not in place.afford:
                continue
            for hazard_id in HAZARDS:
                for tool_id in TOOLS:
                    out.append((place_id, reptile_id, hazard_id))
    return out


def hazard_at_risk(place: PlaceSpec, reptile: ReptileSpec, hazard: HazardSpec) -> bool:
    return reptile.id in place.afford and hazard.makes_problem


def _r_bravery(world: World) -> list[str]:
    out = []
    hero = world.get("hero")
    if hero.memes["bravery"] >= THRESHOLD and hero.meters["fear"] >= THRESHOLD:
        sig = ("bravery", hero.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["resolve"] += 1
            out.append("__brave__")
    return out


CAUSAL_RULES = [Rule("bravery", _r_bravery)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
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


def predict_moment(world: World, hazard_id: str) -> dict:
    sim = world.copy()
    h = sim.get(hazard_id)
    h.meters["danger"] += 1
    return {"danger": h.meters["danger"], "fear": sim.get("hero").memes["fear"]}


def tell(place: PlaceSpec, hero: CharacterSpec, sidekick: CharacterSpec,
         reptile: ReptileSpec, hazard: HazardSpec, tool: ToolSpec) -> World:
    world = World()
    h = world.add(Entity(id="hero", kind="character", type=hero.type, label=hero.label, role="hero"))
    d = world.add(Entity(id="doc", kind="character", type=sidekick.type, label=sidekick.label, role="doctor"))
    r = world.add(Entity(id="reptile", kind="thing", type="reptile", label=reptile.label, role="rescued"))
    haz = world.add(Entity(id="hazard", kind="thing", type="hazard", label=hazard.label, role="risk"))
    t = world.add(Entity(id="tool", kind="thing", type="tool", label=tool.label, role="tool"))

    h.memes["bravery"] = float(hero.bravery)
    d.memes["care"] = float(sidekick.cautious)
    h.memes["curiosity"] = 1.0
    world.facts.update(place=place, hero=hero, sidekick=sidekick, reptile=reptile, hazard=hazard, tool=tool)

    world.say(
        f"{hero.label} and {sidekick.label} stepped into {place.label}. "
        f"{place.scene} The air felt like a comic book ready to burst with action."
    )
    world.say(
        f"They were there to help {reptile.phrase}, because every good hero knows a small {reptile.id} still needs a safe hand."
    )
    world.say(
        f"Then {hazard.label} happened near {place.dark_spot}. Dang -- the whole room jolted, and the reptile started to slide the wrong way."
    )

    world.para()
    h.memes["fear"] += 1
    d.memes["alert"] += 1
    predict_moment(world, "hazard")
    world.say(
        f"{hero.label} took a deep breath. Brave as a cape in the wind, {hero.pronoun()} shouted, "
        f'"{sidekick.label}, I can help!"'
    )
    world.say(
        f"{sidekick.label.capitalize()} nodded fast and lifted {tool.phrase}. {tool.effect.capitalize()}."
    )

    if tool.power >= 4:
        world.para()
        h.memes["bravery"] += 1
        r.meters["safe"] += 1
        haz.meters["stopped"] += 1
        world.say(
            f"Together they used the {tool.label} and kept everyone back. The {reptile.id} was guided safely, and the dang moment ended."
        )
        world.say(
            f"At last {hero.label} stood taller than the scare. {hero.pronoun().capitalize()} smiled at the doc, feeling like a real hero."
        )
    else:
        world.para()
        h.memes["fear"] += 1
        world.say(
            f"The first try was not enough, but {hero.label} did not run away. {hero.pronoun().capitalize()} kept the path clear until the doc could try again."
        )
        world.say(
            f"That was bravery too: staying close, staying calm, and keeping the reptile safe."
        )

    world.facts.update(outcome="safe", tool=tool, brave=bool(h.memes["bravery"] >= THRESHOLD))
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a superhero story for a 3-to-5-year-old that includes the words "doc", "reptile", and "dang".',
        f"Tell a brave rescue story where {f['hero'].label} helps {f['sidekick'].label} keep a {f['reptile'].id} safe after a {f['hazard'].label}.",
        f"Write a short superhero tale about bravery, a doc, and a reptile rescue with a happy ending.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero: CharacterSpec = f["hero"]
    sidekick: CharacterSpec = f["sidekick"]
    reptile: ReptileSpec = f["reptile"]
    hazard: HazardSpec = f["hazard"]
    tool: ToolSpec = f["tool"]
    return [
        (
            "Who was the story about?",
            f"It was about {hero.label} and {sidekick.label}. They worked together like superheroes in a rescue room."
        ),
        (
            "What went wrong?",
            f"{hazard.label.capitalize()} happened, and that made a dangerous moment for {reptile.phrase}. The room had to stay calm so nobody got hurt."
        ),
        (
            "How did they fix it?",
            f"They used {tool.phrase} to help. That kept the reptile safe and turned the dang moment into a rescue."
        ),
        (
            "Why was the hero brave?",
            f"{hero.label} was brave because {hero.label_word if hasattr(hero, 'label_word') else hero.label} kept helping even after the scare. {hero.label} stayed close, spoke up, and helped the doc solve the problem."
        ),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a doctor?", "A doctor is a grown-up who helps people when they are hurt or sick. Doctors use careful hands and kind words."),
        ("What is a reptile?", "A reptile is a kind of animal like a lizard, snake, or turtle. Reptiles have scaly skin and need gentle care."),
        ("What does bravery mean?", "Bravery means doing the right thing even when you feel scared. A brave person keeps going to help someone else."),
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
brave(H) :- hero(H), bravery(H, B), fear(H, F), B >= 1, F >= 1.
safe_outcome :- brave(hero), tool(tool, P), P >= 4.
dang_moment :- hazard(hazard), reptile(reptile).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for hid, h in HEROES.items():
        lines.append(asp.fact("hero", hid))
        lines.append(asp.fact("bravery", hid, h.bravery))
    for sid in SIDES:
        lines.append(asp.fact("doc", sid))
    for rid in REPTILES:
        lines.append(asp.fact("reptile", rid))
    for hid in HAZARDS:
        lines.append(asp.fact("hazard", hid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid, t.power))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_safe_tools() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show safe_outcome/0."))
    return asp.atoms(model, "safe_outcome")


def asp_verify() -> int:
    rc = 0
    if not asp_safe_tools() and not any(t.power >= 4 for t in TOOLS.values()):
        print("MISMATCH: ASP safety gate failed.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: normal generation smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero doc/reptile/bravery story world.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--sidekick", choices=SIDES)
    ap.add_argument("--reptile", choices=REPTILES)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--tool", choices=TOOLS)
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
    place_id = args.place or rng.choice(list(PLACES))
    place = PLACES[place_id]
    reptile_id = args.reptile or rng.choice(sorted(place.afford))
    hazard_id = args.hazard or rng.choice(list(HAZARDS))
    tool_id = args.tool or rng.choice(list(TOOLS))
    hero = args.hero or rng.choice(list(HEROES))
    sidekick = args.sidekick or rng.choice(list(SIDES))
    if reptile_id not in place.afford:
        raise StoryError(f"(No story: {reptile_id} does not belong in {place.label}.)")
    return StoryParams(
        place=place_id,
        hero=hero,
        hero_type=HEROES[hero].type,
        sidekick=sidekick,
        sidekick_type=SIDES[sidekick].type,
        doc="doc",
        reptile=reptile_id,
        hazard=hazard_id,
        tool=tool_id,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.hero not in HEROES or params.sidekick not in SIDES:
        raise StoryError("invalid story parameters")
    if params.reptile not in REPTILES or params.hazard not in HAZARDS or params.tool not in TOOLS:
        raise StoryError("invalid story parameters")
    place = PLACES[params.place]
    if params.reptile not in place.afford:
        raise StoryError(f"(No story: {params.reptile} does not fit {place.label}.)")
    world = tell(place, HEROES[params.hero], SIDES[params.sidekick], REPTILES[params.reptile], HAZARDS[params.hazard], TOOLS[params.tool])
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show brave/1.\n#show safe_outcome/0.\n#show dang_moment/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode not expanded for this tiny world.")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
