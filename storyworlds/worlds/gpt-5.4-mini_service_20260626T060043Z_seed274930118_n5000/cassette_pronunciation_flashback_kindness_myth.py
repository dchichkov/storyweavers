#!/usr/bin/env python3
"""
storyworlds/worlds/cassette_pronunciation_flashback_kindness_myth.py
====================================================================

A small myth-like story world about a child, a cassette, a pronunciation
lesson, a flashback, and a kindness-based resolution.

Seed premise:
- A child finds an old cassette that holds the right pronunciation of a name.
- They want to hear it at once, but the tape is fragile and can tangle.
- A kind elder remembers a past act of care and turns that memory into a
  gentler way to proceed.

The story stays grounded in simulated state:
- physical meters track cassette damage, dust, and repair effort
- emotional memes track longing, worry, tenderness, and relief
- a flashback is triggered by a shared memory of kindness
- the ending image proves the cassette survived and the pronunciation was learned
"""

from __future__ import annotations

import argparse
import dataclasses
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
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    elder: object | None = None
    hero: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "aunt"}
        male = {"boy", "father", "dad", "man", "grandfather", "uncle"}
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
    indoor: bool
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
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    risk: str
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
    fragile: bool = True
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})
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
class Gear:
    id: str
    label: str
    prep: str
    tail: str
    guards: set[str] = field(default_factory=set)
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
        self.fired: set[str] = set()
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
        clone.entities = dataclasses.deepcopy(self.entities) if hasattr(dataclasses, "deepcopy") else __import__("copy").deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _m(entity: Entity, key: str, amount: float = 1.0) -> float:
    entity.meters[key] = entity.meters.get(key, 0.0) + amount
    return entity.meters[key]


def _e(entity: Entity, key: str, amount: float = 1.0) -> float:
    entity.memes[key] = entity.memes.get(key, 0.0) + amount
    return entity.memes[key]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for actor in [e for e in world.entities.values() if e.kind == "character"]:
            tape = world.entities.get("cassette")
            if not tape:
                continue
            if actor.memes.get("rush", 0.0) >= THRESHOLD and tape.meters.get("dust", 0.0) >= THRESHOLD:
                sig = f"tangle:{actor.id}"
                if sig not in world.fired:
                    world.fired.add(sig)
                    tape.meters["tangle"] = tape.meters.get("tangle", 0.0) + 1
                    actor.memes["worry"] = actor.memes.get("worry", 0.0) + 1
                    out.append("The tape shivered with a tiny tangle, and worry rose in the room.")
                    changed = True
            if world.facts.get("kindness_recalled") and actor.memes.get("worry", 0.0) >= THRESHOLD:
                sig = f"soften:{actor.id}"
                if sig not in world.fired:
                    world.fired.add(sig)
                    actor.memes["worry"] = max(0.0, actor.memes.get("worry", 0.0) - 1)
                    actor.memes["tenderness"] = actor.memes.get("tenderness", 0.0) + 1
                    out.append("The remembered kindness softened the fear like warm light.")
                    changed = True
    if narrate:
        for line in out:
            world.say(line)
    return out


def predict_damage(world: World, actor: Entity, activity: Activity, tape_id: str) -> dict:
    sim = world.copy()
    tape = sim.get(tape_id)
    _e(actor, "rush", 1.0)
    tape.meters["dust"] = tape.meters.get("dust", 0.0) + 1
    tangle = tape.meters.get("tangle", 0.0) + 1 if actor.memes.get("rush", 0.0) >= THRESHOLD else tape.meters.get("tangle", 0.0)
    return {"tangled": tangle >= THRESHOLD, "lost_pronunciation": tangle >= THRESHOLD}


def choose_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    if activity.id == "listen" and prize.fragile:
        return GEAR["soft_cloth"]
    return None


def setting_line(setting: Setting) -> str:
    return {
        "archive": "The archive was cool and still, with old shelves waiting like patient mountains.",
        "study": "The study was quiet, and the lamp made a small gold circle on the table.",
        "attic": "The attic held dust, beams, and old boxes with sleepy corners.",
        "temple_room": "The temple room smelled of wood and cedar, and the air seemed to listen.",
    }[setting.place]


def introduce(world: World, hero: Entity, elder: Entity, prize: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} who loved old sounds and the right way to say names."
    )
    world.say(
        f"One day, {hero.id} found {hero.pronoun('possessive')} {prize.label}, and inside it waited the true pronunciation of a sacred word."
    )
    world.say(
        f"{elder.id} stayed near, because {elder.pronoun()} knew that some lessons had to be handled gently."
    )


