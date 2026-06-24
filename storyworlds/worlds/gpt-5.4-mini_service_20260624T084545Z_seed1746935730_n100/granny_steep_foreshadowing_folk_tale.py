#!/usr/bin/env python3
"""
A small folk-tale storyworld about a granny, a steep hill, and foreshadowing.

Seed premise:
A granny lives by a steep hill. She notices small signs that a hard trip is coming.
She prepares wisely, helps her family, and the warning pays off before the day ends.

This world models:
- a granny character with care and patience
- a steep path with risk of slipping
- foreshadowing as a stateful omen that predicts trouble
- a turn where planning prevents the trouble

The story reads like a classical folk tale:
- beginning: a cozy home and a quiet warning
- middle: the granny follows the clue and gathers what is needed
- ending: the climb is safer, and the later trouble is already solved
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

NAME_POOL = [
    "Mira", "Anya", "Nell", "Tara", "Bess", "June", "Ivy", "Clara", "Lena", "Mabel"
]

HELPERS = [
    ("lantern", "a little lantern", "gives light on the path"),
    ("shawl", "a warm shawl", "keeps shoulders cozy in the wind"),
    ("staff", "a smooth wooden staff", "helps steady each step"),
    ("basket", "a sturdy basket", "carries bread and apples safely"),
]

TENSIONS = [
    ("wind", "a cold wind"), 
    ("fog", "a white fog"),
    ("mud", "fresh mud"),
    ("rain", "soft rain"),
]

OMENS = [
    ("cracked_cup", "the tea cup cracked on the saucer"),
    ("bird_call", "a black bird called from the fence"),
    ("loose_stone", "a loose stone rolled down the path"),
    ("dull_fire", "the fire burned low and blue"),
]



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
    label: str = ""
    phrase: str = ""
    type: str = "thing"
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    granny: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"granny", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)

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
class StoryParams:
    place: str
    omen: str
    helper: str
    tension: str
    name: str
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


PLACES = {
    "hill": "the steep hill",
    "lane": "the steep lane",
    "path": "the steep path",
    "stairs": "the steep stone stairs",
}

SETTING_DETAILS = {
    "hill": "The hill rose high behind the cottage, and the road curved like a ribbon.",
    "lane": "The lane climbed past hedges and old posts, and every cart wheel had to work hard there.",
    "path": "The path climbed through the trees, narrow and rough, with roots like fingers underfoot.",
    "stairs": "The stone stairs climbed the old bank, and each step was uneven from long use.",
}


@dataclass
class OmenDef:
    id: str
    sign: str
    warning: str
    later: str
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


OMENS_REGISTRY = {
    "cracked_cup": OmenDef(
        id="cracked_cup",
        sign="the tea cup cracked on the saucer",
        warning="something small can split before something bigger slips",
        later="the top stone on the steep way would loosen too",
    ),
    "bird_call": OmenDef(
        id="bird_call",
        sign="a black bird called from the fence",
        warning="a dark cry can mean weather is turning",
        later="the hill would grow wet and slick before supper",
    ),
    "loose_stone": OmenDef(
        id="loose_stone",
        sign="a loose stone rolled down the path",
        warning="a rolling stone means the climb will be tricky",
        later="more stones would roll once feet began to hurry",
    ),
    "dull_fire": OmenDef(
        id="dull_fire",
        sign="the fire burned low and blue",
        warning="when the hearth burns odd, a hard errand is near",
        later="the evening would ask for light and a steady hand",
    ),
}


HELPER_REGISTRY = {
    "lantern": {"label": "a little lantern", "use": "shine on the steep way"},
    "shawl": {"label": "a warm shawl", "use": "keep the wind from biting"},
    "staff": {"label": "a smooth wooden staff", "use": "steady each careful step"},
    "basket": {"label": "a sturdy basket", "use": "carry bread and apples without dropping them"},
}


class OmenWorld(World):
    pass


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk tale world about granny, steep ground, and foreshadowing.")
    ap.add_argument("--place", choices=PLACES.keys())
    ap.add_argument("--omen", choices=OMENS_REGISTRY.keys())
    ap.add_argument("--helper", choices=HELPER_REGISTRY.keys())
    ap.add_argument("--tension", choices=[t[0] for t in TENSIONS])
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for omen in OMENS_REGISTRY:
            for helper in HELPER_REGISTRY:
                combos.append((place, omen, helper))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "place", None) and getattr(args, "place", None) not in PLACES:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place = getattr(args, "place", None) or rng.choice(list(PLACES.keys()))
    omen = getattr(args, "omen", None) or rng.choice(list(OMENS_REGISTRY.keys()))
    helper = getattr(args, "helper", None) or rng.choice(list(HELPER_REGISTRY.keys()))
    tension = getattr(args, "tension", None) or rng.choice([t[0] for t in TENSIONS])
    name = getattr(args, "name", None) or rng.choice(NAME_POOL)
    return StoryParams(place=place, omen=omen, helper=helper, tension=tension, name=name)


def _set(world: World, eid: str, meter: str, value: float) -> None:
    world.get(eid).meters[meter] = value


def introduce(world: OmenWorld, granny: Entity) -> None:
    world.say(f"Long ago, in a little cottage near {world.place}, there lived a kind granny named {granny.id}.")
    world.say("She noticed small things the way some people notice songs: a cracked cup, a sudden hush, or a stone in the wrong place.")


def foreshadow(world: OmenWorld, granny: Entity) -> None:
    omen = _safe_fact(world, world.facts, "omen")
    world.say(f"One morning, {omen.sign}.")
    world.say(f"{granny.id} nodded softly, because {omen.warning}.")
    world.facts["foreshadowed"] = True
    granny.memes["care"] = granny.memes.get("care", 0) + 1
    granny.memes["worry"] = granny.memes.get("worry", 0) + 1


def prepare(world: OmenWorld, granny: Entity) -> None:
    helper_key = (world.facts.get("helper") if hasattr(world.facts, "get") else _safe_fact(world, world.facts, "helper"))
    helper = HELPER_REGISTRY[helper_key]
    world.say(f"So {granny.id} fetched {helper['label']} from the shelf, for it could {helper['use']}.")
    world.facts["prepared"] = True
    world.add(Entity(id=helper_key, label=helper["label"], phrase=helper["label"], type=helper_key, owner=granny.id))


def warn_on_steep(world: OmenWorld, granny: Entity) -> None:
    tension = dict(TENSIONS)[world.facts["tension"]]
    world.say(f"By afternoon, {tension} moved over {world.place}.")
    world.say(f"The hill looked steeper than before, and {granny.id} knew the day would ask for patience.")
    world.facts["risk"] = True


def climb(world: OmenWorld, granny: Entity) -> None:
    helper_key = (world.facts.get("helper") if hasattr(world.facts, "get") else _safe_fact(world, world.facts, "helper"))
    helper = HELPER_REGISTRY[helper_key]
    world.say(f"{granny.id} went on the steep way with {helper['label']}.")
    if helper_key == "staff":
        world.say("She set the staff down before each step and climbed slowly.")
    elif helper_key == "lantern":
        world.say("She lifted the lantern where the shadows hid the uneven stones.")
    elif helper_key == "shawl":
        world.say("She wrapped the shawl close and kept the wind from troubling her eyes.")
    else:
        world.say("She held the basket with both hands, so the bread and apples would stay safe.")
    world.facts["climbed"] = True


def payoff(world: OmenWorld, granny: Entity) -> None:
    omen = _safe_fact(world, world.facts, "omen")
    tension = dict(TENSIONS)[world.facts["tension"]]
    helper_key = (world.facts.get("helper") if hasattr(world.facts, "get") else _safe_fact(world, world.facts, "helper"))
    world.say(f"And just as {omen.later}, {tension} thickened on the path.")
    if helper_key in {"staff", "lantern"}:
        world.say(f"But because {granny.id} had listened early, she was already safe and steady on the way.")
    else:
        world.say(f"But because {granny.id} had listened early, she was already warm and careful, and the hill could not rush her.")
    world.say(f"At the top, {granny.id} smiled at the little cottage below, where the warning had helped before trouble arrived.")
    world.facts["resolved"] = True


def tell(params: StoryParams) -> OmenWorld:
    world = OmenWorld(place=_safe_lookup(PLACES, params.place))
    world.facts.update(params=params, omen=params.omen, helper=params.helper, tension=params.tension)

    granny = world.add(Entity(id=params.name, kind="character", type="granny", label="granny"))
    world.say(_safe_lookup(SETTING_DETAILS, params.place))
    world.para()

    introduce(world, granny)
    foreshadow(world, granny)
    world.para()

    prepare(world, granny)
    warn_on_steep(world, granny)
    climb(world, granny)
    world.para()

    payoff(world, granny)
    world.facts["granny"] = granny
    return world


def generation_prompts(world: OmenWorld) -> list[str]:
    p = _safe_fact(world, world.facts, "params")
    return [
        f'Write a short folk tale for young children about a granny named {p.name} on {world.place}, where a small omen comes before a steep climb.',
        f'Tell a gentle story with foreshadowing: show {p.name} noticing {OMENS_REGISTRY[p.omen].sign}, then taking {HELPER_REGISTRY[p.helper]["label"]} to face the steep way.',
        f'Write a cozy folk tale about a steep path, a careful granny, and a warning that turns out to be useful later.',
    ]


def story_qa(world: OmenWorld) -> list[QAItem]:
    p = _safe_fact(world, world.facts, "params")
    helper = HELPER_REGISTRY[p.helper]["label"]
    omen = OMENS_REGISTRY[p.omen].sign
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about a kind granny named {p.name} who lives near {world.place} and pays attention to small signs.",
        ),
        QAItem(
            question=f"What small sign foreshadowed trouble?",
            answer=f"The story foreshadowed trouble when {omen}. Granny understood that the sign meant something harder might come later.",
        ),
        QAItem(
            question=f"What did granny take because the hill was steep?",
            answer=f"She took {helper} so she could handle the steep way wisely instead of hurrying and slipping.",
        ),
        QAItem(
            question=f"How did the warning help in the end?",
            answer=f"The warning helped because granny prepared before the trouble arrived, so when the weather or stones turned worse, she was already safe and ready.",
        ),
    ]


def world_knowledge_qa(world: OmenWorld) -> list[QAItem]:
    return [
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is when a story gives a small hint early on that something important may happen later.",
        ),
        QAItem(
            question="What does steep mean?",
            answer="Steep means rising or falling sharply, so a steep hill or path can be hard to climb.",
        ),
        QAItem(
            question="Why do people use a staff when walking on a rough path?",
            answer="A staff can help someone keep balance, especially on a rough or steep path.",
        ),
    ]


def dump_trace(world: OmenWorld) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


ASP_RULES = r"""
place(hill; lane; path; stairs).
omen(cracked_cup; bird_call; loose_stone; dull_fire).
helper(lantern; shawl; staff; basket).

steep(hill).
steep(lane).
steep(path).
steep(stairs).

foreshadows(O) :- omen(O).
useful(lantern, hill).
useful(shawl, lane).
useful(staff, path).
useful(staff, stairs).
useful(basket, lane).

valid(Place, Omen, Helper) :- place(Place), omen(Omen), helper(Helper), steep(Place).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
        lines.append(asp.fact("steep", p))
    for o in OMENS_REGISTRY:
        lines.append(asp.fact("omen", o))
    for h in HELPER_REGISTRY:
        lines.append(asp.fact("helper", h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    if py - cl:
        print(" only in python:", sorted(py - cl))
    if cl - py:
        print(" only in ASP:", sorted(cl - py))
    return 1


CURATED = [
    StoryParams(place="hill", omen="cracked_cup", helper="staff", tension="fog", name="Mabel"),
    StoryParams(place="path", omen="loose_stone", helper="lantern", tension="rain", name="Ivy"),
    StoryParams(place="stairs", omen="bird_call", helper="shawl", tension="wind", name="Clara"),
]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


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
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, omen, helper) combos:")
        for c in combos:
            print("  ", c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(getattr(args, "n", None)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 and not getattr(args, "all", None) else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
