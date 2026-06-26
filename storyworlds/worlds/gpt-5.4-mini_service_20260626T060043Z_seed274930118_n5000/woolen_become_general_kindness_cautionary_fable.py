#!/usr/bin/env python3
"""
storyworlds/worlds/woolen_become_general_kindness_cautionary_fable.py
======================================================================

A small fable-world about a woolen gift, a cautious lesson, and a general who
learns that kindness can be stronger than pride.

The seed words for this world are:
- woolen
- become
- general

The story premise is fable-like: a proud general wants to keep a woolen cloak
for status, but a careful act of kindness changes what the cloak becomes in the
eyes of the village. The world model tracks both physical warmth and emotional
memes so the narration can show the turn from vanity to care.

This script follows the Storyworld contract:
- self-contained stdlib script under storyworlds/worlds/
- eager import of storyworlds/results.py
- lazy import of storyworlds/asp.py in ASP helpers
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- support for default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    item: object | None = None
    def __post_init__(self) -> None:
        for k in ("cold", "tattered", "dusty", "warmth", "distance"):
            self.meters.setdefault(k, 0.0)
        for k in ("pride", "kindness", "caution", "gratitude", "worry", "relief"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "queen"}
        male = {"boy", "man", "father", "general"}
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
class Setting:
    place: str = "the village square"
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
    plural: bool = False
    answer: object | None = None
    question: object | None = None
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
    item: str
    hero_name: str
    hero_role: str
    helper_name: str
    helper_role: str
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
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

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
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def _hero_role(role: str) -> str:
    return {"general": "general", "shepherd": "shepherd", "weaver": "weaver"}.get(role, role)


def _item_phrase(item: Item) -> str:
    return item.phrase


def _item_sits(item: Item) -> str:
    return "sit" if item.plural else "sits"


def _warmth_story(item: Item) -> str:
    return {
        "cloak": "It held the winter wind back like a quiet wall.",
        "blanket": "It could cover cold shoulders all at once.",
        "scarf": "It wrapped close and kept the throat warm.",
    }.get(item.id, "It was made to keep a body warm.")


def _general_title(name: str) -> str:
    return name


def _metered(world: World, eid: str, key: str) -> float:
    return world.get(eid).meters.get(key, 0.0)


def _memed(world: World, eid: str, key: str) -> float:
    return world.get(eid).memes.get(key, 0.0)


def set_worn(world: World, item: Entity, wearer: Entity) -> None:
    item.worn_by = wearer.id
    wearer.meters["warmth"] += 1.0


def spread_cold(world: World, wearer: Entity, item: Entity) -> None:
    wearer.meters["cold"] += 1.0
    item.meters["tattered"] += 1.0
    wearer.memes["worry"] += 1.0
    item.meters["dusty"] += 1.0


def teach_kindness(world: World, hero: Entity, helper: Entity, item: Entity) -> None:
    hero.memes["kindness"] += 1.0
    hero.memes["caution"] += 1.0
    helper.memes["gratitude"] += 1.0
    world.say(
        f"{helper.id} said, \"A good thing can become even better when it is shared.\""
    )
    world.say(
        f"{hero.id} listened. {hero.pronoun().capitalize()} chose to give the {item.label} where it was needed most."
    )


def caution_beats_pride(world: World, hero: Entity, helper: Entity, item: Entity) -> None:
    hero.memes["pride"] += 1.0
    world.say(
        f"{hero.id} was proud of {hero.pronoun('possessive')} bright {item.label}, and {hero.pronoun()} wanted everyone to notice."
    )
    world.say(
        f"But {helper.id} gave a careful warning: \"Cold weather can become sharp quickly. It is wiser to share warmth before anyone shivers.\""
    )


def resolve_turn(world: World, hero: Entity, helper: Entity, item: Entity) -> None:
    hero.memes["pride"] = max(0.0, hero.memes["pride"] - 1.0)
    hero.memes["kindness"] += 1.0
    hero.memes["relief"] += 1.0
    helper.memes["relief"] += 1.0
    world.say(
        f"{hero.id} nodded at last and draped the {item.label} over the smallest shivering child in the square."
    )
    world.say(
        f"At once, the child grew warmer, the wind seemed less cruel, and {hero.id}'s face became gentle."
    )
    world.say(
        f"That day, the {item.label} did not become less valuable. It became a sign that a strong heart can also be kind."
    )


def maybe_cold(world: World, hero: Entity, item: Entity) -> None:
    if hero.meters["cold"] >= THRESHOLD:
        world.say(
            f"The cold had reached {hero.id}'s hands and cheeks, and even {hero.pronoun('possessive')} fine {item.label} could not hide it."
        )


def tell(setting: Setting, item_cfg: Item, params: StoryParams) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_role,
    ))
    helper = world.add(Entity(
        id=params.helper_name,
        kind="character",
        type=params.helper_role,
    ))
    item = world.add(Entity(
        id=item_cfg.id,
        type=item_cfg.id,
        label=item_cfg.label,
        phrase=item_cfg.phrase,
        owner=hero.id,
        caretaker=helper.id,
    ))

    set_worn(world, item, hero)

    world.say(
        f"{hero.id} was {_general_title(hero.type)} {_hero_role(hero.type)} in {world.setting.place}, and everyone knew {hero.pronoun('possessive')} {item.label} was woolen and fine."
    )
    world.say(_warmth_story(item_cfg))
    world.say(
        f"Still, {hero.id} liked to stand very straight so the whole village could see the {item.label} and call {hero.id} important."
    )

    world.para()
    caution_beats_pride(world, hero, helper, item)
    spread_cold(world, hero, item)
    maybe_cold(world, hero, item)

    world.para()
    teach_kindness(world, hero, helper, item)
    resolve_turn(world, hero, helper, item)

    world.facts.update(
        hero=hero,
        helper=helper,
        item=item,
        item_cfg=item_cfg,
        setting=setting,
        cold=hero.meters["cold"] >= THRESHOLD,
        kind=hero.memes["kindness"] >= THRESHOLD,
        cautious=hero.memes["caution"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "village_square": Setting(place="the village square", affords={"share"}),
    "hill_road": Setting(place="the hill road", affords={"share"}),
    "fire_pit": Setting(place="the fire pit", affords={"share"}),
}

ITEMS = {
    "cloak": Item(
        id="cloak",
        label="cloak",
        phrase="a woolen cloak",
        region="torso",
    ),
    "blanket": Item(
        id="blanket",
        label="blanket",
        phrase="a woolen blanket",
        region="torso",
        plural=False,
    ),
    "scarf": Item(
        id="scarf",
        label="scarf",
        phrase="a woolen scarf",
        region="neck",
    ),
}

HERO_NAMES = ["Rowan", "Mira", "Toby", "Clara", "Mina", "Elias"]
HELPER_NAMES = ["Nell", "Bram", "Iris", "Oren", "Pia", "Hugo"]


KNOWLEDGE = {
    "woolen": [
        (
            "What is woolen cloth?",
            "Woolen cloth is cloth made from wool. It feels warm and is often used for cloaks, scarves, and blankets.",
        )
    ],
    "kindness": [
        (
            "What does kindness mean?",
            "Kindness means choosing to help, share, or comfort someone in a gentle and caring way.",
        )
    ],
    "cautionary": [
        (
            "What does cautionary mean?",
            "Cautionary means giving a warning so someone can avoid a mistake or a danger.",
        )
    ],
    "general": [
        (
            "Who is a general?",
            "A general is a leader in an army. A general gives orders and helps guide soldiers.",
        )
    ],
    "become": [
        (
            "What does become mean?",
            "Become means to change into something new, or to start being in a new way.",
        )
    ],
}

KNOWLEDGE_ORDER = ["woolen", "kindness", "cautionary", "general", "become"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for item_id in setting.affords:
            combos.append((place, item_id))
    return combos


@dataclass
class StoryParams:
    place: str
    item: str
    hero_name: str
    hero_role: str
    helper_name: str
    helper_role: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    item = _safe_fact(world, f, "item_cfg")
    return [
        f'Write a short fable about a woolen {item.label} that can become a lesson in kindness.',
        f"Tell a cautionary story where {hero.id}, a {hero.type}, learns from {helper.id} and shares a woolen {item.label}.",
        f'Write a child-friendly fable that includes a general, a woolen item, and the word "become".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    item = _safe_fact(world, f, "item_cfg")
    return [
        QAItem(
            question=f"Who was the story about in the village square?",
            answer=f"It was about {hero.id}, a {_hero_role(hero.type)}, and {helper.id}, who helped {hero.id} learn a kinder way to act.",
        ),
        QAItem(
            question=f"What woolen thing was important in the story?",
            answer=f"The important thing was {item.phrase}. It was warm, proud-looking, and later became a sign of kindness.",
        ),
        QAItem(
            question=f"What warning did {helper.id} give?",
            answer=f"{helper.id} warned that cold weather can become sharp quickly and that it is wiser to share warmth before anyone shivers.",
        ),
        QAItem(
            question=f"How did {hero.id} change by the end?",
            answer=f"{hero.id} became less proud, more cautious, and much kinder after listening and sharing the {item.label}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for tag in globals().get("KNOWLEDGE_ORDER", sorted(globals().get("KNOWLEDGE", []))):
        if tag in KNOWLEDGE:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: round(v, 3) for k, v in e.meters.items() if v}
        memes = {k: round(v, 3) for k, v in e.memes.items() if v}
        parts = [f"type={e.type}"]
        if e.label:
            parts.append(f"label={e.label}")
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {e.id}: {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="village_square",
        item="cloak",
        hero_name="General Rowan",
        hero_role="general",
        helper_name="Nell",
        helper_role="weaver",
    ),
    StoryParams(
        place="hill_road",
        item="scarf",
        hero_name="General Mira",
        hero_role="general",
        helper_name="Bram",
        helper_role="shepherd",
    ),
    StoryParams(
        place="fire_pit",
        item="blanket",
        hero_name="General Elias",
        hero_role="general",
        helper_name="Iris",
        helper_role="weaver",
    ),
]


def explain_rejection(place: str, item: str) -> str:
    return f"(No story: the setting {place} does not support the woolen {item} fable.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, a))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("woolen_item", iid))
        lines.append(asp.fact("label", iid, item.label))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, I) :- place(P), item(I), affords(P, share), woolen_item(I).
#show valid/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in clingo:", sorted(clingo_set - python_set))
    print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fable world about a woolen gift, caution, and kindness.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "item", None) is None or c[1] == getattr(args, "item", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, item = rng.choice(list(combos))
    return StoryParams(
        place=place,
        item=item,
        hero_name=getattr(args, "name", None) or rng.choice(HERO_NAMES),
        hero_role="general",
        helper_name=getattr(args, "helper", None) or rng.choice(HELPER_NAMES),
        helper_role=rng.choice(["weaver", "shepherd"]),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ITEMS, params.item), params)
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
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, item) combos:\n")
        for place, item in combos:
            print(f"  {place:14} {item}")
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
            header = f"### {p.hero_name}: {p.item} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
