#!/usr/bin/env python3
"""
storyworlds/worlds/aardvark_settle_karma_sharing_fairy_tale.py
==============================================================

A small fairy-tale story world about an aardvark, a sharing lesson, and a
gentle settling of karma.

Premise:
- A childlike aardvark wants something shiny or sweet.
- A village or forest sharing rule makes taking without asking feel unkind.
- An unfair act brings immediate trouble, while a kind act later settles the
  balance.

The world simulates:
- physical meters: carrying, holding, full, empty, tired, clean
- emotional memes: want, joy, worry, guilt, gratitude, harmony, karma

The story should feel like a complete fairy tale: opening, tension, turn,
resolution, and an ending image proving what changed.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    held_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    gift: object | None = None
    hero: object | None = None
    treasure: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            if self.type in {"aardvark"}:
                return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)
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
    kind: str = "forest"
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
class Treasure:
    label: str
    phrase: str
    type: str
    taste: str
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
class Gift:
    label: str
    phrase: str
    kind: str
    helps: set[str]
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


def _do_action(world: World, actor: Entity, action: str, target: Optional[Entity] = None, narrate: bool = True) -> None:
    if action == "take":
        actor.meters["carrying"] = actor.meter("carrying") + 1
        if target is not None:
            target.held_by = actor.id
            actor.memes["want"] = max(actor.meme("want"), 0.0) + 1
    elif action == "share":
        actor.meters["carrying"] = max(0.0, actor.meter("carrying") - 1)
        actor.meters["generous"] = actor.meter("generous") + 1
        actor.memes["karma"] = actor.meme("karma") + 1
    if narrate:
        propagate(world)


def _r_guilt(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meme("want") < THRESHOLD:
            continue
        if actor.meters.get("carrying", 0.0) < THRESHOLD:
            continue
        sig = ("guilt", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["guilt"] = actor.meme("guilt") + 1
        actor.memes["worry"] = actor.meme("worry") + 1
        out.append(f"{actor.id} felt a prick of worry in a small warm place inside.")
    return out


def _r_settle(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meme("karma") < THRESHOLD:
            continue
        sig = ("settle", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["harmony"] = actor.meme("harmony") + 1
        actor.memes["worry"] = max(0.0, actor.meme("worry") - 1)
        out.append(f"The balance began to settle, like pond water after a pebble falls still.")
    return out


CAUSAL_RULES = [
    _r_guilt,
    _r_settle,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


@dataclass
class StoryParams:
    place: str
    treasure: str
    gift: str
    name: str
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
    "forest": Setting(place="the moonlit forest", kind="forest", affords={"take", "share"}),
    "glade": Setting(place="the quiet glade", kind="forest", affords={"take", "share"}),
    "lantern_lane": Setting(place="the lantern lane", kind="village", affords={"take", "share"}),
}

TREASURES = {
    "berries": Treasure(label="berries", phrase="a bowl of red berries", type="berries", taste="sweet", plural=True),
    "honey": Treasure(label="honey", phrase="a pot of golden honey", type="honey", taste="sweet"),
    "cakes": Treasure(label="cakes", phrase="three little cakes", type="cakes", taste="sweet", plural=True),
}

GIFTS = {
    "bread": Gift(label="bread", phrase="a loaf of warm bread", kind="bread", helps={"berries", "honey", "cakes"}),
    "flower": Gift(label="flower", phrase="a bright flower crown", kind="flower", helps={"berries", "cakes"}),
    "song": Gift(label="song", phrase="a soft thank-you song", kind="song", helps={"berries", "honey", "cakes"}),
}

NAMES = ["Ari", "Bram", "Cleo", "Dora", "Elin", "Fenn"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for treasure_id in setting.affords:
            for gift_id, gift in GIFTS.items():
                if treasure_id in gift.helps:
                    combos.append((place, treasure_id, gift_id))
    return combos


def reason_rejection(treasure: Treasure, gift: Gift) -> str:
    return (
        f"(No story: {gift.label} does not reasonably help settle the trouble around "
        f"{treasure.phrase}. The kindness at the end would feel forced.)"
    )


def build_scene(params: StoryParams) -> StorySample:
    world = World(_safe_lookup(SETTINGS, params.place))
    hero = world.add(Entity(id=params.name, kind="character", type="aardvark"))
    treasure = world.add(Entity(id="treasure", type=params.treasure, label=_safe_lookup(TREASURES, params.treasure).label,
                                phrase=_safe_lookup(TREASURES, params.treasure).phrase, owner=hero.id))
    gift = world.add(Entity(id="gift", type=params.gift, label=_safe_lookup(GIFTS, params.gift).label,
                            phrase=_safe_lookup(GIFTS, params.gift).phrase, owner=hero.id))

    hero.memes["joy"] = 1.0
    world.say(f"Once upon a time, in {world.setting.place}, there lived an aardvark named {hero.id}.")
    world.say(f"{hero.id} loved the feel of sharing, because kindness made the lanterns glow a little brighter.")
    world.say(f"One day {hero.id} saw {treasure.phrase} and wanted {treasure.it()} very badly.")

    world.para()
    world.say(f"But in that same place, the wise old rule was simple: a sweet thing should be shared, not snatched.")
    world.say(f"{hero.id} took {treasure.it()} anyway, and at once the air felt heavier.")
    _do_action(world, hero, "take", treasure)
    world.say(f"{hero.id} hid {treasure.it()} behind a stone and tried to hush the guilty feeling.")

    world.para()
    propagate(world)
    world.say(f"Then {hero.id} noticed a smaller creature looking sadly at the empty table.")
    world.say(f"That sight made {hero.id}'s heart settle. {hero.id} carried the {gift.label} forward and bowed low.")
    _do_action(world, hero, "share", gift)
    world.say(f'"Please take this," {hero.id} said. "I did wrong, and I want to make it right."')

    world.para()
    hero.memes["karma"] = hero.meme("karma") + 1
    hero.memes["harmony"] = hero.meme("harmony") + 1
    world.say(f"The forest grew soft and kind again.")
    world.say(f"{hero.id} shared the last of the {gift.label}, and the balance of karma settled at last.")
    world.say(f"By moonrise, {hero.id} sat under a silver branch with an open hand and a peaceful chest.")

    world.facts.update(hero=hero, treasure=treasure, gift=gift, setting=world.setting)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fairy tale about an aardvark named {f["hero"].id} who learns that sharing can settle karma.',
        f"Tell a gentle story set in {f['setting'].place} where {f['hero'].id} takes {f['treasure'].phrase} and later makes amends by sharing {f['gift'].phrase}.",
        "Write a child-friendly fairy tale about wanting, taking, sharing, and the peaceful feeling after doing what is kind.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    treasure: Entity = _safe_fact(world, f, "treasure")
    gift: Entity = _safe_fact(world, f, "gift")
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about an aardvark named {hero.id} who learns about sharing and settling karma."
        ),
        QAItem(
            question=f"What did {hero.id} want at first?",
            answer=f"{hero.id} wanted {treasure.phrase}, but taking it without sharing made the air feel heavy."
        ),
        QAItem(
            question=f"How did {hero.id} make things right?",
            answer=f"{hero.id} shared {gift.phrase} and spoke kindly, which helped the balance settle again."
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"At the end, {hero.id} felt peaceful, the trouble had settled, and the sharing made the forest kind again."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is sharing?",
            answer="Sharing means letting someone else use or enjoy something with you instead of keeping it all to yourself."
        ),
        QAItem(
            question="What does it mean when karma settles?",
            answer="It means a story balance feels calm again after a person does something kind to make up for a wrong choice."
        ),
        QAItem(
            question="What is an aardvark?",
            answer="An aardvark is a real animal with a long nose that likes to sniff for food on the ground."
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
wanting(hero) :- hero(A).
guilt(A) :- took(A), treasure(T).
karma_settles(A) :- shared(A).
"""


