#!/usr/bin/env python3
"""
storyworlds/worlds/north_bad_ending_moral_value_problem_solving.py
===================================================================

A standalone story world about a small northward quest with a nursery-rhyme
voice, a moral lesson, problem solving, and a bad ending that still feels like
a complete little tale.

Seed tale:
---
A little mouse and a little child went to the north hill to find a lost kite.
They shared a spool of string, listened to the wind, and tried to solve the
problem together. They made a careful plan, but the north wind rose stronger,
the kite slipped away, and the ending was sad. They learned to be kind and to
listen, even when the answer does not come out happy.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    tags: set[str] = field(default_factory=set)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
        return self.label or self.type
    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))


@dataclass
class Place:
    id: str
    label: str
    northy: bool = False
    affords: set[str] = field(default_factory=set)
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


@dataclass
class Problem:
    id: str
    verb: str
    gerund: str
    risk: str
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


@dataclass
class Solution:
    id: str
    label: str
    step: str
    effect: str
    helps: set[str] = field(default_factory=set)
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


class World:
    def __init__(self, place: Place) -> None:
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str = "hill"
    problem: str = "kite"
    solution: str = "string"
    child_name: str = "Mia"
    child_gender: str = "girl"
    friend_name: str = "Pip"
    friend_gender: str = "boy"
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


PLACES = {
    "hill": Place(id="hill", label="the north hill", northy=True, affords={"kite"}),
    "field": Place(id="field", label="the field by the road", northy=False, affords={"kite"}),
    "bank": Place(id="bank", label="the river bank", northy=False, affords={"boat"}),
}

PROBLEMS = {
    "kite": Problem(id="kite", verb="fly the kite", gerund="flying the kite", risk="snapped", tags={"wind", "kite"}),
    "boat": Problem(id="boat", verb="reach the toy boat", gerund="reaching the toy boat", risk="drifted", tags={"water", "boat"}),
}

SOLUTIONS = {
    "string": Solution(id="string", label="a spool of string", step="tie the string tight", effect="held it fast", helps={"kite"}),
    "basket": Solution(id="basket", label="a little basket", step="carry the basket carefully", effect="kept the boat close", helps={"boat"}),
}

GIRL_NAMES = ["Mia", "Nora", "Lily", "Ava", "Rose"]
BOY_NAMES = ["Pip", "Toby", "Finn", "Ben", "Jules"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for prob_id, prob in PROBLEMS.items():
            if prob.id in place.affords:
                for sol_id, sol in SOLUTIONS.items():
                    if prob.id in sol.helps:
                        combos.append((place_id, prob_id, sol_id))
    return combos


def choose_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def build_story(world: World) -> None:
    child = world.get("child")
    friend = world.get("friend")
    problem = world.facts["problem"]
    solution = world.facts["solution"]
    place = world.place

    world.say(
        f"Little {child.id} and little {friend.id} went out one day, "
        f"up to {place.label}, where the grass grew gray."
    )
    world.say(
        f"They wanted {problem.gerund}, for the breeze was light, "
        f"and both of them sang in the morning bright."
    )
    world.para()
    child.memes["want"] += 1
    friend.memes["want"] += 1
    world.say(
        f"But the north wind whispered, soft at first, then sly: "
        f'"Keep hold of your plan, and keep hold of the sky."'
    )
    world.say(
        f'{friend.id} said, "Let us {solution.step}." {child.id} nodded slow, '
        f"for sharing ideas can help them grow."
    )
    child.memes["care"] += 1
    friend.memes["care"] += 1
    world.para()
    child.meters["effort"] += 1
    friend.meters["effort"] += 1
    world.say(
        f"They worked together, neat as neat, with careful hands and careful feet."
    )
    world.say(
        f"But the wind grew wild from the north, so keen, and the kite went up "
        f"where no child had been."
    )
    world.say(
        f"The string slipped loose; the bright thing flew away. "
        f"It vanished northward and would not stay."
    )
    child.memes["sad"] += 2
    friend.memes["sad"] += 2
    world.para()
    world.say(
        f"Little {child.id} sighed, and little {friend.id} sighed too. "
        f"They learned that kindness is something true."
    )
    world.say(
        f"Even when a plan does not save the day, it helps to be gentle and try "
        f"a kind new way."
    )
    world.facts["ending"] = "bad"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a nursery-rhyme-style story about {f["child"]} and {f["friend"]} '
        f"trying to solve a problem on the {f['place_label']} with the word "
        f'"north" in it.',
        f"Tell a short story where two little friends make a plan, but the north "
        f"wind ruins the fix and the ending is sad.",
        f"Write a gentle story with a moral lesson about sharing and trying to "
        f"solve a problem, even though the result is a bad ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    friend = f["friend"]
    problem = f["problem"]
    solution = f["solution"]
    place = f["place_label"]
    return [
        QAItem(
            question=f"Who tried to solve the problem at {place}?",
            answer=f"{child} and {friend} tried together. They went to {place} to work on the problem and help each other.",
        ),
        QAItem(
            question=f"What did {child} and {friend} use to help with the problem?",
            answer=f"They used {solution.label}. They shared it and made a careful plan, hoping it would help {problem.gerund}.",
        ),
        QAItem(
            question=f"Why did the ending go badly even after their good plan?",
            answer=f"The north wind grew too strong and carried the {problem.id} away. Their idea was kind and careful, but the wind was stronger than their fix.",
        ),
        QAItem(
            question=f"What moral did {child} and {friend} learn?",
            answer="They learned to be kind, to share, and to keep trying even when a problem does not end happily. A gentle heart still matters on a bad day.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does north mean?",
            answer="North is one direction on a compass. People use it to find where to go.",
        ),
        QAItem(
            question="What is a problem?",
            answer="A problem is something that is hard to do or hard to fix. People can think, share, and plan to solve it.",
        ),
        QAItem(
            question="What does it mean to solve a problem?",
            answer="To solve a problem means to find a way to make it better or to finish it. Sometimes the first plan works, and sometimes people need a new plan.",
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


def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place)
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_gender))
    friend = world.add(Entity(id=params.friend_name, kind="character", type=params.friend_gender))
    world.facts["child"] = child.id
    world.facts["friend"] = friend.id
    world.facts["place_label"] = place.label
    world.facts["problem"] = PROBLEMS[params.problem]
    world.facts["solution"] = SOLUTIONS[params.solution]

    build_story(world)
    return world


CURATED = [
    StoryParams(place="hill", problem="kite", solution="string", child_name="Mia", child_gender="girl", friend_name="Pip", friend_gender="boy"),
    StoryParams(place="field", problem="kite", solution="string", child_name="Nora", child_gender="girl", friend_name="Ben", friend_gender="boy"),
]


def explain_rejection(problem: Problem, solution: Solution, place: Place) -> str:
    return (
        f"(No story: {problem.verb} does not fit {place.label}, or {solution.label} "
        f"does not help with that problem. Pick a matching, simple pair.)"
    )


def valid_story_params(params: StoryParams) -> bool:
    return (params.place, params.problem, params.solution) in valid_combos()


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme story world with a bad ending and a moral lesson.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--solution", choices=SOLUTIONS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
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
              if (args.place is None or c[0] == args.place)
              and (args.problem is None or c[1] == args.problem)
              and (args.solution is None or c[2] == args.solution)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, problem, solution = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if child_gender == "girl" else "girl")
    child_name = args.child_name or choose_name(rng, child_gender)
    friend_name = args.friend_name or choose_name(rng, friend_gender)
    if friend_name == child_name:
        friend_name = choose_name(rng, friend_gender)
    return StoryParams(
        place=place,
        problem=problem,
        solution=solution,
        child_name=child_name,
        child_gender=child_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if not valid_story_params(params):
        raise StoryError(explain_rejection(PROBLEMS[params.problem], SOLUTIONS[params.solution], PLACES[params.place]))
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


ASP_RULES = r"""
place(hill). place(field). place(bank).
problem(kite). problem(boat).
solution(string). solution(basket).

affords(hill,kite).
affords(field,kite).
affords(bank,boat).

helps(string,kite).
helps(basket,boat).

valid(P,Pr,S) :- affords(P,Pr), helps(S,Pr).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
        if PLACES[p].northy:
            lines.append(asp.fact("northy", p))
    for pr in PROBLEMS:
        lines.append(asp.fact("problem", pr))
    for s in SOLUTIONS:
        lines.append(asp.fact("solution", s))
    for p, pl in PLACES.items():
        for pr in pl.affords:
            lines.append(asp.fact("affords", p, pr))
    for s, sol in SOLUTIONS.items():
        for pr in sol.helps:
            lines.append(asp.fact("helps", s, pr))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    ok = set(asp_valid_combos()) == set(valid_combos())
    smoke_params = CURATED[0]
    smoke = generate(smoke_params)
    _ = smoke.to_json()
    if ok and smoke.story:
        print(f"OK: ASP matches Python valid_combos() ({len(valid_combos())} combos) and smoke test passed.")
        return 0
    print("MISMATCH or smoke-test failure.")
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:\n")
        for p, pr, s in combos:
            print(f"  {p:6} {pr:6} {s}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name} and {p.friend_name}: {p.problem} on the {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
