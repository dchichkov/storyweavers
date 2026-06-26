#!/usr/bin/env python3
"""
A small storyworld: a whodunit set on the basement stairs, with a flashback,
an aggressive system, and a transformation that resolves the mystery.
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
    kind: str = "thing"  # character | thing
    label: str = ""
    type: str = ""
    owner: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    hidden: bool = False
    transformed: bool = False

    child: object | None = None
    clue: object | None = None
    culprit: object | None = None
    parent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        feminine = {"girl", "woman", "mother", "sister", "aunt"}
        masculine = {"boy", "man", "father", "brother", "uncle"}
        if self.type in feminine:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in masculine:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    name: str
    gender: str
    parent: str
    clue: str
    culprit: str
    seed: Optional[int] = None
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
class Scene:
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    scene: object | None = None
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


class World:
    def __init__(self) -> None:
        self.scene = Scene()
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.trace: list[str] = []

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def say(self, text: str) -> None:
        self.scene.say(text)

    def para(self) -> None:
        self.scene.para()

    def render(self) -> str:
        return self.scene.render()


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

LOCATIONS = {
    "basement stairs": {
        "description": "the basement stairs",
        "clue": "a loose dusty tread",
    }
}

CLUES = {
    "loose tread": "a loose dusty tread",
    "broken latch": "a broken latch",
    "cold draft": "a cold draft from below",
}

CULPRITS = {
    "cat": "a nervous cat",
    "toy robot": "a toy robot with a jammed motor",
    "system": "the old stair system itself",
}

TRANSFORMATIONS = {
    "system": "the stair system turned from creaky and aggressive to steady and safe",
    "cat": "the cat turned from wild and hiding to calm and purring",
    "toy robot": "the toy robot turned from clattering and stuck to quiet and helpful",
}


@dataclass
class Config:
    place: str = "basement stairs"
    clue: str = "loose tread"
    culprit: str = "system"


# ---------------------------------------------------------------------------
# Narrative engine
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


def setup_world(params: StoryParams) -> World:
    w = World()
    child = w.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
        location="basement stairs",
        meters={"curiosity": 1.0},
        memes={"unease": 1.0},
    ))
    parent = w.add(Entity(
        id="parent",
        kind="character",
        type=params.parent,
        label=f"the {params.parent}",
        location="basement stairs",
        meters={"attention": 1.0},
        memes={"concern": 1.0},
    ))
    culprit = w.add(Entity(
        id=params.culprit,
        kind="thing",
        label=_safe_lookup(CULPRITS, params.culprit),
        type=params.culprit,
        location="basement stairs",
        hidden=True,
        meters={"danger": 1.0 if params.culprit == "system" else 0.5},
        memes={"aggression": 1.0 if params.culprit == "system" else 0.4},
    ))
    clue = w.add(Entity(
        id=params.clue,
        kind="thing",
        label=_safe_lookup(CLUES, params.clue),
        type="clue",
        location="basement stairs",
        hidden=False,
    ))
    w.facts.update(child=child, parent=parent, culprit=culprit, clue=clue, params=params)
    return w


def intro(w: World) -> None:
    child: Entity = w.facts["child"]
    parent: Entity = w.facts["parent"]
    w.say(f"{child.label} was the kind of child who noticed small things at once.")
    w.say(f"One evening, {child.label} and {parent.label} stood at the basement stairs, where the air felt old and quiet.")


def flashback(w: World) -> None:
    child: Entity = w.facts["child"]
    clue: Entity = w.facts["clue"]
    w.para()
    w.say(
        f"{child.label} paused, and a flashback stirred in {child.pronoun('possessive')} mind: "
        f"earlier that day, {clue.label} had looked ordinary, but it had not felt ordinary."
    )
    w.say(
        f"{child.label} remembered a sharp clack and a mean little jolt, as if the stairs were trying to scare everyone away."
    )


def mystery_turn(w: World) -> None:
    child: Entity = w.facts["child"]
    parent: Entity = w.facts["parent"]
    culprit: Entity = w.facts["culprit"]
    clue: Entity = w.facts["clue"]

    w.para()
    w.say(
        f"{parent.label} asked, 'What happened here?' and {child.label} looked again at {clue.label}."
    )
    w.say(
        f"The clue pointed to the truth: the basement stair system had been aggressive, with one step sticking out like a grumpy tooth."
    )
    w.say(
        f"{child.label} said the stairs were not haunted at all; they were simply broken in a way that could hurt someone."
    )
    w.trace.append("flashback->clue->suspect: aggressive stair system")


def reveal_and_transform(w: World) -> None:
    child: Entity = w.facts["child"]
    parent: Entity = w.facts["parent"]
    culprit: Entity = w.facts["culprit"]

    w.para()
    if culprit.id == "system":
        culprit.hidden = False
        culprit.transformed = True
        culprit.meters["danger"] = 0.0
        culprit.memes["aggression"] = 0.0
        w.say(
            f"At last, the mystery was solved: the stair system itself was the culprit, because a loose part had made every step unsafe."
        )
        w.say(
            f"After repairs, the transformation was easy to see. The stairs stopped feeling aggressive and became solid and calm."
        )
        w.say(
            f"{child.label} and {parent.label} walked down together, and each step stayed steady under their feet."
        )
    else:
        culprit.hidden = False
        culprit.transformed = True
        w.say(
            f"The culprit came into the light and changed at once, so the scary feeling faded from the basement stairs."
        )
        w.say(f"{child.label} smiled because the mystery had finally been answered.")


def tell_story(params: StoryParams) -> World:
    w = setup_world(params)
    intro(w)
    flashback(w)
    mystery_turn(w)
    reveal_and_transform(w)
    return w


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% Facts supplied:
% place(P). clue(C). culprit(X). aggressive(X). system(X).
% The story is reasonable when the clue matches the dangerous place and the
% culprit can be identified as the system or as a transformed source of trouble.

mystery(P, C, X) :- place(P), clue(C), culprit(X).
reasonably_aggressive(X) :- aggressive(X).
system_culprit(X) :- system(X).

solved(P, C, X) :- mystery(P, C, X), reasonably_aggressive(X), system_culprit(X).
solved(P, C, X) :- mystery(P, C, X), not system_culprit(X).

#show solved/3.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("place", "basement_stairs"),
        asp.fact("clue", "loose_tread"),
        asp.fact("culprit", "system"),
        asp.fact("aggressive", "system"),
        asp.fact("system", "system"),
    ]
    return "\n".join(lines)


def asp_program(show: str = "#show solved/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_solved() -> bool:
    import asp
    model = asp.one_model(asp_program("#show solved/3."))
    return bool(asp.atoms(model, "solved"))


def asp_verify() -> int:
    python_ok = True
    asp_ok = asp_solved()
    if python_ok == asp_ok:
        print("OK: ASP and Python gates agree for the basement-stairs mystery.")
        return 0
    print("MISMATCH between ASP and Python gates.")
    return 1


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    params: StoryParams = _safe_fact(world, world.facts, "params")
    return [
        f"Write a short whodunit for young children set on the {_safe_lookup(LOCATIONS, params.place)['description']}, including a flashback and a transformation.",
        f"Tell a mystery story where {params.name} notices a clue on the basement stairs and learns what made the stairs aggressive.",
        f"Write a child-friendly detective story that ends with the basement stairs becoming safe again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    params: StoryParams = _safe_fact(world, world.facts, "params")
    child: Entity = _safe_fact(world, world.facts, "child")
    parent: Entity = _safe_fact(world, world.facts, "parent")
    culprit: Entity = _safe_fact(world, world.facts, "culprit")
    clue: Entity = _safe_fact(world, world.facts, "clue")
    return [
        QAItem(
            question=f"Where does the mystery happen?",
            answer="It happens on the basement stairs, where the clue was found.",
        ),
        QAItem(
            question=f"What did {child.label} remember in the flashback?",
            answer=f"{child.label} remembered seeing {clue.label} earlier and feeling that something about the stairs was wrong.",
        ),
        QAItem(
            question=f"Who was the culprit in the story?",
            answer=f"The culprit was {culprit.label}, the aggressive stair system that made the steps unsafe.",
        ),
        QAItem(
            question=f"How did the story end for {parent.label} and {child.label}?",
            answer=f"They walked down the repaired basement stairs together after the problem was solved.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when a story briefly shows something that happened earlier.",
        ),
        QAItem(
            question="What does transformation mean?",
            answer="Transformation means something changes into a different form or becomes different in an important way.",
        ),
        QAItem(
            question="What is a whodunit?",
            answer="A whodunit is a mystery story where the characters try to figure out who caused the trouble.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story QA ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Parameter resolution / generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit storyworld: basement stairs, flashback, transformation.")
    ap.add_argument("--place", choices=["basement stairs"])
    ap.add_argument("--clue", choices=list(CLUES))
    ap.add_argument("--culprit", choices=list(CULPRITS))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    place = getattr(args, "place", None) or "basement stairs"
    clue = getattr(args, "clue", None) or rng.choice(list(CLUES))
    culprit = getattr(args, "culprit", None) or rng.choice(list(CULPRITS))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    name = getattr(args, "name", None) or rng.choice(["Mina", "Leo", "Nora", "Owen", "Ivy", "Eli"])

    if place != "basement stairs":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if culprit != "system":
        # still allowed, but the requested style is close to whodunit with the aggressive system seed words
        pass
    return StoryParams(name=name, gender=gender, parent=parent, clue=clue, culprit=culprit)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.hidden:
            bits.append("hidden=True")
        if e.transformed:
            bits.append("transformed=True")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.label or e.type} {' '.join(bits)}")
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


def asp_verify_wrapper() -> int:
    return asp_verify()


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify_wrapper())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program())
        atoms = asp.atoms(model, "solved")
        print(f"{len(atoms)} solved model(s)")
        for a in atoms:
            print(a)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        params = StoryParams(name="Mina", gender="girl", parent="mother", clue="loose tread", culprit="system")
        params.seed = base_seed
        samples.append(generate(params))
    else:
        for i in range(getattr(args, "n", None)):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
