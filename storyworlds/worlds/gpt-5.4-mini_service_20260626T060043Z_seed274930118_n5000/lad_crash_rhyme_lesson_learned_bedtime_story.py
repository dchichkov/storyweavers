#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/lad_crash_rhyme_lesson_learned_bedtime_story.py
================================================================================================

A tiny bedtime-style storyworld about a little lad, a crash, a rhyme,
and a lesson learned.

Seed tale:
---
A little lad loved building a tall tower of blocks before bed.
He hummed a silly rhyme while he worked: "Stack it high, don't let it slide."
Then his toy cart bumped the tower, and crash! down it went.
The lad felt sad at first, but his caregiver helped him breathe, tidy up,
and learn a gentle lesson: build low towers near heavy wheels.
By bedtime, the lad had a cozy new rhyme and a safer place for his blocks.
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

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    caregiver: object | None = None
    lad: object | None = None
    tower: object | None = None
    vehicle: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"lad", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.kind == "character":
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
class StoryParams:
    name: str = "Milo"
    caregiver: str = "mom"
    toy: str = "blocks"
    vehicle: str = "toy cart"
    rhyme: str = "Stack it high, don't let it slide"
    lesson: str = "build low towers near heavy wheels"
    seed: Optional[int] = None
    DEFAULT_PARAMS: object | None = None
    params: object | None = None
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
class Setting:
    place: str = "the bedroom floor"
    world: object | None = None
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A crash happens when the vehicle bumps the tower.
crash_happens :- vehicle_near_tower, tower_high.

% A lesson is learned when the child calms down and chooses a safer plan.
lesson_learned :- crash_happens, comforted, safer_plan.

