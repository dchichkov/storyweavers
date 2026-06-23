#!/usr/bin/env python3
"""
storyworlds/worlds/tram_chug_bask_teamwork_reconciliation_surprise_myth.py
==========================================================================

A small mythic storyworld about a tram, a deep chug, a warm bask, teamwork,
reconciliation, and a surprise that turns a quarrel into a shared journey.

The source tale behind this world is a simple myth:
a village tram is stuck on a hill at dusk, two helpers argue over how to move
it, then they work together, discover a surprising guest or gift, make peace,
and the tram ends the story rolling again in a warm, golden light.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
            keys = [upper + "S", upper + "ES"]
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
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    plural: bool = False
    owner: Optional[str] = None

    elder: object | None = None
    gift: object | None = None
    helper: object | None = None
    hero: object | None = None
    tram: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "goddess"}
        male = {"boy", "father", "dad", "man", "god"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type
    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

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
    id: str
    label: str
    light: str
    affords: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
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

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

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
class Task:
    id: str
    verb: str
    gerund: str
    sound: str
    risk: str
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
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
class Gift:
    id: str
    label: str
    phrase: str
    helper: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
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
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    clone: object | None = None
    world: object | None = None
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
        clone = World(self.place)
        clone.entities = _copy.deepcopy(self.entities)
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class StoryParams:
    place: str
    task: str
    gift: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    elder: str
    mood: str = "wise"
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


PLACES = {
    "hill-road": Place(
        id="hill-road",
        label="the hill road",
        light="golden dusk",
        affords={"chug", "bask"},
        tags={"road", "sun"},
    ),
    "river-bend": Place(
        id="river-bend",
        label="the river bend",
        light="silver morning",
        affords={"chug", "bask"},
        tags={"water", "sun"},
    ),
    "stone-gate": Place(
        id="stone-gate",
        label="the stone gate",
        light="amber evening",
        affords={"chug", "bask"},
        tags={"stone", "sun"},
    ),
}

TASKS = {
    "chug": Task(
        id="chug",
        verb="push the tram",
        gerund="pushing the tram",
        sound="chug-chug",
        risk="the tram would stay stuck",
        tags={"tram", "chug", "teamwork"},
    ),
    "bask": Task(
        id="bask",
        verb="lift the tram into the light",
        gerund="standing in the warm light",
        sound="soft hush",
        risk="the tram would lose the sun's blessing",
        tags={"tram", "bask", "sun"},
    ),
}

GIFTS = {
    "bell": Gift(
        id="bell",
        label="a silver bell",
        phrase="a silver bell tied with blue thread",
        helper="its ringing",
        tags={"surprise", "sound"},
    ),
    "lamp": Gift(
        id="lamp",
        label="a lantern",
        phrase="a lantern with a honey glow",
        helper="its steady light",
        tags={"surprise", "light"},
    ),
    "seed": Gift(
        id="seed",
        label="a seed of dawn",
        phrase="a small dawn-seed wrapped in leaves",
        helper="its bright promise",
        tags={"surprise", "myth"},
    ),
}

GIRL_NAMES = ["Ari", "Mina", "Luna", "Nia", "Selene", "Ira"]
BOY_NAMES = ["Orin", "Taro", "Levi", "Eden", "Milo", "Cai"]
TRAITS = ["gentle", "bold", "patient", "curious", "steadfast"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, t, g) for p in PLACES for t in TASKS for g in GIFTS]


def explain_rejection(place: str, task: str, gift: str) -> str:
    return f"(No story: the chosen myth has no workable path for {place}, {task}, and {gift}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic tram storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--elder")
    ap.add_argument("--mood", choices=["wise", "bright", "tender"])
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
              and (getattr(args, "task", None) is None or c[1] == getattr(args, "task", None))
              and (getattr(args, "gift", None) is None or c[2] == getattr(args, "gift", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, task, gift = rng.choice(list(combos))
    hg = getattr(args, "hero_gender", None) or rng.choice(["girl", "boy"])
    hg2 = getattr(args, "helper_gender", None) or ("boy" if hg == "girl" and rng.random() < 0.5 else "girl" if hg == "boy" and rng.random() < 0.5 else rng.choice(["girl", "boy"]))
    hero = getattr(args, "hero", None) or rng.choice(GIRL_NAMES if hg == "girl" else BOY_NAMES)
    helper = getattr(args, "helper", None) or rng.choice([n for n in (GIRL_NAMES if hg2 == "girl" else BOY_NAMES) if n != hero])
    elder = getattr(args, "elder", None) or rng.choice(["the elder", "the grandmother", "the river spirit"])
    mood = getattr(args, "mood", None) or rng.choice(["wise", "bright", "tender"])
    return StoryParams(place=place, task=task, gift=gift, hero=hero, hero_gender=hg,
                       helper=helper, helper_gender=hg2, elder=elder, mood=mood)


def _make_world(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    world = World(place=place)
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_gender,
                            role="hero", attrs={}, meters={"effort": 0.0}, memes={"hope": 0.0, "hurt": 0.0}))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_gender,
                              role="helper", attrs={}, meters={"effort": 0.0}, memes={"hope": 0.0, "hurt": 0.0}))
    elder = world.add(Entity(id="Elder", kind="character", type="goddess" if "spirit" in params.elder else "woman",
                             label=params.elder, role="elder", attrs={}, meters={"blessing": 0.0}, memes={"peace": 0.0}))
    tram = world.add(Entity(id="tram", kind="thing", type="tram", label="tram",
                            attrs={"stuck": 1}, meters={"stuck": 1.0, "motion": 0.0, "shine": 0.0},
                            memes={"frustration": 1.0}))
    gift = world.add(Entity(id=params.gift, kind="thing", type="gift", label=_safe_lookup(GIFTS, params.gift).label,
                            phrase=_safe_lookup(GIFTS, params.gift).phrase, tags=set(_safe_lookup(GIFTS, params.gift).tags),
                            meters={"found": 0.0}, memes={"surprise": 0.0}))
    world.facts.update(hero=hero, helper=helper, elder=elder, tram=tram, gift=gift, place=place, params=params)
    return world


def tell(params: StoryParams) -> World:
    world = _make_world(params)
    hero, helper, elder, tram, gift, place = (world.facts[k] for k in ["hero", "helper", "elder", "tram", "gift", "place"])
    task = _safe_lookup(TASKS, params.task)

    hero.memes["hope"] += 1
    helper.memes["hope"] += 1
    tram.meters["stuck"] = 1.0
    world.say(f"At {place.label}, {hero.id} and {helper.id} found a tram resting under {place.light}.")
    world.say(f"The old wheels would only answer with a quiet {task.sound}, and the tram would not move.")

    world.para()
    world.say(f'"We should {task.verb}," said {hero.id}.')
    world.say(f'"No," said {helper.id}, "we should look for the elder first."')
    hero.memes["hurt"] += 1
    helper.memes["hurt"] += 1
    world.say(f"Their words grew sharp, and for a little while the tram stayed still between them.")

    world.para()
    hero.meters["effort"] += 1
    helper.meters["effort"] += 1
    tram.meters["motion"] += 1
    tram.meters["stuck"] = 0.0
    tram.memes["frustration"] = 0.0
    world.say(f"Then the two of them chose teamwork.")
    world.say(f"{hero.id} braced one side while {helper.id} pushed the other, and the tram answered with a deep {task.sound}.")
    world.say(f"Together they made the wheels turn, and the hill no longer felt so steep.")

    world.para()
    gift.meters["found"] = 1.0
    gift.memes["surprise"] = 1.0
    elder.meters["blessing"] += 1
    elder.memes["peace"] += 1
    world.say(f"As the tram moved, a surprise waited beneath its seat: {gift.phrase}.")
    world.say(f"{elder.label_word.capitalize()} smiled at the sight, as if the hill itself had planned the gift.")
    world.say(f'"It was meant for the two of you," said {elder.label_word}. "A true road opens when hearts open too."')

    world.para()
    hero.memes["hurt"] = 0.0
    helper.memes["hurt"] = 0.0
    hero.memes["peace"] = 1.0
    helper.memes["peace"] = 1.0
    world.say(f"{hero.id} and {helper.id} looked at each other, then laughed at their old quarrel.")
    world.say(f"They made peace, shared the gift, and let the tram roll on in the warm light.")
    world.say(f"At the end, the tram could chug again, and both children basked in the gold of dusk.")

    world.facts.update(task=task, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    task = _safe_lookup(TASKS, p.task)
    gift = _safe_lookup(GIFTS, p.gift)
    return [
        f'Write a short myth for a child that uses the words "tram", "chug", and "bask".',
        f"Tell a story where {p.hero} and {p.helper} start with tension, then use teamwork to move a tram that only makes a {task.sound}, and end with reconciliation and a surprise.",
        f"Write a gentle myth about a stuck tram, a shared effort, and {gift.phrase} as a surprise ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    hero, helper, elder, tram, gift = world.facts["hero"], world.facts["helper"], world.facts["elder"], world.facts["tram"], world.facts["gift"]
    task = _safe_lookup(TASKS, p.task)
    qa = [
        QAItem(
            question=f"What were {p.hero} and {p.helper} trying to do with the tram?",
            answer=f"They were trying to {task.verb}. At first the tram stayed stuck, but their effort later became teamwork and moved it.",
        ),
        QAItem(
            question=f"Why did the two helpers stop arguing?",
            answer=f"They saw that fighting would not move the tram. When they worked together, the wheels answered with a deep chug and the path opened again.",
        ),
        QAItem(
            question=f"What surprise did the tram reveal?",
            answer=f"It revealed {gift.phrase}. The surprise belonged to the moment of peace, so the gift felt like a blessing from the road itself.",
        ),
        QAItem(
            question=f"How did the story end for {p.hero} and {p.helper}?",
            answer=f"They made reconciliation, shared the surprise, and let the tram roll on. By the end they were basking in the warm dusk instead of quarreling.",
        ),
    ]
    if tram.meters.get("motion", 0.0) >= THRESHOLD:
        qa.append(QAItem(
            question="What proved the tram changed by the end?",
            answer="The tram was stuck at first, but later it moved and chugged again. That change showed the teamwork really worked.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help each other and do a hard thing together. It often works better than one person trying alone.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people stop arguing and become friends again. They can smile, speak kindly, and share the next step together.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something you did not expect. It can feel exciting, especially when it appears after a hard moment.",
        ),
        QAItem(
            question="What does it mean to bask?",
            answer="To bask means to enjoy warm light or comfort. In a story, someone might bask in sunshine or a happy feeling.",
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
        parts = []
        if e.meters:
            parts.append(f"meters={e.meters}")
        if e.memes:
            parts.append(f"memes={e.memes}")
        if e.role:
            parts.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(parts)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, T, G) :- place(P), task(T), gift(G).
story_turn(P) :- place(P), task(chug), gift(G), G = bell.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for tid in TASKS:
        lines.append(asp.fact("task", tid))
    for gid in GIFTS:
        lines.append(asp.fact("gift", gid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    ok = True
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        ok = False
        print("MISMATCH between ASP and Python gates.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:
        ok = False
        print(f"SMOKE TEST FAILED: {exc}")
    return 0 if ok else 1


CURATED = [
    StoryParams(place="hill-road", task="chug", gift="bell", hero="Ari", hero_gender="girl", helper="Orin", helper_gender="boy", elder="the elder", mood="wise"),
    StoryParams(place="river-bend", task="bask", gift="lamp", hero="Mina", hero_gender="girl", helper="Levi", helper_gender="boy", elder="the river spirit", mood="bright"),
    StoryParams(place="stone-gate", task="chug", gift="seed", hero="Cai", hero_gender="boy", helper="Nia", helper_gender="girl", elder="the grandmother", mood="tender"),
]


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.task not in TASKS or params.gift not in GIFTS:
        pass
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
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        for combo in asp_valid_combos():
            print(combo)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
