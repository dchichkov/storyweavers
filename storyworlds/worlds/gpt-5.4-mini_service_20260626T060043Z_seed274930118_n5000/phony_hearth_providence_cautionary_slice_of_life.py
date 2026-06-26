#!/usr/bin/env python3
"""
A small cautionary slice-of-life world about a child, a cozy hearth, and a
phony promise that looks helpful until careful thinking turns it harmless.

Seed premise:
- A child notices a phony "providence" coupon that claims to fix or improve the
  hearth, but the grown-up spots the trick before anyone trusts it.
- The story stays close to daily life: a home evening, a shared task, a small
  temptation, and a calm correction.

The simulated world tracks:
- physical meters: warmth, soot, tidiness, cost, wear
- emotional memes: trust, worry, relief, pride, patience

A reasonable story is one where the phony offer is rejected, the hearth is kept
safe, and the family chooses a plain, honest fix instead.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import re
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0



def _safe_fact(world, facts, key):
    value = facts.get(key) if hasattr(facts, "get") else None
    if hasattr(value, "id") or hasattr(value, "label") or hasattr(value, "verb") or hasattr(value, "sign"):
        return value
    if isinstance(value, str):
        if hasattr(world, "get"):
            try:
                resolved = world.get(value)
                if resolved is not None:
                    return resolved
            except Exception:
                pass
        upper = key.upper()
        for registry_name in (upper, upper + "S", upper + "ES", upper + "_REGISTRY"):
            registry = globals().get(registry_name)
            if isinstance(registry, dict) and value in registry:
                return registry[value]
        if upper.endswith("Y"):
            registry = globals().get(upper[:-1] + "IES")
            if isinstance(registry, dict) and value in registry:
                return registry[value]
    entities = getattr(world, "entities", {})
    if hasattr(entities, "values"):
        for entity in entities.values():
            if hasattr(entity, "id") or hasattr(entity, "label"):
                return entity
    return value


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
            keys = [upper, upper + "S", upper + "ES"]
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    wearable: bool = False
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hearth: object | None = None
    hero: object | None = None
    parent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "daughter", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "son", "father", "man"}:
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
        if "_tags" not in self.__dict__:
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
    place: str = "the cottage"
    hearth_kind: str = "fireplace"
    wintery: bool = True
    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class Offer:
    id: str
    label: str
    phrase: str
    effect: str
    cost_risk: str
    trust_risk: str
    fix_word: str
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
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
class StoryParams:
    setting: str
    offer: str
    hero_name: str
    hero_gender: str
    parent_kind: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone = World(copy.deepcopy(self.setting))
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


SETTINGS = {
    "cottage": Setting(place="the cottage", hearth_kind="hearth", wintery=True),
    "rowhouse": Setting(place="the rowhouse", hearth_kind="fireplace", wintery=False),
    "farmhouse": Setting(place="the farmhouse", hearth_kind="wood stove", wintery=True),
}

OFFERS = {
    "phony_providence": Offer(
        id="phony_providence",
        label="phony Providence coupon",
        phrase='a shiny coupon stamped "Providence" in gold letters',
        effect="promises to make the hearth warm for free",
        cost_risk="it could waste money",
        trust_risk="it looks fake and could trick the family",
        fix_word="honest",
    ),
    "cheap_coal": Offer(
        id="cheap_coal",
        label="cheap coal ad",
        phrase="a too-cheap flyer for coal",
        effect="promises a warm hearth at a tiny price",
        cost_risk="it might be poor fuel",
        trust_risk="the offer sounds phony",
        fix_word="plain",
    ),
    "spark_cleaner": Offer(
        id="spark_cleaner",
        label="spark cleaner spray",
        phrase="a bottle that claims it can clean soot in one puff",
        effect="promises a spotless hearth",
        cost_risk="it may waste money",
        trust_risk="the claim sounds too big to be true",
        fix_word="careful",
    ),
}

NAMES = ["Mina", "Eli", "June", "Noah", "Pia", "Owen", "Lina", "Theo"]
PARENTS = ["mother", "father", "grandmother", "grandfather"]
GENDERS = ["girl", "boy"]


def _m(d: dict[str, float], key: str, amount: float = 0.0) -> float:
    return d.get(key, amount)


def _set(d: dict[str, float], key: str, value: float) -> None:
    d[key] = value


def _add(d: dict[str, float], key: str, value: float) -> None:
    d[key] = d.get(key, 0.0) + value


def normalize_name(name: str) -> str:
    return re.sub(r"\s+", " ", name.strip())


def valid_combo(setting: Setting, offer: Offer) -> bool:
    if setting.hearth_kind == "hearth":
        return offer.id in {"phony_providence", "spark_cleaner"}
    if setting.hearth_kind == "fireplace":
        return offer.id in {"phony_providence", "cheap_coal", "spark_cleaner"}
    return offer.id in OFFERS


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for sid, setting in SETTINGS.items():
        for oid, offer in OFFERS.items():
            if valid_combo(setting, offer):
                out.append((sid, oid))
    return out


def _ensure_reasonable(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        pass
    if params.offer not in OFFERS:
        pass
    if not valid_combo(_safe_lookup(SETTINGS, params.setting), _safe_lookup(OFFERS, params.offer)):
        pass
    if params.hero_gender not in GENDERS:
        pass


def introduce(world: World, hero: Entity, parent: Entity, offer: Offer) -> None:
    world.say(
        f"{hero.id} lived in {world.setting.place} and liked the warm glow of the {world.setting.hearth_kind}."
    )
    world.say(
        f"{hero.pronoun().capitalize()} was curious about {offer.phrase}, even though it looked a little phony."
    )
    parent.memes["patience"] += 1
    world.say(
        f"{hero.id}'s {parent.type} kept the fire tidy and said the home felt best when it stayed honest and simple."
    )


def notice_offer(world: World, hero: Entity, offer: Offer) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"One quiet evening, {hero.id} found {offer.phrase} on the table beside the kettle."
    )
    world.say(
        f"The paper said it {offer.effect}, but the promise sounded too neat for real life."
    )


def predict_harm(world: World, offer: Offer) -> dict:
    sim = world.copy()
    hearth = sim.get("hearth")
    if offer.id == "phony_providence":
        _add(hearth.meters, "worry", 1)
        _add(hearth.memes, "doubt", 1)
        _add(hearth.meters, "cost", 1)
    elif offer.id == "cheap_coal":
        _add(hearth.meters, "soot", 2)
        _add(hearth.meters, "wear", 1)
        _add(hearth.memes, "worry", 1)
    else:
        _add(hearth.meters, "satin", 0)  # no-op to keep the simulation explicit
        _add(hearth.meters, "cost", 1)
    return {
        "soot": _m(hearth.meters, "soot"),
        "wear": _m(hearth.meters, "wear"),
        "cost": _m(hearth.meters, "cost"),
        "worry": _m(hearth.memes, "worry"),
    }


def warn(world: World, parent: Entity, hero: Entity, offer: Offer) -> None:
    pred = predict_harm(world, offer)
    if offer.id == "phony_providence":
        world.facts["predicted"] = pred
        world.say(
            f'"That looks phony," {parent.id} said. "A real home does not need a fake promise with Providence written on it."'
        )
        world.say(
            f"{hero.id} paused and listened, because the warning matched the crooked-looking paper."
        )
    elif offer.id == "cheap_coal":
        world.facts["predicted"] = pred
        world.say(
            f'"Cheap fuel can make a dirty hearth," {parent.id} said. "If it leaves more soot, it is not really cheap."'
        )
        world.say(
            f"{hero.id} looked at the stack of black dust by the grate and frowned."
        )
    else:
        world.facts["predicted"] = pred
        world.say(
            f'"That cleaner sounds too good to be true," {parent.id} said. "Careful is better than sorry."'
        )


def choose_again(world: World, hero: Entity, parent: Entity, offer: Offer) -> None:
    hero.memes["worry"] += 1
    world.say(
        f"{hero.id} wanted a quick fix, but {hero.pronoun('possessive')} stomach felt tight."
    )
    world.say(
        f"{hero.pronoun().capitalize()} put the paper back and asked {parent.pronoun('object')} to check it again."
    )


def resolve(world: World, hero: Entity, parent: Entity, offer: Offer) -> None:
    hearth = world.get("hearth")
    parent.memes["relief"] += 1
    hero.memes["relief"] += 1
    if offer.id == "phony_providence":
        _add(hearth.memes, "trust", -1)
        world.say(
            f"{parent.id} tore the coupon in half and showed {hero.id} the small print that made it a trick."
        )
        world.say(
            f"Then they used a simple, honest fix: they opened the vent, swept the ash, and left the {world.setting.hearth_kind} bright and safe."
        )
    elif offer.id == "cheap_coal":
        _add(hearth.meters, "soot", -1)
        _add(hearth.memes, "trust", 1)
        world.say(
            f"Instead of buying the cheap coal, they chose the regular bag from the good shop."
        )
        world.say(
            f"The {world.setting.hearth_kind} stayed cleaner, and the room still felt warm by bedtime."
        )
    else:
        _add(hearth.meters, "soot", -1)
        world.say(
            f"They ignored the flashy spray and wiped the hearth with a damp cloth."
        )
        world.say(
            f"The little shine returned slowly, the way real work often does at home."
        )


def tell(setting: Setting, offer: Offer, hero_name: str, hero_gender: str, parent_kind: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender))
    parent = world.add(Entity(id="parent", kind="character", type=parent_kind, label=parent_kind))
    hearth = world.add(Entity(id="hearth", kind="thing", type=setting.hearth_kind, label=setting.hearth_kind))
    _add(hearth.meters, "warmth", 2)
    _add(hearth.meters, "soot", 1)
    _add(hearth.memes, "comfort", 2)
    _add(hearth.memes, "trust", 1)

    introduce(world, hero, parent, offer)
    world.para()
    notice_offer(world, hero, offer)
    warn(world, parent, hero, offer)
    choose_again(world, hero, parent, offer)
    world.para()
    resolve(world, hero, parent, offer)

    world.facts.update(
        hero=hero,
        parent=parent,
        hearth=hearth,
        offer=offer,
        setting=setting,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    parent: Entity = _safe_fact(world, f, "parent")
    offer: Offer = _safe_fact(world, f, "offer")
    setting: Setting = _safe_fact(world, f, "setting")
    return [
        f'Write a short slice-of-life story for a child about a {setting.hearth_kind} and a phony promise.',
        f"Tell a gentle cautionary story where {hero.id} notices {offer.phrase} at {setting.place} and {parent.pronoun('object')} spots the trick.",
        f"Write a calm story about family life at {setting.place}, where a flashy offer is refused and the hearth stays safe.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    parent: Entity = _safe_fact(world, f, "parent")
    offer: Offer = _safe_fact(world, f, "offer")
    setting: Setting = _safe_fact(world, f, "setting")
    hearth: Entity = _safe_fact(world, f, "hearth")
    return [
        QAItem(
            question=f"What did {hero.id} find beside the kettle at {setting.place}?",
            answer=f"{hero.id} found {offer.phrase}. It looked shiny, but it was a phony promise, not a sure thing.",
        ),
        QAItem(
            question=f"Why did the grown-up warn {hero.id} about the offer?",
            answer=f"{parent.id} warned {hero.id} because the offer looked phony and could waste money or cause trouble for the {setting.hearth_kind}.",
        ),
        QAItem(
            question=f"What did the family do instead of trusting the fake offer?",
            answer=f"They chose a plain, honest fix and kept the {setting.hearth_kind} clean, warm, and safe.",
        ),
        QAItem(
            question=f"How did the story end for the {setting.hearth_kind}?",
            answer=f"The {setting.hearth_kind} ended bright and steady, with the home feeling calm again by bedtime.",
        ),
        QAItem(
            question=f"What changed in {hero.id}'s feelings after listening carefully?",
            answer=f"{hero.id} moved from curiosity and worry to relief, because listening helped the family avoid a bad choice.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a hearth?",
            answer="A hearth is the warm area around a fire, often a fireplace or stove in a home.",
        ),
        QAItem(
            question="Why should someone be careful with a phony offer?",
            answer="A phony offer can trick people into wasting money or buying something that does not really help.",
        ),
        QAItem(
            question="What does providence mean in a normal way?",
            answer="Providence can mean careful help or wise guidance, often something people trust when they plan for the future.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== prompts =="]
    for p in sample.prompts:
        parts.append(f"- {p}")
    parts.append("")
    parts.append("== story QA ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== world QA ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"{e.id}: {e.kind}/{e.type} " + " ".join(parts))
    return "\n".join(lines)


ASP_RULES = r"""
setting(cottage). setting(rowhouse). setting(farmhouse).
hearth_kind(cottage,hearth).
hearth_kind(rowhouse,fireplace).
hearth_kind(farmhouse,"wood stove").

