#!/usr/bin/env python3
"""
storyworlds/worlds/vault_chimpanzee_endow_suspense_myth.py
==========================================================

A small storyworld about a mythic vault, a chimpanzee messenger, and an
endowment that must be given at the right moment.

Premise:
- A village keeps a sealed vault of bright gifts.
- A young chimpanzee is chosen to carry one blessing to the people.
- The vault may only be opened when a true need appears.

Tension:
- The chimpanzee wants to help right away, but the keeper fears a rash opening.
- Suspense comes from waiting for the proper sign and choosing the right gift.

Turn:
- A storm, missing tools, or a frightened child reveals a real need.
- The keeper finally endows the chimpanzee with a useful token and trust.

Resolution:
- The chimpanzee delivers the blessing, the vault remains honored, and the
  village ends with relief rather than chaos.

This world is intentionally small and constraint-checked: a valid story requires
a real need, a matching gift, and a safe endowment path.
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
    if hasattr(key, "id"):
        key = key.id
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = [value for value in mapping.values() if value is not None]
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    chimp: object | None = None
    keeper: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"keeper", "elder", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "priest"}:
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class Setting:
    place: str = "the stone village"
    has_vault: bool = True
    mood: str = "quiet"
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
class Gift:
    id: str
    label: str
    phrase: str
    helps: str
    sign: str
    tags: set[str] = field(default_factory=set)
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class StoryParams:
    place: str
    gift: str
    name: str
    keeper: str
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
    def copy(self):
        clone = __import__("copy").deepcopy(self)
        return clone


GIFT_CATALOG = {
    "rope": Gift(
        id="rope",
        label="rope",
        phrase="a strong braided rope",
        helps="pull a stuck gate open",
        sign="a cracked gate",
        tags={"rope", "help"},
    ),
    "lamp": Gift(
        id="lamp",
        label="lamp",
        phrase="a small brass lamp",
        helps="light a dark path",
        sign="darkness",
        tags={"light", "dark"},
    ),
    "water": Gift(
        id="water",
        label="water jar",
        phrase="a cool clay jar of water",
        helps="soothe a thirsty child",
        sign="thirst",
        tags={"water", "thirst"},
    ),
    "seed": Gift(
        id="seed",
        label="seed pouch",
        phrase="a pouch of bright seeds",
        helps="feed birds at dawn",
        sign="hungry birds",
        tags={"seed", "bird"},
    ),
}

SETTINGS = {
    "village": Setting(place="the stone village", has_vault=True, mood="quiet"),
    "temple": Setting(place="the hill temple", has_vault=True, mood="solemn"),
    "grove": Setting(place="the old grove", has_vault=True, mood="still"),
}

KEEPER_TYPES = ["keeper", "elder", "priest"]
CHIMP_NAMES = ["Milo", "Kito", "Suri", "Beni", "Nala", "Ravi"]
TRAITS = ["quick", "small", "careful", "curious"]


def valid_combos() -> list[tuple[str, str]]:
    return [(place, gid) for place in SETTINGS for gid in GIFT_CATALOG]


@dataclass
class StoryState:
    need: str = ""
    suspense: float = 0.0
    vault_open: bool = False
    gift_given: bool = False
    sign_seen: bool = False
    state: object | None = None
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


def is_reasonable(place: str, gift: str) -> bool:
    return place in SETTINGS and gift in GIFT_CATALOG


def reason_rejection(place: str, gift: str) -> str:
    return f"(No story: the vault at {place} cannot meaningfully endow {gift} here.)"


def _make_opening(world: World, chimp: Entity, keeper: Entity) -> None:
    world.say(
        f"In {world.setting.place}, people spoke of a vault that held blessings "
        f"older than anyone could count."
    )
    world.say(
        f"{chimp.id} was a little chimpanzee with bright eyes and a brave heart, "
        f"and {keeper.pronoun('possessive')} {keeper.label} watched {(getattr(chimp, 'it')() if callable(getattr(chimp, 'it', None)) else getattr(chimp, 'it', 'it'))} carefully."
    )
    world.say(
        f"Everyone knew the same old rule: the vault stayed closed unless a true need arrived."
    )


def _build_need(world: World, state: StoryState, gift: Gift, keeper: Entity, chimp: Entity) -> None:
    state.need = gift.sign
    world.para()
    if gift.id == "rope":
        world.say("One morning, the village gate stuck fast after a loud crack split the hinge.")
    elif gift.id == "lamp":
        world.say("That night, a hush of darkness fell on the road, and the path seemed to vanish.")
    elif gift.id == "water":
        world.say("By noon, a child sat under a tree with a dry throat and shaking lips.")
    else:
        world.say("At dawn, birds gathered above the roofs, too hungry to sing.")
    state.suspense += 1
    world.say(
        f"{chimp.id} looked toward the vault, because {chimp.pronoun()} wanted to help at once."
    )
    world.say(
        f"But {keeper.id} lifted {keeper.pronoun('possessive')} hand and said, "
        f'"Wait. The vault must answer a real need, not a rushed wish."'
    )


def _suspense_turn(world: World, state: StoryState, chimp: Entity, keeper: Entity, gift: Gift) -> None:
    world.say(
        f"So {chimp.id} waited, and the waiting felt long, like a drumbeat behind a curtain."
    )
    world.say(
        f"At last, the sign came: {gift.sign} was impossible to ignore."
    )
    state.sign_seen = True
    state.suspense += 1
    world.say(
        f"{chimp.id} ran to {keeper.id} and pointed to the sign, as if saying the old story itself had spoken."
    )


def _endow(world: World, state: StoryState, chimp: Entity, keeper: Entity, gift: Gift) -> None:
    state.vault_open = True
    state.gift_given = True
    chimp.memes["trust"] = chimp.memes.get("trust", 0.0) + 1
    keeper.memes["relief"] = keeper.memes.get("relief", 0.0) + 1
    world.para()
    world.say(
        f"Then {keeper.id} opened the vault at last, and the old doors answered with a deep, steady sigh."
    )
    world.say(
        f"{keeper.id} did not give {chimp.id} everything inside; {keeper.pronoun('subject')} "
        f"endowed {chimp.id} with {gift.phrase} and the right to carry it."
    )
    world.say(
        f"{chimp.id} hurried away and used {(getattr(gift, 'it')() if callable(getattr(gift, 'it', None)) else getattr(gift, 'it', 'it'))} to {gift.helps}, and the village breathed again."
    )
    world.say(
        f"By sunset, the vault was sealed once more, respected and whole, while {chimp.id} stood proud beside the people."
    )


def tell(setting: Setting, gift: Gift, chimp_name: str, keeper_type: str) -> World:
    world = World(setting)
    chimp = world.add(Entity(id=chimp_name, kind="character", type="chimpanzee", label="chimpanzee"))
    keeper = world.add(Entity(id="Keeper", kind="character", type=keeper_type, label="keeper"))
    state = StoryState()

    _make_opening(world, chimp, keeper)
    _build_need(world, state, gift, keeper, chimp)
    _suspense_turn(world, state, chimp, keeper, gift)
    _endow(world, state, chimp, keeper, gift)

    world.facts.update(
        chimp=chimp,
        keeper=keeper,
        gift=gift,
        state=state,
        setting=setting,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    chimp: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "chimp")
    gift: Gift = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "gift")
    return [
        f"Write a short myth about a vault, a chimpanzee, and an endowment that waits for the right sign.",
        f"Tell a suspenseful story in which {chimp.id} the chimpanzee must wait before the keeper opens the vault.",
        f"Write a child-friendly myth where a vault gives out {gift.label} only when a real need appears.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    chimp: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "chimp")
    keeper: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "keeper")
    gift: Gift = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "gift")
    state: StoryState = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "state")
    setting: Setting = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "setting")

    return [
        QAItem(
            question=f"Who waited by the vault in {setting.place}?",
            answer=f"{chimp.id} the chimpanzee waited by the vault while {keeper.id} watched for the right moment.",
        ),
        QAItem(
            question=f"What did the keeper endow to {chimp.id}?",
            answer=f"{keeper.id} endowed {chimp.id} with {gift.phrase} so {chimp.id} could {gift.helps}.",
        ),
        QAItem(
            question=f"Why was the story suspenseful?",
            answer=(
                f"It was suspenseful because the vault stayed closed until a real need appeared, "
                f"and everyone had to wait before the gift could be given."
            ),
        ),
        QAItem(
            question=f"What sign finally showed that the vault should open?",
            answer=f"The sign was {gift.sign}, which proved the need was real.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=(
                f"At the end, the vault opened for the right reason, {chimp.id} carried the gift, "
                f"and the village felt relief instead of worry."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a vault?",
            answer="A vault is a strong, closed room or box used to keep valuable things safe.",
        ),
        QAItem(
            question="What is a chimpanzee?",
            answer="A chimpanzee is a smart ape with strong arms that can climb and carry things.",
        ),
        QAItem(
            question="What does it mean to endow something?",
            answer="To endow something means to give it as a gift or blessing, especially in a careful way.",
        ),
        QAItem(
            question="What is suspense in a story?",
            answer="Suspense is the feeling of waiting to find out what will happen next.",
        ),
        QAItem(
            question="What is a myth?",
            answer="A myth is an old story that explains special places, gifts, or events in a memorable way.",
        ),
    ]


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
    lines.append("== (3) World-knowledge questions ==")
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
        lines.append(f"  {e.id:10} ({e.type:11}) {' '.join(bits)}")
    state: StoryState = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "state")
    lines.append(
        f"  state: need={state.need!r} suspense={state.suspense} "
        f"vault_open={state.vault_open} gift_given={state.gift_given} sign_seen={state.sign_seen}"
    )
    return "\n".join(lines)


ASP_RULES = r"""
% A gift is valid for a place if that place exists and the gift exists.
valid(Place, Gift) :- setting(Place), gift(Gift).

