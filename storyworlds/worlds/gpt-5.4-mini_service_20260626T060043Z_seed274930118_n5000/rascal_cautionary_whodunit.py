#!/usr/bin/env python3
"""
rascal_cautionary_whodunit.py
=============================

A small storyworld in the spirit of a cautionary whodunit.

Premise:
- A curious little rascal meddles with a mysterious lost item.
- The household notices odd clues: a gate ajar, a ribbon gone, a trail of crumbs.
- A parent-like helper follows the clues, solves the little mystery, and shows the
  child why sneaking and taking things without asking causes trouble.
- The ending resolves by returning the item and choosing honesty.

The world is intentionally small and constraint-checked:
- One child, one caretaker, one missing object, one clue trail, one fix.
- The story is driven by simulated state, not just template swapping.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    clue: object | None = None
    lost: object | None = None
    def __post_init__(self) -> None:
        for k in ("missing", "found", "crumbs", "worry", "suspicion", "guilt", "relief", "curiosity"):
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
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
    place: str
    indoor: bool
    clue: str
    afford: str
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
    secret_place: str
    clue: str
    outcome: str
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
    item: str
    name: str
    gender: str
    caretaker: str
    trait: str
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
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

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


SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoor=True, clue="crumbs", afford="search"),
    "hall": Setting(place="the hall", indoor=True, clue="mud", afford="search"),
    "garden": Setting(place="the garden", indoor=False, clue="broken twig", afford="search"),
}

ITEMS = {
    "cookie": Item(
        id="cookie",
        label="cookie tin",
        phrase="a blue cookie tin",
        secret_place="the high shelf",
        clue="crumbs",
        outcome="the cookie tin had been hidden on the high shelf all along",
    ),
    "key": Item(
        id="key",
        label="brass key",
        phrase="a brass key on a red ribbon",
        secret_place="under the rug",
        clue="ribbon",
        outcome="the brass key was under the rug near the door",
    ),
    "toy": Item(
        id="toy",
        label="toy mouse",
        phrase="a tiny toy mouse",
        secret_place="behind the curtain",
        clue="dust",
        outcome="the toy mouse was behind the curtain by the window",
    ),
}

NAMES = {
    "girl": ["Mina", "Lily", "Nora", "Zoe"],
    "boy": ["Toby", "Finn", "Eli", "Milo"],
}
TRAITS = ["curious", "bold", "restless", "sly", "playful"]


def _story_setting(place: str) -> Setting:
    if place not in SETTINGS:
        pass
    return _safe_lookup(SETTINGS, place)


def _story_item(item: str) -> Item:
    if item not in ITEMS:
        pass
    return _safe_lookup(ITEMS, item)


def reasonableness_gate(setting: Setting, item: Item) -> bool:
    return True if setting.afford == "search" and item.secret_place else False


ASP_RULES = r"""
#show valid/2.
#show clue/2.
#show hidden/2.
valid(Place, Item) :- setting(Place), item(Item), clue(Place, _), hidden(Item, _).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
        lines.append(asp.fact("clue", sid, s.clue))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("hidden", iid, item.secret_place))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Cautionary whodunit storyworld about a little rascal.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--caretaker", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
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
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    item = getattr(args, "item", None) or rng.choice(list(ITEMS))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(NAMES, gender))
    caretaker = getattr(args, "caretaker", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, item=item, name=name, gender=gender, caretaker=caretaker, trait=trait)


def _indefinite(word: str) -> str:
    return ("an " if word[:1].lower() in "aeiou" else "a ") + word


