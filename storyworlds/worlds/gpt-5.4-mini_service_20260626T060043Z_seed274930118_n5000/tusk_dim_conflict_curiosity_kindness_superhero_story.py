#!/usr/bin/env python3
"""
tusk_dim_conflict_curiosity_kindness_superhero_story.py
========================================================

A small superhero storyworld about a curious young hero, a dim tusk, a conflict,
and a kind fix.

The world is built around a seed tale:
- a child hero notices a tusk in a dim place
- curiosity leads to trouble
- conflict rises when someone wants the tusk for the wrong reason
- kindness turns the day into a rescue

The prose is driven by state:
- light level changes
- trust and fear change
- an object can be hidden, guarded, or returned
- the ending proves what changed by showing the tusk safe and the room bright
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, replace
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
    guardian: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)
    plural: bool = False

    hero: object | None = None
    lamp: object | None = None
    rival: object | None = None
    tusk: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "heroine"}
        male = {"boy", "father", "man", "hero"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name_word(self) -> str:
        return self.label or self.id
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
    dimness: float
    light_source: str
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
class Gadget:
    id: str
    label: str
    phrase: str
    light_gain: float
    kind: str = "tool"
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
    hero_name: str
    hero_type: str
    rival_name: str
    rival_type: str
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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = {k: replace(v, meters=dict(v.meters), memes=dict(v.memes), traits=list(v.traits))
                          for k, v in self.entities.items()}
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


SETTINGS = {
    "museum": Setting(place="the museum hall", dimness=0.7, light_source="a tiny skylight"),
    "cave": Setting(place="the shadowy cave", dimness=0.9, light_source="a flashlight"),
    "attic": Setting(place="the old attic", dimness=0.8, light_source="a dusty lamp"),
}

HERO_TYPES = ["girl", "boy"]
RIVAL_TYPES = ["boy", "girl"]
HERO_NAMES = ["Mira", "Theo", "Nina", "Owen", "Lia", "Finn"]
RIVAL_NAMES = ["Rex", "Pia", "Gus", "Jade", "Cole", "Rita"]


@dataclass
class Tusk:
    label: str = "tusk"
    phrase: str = "a pale ivory tusk"
    safe_place: str = "a soft velvet stand"
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
class Problem:
    label: str
    fear_line: str
    action: str
    harm: str
    PROBLEM: object | None = None
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


PROBLEM = Problem(
    label="the rival wanted to carry it away",
    fear_line="someone was trying to grab the tusk in the dark",
    action="snatch the tusk",
    harm="leave the room even dimmer and the tusk in danger",
)

GADGETS = [
    Gadget(id="lamp", label="a lantern", phrase="a bright lantern", light_gain=1.0),
    Gadget(id="prism", label="a prism badge", phrase="a shining prism badge", light_gain=0.5),
    Gadget(id="mirror", label="a mirror shield", phrase="a silver mirror shield", light_gain=0.8),
]


class Rules:
    @staticmethod
    def apply(world: World) -> list[str]:
        out: list[str] = []
        hero = world.get("hero")
        tusk = world.get("tusk")
        rival = world.get("rival")
        if hero.memes.get("kindness", 0.0) >= THRESHOLD and rival.memes.get("shame", 0.0) >= THRESHOLD:
            sig = ("resolve",)
            if sig not in world.fired:
                world.fired.add(sig)
                world.facts["resolved"] = True
                world.facts["tusk_safe"] = True
                tusk.meters["safe"] = 1.0
                out.append("The kind choice settled the conflict.")
        return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        sents = Rules.apply(world)
        if sents:
            changed = True
            produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def dimmer_story_line(setting: Setting) -> str:
    if setting.place == "the museum hall":
        return "The hall glowed weakly under a small skylight."
    if setting.place == "the shadowy cave":
        return "The cave stayed dim, with one beam of light on the stone floor."
    return "The attic felt dim and sleepy, with one old lamp blinking awake."


def tell(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    world = World(setting)

    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero_name))
    rival = world.add(Entity(id="rival", kind="character", type=params.rival_type, label=params.rival_name))
    tusk = world.add(Entity(id="tusk", kind="thing", type="artifact", label="tusk",
                            phrase="a pale ivory tusk", owner=None, guardian="hero"))
    lamp = world.add(Entity(id="lamp", kind="thing", type="tool", label="lantern",
                            phrase="a bright lantern", owner="hero"))

    world.facts.update(setting=setting, hero=hero, rival=rival, tusk=tusk, lamp=lamp)

    hero.memes["curiosity"] = 1.0
    hero.memes["kindness"] = 0.0
    rival.memes["greed"] = 0.0
    tusk.meters["safe"] = 0.0

    world.say(f"{hero.label} was a small hero with a brave cape and quick eyes.")
    world.say(f"{hero.pronoun().capitalize()} loved noticing strange things before anyone else did.")
    world.say(f"One day in {setting.place}, {hero.label} found {tusk.phrase}.")
    world.say(dimmer_story_line(setting))
    world.say(f"The tusk looked even more special because the place was so dim.")

    world.para()
    world.say(f"{hero.label} leaned closer, full of curiosity.")
    hero.memes["curiosity"] += 1.0
    world.say(f"{hero.pronoun().capitalize()} wanted to see where the tusk came from and why it was hidden there.")
    world.say(f"Then {rival.label} stepped out and wanted to {PROBLEM.action}.")
    rival.memes["greed"] += 1.0
    rival.memes["conflict"] += 1.0
    world.say(f"That would {PROBLEM.harm}.")
    world.say(f"{hero.label} felt the worry rise, because {PROBLEM.fear_line}.")

    world.para()
    world.say(f"{hero.label} did not push or shout.")
    hero.memes["kindness"] += 1.0
    world.say(f"{hero.pronoun().capitalize()} turned on the lantern and held it low so everyone could see.")
    setting_light = setting.dimness - lamp.meters.get("light", 0.0)
    if setting_light > 0:
        world.say(f"The light reached the tusk and made the shadows shrink back.")
    rival.memes["shame"] = 1.0
    world.say(f"{hero.label} said the tusk should stay on {tusk.owner or tusk.guardian or 'the stand'} where it would be safe and shared.")
    world.say(f"That kind idea made {rival.label} pause.")
    world.say(f"{rival.label} lowered {rival.pronoun('possessive')} hands and nodded.")

    propagate(world, narrate=True)

    if not world.facts.get("resolved"):
        world.facts["resolved"] = True
        world.facts["tusk_safe"] = True
        tusk.meters["safe"] = 1.0

    world.para()
    world.say(f"After that, {hero.label} placed the tusk on {Tusk().safe_place}.")
    world.say(f"The lantern kept the room bright, and the two children stood together instead of apart.")
    world.say(f"The tusk stayed safe, and the dim place felt gentle now.")

    world.facts["kindness"] = hero.memes["kindness"]
    world.facts["curiosity"] = hero.memes["curiosity"]
    world.facts["conflict"] = rival.memes.get("conflict", 0.0) >= THRESHOLD
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    rival = _safe_fact(world, f, "rival")
    setting = _safe_fact(world, f, "setting")
    return [
        f'Write a short superhero story for a child where {hero.label} notices a tusk in {setting.place} and curiosity leads to trouble.',
        f"Tell a simple story about {hero.label} and {rival.label} in a dim place, where kindness solves a conflict about a tusk.",
        f'Write a gentle adventure story that includes the words "tusk" and "dim" and ends with a safe, happy rescue.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    rival = _safe_fact(world, f, "rival")
    setting = _safe_fact(world, f, "setting")
    qa = [
        QAItem(
            question=f"Who found the tusk in {setting.place}?",
            answer=f"{hero.label} found the tusk in {setting.place} while looking around with curious eyes.",
        ),
        QAItem(
            question=f"Why did the scene turn into a conflict?",
            answer=f"It turned into a conflict because {rival.label} wanted to snatch the tusk and carry it away.",
        ),
        QAItem(
            question=f"What did {hero.label} do instead of fighting back?",
            answer=f"{hero.label} chose kindness, turned on the lantern, and helped everyone see that the tusk should stay safe.",
        ),
        QAItem(
            question="How did the story end?",
            answer="The tusk stayed on a safe stand, the room was brighter, and the children were calm together.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tusk?",
            answer="A tusk is a long, pointed tooth that grows out of the mouth of some animals.",
        ),
        QAItem(
            question="What does dim mean?",
            answer="Dim means not very bright, so it can be hard to see things clearly.",
        ),
        QAItem(
            question="What does kindness do in a hard moment?",
            answer="Kindness helps people calm down, share, and choose a safer way to solve a problem.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the wish to look, learn, and ask questions about something new.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World-knowledge questions ==")
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
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="museum", hero_name="Mira", hero_type="girl", rival_name="Rex", rival_type="boy"),
    StoryParams(place="cave", hero_name="Theo", hero_type="boy", rival_name="Jade", rival_type="girl"),
    StoryParams(place="attic", hero_name="Lia", hero_type="girl", rival_name="Cole", rival_type="boy"),
]


ASP_RULES = r"""
hero(H) :- selected_hero(H, _).
rival(R) :- selected_rival(R, _).
setting(P) :- selected_place(P).

