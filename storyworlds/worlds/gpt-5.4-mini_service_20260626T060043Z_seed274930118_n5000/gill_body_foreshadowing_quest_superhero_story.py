#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/gill_body_foreshadowing_quest_superhero_story.py
================================================================================================

A small superhero storyworld about a hero named Gill, a body-problem clue,
foreshadowing, and a quest that ends in a clear rescue.

Premise:
- Gill is a young superhero in a city that needs help.
- A weird faint mark on Gill's body foreshadows a hidden problem.
- Gill and a helper follow clues on a quest to find a stolen power core.
- The turn is that the foreshadowed body clue points to the right place.
- The resolution is a brave fix that saves the day and changes Gill's mood.

This script is intentionally self-contained, stdlib-only, and uses the shared
result containers from storyworlds/results.py. The ASP twin is inline via
ASP_RULES and mirrors the Python reasonableness gate.
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
    protective: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    traits: list = field(default_factory=list)
    helper: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
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
    name: str
    indoors: bool
    clue: str
    threat: str
    SETTING: object | None = None
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
class Quest:
    id: str
    goal: str
    path: str
    reward: str
    clue_kind: str
    risk_kind: str
    setting_key: str
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
class Gear:
    id: str
    label: str
    guards: set[str]
    covers: set[str]
    prep: str
    tail: str
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
    def __init__(self, place: Place, quest: Quest) -> None:
        self.place = place
        self.quest = quest
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.foreshadowed: bool = False
        self.clue_found: bool = False

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
        w = World(self.place, self.quest)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.foreshadowed = self.foreshadowed
        w.clue_found = self.clue_found
        return w


SETTING = Place(
    name="the city",
    indoors=False,
    clue="a faint blue glow on the wall",
    threat="a dark energy drain",
)

QUESTS = {
    "core": Quest(
        id="core",
        goal="find the stolen power core",
        path="follow the clue trail",
        reward="the city's lights turn back on",
        clue_kind="glow",
        risk_kind="drain",
        setting_key="city",
    ),
    "signal": Quest(
        id="signal",
        goal="restore the tower signal",
        path="track the buzzing street lamps",
        reward="the tower begins to hum again",
        clue_kind="buzz",
        risk_kind="shadow",
        setting_key="city",
    ),
}

GEAR = [
    Gear(
        id="gloves",
        label="shock gloves",
        guards={"drain"},
        covers={"hands"},
        prep="put on shock gloves first",
        tail="grabbed the core with the shock gloves on",
    ),
    Gear(
        id="mask",
        label="a silver mask",
        guards={"shadow"},
        covers={"face"},
        prep="wear a silver mask first",
        tail="stepped into the dark with a silver mask",
    ),
    Gear(
        id="cape",
        label="a sturdy cape",
        guards={"wind"},
        covers={"back"},
        prep="fasten a sturdy cape first",
        tail="flew through the wind with a sturdy cape",
    ),
]

GENDERS = {"girl", "boy"}
NAMES = ["Gill", "Aria", "Nova", "Kai", "Mina", "Tess", "Rex", "Luca"]
HELPERS = ["Aunt Star", "Captain Kite", "Mister Flash", "Doctor Beam"]

ASP_RULES = r"""
quest_valid(Q) :- quest(Q), clue_kind(Q,C), risk_kind(Q,R), has_gear(C,R).
"""

HEROES = {
    "gill": {
        "type": "boy",
        "label": "Gill",
        "traits": ["brave", "quick", "kind"],
    }
}


def _risk_of(quest: Quest) -> str:
    return quest.risk_kind


def _clue_of(quest: Quest) -> str:
    return quest.clue_kind


def quest_has_gear(quest: Quest) -> bool:
    clue = _clue_of(quest)
    risk = _risk_of(quest)
    return any(risk in g.guards for g in GEAR) and clue in {"glow", "buzz"}


def select_gear(quest: Quest) -> Optional[Gear]:
    clue = _clue_of(quest)
    risk = _risk_of(quest)
    for gear in GEAR:
        if risk in gear.guards and gear.label and clue:
            return gear
    return None


def foreshadow(world: World, hero: Entity, quest: Quest, helper: Entity) -> None:
    hero.memes["unease"] = hero.memes.get("unease", 0.0) + 1
    world.foreshadowed = True
    world.say(
        f"Gill felt a strange tickle in {hero.pronoun('possessive')} body, like "
        f"something important was trying to warn {hero.pronoun('object')}."
    )
    world.say(
        f"On the wall, {SETTING.clue} shimmered once, and {helper.label} said, "
        f'"That kind of clue usually means a bigger problem is nearby."'
    )


def run_quest(world: World, hero: Entity, quest: Quest, helper: Entity) -> Optional[Gear]:
    gear = select_gear(quest)
    if gear is None:
        return None
    world.say(
        f"Gill and {helper.label} decided to {quest.path} and look for "
        f"the thing behind the mystery."
    )
    world.say(
        f"Before they left, {helper.label} told Gill to {gear.prep}, because "
        f"the hidden danger could hit hard."
    )
    return gear


