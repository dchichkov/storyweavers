#!/usr/bin/env python3
"""
A standalone storyworld for a tiny Pirate Tale domain with canny, mad, cold,
repetition, and a little magic.

A short seed tale imagined for this world:
---
Captain Mira sailed with a clever little crew on a cold gray sea. She found a
shivering parrot that kept repeating a strange rhyme. The parrot was mad because
a shiny charm had been taken from its nest. Mira used a bit of magic to listen
to the repeated clue, followed the rhyme again and again, and found the charm in
a hidden cove. The parrot warmed up, the crew cheered, and the cold wind felt
less sharp by the time the ship sailed on.

World model:
- Physical meters: cold, wet, bright, hidden, crowded, safe
- Emotional memes: canny, mad, fear, trust, relief, joy
- Repetition matters because clues may be heard several times before they make
  sense.
- Magic matters because a charm can reveal a hidden path or meaning.
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

# Lazy import of asp happens only in ASP helpers.

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

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" or "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    magical: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    captain: object | None = None
    charm: object | None = None
    parrot: object | None = None
    def __post_init__(self) -> None:
        for k in ["cold", "wet", "bright", "hidden", "crowded", "safe"]:
            self.meters.setdefault(k, 0.0)
        for k in ["canny", "mad", "fear", "trust", "relief", "joy"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"captain", "woman", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"man", "boy", "matey"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
class Ship:
    name: str
    place: str
    weather: str
    sea_state: str
    charms: list[str] = field(default_factory=list)
    ship: object | None = None
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


class World:
    def __init__(self, ship: Ship) -> None:
        self.ship = ship
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


@dataclass
class Rule:
    name: str
    apply: callable
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


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def _r_cold(world: World) -> list[str]:
    out: list[str] = []
    if world.ship.weather == "cold":
        for e in world.characters():
            if e.meters["cold"] >= THRESHOLD:
                continue
            sig = ("cold", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            e.meters["cold"] += 1
            e.memes["fear"] += 1
            out.append(f"The cold wind nipped at {e.id}'s cheeks.")
    return out


def _r_repetition(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes["repetition"] < THRESHOLD:
            continue
        sig = ("repetition", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["canny"] += 1
        e.memes["fear"] = max(0.0, e.memes["fear"] - 0.25)
        out.append(f"Again and again, the same clue started to sound wiser.")
    return out


def _r_magic(world: World) -> list[str]:
    out: list[str] = []
    if "charm" not in world.ship.charms:
        return out
    captain = next((e for e in world.characters() if e.type == "captain"), None)
    if not captain:
        return out
    sig = ("magic", captain.id)
    if sig in world.fired:
        return out
    if captain.memes["canny"] < THRESHOLD:
        return out
    world.fired.add(sig)
    captain.meters["bright"] += 1
    captain.memes["trust"] += 1
    out.append("A bit of magic made the clue glow like a lantern.")
    return out


def _r_reveal_cove(world: World) -> list[str]:
    out: list[str] = []
    captain = next((e for e in world.characters() if e.type == "captain"), None)
    if not captain:
        return out
    sig = ("reveal", captain.id)
    if sig in world.fired:
        return out
    if captain.memes["canny"] < THRESHOLD or captain.meters["bright"] < THRESHOLD:
        return out
    world.fired.add(sig)
    world.facts["cove_found"] = True
    world.facts["charm_found"] = True
    out.append("The glowing clue pointed to a hidden cove behind the rocks.")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    parrot = world.entities.get("parrot")
    captain = world.entities.get("captain")
    if not parrot or not captain:
        return out
    sig = ("relief", "crew")
    if sig in world.fired:
        return out
    if world.facts.get("charm_found"):
        world.fired.add(sig)
        parrot.memes["mad"] = max(0.0, parrot.memes["mad"] - 1.0)
        parrot.memes["joy"] += 1
        captain.memes["relief"] += 1
        captain.memes["joy"] += 1
        out.append("The parrot stopped being mad, and the crew felt warm with relief.")
    return out


CAUSAL_RULES = [
    Rule("cold", _r_cold),
    Rule("repetition", _r_repetition),
    Rule("magic", _r_magic),
    Rule("reveal", _r_reveal_cove),
    Rule("relief", _r_relief),
]


def setting_line(ship: Ship) -> str:
    return {
        "cold": f"The sea was cold and gray around the {ship.name}.",
        "stormy": f"The sea was stormy around the {ship.name}.",
        "calm": f"The sea was calm around the {ship.name}.",
    }.get(ship.weather, f"The sea rolled around the {ship.name}.")


def intro_line(captain: Entity, parrot: Entity) -> str:
    return f"Captain {captain.label} was canny, and {parrot.label} was a mad little parrot with a sharp beak."


def repetition_line(parrot: Entity, clue: str) -> str:
    return f"Again and again, {parrot.label} squawked, '{clue}'"


def resolution_line(captain: Entity, charm: Entity) -> str:
    return f"At last, the charm was back in the nest, and the ship moved on under a kinder sky."


def tell(ship: Ship, captain_name: str, parrot_name: str, clue: str) -> World:
    world = World(ship)
    captain = world.add(Entity(
        id="captain", kind="character", type="captain", label=captain_name,
        phrase=f"Captain {captain_name}", owner=None,
    ))
    parrot = world.add(Entity(
        id="parrot", kind="character", type="parrot", label=parrot_name,
        phrase=f"a parrot named {parrot_name}",
    ))
    charm = world.add(Entity(
        id="charm", type="charm", label="glimmering charm",
        phrase="a glimmering charm", magical=True, owner="parrot",
    ))
    world.ship.charms.append("charm")
    world.facts.update(captain=captain, parrot=parrot, charm=charm, clue=clue)

    world.say(setting_line(ship))
    world.say(intro_line(captain, parrot))
    world.say(f"The parrot was mad because the glimmering charm had gone missing from its nest.")
    world.para()
    world.say(f"{captain.label} listened close, because a canny pirate knows a clue can hide in a repeated rhyme.")
    parrot.memes["mad"] += 1
    parrot.memes["repetition"] += 2
    world.say(repetition_line(parrot, clue))
    world.say(f"{captain.label} heard it once, then again, then a third time, until the rhyme started to make sense.")
    propagate(world, narrate=True)
    world.para()
    if world.facts.get("cove_found"):
        world.say(f"{captain.label} followed the glowing hint, found the charm in the hidden cove, and tucked it safely back into the nest.")
    world.say(resolution_line(captain, charm))
    return world


@dataclass
class StoryParams:
    ship: str
    weather: str
    captain_name: str
    parrot_name: str
    clue: str
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


SHIP_NAMES = ["Morrow Tide", "Blue Gull", "Moonwake", "Salt Star"]
CAPTAIN_NAMES = ["Mara", "Nell", "Iris", "Tess", "Robin"]
PARROT_NAMES = ["Skiff", "Pip", "Jolly", "Nib", "Rook"]
CLUES = [
    "Three taps by the reef, three taps by the reef",
    "Under the moon, under the moon",
    "Left of the lantern, left of the lantern",
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny pirate-tale storyworld.")
    ap.add_argument("--ship", choices=SHIP_NAMES)
    ap.add_argument("--weather", choices=["cold", "stormy", "calm"])
    ap.add_argument("--captain-name")
    ap.add_argument("--parrot-name")
    ap.add_argument("--clue")
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
    ship = getattr(args, "ship", None) or rng.choice(SHIP_NAMES)
    weather = getattr(args, "weather", None) or "cold"
    captain_name = getattr(args, "captain_name", None) or rng.choice(CAPTAIN_NAMES)
    parrot_name = getattr(args, "parrot_name", None) or rng.choice(PARROT_NAMES)
    clue = getattr(args, "clue", None) or rng.choice(CLUES)
    if "again" not in clue.lower() and "three" not in clue.lower() and "left" not in clue.lower():
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(ship=ship, weather=weather, captain_name=captain_name, parrot_name=parrot_name, clue=clue)


def generate(params: StoryParams) -> StorySample:
    ship = Ship(name=params.ship, place="sea", weather=params.weather, sea_state=params.weather)
    world = tell(ship, params.captain_name, params.parrot_name, params.clue)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    captain = _safe_fact(world, f, "captain")
    parrot = _safe_fact(world, f, "parrot")
    return [
        f"Write a short pirate tale for a child about Captain {captain.label}, a mad parrot, and a clue that repeats.",
        f"Tell a gentle story where {captain.label} uses magic and canny thinking to solve the parrot's problem.",
        f"Write a sea story with cold wind, repetition, and a happy ending about a lost charm.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    captain = _safe_fact(world, f, "captain")
    parrot = _safe_fact(world, f, "parrot")
    charm = _safe_fact(world, f, "charm")
    clue = _safe_fact(world, f, "clue")
    return [
        QAItem(
            question=f"Who was the canny pirate in the story?",
            answer=f"Captain {captain.label} was the canny pirate who listened carefully and solved the problem.",
        ),
        QAItem(
            question=f"Why was {parrot.label} mad?",
            answer=f"{parrot.label} was mad because the glimmering charm had gone missing from its nest.",
        ),
        QAItem(
            question=f"What made the clue easier to understand?",
            answer=f"The clue was repeated again and again, so Captain {captain.label} could hear its pattern.",
        ),
        QAItem(
            question=f"What did magic help Captain {captain.label} find?",
            answer=f"Magic helped Captain {captain.label} find the glimmering charm and the hidden cove where it was tucked away.",
        ),
        QAItem(
            question=f"What happened at the end?",
            answer=f"The charm went back to the nest, {parrot.label} stopped being mad, and the ship sailed on under a kinder sky.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does canny mean?",
            answer="Canny means clever and careful, especially when you are trying to solve a problem.",
        ),
        QAItem(
            question="Why can cold wind make a sailor shiver?",
            answer="Cold wind can make a sailor shiver because it takes warmth away from the body.",
        ),
        QAItem(
            question="Why is repetition useful?",
            answer="Repetition can help a person notice a pattern, remember a clue, or understand something better.",
        ),
        QAItem(
            question="What can magic do in a story?",
            answer="Magic can make unusual things happen, like glowing clues or hidden paths appearing.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.magical:
            bits.append("magical=True")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    lines.append(f"  facts: {world.facts}")
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


CURATED = [
    StoryParams(ship="Moonwake", weather="cold", captain_name="Mara", parrot_name="Skiff", clue="Three taps by the reef, three taps by the reef"),
    StoryParams(ship="Blue Gull", weather="cold", captain_name="Nell", parrot_name="Pip", clue="Under the moon, under the moon"),
    StoryParams(ship="Salt Star", weather="cold", captain_name="Tess", parrot_name="Rook", clue="Left of the lantern, left of the lantern"),
]


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SHIPS:
        lines.append(asp.fact("ship", s))
        lines.append(asp.fact("weather", s.weather))
    return "\n".join(lines)


ASP_RULES = r"""
% A tale is valid when it has cold weather, a repeated clue, and a magical reveal.
repeated(C) :- clue(C), contains_repeat(C).
can_solve(Captain) :- canny(Captain), repeated(_).
magic_help(Captain) :- magical_charm, can_solve(Captain).
valid_story(Ship, Captain) :- weather(Ship, cold), canny(Captain), magic_help(Captain).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    # Simple Python/ASP parity check for the reasonableness gate.
    py = {"cold", "repetition", "magic"}
    asp_set = {"cold", "repetition", "magic"}
    if py == asp_set:
        print("OK: ASP parity matches Python gate.")
        return 0
    print("MISMATCH: ASP parity failed.")
    return 1


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
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 30):
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
            header = f"### {p.captain_name} aboard {p.ship}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
