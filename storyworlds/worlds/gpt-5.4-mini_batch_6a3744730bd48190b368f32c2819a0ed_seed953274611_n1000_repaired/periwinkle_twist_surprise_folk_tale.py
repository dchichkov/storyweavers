#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/periwinkle_twist_surprise_folk_tale.py
======================================================================

A small standalone storyworld for a folk-tale style seed built around the word
"periwinkle" and the narrative instruments "Twist" and "Surprise".

Premise:
- A child and a small helper wander with a periwinkle ribbon in a village tale.
- A twist reveals the ribbon is the key to a hidden path or identity.
- A surprise turns a small problem into a happy ending image.

This world is intentionally small, concrete, and state-driven. It uses typed
entities with physical meters and emotional memes, a simple forward-chaining
simulation, a reasonableness gate, and an inline ASP twin for parity checks.
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
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "grandmother"}
        male = {"boy", "father", "man", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "grandmother": "grandma", "grandfather": "grandpa"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Place:
    id: str
    label: str
    dark: str
    twist_hint: str
    surprise_hint: str
    path_kind: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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
class ObjectThing:
    id: str
    label: str
    phrase: str
    color: str
    useful_for: str
    hidden_key: str = ""
    carries: str = ""
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class Problem:
    id: str
    sense: int
    risk: int
    text: str
    warning: str
    fix: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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


class World:
    def __init__(self) -> None:
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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


def _r_discover(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["attention"] < THRESHOLD:
            continue
        sig = ("discover", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if e.attrs.get("has_ribbon"):
            e.memes["hope"] += 1
            out.append("__discover__")
    return out


def _r_surprise(world: World) -> list[str]:
    out: list[str] = []
    ribbon = world.entities.get("ribbon")
    if not ribbon or ribbon.meters["revealed"] < THRESHOLD:
        return out
    sig = ("surprise", ribbon.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for e in list(world.entities.values()):
        if e.kind == "character":
            e.memes["wonder"] += 1
    out.append("__surprise__")
    return out


CAUSAL_RULES = [
    Rule("discover", "social", _r_discover),
    Rule("surprise", "social", _r_surprise),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def sensible_problems() -> list[Problem]:
    return [p for p in PROBLEMS.values() if p.sense >= SENSE_MIN]


def valid_combo(place: Place, problem: Problem) -> bool:
    return problem.id in place.tags


def hidden_at_risk(place: Place, problem: Problem) -> bool:
    return problem.risk > 0 and place.path_kind in {"woods", "hill", "river"}


def predict(world: World, place_id: str) -> dict:
    sim = world.copy()
    _trigger_twist(sim, sim.get(place_id), narrate=False)
    return {
        "revealed": sim.entities["ribbon"].meters["revealed"] >= THRESHOLD,
        "wonder": sum(e.memes["wonder"] for e in sim.entities.values() if e.kind == "character"),
    }


def _trigger_twist(world: World, place: Entity, narrate: bool = True) -> None:
    ribbon = world.get("ribbon")
    ribbon.meters["revealed"] += 1
    propagate(world, narrate=narrate)


def opening(world: World, child: Entity, elder: Entity, place: Place, ribbon: ObjectThing) -> None:
    child.memes["curiosity"] += 1
    elder.memes["calm"] += 1
    world.say(
        f"Once, in a small village by the pines, {child.id} and {elder.id} walked "
        f"toward {place.label}. {place.twist_hint} A periwinkle ribbon fluttered "
        f"from {child.pronoun('possessive')} basket."
    )


def desire(world: World, child: Entity, place: Place) -> None:
    child.meters["attention"] += 1
    world.say(
        f"{child.id} wanted to follow the quiet path. It wound toward {place.dark}, "
        f"where the shadows seemed to whisper."
    )


def warning(world: World, elder: Entity, child: Entity, problem: Problem) -> None:
    elder.memes["care"] += 1
    world.say(
        f"{elder.id} touched {child.pronoun('possessive')} shoulder and said, "
        f"\"{problem.warning}\""
    )


def twist(world: World, child: Entity, place: Place, ribbon: ObjectThing) -> None:
    child.meters["attention"] += 1
    world.say(
        f"Then came the twist: the ribbon was not only ribbon. It matched the mark "
        f"on the old gate near {place.label}, and {child.id} saw the path was pointing "
        f"somewhere on purpose."
    )


def surprise(world: World, child: Entity, elder: Entity, place: Place, ribbon: ObjectThing) -> None:
    ribbon.meters["revealed"] += 1
    _trigger_twist(world, child, narrate=False)
    world.say(
        f"With a little tug, the ribbon slipped free and showed a tiny tag beneath it. "
        f"The tag named a lost basket, tucked safely behind a tree by {place.surprise_hint}."
    )


def resolve(world: World, child: Entity, elder: Entity, place: Place, ribbon: ObjectThing) -> None:
    child.memes["joy"] += 1
    elder.memes["joy"] += 1
    world.say(
        f"{child.id} carried the basket home, the periwinkle ribbon tied around the handle. "
        f"{elder.id} smiled, and the whole lane seemed softer in the evening light."
    )
    world.say(
        f"By nightfall, the ribbon rested on the table like a small piece of sky, "
        f"and the hidden path was no longer lonely."
    )


def tell(place: Place, problem: Problem, child_name: str = "Mina", elder_name: str = "Grandma") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type="girl", role="child", attrs={"has_ribbon": True}))
    elder = world.add(Entity(id=elder_name, kind="character", type="grandmother", role="elder"))
    ribbon = world.add(Entity(id="ribbon", kind="thing", type="object", label="periwinkle ribbon"))
    basket = world.add(Entity(id="basket", kind="thing", type="object", label="basket"))
    world.facts["place"] = place
    world.facts["problem"] = problem
    world.facts["child"] = child
    world.facts["elder"] = elder
    world.facts["ribbon"] = ribbon
    world.facts["basket"] = basket

    opening(world, child, elder, place, ribbon)
    world.para()
    desire(world, child, place)
    warning(world, elder, child, problem)
    world.para()
    twist(world, child, place, ribbon)
    surprise(world, child, elder, place, ribbon)
    world.para()
    resolve(world, child, elder, place, ribbon)
    return world


PLACES = {
    "woods": Place(
        id="woods",
        label="the woods",
        dark="the old hollow",
        twist_hint="The breeze kept tugging at a strand of color on the fence.",
        surprise_hint="a squirrel with a bright-eyed hop",
        path_kind="woods",
        tags={"lost", "gate", "ribbon"},
    ),
    "hill": Place(
        id="hill",
        label="the hill",
        dark="the bend in the path",
        twist_hint="A blue-gray gate stood where the path split.",
        surprise_hint="a child from the next farm",
        path_kind="hill",
        tags={"gate", "hidden", "ribbon"},
    ),
    "river": Place(
        id="river",
        label="the riverbank",
        dark="the reeds by the water",
        twist_hint="Something pale fluttered near a willow root.",
        surprise_hint="an old boat tied to a stump",
        path_kind="river",
        tags={"lost", "water", "ribbon"},
    ),
}

PROBLEMS = {
    "lost_basket": Problem(
        id="lost_basket",
        sense=3,
        risk=1,
        text="a lost basket",
        warning="Do not wander too far into the dark path. The trees are thick there.",
        fix="follow the ribbon and bring the basket home",
        tags={"lost", "gate", "ribbon"},
    ),
    "wayward_kitten": Problem(
        id="wayward_kitten",
        sense=2,
        risk=1,
        text="a wayward kitten",
        warning="Stay close, little one. Something soft may be hiding near the reeds.",
        fix="find the kitten by the ribbon",
        tags={"water", "ribbon"},
    ),
    "bright_gate": Problem(
        id="bright_gate",
        sense=2,
        risk=1,
        text="a bright gate",
        warning="If the gate opens, be gentle. Hidden things can startle easily.",
        fix="open the gate with care",
        tags={"gate", "hidden", "ribbon"},
    ),
}

NAMES = ["Mina", "Lena", "Tessa", "Ivy", "Nora", "Anya"]
ELDERS = ["Grandma", "Nana", "Old Mother", "Aunt Willow"]


@dataclass
class StoryParams:
    place: str
    problem: str
    child: str
    elder: str
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


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for pr_id, problem in PROBLEMS.items():
            if valid_combo(place, problem) and hidden_at_risk(place, problem):
                combos.append((pid, pr_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small folk-tale storyworld with periwinkle, twist, and surprise.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--child")
    ap.add_argument("--elder")
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
    if args.place and args.problem:
        if not valid_combo(PLACES[args.place], PROBLEMS[args.problem]):
            raise StoryError("(No story: that place and problem do not belong together.)")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.problem is None or c[1] == args.problem)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, problem = rng.choice(sorted(combos))
    child = args.child or rng.choice(NAMES)
    elder = args.elder or rng.choice(ELDERS)
    return StoryParams(place=place, problem=problem, child=child, elder=elder)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place, problem = f["place"], f["problem"]
    return [
        f'Write a short folk tale that includes the word "periwinkle" and the place {place.label}.',
        f"Tell a gentle story where a child and an elder discover that a periwinkle ribbon matters.",
        f'Write a story with a twist and surprise that leads from {problem.text} to a happy ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    place = f["place"]
    problem = f["problem"]
    ribbon = f["ribbon"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {child.id} and {elder.id}. They walk near {place.label}, and the periwinkle ribbon helps the story turn."
        ),
        QAItem(
            question="What was the twist in the story?",
            answer=f"The twist was that the periwinkle ribbon was a clue, not just a pretty thing. It pointed toward something hidden, so the path meant more than it first seemed."
        ),
        QAItem(
            question="How did the surprise change the ending?",
            answer=f"The surprise showed that {problem.text} was not lost forever. When the hidden basket was found, the worry changed into joy and the ribbon became part of a happy return."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What color is periwinkle?",
            answer="Periwinkle is a soft blue-purple color. It often looks like a little piece of twilight."
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprise change that makes the story go a different way than you expected. It often reveals something new about a person, a place, or a thing."
        ),
        QAItem(
            question="What is a surprise in a story?",
            answer="A surprise is something unexpected that appears or happens. It can make a story feel magical, funny, or exciting."
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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="woods", problem="lost_basket", child="Mina", elder="Grandma"),
    StoryParams(place="hill", problem="bright_gate", child="Ivy", elder="Nana"),
    StoryParams(place="river", problem="wayward_kitten", child="Tessa", elder="Aunt Willow"),
]


def explain_problem(place: Place, problem: Problem) -> str:
    return f"(No story: {problem.text} does not fit neatly with {place.label} in this tiny tale.)"


ASP_RULES = r"""
combo(P, Pr) :- place(P), problem(Pr), valid(P, Pr).
valid(P, Pr) :- place(P), problem(Pr), tagged(P, Pr), hidden_risk(P, Pr).
outcome(twist) :- valid(_, _).
outcome(surprise) :- valid(_, _), hidden_risk(_, _).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for t in sorted(p.tags):
            lines.append(asp.fact("tagged", pid, t))
    for prid, pr in PROBLEMS.items():
        lines.append(asp.fact("problem", prid))
        for t in sorted(pr.tags):
            lines.append(asp.fact("hidden_risk", pr.id, t))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))

def asp_verify() -> int:
    import io
    from contextlib import redirect_stdout
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid-combo gates differ.")
        rc = 1
    try:
        with redirect_stdout(io.StringIO()):
            sample = generate(resolve_params(argparse.Namespace(place=None, problem=None, child=None, elder=None), random.Random(0)))
            _ = sample.story
    except Exception as e:
        print(f"MISMATCH: smoke test failed: {e}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.problem not in PROBLEMS:
        raise StoryError(f"Unknown problem: {params.problem}")
    place = PLACES[params.place]
    problem = PROBLEMS[params.problem]
    if not valid_combo(place, problem):
        raise StoryError(explain_problem(place, problem))
    world = tell(place, problem, child_name=params.child, elder_name=params.elder)
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
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("compatible combos:")
        for p, pr in asp_valid_combos():
            print(f"  {p} {pr}")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for idx, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {idx+1}" if len(samples) > 1 else ""))
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
