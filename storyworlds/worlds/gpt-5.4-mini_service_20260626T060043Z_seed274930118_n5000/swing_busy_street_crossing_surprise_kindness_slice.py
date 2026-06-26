#!/usr/bin/env python3
"""
storyworlds/worlds/swing_busy_street_crossing_surprise_kindness_slice.py
========================================================================

A small slice-of-life storyworld about a child, a swing, and a busy street
crossing. The world tracks both physical meters and emotional memes so the
story turns from tension to kindness in a state-driven way.

Premise:
- A child wants to reach a favorite swing on the other side of a busy crossing.
- The street is crowded, so a parent and crossing guard slow the moment down.
- A small surprise opens the way for a kind compromise.
- The ending image proves what changed: the child reaches the swing safely,
  and the crossing feels warmer than it did before.
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

    child: object | None = None
    guard: object | None = None
    parent: object | None = None
    swing: object | None = None
    def __post_init__(self) -> None:
        for k in ("distance", "traffic", "wait", "safe", "busy"):
            self.meters.setdefault(k, 0.0)
        for k in ("joy", "worry", "surprise", "kindness", "patience", "relief"):
            self.memes.setdefault(k, 0.0)

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
class Crossing:
    place: str = "the busy street crossing"
    afford_wait: bool = True
    afford_cross: bool = True
    affords_swing: bool = True
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
class Swing:
    label: str = "swing"
    phrase: str = "the bright blue swing"
    keyword: str = "swing"
    surprise: str = "a small surprise"
    kindness: str = "a kind little help"
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
    def __init__(self, setting: Crossing) -> None:
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


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
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


SETTINGS = {
    "crossing": Crossing(),
}

SWINGS = {
    "swing": Swing(),
}

GIRL_NAMES = ["Mina", "Lily", "Ava", "Nora", "Ivy", "Zoe"]
BOY_NAMES = ["Theo", "Leo", "Finn", "Milo", "Eli", "Noah"]


def _line(world: World, text: str) -> None:
    world.say(text)


def _introduce(world: World, child: Entity, parent: Entity, swing: Entity) -> None:
    child.memes["joy"] += 1
    _line(
        world,
        f"{child.id} loved the little swing at the other side of {world.setting.place}. "
        f"On quiet afternoons, {child.pronoun()} liked to race the clouds there with {child.pronoun('possessive')} {parent.type}."
    )
    _line(
        world,
        f"Today, though, the road was louder than usual. Cars hummed past in a steady stream, and the crossing looked extra busy."
    )
    world.facts["swing_phrase"] = swing.phrase


def _want_cross(world: World, child: Entity, parent: Entity) -> None:
    child.memes["worry"] += 0.2
    child.memes["desire"] += 1
    _line(
        world,
        f"{child.id} pointed across the street and said {child.pronoun('possessive')} {parent.type} wanted to go now, because the swing was waiting."
    )
    _line(
        world,
        f"{parent.id} held out a hand and asked {child.id} to stay close. The light had not changed yet, and the curb was too near the cars."
    )


def _surprise(world: World, guard: Entity, child: Entity, swing: Entity) -> None:
    guard.memes["surprise"] += 1
    child.memes["surprise"] += 1
    _line(
        world,
        f"Then something small and surprising happened: {guard.id}, the crossing guard, smiled and pointed to the far side."
    )
    _line(
        world,
        f"{guard.id} had already noticed {swing.phrase}, and {guard.pronoun()} had saved the shortest safe moment for {child.id}."
    )
    world.facts["surprise"] = True
    world.facts["kindness_offer"] = True


def _kindness(world: World, guard: Entity, parent: Entity, child: Entity) -> None:
    guard.memes["kindness"] += 1
    parent.memes["patience"] += 1
    child.memes["patience"] += 1
    _line(
        world,
        f"With a gentle wave, {guard.id} asked the cars to wait. {guard.pronoun().capitalize()} let the family cross first and even walked beside them."
    )
    _line(
        world,
        f"{parent.id} thanked {guard.id}, and {child.id} felt the tight feeling in {child.pronoun('possessive')} chest loosen a little."
    )


def _cross_and_play(world: World, child: Entity, parent: Entity, swing: Entity) -> None:
    child.meters["distance"] += 1
    child.memes["joy"] += 1
    child.memes["relief"] += 1
    _line(
        world,
        f"They crossed carefully together. When they reached the other side, the traffic noise faded behind them like a held breath."
    )
    _line(
        world,
        f"At last, {child.id} sat on {swing.phrase} and pumped {child.pronoun('possessive')} feet. {parent.id} stood nearby, smiling at how a busy crossing had turned into a safe little adventure."
    )


def tell(setting: Crossing, swing_def: Swing, hero_name: str, hero_type: str, parent_type: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type))
    guard = world.add(Entity(id="Guard", kind="character", type="adult"))
    swing = world.add(Entity(id="Swing", type="thing", label=swing_def.label, phrase=swing_def.phrase, owner="Park"))
    world.facts.update(child=child, parent=parent, guard=guard, swing=swing, setting=setting, swing_def=swing_def)

    _introduce(world, child, parent, swing)
    world.para()
    _want_cross(world, child, parent)
    _surprise(world, guard, child, swing)
    world.para()
    _kindness(world, guard, parent, child)
    _cross_and_play(world, child, parent, swing)

    world.facts["resolved"] = True
    return world


def valid_combos() -> list[tuple[str, str]]:
    return [("crossing", "swing")]


def explain_rejection(place: str, keyword: str) -> str:
    return f"(No story: this world is built for {keyword} at {place}, and the reasonableness gate only allows the crossing story.)"


def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", "crossing"), asp.fact("activity", "swing")]
    lines.append(asp.fact("affords", "crossing", "swing"))
    lines.append(asp.fact("feature", "surprise"))
    lines.append(asp.fact("feature", "kindness"))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(crossing,swing) :- affords(crossing,swing), feature(surprise), feature(kindness).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a gentle slice-of-life story about a child who wants to reach a swing at a busy street crossing.',
        'Tell a short story where surprise and kindness help a child cross the street safely to play on a swing.',
        f'Write a child-facing story that includes the word "{world.facts["swing_def"].keyword}" and ends in a calm, happy moment.',
    ]


def story_qa(world: World) -> list[QAItem]:
    child = _safe_fact(world, world.facts, "child")
    parent = _safe_fact(world, world.facts, "parent")
    guard = _safe_fact(world, world.facts, "guard")
    swing = _safe_fact(world, world.facts, "swing_def")
    return [
        QAItem(
            question=f"Why did {child.id} want to cross the street?",
            answer=f"{child.id} wanted to cross because {child.pronoun()} wanted to reach the {swing.label} on the other side of {world.setting.place}.",
        ),
        QAItem(
            question=f"What was surprising about the crossing?",
            answer=f"It was surprising that {guard.id} had already noticed the {swing.label} and helped the family cross at the right moment.",
        ),
        QAItem(
            question=f"How did kindness change the end of the story?",
            answer=f"Kindness made the crossing feel safe and calm, so {child.id} could enjoy the {swing.label} after crossing with {parent.id} nearby.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a swing for?",
            answer="A swing is for sitting and moving back and forth, which makes playing feel light and fun.",
        ),
        QAItem(
            question="Why do people wait at a busy street crossing?",
            answer="People wait so cars can pass and everyone can cross safely when it is their turn.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means helping in a gentle way, especially when someone needs patience or care.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that can make a moment feel exciting or new.",
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld: swing, surprise, kindness, and a busy street crossing.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--activity", choices=SWINGS.keys())
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "place", None) and getattr(args, "place", None) != "crossing":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "activity", None) and getattr(args, "activity", None) != "swing":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    return StoryParams(name=name, gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS["crossing"], SWINGS["swing"], params.name, params.gender, params.parent)
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
    StoryParams(name="Mina", gender="girl", parent="mother"),
    StoryParams(name="Theo", gender="boy", parent="father"),
    StoryParams(name="Lily", gender="girl", parent="father"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combo(s):")
        for place, act in combos:
            print(f"  {place:10} {act}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not getattr(args, "all", None) else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
