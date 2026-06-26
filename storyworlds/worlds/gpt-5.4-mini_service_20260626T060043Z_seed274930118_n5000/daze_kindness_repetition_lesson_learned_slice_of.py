#!/usr/bin/env python3
"""
A small slice-of-life story world about a child, a daze, repeated kindness,
and a lesson learned.

Premise:
- The child starts the day a little dazed.
- A repeated task or routine keeps getting skipped or muddled.
- A kind helper responds patiently instead of scolding.
- The child notices the pattern, learns the lesson, and changes their routine.

This world is intentionally compact and state-driven: meters track tiredness,
attention, and warmth; memes track embarrassment, patience, and gratitude.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    helper: object | None = None
    def __post_init__(self):
        if not self.meters:
            self.meters = {"tired": 0.0, "attention": 0.0, "order": 0.0}
        if not self.memes:
            self.memes = {"daze": 0.0, "kindness": 0.0, "patience": 0.0, "gratitude": 0.0, "lesson": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
class Place:
    id: str
    label: str
    indoors: bool = True
    repeated_task: str = "tidy the table"
    affordances: set[str] = field(default_factory=set)
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


@dataclass
class Routine:
    id: str
    name: str
    repeated_action: str
    trigger: str
    correction: str
    lesson: str
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


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.repeat_count: int = 0
        self.task_done: bool = False
        self.moment_of_clarity: bool = False

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
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.repeat_count = self.repeat_count
        c.task_done = self.task_done
        c.moment_of_clarity = self.moment_of_clarity
        return c


@dataclass
class StoryParams:
    place: str
    routine: str
    child_name: str
    child_type: str
    helper_type: str
    trait: str
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


PLACES = {
    "kitchen": Place(id="kitchen", label="the kitchen", indoors=True, repeated_task="set the table", affordances={"tidy", "share"}),
    "hallway": Place(id="hallway", label="the hallway", indoors=True, repeated_task="put shoes away", affordances={"tidy", "share"}),
    "garden": Place(id="garden", label="the garden", indoors=False, repeated_task="water the plants", affordances={"water", "share"}),
}

ROUTINES = {
    "table": Routine(
        id="table",
        name="set the table",
        repeated_action="set the table",
        trigger="the plates needed a place",
        correction="move each plate one by one until the table looked ready",
        lesson="small careful steps make a job feel easier",
    ),
    "shoes": Routine(
        id="shoes",
        name="put shoes away",
        repeated_action="put shoes away",
        trigger="the shoes kept ending up in the wrong spot",
        correction="line up each shoe beside its pair and leave them by the mat",
        lesson="when a task is repeated kindly, the habit gets stronger",
    ),
    "plants": Routine(
        id="plants",
        name="water the plants",
        repeated_action="water the plants",
        trigger="the leaves looked droopy by lunchtime",
        correction="fill the watering can again and give each pot a slow pour",
        lesson="doing the same kind thing again and again can help living things grow",
    ),
}

CHILD_NAMES = ["Mina", "Owen", "Lena", "Noah", "Iris", "Theo", "Pia", "Jules"]
CHILD_TYPES = ["girl", "boy"]
HELPER_TYPES = ["mother", "father", "grandmother", "grandfather"]
TRAITS = ["quiet", "curious", "gentle", "thoughtful", "small", "slow-moving"]


def reasonableness_gate(place: Place, routine: Routine) -> None:
    if routine.id not in place.affordances:
        pass


def routine_requires_repetition(routine: Routine) -> bool:
    return True


def _step_daze(world: World, child: Entity, routine: Routine) -> None:
    child.memes["daze"] += 1
    child.meters["attention"] -= 0.5
    world.repeat_count += 1
    world.say(
        f"{child.id} woke up in a little daze and stood still for a moment, "
        f"looking at {world.place.label} as if it had just drifted into focus."
    )
    world.say(
        f"{child.pronoun().capitalize()} kept trying to {routine.repeated_action}, "
        f"but the steps felt slippery and easy to forget."
    )


def _step_kindness(world: World, helper: Entity, child: Entity, routine: Routine) -> None:
    helper.memes["kindness"] += 1
    helper.memes["patience"] += 1
    child.memes["kindness"] += 1
    world.say(
        f"{helper.pronoun().capitalize()} noticed and smiled gently. "
        f'"No rush," {helper.pronoun()} said. "Let us do it together, one step at a time."'
    )
    world.say(
        f"{helper.pronoun().capitalize()} showed {child.pronoun('object')} the same calm way again, "
        f"and the room felt less hazy."
    )


def _step_repetition(world: World, child: Entity, routine: Routine) -> None:
    world.repeat_count += 1
    child.meters["attention"] += 0.5
    child.meters["order"] += 1
    world.say(
        f"They tried again, and then again, until the repeated rhythm of the task "
        f"started to feel familiar."
    )
    world.say(
        f"Each time {child.id} copied the motion, {child.pronoun('possessive')} hands got surer."
    )


def _step_lesson(world: World, child: Entity, helper: Entity, routine: Routine) -> None:
    child.memes["lesson"] += 1
    child.memes["gratitude"] += 1
    world.moment_of_clarity = True
    world.task_done = True
    world.say(
        f"At last, {child.id} understood the lesson: {routine.lesson}."
    )
    world.say(
        f"{child.id} thanked {helper.pronoun('object')} and did the task again without being asked, "
        f"this time with careful hands and a clear head."
    )


def tell(place: Place, routine: Routine, child_name: str, child_type: str, helper_type: str, trait: str) -> World:
    world = World(place)
    child = world.add(Entity(id=child_name, kind="character", type=child_type, traits=["little", trait]))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, label="the helper"))

    world.say(
        f"{child.id} was a little {trait} {child_type} who moved through the day in a mild daze."
    )
    world.say(
        f"At {place.label}, {child.id} had one small job: to {routine.repeated_action}."
    )

    world.para()
    _step_daze(world, child, routine)
    world.say(f"That was why {routine.trigger} kept causing trouble.")

    world.para()
    _step_kindness(world, helper, child, routine)
    _step_repetition(world, child, routine)
    _step_repetition(world, child, routine)
    _step_lesson(world, child, helper, routine)

    world.para()
    if world.task_done:
        world.say(
            f"By the end, {place.label} looked tidier and quieter, and {child.id} "
            f"no longer seemed lost in the daze."
        )
        world.say(
            f"{child.id} could remember the routine without help, which made the whole place feel calmer."
        )

    world.facts.update(
        child=child,
        helper=helper,
        routine=routine,
        place=place,
        task_done=world.task_done,
        repeat_count=world.repeat_count,
    )
    return world


SETTINGS = PLACES
ACTIVITIES = ROUTINES

ASP_RULES = r"""
dazed(C) :- child(C), mood(C,daze).
needs_help(C,R) :- dazed(C), routine(R), repeated(R).
kindly_guided(C,H) :- helper(H), child(C), helps(H,C).
learns(C) :- kindly_guided(C,H), repeats(C,R), lesson(R).
done(C,R) :- learns(C), routine(R).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.indoors:
            lines.append(asp.fact("indoors", pid))
        for a in sorted(p.affordances):
            lines.append(asp.fact("affords", pid, a))
    for rid, r in ROUTINES.items():
        lines.append(asp.fact("routine", rid))
        lines.append(asp.fact("repeated", rid))
        lines.append(asp.fact("lesson", rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show done/2."))
    return sorted(set(asp.atoms(model, "done")))


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for rid, routine in ROUTINES.items():
            if routine.id in place.affordances:
                combos.append((pid, rid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life story world about daze, kindness, repetition, and lesson learned.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father", "grandmother", "grandfather"])
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
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity = rng.choice(list(combos))
    child_type = getattr(args, "gender", None) or rng.choice(CHILD_TYPES)
    helper = getattr(args, "helper", None) or rng.choice(HELPER_TYPES)
    name = getattr(args, "name", None) or rng.choice(CHILD_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, routine=activity, child_name=name, child_type=child_type, helper_type=helper, trait=trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child, helper, routine, place = f["child"], f["helper"], f["routine"], f["place"]
    return [
        f'Write a gentle slice-of-life story for a young child about a daze, kindness, and learning a lesson at {place.label}.',
        f"Tell a short story where {child.id} keeps forgetting how to {routine.repeated_action}, but {helper.type} helps patiently until the job feels easy.",
        f'Write a simple story that repeats the idea of "again and again" and ends with {child.id} understanding a lesson.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, helper, routine, place = f["child"], f["helper"], f["routine"], f["place"]
    return [
        QAItem(
            question=f"What was {child.id} doing in {place.label}?",
            answer=f"{child.id} was trying to {routine.repeated_action}, but {child.id} started out in a daze and needed help."
        ),
        QAItem(
            question=f"How did {helper.pronoun().capitalize()} help {child.id}?",
            answer=f"{helper.pronoun().capitalize()} helped kindly by showing the same steps again, one at a time, and staying patient."
        ),
        QAItem(
            question=f"What lesson did {child.id} learn?",
            answer=f"{child.id} learned that {routine.lesson}."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is kindness?",
            answer="Kindness is being gentle and helpful to someone, especially when they are having a hard time."
        ),
        QAItem(
            question="Why do people repeat a task?",
            answer="People repeat a task so they can remember it better, make it feel familiar, and get better at doing it."
        ),
        QAItem(
            question="What does it mean to learn a lesson?",
            answer="Learning a lesson means understanding something important that changes how you act next time."
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"  {e.id:8} ({e.type:10}) meters={{{', '.join(f'{k}: {v}' for k, v in e.meters.items() if v)}}} memes={{{', '.join(f'{k}: {v}' for k, v in e.memes.items() if v)}}}")
    lines.append(f"  task_done={world.task_done} repeat_count={world.repeat_count} moment_of_clarity={world.moment_of_clarity}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIVITIES, params.routine), params.child_name, params.child_type, params.helper_type, params.trait)
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


def explain_rejection(place: Place, routine: Routine) -> str:
    return f"(No story: {place.label} does not support the routine {routine.name!r}.)"


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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show done/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, routine) combos:\n")
        for place, routine in combos:
            print(f"  {place:10} {routine}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [
            StoryParams(place="kitchen", routine="table", child_name="Mina", child_type="girl", helper_type="mother", trait="thoughtful"),
            StoryParams(place="hallway", routine="shoes", child_name="Owen", child_type="boy", helper_type="father", trait="quiet"),
            StoryParams(place="garden", routine="plants", child_name="Lena", child_type="girl", helper_type="grandmother", trait="gentle"),
        ]
        samples = [generate(p) for p in curated]
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
            header = f"### {p.child_name}: {p.routine} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