def asp_facts() -> str:
    import asp

    lines = []
    for place, s in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        lines.append(asp.fact("affords", place, "take"))
        lines.append(asp.fact("affords", place, "share"))
        lines.append(asp.fact("place_name", place, s.place))
    for t in TREASURES:
        lines.append(asp.fact("treasure", t))
    for g in GIFTS:
        lines.append(asp.fact("gift", g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale story world: an aardvark learns to share and settle karma.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--name")
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
    combos = [c for c in combos if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "treasure", None) is None or c[1] == getattr(args, "treasure", None))
              and (getattr(args, "gift", None) is None or c[2] == getattr(args, "gift", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, treasure, gift = rng.choice(list(combos))
    return StoryParams(
        place=place,
        treasure=treasure,
        gift=gift,
        name=getattr(args, "name", None) or rng.choice(NAMES),
    )


def generate(params: StoryParams) -> StorySample:
    return build_scene(params)


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
    StoryParams(place="forest", treasure="berries", gift="bread", name="Ari"),
    StoryParams(place="glade", treasure="honey", gift="song", name="Bram"),
    StoryParams(place="lantern_lane", treasure="cakes", gift="flower", name="Cleo"),
]


def valid_stories() -> list[tuple[str, str, str]]:
    return valid_combos()


def asp_verify() -> int:
    import asp

    python_set = set(valid_combos())
    model = asp.one_model(asp_program("#show valid/3."))
    clingo_set = set(asp.atoms(model, "valid"))
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    return 1


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    return asp_valid_combos()


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, treasure, gift) combos:\n")
        for place, treasure, gift in combos:
            print(f"  {place:12} {treasure:10} {gift}")
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
