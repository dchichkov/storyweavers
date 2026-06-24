#!/usr/bin/env python3
"""
Standalone storyworld: an animal tale about an olympian con, a rubber trinket,
suspense, sharing, and repetition.

The seed imagination behind this world:
- A clever con artist animal keeps promising a shiny "olympian" prize.
- The real tension is whether the animals will trust the show and share the
  rubber token that makes the trick possible.
- Repetition is part of the charm: the con repeats a line, the animals repeat a
  check, and the ending proves who shared what.

This file is self-contained, uses only the stdlib plus the shared results.py
containers, and imports the shared ASP helper lazily inside ASP functions.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

# Make shared containers importable when run as a script.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Core model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0



def _fallback_storyparams(args, rng, cls, ns):
    data = {}
    missing = getattr(__import__("dataclasses"), "MISSING")
    for field in __import__("dataclasses").fields(cls):
        name = field.name
        value = None
        for arg_name in (name, name.removesuffix("_name"), name.removesuffix("_id")):
            if hasattr(args, arg_name):
                value = getattr(args, arg_name)
                if value is not None:
                    break
        if value is None:
            upper = name.upper()
            keys = [upper + "S", upper + "ES"]
            if upper.endswith("Y"):
                keys.append(upper[:-1] + "IES")
            for key in keys:
                pool = ns.get(key)
                if isinstance(pool, dict) and pool:
                    value = next(iter(pool.keys()))
                    break
                if isinstance(pool, (list, tuple, set)) and pool:
                    value = sorted(pool)[0] if isinstance(pool, set) else pool[0]
                    break
        if value is None and field.default is not missing:
            value = field.default
        if value is None:
            if name == "seed":
                value = getattr(args, "seed", None)
            elif "gender" in name or name.endswith("_type"):
                value = "girl"
            elif "name" in name or name in {"child", "hero", "helper", "friend", "pal", "guide"}:
                value = name.removesuffix("_name").replace("_", " ").title() or "Mia"
            else:
                value = name
        data[name] = value
    return cls(**data)


def _safe_lookup(mapping, key):
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = list(mapping.values())
        if values:
            return values[0]
    if mapping:
        return mapping[0]
    raise KeyError(key)

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" or "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    region: object | None = None
    foil: object | None = None
    hero: object | None = None
    item: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"fox", "cat", "dog", "rabbit", "bear", "mouse"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class Setting:
    place: str
    indoor: bool = False
    affords: set[str] = field(default_factory=set)
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

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

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

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    offers: str
    fix: str
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

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

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.fired: set[tuple] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = dict(self.facts)
        clone.zone = set(self.zone)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# World content
# ---------------------------------------------------------------------------

SETTINGS = {
    "field": Setting(place="the field", affords={"show", "race"}),
    "barn": Setting(place="the barn", indoor=True, affords={"show"}),
    "park": Setting(place="the park", affords={"show", "race"}),
}

ACTIVITIES = {
    "show": Activity(
        id="show",
        verb="put on a show",
        gerund="putting on shows",
        rush="dash to the stage",
        risk="the rubber prop might snap during the act",
        zone={"hands", "torso"},
        keyword="show",
        tags={"suspense", "repetition"},
    ),
    "race": Activity(
        id="race",
        verb="race fast",
        gerund="racing fast",
        rush="run to the track",
        risk="the rubber boot could bounce off",
        zone={"feet"},
        keyword="race",
        tags={"suspense"},
    ),
}

PRIZES = {
    "badge": Prize(id="badge", label="badge", phrase="a shiny badge", region="torso"),
    "boots": Prize(id="boots", label="boots", phrase="rubber boots", region="feet", plural=True),
    "glove": Prize(id="glove", label="glove", phrase="a rubber glove", region="hands"),
}

GEAR = {
    "rubber_band": Gear(
        id="rubber_band",
        label="a rubber band",
        covers={"hands"},
        offers="wrap the prop with a rubber band",
        fix="kept the prop steady",
    ),
    "rubber_boots": Gear(
        id="rubber_boots",
        label="rubber boots",
        covers={"feet"},
        offers="wear the rubber boots",
        fix="kept the feet dry and safe",
    ),
}

ANIMAL_NAMES = ["Milo", "Pip", "Ruby", "Nina", "Bram", "Toby"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    hero: str
    foil: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
    params: object | None = None
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

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


ASP_RULES = r"""
at_risk(A,P) :- activity(A), prize(P), zone(A,R), region(P,R).
compatible(G,A,P) :- gear(G), at_risk(A,P), covers(G,R), zone(A,R), region(P,R).
valid(Place,A,P) :- setting(Place), affords(Place,A), at_risk(A,P), compatible(_,A,P).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for r in sorted(a.zone):
            lines.append(asp.fact("zone", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("region", pid, p.region))
    for gid, g in GEAR.items():
        lines.append(asp.fact("gear", gid))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", gid, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, s in SETTINGS.items():
        for act_id in s.affords:
            act = _safe_lookup(ACTIVITIES, act_id)
            for prize_id, prize in PRIZES.items():
                if prize.region in act.zone:
                    if any(prize.region in g.covers for g in GEAR.values()):
                        combos.append((place, act_id, prize_id))
    return combos


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def predict_risk(world: World, hero: Entity, act: Activity, prize: Entity) -> bool:
    return prize.region in act.zone


def select_gear(act: Activity, prize: Prize) -> Optional[Gear]:
    for g in GEAR.values():
        if prize.region in g.covers:
            return g
    return None


def tell(setting: Setting, act: Activity, prize: Prize, hero_name: str, foil_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="fox"))
    foil = world.add(Entity(id=foil_name, kind="character", type="rabbit"))
    item = world.add(Entity(id=prize.id, type=prize.id, label=prize.label, phrase=prize.phrase, owner=hero.id, region=prize.region, plural=prize.plural))

    hero.memes["curious"] = 1
    foil.memes["careful"] = 1

    world.say(f"{hero.id} was a clever little fox who loved a big plan.")
    world.say(f"{foil.id} was a careful rabbit who liked to count things twice.")
    world.say(f"One day, {hero.id} found {item.phrase} and promised a grand {act.keyword}.")

    world.para()
    world.say(f"At {world.setting.place}, {hero.id} wanted to {act.verb}, but there was suspense in the air.")
    world.say(f"{hero.id} kept saying, 'Just wait, just wait,' and the others kept watching.")

    if predict_risk(world, hero, act, item):
        world.say(f"{foil.id} worried because {item.label} could get ruined if the act went wrong.")
        world.say(f"{foil.id} asked, 'Will the rubber trick really work?'")

    world.para()
    hero.memes["con"] += 1
    hero.memes["repetition"] += 1
    world.say(f"{hero.id} repeated, 'Trust me, trust me,' and the crowd listened.")
    world.say(f"Then {foil.id} repeated the check: first the feet, then the hands, then the finish.")

    gear = select_gear(act, prize)
    if gear is None:
        pass

    world.say(f"{foil.id} suggested they {gear.offers} before the show.")
    world.say(f"{hero.id} agreed, and the rubber idea made the waiting feel safer.")
    hero.memes["sharing"] += 1
    foil.memes["sharing"] += 1

    world.para()
    world.say(f"They shared the gear, shared the worry, and shared one more look at the stage.")
    world.say(f"At last, {hero.id} did {act.gerund} while {foil.id} smiled nearby.")
    world.say(f"The {prize.label} stayed safe, the rubber stayed useful, and the ending felt brave.")

    world.facts.update(hero=hero, foil=foil, prize=item, activity=act, setting=setting, gear=gear)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    act = f["activity"]
    prize = f["prize"]
    return [
        f"Write an animal story about {hero.id} the fox, a suspenseful plan, and {prize.phrase}.",
        f"Tell a repetitive, child-friendly tale where someone keeps saying the same line before {act.verb}.",
        f"Write a short story with sharing, rubber, and a clever animal trick that ends safely.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    foil = f["foil"]
    prize = f["prize"]
    act = f["activity"]
    gear = f["gear"]
    return [
        QAItem(
            question=f"Who was trying to run the plan in the story?",
            answer=f"{hero.id} the fox was the one trying to run the plan.",
        ),
        QAItem(
            question=f"What did {foil.id} worry about?",
            answer=f"{foil.id} worried that the {prize.label} might get ruined during the {act.keyword} plan.",
        ),
        QAItem(
            question=f"What helped the animals stay safe?",
            answer=f"They used {gear.label}, and that kept the important part safe.",
        ),
        QAItem(
            question="What was repeated in the story?",
            answer="The fox repeated the same promise, and the rabbit repeated the safety check.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is rubber?",
            answer="Rubber is a bendy material that can stretch, bounce, and help make things like bands or boots.",
        ),
        QAItem(
            question="What does suspense mean in a story?",
            answer="Suspense is the feeling of waiting to see what will happen next.",
        ),
        QAItem(
            question="What is sharing?",
            answer="Sharing means letting other people use something or helping them enjoy it too.",
        ),
        QAItem(
            question="Why do stories use repetition?",
            answer="Repetition helps a story feel playful, easy to follow, and memorable.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal storyworld with suspense, sharing, and repetition.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--hero")
    ap.add_argument("--foil")
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
    combos = valid_combos()
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "activity", None):
        combos = [c for c in combos if c[1] == getattr(args, "activity", None)]
    if getattr(args, "prize", None):
        combos = [c for c in combos if c[2] == getattr(args, "prize", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, prize = rng.choice(list(combos))
    hero = getattr(args, "hero", None) or rng.choice(ANIMAL_NAMES)
    foil = getattr(args, "foil", None) or rng.choice([n for n in ANIMAL_NAMES if n != hero])
    return StoryParams(place=place, activity=activity, prize=prize, hero=hero, foil=foil)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIVITIES, params.activity), _safe_lookup(PRIZES, params.prize), params.hero, params.foil)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: kind={e.kind} type={e.type} label={e.label} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP parity matches {len(py)} combos.")
        return 0
    print("MISMATCH")
    print("python only:", sorted(py - cl))
    print("asp only:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    rng = random.Random(getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31))
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for place, act, prize in sorted(valid_combos()):
            params = StoryParams(place=place, activity=act, prize=prize, hero="Milo", foil="Pip")
            samples.append(generate(params))
    else:
        for i in range(getattr(args, "n", None)):
            params = resolve_params(args, random.Random(rng.randrange(2**31)))
            params.seed = getattr(args, "seed", None)
            samples.append(generate(params))

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
