#!/usr/bin/env python3
"""
A standalone storyworld for a tiny pirate tale with a magic coverlet and a
lesson learned.

Seed tale:
---
A small pirate child finds a strange coverlet on the ship. The coverlet seems
to glow and whisper when the wind gets cold. The child wants to use the magic
coverlet to keep treasure warm, but the captain warns that magic should not be
used carelessly. After a bit of trouble, the child learns to share the coverlet
and use it to help the whole crew through the night.

World model:
- physical meters: cold, damp, glow, treasure_safeness, magic_used
- emotional memes: curiosity, worry, pride, teamwork, lesson

The story is narrated from the evolving state: discovery, tension, turn,
resolution, and an ending image that proves what changed.
"""

from __future__ import annotations

import argparse
import copy
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
    carried_by: Optional[str] = None
    plural: bool = False
    magical: bool = False
    uses: int = 0
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    captain: object | None = None
    gift: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "captain"}
        male = {"boy", "father", "dad", "man", "pirate", "captain"}
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man", "pirate"}:
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


@dataclass
class Setting:
    place: str
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
class Gift:
    id: str
    label: str
    phrase: str
    region: str
    enchantment: str
    helps: set[str]
    lesson: str
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
    gift: str
    hero_name: str
    hero_type: str
    captain_name: str
    captain_type: str
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
        self.fired: set[tuple] = set()
        self.lines: list[str] = []
        self.paras: list[list[str]] = [[]]
        self.facts: dict = {}
        self.weather: str = "cold"

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paras[-1].append(text)

    def para(self) -> None:
        if self.paras[-1]:
            self.paras.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paras if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paras = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.weather = self.weather
        return clone


SETTINGS = {
    "ship": Setting(place="the ship", affords={"discover", "warm", "share"}),
    "cabin": Setting(place="the captain's cabin", affords={"discover", "warm", "share"}),
    "island": Setting(place="the small island camp", affords={"discover", "warm", "share"}),
}

GIFTS = {
    "coverlet": Gift(
        id="coverlet",
        label="coverlet",
        phrase="a soft coverlet stitched with silver stars",
        region="body",
        enchantment="glow",
        helps={"cold", "damp"},
        lesson="magic works best when it is shared",
    ),
    "lanterncloth": Gift(
        id="lanterncloth",
        label="lantern cloth",
        phrase="a bright lantern cloth folded in a neat square",
        region="hands",
        enchantment="shine",
        helps={"dark"},
        lesson="bright things should be used carefully",
    ),
}

GIRL_NAMES = ["Mara", "Nina", "Tia", "Lila", "Sora", "Ivy"]
BOY_NAMES = ["Finn", "Jory", "Pip", "Rex", "Toby", "Ned"]
CAPTAIN_NAMES = ["Captain Bay", "Captain Reed", "Captain Flint", "Captain Sable"]


def build_reasonable_story(place: str, gift_id: str) -> bool:
    return place in SETTINGS and gift_id in GIFTS


def valid_combos() -> list[tuple[str, str]]:
    return [(p, g) for p in SETTINGS for g in GIFTS if build_reasonable_story(p, g)]


def select_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def story_prefix(hero: Entity, captain: Entity) -> str:
    return f"{hero.id} was a little {hero.type} pirate who sailed with {captain.id}."


def setup(world: World, hero: Entity, captain: Entity, gift: Entity) -> None:
    world.say(story_prefix(hero, captain))
    world.say(
        f"One windy night, {hero.id} found {gift.phrase} tucked beside a chest."
    )
    world.say(
        f"When {hero.id} touched {gift.label}, it gave off a faint {_safe_lookup(GIFTS, gift.id).enchantment}."
    )


def anticipate(world: World, hero: Entity, captain: Entity, gift: Entity) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    hero.memes["pride"] = hero.memes.get("pride", 0) + 1
    world.say(
        f"{hero.id} loved the sparkly feeling and wanted to keep the {gift.label} all to "
        f"{hero.pronoun('possessive')}self."
    )
    world.say(
        f"The ship creaked as the cold wind slipped through the boards, and the night felt too chilly for sleep."
    )