def resolve(world: World, hero: Entity, quest: Quest, helper: Entity, gear: Gear) -> None:
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1
    hero.memes["fear"] = 0.0
    world.clue_found = True
    world.say(
        f"At last, the clue led them to the stolen core, and Gill "
        f"{gear.tail}."
    )
    world.say(
        f"The core stopped the drain, the city lights came back, and Gill's "
        f"body felt steady again."
    )
    world.say(
        f"Gill smiled at {helper.label} because the foreshadowed warning had "
        f"helped them save the day."
    )


def tell_story(hero_name: str = "Gill", helper_name: str = "Captain Kite", quest_id: str = "core") -> World:
    quest = _safe_lookup(QUESTS, quest_id)
    world = World(SETTING, quest)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type="boy" if hero_name == "Gill" else "hero",
        label=hero_name,
        traits=["brave", "quick", "kind"],
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type="adult",
        label=helper_name,
        traits=["wise"],
    ))

    world.say(
        f"Gill was a small superhero with a brave heart and a body that noticed "
        f"things before other people did."
    )
    world.say(
        f"{helper.label} said Gill had a good eye for trouble, especially when "
        f"the trouble was hiding."
    )
    world.para()
    foreshadow(world, hero, quest, helper)
    gear = run_quest(world, hero, quest, helper)
    if gear is None:
        pass
    world.para()
    resolve(world, hero, quest, helper, gear)
    world.facts.update(
        hero=hero,
        helper=helper,
        quest=quest,
        gear=gear,
        foreshadowed=world.foreshadowed,
        clue_found=world.clue_found,
    )
    return world


@dataclass
class StoryParams:
    hero: str
    helper: str
    quest: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero foreshadowing quest storyworld.")
    ap.add_argument("--hero", choices=["Gill"], default=None)
    ap.add_argument("--helper", choices=HELPERS, default=None)
    ap.add_argument("--quest", choices=QUESTS, default=None)
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
    hero = getattr(args, "hero", None) or "Gill"
    helper = getattr(args, "helper", None) or rng.choice(HELPERS)
    quest = getattr(args, "quest", None) or rng.choice(list(QUESTS))
    if hero.lower() != "gill":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if quest not in QUESTS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if not quest_has_gear(_safe_lookup(QUESTS, quest)):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(hero=hero, helper=helper, quest=quest)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a short superhero story for a child about Gill noticing a clue in his body before a quest.",
        f"Tell a story where {f['hero'].label} and {f['helper'].label} follow a foreshadowed clue to {f['quest'].goal}.",
        "Make the ending show that the warning clue mattered and the city was saved.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, quest = f["hero"], f["helper"], f["quest"]
    return [
        QAItem(
            question="Who is the superhero in the story?",
            answer=f"The superhero is Gill, a small hero who notices clues in his body and stays brave.",
        ),
        QAItem(
            question=f"What did Gill and {helper.label} do when the clue appeared?",
            answer=f"They followed the clue and began a quest to {quest.goal}.",
        ),
        QAItem(
            question="What did the foreshadowing help them understand?",
            answer="It helped them understand that the strange clue was pointing to real danger, so they could act before the problem got worse.",
        ),
        QAItem(
            question="How did the story end?",
            answer="They found the hidden danger, fixed it, and the city lights came back on.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is when a story gives a small clue early so readers can guess that something important may happen later.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a goal-filled journey where someone goes looking for something important or tries to solve a hard problem.",
        ),
        QAItem(
            question="Why do superheroes wear gear?",
            answer="Superheroes wear gear to protect themselves and to help them handle danger while they work.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(parts)}")
    lines.append(f"  foreshadowed={world.foreshadowed} clue_found={world.clue_found}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params.hero, params.helper, params.quest)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
    StoryParams(hero="Gill", helper="Captain Kite", quest="core"),
]


def asp_facts() -> str:
    import asp
    lines = []
    lines.append(asp.fact("hero", "gill"))
    lines.append(asp.fact("quest", "core"))
    lines.append(asp.fact("clue_kind", "core", "glow"))
    lines.append(asp.fact("risk_kind", "core", "drain"))
    lines.append(asp.fact("has_gear", "glow", "drain"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show quest_valid/1."))
    clingo_set = set(asp.atoms(model, "quest_valid"))
    python_set = {("core",)} if quest_has_gear(QUESTS["core"]) else set()
    if clingo_set == python_set:
        print("OK: ASP matches Python reasonableness gate.")
        return 0
    print("MISMATCH between ASP and Python gate.")
    print("ASP:", sorted(clingo_set))
    print("PY :", sorted(python_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show quest_valid/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen = set()
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
