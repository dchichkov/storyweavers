#!/usr/bin/env python3
"""
storyworlds/worlds/bot_kindness_pirate_tale.py
==============================================

A tiny pirate-tale storyworld about a bot whose kindness changes the course
of one small voyage.

Premise:
- A bot on a pirate ship loves helping the crew.
- The crew finds a little sealed chest.
- Opening it too fast would hurt a trapped friend inside.
- Kindness leads the bot to slow down, help carefully, and share the treasure.

This script keeps the world classical and state-driven:
- physical meters track things like charge, damage, and treasure;
- emotional memes track kindness, worry, trust, and cheer.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    region: object | None = None
    aid: object | None = None
    bot: object | None = None
    captain: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type == "bot":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"pirate", "captain", "man", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"woman", "girl", "captainess"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
    place: str = "the pirate ship"
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
class Quest:
    id: str
    verb: str
    gerund: str
    rush: str
    harm: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)
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
class Prize:
    label: str
    phrase: str
    type: str
    region: str
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
class Aid:
    id: str
    label: str
    prep: str
    tail: str
    guards: set[str]
    covers: set[str]
    plural: bool = False
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
        self.fired: set[tuple] = set()
        self.zone: set[str] = set()
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

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(region in getattr(item, "covers", set()) for item in self.worn_items(actor))

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        return clone


def _r_damage(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("swift_action", 0.0) < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("damage", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["damage"] = item.meters.get("damage", 0.0) + 1
            out.append(f"{actor.id}'s {item.label} got scratched.")
    return out


def _r_alarm(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("worry", 0.0) < THRESHOLD:
            continue
        sig = ("alarm", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["kindness"] = actor.memes.get("kindness", 0.0) + 1
        out.append(f"{actor.id} took a careful breath and looked closer.")
    return out


CAUSAL_RULES = [
    _r_damage,
    _r_alarm,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def predict_harm(world: World, actor: Entity, quest: Quest, prize_id: str) -> dict:
    sim = world.copy()
    sim.get(actor.id).meters["swift_action"] = 1
    sim.zone = set(quest.zone)
    propagate(sim, narrate=False)
    prize = sim.entities[prize_id]
    return {
        "damaged": prize.meters.get("damage", 0.0) >= THRESHOLD,
    }


def select_aid(quest: Quest, prize: Prize) -> Optional[Aid]:
    for aid in AIDS:
        if quest.keyword in aid.guards and prize.region in aid.covers:
            return aid
    return None


def setting_line(setting: Setting, quest: Quest) -> str:
    return f"The {setting.place.removeprefix('the ')} rolled with sea wind, salt, and a little creak of wood."


def introduce(world: World, bot: Entity) -> None:
    world.say(
        f"On a small pirate ship, {bot.id} was a kind little bot who liked helping before anyone had to ask."
    )


def loves_help(world: World, bot: Entity, quest: Quest) -> None:
    bot.memes["kindness"] = bot.memes.get("kindness", 0.0) + 1
    world.say(
        f"{bot.pronoun().capitalize()} loved being useful, especially when there was a {quest.keyword} problem to solve."
    )


def bring_treasure(world: World, bot: Entity, prize: Entity) -> None:
    world.say(
        f"The crew found {bot.pronoun('possessive')} {prize.label}, and everyone leaned close to peek inside."
    )


def discover_risk(world: World, bot: Entity, quest: Quest, prize: Entity) -> None:
    world.say(
        f"{bot.id} noticed the lid was stuck, and the fastest way to open it could hurt what was inside."
    )
    bot.memes["worry"] = bot.memes.get("worry", 0.0) + 1


def warn(world: World, bot: Entity, quest: Quest, prize: Entity) -> bool:
    if not predict_harm(world, bot, quest, prize.id)["damaged"]:
        return False
    world.say(
        f'"Wait," {bot.id} said. "If we rush, we could scratch the {prize.label}."'
    )
    return True


def choose_kindness(world: World, bot: Entity, quest: Quest) -> None:
    bot.memes["kindness"] = bot.memes.get("kindness", 0.0) + 1
    world.say(f"{bot.id} offered a kinder plan instead of a rough one.")


def compromise(world: World, bot: Entity, quest: Quest, prize: Entity) -> Optional[Aid]:
    aid_def = select_aid(quest, prize)
    if aid_def is None:
        return None
    aid = world.add(Entity(
        id=aid_def.id,
        type="gear",
        label=aid_def.label,
        owner=bot.id,
        plural=aid_def.plural,
    ))
    aid.worn_by = bot.id
    aid.covers = set(aid_def.covers)  # type: ignore[attr-defined]
    if predict_harm(world, bot, quest, prize.id)["damaged"]:
        aid.worn_by = None
        del world.entities[aid.id]
        return None
    world.say(
        f"{bot.id} fetched {aid.label} and used {aid_def.prep}."
    )
    return aid


def resolve(world: World, bot: Entity, quest: Quest, prize: Entity, aid_def: Aid) -> None:
    bot.memes["worry"] = 0.0
    bot.memes["cheer"] = bot.memes.get("cheer", 0.0) + 1
    world.say(
        f"Together, they {aid_def.tail}, and the careful opening kept the {prize.label} safe."
    )
    world.say(
        f"Inside the chest, they found a tiny lost hatchling, and {bot.id} gently passed it a cup of water."
    )
    world.say(
        f"At the end, the little bot was still shiny, the crew was smiling, and the rescued friend was safe in warm hands."
    )


def tell(setting: Setting, quest: Quest, prize_cfg: Prize, bot_name: str = "Bix") -> World:
    world = World(setting)
    bot = world.add(Entity(id=bot_name, kind="character", type="bot", label="bot"))
    captain = world.add(Entity(id="Captain", kind="character", type="pirate", label="captain"))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        caretaker=captain.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))
    world.say(setting_line(setting, quest))
    introduce(world, bot)
    loves_help(world, bot, quest)
    world.para()
    bring_treasure(world, bot, prize)
    discover_risk(world, bot, quest, prize)
    warn(world, bot, quest, prize)
    choose_kindness(world, bot, quest)
    aid_def = compromise(world, bot, quest, prize)
    if aid_def is not None:
        world.para()
        resolve(world, bot, quest, prize, aid_def)
    world.facts.update(bot=bot, captain=captain, prize=prize, quest=quest, aid=aid_def, setting=setting)
    return world


SETTINGS = {
    "ship": Setting(place="the pirate ship", affords={"stuck_chest"}),
    "dock": Setting(place="the moonlit dock", affords={"stuck_chest"}),
}

QUESTS = {
    "stuck_chest": Quest(
        id="stuck_chest",
        verb="open the chest",
        gerund="opening the chest",
        rush="pry the chest open",
        harm="scratch the treasure",
        zone={"torso"},
        keyword="chest",
        tags={"treasure", "care"},
    ),
}

PRIZES = {
    "chest": Prize(
        label="treasure chest",
        phrase="a little treasure chest with a stubborn lid",
        type="chest",
        region="torso",
    ),
    "box": Prize(
        label="wooden box",
        phrase="a wooden box with a jammed latch",
        type="box",
        region="torso",
    ),
}

AIDS = [
    Aid(
        id="soft_gloves",
        label="soft gloves",
        prep="put on soft gloves first",
        tail="used soft gloves and lifted the lid gently",
        guards={"chest"},
        covers={"torso"},
    ),
    Aid(
        id="silk_cloth",
        label="a silk cloth",
        prep="lay a silk cloth over the lid",
        tail="used the silk cloth to ease the lid up slowly",
        guards={"chest"},
        covers={"torso"},
    ),
]

BOT_NAMES = ["Bix", "Milo", "Nim", "Tess", "Rin", "Pip"]
TRAITS = ["kind", "brave", "careful", "cheerful"]


@dataclass
class StoryParams:
    place: str
    quest: str
    prize: str
    bot_name: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for qid in setting.affords:
            quest = _safe_lookup(QUESTS, qid)
            for pid, prize in PRIZES.items():
                if prize.region in quest.zone and select_aid(quest, prize):
                    combos.append((place, qid, pid))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    bot = _safe_fact(world, f, "bot")
    quest = _safe_fact(world, f, "quest")
    prize = _safe_fact(world, f, "prize")
    return [
        f'Write a short pirate tale about a kind bot named {bot.id} and a {prize.label}.',
        f"Tell a story where {bot.id} wants to {quest.verb}, but kindness helps {bot.pronoun('subject')} slow down and choose a gentler plan.",
        f'Write a child-friendly pirate story using the word "kindness" and ending with a safe surprise inside a chest.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    bot = _safe_fact(world, f, "bot")
    prize = _safe_fact(world, f, "prize")
    quest = _safe_fact(world, f, "quest")
    aid = _safe_fact(world, f, "aid")
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {bot.id}, a kind little bot on a pirate ship.",
        ),
        QAItem(
            question=f"What did {bot.id} want to do with the {prize.label}?",
            answer=f"{bot.id} wanted to {quest.verb}, but {bot.pronoun('possessive')} kindness made {bot.pronoun('object')} careful.",
        ),
        QAItem(
            question=f"Why did {bot.id} stop the crew from rushing?",
            answer=f"Because rushing could have scratched the {prize.label} and hurt what was inside it.",
        ),
    ]
    if aid is not None:
        qa.append(
            QAItem(
                question=f"How did the {aid.label} help?",
                answer=f"The {aid.label} helped {bot.id} open the chest slowly and safely.",
            )
        )
        qa.append(
            QAItem(
                question=f"How did the story end?",
                answer=f"It ended with the chest opened gently, the hidden little hatchling safe, and the crew smiling with {bot.id}.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is kindness?",
            answer="Kindness is when you care about someone else and choose to help in a gentle way.",
        ),
        QAItem(
            question="What is a pirate ship?",
            answer="A pirate ship is a boat that pirates sail on the sea.",
        ),
        QAItem(
            question="Why should you open a stuck chest carefully?",
            answer="Because forcing it can break the lid or hurt whatever is inside.",
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
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="ship", quest="stuck_chest", prize="chest", bot_name="Bix"),
    StoryParams(place="dock", quest="stuck_chest", prize="box", bot_name="Nim"),
]


def explain_rejection(quest: Quest, prize: Prize) -> str:
    return f"(No story: {quest.verb} would not be a safe match for a {prize.label} here.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny pirate-tale storyworld about a kind bot.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name", dest="bot_name")
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
    if getattr(args, "quest", None) and getattr(args, "prize", None):
        q = _safe_lookup(QUESTS, getattr(args, "quest", None))
        p = _safe_lookup(PRIZES, getattr(args, "prize", None))
        if not (p.region in q.zone and select_aid(q, p)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "quest", None) is None or c[1] == getattr(args, "quest", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, quest, prize = rng.choice(list(combos))
    return StoryParams(
        place=place,
        quest=quest,
        prize=prize,
        bot_name=getattr(args, "bot_name", None) or rng.choice(BOT_NAMES),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(QUESTS, params.quest), _safe_lookup(PRIZES, params.prize), params.bot_name)
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


ASP_RULES = r"""
prize_at_risk(Q, P) :- zone(Q, R), prize_on(P, R).
fix(A, Q, P) :- aid(A), prize_at_risk(Q, P), guards(A, K), quest_keyword(Q, K), covers(A, R), prize_on(P, R).
valid(Place, Q, P) :- affords(Place, Q), prize_at_risk(Q, P), fix(_, Q, P).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for q in sorted(s.affords):
            lines.append(asp.fact("affords", pid, q))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("quest_keyword", qid, q.keyword))
        for r in sorted(q.zone):
            lines.append(asp.fact("zone", qid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("prize_on", pid, p.region))
    for aid in AIDS:
        lines.append(asp.fact("aid", aid.id))
        for g in sorted(aid.guards):
            lines.append(asp.fact("guards", aid.id, g))
        for c in sorted(aid.covers):
            lines.append(asp.fact("covers", aid.id, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.bot_name}: {p.quest} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
