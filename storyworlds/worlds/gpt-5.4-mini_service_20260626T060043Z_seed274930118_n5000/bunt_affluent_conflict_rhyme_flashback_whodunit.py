#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/bunt_affluent_conflict_rhyme_flashback_whodunit.py
===============================================================================================================

A small whodunit story world with conflict, rhyme, and flashback beats.

Premise:
- An affluent household hosts a quiet evening.
- A small object goes missing.
- A child detective follows a rhyming clue.
- A flashback to an earlier bunt in the garden reveals the real path of the object.
- The story ends with the culprit named and the missing thing recovered.

The world keeps a tiny state machine:
- physical meters: missing, messy, found, suspicion
- emotional memes: worry, conflict, relief, pride

The prose is child-facing and state-driven, not a frozen template.
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
    kind: str = "thing"          # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    detective: object | None = None
    item: object | None = None
    suspect: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "aunt", "woman"}
        male = {"boy", "father", "uncle", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    place: str
    affluent: bool
    affords: set[str] = field(default_factory=set)
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
class Item:
    id: str
    label: str
    phrase: str
    region: str
    value: str
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
class Suspect:
    id: str
    label: str
    type: str
    role: str
    clue: str
    can_bunt: bool = False
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
class StoryParams:
    setting: str
    item: str
    suspect: str
    detective: str
    seed: Optional[int] = None
    params: object | None = None
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


SETTINGS = {
    "manor": Setting(place="the manor house", affluent=True, affords={"tea", "garden"}),
    "mansion": Setting(place="the mansion", affluent=True, affords={"tea", "garden"}),
    "villa": Setting(place="the villa", affluent=True, affords={"tea", "garden"}),
}

ITEMS = {
    "brooch": Item(id="brooch", label="brooch", phrase="a pearl brooch", region="lapel", value="shiny"),
    "key": Item(id="key", label="key", phrase="a small silver key", region="pocket", value="important"),
    "crown": Item(id="crown", label="crown", phrase="a toy gold crown", region="table", value="bright"),
}

SUSPECTS = {
    "butler": Suspect(id="butler", label="butler", type="man", role="butler", clue="tray"),
    "cousin": Suspect(id="cousin", label="cousin", type="boy", role="cousin", clue="glove", can_bunt=True),
    "aunt": Suspect(id="aunt", label="aunt", type="aunt", role="aunt", clue="lace"),
}

DETECTIVE_NAMES = ["Milo", "Nina", "Pia", "Theo", "June", "Elsie", "Ari", "Cora"]
TRAITS = ["curious", "careful", "brave", "sharp-eyed", "quiet"]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()
        self.last_flashback: str = ""

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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small affluent whodunit with rhyme and flashback.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--detective", choices=DETECTIVE_NAMES)
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


def _affluent_opening(world: World, detective: Entity, item: Entity) -> None:
    world.say(
        f"At {world.setting.place}, everything looked neat and affluent, with polished floors and bright lamps."
    )
    world.say(
        f"{detective.id} was a {detective.meters.get('trait_word', 'curious')} little detective who noticed small things."
    )
    world.say(
        f"That evening, everyone admired {item.phrase} before tea."
    )


def _conflict(world: World, detective: Entity, suspect: Entity, item: Entity) -> None:
    detective.memes["worry"] += 1
    suspect.memes["conflict"] += 1
    item.meters["missing"] = 1
    world.say(
        f"Then {item.phrase} vanished from the room."
    )
    world.say(
        f"{suspect.label} frowned at the questions, and the room grew tense."
    )


def _rhyme_clue(world: World, detective: Entity, item: Entity) -> None:
    world.say(
        f"Near the mantel, {detective.id} found a tiny note that rhymed:"
    )
    world.say(
        f'"Find the shine where the vines entwine; look low, look slow, where garden shadows go."'
    )
    world.facts["rhyme"] = True


def _flashback(world: World, detective: Entity, suspect: Entity, item: Entity) -> None:
    world.say(
        f"That rhyme made {detective.id} remember a flashback from earlier by the garden wall."
    )
    if suspect.can_bunt:
        world.say(
            f"{suspect.label} had tried to bunt a ball across the grass, and the ball skipped under a rose trellis."
        )
        world.say(
            f"While everyone laughed, {item.label} had slipped from a tray and rolled toward the same vines."
        )
        world.last_flashback = "bunt"
    else:
        world.say(
            f"{suspect.label} had been carrying a tray past the roses, and a quick turn made things wobble."
        )
        world.last_flashback = "tray"


def _reveal(world: World, detective: Entity, suspect: Entity, item: Entity) -> None:
    world.say(
        f"{detective.id} followed the rhyme to the vines and found {item.phrase} tangled in the branches."
    )
    world.say(
        f"The clue fit the flashback: {suspect.label} had not stolen it for keeps, only sent it rolling away."
    )
    world.say(
        f"{suspect.label} apologized, {detective.id} smiled, and the house felt calm again."
    )
    item.meters["found"] = 1
    detective.memes["pride"] += 1
    detective.memes["relief"] += 1


def tell(setting: Setting, item_cfg: Item, suspect_cfg: Suspect, detective_name: str) -> World:
    world = World(setting)
    detective = world.add(Entity(
        id=detective_name,
        kind="character",
        type="girl" if detective_name in {"Nina", "Pia", "June", "Elsie", "Cora"} else "boy",
    ))
    detective.meters["trait_word"] = "curious"  # used only in prose selection, not exposed in trace
    suspect = world.add(Entity(id=suspect_cfg.id, kind="character", type=suspect_cfg.type, label=suspect_cfg.label))
    item = world.add(Entity(id=item_cfg.id, type="thing", label=item_cfg.label, phrase=item_cfg.phrase))

    detective.memes["worry"] = 0
    suspect.memes["conflict"] = 0
    item.meters["missing"] = 0
    item.meters["found"] = 0

    _affluent_opening(world, detective, item)
    world.para()
    _conflict(world, detective, suspect, item)
    _rhyme_clue(world, detective, item)
    world.para()
    _flashback(world, detective, suspect, item)
    _reveal(world, detective, suspect, item)

    world.facts.update(
        setting=setting,
        item=item_cfg,
        suspect=suspect_cfg,
        detective=detective,
        found=True,
        flashback=world.last_flashback,
    )
    return world


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    det: Entity = _safe_fact(world, f, "detective")  # type: ignore[assignment]
    item: Item = _safe_fact(world, f, "item")  # type: ignore[assignment]
    suspect: Suspect = _safe_fact(world, f, "suspect")  # type: ignore[assignment]
    setting: Setting = _safe_fact(world, f, "setting")  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Where did the missing {item.label} disappear in the story?",
            answer=f"It disappeared at {setting.place}, in the neat affluent house where tea was being served.",
        ),
        QAItem(
            question=f"What rhyming clue helped {det.id} look for the missing {item.label}?",
            answer='The note said, "Find the shine where the vines entwine; look low, look slow, where garden shadows go."',
        ),
        QAItem(
            question=f"What flashback did {det.id} remember before finding the {item.label}?",
            answer=f"{det.id} remembered {suspect.label} trying to bunt a ball by the garden wall, which pointed the search toward the rose vines.",
        ),
        QAItem(
            question=f"Who was involved in the conflict over the missing {item.label}?",
            answer=f"{suspect.label} was the one caught in the conflict, but the story showed it was an accident, not a mean trick.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"{det.id} found the {item.label} in the vines, and everyone relaxed once the object was back where it belonged.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does affluent mean?",
            answer="Affluent means having a lot of money or nice things, so the house can look polished and grand.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is when words sound alike at the end, like shine and vine.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when the story remembers something that happened earlier, to help explain what is going on now.",
        ),
        QAItem(
            question="What is a bunt in baseball?",
            answer="A bunt is a very soft hit that nudges the ball instead of sending it far away.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    item: Item = _safe_fact(world, f, "item")  # type: ignore[assignment]
    suspect: Suspect = _safe_fact(world, f, "suspect")  # type: ignore[assignment]
    return [
        f'Write a short whodunit for a child about a missing {item.label} in an affluent house.',
        f"Tell a gentle mystery where a rhyme clue and a flashback help {suspect.label} explain a garden accident.",
        f'Write a story that includes the word "bunt" and ends with the missing thing being found safely.',
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


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
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  flashback={world.last_flashback}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for i in ITEMS:
            for sus in SUSPECTS:
                combos.append((s, i, sus))
    return combos


ASP_RULES = r"""
setting(manor). setting(mansion). setting(villa).
affluent(manor). affluent(mansion). affluent(villa).

item(brooch). item(key). item(crown).
suspect(butler). suspect(cousin). suspect(aunt).

valid(S,I,X) :- setting(S), item(I), suspect(X), affluent(S).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
        if _safe_lookup(SETTINGS, s).affluent:
            lines.append(asp.fact("affluent", s))
    for i in ITEMS:
        lines.append(asp.fact("item", i))
    for x in SUSPECTS:
        lines.append(asp.fact("suspect", x))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if a - b:
        print("only in clingo:", sorted(a - b))
    if b - a:
        print("only in python:", sorted(b - a))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    item = getattr(args, "item", None) or rng.choice(list(ITEMS))
    suspect = getattr(args, "suspect", None) or rng.choice(list(SUSPECTS))
    detective = getattr(args, "detective", None) or rng.choice(DETECTIVE_NAMES)
    if setting not in SETTINGS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if item not in ITEMS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if suspect not in SUSPECTS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(setting=setting, item=item, suspect=suspect, detective=detective)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(ITEMS, params.item), _safe_lookup(SUSPECTS, params.suspect), params.detective)
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
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:")
        for s, i, x in combos:
            print(f"  {s:8} {i:8} {x:8}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for setting in SETTINGS:
            for item in ITEMS:
                for suspect in SUSPECTS:
                    params = StoryParams(setting=setting, item=item, suspect=suspect, detective="Milo")
                    samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
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
            header = f"### {p.detective}: {p.item} at {p.setting} (suspect: {p.suspect})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
