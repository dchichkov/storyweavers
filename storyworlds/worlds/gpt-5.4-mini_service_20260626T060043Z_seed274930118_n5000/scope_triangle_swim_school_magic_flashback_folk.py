#!/usr/bin/env python3
"""
storyworlds/worlds/scope_triangle_swim_school_magic_flashback_folk.py
=====================================================================

A small story world for a folk-tale style swim-school story with a magical
triangle scope and a brief flashback that helps a child find courage.

The world is intentionally tiny and constraint-checked:
- one child at swim school
- one teacher
- one small magical object shaped like a triangle scope
- one worry about deep water
- one flashback that turns fear into courage
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
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "teacher"}
        male = {"boy", "father", "man"}
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
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    world: object | None = None
    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
    name: str = "Mira"
    gender: str = "girl"
    teacher: str = "teacher"
    trait: str = "curious"
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


NAMES_GIRL = ["Mira", "Lina", "Tia", "Sana", "Rosa", "Nina"]
NAMES_BOY = ["Oren", "Eli", "Tavi", "Nico", "Rafi", "Milo"]
TRAITS = ["curious", "brave", "gentle", "shy", "bright", "patient"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Folk-tale swim school story with magic, flashback, scope, and triangle."
    )
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--teacher", choices=["teacher"])
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
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    return StoryParams(
        name=name,
        gender=gender,
        teacher=getattr(args, "teacher", None) or "teacher",
        trait=getattr(args, "trait", None) or rng.choice(TRAITS),
    )


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("place", "swim_school"),
        asp.fact("child_type", "girl"),
        asp.fact("child_type", "boy"),
        asp.fact("teacher_type", "teacher"),
        asp.fact("object", "scope"),
        asp.fact("object", "triangle"),
        asp.fact("has_feature", "magic"),
        asp.fact("has_feature", "flashback"),
    ])


ASP_RULES = r"""
% A valid story needs a child, a swim-school setting, a magical object,
% and a flashback that changes fear into courage.
needs_story(swim_school, magic, flashback).

story_ready :- place(swim_school), has_feature(magic), has_feature(flashback), object(scope), object(triangle).
#show story_ready/0.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show story_ready/0."))
    ok = any(sym.name == "story_ready" for sym in model)
    if ok:
        print("OK: ASP program produces story_ready.")
        return 0
    print("MISMATCH: ASP program did not produce story_ready.")
    return 1


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a triangle?",
            answer="A triangle is a shape with three straight sides and three corners.",
        ),
        QAItem(
            question="What is a scope?",
            answer="A scope is a tool used for looking closely or looking far away, like a little viewer.",
        ),
        QAItem(
            question="What does magic mean in a folk tale?",
            answer="Magic in a folk tale means something strange and wonderful can happen to help the story move forward.",
        ),
        QAItem(
            question="What is swim school for?",
            answer="Swim school is a place where children practice floating, kicking, and learning to swim safely.",
        ),
    ]


def _say_intro(world: World, child: Entity, teacher: Entity) -> None:
    world.say(
        f"Once, at the swim school by the bright blue water, there lived a little {child.pronoun('subject')} named {child.id}."
    )
    world.say(
        f"{child.id} was a {child.traits[0]} child who loved to watch the ripples, and {teacher.pronoun().capitalize()} taught the children to float like reeds on a pond."
    )


def _say_problem(world: World, child: Entity, teacher: Entity, scope: Entity) -> None:
    child.memes["fear"] += 1
    world.para()
    world.say(
        f"One morning, {child.id} stood at the edge of the deep lane and felt the water look wider than a barn door."
    )
    world.say(
        f"{child.pronoun().capitalize()} wanted to swim, but {child.pronoun('possessive')} feet would not move, and {child.pronoun('possessive')} heart thumped hard as a drum."
    )
    world.say(
        f"Then {teacher.pronoun().capitalize()} lifted a tiny triangle scope, carved with silver marks, and said it had a magic eye for brave thoughts."
    )
    scope.carried_by = child.id
    scope.meters["magic"] = 1
    child.memes["hope"] += 1