def warn(world: World, captain: Entity, hero: Entity, gift: Entity) -> None:
    captain.memes["worry"] = captain.memes.get("worry", 0) + 1
    world.say(
        f'"Magic is not for showing off," {captain.id} said. '
        f'"If you use that {gift.label} carelessly, someone could get left out in the cold."'
    )


def try_magic(world: World, hero: Entity, gift: Entity) -> None:
    if world.setting.place not in SETTINGS:
        pass
    hero.meters["magic_used"] = hero.meters.get("magic_used", 0) + 1
    gift.uses += 1
    hero.memes["pride"] = hero.memes.get("pride", 0) + 1
    world.say(
        f"But {hero.id} still tried the magic anyway. {gift.label.capitalize()} glimmered bright and warm."
    )
    world.say(
        f"The glow was lovely at first, but it only wrapped around the treasure chest and not the whole crew."
    )


def consequence(world: World, hero: Entity, captain: Entity, gift: Entity) -> None:
    hero.meters["cold"] = hero.meters.get("cold", 0) + 1
    captain.meters["cold"] = captain.meters.get("cold", 0) + 1
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    world.say(
        f"The deck stayed chilly for everyone else, and {hero.id} saw that the warm glow had not helped the lonely sailors nearby."
    )
    world.say(
        f"{hero.id}'s smile faded. The magic felt less like a prize and more like a problem."
    )


def lesson_turn(world: World, captain: Entity, hero: Entity, gift: Entity) -> None:
    hero.memes["lesson"] = hero.memes.get("lesson", 0) + 1
    captain.memes["teamwork"] = captain.memes.get("teamwork", 0) + 1
    world.say(
        f"Then {hero.id} handed the {gift.label} to {captain.id} and asked how to use it the right way."
    )
    world.say(
        f"{captain.id} smiled and showed {hero.id} how to spread the {gift.label}'s warmth over the whole sleeping space, not just one chest."
    )


def resolution(world: World, hero: Entity, captain: Entity, gift: Entity) -> None:
    hero.meters["cold"] = 0
    captain.meters["cold"] = 0
    hero.meters["treasure_safeness"] = hero.meters.get("treasure_safeness", 0) + 1
    captain.meters["treasure_safeness"] = captain.meters.get("treasure_safeness", 0) + 1
    hero.memes["teamwork"] = hero.memes.get("teamwork", 0) + 1
    hero.memes["lesson"] = hero.memes.get("lesson", 0) + 1
    world.say(
        f"At last, the whole crew tucked under the glowing coverlet, and the ship felt cozy from bow to stern."
    )
    world.say(
        f"{hero.id} learned that magic shines best when it helps everyone, and the {gift.label} became a bedtime thing for the whole crew."
    )


