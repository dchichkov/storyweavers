#!/usr/bin/env python3
"""
A small mythic storyworld: a hero enters an auditorium, notices appearances
changing, trusts a gut feeling, faces conflict, and solves a problem through a
careful transformation.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    region: object | None = None
    elder: object | None = None
    hero: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = __import__('collections').defaultdict(float)
        if not self.memes:
            self.memes = __import__('collections').defaultdict(float)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "queen", "goddess"}
        male = {"boy", "man", "father", "king", "god"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
class Place:
    id: str
    label: str
    grandeur: int = 0
    echoes: int = 0
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
class Rite:
    id: str
    name: str
    action: str
    rash_choice: str
    turn: str
    solved_by: str
    appearance_shift: str
    zone: str
    danger: str
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
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
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
class Relic:
    id: str
    label: str
    phrase: str
    type: str
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
    place: str
    rite: str
    relic: str
    hero_name: str
    hero_type: str
    elder_type: str
    seed: Optional[int] = None
    curated: list = field(default_factory=list)
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: str = ""
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
        import copy as _copy

        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.zone = self.zone
        w.paragraphs = [[]]
        return w


def _meter(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def _set_meter(ent: Entity, key: str, value: float) -> None:
    ent.meters[key] = value


def _add_meter(ent: Entity, key: str, delta: float) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + delta


def _add_meme(ent: Entity, key: str, delta: float) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + delta


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if _meter(actor, "unease") >= THRESHOLD and _meter(actor, "blocked") >= THRESHOLD:
            sig = ("conflict", actor.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            _add_meme(actor, "conflict", 1)
            out.append(f"Their heart stirred with conflict.")
    return out


def _r_transformation(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if _meter(actor, "transformed") >= THRESHOLD:
            sig = ("transformed", actor.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            _add_meme(actor, "wonder", 1)
            out.append(f"{actor.id} changed like a moon in the sky.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_r_conflict, _r_transformation):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_gate(place: Place, rite: Rite, relic: Relic) -> bool:
    if place.id != "auditorium":
        return False
    if rite.zone != relic.region:
        return False
    return True


def predict(world: World, hero: Entity, rite: Rite, relic: Relic) -> dict:
    sim = world.copy()
    do_rite(sim, sim.get(hero.id), rite, narrate=False)
    rel = sim.get(relic.id)
    return {
        "changed": _meter(rel, "changed") >= THRESHOLD,
        "conflict": _meter(sim.get(hero.id), "blocked") >= THRESHOLD,
    }


def do_rite(world: World, actor: Entity, rite: Rite, narrate: bool = True) -> None:
    if world.place.id != "auditorium":
        pass
    actor.meters["performed"] = actor.meters.get("performed", 0.0) + 1
    actor.meters["unease"] = actor.meters.get("unease", 0.0) + 1
    actor.meters["blocked"] = actor.meters.get("blocked", 0.0) + 1
    world.zone = rite.zone
    propagate(world, narrate=narrate)


def transform_relic(world: World, relic: Entity, rite: Rite) -> None:
    relic.meters["changed"] = relic.meters.get("changed", 0.0) + 1
    relic.meters["glow"] = relic.meters.get("glow", 0.0) + 1
    relic.label = f"transformed {relic.label}"
    world.say(f"{relic.id} took on a new appearance, bright as dawn.")


def resolve_problem(world: World, hero: Entity, elder: Entity, rite: Rite, relic: Entity) -> None:
    _add_meme(hero, "courage", 1)
    _set_meter(hero, "blocked", 0)
    _set_meter(hero, "unease", 0)
    _add_meme(hero, "peace", 1)
    world.say(
        f"{hero.id} trusted a quiet gut feeling, and {elder.id} saw the sign. "
        f'Together they chose the wiser path: "{rite.solved_by}."'
    )
    world.say(
        f"Then the {relic.label} changed its appearance at the center of the auditorium, "
        f"and the old trouble could not remain."
    )


def tell(place: Place, rite: Rite, relic_cfg: Relic, hero_name: str, hero_type: str, elder_type: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    elder = world.add(Entity(id="Elder", kind="character", type=elder_type, label="the elder"))
    relic = world.add(
        Entity(
            id=relic_cfg.id,
            type=relic_cfg.type,
            label=relic_cfg.label,
            phrase=relic_cfg.phrase,
            owner=hero.id,
            caretaker=elder.id,
            region=relic_cfg.region,
            plural=relic_cfg.plural,
        )
    )

    world.say(
        f"In the old auditorium, {hero.id} stood beneath the high beams like a small hero in a myth."
    )
    world.say(
        f"{hero.id} loved the rite called {rite.name}, because its appearance seemed to promise glory."
    )
    world.say(
        f"Their {elder.label} had brought {hero.pronoun('object')} the {relic.phrase}, and {hero.id} treasured it."
    )

    world.para()
    world.say(
        f"One evening, when the lamps were low, {hero.id} stepped into the auditorium and wanted to {rite.action}."
    )
    world.say(
        f"Yet the {relic.label} looked too plain for such a ceremony, and {hero.id}'s gut grew tight."
    )
    world.say(
        f"{hero.id} feared the crowd would laugh, so the fear became conflict in {hero.pronoun('possessive')} chest."
    )

    world.para()
    if not reasonableness_gate(place, rite, relic_cfg):
        pass
    pred = predict(world, hero, rite, relic)
    if pred["changed"]:
        world.say(
            f"{hero.id} almost rushed ahead, but the elder lifted a hand and named the problem clearly."
        )
        world.say(f"'{rite.danger},' the elder said. 'We must solve it with care, not haste.'")
        transform_relic(world, relic, rite)
        resolve_problem(world, hero, elder, rite, relic)
    else:
        pass

    world.facts.update(hero=hero, elder=elder, relic=relic, rite=rite, place=place)
    return world


PLACES = {
    "auditorium": Place(id="auditorium", label="the auditorium", grandeur=3, echoes=2),
}

RITES = {
    "transformation": Rite(
        id="transformation",
        name="the Rite of Transformation",
        action="seek the hidden change",
        rash_choice="rush the old mask onto the stage",
        turn="listen to the gut and wait for the sign",
        solved_by="They paused, breathed, and let the appearance change at the right moment",
        appearance_shift="appearance changed from plain to radiant",
        zone="face",
        danger="A rushed ceremony would spoil the transformation",
        tags={"appearance", "transformation"},
    ),
    "conflict": Rite(
        id="conflict",
        name="the Rite of Conflict",
        action="challenge the shadow",
        rash_choice="shout at the shadow in anger",
        turn="let the elder calm the heart",
        solved_by="They spoke truth instead of pride",
        appearance_shift="appearance changed from tense to calm",
        zone="heart",
        danger="Anger would only deepen the conflict",
        tags={"conflict"},
    ),
    "problem_solving": Rite(
        id="problem_solving",
        name="the Rite of Problem Solving",
        action="solve the broken gate",
        rash_choice="push the gate harder",
        turn="study the hinge and choose the right key",
        solved_by="They looked, thought, and fit the key gently",
        appearance_shift="appearance changed from broken to whole",
        zone="hand",
        danger="Force would only break the gate further",
        tags={"problem_solving"},
    ),
}

RELICS = {
    "mask": Relic(id="mask", label="mask", phrase="a painted mask", type="mask", region="face"),
    "drum": Relic(id="drum", label="drum", phrase="a sacred drum", type="drum", region="heart"),
    "key": Relic(id="key", label="key", phrase="an old bronze key", type="key", region="hand"),
}

HERO_NAMES = ["Aster", "Iris", "Niko", "Mira", "Orion", "Lyra"]
HERO_TYPES = ["girl", "boy"]
ELDER_TYPES = ["woman", "man", "priest", "seer"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for pid, place in PLACES.items():
        for rid, rite in RITES.items():
            for relid, relic in RELICS.items():
                if reasonableness_gate(place, rite, relic):
                    out.append((pid, rid, relid))
    return out


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for rid, rite in RITES.items():
        lines.append(asp.fact("rite", rid))
        lines.append(asp.fact("zone", rid, rite.zone))
        for tag in sorted(rite.tags):
            lines.append(asp.fact("tag", rid, tag))
    for relid, relic in RELICS.items():
        lines.append(asp.fact("relic", relid))
        lines.append(asp.fact("region", relid, relic.region))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,R,L) :- place(P), rite(R), relic(L), zone(R,Z), region(L,Z).
#show valid/3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


@dataclass
class StoryParams:
    place: str
    rite: str
    relic: str
    hero_name: str
    hero_type: str
    elder_type: str
    seed: Optional[int] = None
    curated: list = field(default_factory=list)
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a mythic story about {f["hero"].id} in {f["place"].label}, where appearance changes and a gut feeling matters.',
        f"Tell a small legend in the auditorium where a {f['hero'].type} hero faces conflict and solves a problem with an elder.",
        f"Write a child-friendly myth about a sacred {f['relic'].label} that becomes transformed after careful problem solving.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, elder, relic, rite = f["hero"], f["elder"], f["relic"], f["rite"]
    return [
        QAItem(
            question=f"Where did {hero.id} face the trouble?",
            answer=f"{hero.id} faced the trouble in {world.place.label}, beneath the echoing roof of the auditorium.",
        ),
        QAItem(
            question=f"What did {hero.id} feel in {hero.pronoun('possessive')} gut before the change?",
            answer=f"{hero.id} felt a tight gut feeling that warned {hero.pronoun('object')} something was not yet right.",
        ),
        QAItem(
            question=f"What problem were {hero.id} and {elder.label} trying to solve?",
            answer=f"They were trying to solve the problem of making {relic.phrase} ready for the rite without forcing it.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"The {relic.label} changed its appearance, and the conflict in {hero.id}'s heart turned into peace.",
        ),
        QAItem(
            question=f"How did the elder help {hero.id}?",
            answer=f"The elder helped by slowing the moment down, naming the danger, and guiding {hero.id} toward the careful answer.",
        ),
    ]


KNOWLEDGE = {
    "appearance": [
        QAItem(
            question="What is appearance?",
            answer="Appearance is how something looks on the outside, such as its shape, color, or shine.",
        )
    ],
    "auditorium": [
        QAItem(
            question="What is an auditorium?",
            answer="An auditorium is a large room or hall where people gather to listen, watch, or speak.",
        )
    ],
    "gut": [
        QAItem(
            question="What does a gut feeling mean?",
            answer="A gut feeling is a strong hunch inside you that tells you something may be right or wrong.",
        )
    ],
    "transformation": [
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a big change, when something becomes different from what it was before.",
        )
    ],
    "conflict": [
        QAItem(
            question="What is conflict?",
            answer="Conflict is trouble between wishes or people, when different feelings pull in different directions.",
        )
    ],
    "problem_solving": [
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means thinking carefully about a trouble and finding a good way to fix it.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["rite"].tags) | {"appearance", "auditorium", "gut"}
    out: list[QAItem] = []
    for key in ["appearance", "auditorium", "gut", "transformation", "conflict", "problem_solving"]:
        if key in tags:
            out.extend(KNOWLEDGE[key])
    return out


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic storyworld: appearance, auditorium, gut, transformation, conflict, problem solving.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--rite", choices=RITES)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=HERO_TYPES)
    ap.add_argument("--elder", choices=ELDER_TYPES)
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
    combos = [c for c in combos
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "rite", None) is None or c[1] == getattr(args, "rite", None))
              and (getattr(args, "relic", None) is None or c[2] == getattr(args, "relic", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, rite, relic = rng.choice(list(combos))
    return StoryParams(
        place=place,
        rite=rite,
        relic=relic,
        hero_name=getattr(args, "name", None) or rng.choice(HERO_NAMES),
        hero_type=getattr(args, "gender", None) or rng.choice(HERO_TYPES),
        elder_type=getattr(args, "elder", None) or rng.choice(ELDER_TYPES),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(PLACES, params.place), _safe_lookup(RITES, params.rite), _safe_lookup(RELICS, params.relic),
                 params.hero_name, params.hero_type, params.elder_type)
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


def asp_verify() -> int:
    import asp

    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo matches Python ({len(py)} combos).")
        return 0
    print("Mismatch between clingo and Python:")
    print(" only in clingo:", sorted(cl - py))
    print(" only in python:", sorted(py - cl))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp

        model = asp.one_model(asp_program("#show valid/3."))
        print(sorted(set(asp.atoms(model, "valid"))))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [StoryParams(place=p, rite=r, relic=l, hero_name="Aster", hero_type="girl", elder_type="seer")
                   for p, r, l in valid_combos()]
        samples = [generate(p) for p in curated]
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