def longing(world: World, hero: Entity, activity: Activity) -> None:
    _e(world.get("hero"), "longing", 1.0)
    world.say(
        f"{hero.id} wanted to {activity.verb} at once, because {activity.keyword} felt important, almost like a key."
    )


def warn(world: World, elder: Entity, hero: Entity, prize: Prize, activity: Activity) -> bool:
    pred = predict_damage(world, hero, activity, prize.type)
    if not pred["tangled"]:
        return False
    _e(elder, "worry", 1.0)
    world.facts["predicted_loss"] = True
    world.say(
        f'"If we rush, the {prize.label} may tangle," {elder.id} said. "Then the pronunciation could be lost."'
    )
    return True


def flashback(world: World, elder: Entity) -> None:
    world.facts["kindness_recalled"] = True
    _e(elder, "memory", 1.0)
    world.say(
        f"{elder.id} looked at the old cassette and remembered a kinder day."
    )
    world.say(
        f"In that memory, someone had once paused to teach the same word slowly, smiling each time the child tried again."
    )
    world.say(
        f"That patience had not only fixed the sound; it had made the child brave."
    )


def offer_kindness(world: World, elder: Entity, hero: Entity, gear: Gear, activity: Activity) -> None:
    _e(hero, "hope", 1.0)
    world.say(
        f'{elder.id} picked up {gear.label} and said, "{gear.prep}."'
    )
    world.say(
        f'"We will take care of the {activity.keyword}, and the word will stay clear."'
    )