def tell(setting: Setting, gift_cfg: Gift, hero_name: str, hero_type: str, captain_name: str, captain_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    captain = world.add(Entity(id=captain_name, kind="character", type=captain_type))
    gift = world.add(Entity(id=gift_cfg.id, type="thing", label=gift_cfg.label, phrase=gift_cfg.phrase, magical=True))

    setup(world, hero, captain, gift)
    world.para()
    anticipate(world, hero, captain, gift)
    warn(world, captain, hero, gift)
    try_magic(world, hero, gift)
    consequence(world, hero, captain, gift)
    world.para()
    lesson_turn(world, captain, hero, gift)
    resolution(world, hero, captain, gift)

    world.facts.update(hero=hero, captain=captain, gift=gift, gift_cfg=gift_cfg)
    return world


KNOWLEDGE = {
    "coverlet": [
        ("What is a coverlet?", "A coverlet is a light blanket that covers a bed and helps keep someone warm."),
    ],
    "magic": [
        ("What is magic in a story?", "Magic in a story is something strange and special that can do things real things usually cannot."),
    ],
    "lesson": [
        ("What does it mean to learn a lesson?", "Learning a lesson means understanding a better way to act after something happens."),
    ],
    "pirate": [
        ("What is a pirate?", "A pirate is a seafaring person in stories who sails ships and looks for treasure."),
    ],
    "ship": [
        ("What is a ship?", "A ship is a big boat that sails on the sea and carries people and cargo."),
    ],
    "cold": [
        ("How can a blanket help when it is cold?", "A blanket can trap warmth close to your body, which helps you feel less cold."),
    ],
}

KNOWLEDGE_ORDER = ["pirate", "ship", "coverlet", "magic", "cold", "lesson"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short pirate tale for a child that includes the word "{f["gift"].label}".',
        f"Tell a gentle story where {f['hero'].id} finds a magic {f['gift_cfg'].label} on {world.setting.place} and learns a lesson.",
        f"Write a small story about a pirate child, a glowing coverlet, and a captain who teaches a kinder way to use magic.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    captain: Entity = _safe_fact(world, f, "captain")
    gift_cfg: Gift = _safe_fact(world, f, "gift_cfg")
    gift: Entity = _safe_fact(world, f, "gift")
    return [
        QAItem(
            question=f"Who found the {gift_cfg.label} in the story?",
            answer=f"{hero.id} found the {gift.label} tucked beside a chest on {world.setting.place}.",
        ),
        QAItem(
            question=f"Why did {captain.id} warn {hero.id} about the magic {gift_cfg.label}?",
            answer=f"{captain.id} warned {hero.id} because magic should not be used carelessly, and the warmth was needed by the whole crew, not just one treasure chest.",
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn by the end?",
            answer=f"{hero.id} learned that magic shines best when it helps everyone, so the {gift.label} became a shared comfort for the crew.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    tags = {world.facts["gift_cfg"].id, "magic", "lesson", "pirate", "ship"}
    for tag in globals().get("KNOWLEDGE_ORDER", sorted(globals().get("KNOWLEDGE", []))):
        if tag in tags:
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.magical:
            bits.append("magical=True")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A combination is reasonable if the place and gift both exist.
reasonable(P, G) :- place(P), gift(G).

#show reasonable/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for g in GIFTS:
        lines.append(asp.fact("gift", g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_reasonable_combos() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show reasonable/2."))
    return sorted(set(asp.atoms(model, "reasonable")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_reasonable_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in asp:", sorted(cl - py))
    return 1


CURATED = [
    StoryParams(place="ship", gift="coverlet", hero_name="Mara", hero_type="girl", captain_name="Captain Bay", captain_type="captain"),
    StoryParams(place="cabin", gift="coverlet", hero_name="Pip", hero_type="boy", captain_name="Captain Reed", captain_type="captain"),
    StoryParams(place="island", gift="coverlet", hero_name="Tia", hero_type="girl", captain_name="Captain Flint", captain_type="captain"),
    StoryParams(place="ship", gift="lanterncloth", hero_name="Ned", hero_type="boy", captain_name="Captain Sable", captain_type="captain"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny pirate tale about a magic coverlet and a lesson learned.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--captain")
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
    if getattr(args, "gift", None) and getattr(args, "gift", None) not in GIFTS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "place", None) and getattr(args, "place", None) not in SETTINGS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = valid_combos()
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "gift", None):
        combos = [c for c in combos if c[1] == getattr(args, "gift", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, gift_id = rng.choice(combos)
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or select_name(rng, gender)
    captain = getattr(args, "captain", None) or rng.choice(CAPTAIN_NAMES)
    return StoryParams(
        place=place,
        gift=gift_id,
        hero_name=name,
        hero_type=gender,
        captain_name=captain,
        captain_type="captain",
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(GIFTS, params.gift), params.hero_name, params.hero_type, params.captain_name, params.captain_type)
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
        print(asp_program("#show reasonable/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_reasonable_combos()
        print(f"{len(combos)} reasonable combos:")
        for p, g in combos:
            print(f"  {p:8} {g}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
