#!/usr/bin/env python3
"""
A small nursery-rhyme storyworld about comparison, crying, magic, and dialogue.

A little child sees a brighter thing, compares it to their own, and feels a tearful
sting. Then a kindly helper speaks a magical promise, and the child ends with a
new way to see the same old thing.
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

    child: object | None = None
    helper: object | None = None
    prize: object | None = None
    spell: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"brightness": 0.0, "tears": 0.0, "magic": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "hurt": 0.0, "wonder": 0.0, "envy": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
class Setting:
    place: str
    light: str
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
    type: str
    sparkle: float
    compare_word: str
    remedy: str
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})
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
class Magic:
    id: str
    label: str
    spell: str
    result: str
    patience: str
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

    def copy(self) -> "World":
        import copy as _copy
        c = World(self.setting)
        c.entities = _copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


@dataclass
class StoryParams:
    setting: str
    item: str
    magic: str
    name: str
    gender: str
    helper: str
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


SETTINGS = {
    "nursery": Setting(place="the nursery nook", light="soft", affords={"compare", "cry", "magic"}),
    "garden": Setting(place="the moonlit garden", light="silver", affords={"compare", "cry", "magic"}),
    "attic": Setting(place="the little attic", light="dim", affords={"compare", "cry", "magic"}),
}

ITEMS = {
    "lamp": Item(
        id="lamp",
        label="lamp",
        phrase="a plain little lamp",
        type="lamp",
        sparkle=0.0,
        compare_word="brighter",
        remedy="glow",
        genders={"girl", "boy"},
    ),
    "crown": Item(
        id="crown",
        label="crown",
        phrase="a tiny paper crown",
        type="crown",
        sparkle=0.1,
        compare_word="shinier",
        remedy="shine",
        genders={"girl", "boy"},
    ),
    "kite": Item(
        id="kite",
        label="kite",
        phrase="a small cloth kite",
        type="kite",
        sparkle=0.0,
        compare_word="higher",
        remedy="sail",
        genders={"girl", "boy"},
    ),
}

MAGICS = {
    "glimmer": Magic(
        id="glimmer",
        label="glimmer magic",
        spell="glimmer",
        result="a soft gold glow",
        patience="the glow could grow with a gentle word",
    ),
    "mirror": Magic(
        id="mirror",
        label="mirror magic",
        spell="mirror",
        result="a kind bright reflection",
        patience="the mirror only worked when spoken to kindly",
    ),
    "stitch": Magic(
        id="stitch",
        label="stitch magic",
        spell="stitch",
        result="a sparkling patch",
        patience="the patch needed calm hands and careful talk",
    ),
}

HELPERS = {
    "fairy": "fairy",
    "grandma": "grandma",
    "rabbit": "rabbit",
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Zoe", "Ava", "Ivy"]
BOY_NAMES = ["Leo", "Finn", "Noah", "Eli", "Theo", "Max"]


class MiniWorld:
    def __init__(self) -> None:
        self.fired: set[str] = set()


def _do_compare(world: World, child: Entity, item: Entity, narrate: bool = True) -> None:
    child.memes["envy"] += 1
    child.memes["hurt"] += 1
    child.meters["tears"] += 0.5
    item.meters["brightness"] += 0.2
    if narrate:
        world.say(
            f"{child.id} looked at {item.phrase} and made a comparison, "
            f"but {child.pronoun('possessive')} own little thing felt far from grand."
        )


def _do_cry(world: World, child: Entity, narrate: bool = True) -> None:
    child.meters["tears"] += 1.0
    child.memes["hurt"] += 1.0
    if narrate:
        world.say(
            f"Then {child.id} did cry, with teardrops bright as pearls."
        )


def _do_magic(world: World, child: Entity, helper: Entity, magic: Entity, item: Entity, narrate: bool = True) -> None:
    child.meters["magic"] += 1.0
    child.memes["wonder"] += 1.0
    child.memes["envy"] = 0.0
    child.memes["hurt"] = max(0.0, child.memes["hurt"] - 1.0)
    item.meters["brightness"] += 1.0
    if narrate:
        world.say(
            f'{helper.id} said, "Let us try {magic.label}." '
            f'{helper.id} whispered, "{magic.spell}, {magic.spell}," and {magic.result} bloomed.'
        )
        world.say(
            f'{child.id} heard the little spell and smiled, because {magic.patience}.'
        )


def tell_world(setting: Setting, item: Item, magic: Magic, name: str, gender: str, helper_kind: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=name, kind="character", type=gender, meters={"brightness": 0.0, "tears": 0.0, "magic": 0.0}, memes={"joy": 0.0, "hurt": 0.0, "wonder": 0.0, "envy": 0.0}))
    helper = world.add(Entity(id=helper_kind.capitalize(), kind="character", type=helper_kind, label=helper_kind))
    prize = world.add(Entity(id=item.id, type=item.type, label=item.label, phrase=item.phrase, owner=child.id))
    spell = world.add(Entity(id=magic.id, type="magic", label=magic.label))
    world.facts.update(child=child, helper=helper, item=prize, magic=spell, item_cfg=item, magic_cfg=magic)
    world.say(f"In {setting.place}, under a {setting.light} little light, there lived {name}.")
    world.say(f"{name} loved {item.phrase}, but {name} could not help a comparison when a {item.compare_word} thing gleamed nearby.")
    world.para()
    _do_compare(world, child, prize)
    _do_cry(world, child)
    world.para()
    world.say(f"{helper.id} came close and spoke in a soft voice.")
    _do_magic(world, child, helper, spell, prize)
    world.para()
    child.memes["joy"] += 1.0
    world.say(
        f"By the end, {name} kept {prize.phrase} close. It was not the {item.compare_word} thing in the room, "
        f"but it was theirs, and it shone in a small, brave way."
    )
    return world


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sname, setting in SETTINGS.items():
        for iname, item in ITEMS.items():
            if "compare" not in setting.affords:
                continue
            for mname in MAGICS:
                for helper in HELPERS:
                    combos.append((sname, iname, mname, helper))
    return combos


def explain_rejection() -> str:
    return "(No story: this world needs a setting, an item to compare, a magic trick, and a helper to speak the dialogue.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld about comparison, crying, magic, and dialogue.")
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--item", choices=sorted(ITEMS))
    ap.add_argument("--magic", choices=sorted(MAGICS))
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    if getattr(args, "setting", None):
        combos = [c for c in combos if c[0] == getattr(args, "setting", None)]
    if getattr(args, "item", None):
        combos = [c for c in combos if c[1] == getattr(args, "item", None)]
    if getattr(args, "magic", None):
        combos = [c for c in combos if c[2] == getattr(args, "magic", None)]
    if getattr(args, "helper", None):
        combos = [c for c in combos if c[3] == getattr(args, "helper", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, item, magic, helper = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    if gender not in _safe_lookup(ITEMS, item).genders:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(setting=setting, item=item, magic=magic, name=name, gender=gender, helper=helper)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short nursery-rhyme story about {f["child"].id} making a comparison and then crying.',
        f"Tell a gentle tale where {f['child'].id} sees {f['item_cfg'].phrase} and {f['helper'].id} answers with magic dialogue.",
        f'Write a child-friendly rhyme that includes the words "comparison" and "cry" and ends in a soft magical turn.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, helper, item, item_cfg, magic_cfg = f["child"], f["helper"], f["item"], f["item_cfg"], f["magic_cfg"]
    return [
        QAItem(
            question=f"What did {child.id} do before the tears came?",
            answer=f"{child.id} made a comparison after noticing {item_cfg.phrase}.",
        ),
        QAItem(
            question=f"Why did {child.id} cry?",
            answer=f"{child.id} cried because {child.pronoun('possessive')} own thing felt small beside something {item_cfg.compare_word}.",
        ),
        QAItem(
            question=f"Who helped, and what did they say?",
            answer=f"{helper.id} helped by speaking softly and using {magic_cfg.label}; the words were kind and magical.",
        ),
        QAItem(
            question=f"What changed at the end?",
            answer=f"{child.id} stopped feeling stuck in the comparison and ended with joy, wonder, and {item_cfg.phrase} still close by.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a comparison?",
            answer="A comparison is when you look at two things and think about how they are the same or different.",
        ),
        QAItem(
            question="What does cry mean?",
            answer="To cry means to let tears come out when you feel sad, hurt, or overwhelmed.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic is a special pretend power that can make surprising changes happen in a story.",
        ),
        QAItem(
            question="What is dialogue?",
            answer="Dialogue is the part of a story where the characters speak to one another.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


ASP_RULES = r"""
chosen_setting(S) :- setting(S).
chosen_item(I) :- item(I).
chosen_magic(M) :- magic(M).
chosen_helper(H) :- helper(H).

