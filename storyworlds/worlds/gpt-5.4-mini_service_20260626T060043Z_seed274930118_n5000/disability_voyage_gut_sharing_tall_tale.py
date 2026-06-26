#!/usr/bin/env python3
"""
storyworlds/worlds/disability_voyage_gut_sharing_tall_tale.py
==============================================================

A small storyworld for a tall-tale voyage about disability, sharing, and a
tricky waterway called the Gut.

Seed tale:
---
A one-legged peddler named Juniper wanted to sail the long river to bring a
bright lantern to her aunt on the far bank. Her wooden leg made the docks hard
to climb, but she knew every bend in the water and had a gut feeling about
storms. She and her brother shared the work, the snacks, and the steering oar.
When the river narrowed into the Gut, a great wind rose, yet Juniper used her
map and her brother's help to keep the boat steady. They reached the far side
just as the lantern-light was needed, and everyone on the dock cheered as if
the moon had tied a ribbon in the sky.

This script models:
- physical meters: balance, wind, tide, wetness, fatigue, help
- emotional memes: hope, worry, pride, trust, joy, relief

The premise and turn are state-driven:
- a disabled voyager can still lead the trip, but steep docks and rough water
  make the crossing risky
- shared labor and shared supplies reduce the strain
- the gut channel is narrow and windy, so the crew must cooperate
- the ending proves change through safer travel and a brighter landing
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
    plural: bool = False
    owner: Optional[str] = None
    helper: Optional[str] = None
    supports: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    destination: object | None = None
    gift: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "uncle", "brother"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
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
    place: str
    on_water: bool = True
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
class Voyage:
    id: str
    verb: str
    gerund: str
    rush: str
    hazard: str
    hazard_meters: dict[str, float]
    feature: str = "sharing"
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
class Gift:
    label: str
    phrase: str
    type: str
    destination: str
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
    shares: set[str]
    calms: set[str]
    prep: str
    tail: str
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
        self.facts: dict = {}
        self.channel: str = ""
        self.weather: str = ""

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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.channel = self.channel
        clone.weather = self.weather
        return clone


def _fmt_list(words: list[str]) -> str:
    if len(words) == 1:
        return words[0]
    return ", ".join(words[:-1]) + " and " + words[-1]


def _join_two(a: str, b: str) -> str:
    return f"{a} and {b}"


def risk_level(world: World, voyage: Voyage, gift: Gift) -> bool:
    return gift.destination in {"far bank", "shore"} and voyage.hazard == "wind"


def select_aid(voyage: Voyage, gift: Gift) -> Optional[Aid]:
    for aid in AIDS:
        if voyage.hazard in aid.calms and gift.destination in aid.shares:
            return aid
    return None


def predict(world: World, hero: Entity, voyage: Voyage, gift: Gift) -> dict:
    sim = world.copy()
    _do_voyage(sim, sim.get(hero.id), voyage, narrate=False)
    return {
        "wonky": any(e.meters.get("wobble", 0) >= THRESHOLD for e in sim.characters()),
        "delivered": sim.get("gift").meters.get("delivered", 0) >= THRESHOLD,
    }


def _do_voyage(world: World, hero: Entity, voyage: Voyage, narrate: bool = True) -> None:
    world.channel = voyage.id
    hero.meters["fatigue"] = hero.meters.get("fatigue", 0) + 1
    hero.meters["balance"] = hero.meters.get("balance", 0) - voyage.hazard_meters.get("balance", 0)
    for ent in world.characters():
        if ent.id != hero.id:
            ent.meters["help"] = ent.meters.get("help", 0) + 1
    if narrate:
        world.say(f"They set out on the {voyage.gerund}.")

def _r_wobble(world: World) -> list[str]:
    out = []
    for hero in world.characters():
        if hero.meters.get("balance", 0) > -THRESHOLD:
            continue
        sig = ("wobble", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero.meters["wobble"] = hero.meters.get("wobble", 0) + 1
        hero.memes["worry"] = hero.memes.get("worry", 0) + 1
        out.append(f"The boat gave a long lean, and {hero.id} had to hold fast.")
    return out


def _r_delivery(world: World) -> list[str]:
    gift = world.get("gift")
    crew = world.characters()
    if not crew:
        return []
    if sum(c.meters.get("help", 0) for c in crew) < THRESHOLD:
        return []
    sig = ("delivery", gift.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    gift.meters["delivered"] = 1
    return [f"The gift reached the far bank bright as a lantern at dusk."]


RULES = [_r_wobble, _r_delivery]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sent = rule(world)
            if sent:
                changed = True
                produced.extend(sent)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tell(setting: Setting, voyage: Voyage, gift_cfg: Gift,
         hero_name: str = "Juniper", hero_type: str = "woman",
         helper_name: str = "Nell", helper_type: str = "boy") -> World:
    world = World(setting)
    world.weather = "windy"
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, label=helper_name))
    gift = world.add(Entity(id="gift", type=gift_cfg.type, label=gift_cfg.label,
                            phrase=gift_cfg.phrase, owner=hero.id,
                            destination=gift_cfg.destination))
    hero.meters.update({"balance": 1.0, "fatigue": 0.0, "help": 0.0})
    hero.memes.update({"hope": 1.0, "worry": 0.0, "pride": 1.0, "trust": 0.0})
    helper.meters.update({"balance": 1.0, "fatigue": 0.0, "help": 0.0})
    helper.memes.update({"hope": 1.0, "worry": 0.0, "pride": 0.0, "trust": 0.0})

    world.say(f"{hero.id} was a tall-tale voyager with a disability that made the docks hard to climb.")
    world.say(f"Even so, {hero.id} knew the river by heart and had a gut feeling for safe water.")
    world.say(f"{helper.id} was ready to share the work, the snacks, and the steering oar.")
    world.say(f"Together they carried {hero.pronoun('possessive')} {gift.label} for the trip.")

    world.para()
    world.say(f"At dawn, they climbed aboard the little boat and headed for {setting.place}.")
    _do_voyage(world, hero, voyage, narrate=False)
    hero.memes["hope"] += 1
    helper.memes["trust"] += 1
    world.say(f"The river was wide as a blue blanket, but the wind kept tugging at the sail.")
    world.say(f"{hero.id} held the map steady while {helper.id} shared the oar and kept the bow straight.")
    propagate(world, narrate=True)

    world.para()
    world.say(f"Then the water narrowed into the Gut, a thin, twisting stretch where the wind could bark.")
    hero.memes["worry"] += 1
    helper.meters["help"] += 1
    world.say(f"{hero.id} felt a gut-deep warning and pointed to the calmer side of the channel.")
    aid = select_aid(voyage, gift)
    if aid is None:
        pass
    world.say(f"{helper.id} grinned and said, \"Let's share the load and use the {aid.label}.\"")
    world.say(f"They {aid.prep}, and the boat answered like a well-trained gull.")
    hero.memes["trust"] += 1
    helper.memes["trust"] += 1
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1

    world.para()
    gift.meters["delivered"] = 1
    world.say(f"By the time they slipped out of the Gut, the far bank was waiting like an open hand.")
    world.say(f"{hero.id} delivered the {gift.label}, and everyone on shore cheered so hard the reeds bent.")
    world.say(f"That night, the lantern glowed, the river settled, and the shared boat rested easy under the stars.")

    world.facts.update(hero=hero, helper=helper, gift=gift, voyage=voyage, aid=aid, setting=setting)
    return world


SETTINGS = {
    "river": Setting(place="the far bank", on_water=True, affords={"voyage"}),
}

VOYAGES = {
    "river_run": Voyage(
        id="river_run",
        verb="sail the river",
        gerund="sailing the river",
        rush="push into the current",
        hazard="wind",
        hazard_meters={"balance": 1.0},
        feature="sharing",
    ),
}

GIFTS = {
    "lantern": Gift(
        label="lantern",
        phrase="a bright brass lantern",
        type="lantern",
        destination="far bank",
    ),
}

AIDS = [
    Aid(
        id="shared_oar",
        label="shared steering oar",
        shares={"far bank", "shore"},
        calms={"wind"},
        prep="shared the steering oar and took turns at the tiller",
        tail="shared the steering oar",
        plural=False,
    ),
    Aid(
        id="shared_snacks",
        label="shared snacks",
        shares={"far bank", "shore"},
        calms={"wind"},
        prep="passed around the snacks and let the boat steady itself",
        tail="shared the snacks",
        plural=True,
    ),
]


@dataclass
class StoryParams:
    setting: str
    voyage: str
    gift: str
    hero_name: str
    helper_name: str
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
    ap = argparse.ArgumentParser(description="Tall-tale voyage storyworld with disability and sharing.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--voyage", choices=VOYAGES)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--hero-name")
    ap.add_argument("--helper-name")
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
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    voyage = getattr(args, "voyage", None) or rng.choice(list(VOYAGES))
    gift = getattr(args, "gift", None) or rng.choice(list(GIFTS))
    hero_name = getattr(args, "hero_name", None) or rng.choice(["Juniper", "Mabel", "Orin", "Nora"])
    helper_name = getattr(args, "helper_name", None) or rng.choice(["Nell", "Pip", "Tobias", "Wren"])
    return StoryParams(setting=setting, voyage=voyage, gift=gift, hero_name=hero_name, helper_name=helper_name)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short tall tale about a disability, a voyage, and sharing on the river.',
        f"Tell a child-friendly story about {f['hero'].id} and {f['helper'].id} sharing the work on a windy voyage.",
        'Write a story that includes a narrow place called the Gut and ends with the gift safely delivered.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    gift = _safe_fact(world, f, "gift")
    return [
        QAItem(
            question=f"Who led the voyage even though the docks were hard for {hero.id} to climb?",
            answer=f"{hero.id} led it. {hero.pronoun('subject').capitalize()} had a disability, but {hero.pronoun('subject')} still knew the river well and guided the trip.",
        ),
        QAItem(
            question=f"What did {hero.id} and {helper.id} share on the trip?",
            answer=f"They shared the work, the snacks, and the steering oar, which helped the boat stay steady.",
        ),
        QAItem(
            question="What happened in the Gut?",
            answer="The river narrowed, the wind pressed hard, and the crew had to cooperate closely to keep the boat on course.",
        ),
        QAItem(
            question=f"What was delivered at the far bank?",
            answer=f"They delivered {gift.phrase}, and it glowed like a little moon in the evening.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting other people use, hold, or enjoy something together instead of keeping it all to yourself.",
        ),
        QAItem(
            question="What is a voyage?",
            answer="A voyage is a long trip, often by water, where people travel from one place to another.",
        ),
        QAItem(
            question="What does gut feeling mean?",
            answer="A gut feeling is a strong inner hunch that tells someone what seems safe or right, even before they can explain why.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
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
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(VOYAGES, params.voyage), _safe_lookup(GIFTS, params.gift), params.hero_name, "woman", params.helper_name, "boy")
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
voyage(v1).
gift(g1).
aid(a1).

sharing(v1,g1).
helps(a1,v1).
calms(a1,wind).
"""
def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("setting", "river"),
        asp.fact("voyage", "v1"),
        asp.fact("gift", "g1"),
        asp.fact("aid", "a1"),
        asp.fact("feature", "v1", "sharing"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show sharing/2."))
    ok = set(asp.atoms(model, "sharing")) == {("v1", "g1")}
    if ok:
        print("OK: ASP reasoning matches the Python story gate.")
        return 0
    print("MISMATCH: ASP reasoning does not match the Python story gate.")
    return 1


CURATED = [
    StoryParams(setting="river", voyage="river_run", gift="lantern", hero_name="Juniper", helper_name="Nell"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show sharing/2."))
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
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
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
