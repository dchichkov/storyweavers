#!/usr/bin/env python3
"""
Story world: glad twist kindness space adventure.

A small, classical, constraint-checked story domain about a child on a space
trip, a surprising twist, and a kind fix that makes the ending feel glad.

The story is intentionally tiny: one hero, one companion, one odd space problem,
and one helpful turn. The prose is driven by simulated state so the ending
proves what changed.
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
    companion: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    kit: object | None = None
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
    detail: str
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
class Twist:
    id: str
    event: str
    surprise: str
    risk: str
    remedy: str
    keyword: str = "glad"
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
class Kindness:
    id: str
    label: str
    action: str
    effect: str
    covers: set[str] = field(default_factory=set)
    protects: set[str] = field(default_factory=set)
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
        self.space_state: str = "calm"

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
        import copy as _copy

        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.space_state = self.space_state
        w.paragraphs = [[]]
        return w


def _apply_twist(world: World) -> list[str]:
    out: list[str] = []
    for hero in list(world.entities.values()):
        if hero.kind != "character":
            continue
        if hero.meters["drift"] < THRESHOLD:
            continue
        sig = ("twist", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero.memes["worry"] += 1
        hero.memes["surprise"] += 1
        world.space_state = "twisted"
        out.append("The little ship gave a sudden twist.")
    return out


def _apply_kindness(world: World) -> list[str]:
    out: list[str] = []
    for hero in list(world.entities.values()):
        if hero.kind != "character":
            continue
        if hero.memes["kindness"] < THRESHOLD or hero.meters["stuck"] < THRESHOLD:
            continue
        sig = ("kindness_fix", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero.meters["stuck"] = 0
        hero.memes["worry"] = 0
        hero.memes["glad"] += 1
        world.space_state = "steady"
        out.append("Kindness made the problem feel smaller.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_apply_twist, _apply_kindness):
            sent = rule(world)
            if sent:
                changed = True
                produced.extend(sent)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_twist(world: World, hero: Entity) -> bool:
    sim = world.copy()
    sim.get(hero.id).meters["drift"] += 1
    propagate(sim, narrate=False)
    return sim.space_state == "twisted"


def tell(setting: Setting, twist: Twist, kindness: Kindness, hero_name: str,
         hero_type: str, helper_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        label=hero_name.lower(),
        meters={"drift": 0, "stuck": 0},
        memes={"glad": 0, "worry": 0, "surprise": 0, "kindness": 0},
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper_type,
        label="the helper",
        meters={},
        memes={"glad": 0, "kindness": 0},
    ))
    kit = world.add(Entity(
        id="Kit",
        type="tool",
        label=kindness.label,
        phrase=kindness.label,
        owner=hero.id,
    ))

    world.say(
        f"{hero.id} was a little {hero.type} on a space trip, and {hero.pronoun('subject')} felt glad "
        f"to look at the bright stars from {world.setting.place}."
    )
    world.say(
        f"The {world.setting.detail} made {hero.pronoun('object')} smile, because the ship felt like a tiny home."
    )

    world.para()
    world.say(
        f"Then came a {twist.keyword} twist: {twist.event}. {twist.surprise}"
    )
    hero.meters["drift"] += 1
    if predict_twist(world, hero):
        propagate(world, narrate=True)
    hero.meters["stuck"] += 1
    hero.memes["worry"] += 1
    world.say(
        f"{hero.id} tried to keep calm, but {hero.pronoun('possessive')} hands held still and the problem stayed close."
    )

    world.para()
    hero.memes["kindness"] += 1
    helper.memes["kindness"] += 1
    world.say(
        f"Then {helper.label} chose kindness. {kindness.action}. {kindness.effect}"
    )
    world.say(
        f"{hero.id} used the {kit.label} and worked with {helper.label} to fix the {twist.id}."
    )
    propagate(world, narrate=True)
    if hero.meters["stuck"] < THRESHOLD:
        world.say(
            f"At last the ship felt steady again, and {hero.id} was glad to see the stars shine past the window."
        )
        hero.memes["glad"] += 1

    world.facts.update(
        hero=hero,
        helper=helper,
        kit=kit,
        twist=twist,
        kindness=kindness,
        setting=setting,
        resolved=hero.meters["stuck"] < THRESHOLD,
    )
    return world


SETTINGS = {
    "orbital_deck": Setting(
        place="the orbital deck",
        detail="glassy control room with floating lights",
        affords={"twist", "kindness"},
    ),
    "moon_bay": Setting(
        place="the moon bay",
        detail="silver hangar with a round window",
        affords={"twist", "kindness"},
    ),
    "star_room": Setting(
        place="the star room",
        detail="quiet cabin with a sky map on the wall",
        affords={"twist", "kindness"},
    ),
}

TWISTS = {
    "jammed_rope": Twist(
        id="jammed rope",
        event="a rope on the little ship snagged and pulled the lantern sideways",
        surprise="The ship lurched, and one panel stayed twisted open.",
        risk="the ship can wobble and trap the hero's hands",
        remedy="a careful reset",
        tags={"twist", "space"},
    ),
    "spinning_map": Twist(
        id="spinning map",
        event="a star map flipped around and made the route look backwards",
        surprise="The dots spun like tiny fireflies, and the path got confusing.",
        risk="the hero may feel lost",
        remedy="a calm check",
        tags={"twist", "space"},
    ),
    "stuck_button": Twist(
        id="stuck button",
        event="a button on the ship stuck down with a soft click",
        surprise="The lights blinked twice, then waited.",
        risk="the ship may stop moving",
        remedy="a gentle push",
        tags={"twist", "space"},
    ),
}

KINDNESSES = {
    "soft_glove": Kindness(
        id="soft glove",
        label="soft glove",
        action="the helper held out a soft glove and guided the hero's hand slowly",
        effect="That calm help made the twist easier to fix.",
        covers={"hands"},
        protects={"stuck"},
    ),
    "warm_lamp": Kindness(
        id="warm lamp",
        label="warm lamp",
        action="the helper turned on a warm lamp so the buttons were easy to see",
        effect="The bright glow made the next step clear and kind.",
        covers={"hands", "eyes"},
        protects={"stuck", "drift"},
    ),
    "steady_rope": Kindness(
        id="steady rope",
        label="steady rope",
        action="the helper offered a steady rope and stood close by",
        effect="With a patient tug, the little ship stopped wobbling.",
        covers={"hands"},
        protects={"drift"},
    ),
}

NAMES = ["Ari", "Mila", "Noah", "Zoe", "Luna", "Finn", "Ivy", "Theo"]


@dataclass
class StoryParams:
    setting: str
    twist: str
    kindness: str
    name: str
    hero_type: str
    helper_type: str = "adult"
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
    for sid, s in SETTINGS.items():
        for tid in s.affords:
            for kid in s.affords:
                combos.append((sid, tid, kid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure story world with a glad twist and kindness.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--kindness", choices=KINDNESSES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    combos = valid_combos()
    if getattr(args, "setting", None):
        combos = [c for c in combos if c[0] == getattr(args, "setting", None)]
    if getattr(args, "twist", None):
        combos = [c for c in combos if c[1] == getattr(args, "twist", None)]
    if getattr(args, "kindness", None):
        combos = [c for c in combos if c[2] == getattr(args, "kindness", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, twist, kindness = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    hero_type = gender
    return StoryParams(setting=setting, twist=twist, kindness=kindness, name=name, hero_type=hero_type, seed=None)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short space adventure story for a small child that includes the word "{f["twist"].keyword}".',
        f"Tell a gentle story where {f['hero'].id} meets a surprising twist in {f['setting'].place} and kindness helps fix it.",
        f"Write a glad ending space story about a child, a twist, and a kind helper.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, twist, kindness = f["hero"], f["helper"], f["twist"], f["kindness"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a little {hero.type} who goes on a space trip and ends up feeling glad again.",
        ),
        QAItem(
            question=f"What surprising problem happened in {f['setting'].place}?",
            answer=f"A twist happened when {twist.event.lower()}. That made the ship wobble and the hero worry.",
        ),
        QAItem(
            question=f"How did the helper fix the problem?",
            answer=f"{helper.label.capitalize()} chose kindness by helping carefully with {kindness.label}, and that made the ship steady again.",
        ),
        QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt glad at the end because the problem was solved and the stars looked bright and safe again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a space trip?",
            answer="A space trip is a journey beyond Earth, often in a ship, where people can look at stars, moons, and planets.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means helping, sharing, and being gentle so someone else feels safe and cared for.",
        ),
        QAItem(
            question="What is a twist?",
            answer="A twist is a quick turn or sudden change. In a story, a twist can make the problem surprise the characters.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: type={e.type} meters={meters} memes={memes}")
    lines.append(f"space_state={world.space_state}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(S) :- setting_fact(S).
twist(T) :- twist_fact(T).
kindness(K) :- kindness_fact(K).
compatible(S,T,K) :- setting(S), twist(T), kindness(K).
#show compatible/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting_fact", sid))
    for tid in TWISTS:
        lines.append(asp.fact("twist_fact", tid))
    for kid in KINDNESSES:
        lines.append(asp.fact("kindness_fact", kid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH")
    if py - cl:
        print("only in python:", sorted(py - cl))
    if cl - py:
        print("only in clingo:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(TWISTS, params.twist), _safe_lookup(KINDNESSES, params.kindness), params.name, params.hero_type, params.helper_type)
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
    StoryParams(setting="orbital_deck", twist="jammed_rope", kindness="steady_rope", name="Ari", hero_type="boy"),
    StoryParams(setting="moon_bay", twist="spinning_map", kindness="warm_lamp", name="Luna", hero_type="girl"),
    StoryParams(setting="star_room", twist="stuck_button", kindness="soft_glove", name="Mila", hero_type="girl"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show compatible/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        for row in asp_valid_combos():
            print(row)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
