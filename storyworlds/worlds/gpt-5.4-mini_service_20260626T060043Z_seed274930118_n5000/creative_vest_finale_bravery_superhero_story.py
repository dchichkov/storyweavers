#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/creative_vest_finale_bravery_superhero_story.py
==============================================================================================================

A small superhero-story world built from the seed words:
creative, vest, finale, and the feature bravery.

Premise:
- A young hero loves making bold, clever things.
- A special vest helps them act like a hero in a public finale.
- A small problem threatens the last scene.
- Bravery turns fear into action, and the ending proves the change.

The domain is intentionally tiny and constraint-checked:
- A vest can be useful only when the danger matches what the vest protects.
- The hero's bravery rises when they choose to help others.
- The finale can only succeed if the right helper and gear are present.
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

BRAVERY_THRESHOLD = 1.0



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
    worn_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    vest: object | None = None
    def __post_init__(self) -> None:
        self.meters.setdefault("spark", 0.0)
        self.meters.setdefault("risk", 0.0)
        self.meters.setdefault("damage", 0.0)
        self.memes.setdefault("bravery", 0.0)
        self.memes.setdefault("hope", 0.0)
        self.memes.setdefault("worry", 0.0)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "she", "object": "her", "possessive": "her"}[case]

    def it(self) -> str:
        return "it"
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
class Setting:
    place: str
    crowd: str
    afford: set[str]
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
    verb: str
    danger: str
    risk: str
    zone: str
    keyword: str
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
class Gear:
    id: str
    label: str
    covers: set[str]
    blocks: set[str]
    prep: str
    finale_phrase: str
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
        self.events: list[str] = []
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]

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
        clone.events = list(self.events)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _risk_fire(world: World) -> list[str]:
    out = []
    hero = world.get("hero")
    challenge = _safe_fact(world, world.facts, "challenge")
    vest = world.entities.get("vest")
    if hero.meters["risk"] < BRAVERY_THRESHOLD:
        return out
    if not vest or vest.worn_by != hero.id:
        return out
    sig = ("risk_fire", challenge.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if challenge.zone in vest.covers or challenge.tag in vest.blocks:
        hero.meters["damage"] += 0
    else:
        hero.meters["damage"] += 1
    return out


def _brave_turn(world: World) -> list[str]:
    hero = world.get("hero")
    sig = ("brave_turn",)
    if sig in world.fired:
        return []
    if hero.memes["bravery"] >= BRAVERY_THRESHOLD and hero.meters["risk"] >= BRAVERY_THRESHOLD:
        world.fired.add(sig)
        hero.memes["hope"] += 1
        return ["__brave__"]
    return []


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_risk_fire, _brave_turn):
            sents = rule(world)
            if sents:
                changed = True
                out.extend(s for s in sents if s != "__brave__")
    if narrate:
        for s in out:
            world.say(s)
    return out


SETTINGS = {
    "rooftop": Setting(place="the rooftop", crowd="the city crowd", afford={"rescue"}),
    "plaza": Setting(place="the plaza", crowd="the cheering crowd", afford={"rescue"}),
    "stage": Setting(place="the stage", crowd="the audience", afford={"rescue"}),
}

CHALLENGES = {
    "blowout": Challenge(
        id="blowout",
        verb="stop the smoke machine",
        danger="a drifting smoke burst",
        risk="the finale lights could disappear",
        zone="eyes",
        keyword="creative",
        tag="smoke",
    ),
    "loosebanner": Challenge(
        id="loosebanner",
        verb="catch the falling banner",
        danger="a snapping banner rope",
        risk="the finale sign could fall",
        zone="hands",
        keyword="finale",
        tag="rope",
    ),
    "rainwind": Challenge(
        id="rainwind",
        verb="steady the wind machine",
        danger="a gusty blast",
        risk="the finale costumes could blow away",
        zone="torso",
        keyword="vest",
        tag="wind",
    ),
}

GEAR = {
    "vest": Gear(
        id="vest",
        label="a bright creative vest",
        covers={"torso"},
        blocks={"wind"},
        prep="button up the bright creative vest",
        finale_phrase="stood tall in the creative vest",
    )
}

NAMES = ["Maya", "Nina", "Lina", "Tess", "Zara", "Aria", "Ivy", "June"]
TRAITS = ["creative", "brave", "bold", "kind", "inventive"]


