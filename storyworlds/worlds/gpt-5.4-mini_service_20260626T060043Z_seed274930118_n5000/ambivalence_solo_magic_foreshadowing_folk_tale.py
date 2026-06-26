#!/usr/bin/env python3
"""
A small folk-tale storyworld about a solo wanderer, a magic charm, and the
feeling of ambivalence before a gentle choice.

The seed story premise:
- A single child or young wanderer finds a magical object in the woods.
- The object can solve a small problem, but using it alone feels both tempting
  and uneasy.
- Early signs foreshadow what the magic will cost or change.
- The ending proves the choice by changing the world state.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    kin: object | None = None
    relic: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "queen"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "king"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
class Place:
    id: str
    label: str
    indoor: bool = False
    paths: int = 0
    water: int = 0
    trees: int = 0
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
class Charm:
    id: str
    label: str
    phrase: str
    magic_kind: str
    cost_kind: str
    foreshadow: str
    fix_kind: str
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
    charm: str
    hero_name: str
    hero_type: str
    kin_name: str
    kin_type: str
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
    def __init__(self, place: Place, charm: Charm) -> None:
        self.place = place
        self.charm = charm
        self.entities: dict[str, Entity] = {}
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "woods": Place(id="woods", label="the deep woods", indoor=False, paths=1, water=1, trees=3),
    "hill": Place(id="hill", label="the windy hill", indoor=False, paths=2, water=0, trees=1),
    "village": Place(id="village", label="the edge of the village", indoor=False, paths=3, water=0, trees=1),
    "cottage": Place(id="cottage", label="the little cottage", indoor=True, paths=0, water=0, trees=0),
}

CHARMS = {
    "bell": Charm(
        id="bell",
        label="a silver bell",
        phrase="a silver bell that rang without a hand",
        magic_kind="guidance",
        cost_kind="echo",
        foreshadow="The bell gave one tiny ring before anyone touched it.",
        fix_kind="call",
    ),
    "stone": Charm(
        id="stone",
        label="a moon stone",
        phrase="a pale moon stone that held a soft blue glow",
        magic_kind="light",
        cost_kind="sleep",
        foreshadow="The stone grew warm whenever the moon hid behind clouds.",
        fix_kind="share",
    ),
    "seed": Charm(
        id="seed",
        label="a golden seed",
        phrase="a golden seed that hummed like a small hive",
        magic_kind="growth",
        cost_kind="thirst",
        foreshadow="Where the seed rested, the grass leaned toward it like listeners.",
        fix_kind="plant",
    ),
}


# ---------------------------------------------------------------------------
# Story helpers
# ---------------------------------------------------------------------------
def article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def possessive(name: str) -> str:
    return f"{name}'s"


def setup_world(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    charm = _safe_lookup(CHARMS, params.charm)
    w = World(place, charm)
    hero = w.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        meters={"tired": 0.0, "hope": 1.0},
        memes={"ambivalence": 0.0, "curiosity": 1.0, "alone": 1.0, "joy": 0.0},
    ))
    kin = w.add(Entity(
        id="kin",
        kind="character",
        type=params.kin_type,
        label=params.kin_name,
        meters={"need": 1.0},
        memes={"worry": 1.0},
    ))
    relic = w.add(Entity(
        id="relic",
        kind="thing",
        type="charm",
        label=charm.label,
        phrase=charm.phrase,
        owner=hero.id,
        meters={"magic": 1.0},
    ))
    w.facts.update(hero=hero, kin=kin, relic=relic, place=place, charm=charm)
    return w


def tell(world: World) -> World:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    kin: Entity = _safe_fact(world, world.facts, "kin")
    relic: Entity = _safe_fact(world, world.facts, "relic")
    place: Place = _safe_fact(world, world.facts, "place")
    charm: Charm = _safe_fact(world, world.facts, "charm")

    # Opening: the solo state, with a foreshadowing image.
    world.say(
        f"Once, {hero.id} walked alone through {place.label}, with only the birds for company."
    )
    world.say(
        f"Under a root and a stone, {hero.id} found {relic.phrase}."
    )
    world.say(
        f"{charm.foreshadow}"
    )

    # Middle: the ambivalence.
    world.para()
    hero.memes["ambivalence"] += 1.0
    hero.memes["hope"] += 0.5
    world.say(
        f"{hero.id} held {relic.label} in both hands and felt two thoughts tug at once."
    )
    world.say(
        f"One thought said, 'Keep it, for it is yours alone.' The other said, 'Use it to help {kin.label}.'"
    )
    if place.id in {"woods", "hill"}:
        world.say(
            f"The wind moved through the trees like a warning, and the bell of evening sounded far away."
        )
    else:
        world.say(
            f"Even the cottage window seemed to wait and listen."
        )

    # Turn: magic answers the hidden need.
    world.para()
    if charm.id == "bell":
        kin.meters["lost"] = 1.0
        world.say(
            f"At last, {hero.id} rang the bell once. The sound traveled through the {place.label}, clear as a path in snow."
        )
        world.say(
            f"{kin.label} heard it and came straight on, for {charm.magic_kind} had made the way plain."
        )
        hero.memes["ambivalence"] = 0.0
        hero.memes["joy"] += 1.0
    elif charm.id == "stone":
        kin.meters["dark"] = 1.0
        world.say(
            f"{hero.id} lifted the moon stone, and a pale light spilled over the path."
        )
        world.say(
            f"The light showed {kin.label} the little hole in the fence where {kin.pronoun('subject')} had been trying to pass."
        )
        hero.memes["ambivalence"] = 0.0
        hero.memes["joy"] += 1.0
    else:
        kin.meters["hungry"] = 1.0
        world.say(
            f"{hero.id} pressed the golden seed into the soil, and green shoots woke at once."
        )
        world.say(
            f"From the sudden sprouts came berries enough for {kin.label}, and the air smelled sweet and new."
        )
        hero.memes["ambivalence"] = 0.0
        hero.memes["joy"] += 1.0

    # Resolution: the cost is shown, but the choice is accepted.
    world.para()
    if charm.cost_kind == "echo":
        hero.meters["echo"] = 1.0
        world.say(
            f"Afterward, the bell left a faint echo in {hero.id}'s chest, but {hero.id} did not mind."
        )
    elif charm.cost_kind == "sleep":
        hero.meters["sleepy"] = 1.0
        world.say(
            f"Afterward, {hero.id} felt sleepy and warm, as if the moon had tucked {hero.pronoun('object')} in."
        )
    else:
        hero.meters["thirst"] = 1.0
        world.say(
            f"Afterward, the ground asked for rain, but the little garden had already been blessed."
        )

    world.say(
        f"{kin.label} smiled at {hero.id}, and the solo wanderer was not quite alone anymore."
    )
    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_places(charm: Charm) -> list[str]:
    if charm.id == "bell":
        return ["woods", "hill", "village"]
    if charm.id == "stone":
        return ["woods", "hill", "cottage"]
    if charm.id == "seed":
        return ["woods", "village", "cottage"]
    return []


def valid_combo(place: str, charm: str) -> bool:
    return place in valid_places(_safe_lookup(CHARMS, charm))


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for p in PLACES:
        for c in CHARMS:
            if valid_combo(p, c):
                out.append((p, c))
    return out


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, kin, charm, place = f["hero"], f["kin"], f["charm"], f["place"]
    return [
        f'Write a short folk tale for a child about {hero.id}, who is alone, finds {charm.phrase}, and feels ambivalence before making a kind choice.',
        f"Tell a simple magical story set at {place.label} where {hero.id} notices {charm.foreshadow.lower()}",
        f'Write a gentle tale in which a solo wanderer uses {article(charm.label)} {charm.label} to help {kin.label}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, kin, charm, place = f["hero"], f["kin"], f["charm"], f["place"]
    return [
        QAItem(
            question=f"Who was alone in the beginning of the tale?",
            answer=f"{hero.id} was alone in {place.label}, walking by {hero.pronoun('possessive')} self.",
        ),
        QAItem(
            question=f"What magical thing did {hero.id} find?",
            answer=f"{hero.id} found {charm.phrase}, which was {charm.label}.",
        ),
        QAItem(
            question=f"Why did {hero.id} feel ambivalent?",
            answer=f"{hero.id} wanted to keep the magic for {hero.pronoun('object')}self, but also wanted to help {kin.label}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"{hero.id} used {charm.label} to help {kin.label}, and the two were not lonely at the end.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    charm: Charm = _safe_fact(world, world.facts, "charm")
    return [
        QAItem(
            question="What is a charm in a folk tale?",
            answer="A charm is a small special object that can do magic or bring luck in a story.",
        ),
        QAItem(
            question="What does ambivalence mean?",
            answer="Ambivalence means feeling two opposite ways at the same time, like wanting to do something and feeling unsure about it.",
        ),
        QAItem(
            question="What is a foreshadowing clue?",
            answer="A foreshadowing clue is a little hint that tells readers something important may happen later.",
        ),
        QAItem(
            question=f"What kind of magic does {charm.label} have?",
            answer=f"{charm.label.capitalize()} has {charm.magic_kind} magic, so it changes how the path or problem is seen.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={meters} memes={memes}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(P) :- place_fact(P).
charm(C) :- charm_fact(C).
valid(P,C) :- place_fact(P), charm_fact(C), combo_ok(P,C).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place_fact", pid))
    for cid in CHARMS:
        lines.append(asp.fact("charm_fact", cid))
    for p, c in valid_combos():
        lines.append(asp.fact("combo_ok", p, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asps = set(asp_valid_combos())
    if py == asps:
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
        return 0
    print("Mismatch between ASP and Python gates.")
    print("Only in Python:", sorted(py - asps))
    print("Only in ASP:", sorted(asps - py))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
NAME_POOL = {
    "girl": ["Mira", "Lina", "Sana", "Tova", "Eira"],
    "boy": ["Jorin", "Pavel", "Niko", "Bram", "Arin"],
}
KIN_POOL = {
    "girl": ("sister", "little sister"),
    "boy": ("brother", "little brother"),
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small folk-tale world about ambivalence, a solo wanderer, and magic.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--charm", choices=sorted(CHARMS))
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--kin-name")
    ap.add_argument("--kin-type", choices=["girl", "boy"])
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
    if getattr(args, "place", None) and getattr(args, "charm", None) and not valid_combo(getattr(args, "place", None), getattr(args, "charm", None)):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place = getattr(args, "place", None) or rng.choice(sorted(PLACES))
    charm = getattr(args, "charm", None) or rng.choice(sorted(CHARMS))
    if not valid_combo(place, charm):
        combos = [p for p in valid_combos() if (getattr(args, "place", None) is None or p[0] == getattr(args, "place", None)) and (getattr(args, "charm", None) is None or p[1] == getattr(args, "charm", None))]
        if not combos:
            return _fallback_storyparams(args, rng, StoryParams, globals())
        place, charm = rng.choice(combos)
    hero_type = getattr(args, "hero_type", None) or rng.choice(["girl", "boy"])
    kin_type = getattr(args, "kin_type", None) or hero_type
    hero_name = getattr(args, "hero_name", None) or rng.choice(NAME_POOL[hero_type])
    kin_name = getattr(args, "kin_name", None) or rng.choice(["Nari", "Bela", "Ivo", "Maren", "Oren"])
    if hero_name == kin_name:
        kin_name = kin_name + "kin"
    return StoryParams(place=place, charm=charm, hero_name=hero_name, hero_type=hero_type, kin_name=kin_name, kin_type=kin_type)


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    tell(world)
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combo(s):")
        for p, c in combos:
            print(f"  {p} / {c}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [
            StoryParams(place="woods", charm="bell", hero_name="Mira", hero_type="girl", kin_name="Oren", kin_type="boy"),
            StoryParams(place="hill", charm="stone", hero_name="Jorin", hero_type="boy", kin_name="Bela", kin_type="girl"),
            StoryParams(place="village", charm="seed", hero_name="Sana", hero_type="girl", kin_name="Ivo", kin_type="boy"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
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
            header = f"### {p.hero_name}: {p.place} / {p.charm}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
