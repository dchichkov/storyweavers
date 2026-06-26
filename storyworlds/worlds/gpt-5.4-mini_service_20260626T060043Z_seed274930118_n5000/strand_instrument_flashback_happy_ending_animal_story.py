#!/usr/bin/env python3
"""
storyworlds/worlds/strand_instrument_flashback_happy_ending_animal_story.py
===========================================================================

A small animal-story world about a stranded tune, a helpful instrument, a
flashback to a lesson learned, and a happy ending.

Seed premise:
- An animal character wants to make music with an instrument.
- A fragile strand (like a string, ribbon, or braid) causes a problem.
- A remembered flashback provides the key idea for fixing it.
- The ending should feel warm, concrete, and satisfying.

This world keeps the prose child-facing and state-driven: the same entity model
drives the story, trace output, Q&A, and the ASP twin.
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
# Core model
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    hero: object | None = None
    inst: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"cat", "kitten", "rabbit", "fox", "mouse", "bear", "bird", "dog"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    place: str = "the little music meadow"
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
    trouble: str
    fixable_by: str
    keyword: str = ""
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
class Instrument:
    id: str
    label: str
    phrase: str
    kind: str
    delicate_part: str
    requires: str
    repaired_by: str
    sound: str
    tags: set[str] = field(default_factory=set)
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
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

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
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "meadow": Setting(place="the little music meadow", affords={"play", "practice"}),
    "barn": Setting(place="the barn stage", affords={"play", "practice"}),
    "treehouse": Setting(place="the treehouse room", affords={"practice"}),
}

ACTIVITIES = {
    "play": Activity(
        id="play",
        verb="play a song",
        gerund="playing a song",
        rush="rush to the stage",
        trouble="a broken strand on the instrument",
        fixable_by="rest",
        keyword="strand",
        tags={"music", "strand"},
    ),
    "practice": Activity(
        id="practice",
        verb="practice a tune",
        gerund="practicing a tune",
        rush="hurry to the corner bench",
        trouble="a loose strand on the bow",
        fixable_by="care",
        keyword="instrument",
        tags={"music", "instrument"},
    ),
}

INSTRUMENTS = {
    "harp": Instrument(
        id="harp",
        label="harp",
        phrase="a small wooden harp",
        kind="harp",
        delicate_part="one string",
        requires="careful hands",
        repaired_by="a fresh string",
        sound="soft and bright",
        tags={"string", "music"},
    ),
    "drum": Instrument(
        id="drum",
        label="drum",
        phrase="a round drum with a bright strap",
        kind="drum",
        delicate_part="the strap strand",
        requires="gentle taps",
        repaired_by="a tied knot",
        sound="booming and happy",
        tags={"strap", "music"},
    ),
    "flute": Instrument(
        id="flute",
        label="flute",
        phrase="a smooth little flute",
        kind="flute",
        delicate_part="a reed strand",
        requires="slow breath",
        repaired_by="a new reed",
        sound="light and sweet",
        tags={"reed", "music"},
    ),
}

ANIMALS = {
    "rabbit": ("rabbit", "bouncy"),
    "fox": ("fox", "clever"),
    "cat": ("cat", "curious"),
    "bear": ("bear", "gentle"),
    "mouse": ("mouse", "tiny"),
    "bird": ("bird", "bright"),
}


@dataclass
class StoryParams:
    place: str
    activity: str
    instrument: str
    animal: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
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


def instrument_at_risk(activity: Activity, instrument: Instrument) -> bool:
    return activity.id in {"play", "practice"} and instrument.kind in {"harp", "drum", "flute"}


def select_fix(activity: Activity, instrument: Instrument) -> bool:
    return instrument_at_risk(activity, instrument)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = _safe_lookup(ACTIVITIES, act_id)
            for inst_id, inst in INSTRUMENTS.items():
                if instrument_at_risk(act, inst) and select_fix(act, inst):
                    combos.append((place, act_id, inst_id))
    return combos


def explain_rejection(activity: Activity, instrument: Instrument) -> str:
    return (
        f"(No story: {activity.gerund} does not sensibly lead to a fixable problem "
        f"for {instrument.phrase}. Try a different instrument or activity.)"
    )


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def predict_break(world: World, activity: Activity, instrument: Instrument) -> dict:
    sim = world.copy()
    hero = next(e for e in sim.characters())
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    instrument_ent = sim.get(instrument.id)
    instrument_ent.meters["tension"] = instrument_ent.meters.get("tension", 0.0) + 1
    return {
        "trouble": True,
        "memory_helped": True,
    }


def flashback_line(hero: Entity, instrument: Instrument) -> str:
    return (
        f"{hero.pronoun('subject').capitalize()} remembered how {hero.id} had once "
        f"watched a grown-up tie a loose strand before bedtime."
    )


def tell(setting: Setting, activity: Activity, instrument: Instrument, animal_name: str) -> World:
    world = World(setting)
    animal_type, trait = _safe_lookup(ANIMALS, animal_name)
    hero = world.add(Entity(
        id=animal_name,
        kind="character",
        type=animal_type,
        traits=["little", trait, "music-loving"],
    ))
    inst = world.add(Entity(
        id=instrument.id,
        type=instrument.kind,
        label=instrument.label,
        phrase=instrument.phrase,
        owner=hero.id,
    ))

    world.say(
        f"{hero.id} was a little {trait} {animal_type} who loved music and loved "
        f"{inst.phrase}."
    )
    world.say(
        f"At {setting.place}, {hero.id} liked to {activity.verb} because {inst.sound} sounds "
        f"made the whole day feel kind."
    )

    world.para()
    world.say(
        f"One day, {hero.id} hurried to {setting.place} to {activity.verb}, but "
        f"{inst.label} had {activity.trouble}."
    )
    world.say(
        f"The strand looked too loose, and the song could not begin the right way."
    )

    world.para()
    world.say(flashback_line(hero, inst))
    world.say(
        f"{hero.id} gently found a fresh thread and tied it the same careful way."
    )
    world.say(
        f"Then {hero.id} tried again, and this time the {inst.label} sang with {inst.sound} notes."
    )
    world.say(
        f"The other animals clapped, and {hero.id} smiled at the happy sound filling {setting.place}."
    )

    world.facts.update(
        hero=hero,
        instrument=inst,
        setting=setting,
        activity=activity,
        trait=trait,
        animal_type=animal_type,
        resolved=True,
        flashback=True,
        ending="happy",
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    act = _safe_fact(world, f, "activity")
    inst = _safe_fact(world, f, "instrument")
    return [
        'Write a short Animal Story about a little animal, a musical instrument, '
        'a remembered lesson, and a happy ending.',
        f"Tell a gentle story where {hero.id} wants to {act.verb} with {inst.phrase}, "
        f"but a loose strand causes trouble first.",
        f"Write a child-friendly story that includes the words 'strand' and 'instrument' "
        f"and ends with the music working again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    inst = _safe_fact(world, f, "instrument")
    act = _safe_fact(world, f, "activity")
    trait = _safe_fact(world, f, "trait")
    place = _safe_fact(world, f, "setting").place
    return [
        QAItem(
            question=f"Who is the story about at {place}?",
            answer=f"It is about {hero.id}, a little {trait} {f['animal_type']} who loves music.",
        ),
        QAItem(
            question=f"What was the problem with the {inst.label}?",
            answer=f"{inst.phrase} had {act.trouble}, so the song could not begin smoothly.",
        ),
        QAItem(
            question=f"What did {hero.id} remember to help fix the problem?",
            answer=(
                f"{hero.id} remembered a lesson about tying up a loose strand carefully, "
                f"and that helped make the instrument ready again."
            ),
        ),
        QAItem(
            question=f"How did the story end?",
            answer=(
                f"It ended happily, with the {inst.label} making {inst.sound} music and "
                f"the other animals clapping."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a strand?",
            answer="A strand is a thin piece, like a thread, string, or piece of hair.",
        ),
        QAItem(
            question="What is an instrument?",
            answer="An instrument is something people or animals use to make music, like a harp, drum, or flute.",
        ),
        QAItem(
            question="Why is careful fixing important?",
            answer="Careful fixing keeps delicate things from breaking more, so they can work again safely.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
at_risk(A,I) :- activity(A), instrument(I), needs_music(A), delicate(I).
valid(Place,A,I) :- affords(Place,A), at_risk(A,I), has_fix(A,I).
has_fix(A,I) :- at_risk(A,I).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        if a.id in {"play", "practice"}:
            lines.append(asp.fact("needs_music", aid))
    for iid, inst in INSTRUMENTS.items():
        lines.append(asp.fact("instrument", iid))
        lines.append(asp.fact("delicate", iid))
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
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI / generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal Story world: strand, instrument, flashback, happy ending."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--instrument", choices=INSTRUMENTS)
    ap.add_argument("--animal", choices=sorted(ANIMALS))
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
    if getattr(args, "activity", None) and getattr(args, "instrument", None):
        act = _safe_lookup(ACTIVITIES, getattr(args, "activity", None))
        inst = _safe_lookup(INSTRUMENTS, getattr(args, "instrument", None))
        if not instrument_at_risk(act, inst):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, instrument = rng.choice(list(combos))
    animal = getattr(args, "animal", None) or rng.choice(sorted(ANIMALS))
    return StoryParams(place=place, activity=activity, instrument=instrument, animal=animal)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIVITIES, params.activity), _safe_lookup(INSTRUMENTS, params.instrument), params.animal)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


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
        print(f"{len(combos)} compatible (place, activity, instrument) combos:")
        for row in combos:
            print("  ", row)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    if getattr(args, "all", None):
        samples = [
            generate(StoryParams(place=p, activity=a, instrument=i, animal=an))
            for (p, a, i) in valid_combos()
            for an in ["rabbit"]
        ]
    else:
        samples = []
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
