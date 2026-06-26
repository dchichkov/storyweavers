#!/usr/bin/env python3
"""
A small myth-styled story world about a hobo on a quest for pardon, carrying
semolina as an offering and changing the hearts of the gatekeepers through a
physical journey and an emotional turn.

The premise is simple: a hobo comes to a city gate after a wrong once done.
The tension is whether the gatekeeper will grant pardon. The turn is a quest
through a hard place where the hobo gathers semolina for a humble gift. The
resolution is a pardon earned by persistence, honesty, and shared bread.
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
    worn_by: Optional[str] = None
    portable: bool = True
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    gate: object | None = None
    hobo: object | None = None
    pardon: object | None = None
    semolina: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"hobo", "man", "boy", "king", "priest"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"woman", "girl", "queen", "priestess"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
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
    kind: str
    offers: set[str] = field(default_factory=set)
    hard: bool = False
    holy: bool = False
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
class Quest:
    id: str
    goal: str
    offering: str
    trial: str
    reward: str
    required_place: str
    offering_item: str = "semolina"
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
    def __init__(self, place: Place, quest: Quest) -> None:
        self.place = place
        self.quest = quest
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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

        clone = World(self.place, self.quest)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _add_meter(ent: Entity, key: str, amount: float) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amount


def _add_meme(ent: Entity, key: str, amount: float) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


def _rule_weariness(world: World) -> list[str]:
    out: list[str] = []
    hobo = world.get("hobo")
    if hobo.meters.get("road", 0.0) >= 2 and ("weariness",) not in world.fired:
        world.fired.add(("weariness",))
        _add_meme(hobo, "resolve", 1.0)
        out.append("The road made the hobo tired, but it also made his will harder.")
    return out


def _rule_grace(world: World) -> list[str]:
    out: list[str] = []
    hobo = world.get("hobo")
    gate = world.get("gatekeeper")
    pardon = world.get("pardon")
    if pardon.meters.get("offered", 0.0) >= 1 and hobo.memes.get("humility", 0.0) >= 1:
        sig = ("grace",)
        if sig not in world.fired:
            world.fired.add(sig)
            _add_meme(gate, "softness", 1.0)
            _add_meme(hobo, "hope", 1.0)
            out.append("The gatekeeper's stern face softened like stone warmed by dawn.")
    return out


def _rule_pardon(world: World) -> list[str]:
    hobo = world.get("hobo")
    gate = world.get("gatekeeper")
    pardon = world.get("pardon")
    if hobo.memes.get("honesty", 0.0) >= 1 and gate.memes.get("softness", 0.0) >= 1:
        sig = ("pardon",)
        if sig not in world.fired:
            world.fired.add(sig)
            pardon.meters["granted"] = 1.0
            _add_meme(hobo, "relief", 1.0)
            _add_meme(gate, "mercy", 1.0)
            return ["__pardon__"]
    return []


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_rule_weariness, _rule_grace, _rule_pardon):
            sents = rule(world)
            if sents:
                changed = True
                for s in sents:
                    if s != "__pardon__":
                        produced.append(s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tell(place: Place, quest: Quest, hero_name: str = "Rook", gatekeeper_name: str = "Elder", seed: Optional[int] = None) -> World:
    world = World(place, quest)
    hobo = world.add(Entity(id="hobo", kind="character", type="hobo", label=hero_name))
    gate = world.add(Entity(id="gatekeeper", kind="character", type="priest", label=gatekeeper_name))
    semolina = world.add(Entity(id="semolina", type="semolina", label="semolina", phrase="a sack of semolina", owner="hobo"))
    pardon = world.add(Entity(id="pardon", type="pardon", label="pardon", phrase="a pardon from the gate", owner="gatekeeper"))

    _add_meme(hobo, "need", 1.0)
    _add_meme(hobo, "shame", 1.0)

    world.say(
        f"In {place.label}, a hobo named {hobo.label} came with empty hands and a heavy heart."
    )
    world.say(
        f"He had heard of a pardon kept behind the gate, but the gate would not open for old grief alone."
    )

    world.para()
    world.say(
        f"So the hobo began a quest through the hard road beyond the walls, searching for semolina."
    )
    _add_meter(hobo, "road", 1.0)
    _add_meter(semolina, "found", 1.0)
    _add_meme(hobo, "hope", 1.0)
    world.say(
        f"At last he found semolina in a market bowl, and he bought it with the last coin in his pocket."
    )
    world.say(
        f"He set the sack on his shoulder like a small white moon and walked back to the gate."
    )

    world.para()
    world.say(
        f"The gatekeeper asked what the hobo wanted from the city."
    )
    _add_meme(hobo, "honesty", 1.0)
    world.say(
        f"The hobo bowed his head and said he wanted pardon for the wrong he had done."
    )
    world.say(
        f"He offered the semolina as a humble gift and promised to share bread instead of taking what was not his."
    )
    semolina.meters["offered"] = 1.0
    pardon.meters["offered"] = 1.0

    propagate(world, narrate=True)

    world.para()
    if pardon.meters.get("granted", 0.0) >= 1:
        world.say(
            f"The gatekeeper granted pardon, and the hobo entered the city with lighter steps."
        )
        world.say(
            f"That night, semolina was baked into warm bread, and the hobo slept without fear for the first time in many days."
        )
    else:
        pass

    world.facts.update(
        hobo=hobo,
        gatekeeper=gate,
        semolina=semolina,
        pardon=pardon,
        place=place,
        quest=quest,
    )
    return world


PLACES = {
    "gate": Place(
        id="gate",
        label="the city gate",
        kind="gate",
        offers={"quest"},
        hard=True,
        holy=True,
    ),
    "market": Place(
        id="market",
        label="the night market",
        kind="market",
        offers={"quest"},
        hard=False,
        holy=False,
    ),
    "road": Place(
        id="road",
        label="the long road",
        kind="road",
        offers={"quest"},
        hard=True,
        holy=False,
    ),
}

QUESTS = {
    "pardon": Quest(
        id="pardon",
        goal="seek pardon",
        offering="semolina",
        trial="ask for mercy with an honest heart",
        reward="pardon",
        required_place="gate",
        offering_item="semolina",
    )
}

NAMES = ["Rook", "Ivo", "Soren", "Milo", "Bram", "Toma", "Ari"]
GATEKEEPER_NAMES = ["Elder", "Abbot", "Keeper", "Watcher"]


@dataclass
class StoryParams:
    place: str
    quest: str
    name: str
    gatekeeper: str
    seed: Optional[int] = None
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic quest world: a hobo seeks pardon with semolina.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--name")
    ap.add_argument("--gatekeeper")
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


def reasonableness_gate(place: Place, quest: Quest) -> bool:
    return quest.id == "pardon" and place.id == "gate" and place.holy and place.hard


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or "gate"
    quest = getattr(args, "quest", None) or "pardon"
    if not reasonableness_gate(_safe_lookup(PLACES, place), _safe_lookup(QUESTS, quest)):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    name = getattr(args, "name", None) or rng.choice(NAMES)
    gatekeeper = getattr(args, "gatekeeper", None) or rng.choice(GATEKEEPER_NAMES)
    return StoryParams(place=place, quest=quest, name=name, gatekeeper=gatekeeper)


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a short myth about a hobo who goes on a quest for pardon and brings semolina to the gate.",
        f"Tell a child-facing legend where {world.facts['hobo'].label} asks for pardon after a long road and a humble offering.",
        "Make the ending feel like mercy arrived at the city gate and bread was shared.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hobo = _safe_fact(world, world.facts, "hobo")
    gatekeeper = _safe_fact(world, world.facts, "gatekeeper")
    return [
        QAItem(
            question=f"Who went on the quest for pardon?",
            answer=f"The hobo named {hobo.label} went on the quest for pardon.",
        ),
        QAItem(
            question=f"What did the hobo bring to the gate?",
            answer=f"He brought semolina as a humble offering.",
        ),
        QAItem(
            question=f"Who granted the pardon at the end?",
            answer=f"The gatekeeper named {gatekeeper.label} granted the pardon.",
        ),
        QAItem(
            question="Why did the story feel like a myth?",
            answer="It followed an old, serious journey with a hard road, a holy gate, an offering, and mercy at the end.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is semolina?",
            answer="Semolina is a coarse flour made from wheat, often used to make bread, porridge, or pasta.",
        ),
        QAItem(
            question="What does pardon mean?",
            answer="Pardon means forgiveness for a wrong, so someone is allowed to move on without punishment.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a long search or journey to reach an important goal.",
        ),
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
place(gate).
quest(pardon).

hard(gate).
holy(gate).

reasonably_valid(P, Q) :- place(P), quest(Q), hard(P), holy(P), P = gate, Q = pardon.

#show reasonably_valid/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.hard:
            lines.append(asp.fact("hard", pid))
        if p.holy:
            lines.append(asp.fact("holy", pid))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show reasonably_valid/2."))
    return sorted(set(asp.atoms(model, "reasonably_valid")))


def asp_verify() -> int:
    py = {("gate", "pardon")} if reasonableness_gate(PLACES["gate"], QUESTS["pardon"]) else set()
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(cl)} valid quest).")
        return 0
    print("MISMATCH between clingo and Python gate.")
    print("python:", sorted(py))
    print("clingo:", sorted(cl))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(PLACES, params.place), _safe_lookup(QUESTS, params.quest), params.name, params.gatekeeper, params.seed)
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
    StoryParams(place="gate", quest="pardon", name="Rook", gatekeeper="Elder"),
    StoryParams(place="gate", quest="pardon", name="Milo", gatekeeper="Watcher"),
    StoryParams(place="gate", quest="pardon", name="Soren", gatekeeper="Abbot"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show reasonably_valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("Valid quest models:")
        for item in asp_valid():
            print(" ", item)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError:
                continue
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not getattr(args, "all", None) else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