def accept(world: World, hero: Entity, elder: Entity, prize: Prize, gear: Gear, activity: Activity) -> None:
    hero.memes["worry"] = 0.0
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["kindness"] = hero.memes.get("kindness", 0.0) + 1
    world.say(
        f"{hero.id} nodded and held the {prize.label} carefully while {elder.id} placed it on the soft cloth."
    )
    world.say(
        f"They listened together, repeated the pronunciation, and let the old voice travel from the cassette into the room."
    )
    world.say(
        f"At the end, {hero.id} could say the name correctly, and {prize.label} stayed safe, bright, and ready for another day."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, hero_type: str, elder_name: str, elder_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    elder = world.add(Entity(id=elder_name, kind="character", type=elder_type))
    prize = world.add(Entity(id="cassette", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id))
    world.facts.update(hero=hero, elder=elder, prize=prize, activity=activity, setting=setting)

    world.say(setting_line(setting))
    introduce(world, hero, elder, prize)
    world.para()
    longing(world, hero, activity)
    warn(world, elder, hero, prize, activity)
    flashback(world, elder)
    world.para()
    gear = choose_gear(activity, prize)
    if gear:
        offer_kindness(world, elder, hero, gear, activity)
        accept(world, hero, elder, prize, gear, activity)
    return world


SETTINGS = {
    "archive": Setting(place="archive", indoor=True, affords={"listen"}),
    "study": Setting(place="study", indoor=True, affords={"listen"}),
    "attic": Setting(place="attic", indoor=True, affords={"listen"}),
    "temple_room": Setting(place="temple_room", indoor=True, affords={"listen"}),
}

ACTIVITIES = {
    "listen": Activity(
        id="listen",
        verb="play the cassette",
        gerund="playing the cassette",
        rush="rush to press play",
        mess="dust",
        soil="dusty and tangled",
        risk="tangle",
        keyword="pronunciation",
        tags={"cassette", "pronunciation", "kindness", "flashback", "myth"},
    )
}

PRIZES = {
    "cassette": Prize(
        label="cassette",
        phrase="an old cassette with the right pronunciation inside",
        type="cassette",
    )
}

GEAR = {
    "soft_cloth": Gear(
        id="soft_cloth",
        label="a soft cloth",
        prep="Let's clean the cassette first",
        tail="They used the cloth and the tape turned smoothly",
        guards={"dust"},
    )
}

HERO_NAMES = ["Nia", "Milo", "Ari", "Suri", "Toma", "Lina"]
ELDER_NAMES = ["Grandmother Iri", "Old Father Kato", "Aunt Sena", "Keeper Vara"]
TRAITS = ["careful", "curious", "brave", "gentle"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    hero_name: str
    hero_type: str
    elder_name: str
    elder_type: str
    trait: str = "curious"
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
    return [(p, "listen", "cassette") for p in SETTINGS]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return "(No story: this world only tells the cassette pronunciation tale.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "activity", None) and getattr(args, "activity", None) != "listen":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "prize", None) and getattr(args, "prize", None) != "cassette":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    places = list(SETTINGS)
    place = getattr(args, "place", None) or rng.choice(places)
    hero_type = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    hero_name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    elder_name = getattr(args, "elder", None) or rng.choice(ELDER_NAMES)
    elder_type = getattr(args, "elder_type", None) or rng.choice(["grandmother", "grandfather", "aunt"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place,
        activity="listen",
        prize="cassette",
        hero_name=hero_name,
        hero_type=hero_type,
        elder_name=elder_name,
        elder_type=elder_type,
        trait=trait,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a myth-like story for a small child about a cassette that holds the true pronunciation of a sacred name.',
        f"Tell a gentle story where {f['hero'].id} wants to play the cassette at once, but {f['elder'].id} worries the pronunciation may be lost if the tape tangles.",
        "Write a short myth-style tale that includes a flashback, a kindness, and a safe way to hear an old cassette.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, elder, prize, act = f["hero"], f["elder"], f["prize"], f["activity"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do with the {prize.label}?",
            answer=f"{hero.id} wanted to {act.verb} so {hero.id} could hear the right pronunciation.",
        ),
        QAItem(
            question=f"Why did {elder.id} warn {hero.id} not to rush?",
            answer=f"{elder.id} warned them because rushing could tangle the cassette and spoil the pronunciation lesson.",
        ),
        QAItem(
            question="What did the flashback remind the elder of?",
            answer="The flashback reminded the elder of a kinder day when someone had patiently taught the same word slowly.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id} and the cassette?",
            answer=f"They cleaned the cassette, listened carefully, and {hero.id} learned the pronunciation while the tape stayed safe.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cassette?",
            answer="A cassette is a small plastic tape container that can hold recorded sound.",
        ),
        QAItem(
            question="Why does careful pronunciation matter for some names?",
            answer="Careful pronunciation matters because some names are special, and saying them clearly shows respect.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a part of a story that shows something that happened earlier.",
        ),
        QAItem(
            question="What does kindness do in a hard moment?",
            answer="Kindness can make fear smaller and help people choose a gentle, wise way forward.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
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
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="archive", activity="listen", prize="cassette", hero_name="Nia", hero_type="girl", elder_name="Grandmother Iri", elder_type="grandmother"),
    StoryParams(place="study", activity="listen", prize="cassette", hero_name="Milo", hero_type="boy", elder_name="Old Father Kato", elder_type="grandfather"),
    StoryParams(place="temple_room", activity="listen", prize="cassette", hero_name="Suri", hero_type="girl", elder_name="Aunt Sena", elder_type="aunt"),
]


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
        lines.append(asp.fact("affords", p, "listen"))
    lines.append(asp.fact("activity", "listen"))
    lines.append(asp.fact("mess_of", "listen", "dust"))
    lines.append(asp.fact("risk", "listen", "tangle"))
    lines.append(asp.fact("prize", "cassette"))
    lines.append(asp.fact("fragile", "cassette"))
    lines.append(asp.fact("gear", "soft_cloth"))
    lines.append(asp.fact("guards", "soft_cloth", "dust"))
    lines.append(asp.fact("fix", "soft_cloth"))
    lines.append(asp.fact("requires", "listen", "cassette"))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(P) :- place(P), affords(P, listen).
need_care(listen, cassette).
has_fix(listen, cassette) :- gear(soft_cloth), guards(soft_cloth, dust).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = set((p,) for p, _, _ in valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and python gate.")
    print("python:", sorted(python_set))
    print("clingo:", sorted(clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A myth-like cassette and pronunciation story world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--elder")
    ap.add_argument("--elder-type", choices=["grandmother", "grandfather", "aunt"])
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


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(ACTIVITIES, params.activity),
        _safe_lookup(PRIZES, params.prize),
        params.hero_name,
        params.hero_type,
        params.elder_name,
        params.elder_type,
    )
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
        print(asp_program("#show valid_story/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    elif getattr(args, "asp", None):
        print("Compatible story places:")
        for (place,) in asp_valid_combos():
            print(place)
        return
    else:
        samples = []
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
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
            header = f"### {p.hero_name}: {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "place", None) and getattr(args, "place", None) not in SETTINGS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    hero_type = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    hero_name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    elder_name = getattr(args, "elder", None) or rng.choice(ELDER_NAMES)
    elder_type = getattr(args, "elder_type", None) or rng.choice(["grandmother", "grandfather", "aunt"])
    return StoryParams(
        place=place,
        activity="listen",
        prize="cassette",
        hero_name=hero_name,
        hero_type=hero_type,
        elder_name=elder_name,
        elder_type=elder_type,
        trait=rng.choice(TRAITS),
    )


if __name__ == "__main__":
    main()