valid_story(S,I,M,H) :- chosen_setting(S), chosen_item(I), chosen_magic(M), chosen_helper(H).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for i in ITEMS:
        lines.append(asp.fact("item", i))
    for m in MAGICS:
        lines.append(asp.fact("magic", m))
    for h in HELPERS:
        lines.append(asp.fact("helper", h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    ax = set(asp_valid_combos())
    if py != ax:
        print("MISMATCH between ASP and Python.")
        if py - ax:
            print("only python:", sorted(py - ax))
        if ax - py:
            print("only asp:", sorted(ax - py))
        return 1
    sample = generate(resolve_params(argparse.Namespace(setting=None, item=None, magic=None, helper=None, name=None, gender=None), random.Random(7)))
    if not sample.story.strip():
        print("Generated empty story.")
        return 1
    print(f"OK: ASP matches Python on {len(py)} combos, and generation works.")
    return 0


def generate(params: StoryParams) -> StorySample:
    world = tell_world(_safe_lookup(SETTINGS, params.setting), _safe_lookup(ITEMS, params.item), _safe_lookup(MAGICS, params.magic), params.name, params.gender, params.helper)
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
    StoryParams(setting="nursery", item="lamp", magic="glimmer", name="Mia", gender="girl", helper="fairy"),
    StoryParams(setting="garden", item="crown", magic="mirror", name="Leo", gender="boy", helper="grandma"),
    StoryParams(setting="attic", item="kite", magic="stitch", name="Nora", gender="girl", helper="rabbit"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        models = asp_valid_combos()
        print(f"{len(models)} compatible stories")
        for row in models:
            print(row)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError:
                continue
            params.seed = base_seed + i
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

    for idx, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.setting}, {p.item}, {p.magic}, {p.helper}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