def _say_flashback(world: World, child: Entity, teacher: Entity) -> None:
    child.memes["flashback"] += 1
    child.memes["fear"] = max(0.0, child.memes["fear"] - 1)
    child.memes["courage"] += 1
    world.para()
    world.say(
        f"When {child.id} peered through the triangle scope, the glass grew misty, and a flashback came like a song from another day."
    )
    world.say(
        f"{child.id} remembered standing in shallow water, first learning to kick while {teacher.pronoun('subject')} clapped soft as rain on a roof."
    )
    world.say(
        f"In that old memory, {child.id} had once floated for three whole breaths, and the remembering made {child.pronoun('possessive')} knees stop shaking."
    )


def _say_turn_and_end(world: World, child: Entity, teacher: Entity, scope: Entity) -> None:
    world.para()
    child.memes["joy"] += 1
    child.meters["swim"] = 1
    world.say(
        f"So {child.id} tucked the triangle scope under one arm, took a small breath, and slipped into the water like a leaf landing in a brook."
    )
    world.say(
        f"{child.id} kicked once, then twice, and the magic of the scope seemed to whisper, 'You have done this before.'"
    )
    world.say(
        f"By the end, {child.id} was gliding across the lane while {teacher.pronoun().capitalize()} smiled, and the triangle scope flashed gold in the sun beside the pool."
    )


def tell(params: StoryParams) -> World:
    world = World(place="swim school")
    child = world.add(
        Entity(
            id=params.name,
            kind="character",
            type=params.gender,
            traits=[params.trait, "little"],
        )
    )
    teacher = world.add(
        Entity(
            id="Teacher",
            kind="character",
            type="teacher",
            traits=["kind", "patient"],
        )
    )
    scope = world.add(
        Entity(
            id="scope",
            kind="thing",
            type="thing",
            label="triangle scope",
            phrase="a tiny triangle scope with a magic eye",
            owner=teacher.id,
        )
    )
    triangle = world.add(
        Entity(
            id="triangle",
            kind="thing",
            type="thing",
            label="triangle charm",
            phrase="a small triangle charm",
            owner=scope.id,
        )
    )

    _say_intro(world, child, teacher)
    _say_problem(world, child, teacher, scope)
    _say_flashback(world, child, teacher)
    _say_turn_and_end(world, child, teacher, scope)

    world.facts.update(
        child=child,
        teacher=teacher,
        scope=scope,
        triangle=triangle,
        place="swim_school",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    child = _safe_fact(world, world.facts, "child")
    return [
        f"Write a folk-tale style story set in swim school about {child.id}, a magic triangle scope, and a flashback that helps with fear.",
        "Tell a gentle children's story where a child at swim school uses magic and remembers an earlier lesson to become brave.",
        "Write a short story that includes the words scope and triangle and ends with a child finally swimming.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child: Entity = _safe_fact(world, world.facts, "child")
    teacher: Entity = _safe_fact(world, world.facts, "teacher")
    return [
        QAItem(
            question=f"Why did {child.id} feel scared at swim school?",
            answer=f"{child.id} felt scared because the deep lane looked wider than a barn door, so the water seemed hard to cross.",
        ),
        QAItem(
            question=f"What helped {child.id} remember being brave?",
            answer=f"A tiny triangle scope with a magic eye helped {child.id} see a flashback of an earlier lesson, when {teacher.pronoun('subject')} taught {child.pronoun('object')} to float and kick.",
        ),
        QAItem(
            question=f"What changed after the flashback?",
            answer=f"After the flashback, {child.id}'s fear grew smaller and courage grew bigger, so {child.id} could slip into the water and swim.",
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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        out.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
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


def valid_combo() -> bool:
    return True


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show story_ready/0."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show story_ready/0."))
        print("story_ready" if any(sym.name == "story_ready" for sym in model) else "no story_ready")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        params = [
            StoryParams(name="Mira", gender="girl", trait="curious"),
            StoryParams(name="Oren", gender="boy", trait="brave"),
            StoryParams(name="Lina", gender="girl", trait="gentle"),
        ]
        samples = [generate(p) for p in params]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
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
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