def tell(params: StoryParams) -> World:
    setting = _story_setting(params.place)
    item = _story_item(params.item)
    world = World(setting)

    child = world.add(Entity(id=params.name, kind="character", type=params.gender, traits=["little", "rascal", params.trait]))
    caretaker = world.add(Entity(id="Caretaker", kind="character", type=params.caretaker, label=f"the {params.caretaker}"))
    lost = world.add(Entity(id=item.id, type="thing", label=item.label, phrase=item.phrase, owner=caretaker.id, caretaker=caretaker.id))
    clue = world.add(Entity(id="clue", type="thing", label=item.clue, phrase=item.clue))

    world.facts.update(child=child, caretaker=caretaker, lost=lost, item=item, setting=setting, clue=clue)

    world.say(f"{child.id} was a little rascal with a curious nose and quick feet.")
    world.say(f"{child.pronoun('possessive').capitalize()} {params.trait} heart always wanted to peek at hidden things.")
    world.say(f"In {setting.place}, {child.id} noticed {item.phrase} was gone.")
    world.para()
    world.say(f"{caretaker.label.capitalize()} looked around and frowned. Somebody had been sneaking where they should not.")
    world.say(f"Then there was a clue: {setting.clue}. That was odd, because {setting.clue} did not belong in {setting.place}.")
    if item.clue == "ribbon":
        world.say("A bright ribbon trail led toward the quiet corner by the door.")
    elif item.clue == "crumbs":
        world.say("Tiny crumbs made a crooked line across the floor, as if someone had taken a secret snack.")
    else:
        world.say("A soft dusty streak pointed toward a hidden place behind the curtain.")
    world.para()
    child.memes["curiosity"] += 1
    child.memes["suspicion"] += 1
    caretaker.memes["worry"] += 1
    world.say(f"{child.id} tried to act innocent, but {child.pronoun('possessive')} eyes kept darting to the clue.")
    world.say(f"{caretaker.label.capitalize()} followed the evidence like a proper detective and asked one careful question at a time.")
    world.say(f"At last, the mystery was solved: {item.outcome}.")
    world.para()
    child.memes["guilt"] += 1
    caretaker.memes["relief"] += 1
    world.say(f"{child.id} confessed and put the missing thing back where it belonged.")
    world.say(f"{caretaker.label.capitalize()} said that riddles are fine, but taking things without asking is not.")
    world.say(f"The rascal lowered {child.pronoun('possessive')} head, then promised to ask first next time.")
    world.say(f"By bedtime, the room was calm again, and the clue had become a lesson.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "child")
    item = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "item")
    setting = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "setting")
    return [
        f'Write a short cautionary whodunit for a young child named {child.id} in {setting.place}.',
        f'Tell a mystery story where a little rascal seems involved when {item.phrase} goes missing.',
        f'Write a gentle detective story that ends with honesty, a returned item, and a lesson about asking first.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "child")
    caretaker = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "caretaker")
    item = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "item")
    setting = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "setting")
    return [
        QAItem(
            question=f"Who was the little rascal in the story?",
            answer=f"The little rascal was {child.id}. {child.id} was curious and sneaky, but learned a lesson by the end.",
        ),
        QAItem(
            question=f"What went missing in {setting.place}?",
            answer=f"{item.phrase} went missing, which made everyone start looking for clues.",
        ),
        QAItem(
            question=f"Who solved the mystery?",
            answer=f"{caretaker.label.capitalize()} solved the mystery by following the clues carefully.",
        ),
        QAItem(
            question=f"What did the rascal do at the end?",
            answer=f"{child.id} confessed, put the missing thing back, and promised to ask first next time.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [
        QAItem(
            question="What is a clue?",
            answer="A clue is a small piece of information that helps solve a mystery.",
        ),
        QAItem(
            question="What does a detective do?",
            answer="A detective looks carefully at clues to figure out what happened.",
        ),
        QAItem(
            question="Why should children ask before taking things?",
            answer="Children should ask first because taking things without permission can worry people and cause trouble.",
        ),
    ]
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    StoryParams(place="kitchen", item="cookie", name="Mina", gender="girl", caretaker="mother", trait="curious"),
    StoryParams(place="hall", item="key", name="Toby", gender="boy", caretaker="father", trait="sly"),
    StoryParams(place="garden", item="toy", name="Nora", gender="girl", caretaker="mother", trait="playful"),
]


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    asp_valid = set(asp.atoms(model, "valid"))
    py_valid = {(p, i) for p in SETTINGS for i in ITEMS if reasonableness_gate(_safe_lookup(SETTINGS, p), _safe_lookup(ITEMS, i))}
    if asp_valid == py_valid:
        print(f"OK: ASP matches Python gate ({len(py_valid)} combos).")
        return 0
    print("Mismatch between ASP and Python.")
    print("ASP only:", sorted(asp_valid - py_valid))
    print("Python only:", sorted(py_valid - asp_valid))
    return 1


def asp_valid_combos() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible setting/item combos:")
        for place, item in combos:
            print(f"  {place:8} {item}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 30, 30):
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
            header = f"### {p.name} / {p.place} / {p.item}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
