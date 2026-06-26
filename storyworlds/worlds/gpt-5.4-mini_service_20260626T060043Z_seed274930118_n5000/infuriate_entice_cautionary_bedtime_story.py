#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/infuriate_entice_cautionary_bedtime_story.py
================================================================================

A small bedtime story world about a sleepy child, one tempting thing, and the
gentle caution that helps the night end well.

The core premise is simple:
- A child wants to keep doing one more exciting thing.
- That tempting thing can make bedtime go wrong.
- A caring grown-up warns them, offers a safer choice, and the night settles.

The story is driven by a live world model with physical meters and emotional
memes, plus an inline ASP twin for the reasonableness gate.
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
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
class Setting:
    place: str
    indoor: bool = True
    quiet: bool = True
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
class Temptation:
    id: str
    noun: str
    verb: str
    gerund: str
    lure: str
    risk: str
    effect: str
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
class Comfort:
    id: str
    label: str
    prep: str
    tail: str
    calms: set[str] = field(default_factory=set)
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
    temptation: str
    comfort: str
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _rule_sleepy(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.kind != "character":
            continue
        if e.meters.get("awake", 0.0) >= THRESHOLD:
            e.meters["sleepy"] = e.meters.get("sleepy", 0.0) + 1
            out.append(f"{e.id} felt sleepier and sleepier.")
    return out


def _rule_infuriate(world: World) -> list[str]:
    out = []
    child = world.entities.get("child")
    if not child:
        return out
    if child.memes.get("blocked", 0.0) >= THRESHOLD and child.memes.get("stubborn", 0.0) >= THRESHOLD:
        sig = ("infuriate", child.id)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["cross"] = child.memes.get("cross", 0.0) + 1
            out.append(f"{child.id} crossed {child.pronoun('possessive')} arms and grew more upset.")
    return out


def _rule_settle(world: World) -> list[str]:
    out = []
    child = world.entities.get("child")
    if not child:
        return out
    if child.memes.get("calmed", 0.0) >= THRESHOLD and child.meters.get("sleepy", 0.0) >= THRESHOLD:
        sig = ("settle", child.id)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["peace"] = child.memes.get("peace", 0.0) + 1
            out.append(f"{child.id} finally softened and felt ready for bed.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_rule_sleepy, _rule_infuriate, _rule_settle):
            s = rule(world)
            if s:
                changed = True
                produced.extend(s)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def bedtime_detail(setting: Setting, temptation: Temptation) -> str:
    if setting.indoor:
        return f"The room was quiet, with soft shadows and a little lamp glowing near the bed."
    return f"The night outside was still, and the windows looked blue and hush-quiet."


def predicted_mischief(world: World, child: Entity, temptation: Temptation) -> dict:
    sim = world.copy()
    _do_temptation(sim, sim.get(child.id), temptation, narrate=False)
    return {
        "upset": sim.entities[child.id].memes.get("blocked", 0.0) >= THRESHOLD,
        "awake": sim.entities[child.id].meters.get("awake", 0.0),
    }


def _do_temptation(world: World, child: Entity, temptation: Temptation, narrate: bool = True) -> None:
    if temptation.id not in world.setting.affords:
        pass
    child.meters["awake"] = child.meters.get("awake", 0.0) + 1
    child.memes["enticed"] = child.memes.get("enticed", 0.0) + 1
    child.memes["blocked"] = child.memes.get("blocked", 0.0) + 1
    child.memes["stubborn"] = child.memes.get("stubborn", 0.0) + 1
    propagate(world, narrate=narrate)


def tell(setting: Setting, temptation: Temptation, comfort: Comfort,
         hero_name: str = "Mina", hero_type: str = "girl",
         hero_traits: Optional[list[str]] = None, caretaker_type: str = "mother") -> World:
    world = World(setting)
    child = world.add(Entity(
        id="child", kind="character", type=hero_type, label=hero_name,
        meters={"awake": 1.0}, memes={"curious": 1.0, "stubborn": 1.0},
    ))
    caretaker = world.add(Entity(
        id="caretaker", kind="character", type=caretaker_type, label="the grown-up"
    ))

    world.say(f"{child.label} was a little {next((t for t in (hero_traits or ['curious']) if t != 'little'), 'curious')} {hero_type} who loved bedtime stories.")
    world.say(f"{child.pronoun().capitalize()} liked the soft part of night, when the blankets felt warm and the house felt safe.")
    world.say(f"But {child.pronoun('possessive')} eyes still followed {temptation.noun}, because it looked so {temptation.lure}.")

    world.para()
    world.say(f"It was bedtime in {setting.place}. {bedtime_detail(setting, temptation)}")
    world.say(f"{child.label} wanted to {temptation.verb}, even though {caretaker.label} said it was time to rest.")
    if predicted_mischief(world, child, temptation)["upset"]:
        world.say(f'"If you keep going," {caretaker.label} warned, "you will feel even more awake, and that can make the night feel long."')
    _do_temptation(world, child, temptation, narrate=False)

    world.para()
    world.say(f"{child.label} felt the warning and got cross. {child.pronoun().capitalize()} wanted the fun to keep going.")
    world.say(f"{child.pronoun().capitalize()} tried to reach for {temptation.noun} again, and that only made {child.pronoun('possessive')} mood hotter and hotter.")
    child.memes["blocked"] = child.memes.get("blocked", 0.0) + 1
    propagate(world, narrate=True)

    world.para()
    child.memes["calmed"] = child.memes.get("calmed", 0.0) + 1
    world.say(f"Then {caretaker.label} knelt beside {child.pronoun('object')} and offered a kinder choice.")
    world.say(f'"How about {comfort.prep}?" {caretaker.label} asked. "You can still enjoy the night, but your body can slow down."')
    world.say(f"{child.label} listened, because the offer sounded gentle and {comfort.label} seemed safe.")
    world.say(f"They {comfort.tail}.")
    child.meters["sleepy"] = child.meters.get("sleepy", 0.0) + 1
    propagate(world, narrate=True)
    world.say(f"At last {child.label} curled up, {child.pronoun('possessive')} eyes heavy and soft, while the tempting {temptation.noun} stayed put for tomorrow.")
    world.say(f"The room grew still, and bedtime won in the quietest way.")

    world.facts.update(
        child=child,
        caretaker=caretaker,
        temptation=temptation,
        comfort=comfort,
        setting=setting,
        resolved=True,
        infuriated=child.memes.get("cross", 0.0) >= THRESHOLD,
    )
    return world


SETTINGS = {
    "bedroom": Setting(place="the bedroom", indoor=True, quiet=True, affords={"storybook", "glowtoy"}),
    "nursery": Setting(place="the nursery", indoor=True, quiet=True, affords={"musicbox", "nightlight"}),
    "cabin": Setting(place="the little cabin", indoor=True, quiet=True, affords={"storybook", "glowtoy", "musicbox"}),
}

TEMPTATIONS = {
    "storybook": Temptation(
        id="storybook",
        noun="the shiny storybook",
        verb="turn its pages one more time",
        gerund="turning pages",
        lure="bright and exciting",
        risk="staying awake too long",
        effect="kept the child's mind buzzing",
        tags={"book", "night", "read"},
    ),
    "glowtoy": Temptation(
        id="glowtoy",
        noun="the glowing toy",
        verb="push its button again and again",
        gerund="watching it glow",
        lure="sparkly and hard to ignore",
        risk="keeping sleepy eyes open",
        effect="made the room feel lively",
        tags={"toy", "light", "night"},
    ),
    "musicbox": Temptation(
        id="musicbox",
        noun="the music box",
        verb="wind it up one more time",
        gerund="listening to the tune",
        lure="sweet and twinkly",
        risk="making the bedtime hour stretch",
        effect="made thoughts dance",
        tags={"music", "night"},
    ),
}

COMFORTS = {
    "cuddle": Comfort(
        id="cuddle",
        label="safe and cozy",
        prep="we curl up for one quiet cuddle and a whisper of the story",
        tail="snuggled under the blanket and listened to the last sleepy page",
        calms={"book", "night"},
    ),
    "milk": Comfort(
        id="milk",
        label="warm and calming",
        prep="we sip a small cup of warm milk and breathe slowly together",
        tail="drank the warm milk and settled their head onto the pillow",
        calms={"toy", "night"},
    ),
    "song": Comfort(
        id="song",
        label="soft and soothing",
        prep="we hum a tiny bedtime song and count the slow breaths",
        tail="hummed along and let the quiet tune carry the excitement away",
        calms={"music", "night"},
    ),
}

CHILD_NAMES = ["Mina", "Ivo", "Nia", "Theo", "Luna", "Owen", "Pia", "Sage"]
TRAITS = ["curious", "spirited", "hopeful", "restless", "gentle", "playful"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sname, setting in SETTINGS.items():
        for tid in setting.affords:
            tempt = _safe_lookup(TEMPTATIONS, tid)
            for cname, comfort in COMFORTS.items():
                if tempt.tags & comfort.calms:
                    combos.append((sname, tid, cname))
    return combos


def explain_rejection(temptation: Temptation, comfort: Comfort) -> str:
    return (
        f"(No story: nothing about {temptation.noun} makes {comfort.label} a believable fix. "
        f"Pick a comfort that matches the tempting thing's kind.)"
    )


def explain_gender(gender: str) -> str:
    return f"(No story: this little bedtime world is comfortable for a {gender} hero too; the gender pin is only used for names.)"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    temp = _safe_fact(world, f, "temptation")
    setting = _safe_fact(world, f, "setting")
    return [
        f'Write a short cautionary bedtime story for a small child named {child.label} about {temp.noun} in {setting.place}.',
        f"Tell a gentle bedtime story where {child.label} is tempted to {temp.verb}, but a grown-up helps them calm down.",
        f'Write a bedtime story that includes the word "{temp.id}" and ends with a sleepy child choosing the safer option.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    temp = _safe_fact(world, f, "temptation")
    comfort = _safe_fact(world, f, "comfort")
    caretaker = _safe_fact(world, f, "caretaker")
    setting = _safe_fact(world, f, "setting")
    qa = [
        QAItem(
            question=f"Who was the bedtime story about in {setting.place}?",
            answer=f"It was about {child.label}, a little {child.type} who wanted to stay awake for one more tempting thing.",
        ),
        QAItem(
            question=f"What did {child.label} want to do with {temp.noun}?",
            answer=f"{child.label} wanted to {temp.verb}, even though that would make bedtime harder.",
        ),
        QAItem(
            question=f"What gentle choice did {caretaker.label} offer instead?",
            answer=f"{caretaker.label} offered {comfort.prep}, which was a calmer way to end the night.",
        ),
    ]
    if f.get("infuriated"):
        qa.append(
            QAItem(
                question=f"Why did {child.label} get so upset before calming down?",
                answer=f"{child.label} got upset because the tempting {temp.noun} felt exciting, but it also risked keeping {child.pronoun('object')} awake too long. The warning made {child.pronoun('object')} feel blocked, and that crossed-up feeling had to cool off before bedtime could work.",
            )
        )
    qa.append(
        QAItem(
            question="How did the story end?",
            answer=f"It ended with {child.label} curled up, sleepy and quiet, while the tempting {temp.noun} stayed for tomorrow.",
        )
    )
    return qa


KNOWLEDGE = {
    "book": [("Why can a storybook make you stay awake?",
              "A storybook can make you stay awake because you want to keep reading and see what happens next.")],
    "toy": [("Why should some toys wait until morning?",
             "Some toys are exciting and bright, so playing with them at bedtime can keep your body from slowing down.")],
    "music": [("Why can a music box feel soothing?",
               "A music box feels soothing because its soft tune is slow and calm, which helps a sleepy child relax.")],
    "night": [("What makes bedtime special?",
               "Bedtime is special because everything gets quiet, and the house can feel safe and cozy.")],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["temptation"].tags)
    out: list[QAItem] = []
    for tag, pairs in KNOWLEDGE.items():
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in pairs)
    return out


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
        lines.append(f"  {e.id:9} ({e.type:8}) meters={meters} memes={memes}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(s1).
setting(s2).
setting(s3).

affords(s1,storybook).
affords(s1,glowtoy).
affords(s2,musicbox).
affords(s2,nightlight).
affords(s3,storybook).
affords(s3,glowtoy).
affords(s3,musicbox).

temptation(storybook).
temptation(glowtoy).
temptation(musicbox).

comfort(cuddle).
comfort(milk).
comfort(song).

tag(storybook,book).
tag(storybook,night).
tag(glowtoy,toy).
tag(glowtoy,light).
tag(glowtoy,night).
tag(musicbox,music).
tag(musicbox,night).

calms(cuddle,book).
calms(cuddle,night).
calms(milk,toy).
calms(milk,night).
calms(song,music).
calms(song,night).

valid(S,T,C) :- affords(S,T), tag(T,X), calms(C,X).
valid(S,T,C) :- affords(S,T), tag(T,night), calms(C,night).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for tid in TEMPTATIONS:
        lines.append(asp.fact("temptation", tid))
    for cid in COMFORTS:
        lines.append(asp.fact("comfort", cid))
    for sname, setting in SETTINGS.items():
        for tid in setting.affords:
            lines.append(asp.fact("affords", sname, tid))
    for tid, t in TEMPTATIONS.items():
        for tag in t.tags:
            lines.append(asp.fact("tag", tid, tag))
    for cid, c in COMFORTS.items():
        for tag in c.calms:
            lines.append(asp.fact("calms", cid, tag))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cautionary bedtime story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--temptation", choices=TEMPTATIONS)
    ap.add_argument("--comfort", choices=COMFORTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--caretaker", choices=["mother", "father"])
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
    if getattr(args, "temptation", None) and getattr(args, "comfort", None):
        tempt = _safe_lookup(TEMPTATIONS, getattr(args, "temptation", None))
        comfort = _safe_lookup(COMFORTS, getattr(args, "comfort", None))
        if not (tempt.tags & comfort.calms):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "temptation", None) is None or c[1] == getattr(args, "temptation", None))
              and (getattr(args, "comfort", None) is None or c[2] == getattr(args, "comfort", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, temptation, comfort = rng.choice(list(combos))
    temp = _safe_lookup(TEMPTATIONS, temptation)
    name = getattr(args, "name", None) or rng.choice(CHILD_NAMES)
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    caretaker = getattr(args, "caretaker", None) or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(setting=setting, temptation=temptation, comfort=comfort,
                       name=name, gender=gender, caretaker=caretaker, trait=trait)


def story_prompt(world: World) -> list[str]:
    return generation_prompts(world)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.setting),
        _safe_lookup(TEMPTATIONS, params.temptation),
        _safe_lookup(COMFORTS, params.comfort),
        hero_name=params.name,
        hero_type=params.gender,
        hero_traits=[params.trait, "little"],
        caretaker_type=params.caretaker,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=story_prompt(world),
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
    StoryParams(setting="bedroom", temptation="storybook", comfort="cuddle", name="Mina", gender="girl", caretaker="mother", trait="curious"),
    StoryParams(setting="nursery", temptation="glowtoy", comfort="milk", name="Theo", gender="boy", caretaker="father", trait="restless"),
    StoryParams(setting="cabin", temptation="musicbox", comfort="song", name="Luna", gender="girl", caretaker="mother", trait="playful"),
]


def asp_valid_stories() -> list[tuple]:
    return []


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (setting, temptation, comfort) combos:\n")
        for s, t, c in triples:
            print(f"  {s:8} {t:10} {c:8}")
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.temptation} in {p.setting} (comfort: {p.comfort})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
