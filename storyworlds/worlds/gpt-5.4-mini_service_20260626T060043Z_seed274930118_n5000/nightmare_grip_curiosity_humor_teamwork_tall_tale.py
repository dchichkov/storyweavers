#!/usr/bin/env python3
"""
storyworlds/worlds/nightmare_grip_curiosity_humor_teamwork_tall_tale.py
========================================================================

A small tall-tale storyworld about a midnight scare, a stubborn grip, and the
way curiosity, humor, and teamwork can turn a nightmare into a story worth
telling.

The world is built from a short seed tale:
- A child wakes from a nightmare and grips a blanket tight.
- Something noisy stirs outside in the dark.
- Curiosity pulls the child toward the mystery.
- Humor keeps everyone brave enough to keep going.
- Teamwork solves the problem and proves the scare was smaller than the story.

The narration is deliberately tall-tale flavored: the wind is oversized, the
dark feels huge, and ordinary helpers act a little legendary.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    lantern: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
    night_sounds: str
    open_sky: bool = True
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
class Challenge:
    id: str
    setup: str
    mystery: str
    noise: str
    fear_reason: str
    twist: str
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
class Tool:
    id: str
    label: str
    phrase: str
    use: str
    helps: set[str]
    covers: set[str] = field(default_factory=set)
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def _r_fear(world: World) -> list[str]:
    out: list[str] = []
    hero = world.facts.get("hero")
    if not hero:
        return out
    if hero.memes.get("fear", 0) >= THRESHOLD and ("fear", hero.id) not in world.fired:
        world.fired.add(("fear", hero.id))
        out.append(f"The fear sat on the room like a suitcase full of thunder.")
    return out


def _r_settle_noise(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("noise_made_sense") and ("noise",) not in world.fired:
        world.fired.add(("noise",))
        out.append("The mystery had an ordinary shape after all.")
    return out


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    team = world.facts.get("team")
    if not team:
        return out
    if team.memes.get("teamwork", 0) >= THRESHOLD and ("teamwork", team.id) not in world.fired:
        world.fired.add(("teamwork", team.id))
        out.append("The helpers moved like they had one big brave idea between them.")
    return out


CAUSAL_RULES = [
    _r_fear,
    _r_settle_noise,
    _r_teamwork,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def setting_detail(setting: Setting) -> str:
    return f"{setting.place} lay under a wide night sky, with {setting.night_sounds} in the dark."


def challenge_tone(ch: Challenge) -> str:
    return {
        "barn": "The barn was so big it could have hidden a county fair in one sleeve.",
        "bridge": "The bridge creaked like an old fiddle learning a new tune.",
        "prairie": "The prairie stretched out like a dark quilt with a silver stitch.",
        "river": "The river glimmered and muttered like it knew every secret in the valley.",
    }.get(ch.id, "The night felt extra large, the way tall tales always do.")


def introduce(world: World, hero: Entity, helper: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} with a big imagination and an even bigger bedtime."
    )
    world.say(
        f"{hero.id} and {helper.id} lived where stories grew tall, and every creak in the night could become a giant."
    )


def nightmare_start(world: World, hero: Entity, ch: Challenge) -> None:
    hero.memes["fear"] += 1
    hero.meters["grip"] += 1
    world.say(
        f"One night, {hero.id} woke from a nightmare about {ch.fear_reason}."
    )
    world.say(
        f"Startled, {hero.id} tightened a grip on the blanket so hard it might have wrinkled the moon."
    )


def curiosity_pulls(world: World, hero: Entity, ch: Challenge) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"Then a funny little {ch.noise} drifted in from outside, and curiosity tugged harder than sleep."
    )
    world.say(
        f"{hero.id} peeked toward the window and wanted to know what could make a noise that lopsided."
    )


def humor_helps(world: World, hero: Entity, helper: Entity) -> None:
    hero.memes["humor"] += 1
    helper.memes["humor"] += 1
    world.say(
        f"{helper.id} made a joke so dry it could have cracked a horseshoe."
    )
    world.say(
        f"{hero.id} giggled, and the nightmare stopped looking quite so enormous."
    )


def teamwork_plan(world: World, hero: Entity, helper: Entity, tool: Tool, ch: Challenge) -> None:
    hero.memes["teamwork"] += 1
    helper.memes["teamwork"] += 1
    world.say(
        f"The two of them decided to use {tool.phrase} and go see the mystery together."
    )
    world.say(
        f"{helper.id} held the light, and {hero.id} held {tool.use}, because brave plans are easier with two sets of hands."
    )


def reveal_twist(world: World, hero: Entity, helper: Entity, ch: Challenge, tool: Tool) -> None:
    world.facts["noise_made_sense"] = True
    world.say(
        f"They followed the sound to the {ch.id}, where the answer turned out to be {ch.twist}."
    )
    world.say(
        f"The whole scare had been big as a thunderhead, but the truth fit neatly in a pocket."
    )


def resolution(world: World, hero: Entity, helper: Entity, ch: Challenge) -> None:
    hero.memes["fear"] = 0
    hero.memes["curiosity"] += 1
    helper.memes["humor"] += 1
    world.say(
        f"{hero.id} laughed, {helper.id} laughed, and the dark lost its fancy disguise."
    )
    world.say(
        f"By the time they returned inside, {hero.id} still had a grip on the blanket, but not on the fear."
    )


def tell(setting: Setting, challenge: Challenge, tool: Tool, hero_name: str = "Mabel",
         hero_type: str = "girl", helper_name: str = "Uncle Jed", helper_type: str = "man") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label="the child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, label="the helper"))
    lantern = world.add(Entity(id="lantern", type="lantern", label=tool.label, phrase=tool.phrase))
    world.facts.update(hero=hero, helper=helper, lantern=lantern, challenge=challenge, tool=tool)

    introduce(world, hero, helper)
    world.para()
    world.say(setting_detail(setting))
    world.say(challenge_tone(challenge))
    nightmare_start(world, hero, challenge)
    curiosity_pulls(world, hero, challenge)
    humor_helps(world, hero, helper)
    world.para()
    teamwork_plan(world, hero, helper, tool, challenge)
    propagate(world, narrate=True)
    reveal_twist(world, hero, helper, challenge, tool)
    resolution(world, hero, helper, challenge)
    return world


SETTINGS = {
    "prairie_home": Setting(
        place="the prairie homestead",
        night_sounds="the wind singing through the fence rails",
        open_sky=True,
        affords={"barn", "prairie"},
    ),
    "river_town": Setting(
        place="the river town",
        night_sounds="the water tapping the pilings like tiny knuckles",
        open_sky=True,
        affords={"bridge", "river"},
    ),
    "canyon_ranch": Setting(
        place="the canyon ranch",
        night_sounds="the coyotes yodeling at the moon",
        open_sky=True,
        affords={"barn", "bridge", "prairie"},
    ),
}

CHALLENGES = {
    "barn": Challenge(
        id="barn",
        setup="a lantern at the barn door",
        mystery="a thumping sound that could have belonged to a bear with boots",
        noise="thump-clang",
        fear_reason="a barn door that groaned like a giant was trying to whisper",
        twist="a calf nudging an old bucket and ringing it like a dinner bell",
        keyword="barn",
        tags={"nightmare", "barn", "animal"},
    ),
    "bridge": Challenge(
        id="bridge",
        setup="the rope bridge over the wash",
        mystery="a wobble that made the boards bounce like a fiddle string",
        noise="creak-creak",
        fear_reason="the bridge swaying in the wind as if it had a mind of its own",
        twist="a possum carrying a tin cup that kept bumping the rail",
        keyword="bridge",
        tags={"nightmare", "bridge", "noise"},
    ),
    "prairie": Challenge(
        id="prairie",
        setup="the moonlit grass beyond the porch",
        mystery="a flicker in the weeds that looked almost like a ghost lantern",
        noise="rustle-rattle",
        fear_reason="shadows sliding across the prairie like a thousand sneaky hats",
        twist="a family of fireflies dancing around a dropped jam jar",
        keyword="prairie",
        tags={"nightmare", "prairie", "light"},
    ),
}

TOOLS = {
    "lantern": Tool(
        id="lantern",
        label="a lantern",
        phrase="the lantern",
        use="the lantern",
        helps={"light", "courage"},
    ),
    "rope": Tool(
        id="rope",
        label="a rope",
        phrase="the rope",
        use="the rope",
        helps={"bridge", "steady"},
    ),
    "bucket": Tool(
        id="bucket",
        label="a bucket",
        phrase="the bucket",
        use="the bucket",
        helps={"fetch", "contain"},
    ),
}

GIRL_NAMES = ["Mabel", "Nell", "Ruby", "Josie", "Annie", "Clara"]
BOY_NAMES = ["Hank", "Toby", "Will", "Otis", "Ezra", "Cal"]
HELPER_NAMES = ["Uncle Jed", "Aunt Bea", "Grandpa Gus", "Miss Ada"]

TRAITS = ["curious", "funny", "brave", "sly", "kind"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for ch in setting.affords:
            if ch in CHALLENGES:
                for tid in TOOLS:
                    combos.append((sid, ch, tid))
    return combos


@dataclass
class StoryParams:
    place: str
    challenge: str
    tool: str
    name: str
    gender: str
    helper: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    challenge = _safe_fact(world, f, "challenge")
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    return [
        f"Write a tall-tale bedtime story where {hero.id} wakes from a nightmare and keeps a grip on {tool.label}.",
        f"Tell a child-friendly story about {hero.id}, curiosity, humor, and teamwork at {world.setting.place}.",
        f"Write a funny, windy midnight adventure involving {challenge.noise} and a brave helper with {tool.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    challenge = _safe_fact(world, f, "challenge")
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    place = _safe_fact(world, f, "setting").place
    return [
        QAItem(
            question=f"What woke {hero.id} up at {place}?",
            answer=f"{hero.id} woke up from a nightmare about {challenge.fear_reason}, and then heard {challenge.noise} outside.",
        ),
        QAItem(
            question=f"Why did {hero.id} keep a grip on {tool.label}?",
            answer=f"{hero.id} held on tight because the nightmare had made the dark feel huge, and {tool.label} gave {hero.id} something steady to reach for.",
        ),
        QAItem(
            question=f"How did {helper.id} help {hero.id} handle the mystery?",
            answer=f"{helper.id} used humor, shared the light, and worked together with {hero.id} until they found out the noise was only {challenge.twist}.",
        ),
        QAItem(
            question=f"What made the ending feel brave instead of scary?",
            answer=f"Curiosity led the way, humor softened the fright, and teamwork solved the mystery, so the nightmare shrank down to a story.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes you want to look, ask, and learn what is going on.",
        ),
        QAItem(
            question="Why can humor help when something feels scary?",
            answer="Humor can help because a joke or a funny moment can make a fright feel smaller and easier to face.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help each other and use their different jobs together to finish something.",
        ),
        QAItem(
            question="What is a nightmare?",
            answer="A nightmare is a bad dream that can make someone wake up feeling scared.",
        ),
        QAItem(
            question="What does it mean to grip something?",
            answer="To grip something means to hold it tightly with your hand.",
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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n[0] if isinstance(n, tuple) and n else n for n in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="prairie_home", challenge="barn", tool="lantern", name="Mabel", gender="girl", helper="Uncle Jed", trait="curious"),
    StoryParams(place="river_town", challenge="bridge", tool="rope", name="Hank", gender="boy", helper="Aunt Bea", trait="funny"),
    StoryParams(place="canyon_ranch", challenge="prairie", tool="bucket", name="Nell", gender="girl", helper="Grandpa Gus", trait="brave"),
]


def explain_rejection(challenge: Challenge, tool: Tool) -> str:
    if challenge.id == "bridge" and tool.id == "bucket":
        return "(No story: a bucket does not help with a bridge mystery. The fix has to match the kind of problem.)"
    return "(No story: this combination does not make a believable tall-tale rescue.)"


ASP_RULES = r"""
valid_story(P,C,T) :- place(P), challenge(C), tool(T),
                      affords(P,C), helpful(T,C).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for c in sorted(s.affords):
            lines.append(asp.fact("affords", pid, c))
    for cid, c in CHALLENGES.items():
        lines.append(asp.fact("challenge", cid))
        for t in sorted(c.tags):
            lines.append(asp.fact("tagged", cid, t))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for h in sorted(t.helps):
            lines.append(asp.fact("helpful", tid, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


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
    ap = argparse.ArgumentParser(description="Tall-tale storyworld: nightmare, grip, curiosity, humor, teamwork.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPER_NAMES)
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
              and (getattr(args, "challenge", None) is None or c[1] == getattr(args, "challenge", None))
              and (getattr(args, "tool", None) is None or c[2] == getattr(args, "tool", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, challenge, tool = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(HELPER_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, challenge=challenge, tool=tool, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(CHALLENGES, params.challenge), _safe_lookup(TOOLS, params.tool),
                 hero_name=params.name, hero_type=params.gender, helper_name=params.helper)
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
    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, challenge, tool) combos:\n")
        for item in triples:
            print("  ", item)
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
            header = f"### {p.name}: {p.challenge} at {p.place} (tool: {p.tool})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
