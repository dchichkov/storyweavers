#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T084545Z_seed1746935730_n100/honcho_bracket_reconciliation_dialogue_folk_tale.py
==============================================================================================================

A small folk-tale story world about a village honcho, a stubborn bracket, and a
reconciliation reached through dialogue.

The source seed suggests a tale in which a leader notices a problem in the
village, speaks too sharply at first, then listens and makes peace after the
truth comes out. This script turns that premise into a stateful simulation with
physical meters and emotional memes.

Domain sketch:
- A honcho oversees a village place.
- A bracket supports something important: a sign, shelf, gate, or lantern.
- If the bracket loosens or breaks, a village item becomes unsafe.
- Dialogue can shift trust and calm the honcho.
- Reconciliation happens when the honcho apologizes and joins the fix.
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
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    bracket: object | None = None
    helper: object | None = None
    honcho: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"sturdy": 0.0, "broken": 0.0, "clean": 0.0}
        if not self.memes:
            self.memes = {"worry": 0.0, "pride": 0.0, "hurt": 0.0, "trust": 0.0, "warmth": 0.0}

    def pronoun(self) -> str:
        if self.type in {"woman", "girl", "mother"}:
            return "she"
        if self.type in {"man", "boy", "father", "honcho"}:
            return "he"
        return "it"

    def poss(self) -> str:
        if self.type in {"woman", "girl", "mother"}:
            return "her"
        if self.type in {"man", "boy", "father", "honcho"}:
            return "his"
        return "its"
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
    setting: str
    afford: str
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
    id: str
    verb: str
    consequence: str
    repair_verb: str
    physical: str
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
class StoryParams:
    place: str
    problem: str
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]


PLACES = {
    "village_square": Place(name="the village square", setting="outdoors", afford="public"),
    "market_lane": Place(name="the market lane", setting="outdoors", afford="bustle"),
    "timber_yard": Place(name="the timber yard", setting="outdoors", afford="tools"),
}

PROBLEMS = {
    "sign_bracket": Problem(
        id="sign_bracket",
        verb="hold the village sign",
        consequence="the sign tilted crooked",
        repair_verb="tighten",
        physical="loose",
        tags={"bracket", "sign"},
    ),
    "lantern_bracket": Problem(
        id="lantern_bracket",
        verb="hold the lantern",
        consequence="the lantern drooped low",
        repair_verb="set straight",
        physical="bent",
        tags={"bracket", "lantern"},
    ),
    "shelf_bracket": Problem(
        id="shelf_bracket",
        verb="hold the loaf shelf",
        consequence="the loaf shelf wobbled",
        repair_verb="brace",
        physical="weak",
        tags={"bracket", "shelf", "bread"},
    ),
}