curious(H) :- selected_hero(H, _).
dim_place(P) :- place_dim(P, D), D > 0.5.

conflict(H, R, T) :- curious(H), rival(R), tusk(T), wants_rival(R, T).
resolved(H, R, T) :- conflict(H, R, T), kind_act(H), shares_light(H).

safe_tusk(T) :- resolved(_, _, T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("selected_place", pid))
        lines.append(asp.fact("place_dim", pid, int(setting.dimness * 10)))
    for name in HERO_NAMES:
        lines.append(asp.fact("selected_hero", name, "hero"))
    for name in RIVAL_NAMES:
        lines.append(asp.fact("selected_rival", name, "rival"))
    lines.append(asp.fact("tusk", "tusk"))
    lines.append(asp.fact("wants_rival", "rival", "tusk"))
    lines.append(asp.fact("kind_act", "hero"))
    lines.append(asp.fact("shares_light", "hero"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for h in HERO_TYPES:
            for r in RIVAL_TYPES:
                combos.append((place, h, r))
    return combos


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show resolved/3."))
    return sorted(set(asp.atoms(model, "resolved")))


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    py = set()
    for place in SETTINGS:
        py.add((place, "hero", "rival"))
    cl = set(asp_valid_combos())
    if cl == py:
        print("OK: ASP parity holds.")
        return 0
    print("MISMATCH:")
    print("python:", sorted(py))
    print("asp:", sorted(cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld with a dim tusk, curiosity, conflict, and kindness.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
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
    return StoryParams(
        place=place,
        hero_name=rng.choice(HERO_NAMES),
        hero_type=rng.choice(HERO_TYPES),
        rival_name=rng.choice(RIVAL_NAMES),
        rival_type=rng.choice(RIVAL_TYPES),
    )


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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show resolved/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    if getattr(args, "asp", None):
        print("ASP mode is available, but this world's core story logic is Python-driven.")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 20, 20):
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

    for idx, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
