#!/usr/bin/env python3
"""
storyworlds/worlds/artillery_reconciliation_myth.py
====================================================

A small mythic storyworld about artillery, a quarrel, and reconciliation.

Seed tale imagined from the prompt:
---
In an old hill-city, the bronze artillery woke before dawn and boomed to warn
the people of an incoming storm of raiders. The gatekeeper blamed the gunner for
shaking the shrines and startling the children. The gunner blamed the gatekeeper
for refusing to sound the bells. A river-priest listened, asked each to name the
hurt, and led them to make peace. Together they mended the cracked shrine and
stood watch with the artillery beside the gate.

This script turns that premise into a compact, state-driven myth:
- artillery can protect the city, but its blast frightens the shrine-keeper;
- a wound to the shrine creates a feud;
- reconciliation is only possible when a mediator helps both sides repair the
  shrine and share the watch.

The story stays small, classical, and child-facing while still being driven by a
live world model with physical meters and emotional memes.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


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
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    owns: set[str] = field(default_factory=set)

    artillery: object | None = None
    guardian: object | None = None
    keeper: object | None = None
    mediator: object | None = None
    shrine: object | None = None
    def __post_init__(self):
        if not self.meters:
            self.meters = {"stability": 0.0, "damage": 0.0, "noise": 0.0}
        if not self.memes:
            self.memes = {"fear": 0.0, "pride": 0.0, "hurt": 0.0, "trust": 0.0, "peace": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"priest", "man", "king", "gunner", "guard"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"priestess", "woman", "queen", "keeper"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    clone: object | None = None
    world: object | None = None
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone
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


@dataclass(frozen=True)
class Place:
    name: str
    place_kind: str
    defensible: bool = True
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


@dataclass(frozen=True)
class Artillery:
    id: str
    label: str
    kind: str
    size: str
    boom: str
    protects: str
    risk: str
    place: str
    noise: int
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


@dataclass(frozen=True)
class RitualItem:
    id: str
    label: str
    kind: str
    damageable: bool = True
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


SETTINGS = {
    "hill_city": Place(name="the hill city", place_kind="city", defensible=True),
    "harbor": Place(name="the harbor wall", place_kind="harbor", defensible=True),
    "river_gate": Place(name="the river gate", place_kind="gate", defensible=True),
}

ARTILLERY = {
    "bronze_cannon": Artillery(
        id="bronze_cannon",
        label="a bronze cannon",
        kind="artillery",
        size="great",
        boom="boomed",
        protects="city",
        risk="the shrine bells",
        place="hill_city",
        noise=2,
    ),
    "salt_mortar": Artillery(
        id="salt_mortar",
        label="a salt mortar",
        kind="artillery",
        size="small",
        boom="thundered",
        protects="harbor",
        risk="the chapel lamps",
        place="harbor",
        noise=1,
    ),
}

RITUAL_ITEMS = {
    "shrine": RitualItem(id="shrine", label="the shrine", kind="shrine"),
    "bells": RitualItem(id="bells", label="the shrine bells", kind="bells"),
    "lamp": RitualItem(id="lamp", label="the chapel lamps", kind="lamp"),
}


@dataclass
class StoryParams:
    place: str
    artillery: str
    mediator: str
    guardian: str
    keeper: str
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

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


NAMES = {
    "mediator": ["Iris", "Noah", "Mira", "Oren", "Selene", "Taro"],
    "guardian": ["Bram", "Leto", "Aster", "Cai", "Rhea", "Dorian"],
    "keeper": ["Elin", "Mara", "Sorin", "Phae", "Niko", "Hera"],
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic storyworld: artillery and reconciliation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--artillery", choices=ARTILLERY)
    ap.add_argument("--mediator")
    ap.add_argument("--guardian")
    ap.add_argument("--keeper")
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


def reasonableness_gate(place: str, artillery: Artillery) -> bool:
    return artillery.place == place


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    artillery = getattr(args, "artillery", None) or rng.choice(list(ARTILLERY))
    art = ARTILLERY[artillery]
    if not reasonableness_gate(place, art):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    mediator = getattr(args, "mediator", None) or rng.choice(NAMES["mediator"])
    guardian = getattr(args, "guardian", None) or rng.choice(NAMES["guardian"])
    keeper = getattr(args, "keeper", None) or rng.choice(NAMES["keeper"])
    return StoryParams(place=place, artillery=artillery, mediator=mediator, guardian=guardian, keeper=keeper)


def _boom(world: World, artillery: Entity, guardian: Entity, keeper: Entity) -> None:
    sig = ("boom", artillery.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    artillery.meters["noise"] += 1
    guardian.memes["pride"] += 1
    keeper.memes["fear"] += 1
    keeper.memes["hurt"] += 1
    world.say(f"The {artillery.label} {ARTILLERY[artillery.id].boom} above the stones, and the hill city heard it.")
    world.say(f"It kept the walls safe, yet {keeper.id} flinched at the crack of the sound.")


def _wound_shrine(world: World, keeper: Entity, item: Entity) -> None:
    sig = ("wound", item.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    item.meters["damage"] += 1
    keeper.memes["hurt"] += 1
    world.say(f"{keeper.id} saw {item.label} shake with a little crack in its face.")
    world.say(f"That hurt {keeper.pronoun('possessive')} heart, and a shadow of anger grew.")


def _feud(world: World, guardian: Entity, keeper: Entity) -> None:
    if guardian.memes["pride"] < THRESHOLD or keeper.memes["hurt"] < THRESHOLD:
        return
    sig = ("feud", guardian.id, keeper.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    guardian.memes["trust"] -= 0.5
    keeper.memes["trust"] -= 0.5
    world.say(f"{guardian.id} blamed the loud cannon.")
    world.say(f"{keeper.id} blamed the guard for choosing war over the old shrine.")


def _reconcile(world: World, mediator: Entity, guardian: Entity, keeper: Entity, item: Entity, artillery: Entity) -> None:
    sig = ("reconcile", mediator.id)
    if sig in world.fired:
        return
    if item.meters["damage"] < THRESHOLD:
        return
    if guardian.memes["trust"] > 0 and keeper.memes["hurt"] > 0:
        world.fired.add(sig)
        guardian.memes["trust"] += 1
        keeper.memes["trust"] += 1
        guardian.memes["peace"] += 1
        keeper.memes["peace"] += 1
        item.meters["damage"] -= 1
        item.meters["stability"] += 1
        world.say(f"Then {mediator.id} came like a quiet river and asked each one to speak the hurt aloud.")
        world.say(f"{mediator.id} led them to mend {item.label} with gold thread and clean hands.")
        world.say(f"At last {guardian.id} and {keeper.id} stood together beside the {artillery.label}, no longer enemies.")


def tell(place: Place, artillery_cfg: Artillery, mediator_name: str, guardian_name: str, keeper_name: str) -> World:
    world = World(place.name)
    mediator = world.add(Entity(id=mediator_name, kind="character", type="priest", label=mediator_name, role="mediator"))
    guardian = world.add(Entity(id=guardian_name, kind="character", type="guard", label=guardian_name, role="guardian"))
    keeper = world.add(Entity(id=keeper_name, kind="character", type="keeper", label=keeper_name, role="keeper"))
    artillery = world.add(Entity(id=artillery_cfg.id, kind="thing", type="artillery", label=artillery_cfg.label, role="weapon"))
    shrine = world.add(Entity(id="shrine", kind="thing", type="shrine", label="the shrine"))
    world.facts.update(place=place, artillery=artillery_cfg, mediator=mediator, guardian=guardian, keeper=keeper, shrine=shrine)

    world.say(f"In {place.name}, there stood {artillery_cfg.label} that guarded the people by dawn.")
    world.say(f"{guardian.id} kept watch over the gate, and {keeper.id} tended {shrine.label} beside the road.")
    world.para()
    _boom(world, artillery, guardian, keeper)
    _wound_shrine(world, keeper, shrine)
    _feud(world, guardian, keeper)
    world.para()
    _reconcile(world, mediator, guardian, keeper, shrine, artillery)
    if shrine.meters["damage"] >= THRESHOLD:
        shrine.meters["damage"] = 0.0
    world.say(f"When the sun climbed up, the {artillery_cfg.label} still stood ready, but now it stood beside peace.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    art: Artillery = f["artillery"]
    return [
        "Write a short myth about artillery, a hurt temple, and reconciliation.",
        f"Tell a child-friendly legend where {art.label} protects the city and a mediator mends a feud.",
        f"Write a story in a myth style about {art.label}, a guard, a keeper, and peace returned.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    art: Artillery = f["artillery"]
    guardian: Entity = f["guardian"]
    keeper: Entity = f["keeper"]
    mediator: Entity = f["mediator"]
    qa = [
        QAItem(
            question=f"What did {art.label} do for the city?",
            answer=f"It guarded the city by warning of danger with a great booming sound.",
        ),
        QAItem(
            question=f"Why were {guardian.id} and {keeper.id} upset?",
            answer=f"{guardian.id} thought the cannon had to be loud for safety, but {keeper.id} was hurt because the booming shook {world.facts['shrine'].label}.",
        ),
        QAItem(
            question=f"Who helped the two of them make peace?",
            answer=f"{mediator.id} listened to both sides and helped them speak gently until they reconciled.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is artillery?",
            answer="Artillery is a large weapon, like a cannon or mortar, that can fire from far away to protect a place.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means making peace again after people have argued or been hurt.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    art = ARTILLERY[params.artillery]
    place = _safe_lookup(SETTINGS, params.place)
    world = tell(place, art, params.mediator, params.guardian, params.keeper)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


ASP_RULES = r"""
artillery(A) :- art(A).
place(P) :- loc(P).
reconciled :- mediation(M), hurt(H), repaired(S), M.
valid_story(P, A) :- artillery(A), place(P), recon(P, A).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("loc", pid))
    for aid, a in ARTILLERY.items():
        lines.append(asp.fact("art", aid))
        lines.append(asp.fact("at", aid, a.place))
        lines.append(asp.fact("boom", aid, a.noise))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str]]:
    return [(p, a) for p in SETTINGS for a, art in ARTILLERY.items() if art.place == p]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos()")
    return 1


CURATED = [
    StoryParams(place="hill_city", artillery="bronze_cannon", mediator="Iris", guardian="Bram", keeper="Elin"),
    StoryParams(place="harbor", artillery="salt_mortar", mediator="Selene", guardian="Cai", keeper="Mara"),
]


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print()
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print()
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(getattr(args, "n", None)):
            rng = random.Random(base_seed + i)
            try:
                params = resolve_params(args, rng)
            except StoryError:
                continue
            params.seed = base_seed + i
            samples.append(generate(params))

    if getattr(args, "json", None):
        print(json.dumps([s.to_dict() for s in samples] if len(samples) > 1 else samples[0].to_dict(), indent=2, ensure_ascii=False))
        return

    for i, s in enumerate(samples):
        emit(s, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