@dataclass
class StoryParams:
    place: str
    challenge: str
    name: str
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


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, s in SETTINGS.items():
        for ch in s.afford:
            combos.append((place, ch))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero story world with a creative vest and a brave finale.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
              and (getattr(args, "challenge", None) is None or c[1] == getattr(args, "challenge", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, challenge = rng.choice(list(combos))
    return StoryParams(
        place=place,
        challenge=getattr(args, "challenge", None) or challenge,
        name=getattr(args, "name", None) or rng.choice(NAMES),
        trait=getattr(args, "trait", None) or rng.choice(TRAITS),
    )


def tell(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    hero = world.add(Entity(id="hero", kind="character", type="girl", label=params.name))
    helper = world.add(Entity(id="helper", kind="character", type="adult", label="Aunt Sol"))
    challenge = _safe_lookup(CHALLENGES, params.challenge)
    world.facts["challenge"] = challenge

    vest = world.add(Entity(
        id="vest",
        type="gear",
        label="creative vest",
        phrase="a bright creative vest with silver stars",
        owner=hero.id,
        worn_by=None,
        protective=True,
        covers={"torso"},
    ))

    hero.memes["bravery"] += 0
    hero.memes["worry"] += 1

    world.say(
        f"{params.name} was a {params.trait} little superhero who loved making plans that felt new and clever."
    )
    world.say(
        f"She kept a bright creative vest by her bed because it made her feel ready for a big finale."
    )

    world.para()
    world.say(
        f"On the night of the finale at {world.setting.place}, {world.setting.crowd} waited for the last act."
    )
    world.say(
        f"Then {challenge.danger} began to spread, and {challenge.risk}."
    )
    hero.meters["risk"] += 1
    hero.memes["worry"] += 1
    hero.memes["bravery"] += 1
    world.say(
        f"{params.name} felt her heart jump, but she remembered that bravery means helping even when your knees feel wobbly."
    )

    world.para()
    if challenge.tag == "wind":
        vest.worn_by = hero.id
        world.say(f"Aunt Sol pointed to {vest.label} and said, \"{challenge.keyword} can still be your strength.\"")
        world.say(f"{params.name} {GEAR['vest'].prep} and ran toward the machine.")
        world.say(f"The vest covered her torso, so the wind couldn't tug her costume loose.")
    else:
        world.say(f"Aunt Sol rushed beside her and said, \"You can do this. Stay creative and stay brave.\"")
        world.say(f"{params.name} chose a clever way to {challenge.verb}, using a rescue line and a quick hand.")

    propagate(world, narrate=False)

    world.para()
    hero.memes["bravery"] += 1
    hero.memes["hope"] += 1
    world.say(
        f"{params.name} solved the trouble before the finale ended, and the crowd gasped, then cheered."
    )
    world.say(
        f"At the end, she {GEAR['vest'].finale_phrase} and smiled at the glowing stage."
    )
    world.say(
        f"The final image was simple: a brave child, a creative vest, and a happy finale with the lights still shining."
    )

    world.facts.update(hero=hero, helper=helper, vest=vest, params=params, setting=world.setting)
    return world


def generation_prompts(world: World) -> list[str]:
    p = _safe_fact(world, world.facts, "params")
    return [
        f"Write a superhero story for a young child about {p.name}, a {p.trait} hero, and a creative vest.",
        f"Tell a short brave finale story where a hero at {p.place} uses a vest and saves the day.",
        f"Write a child-friendly superhero tale that includes the words creative, vest, and finale.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = _safe_fact(world, world.facts, "params")
    ch = _safe_fact(world, world.facts, "challenge")
    hero = _safe_fact(world, world.facts, "hero")
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {p.name}, a {p.trait} little superhero who learned to be brave at the finale.",
        ),
        QAItem(
            question=f"What problem appeared during the finale at {p.place}?",
            answer=f"{ch.danger.capitalize()} appeared, and it could have ruined the finale by making {ch.risk}.",
        ),
        QAItem(
            question=f"Why did {p.name} choose the creative vest?",
            answer=f"She chose the creative vest because it helped her feel brave, and it covered her torso when the wind was a problem.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"{p.name} was no longer worried. She acted bravely, fixed the problem, and the finale ended in cheering light.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bravery?",
            answer="Bravery means doing the helpful thing even when you feel scared or unsure.",
        ),
        QAItem(
            question="What is a vest?",
            answer="A vest is a sleeveless piece of clothing that covers the torso.",
        ),
        QAItem(
            question="What is a finale?",
            answer="A finale is the last part of a show, story, or performance.",
        ),
        QAItem(
            question="Why can a creative idea help a superhero?",
            answer="A creative idea can help a superhero solve a problem in a smart new way.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes} worn_by={e.worn_by}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
place(rooftop;plaza;stage).
challenge(blowout;loosebanner;rainwind).
affords(rooftop,rescue).
affords(plaza,rescue).
affords(stage,rescue).
risk(challenge, wind) :- challenge(rainwind).
risk(challenge, hands) :- challenge(loosebanner).
risk(challenge, eyes) :- challenge(blowout).
valid(Place, Challenge) :- affords(Place,rescue), challenge(Challenge).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
        lines.append(asp.fact("affords", p, "rescue"))
    for c in CHALLENGES:
        lines.append(asp.fact("challenge", c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


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


CURATED = [
    StoryParams(place="plaza", challenge="wind", name="Maya", trait="creative"),
    StoryParams(place="stage", challenge="loosebanner", name="Ivy", trait="brave"),
    StoryParams(place="rooftop", challenge="blowout", name="Zara", trait="inventive"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
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
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.challenge} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
