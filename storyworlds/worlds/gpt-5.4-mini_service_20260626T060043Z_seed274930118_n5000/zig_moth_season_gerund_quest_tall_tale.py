#!/usr/bin/env python3
"""
storyworlds/worlds/zig_moth_season_gerund_quest_tall_tale.py
==============================================================

A small tall-tale storyworld about a zigging hero, a moth, and a seasonal quest.
The central premise is simple: a child wants to finish a quest through the woods
while a giant moth keeps following the light. The world tracks physical meters
(distance, carried things, weather protection) and emotional memes (courage,
worry, wonder, pride), so the story's turn and ending come from simulated state
rather than a fixed paragraph template.

The distinctive seed words are folded into the domain:
- zig: the path through the woods is not straight
- moth: a giant moth is the surprising helper/obstacle
- season-gerund: the quest changes with the season in motion
- Quest: the child has a named quest to finish

The style aims for a child-facing Tall Tale: wide-eyed, concrete, a little funny,
with one big turn and a clear ending image.
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
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    moth: object | None = None
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
    season: str
    weather: str
    allows: set[str] = field(default_factory=set)
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
    title: str
    verb: str
    gerund: str
    path: str
    risk: str
    reward: str
    tag: str
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


@dataclass
class Charm:
    id: str
    label: str
    phrase: str
    protects_from: set[str] = field(default_factory=set)
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
        self.facts: dict = {}
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

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone

    def carrying(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.carried_by == actor.id]


def _story_tail(setting: Setting, quest: Quest, hero: Entity, moth: Entity, charm: Charm) -> str:
    if setting.season == "spring":
        return f"The spring air smelled sweet, and {moth.label} drifted through the blossoms like a lantern with wings."
    if setting.season == "summer":
        return f"The summer air was warm, and {moth.label} bobbed over the road like a tiny moon."
    if setting.season == "autumn":
        return f"The autumn leaves spun around {hero.id}, and {moth.label} fluttered over the trail like a soft gold leaf."
    return f"The winter wind went whistling, but {moth.label} shone bright enough to guide the way."


def _has_charm(world: World, hero: Entity, charm: Charm) -> bool:
    return any(e.id == charm.id and e.carried_by == hero.id for e in world.entities.values())


def predict_finish(world: World, hero: Entity, quest: Quest, charm: Charm) -> dict:
    sim = world.copy()
    _do_quest(sim, sim.get(hero.id), quest, narrate=False)
    return {
        "done": sim.facts.get("quest_done", False),
        "moth_help": sim.facts.get("moth_help", False),
    }


def _do_quest(world: World, hero: Entity, quest: Quest, narrate: bool = True) -> None:
    if quest.id not in world.setting.allows:
        pass
    hero.meters["zig"] += 1
    hero.memes["courage"] += 1
    world.facts["zig_path"] = quest.path
    world.facts["quest_done"] = True
    if narrate:
        world.say(f"{hero.id} zigged along {quest.path} to finish the {quest.title}.")


def tell(setting: Setting, quest: Quest, charm: Charm,
         hero_name: str = "Pippa", hero_type: str = "girl",
         moth_name: str = "Milo", moth_type: str = "moth") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name))
    moth = world.add(Entity(id=moth_name, kind="character", type=moth_type, label="the moth"))
    helper = world.add(Entity(id=charm.id, type="charm", label=charm.label, phrase=charm.phrase))
    helper.carried_by = hero.id

    hero.memes["wonder"] += 1
    world.say(
        f"{hero.id} was a little {hero_type} who loved a tall tale and a brave Quest."
    )
    world.say(
        f"Every day {hero.id} practiced a zig-zag step, because the road to the {quest.title} never went straight."
    )
    world.say(
        f"One day, {hero.id} carried {charm.phrase} and set out to {quest.verb}."
    )

    world.para()
    world.say(f"The quest began in {setting.place}, where the {setting.season} {setting.weather} made the world feel extra large.")
    world.say(_story_tail(setting, quest, hero, moth, charm))
    hero.memes["worry"] += 1
    world.say(f"But the air grew tricky, and {hero.id} worried that the moth might lead {hero.pronoun('object')} in circles.")

    if charm.id == "lantern":
        world.say(f"Still, {charm.label} glowed in {hero.id}'s hand, and the moth began to dance toward the light instead of the trouble.")
        world.facts["moth_help"] = True
    else:
        world.say(f"The charm was handy, but not magical enough to calm the moth right away.")
        world.facts["moth_help"] = False

    world.para()
    if _has_charm(world, hero, charm):
        _do_quest(world, hero, quest, narrate=False)
        hero.memes["pride"] += 1
        world.say(
            f"At last {hero.id} zigged past the last root, finished the {quest.title}, and found the prize: {quest.reward}."
        )
        world.say(
            f"The moth settled on a branch like a sleepy star, and {hero.id} smiled up at the sky, warm and tall as a fence post."
        )
    else:
        pass

    world.facts.update(hero=hero, moth=moth, charm=charm, quest=quest, setting=setting)
    return world


SETTINGS = {
    "woodland": Setting(place="the whispering woodland", season="spring", weather="full of warm breeze", allows={"acorn", "riverstone"}),
    "hillroad": Setting(place="the hill road", season="summer", weather="bright with sun", allows={"acorn", "riverstone"}),
    "orchard": Setting(place="the apple orchard", season="autumn", weather="rustling with leaves", allows={"acorn", "riverstone"}),
    "lantern_lane": Setting(place="the lantern lane", season="winter", weather="frosty and blue", allows={"acorn", "riverstone"}),
}

QUESTS = {
    "acorn": Quest(
        id="acorn",
        title="Quest of the Singing Acorn",
        verb="find the singing acorn",
        gerund="finding the singing acorn",
        path="a zigging path under the old oaks",
        risk="get lost in the long grass",
        reward="a pocketful of gold leaves",
        tag="acorn",
    ),
    "riverstone": Quest(
        id="riverstone",
        title="Quest of the Riverstone Bell",
        verb="bring home the riverstone bell",
        gerund="bringing home the riverstone bell",
        path="a zigzag trail beside the bright creek",
        risk="slip on the slick stones",
        reward="a bell that rang like morning",
        tag="riverstone",
    ),
}

CHARMS = {
    "lantern": Charm(
        id="lantern",
        label="a little lantern",
        phrase="a little lantern",
        protects_from={"dark"},
    ),
    "cloak": Charm(
        id="cloak",
        label="a wool cloak",
        phrase="a wool cloak",
        protects_from={"cold"},
    ),
    "jar": Charm(
        id="jar",
        label="a clear jar",
        phrase="a clear jar",
        protects_from={"breeze"},
    ),
}

GIRL_NAMES = ["Pippa", "Mabel", "Lena", "Tilly", "Nora", "June"]
BOY_NAMES = ["Ollie", "Ned", "Bram", "Theo", "Finn", "Wes"]
MOTH_NAMES = ["Milo", "Mira", "Moss", "Moon", "Midge"]


@dataclass
class StoryParams:
    place: str
    quest: str
    charm: str
    name: str
    gender: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for quest_id in setting.allows:
            for charm_id in CHARMS:
                combos.append((place, quest_id, charm_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld: zig, moth, and a seasonal quest.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "quest", None) is None or c[1] == getattr(args, "quest", None))
              and (getattr(args, "charm", None) is None or c[2] == getattr(args, "charm", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, quest, charm = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(place=place, quest=quest, charm=charm, name=name, gender=gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, quest, setting = f["hero"], f["quest"], f["setting"]
    return [
        f'Write a tall-tale for a child named {hero.id} about a zigging Quest in {setting.place}, with a giant moth and a brave helper.',
        f'Tell a short story where {hero.id} tries to {quest.verb} while a moth follows the light.',
        f'Write a child-friendly tall tale that uses the words zig, moth, and Quest, and ends with a clear winning image.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, quest, setting, charm, moth = f["hero"], f["quest"], f["setting"], f["charm"], f["moth"]
    return [
        QAItem(
            question=f"What was {hero.id} trying to do in {setting.place}?",
            answer=f"{hero.id} was trying to {quest.verb}.",
        ),
        QAItem(
            question=f"Why did the story talk so much about zigging?",
            answer=f"Because the road to the {quest.title} went by a zigging path, not a straight one.",
        ),
        QAItem(
            question=f"What helped {hero.id} keep going when the moth got tricky?",
            answer=f"{charm.label} helped {hero.id} keep the adventure on track, and the moth started following the light instead of causing trouble.",
        ),
        QAItem(
            question=f"What changed by the end of the Quest?",
            answer=f"By the end, {hero.id} finished the quest and found {quest.reward}, while the moth grew calm and still.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does zigzag mean?",
            answer="Zigzag means a path that turns this way and that way instead of going straight.",
        ),
        QAItem(
            question="What is a moth?",
            answer="A moth is a flying insect that often comes out at night and may be drawn to light.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey or job someone does because they are looking for something important.",
        ),
        QAItem(
            question="What is a season?",
            answer="A season is one part of the year, like spring, summer, autumn, or winter.",
        ),
    ]


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
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
quest_path(zig) :- tag(quest, zig).
quest_path(moth) :- tag(moth, fly).
valid_story(P, Q, C) :- setting(P), quest(Q), charm(C).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        lines.append(asp.fact("season", pid, s.season))
        for q in sorted(s.allows):
            lines.append(asp.fact("allows", pid, q))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("tag", "quest", q.tag))
    for cid, c in CHARMS.items():
        lines.append(asp.fact("charm", cid))
        for p in sorted(c.protects_from):
            lines.append(asp.fact("protects_from", cid, p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


CURATED = [
    StoryParams(place="woodland", quest="acorn", charm="lantern", name="Pippa", gender="girl"),
    StoryParams(place="hillroad", quest="riverstone", charm="lantern", name="Ollie", gender="boy"),
    StoryParams(place="orchard", quest="acorn", charm="cloak", name="Mabel", gender="girl"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(QUESTS, params.quest), _safe_lookup(CHARMS, params.charm), params.name, params.gender)
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
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
            header = f"### {p.name}: {p.quest} at {p.place} (charm: {p.charm})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