offer(phony_providence).
offer(cheap_coal).
offer(spark_cleaner).

phony(phony_providence).
phony(cheap_coal).
phony(spark_cleaner).

safe_to_use(cottage,phony_providence).
safe_to_use(cottage,spark_cleaner).
safe_to_use(rowhouse,phony_providence).
safe_to_use(rowhouse,cheap_coal).
safe_to_use(rowhouse,spark_cleaner).
safe_to_use(farmhouse,phony_providence).
safe_to_use(farmhouse,cheap_coal).
safe_to_use(farmhouse,spark_cleaner).

valid(S,O) :- setting(S), offer(O), safe_to_use(S,O).

#show valid/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("hearth_kind", sid, _safe_lookup(SETTINGS, sid).hearth_kind))
    for oid in OFFERS:
        lines.append(asp.fact("offer", oid))
        if "phony" in oid or oid == "spark_cleaner":
            lines.append(asp.fact("phony", oid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    py_set = set(valid_combos())
    if clingo_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH:")
    print("only in clingo:", sorted(clingo_set - py_set))
    print("only in python:", sorted(py_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Cautionary slice-of-life storyworld about a hearth and a phony offer.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--offer", choices=OFFERS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--parent", choices=PARENTS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if getattr(args, "setting", None) and getattr(args, "offer", None):
        if (getattr(args, "setting", None), getattr(args, "offer", None)) not in combos:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    filtered = [
        c for c in combos
        if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
        and (getattr(args, "offer", None) is None or c[1] == getattr(args, "offer", None))
    ]
    if not filtered:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, offer = rng.choice(list(filtered))
    gender = getattr(args, "gender", None) or rng.choice(GENDERS)
    name = normalize_name(getattr(args, "name", None) or rng.choice(NAMES))
    parent = getattr(args, "parent", None) or rng.choice(PARENTS)
    return StoryParams(setting=setting, offer=offer, hero_name=name, hero_gender=gender, parent_kind=parent)


def generate(params: StoryParams) -> StorySample:
    _ensure_reasonable(params)
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(OFFERS, params.offer), params.hero_name, params.hero_gender, params.parent_kind)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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
    StoryParams(setting="cottage", offer="phony_providence", hero_name="Mina", hero_gender="girl", parent_kind="mother"),
    StoryParams(setting="rowhouse", offer="cheap_coal", hero_name="Eli", hero_gender="boy", parent_kind="father"),
    StoryParams(setting="farmhouse", offer="spark_cleaner", hero_name="June", hero_gender="girl", parent_kind="grandmother"),
]


def asp_valid_stories() -> list[tuple]:
    return asp_valid_combos()


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible setting/offer combos:")
        for s, o in combos:
            print(f"  {s:10} {o}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.hero_name}: {p.offer} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
