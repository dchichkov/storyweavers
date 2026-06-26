#!/usr/bin/env python3
"""
storyworlds/worlds/delta_politician_lesson_learned_rhyme_fairy_tale.py
======================================================================

A small fairy-tale story world about a politician in a river delta who learns
a lesson. The tale is built from a simulated world model with physical meters
and emotional memes, plus a matching inline ASP twin for reasonableness checks.

Premise seed:
- delta
- politician
- Lesson Learned
- Rhyme
- Fairy Tale
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    wore: bool = False
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"woman", "queen", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"man", "king", "boy", "politician"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    label: str
    kind: str = "place"
    waters: bool = False
    windy: bool = False


@dataclass
class Task:
    id: str
    verb: str
    rhyme_noun: str
    outcome: str
    trouble: str
    location: str
    mess: str
    lesson: str
    keyword: str


@dataclass
class Promise:
    id: str
    label: str
    phrase: str
    fragile: bool = False
    in_public: bool = False


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    promises: dict[str, Promise] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
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


@dataclass
class StoryParams:
    place: str
    task: str
    promise: str
    name: str
    role: str
    helper: str
    seed: Optional[int] = None


PLACES = {
    "delta": Place(id="delta", label="the river delta", waters=True, windy=True),
    "harbor": Place(id="harbor", label="the harbor", waters=True, windy=False),
    "market": Place(id="market", label="the market square", waters=False, windy=True),
    "meadow": Place(id="meadow", label="the meadow", waters=False, windy=True),
}

TASKS = {
    "bridge": Task(
        id="bridge",
        verb="promise a bridge",
        rhyme_noun="ridge",
        outcome="the bridge would not stand in the soft mud",
        trouble="the water and mud would swallow the supports",
        location="the river delta",
        mess="muddy",
        lesson="A promise needs sturdy work, not only shiny words.",
        keyword="bridge",
    ),
    "fish": Task(
        id="fish",
        verb="promise fresh fish",
        rhyme_noun="dish",
        outcome="the baskets would come back empty",
        trouble="the nets were torn and the tide was late",
        location="the harbor",
        mess="empty",
        lesson="A good plan must match what the day can truly give.",
        keyword="fish",
    ),
    "lanterns": Task(
        id="lanterns",
        verb="promise lanterns",
        rhyme_noun="glow",
        outcome="the lanterns would go out in the wind",
        trouble="the breeze would blow the flames away",
        location="the meadow",
        mess="blown",
        lesson="A promise should fit the weather and the place.",
        keyword="lanterns",
    ),
}

PROMISES = {
    "banner": Promise(
        id="banner",
        label="a silk banner",
        phrase="a bright silk banner for the festival",
        fragile=True,
        in_public=True,
    ),
    "treaty": Promise(
        id="treaty",
        label="a treaty ribbon",
        phrase="a ribbon tied around the peace treaty",
        fragile=True,
        in_public=True,
    ),
    "crown_note": Promise(
        id="crown_note",
        label="a crown note",
        phrase="a note pinned to the mayor's crown",
        fragile=True,
        in_public=False,
    ),
}

NAMES = ["Mira", "Elin", "Toma", "Jori", "Nessa", "Lenn", "Sela", "Peren"]
HELPERS = ["boatmaker", "river guard", "miller", "harp player", "herbalist"]
ROLES = ["politician", "councilor", "mayor", "speaker"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def task_at_risk(task: Task, promise: Promise) -> bool:
    return True if promise.fragile else False


def useful_helper(task: Task, promise: Promise) -> bool:
    if task.id == "bridge" and promise.id in {"banner", "treaty"}:
        return True
    if task.id == "fish" and promise.id in {"banner", "crown_note"}:
        return True
    if task.id == "lanterns" and promise.id in {"banner", "treaty", "crown_note"}:
        return True
    return False


def valid_combo(place: str, task_id: str, promise_id: str) -> bool:
    task = TASKS[task_id]
    promise = PROMISES[promise_id]
    return task_at_risk(task, promise) and useful_helper(task, promise)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
task_at_risk(T, P) :- task(T), promise(P), fragile(P).
useful_helper(bridge, P) :- promise(P), bannerish(P).
useful_helper(fish, P) :- promise(P), bannerish(P).
useful_helper(lanterns, P) :- promise(P), bannerish(P).

valid(Place, T, P) :- place(Place), task(T), promise(P), task_at_risk(T, P), useful_helper(T, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.waters:
            lines.append(asp.fact("waters", pid))
        if p.windy:
            lines.append(asp.fact("windy", pid))
    for tid in TASKS:
        lines.append(asp.fact("task", tid))
    for pid, p in PROMISES.items():
        lines.append(asp.fact("promise", pid))
        if p.fragile:
            lines.append(asp.fact("fragile", pid))
        if p.in_public:
            lines.append(asp.fact("public", pid))
        if pid in {"banner", "treaty"}:
            lines.append(asp.fact("bannerish", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    py_set = set((pl, t, p) for pl in PLACES for t in TASKS for p in PROMISES if valid_combo(pl, t, p))
    if clingo_set == py_set:
        print(f"OK: clingo gate matches valid_combo() ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    print("  only in clingo:", sorted(clingo_set - py_set))
    print("  only in python:", sorted(py_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def setup_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place=place)
    hero = world.add(Entity(id=params.name, kind="character", type=params.role, label=params.name))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper, label=params.helper))
    promise = PROMISES[params.promise]
    world.promises[promise.id] = promise
    world.add(Entity(id="promise", type="thing", label=promise.label, phrase=promise.phrase, owner=hero.id, caretaker=helper.id))
    world.facts.update(hero=hero, helper=helper, promise=promise, task=TASKS[params.task], place=place, params=params)
    return world


def rhyme_line(task: Task, promise: Promise) -> str:
    if task.id == "bridge":
        return f"Words can sing, but mud can drag; a bridge needs stone, not only brag."
    if task.id == "fish":
        return f"Bright promises may sparkle and swish, but empty words are not fresh fish."
    return f"When wind can blow and lanterns glow, wise plans must know the place and flow."


def tell_story(world: World, params: StoryParams) -> None:
    hero = world.get(params.name)
    helper = world.get("helper")
    task = TASKS[params.task]
    promise = PROMISES[params.promise]

    hero.memes["ambition"] = 1
    hero.memes["pride"] = 1
    world.say(f"Once upon a time, {hero.id} was a {hero.type} who loved to speak in grand, ringing phrases.")
    world.say(f"In {world.place.label}, {hero.id} liked to {task.verb} because the crowd listened closely and clapped like rain on reeds.")
    world.say(f"At the festival, {hero.id} showed off {promise.phrase} and smiled as if shining words could hold up the sky.")
    world.say(rhyme_line(task, promise))

    world.para()
    world.say(f"But {task.trouble}.")
    hero.memes["worry"] = 1
    helper.memes["worry"] = 1
    world.say(f"The {helper.label} looked at the {world.place.label.split()[-1]}-mud and said that the plan needed more than applause.")
    hero.meters["risk"] = 1
    world.facts["lesson"] = task.lesson

    world.para()
    hero.memes["shame"] = 1
    hero.memes["humility"] = 1
    helper.memes["trust"] = 1
    world.say(f"{hero.id} listened, lowered the banner, and asked what would actually work.")
    if task.id == "bridge":
        world.say(f"Together they chose to pile stones first and let the bridge grow from a firm base.")
    elif task.id == "fish":
        world.say(f"Together they checked the nets, waited for the tide, and promised only the baskets they could truly fill.")
    else:
        world.say(f"Together they tied the lanterns low, behind straw screens, where the wind could not snuff them out.")
    hero.memes["lesson_learned"] = 1
    world.say(f"That was the lesson learned: {task.lesson}")
    world.say(f"And when the day was done, {hero.id} smiled in a smaller, truer way, because careful promises were better than loud ones.")


# ---------------------------------------------------------------------------
# Registries / params / generation
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    return [(pl, t, p) for pl in PLACES for t in TASKS for p in PROMISES if valid_combo(pl, t, p)]


@dataclass
class StoryParamsResolved:
    place: str
    task: str
    promise: str
    name: str
    role: str
    helper: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale story world about a politician who learns a lesson.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--promise", choices=PROMISES)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--role", choices=ROLES)
    ap.add_argument("--helper", choices=HELPERS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParamsResolved:
    if args.task and args.promise and not valid_combo(args.place or "delta", args.task, args.promise):
        raise StoryError("That promise does not fit the task in a reasonable fairy-tale way.")

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.task is None or c[1] == args.task)
        and (args.promise is None or c[2] == args.promise)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, task, promise = rng.choice(sorted(combos))
    role = args.role or "politician"
    name = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParamsResolved(place=place, task=task, promise=promise, name=name, role=role, helper=helper)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    task = f["task"]
    return [
        f"Write a fairy tale about a {hero.type} in {world.place.label} who learns a lesson after making a grand promise.",
        f"Tell a short rhyme-filled story where {hero.id} tries to {task.verb} and discovers that the plan needs to match the place.",
        f"Create a gentle lesson-learned tale with a river-delta mood, a politician, and a rhyming ending image.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    task = f["task"]
    promise = f["promise"]
    helper = f["helper"]
    place = f["place"]
    return [
        QAItem(
            question=f"Who was the story about in {place.label}?",
            answer=f"It was about {hero.id}, a {hero.type} who loved speaking grand promises but learned to think first.",
        ),
        QAItem(
            question=f"What did {hero.id} try to promise at {place.label}?",
            answer=f"{hero.id} tried to {task.verb}. That sounded wonderful, but the place could not support it safely.",
        ),
        QAItem(
            question=f"Why did the helper worry about {promise.label}?",
            answer=f"The helper worried because {task.trouble}, so {promise.phrase} was not a wise promise for that day.",
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn?",
            answer=f"{task.lesson}",
        ),
        QAItem(
            question=f"How did the story end for {hero.id}?",
            answer=f"{hero.id} ended up listening, choosing a steadier plan, and feeling proud of a careful promise instead of a loud one.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a delta?",
            answer="A delta is a low, wet place where a river spreads into many smaller streams before reaching the sea.",
        ),
        QAItem(
            question="What is a politician?",
            answer="A politician is a person who talks with people, makes plans for a town or country, and tries to win trust.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is when words sound alike at the end, like sing and ring.",
        ),
        QAItem(
            question="What is a lesson learned?",
            answer="A lesson learned is something important a character understands after making a mistake or facing a problem.",
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
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  place: {world.place.label}")
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


def generate(params: StoryParamsResolved) -> StorySample:
    world = setup_world(params)
    tell_story(world, params)
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


# ---------------------------------------------------------------------------
# ASP support
# ---------------------------------------------------------------------------

def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParamsResolved(place="delta", task="bridge", promise="banner", name="Mira", role="politician", helper="boatmaker"),
    StoryParamsResolved(place="delta", task="fish", promise="crown_note", name="Jori", role="mayor", helper="river guard"),
    StoryParamsResolved(place="meadow", task="lanterns", promise="treaty", name="Sela", role="councilor", helper="harp player"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, task, promise) combos:")
        for pl, t, p in combos:
            print(f"  {pl:8} {t:10} {p:10}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.name}: {p.task} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