HONCHO_NAMES = ["Mara", "Tobin", "Iris", "Pavel", "Bela", "Jonas"]
HELPER_NAMES = ["Nell", "Hugo", "Sera", "Milo", "Rina", "Otto"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale story world about a honcho, a bracket, and reconciliation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
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


def valid_pairs() -> list[tuple[str, str]]:
    return [(p, pr) for p in PLACES for pr in PROBLEMS]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    pairs = valid_pairs()
    if getattr(args, "place", None) or getattr(args, "problem", None):
        pairs = [
            (p, pr) for (p, pr) in pairs
            if (getattr(args, "place", None) is None or p == getattr(args, "place", None)) and (getattr(args, "problem", None) is None or pr == getattr(args, "problem", None))
        ]
    if not pairs:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, problem = rng.choice(sorted(pairs))
    return StoryParams(place=place, problem=problem)


def _line(world: World, text: str) -> None:
    world.say(text)


def generate_world(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    problem = _safe_lookup(PROBLEMS, params.problem)
    world = World(place)

    honcho = world.add(Entity(id="Honcho", kind="character", type="honcho", label="the honcho"))
    helper = world.add(Entity(id="Helper", kind="character", type="villager", label="the helper"))

    bracket = world.add(Entity(
        id="Bracket",
        kind="thing",
        type="bracket",
        label="the bracket",
        phrase=f"a little {problem.physical} iron bracket",
    ))
    bracket.meters["sturdy"] = 0.2
    if problem.physical == "loose":
        bracket.meters["broken"] = 0.2
    elif problem.physical == "bent":
        bracket.meters["broken"] = 0.4
    else:
        bracket.meters["broken"] = 0.3

    honcho.memes["pride"] = 1.0
    honcho.memes["worry"] = 1.0
    helper.memes["trust"] = 1.0

    world.facts.update(place=place, problem=problem, honcho=honcho, helper=helper, bracket=bracket)

    _line(world, f"In {place.name}, there lived a village honcho who kept a sharp eye on every small thing.")
    _line(world, f"Near the lane stood {bracket.phrase}, and it had the job to {problem.verb}.")
    _line(world, f"One morning, the honcho noticed that {bracket.label} had grown {problem.physical}.")
    world.para()
    _line(world, f'"Look at that," said the honcho. "If it stays this way, {problem.consequence}."')
    _line(world, f'The helper bowed his head and said, "I saw it too. It only needs a careful hand, not a harsh one."')
    honcho.memes["hurt"] += 1
    helper.memes["worry"] += 1
    world.para()
    _line(world, f"The honcho frowned at first, for {honcho.poss()} pride was big, and the helper felt small.")
    _line(world, f"Still, the helper spoke kindly: \"Let me fetch the tools, and you can show the village how to mend it.\"")
    honcho.memes["trust"] += 0.5
    helper.memes["trust"] += 0.5
    world.para()
    _line(world, f"The honcho listened. \"You speak true,\" {honcho.pronoun()} said, softening at last.")
    _line(world, f"\"I spoke too sharply. Will you forgive me, and will you help me {problem.repair_verb} it?\"")
    honcho.memes["warmth"] += 1.0
    helper.memes["warmth"] += 1.0
    helper.memes["hurt"] = 0.0
    world.para()
    _line(world, f"The helper smiled. \"Yes,\" {helper.pronoun()} said, \"and I am glad you asked.\"")
    _line(world, f"So together they {problem.repair_verb} the bracket until it grew steady again, and the village sign stayed true.")
    bracket.meters["sturdy"] = 1.0
    bracket.meters["broken"] = 0.0
    honcho.memes["pride"] = 0.3
    honcho.memes["trust"] = 1.0
    honcho.memes["worry"] = 0.0
    helper.memes["trust"] = 1.0

    world.facts["reconciled"] = True
    world.facts["ending"] = f"The bracket stood steady, and the honcho and the helper walked home side by side."
    return world


def generation_prompts(world: World) -> list[str]:
    p: Place = world.facts["place"]  # type: ignore[assignment]
    pr: Problem = world.facts["problem"]  # type: ignore[assignment]
    return [
        f"Write a short folk tale about a honcho at {p.name} and a {pr.id} that needs careful fixing.",
        f"Tell a child-friendly story where dialogue helps a honcho and a helper reconcile over a {pr.phrase}.",
        f"Write a gentle tale in which a village bracket is mended after the honcho listens and apologizes.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: Place = world.facts["place"]  # type: ignore[assignment]
    pr: Problem = world.facts["problem"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Where did the story take place?",
            answer=f"It took place at {p.name}, where the honcho watched over a small village problem.",
        ),
        QAItem(
            question=f"What was wrong with the bracket?",
            answer=f"The bracket was {pr.physical}, so it could not properly {pr.verb} until it was fixed.",
        ),
        QAItem(
            question="How did the honcho and the helper make things better?",
            answer=f"They talked kindly, the honcho apologized, and then they worked together to {pr.repair_verb} the bracket.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bracket used for?",
            answer="A bracket is a support piece that helps hold up a sign, shelf, lantern, or other object.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means people stop being upset, speak kindly again, and make peace after a problem.",
        ),
        QAItem(
            question="What is dialogue?",
            answer="Dialogue is talking back and forth between characters, often to share feelings or solve a problem.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


ASP_RULES = r"""
place(village_square).
place(market_lane).
place(timber_yard).

problem(sign_bracket).
problem(lantern_bracket).
problem(shelf_bracket).

valid(Place, Problem) :- place(Place), problem(Problem).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join(
        [asp.fact("place", p) for p in PLACES] +
        [asp.fact("problem", pr) for pr in PROBLEMS]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_pairs() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_pairs())
    cl = set(asp_valid_pairs())
    if py == cl:
        print(f"OK: clingo gate matches valid_pairs() ({len(py)} pairs).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("python-only:", sorted(py - cl))
    print("clingo-only:", sorted(cl - py))
    return 1


def build_sample(params: StoryParams) -> StorySample:
    world = generate_world(params)
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
    StoryParams(place="village_square", problem="sign_bracket"),
    StoryParams(place="market_lane", problem="lantern_bracket"),
    StoryParams(place="timber_yard", problem="shelf_bracket"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "asp", None):
        pairs = asp_valid_pairs()
        print(f"{len(pairs)} valid pairs:")
        for p in pairs:
            print(" ", p)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [build_sample(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            sample = build_sample(params)
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.place} / {p.problem}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