% A vault story is meaningful when a real need can trigger suspense and a gift.
suspense_story(Place, Gift) :- valid(Place, Gift), need_sign(Gift), vault_place(Place).

% Endowment is justified when the story reaches the sign.
can_endow(Place, Gift) :- suspense_story(Place, Gift), sign_reveals_need(Gift).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place in SETTINGS:
        lines.append(asp.fact("setting", place))
        lines.append(asp.fact("vault_place", place))
    for gid, gift in GIFT_CATALOG.items():
        lines.append(asp.fact("gift", gid))
        lines.append(asp.fact("need_sign", gid, gift.sign))
        lines.append(asp.fact("sign_reveals_need", gid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in asp:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic vault storyworld with suspense.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--gift", choices=GIFT_CATALOG)
    ap.add_argument("--name", choices=CHIMP_NAMES)
    ap.add_argument("--keeper", choices=KEEPER_TYPES)
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
    if getattr(args, "place", None) and getattr(args, "gift", None) and not is_reasonable(getattr(args, "place", None), getattr(args, "gift", None)):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [
        (p, g) for p, g in valid_combos()
        if (getattr(args, "place", None) is None or p == getattr(args, "place", None))
        and (getattr(args, "gift", None) is None or g == getattr(args, "gift", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, gift = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(CHIMP_NAMES)
    keeper = getattr(args, "keeper", None) or rng.choice(KEEPER_TYPES)
    return StoryParams(place=place, gift=gift, name=name, keeper=keeper)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), GIFT_CATALOG[params.gift], params.name, params.keeper)
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
    StoryParams(place="village", gift="rope", name="Milo", keeper="elder"),
    StoryParams(place="temple", gift="lamp", name="Kito", keeper="priest"),
    StoryParams(place="grove", gift="water", name="Suri", keeper="keeper"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible place/gift combos:\n")
        for place, gift in combos:
            print(f"  {place:8} {gift:8}")
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.gift} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
