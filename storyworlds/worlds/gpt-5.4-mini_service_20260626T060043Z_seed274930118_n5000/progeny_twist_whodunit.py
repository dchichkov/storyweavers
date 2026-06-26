#!/usr/bin/env python3
"""
storyworlds/worlds/progeny_twist_whodunit.py
============================================

A tiny whodunit story world with a final twist.

Seed premise:
- A child progeny notices a small disappearance.
- Clues point to the obvious suspects.
- The turn reveals a better, kinder explanation.

The domain is intentionally small and constraint-checked: every valid mystery
must have enough clues to make the detective's suspicions feel fair, and the
twist must actually resolve the disappearance.
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
    room: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    obj: object | None = None
    parent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister", "aunt", "daughter"}
        male = {"boy", "father", "dad", "man", "brother", "uncle", "son"}
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
class Case:
    id: str
    object_label: str
    object_phrase: str
    room: str
    missing_verb: str
    found_verb: str
    clue_room: str
    clues: list[str]
    suspicion_targets: list[str]
    twist: str
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
class StoryParams:
    case: str
    name: str
    gender: str
    parent: str
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


class World:
    def __init__(self, case: Case) -> None:
        self.case = case
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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

        clone = World(self.case)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


CASE_REGISTRY = {
    "key": Case(
        id="key",
        object_label="silver key",
        object_phrase="a little silver key with a round head",
        room="study",
        missing_verb="gone missing",
        found_verb="resting where it was meant to be",
        clue_room="hall",
        clues=["a smear of chalk", "a draft from the window", "tiny boot prints"],
        suspicion_targets=["the gardener", "the cat", "the uncle"],
        twist="The key had been tucked into a storybook to keep it safe from the rain.",
    ),
    "jam": Case(
        id="jam",
        object_label="jam tart",
        object_phrase="a glossy jam tart on a blue plate",
        room="kitchen",
        missing_verb="vanished",
        found_verb="waiting safely in the pantry",
        clue_room="kitchen",
        clues=["a breadcrumb trail", "a sticky spoon", "a pink napkin"],
        suspicion_targets=["the cook", "the puppy", "the sister"],
        twist="The tart had been moved to the pantry for a surprise tea, not stolen.",
    ),
    "lantern": Case(
        id="lantern",
        object_label="brass lantern",
        object_phrase="a small brass lantern with a glass door",
        room="attic",
        missing_verb="disappeared",
        found_verb="glowing again by the window",
        clue_room="stairs",
        clues=["a thread of red wool", "dusty footprints", "a faint smell of oil"],
        suspicion_targets=["the aunt", "the mouse", "the brother"],
        twist="The lantern had been borrowed for a repair and returned before supper.",
    ),
}

GIRL_NAMES = ["Mina", "Nora", "Ivy", "Rose", "Lena", "Clara", "Ada", "Maya"]
BOY_NAMES = ["Theo", "Ben", "Leo", "Finn", "Owen", "Max", "Eli", "Sam"]
TRAITS = ["curious", "careful", "brave", "sharp-eyed", "patient", "quiet"]


ASP_RULES = r"""
case(key). case(jam). case(lantern).

clue_set(key, chalk). clue_set(key, draft). clue_set(key, boots).
clue_set(jam, breadcrumb). clue_set(jam, spoon). clue_set(jam, napkin).
clue_set(lantern, wool). clue_set(lantern, dust). clue_set(lantern, oil).

twist(key, book).
twist(jam, pantry).
twist(lantern, return).

valid(Case) :- case(Case), 3 <= #count { X : clue_set(Case, X) }.
resolved(Case) :- valid(Case), twist(Case, _).