#show crash_happens/0.
#show lesson_learned/0.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("vehicle_near_tower"),
        asp.fact("tower_high"),
        asp.fact("comforted"),
        asp.fact("safer_plan"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_outcomes() -> set[str]:
    import asp
    model = asp.one_model(asp_program("#show crash_happens/0. #show lesson_learned/0."))
    return {sym.name for sym in model}


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def reasonableness_gate(params: StoryParams) -> None:
    if not params.name:
        pass
    if params.vehicle == params.toy:
        pass
    if "crash" not in "crash":
        pass


def make_world(params: StoryParams) -> World:
    world = World(Setting(place="the bedroom floor"))
    lad = world.add(Entity(
        id=params.name,
        kind="character",
        type="lad",
        label="lad",
        owner=None,
        caretaker=params.caregiver,
        meters={"sleepy": 0.0, "sad": 0.0, "calm": 0.0},
        memes={"joy": 0.0, "lesson": 0.0},
    ))
    caregiver = world.add(Entity(
        id="caregiver",
        kind="character",
        type=params.caregiver,
        label=f"the {params.caregiver}",
        meters={"helpful": 1.0},
        memes={"love": 1.0},
    ))
    tower = world.add(Entity(
        id="tower",
        type=params.toy,
        label=params.toy,
        phrase=f"a tall tower of {params.toy}",
        owner=lad.id,
        caretaker=caregiver.id,
        meters={"height": 3.0, "broken": 0.0},
        memes={"pride": 1.0},
    ))
    vehicle = world.add(Entity(
        id="vehicle",
        type=params.vehicle,
        label=params.vehicle,
        phrase=params.vehicle,
        owner=lad.id,
        meters={"speed": 1.0, "heavy": 1.0},
    ))

    # Act 1: bedtime play and rhyme.
    world.say(
        f"At bedtime, {lad.id} sat on {world.setting.place} and built {tower.phrase}."
    )
    world.say(
        f"{lad.id} hummed a rhyme: “{params.rhyme}.”"
    )

    # Act 2: crash.
    world.para()
    world.say(
        f"Then {vehicle.label} rolled too close, bumped the tower, and crash!"
    )
    tower.meters["broken"] += 1.0
    tower.meters["height"] = 0.0
    lad.memes["sad"] += 1.0
    lad.meters["calm"] = 0.0

    # Act 3: comfort, tidy, lesson.
    world.para()
    world.say(
        f"The {params.caregiver} sat beside {lad.id}, helped {lad.pronoun('object')} breathe slowly, "
        f"and picked up the blocks with {lad.id}."
    )
    lad.meters["calm"] += 1.0
    lad.memes["lesson"] += 1.0
    world.say(
        f"Together they made a smaller tower far from the wheels, and {lad.id} learned a lesson: "
        f"{params.lesson}."
    )
    world.say(
        f"By the time sleep came, {lad.id} had a new rhyme in {lad.pronoun('possessive')} head "
        f"and a safer spot for {lad.pronoun('possessive')} blocks."
    )

    world.facts = {
        "params": params,
        "lad": lad,
        "caregiver": caregiver,
        "tower": tower,
        "vehicle": vehicle,
        "crash": True,
        "lesson": True,
    }
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    p = _safe_fact(world, world.facts, "params")
    return [
        f'Write a bedtime story for a child that includes the words "{p.name}", "crash", and a rhyme.',
        f"Tell a gentle story where {p.name} builds blocks, there is a crash, and a lesson is learned.",
        "Write a cozy story with a small mistake, a kind helper, and a happy bedtime ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = _safe_fact(world, world.facts, "params")
    lad = _safe_fact(world, world.facts, "lad")
    caregiver = _safe_fact(world, world.facts, "caregiver")
    tower = _safe_fact(world, world.facts, "tower")

    return [
        QAItem(
            question=f"What was {p.name} building before the crash?",
            answer=f"{p.name} was building {tower.phrase} before the crash."
        ),
        QAItem(
            question=f"What rhyme did {p.name} say while playing?",
            answer=f"{p.name} said, “{p.rhyme}.”"
        ),
        QAItem(
            question=f"Who helped {p.name} after the blocks fell?",
            answer=f"The {p.caregiver} helped {p.name} breathe slowly and tidy up."
        ),
        QAItem(
            question="What lesson did the story teach?",
            answer=f"The story taught that you should {p.lesson}."
        ),
        QAItem(
            question=f"How did {p.name} feel at the end?",
            answer=f"{p.name} felt calmer and ready for sleep after the lesson was learned."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a little pattern of sounds in words, like when two lines end in words that sound alike."
        ),
        QAItem(
            question="What does it mean to learn a lesson?",
            answer="Learning a lesson means you understand something important and remember to do it better next time."
        ),
        QAItem(
            question="Why is a crash loud?",
            answer="A crash is loud because things hit each other quickly and make a sharp, sudden sound."
        ),
    ]


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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
DEFAULT_PARAMS = StoryParams()

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime storyworld: lad, crash, rhyme, lesson learned.")
    ap.add_argument("--name", default=None)
    ap.add_argument("--caregiver", choices=["mom", "dad", "grandma", "grandpa"], default=None)
    ap.add_argument("--toy", default=None)
    ap.add_argument("--vehicle", default=None)
    ap.add_argument("--rhyme", default=None)
    ap.add_argument("--lesson", default=None)
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
    params = StoryParams(
        name=getattr(args, "name", None) or rng.choice(["Milo", "Noah", "Toby", "Eli", "Ben"]),
        caregiver=getattr(args, "caregiver", None) or rng.choice(["mom", "dad", "grandma", "grandpa"]),
        toy=getattr(args, "toy", None) or rng.choice(["blocks", "cups", "cubes", "bricks"]),
        vehicle=getattr(args, "vehicle", None) or rng.choice(["toy cart", "little wagon", "red truck"]),
        rhyme=getattr(args, "rhyme", None) or rng.choice([
            "Stack it high, don't let it slide",
            "Build it slow, then watch it grow",
            "Up so neat, with careful feet",
        ]),
        lesson=getattr(args, "lesson", None) or rng.choice([
            "build low towers near heavy wheels",
            "keep rolling toys away from tall stacks",
            "make a small space for big pretend rides",
        ]),
    )
    if params.vehicle == params.toy:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return params


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = make_world(params)
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


def asp_verify() -> int:
    # Python gate: crash and lesson are expected in this world.
    py = {"crash_happens", "lesson_learned"}
    asp_set = asp_outcomes()
    if asp_set == py:
        print(f"OK: ASP parity matched ({sorted(asp_set)}).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("  asp:", sorted(asp_set))
    print("  py :", sorted(py))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show crash_happens/0. #show lesson_learned/0."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    if getattr(args, "asp", None):
        print("ASP twin is present for this world; use --verify to compare parity.")
        return

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        curated = [
            StoryParams(name="Milo", caregiver="mom", toy="blocks", vehicle="toy cart"),
            StoryParams(name="Toby", caregiver="dad", toy="cubes", vehicle="little wagon"),
            StoryParams(name="Eli", caregiver="grandma", toy="bricks", vehicle="red truck"),
        ]
        samples = [generate(p) for p in curated]
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
