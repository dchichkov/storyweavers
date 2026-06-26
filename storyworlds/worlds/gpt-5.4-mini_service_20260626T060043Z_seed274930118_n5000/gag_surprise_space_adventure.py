#!/usr/bin/env python3
"""
storyworlds/worlds/gag_surprise_space_adventure.py
==================================================

A small storyworld for a Space Adventure-style tale with a gag surprise.

Premise:
A tiny crew flies a little ship to deliver a surprise birthday token on a moon.
The ship has a silly gag gadget that keeps going off at the wrong moments.

World model:
- typed entities with meters and memes
- physical risks: loose items, floating snacks, noisy gadget, surprise reveal
- emotional beats: excitement, worry, embarrassment, delight

The story stays close to a classical adventure beat:
setup -> problem -> fix -> surprise ending.
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
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    copilot: object | None = None
    crew: object | None = None
    gadget: object | None = None
    token: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {
                "floaty": 0.0,
                "shaky": 0.0,
                "lost": 0.0,
                "busy": 0.0,
            }
        if not self.memes:
            self.memes = {
                "joy": 0.0,
                "worry": 0.0,
                "surprise": 0.0,
                "embarrassment": 0.0,
                "pride": 0.0,
            }

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "captain"}
        male = {"boy", "pilot"}
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
class SpaceSetting:
    place: str
    detail: str
    affordance: str
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
class GagDevice:
    id: str
    label: str
    effect: str
    trigger: str
    fix: str
    help_text: str
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
class SurpriseItem:
    id: str
    label: str
    phrase: str
    reveal: str
    safe: bool = True
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
    def __init__(self, setting: SpaceSetting) -> None:
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
        clone.facts = dict(self.facts)
        return clone


def _narrate(world: World, text: str) -> None:
    world.say(text)


def _gag_fire(world: World, gag: Entity, crew: Entity) -> None:
    sig = ("gag", gag.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    crew.memes["surprise"] += 1
    crew.memes["embarrassment"] += 1
    gag.meters["shaky"] += 1
    _narrate(world, f"Then the silly {gag.label} went off with a loud beep and a tiny puff of sparkly smoke.")


def _float_items(world: World, crew: Entity) -> None:
    for ent in list(world.entities.values()):
        if ent.kind == "thing" and ent.owner == crew.id and ent.meters["floaty"] >= THRESHOLD:
            sig = ("float", ent.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            ent.meters["lost"] += 1
            _narrate(world, f"{crew.pronoun('possessive').capitalize()} {ent.label} drifted up, then bobbed in the air like a slow balloon.")


def _resolve(world: World, crew: Entity, gadget: Entity, prize: Entity) -> None:
    sig = ("resolve", gadget.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    crew.memes["worry"] = 0.0
    crew.memes["joy"] += 1
    crew.memes["pride"] += 1
    gadget.meters["shaky"] = 0.0
    _narrate(world, f"They used the {gadget.label} the right way at last, and the ship steadied as quiet as a sleeping kitten.")
    _narrate(world, f"That made room for the surprise: {prize.reveal}.")


def predict_gag(world: World, crew: Entity, gag: Entity, surprise: SurpriseItem) -> bool:
    sim = world.copy()
    _gag_fire(sim, sim.get(gag.id), sim.get(crew.id))
    return sim.get(crew.id).memes["embarrassment"] >= THRESHOLD and surprise.safe


def tell(world: World, crew_name: str, crew_type: str, gag: GagDevice, prize: SurpriseItem) -> World:
    crew = world.add(Entity(id=crew_name, kind="character", type=crew_type, label=crew_name))
    copilot = world.add(Entity(id="copilot", kind="character", type="pilot", label="the pilot"))
    gadget = world.add(Entity(
        id=gag.id,
        kind="thing",
        type="gadget",
        label=gag.label,
        phrase=gag.effect,
        owner=crew.id,
        caretaker=crew.id,
    ))
    token = world.add(Entity(
        id=prize.id,
        kind="thing",
        type="gift",
        label=prize.label,
        phrase=prize.phrase,
        owner=crew.id,
        caretaker=crew.id,
    ))

    _narrate(world, f"{crew.name if hasattr(crew, 'name') else crew.id} was a little space traveler who loved every bright launch.")
    _narrate(world, f"{crew.id} and the pilot set out toward {world.setting.place}, where {world.setting.detail}.")
    _narrate(world, f"They carried a surprise: {prize.phrase}.")
    _narrate(world, f"The ship also had a funny {gadget.label}, because the crew liked a good gag on long trips.")

    world.para()
    crew.memes["joy"] += 1
    crew.memes["worry"] += 1
    _narrate(world, f"At first, {crew.id} tried to keep the surprise hidden, but the {gadget.label} kept waiting for the wrong moment.")
    if predict_gag(world, crew, gadget, prize):
        _gag_fire(world, gadget, crew)

    crew.meters["floaty"] += 1
    token.meters["floaty"] += 1
    _float_items(world, crew)
    _narrate(world, f"The moon dust was so light that even the ribbon on the gift box tugged upward.")

    world.para()
    _narrate(world, f"{crew.id} took a breath, held the {gadget.label} still, and used the fix it had always promised: {gag.fix}.")
    _resolve(world, crew, gadget, token)
    _narrate(world, f"At the end, the surprise was safe, the gag was quiet, and the little ship glowed over {world.setting.place} like a happy star.")

    world.facts.update(
        crew=crew,
        copilot=copilot,
        gadget=gadget,
        prize=token,
        gag=gag,
        surprise=prize,
    )
    return world


SETTINGS = {
    "moon_base": SpaceSetting(
        place="Moon Base Nine",
        detail="the landing pad had silver dust and one round window that looked like a sleepy eye",
        affordance="spacewalk",
    ),
    "orbital_station": SpaceSetting(
        place="Orbital Station Pebble",
        detail="the hallway curved in a neat circle and the snack hatch blinked blue",
        affordance="delivery",
    ),
    "crater_outpost": SpaceSetting(
        place="Crater Outpost Bluebell",
        detail="the little dome sat beside a crater full of sparkling dust",
        affordance="landing",
    ),
}

GAGS = {
    "bubble_beeper": GagDevice(
        id="bubble_beeper",
        label="bubble beeper",
        effect="a beep that popped out little soap bubbles",
        trigger="someone pressed the red button",
        fix="cover the red button with a hand until the landing was done",
        help_text="It was meant to cheer everyone up, not to startle them.",
    ),
    "whoopee_thruster": GagDevice(
        id="whoopee_thruster",
        label="whoopee thruster",
        effect="a squeaky horn sound from the rear panel",
        trigger="the ship tilted too fast",
        fix="steady the ship and keep the panel from wobbling",
        help_text="It was a harmless joke thruster for silly rides.",
    ),
    "spark_snicker": GagDevice(
        id="spark_snicker",
        label="spark snicker",
        effect="a blink of glitter that made everyone giggle",
        trigger="the power dial slipped",
        fix="turn the dial back and lock it gently",
        help_text="It made a surprise sparkle instead of a serious alarm.",
    ),
}

SURPRISES = {
    "cake": SurpriseItem(
        id="cake",
        label="moon cake",
        phrase="a tiny moon cake with a candle stuck in the top",
        reveal="the candle lit itself when the hatch opened",
    ),
    "flag": SurpriseItem(
        id="flag",
        label="silver flag",
        phrase="a folded silver flag wrapped in blue ribbon",
        reveal="the flag unfurled into a big smiling banner",
    ),
    "robot": SurpriseItem(
        id="robot",
        label="pocket robot",
        phrase="a pocket-sized robot with a bow tie",
        reveal="the pocket robot sat up and sang a beep-beep birthday song",
    ),
}

NAMES = ["Nova", "Milo", "Iris", "Jax", "Luna", "Pip"]
TYPES = ["girl", "boy", "captain", "pilot"]


@dataclass
class StoryParams:
    place: str
    gag: str
    surprise: str
    name: str
    crew_type: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure storyworld with a surprise gag.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--gag", choices=GAGS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--name")
    ap.add_argument("--crew-type", choices=TYPES)
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
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    gag = getattr(args, "gag", None) or rng.choice(list(GAGS))
    surprise = getattr(args, "surprise", None) or rng.choice(list(SURPRISES))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    crew_type = getattr(args, "crew_type", None) or rng.choice(TYPES)
    if place not in SETTINGS or gag not in GAGS or surprise not in SURPRISES:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, gag=gag, surprise=surprise, name=name, crew_type=crew_type)


def generate(params: StoryParams) -> StorySample:
    world = World(_safe_lookup(SETTINGS, params.place))
    tell(world, params.name, params.crew_type, _safe_lookup(GAGS, params.gag), _safe_lookup(SURPRISES, params.surprise))
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
        f'Write a short Space Adventure story with a gag device called "{f["gag"].label}" and a surprise reveal.',
        f"Tell a child-friendly space tale where {f['crew'].id} travels to {world.setting.place} and a funny gadget causes a surprise before the ending.",
        "Write a gentle spaceship story that includes a silly gag, a careful fix, and a happy surprise at the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    crew: Entity = _safe_fact(world, f, "crew")
    gag: GagDevice = _safe_fact(world, f, "gag")
    surprise: SurpriseItem = _safe_fact(world, f, "surprise")
    token: Entity = _safe_fact(world, f, "prize")
    return [
        QAItem(
            question=f"What did {crew.id} carry on the trip to {world.setting.place}?",
            answer=f"{crew.id} carried {token.phrase} for the surprise. The gift stayed with the crew until the ending.",
        ),
        QAItem(
            question=f"What funny thing kept happening on the ship?",
            answer=f"The {gag.label} kept causing {gag.effect}, which made the trip silly before it was fixed.",
        ),
        QAItem(
            question=f"What was the surprise at the end?",
            answer=f"The surprise was {surprise.phrase}, and {surprise.reveal}.",
        ),
        QAItem(
            question=f"How did the crew solve the problem with the gag?",
            answer=f"They used the fix: {gag.fix}. That calmed the ship and let the surprise happen safely.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a moon base?",
            answer="A moon base is a place people or robots use on the moon to live, work, or visit for a while.",
        ),
        QAItem(
            question="What is a gag in a story?",
            answer="A gag is a funny trick or joke that makes the scene playful instead of scary.",
        ),
        QAItem(
            question="Why can space objects float?",
            answer="In space, things can float because gravity feels much weaker than it does on Earth.",
        ),
        QAItem(
            question="What makes a surprise fun?",
            answer="A surprise is fun when it is hidden first and then revealed in a happy way.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== world qa ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        parts = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(parts)}")
    lines.append(f"setting={world.setting.place}")
    return "\n".join(lines)


ASP_RULES = r"""
gag_device(G) :- gag(G).
surprise_item(S) :- surprise(S).
compatible(P, G, S) :- place(P), gag(G), surprise(S).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for g in GAGS:
        lines.append(asp.fact("gag", g))
    for s in SURPRISES:
        lines.append(asp.fact("surprise", s))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    atoms = set(asp.atoms(model, "compatible"))
    py = {(p, g, s) for p in SETTINGS for g in GAGS for s in SURPRISES}
    if atoms == py:
        print(f"OK: clingo gate matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH")
    print("only in clingo:", sorted(atoms - py))
    print("only in python:", sorted(py - atoms))
    return 1


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


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
    StoryParams(place="moon_base", gag="bubble_beeper", surprise="cake", name="Nova", crew_type="girl"),
    StoryParams(place="orbital_station", gag="whoopee_thruster", surprise="robot", name="Milo", crew_type="boy"),
    StoryParams(place="crater_outpost", gag="spark_snicker", surprise="flag", name="Iris", crew_type="captain"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show compatible/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid()
        print(f"{len(combos)} compatible combos")
        for c in combos:
            print(c)
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 and not getattr(args, "all", None) else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