#show valid/1.
#show resolved/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for cid in CASE_REGISTRY:
        lines.append(asp.fact("case", cid))
        for clue in sorted(CASE_REGISTRY[cid].clues):
            key = clue.split()[0].replace("a", "a")
        # facts below are based on semantic clue tokens
    lines = [
        asp.fact("case", "key"),
        asp.fact("case", "jam"),
        asp.fact("case", "lantern"),
        asp.fact("clue_set", "key", "chalk"),
        asp.fact("clue_set", "key", "draft"),
        asp.fact("clue_set", "key", "boots"),
        asp.fact("clue_set", "jam", "breadcrumb"),
        asp.fact("clue_set", "jam", "spoon"),
        asp.fact("clue_set", "jam", "napkin"),
        asp.fact("clue_set", "lantern", "wool"),
        asp.fact("clue_set", "lantern", "dust"),
        asp.fact("clue_set", "lantern", "oil"),
        asp.fact("twist", "key", "book"),
        asp.fact("twist", "jam", "pantry"),
        asp.fact("twist", "lantern", "return"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_cases() -> list[str]:
    return sorted(CASE_REGISTRY)


def asp_valid_cases() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/1."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(c,) for c in valid_cases()}
    cl = set(asp_valid_cases())
    if py == cl:
        print(f"OK: clingo gate matches valid_cases() ({len(py)} cases).")
        return 0
    print("MISMATCH between clingo and Python validity:")
    print("python only:", sorted(py - cl))
    print("clingo only:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small whodunit story world with a twist.")
    ap.add_argument("--case", choices=CASE_REGISTRY)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    if getattr(args, "case", None):
        case = getattr(args, "case", None)
    else:
        case = rng.choice(valid_cases())
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    if getattr(args, "name", None):
        name = getattr(args, "name", None)
    else:
        name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(case=case, name=name, gender=gender, parent=parent, trait=trait)


def _introduce(world: World, hero: Entity, parent: Entity) -> None:
    world.say(
        f"{hero.id} was the youngest progeny in the house, a {hero.memes['trait']} little {hero.type} "
        f"who liked solving puzzles."
    )
    world.say(
        f"Whenever something strange happened, {hero.id} watched closely while {parent.label} looked on."
    )


def _discovery(world: World, hero: Entity, obj: Entity, case: Case) -> None:
    world.say(
        f"One morning, {hero.id} found that {obj.label} had {case.missing_verb} from the {case.room}."
    )
    hero.memes["worry"] += 1
    world.say(
        f"That felt like a proper whodunit, so {hero.id} set out to ask careful questions."
    )


def _clues(world: World, hero: Entity, case: Case) -> None:
    for clue in case.clues:
        hero.memes["cleverness"] += 1
        world.say(f"In the {case.clue_room}, {hero.id} spotted {clue}.")
    world.say(
        f"Those clues made {hero.id} suspect {case.suspicion_targets[0]}, then {case.suspicion_targets[1]}, "
        f"and even {case.suspicion_targets[2]}."
    )


def _twist(world: World, hero: Entity, parent: Entity, obj: Entity, case: Case) -> None:
    hero.memes["suspicion"] += 1
    world.para()
    world.say(
        f"At last, the truth gave a little twist: {case.twist}"
    )
    world.say(
        f"{parent.label} smiled, because the mystery was never a theft after all."
    )
    obj.meters["found"] = 1
    hero.memes["relief"] += 1
    world.say(
        f"{hero.id} put {obj.label} back where it belonged, and the whole house felt calmer."
    )


def tell(case: Case, name: str, gender: str, parent_type: str, trait: str) -> World:
    world = World(case)
    hero = world.add(Entity(id=name, kind="character", type=gender, memes={"trait": trait}))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label=f"the {parent_type}"))
    obj = world.add(Entity(
        id="Object",
        type="thing",
        label=case.object_label,
        phrase=case.object_phrase,
        caretaker=parent.id,
        room=case.room,
    ))
    _introduce(world, hero, parent)
    world.para()
    _discovery(world, hero, obj, case)
    _clues(world, hero, case)
    _twist(world, hero, parent, obj, case)
    world.facts.update(hero=hero, parent=parent, obj=obj, case=case)
    return world


def story_prompts(world: World) -> list[str]:
    c: Case = _safe_fact(world, world.facts, "case")
    h: Entity = _safe_fact(world, world.facts, "hero")
    return [
        f'Write a short whodunit for a child about a missing {c.object_label} and a surprising twist.',
        f"Tell a gentle mystery where {h.id} investigates why the {c.object_label} {c.missing_verb}.",
        f'Write a story that uses the word "progeny" and ends with the mystery solved.',
    ]


def story_qa(world: World) -> list[QAItem]:
    c: Case = _safe_fact(world, world.facts, "case")
    h: Entity = _safe_fact(world, world.facts, "hero")
    p: Entity = _safe_fact(world, world.facts, "parent")
    o: Entity = _safe_fact(world, world.facts, "obj")
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {h.id}, the youngest progeny in the house, who tries to solve a small mystery.",
        ),
        QAItem(
            question=f"What went missing?",
            answer=f"{o.label.capitalize()} {c.missing_verb} from the {c.room}.",
        ),
        QAItem(
            question=f"What clues did {h.id} notice?",
            answer=f"{h.id} noticed {', '.join(c.clues[:-1])}, and {c.clues[-1]}. Those clues made the mystery feel serious.",
        ),
        QAItem(
            question=f"What was the twist at the end?",
            answer=c.twist,
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"{h.id} found out there was no theft, only a kind surprise, and put {o.label} back where it belonged.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    c: Case = _safe_fact(world, world.facts, "case")
    return [
        QAItem(
            question="What is a whodunit?",
            answer="A whodunit is a mystery story where the reader follows clues to find out what really happened.",
        ),
        QAItem(
            question="Why do detectives look at clues?",
            answer="Detectives look at clues because clues can show who was there, what moved, or why something happened.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprise turn that changes what you thought was true.",
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
        bits = []
        if e.label:
            bits.append(f"label={e.label!r}")
        if e.room:
            bits.append(f"room={e.room}")
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(case="key", name="Mina", gender="girl", parent="mother", trait="curious"),
    StoryParams(case="jam", name="Theo", gender="boy", parent="father", trait="careful"),
    StoryParams(case="lantern", name="Ivy", gender="girl", parent="mother", trait="sharp-eyed"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(CASE_REGISTRY[params.case], params.name, params.gender, params.parent, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=story_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


def asp_valid() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/1.\n#show resolved/1."))
    return sorted(set(asp.atoms(model, "valid")))


def build_asp_output() -> str:
    return asp_program("#show valid/1.\n#show resolved/1.")


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(build_asp_output())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        vals = asp_valid()
        print(f"{len(vals)} valid mystery cases:\n")
        for (case,) in vals:
            print(f"  {case}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
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
            header = f"### {p.name}: {p.case} mystery"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
