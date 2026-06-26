#!/usr/bin/env python3
"""
Storyworld: banner, lone, opposition, rhyme, twist, magic, comedy.

A small, constraint-checked story domain about a lone maker who prepares a
banner for a tiny show, runs into opposition, and discovers that a magical
twist can turn the scene into a funny rhyme.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------


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
    carried_by: Optional[str] = None
    displayed_in: Optional[str] = None
    magical: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    banner: object | None = None
    helper: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
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
class Place:
    name: str
    indoors: bool = False
    echo: bool = False
    outdoors: bool = False
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
class Problem:
    opposition: str
    rhyme_hint: str
    twist_hint: str
    magic_help: str
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
    banner: str
    opposition: str
    hero_name: str
    hero_type: str
    helper_type: str
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
    def __init__(self, place: Place):
        self.place = place
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
        import copy
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "courtyard": Place(name="the courtyard", outdoors=True),
    "hall": Place(name="the hall", indoors=True, echo=True),
    "market": Place(name="the market square", outdoors=True, echo=True),
}

BANNERS = {
    "welcome": ("welcome banner", "a bright welcome banner", "welcome"),
    "joke": ("joke banner", "a silly joke banner", "joke"),
    "festival": ("festival banner", "a colorful festival banner", "festival"),
}

OPPOSITIONS = {
    "wind": Problem(
        opposition="wind",
        rhyme_hint="grinned/wind",
        twist_hint="spin",
        magic_help="The banner could puff up like a sail and sing its own line.",
    ),
    "frown": Problem(
        opposition="frown",
        rhyme_hint="town/frown",
        twist_hint="bounce",
        magic_help="The banner could flash a grin and make the grumpies snort-laugh.",
    ),
    "tangle": Problem(
        opposition="tangle",
        rhyme_hint="angle/tangle",
        twist_hint="unfold",
        magic_help="The banner could untie itself and flatten out with a cheerful pop.",
    ),
}

HERO_NAMES = ["Mina", "Toby", "Pia", "Nico", "Luna", "Remy"]
HERO_TYPES = ["girl", "boy"]
HELPERS = {
    "cat": "a sleepy cat",
    "bird": "a tiny bird",
    "mouse": "a brave mouse",
}


# ---------------------------------------------------------------------------
# Story helpers
# ---------------------------------------------------------------------------

def intro(world: World, hero: Entity, banner: Entity, helper: Entity) -> None:
    world.say(
        f"{hero.id} was a lone little maker who loved turning scraps into smiles."
    )
    world.say(
        f"One morning, {hero.id} painted {banner.phrase} because {hero.pronoun('subject')} "
        f"wanted the whole place to feel cheery."
    )
    world.say(
        f"Only {helper.phrase} stayed near {hero.pronoun('object')}, blinking as if this was a very serious art job."
    )


def opposition_scene(world: World, hero: Entity, banner: Entity, problem: Problem) -> None:
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1
    hero.memes["pride"] = hero.memes.get("pride", 0.0) + 1
    world.para()
    world.say(
        f"But when {hero.id} tried to hang the banner, {problem.opposition} pushed back at every step."
    )
    hero.meters["frustration"] = hero.meters.get("frustration", 0.0) + 1
    world.say(
        f"The cloth curled, wobbled, and made {hero.pronoun('object')} look extra lone."
    )
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1


def rhyme_setup(world: World, hero: Entity, problem: Problem) -> None:
    world.say(
        f"{hero.id} muttered, 'This is no fun in the sun,' and the little helper answered with a hum."
    )
    world.say(
        f"Even the air seemed ready for a rhyme: {problem.rhyme_hint}."
    )


def magic_twist(world: World, hero: Entity, banner: Entity, problem: Problem) -> None:
    banner.magical = True
    banner.meters["glow"] = banner.meters.get("glow", 0.0) + 1
    hero.memes["surprise"] = hero.memes.get("surprise", 0.0) + 1
    world.say(
        f"Then the banner gave a tiny sparkle and the oddest twist hopped out of it."
    )
    world.say(
        f"It whispered, 'Don't fight the {problem.opposition}; outshine it!'"
    )
    world.say(problem.magic_help)


def resolution(world: World, hero: Entity, banner: Entity, helper: Entity, problem: Problem) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 2
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1
    hero.memes["laughter"] = hero.memes.get("laughter", 0.0) + 1
    hero.meters["frustration"] = 0.0
    banner.displayed_in = world.place.name
    world.para()
    world.say(
        f"{hero.id} tried the new idea, and the banner popped open in one bold whoosh."
    )
    world.say(
        f"The {problem.opposition} turned silly instead of scary, and {helper.phrase} did a tiny hop."
    )
    world.say(
        f"Soon everyone could read {banner.phrase}, and the place felt bright, breezy, and a little bit ridiculous."
    )
    world.say(
        f"{hero.id} grinned at the finished sign, no longer lone at all."
    )


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combo(place: str, banner: str, opposition: str) -> bool:
    if place not in PLACES or banner not in BANNERS or opposition not in OPPOSITIONS:
        return False
    # A story needs a real obstacle and a magic-friendly twist.
    if place == "hall" and opposition == "wind":
        return False
    if place == "courtyard" and opposition == "tangle" and banner == "welcome":
        return False
    return True


def reason_for_rejection(place: str, banner: str, opposition: str) -> str:
    if place == "hall" and opposition == "wind":
        return "(No story: wind cannot be a useful opposition in the hall, because the hall is indoors and the banner would not face that problem.)"
    if place == "courtyard" and opposition == "tangle" and banner == "welcome":
        return "(No story: that banner and opposition do not make a strong enough twist together.)"
    return "(No story: the chosen pieces do not form a clear, funny problem-and-fix story.)"


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    world = World(place)
    banner_label, banner_phrase, _ = _safe_lookup(BANNERS, params.banner)
    problem = _safe_lookup(OPPOSITIONS, params.opposition)

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        meters={"frustration": 0.0},
        memes={"hope": 0.0, "pride": 0.0},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=params.helper_type,
        phrase=_safe_lookup(HELPERS, params.helper_type),
        meters={},
        memes={},
    ))
    banner = world.add(Entity(
        id="banner",
        type="banner",
        label=banner_label,
        phrase=banner_phrase,
        owner=hero.id,
        meters={"glow": 0.0},
        memes={},
    ))

    intro(world, hero, banner, helper)
    world.para()
    world.say(f"That afternoon, {hero.id} carried the banner to {world.place.name}.")
    if world.place.echo:
        world.say("The room echoed every rustle, which made the waiting feel even funnier.")
    opposition_scene(world, hero, banner, problem)
    rhyme_setup(world, hero, problem)
    magic_twist(world, hero, banner, problem)
    resolution(world, hero, banner, helper, problem)

    world.facts.update(
        hero=hero,
        helper=helper,
        banner=banner,
        problem=problem,
        place=place,
        params=params,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    banner: Entity = _safe_fact(world, f, "banner")
    problem: Problem = _safe_fact(world, f, "problem")
    return [
        f'Write a short comedic story for a child about {hero.id}, a lone maker, and {banner.phrase}.',
        f"Tell a funny story where a banner faces {problem.opposition} and a magical twist helps it work.",
        f'Write a rhyme-tinged story about "{banner.label}", "{problem.opposition}", and a happy ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    helper: Entity = _safe_fact(world, f, "helper")
    banner: Entity = _safe_fact(world, f, "banner")
    problem: Problem = _safe_fact(world, f, "problem")
    place: Place = _safe_fact(world, f, "place")
    return [
        QAItem(
            question=f"What was {hero.id} trying to make for {place.name}?",
            answer=f"{hero.id} was making {banner.phrase} so the place could feel cheerful.",
        ),
        QAItem(
            question=f"What got in the way of hanging the banner?",
            answer=f"{problem.opposition} kept pushing back and made the banner wobble and curl.",
        ),
        QAItem(
            question=f"Who stayed near {hero.id} while the work was happening?",
            answer=f"{helper.phrase} stayed close and watched the whole silly project.",
        ),
        QAItem(
            question=f"What changed after the magical twist?",
            answer=f"The banner opened up, the trouble turned funny, and {hero.id} was no longer lone.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [
        QAItem(
            question="What is a banner?",
            answer="A banner is a long sign or cloth that shows words or pictures and can be hung up to greet people or celebrate something.",
        ),
        QAItem(
            question="What does lone mean?",
            answer="Lone means alone, with nobody else right beside you.",
        ),
        QAItem(
            question="What is opposition?",
            answer="Opposition is something that pushes against a plan or makes it harder to do.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising turn that changes what is happening in a story.",
        ),
        QAItem(
            question="What does magic do in a funny story?",
            answer="Magic can make impossible things happen, which often adds wonder and a laugh.",
        ),
        QAItem(
            question="What makes comedy funny?",
            answer="Comedy uses silly surprises, odd timing, or playful trouble to make people laugh.",
        ),
    ]
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.phrase:
            bits.append(f"phrase={e.phrase!r}")
        if e.magical:
            bits.append("magical=True")
        if e.displayed_in:
            bits.append(f"displayed_in={e.displayed_in!r}")
        lines.append(f"  {e.id:10} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(P) :- setting(P).
banner(B) :- banner_kind(B).
opposition(O) :- opposition_kind(O).

good_story(P,B,O) :- place(P), banner(B), opposition(O), not bad_combo(P,B,O).
bad_combo(hall,_,wind).
bad_combo(courtyard,welcome,tangle).

valid(P,B,O) :- place(P), banner(B), opposition(O), good_story(P,B,O).

#show valid/3.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("setting", pid))
    for bid in BANNERS:
        lines.append(asp.fact("banner_kind", bid))
    for oid in OPPOSITIONS:
        lines.append(asp.fact("opposition_kind", oid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(p, b, o) for p in PLACES for b in BANNERS for o in OPPOSITIONS if valid_combo(p, b, o)}
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combo() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny comedic storyworld with banners, opposition, rhyme, and magic.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--banner", choices=BANNERS)
    ap.add_argument("--opposition", choices=OPPOSITIONS)
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--helper-type", choices=HELPERS)
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
    places = [getattr(args, "place", None)] if getattr(args, "place", None) else list(PLACES)
    banners = [getattr(args, "banner", None)] if getattr(args, "banner", None) else list(BANNERS)
    oppositions = [getattr(args, "opposition", None)] if getattr(args, "opposition", None) else list(OPPOSITIONS)

    combos = [(p, b, o) for p in places for b in banners for o in oppositions if valid_combo(p, b, o)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place, banner, opposition = (list(rng.choice(combos)) + [None, None, None])[:3]
    hero_type = getattr(args, "hero_type", None) or rng.choice(HERO_TYPES)
    helper_type = getattr(args, "helper_type", None) or rng.choice(list(HELPERS))
    hero_name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    return StoryParams(
        place=place,
        banner=banner,
        opposition=opposition,
        hero_name=hero_name,
        hero_type=hero_type,
        helper_type=helper_type,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
        print(f"{len(combos)} compatible (place, banner, opposition) combos:\n")
        for p, b, o in combos:
            print(f"  {p:10} {b:10} {o}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        curated = [
            StoryParams(place="courtyard", banner="welcome", opposition="wind", hero_name="Mina", hero_type="girl", helper_type="cat"),
            StoryParams(place="hall", banner="joke", opposition="tangle", hero_name="Nico", hero_type="boy", helper_type="mouse"),
            StoryParams(place="market", banner="festival", opposition="frown", hero_name="Luna", hero_type="girl", helper_type="bird"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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
            header = f"### {p.hero_name}: {p.banner} vs {p.opposition} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
