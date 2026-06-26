#!/usr/bin/env python3
"""
A standalone story world for a bedtime-style kindergarten problem-solving tale.

Premise:
- A child at kindergarten wants a cozy bedtime-like rest.
- A small quail is trying to settle in.
- A lump of coal has made a dark mess.
- A jest, or little joke, helps the group calm down and solve the problem.

The story is simulated from world state, not copied from a fixed paragraph.
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {
                "mess": 0.0,
                "clean": 0.0,
                "sleepy": 0.0,
                "joy": 0.0,
                "worry": 0.0,
                "relief": 0.0,
            }
        if not self.memes:
            self.memes = {
                "worry": 0.0,
                "calm": 0.0,
                "joy": 0.0,
                "problem_solving": 0.0,
            }

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


class World:
    def __init__(self, setting: str) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "kindergarten": {
        "place": "the kindergarten",
        "indoor": True,
    }
}

ACTIVITIES = {
    "bedtime": {
        "verb": "settle down for bedtime",
        "gerund": "settling down for bedtime",
        "mess": "tired",
    },
    "nap": {
        "verb": "take a nap",
        "gerund": "taking a nap",
        "mess": "tired",
    },
}

PRIZES = {
    "blanket": {
        "label": "blanket",
        "phrase": "a soft blue blanket",
        "region": "body",
    },
    "pillow": {
        "label": "pillow",
        "phrase": "a fluffy pillow",
        "region": "head",
    },
}

CHARACTER_NAMES = ["Mina", "Noah", "Lila", "Otto", "Iris", "Jun", "Pia", "Theo"]
TRAITS = ["gentle", "curious", "shy", "cheerful", "patient", "brave"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
setting(kindergarten).
indoor(kindergarten).

activity(bedtime).
activity(nap).

prize(blanket).
prize(pillow).

at_risk(A,P) :- activity(A), prize(P), needs_rest(A,P).
helps(P) :- prize(P).

valid_story(kindergarten, A, P) :- at_risk(A,P), helps(P).

needs_rest(bedtime, blanket).
needs_rest(nap, pillow).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", "kindergarten"), asp.fact("indoor", "kindergarten")]
    for a in ACTIVITIES:
        lines.append(asp.fact("activity", a))
    for p in PRIZES:
        lines.append(asp.fact("prize", p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


# ---------------------------------------------------------------------------
# Reasoning helpers
# ---------------------------------------------------------------------------

def valid_combo(activity: str, prize: str) -> bool:
    return (activity, prize) in {("bedtime", "blanket"), ("nap", "pillow")}


def explain_rejection(activity: str, prize: str) -> str:
    return (
        f"(No story: {ACTIVITIES[activity]['verb']} does not fit with {PRIZES[prize]['label']} "
        f"in this little kindergarten bedtime world.)"
    )


def predict_problem(world: World, hero: Entity, activity: str, prize: Entity) -> bool:
    sim = world.copy()
    sim.get(hero.id).memes["worry"] += 1
    sim.get(prize.id).meters["mess"] += 1
    return sim.get(prize.id).meters["mess"] >= THRESHOLD


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def intro(world: World, child: Entity, activity: str, prize: Entity) -> None:
    world.say(
        f"{child.id} was a {next((t for t in child.meters if False), '')}"
    )


def tell_story(world: World, child: Entity, teacher: Entity, quail: Entity,
               coal: Entity, joke: Entity, activity: str, prize: Entity) -> None:
    act = ACTIVITIES[activity]
    world.say(
        f"At the kindergarten, {child.id} was a {child.pronoun('possessive')} {child.type} "
        f"who felt sleepy but still wanted to {act['verb']}."
    )
    world.say(
        f"Near the quiet corner sat a small quail named {quail.id}, and beside it was a little lump of coal."
    )
    world.say(
        f"{child.id} liked the soft {prize.label}, but the coal had left a dark smudge on the floor."
    )

    world.para()
    child.memes["worry"] += 1
    teacher.memes["worry"] += 1
    coal.meters["mess"] += 1
    world.say(
        f"{teacher.id} frowned a little and said, \"We need a careful plan before bedtime can feel cozy.\""
    )
    world.say(
        f"{quail.id} tucked its head down, looking small and worried."
    )

    world.para()
    world.say(
        f"Then {joke.id} told a tiny jest: \"Why did the pillow smile? Because it had sweet dreams waiting!\""
    )
    child.memes["joy"] += 1
    quail.meters["joy"] += 1
    teacher.meters["relief"] += 1
    world.say(
        f"The joke made the room go soft and warm, like a blanket being spread out."
    )

    world.say(
        f"{child.id} helped solve the problem by lifting the {prize.label} away from the smudgy spot "
        f"while {teacher.id} wiped the coal mark clean."
    )
    coal.meters["mess"] = 0.0
    prize.meters["clean"] += 1
    quail.meters["sleepy"] += 1

    world.para()
    world.say(
        f"After that, {quail.id} curled up beside the clean space, {child.id} settled onto the {prize.label}, "
        f"and the whole kindergarten grew quiet enough for bedtime."
    )
    world.say(
        f"The coal stayed put, the jest had done its kind work, and the little room looked ready for dreams."
    )


# ---------------------------------------------------------------------------
# Public generation functions
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    world = World(params.place)
    child = world.add(Entity(
        id=params.name,
        kind="character",
        type="child",
        meters={"mess": 0.0, "joy": 0.0, "sleepy": 1.0},
        memes={"worry": 0.0, "calm": 0.0, "joy": 0.0, "problem_solving": 1.0},
    ))
    teacher = world.add(Entity(
        id="Teacher",
        kind="character",
        type="teacher",
        label="teacher",
        meters={"worry": 0.0, "relief": 0.0},
        memes={"worry": 0.0, "calm": 0.0, "joy": 0.0, "problem_solving": 1.0},
    ))
    quail = world.add(Entity(
        id="Quail",
        kind="character",
        type="quail",
        label="quail",
        meters={"sleepy": 1.0, "joy": 0.0},
        memes={"worry": 1.0, "calm": 0.0, "joy": 0.0},
    ))
    coal = world.add(Entity(
        id="Coal",
        kind="thing",
        type="coal",
        label="coal",
        phrase="a small lump of coal",
        meters={"mess": 1.0},
        memes={"worry": 0.0},
    ))
    joke = world.add(Entity(
        id="Jest",
        kind="thing",
        type="jest",
        label="jest",
        phrase="a tiny jest",
        meters={"mess": 0.0},
        memes={"joy": 1.0},
    ))
    blanket = world.add(Entity(
        id="Blanket",
        kind="thing",
        type="blanket",
        label="blanket",
        phrase="a soft blue blanket",
        owner=child.id,
        caretaker=teacher.id,
        meters={"clean": 1.0, "mess": 0.0},
        plural=False,
    ))
    world.facts = {
        "child": child,
        "teacher": teacher,
        "quail": quail,
        "coal": coal,
        "jest": joke,
        "prize": blanket,
        "activity": activity,
        "params": params,
    }
    tell_story(world, child, teacher, quail, coal, joke, activity, blanket)
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f"Write a bedtime-story for kindergarten about {p.name}, a quail, a lump of coal, and a jest that solves a small problem.",
        f"Tell a gentle story set in kindergarten where a child named {p.name} uses a tiny joke to help a sleepy quail and clean up coal.",
        "Write a child-friendly problem-solving story with a cozy bedtime mood, a quail, coal, and a joke that brings calm.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    child = world.facts["child"]
    teacher = world.facts["teacher"]
    quail = world.facts["quail"]
    coal = world.facts["coal"]
    blanket = world.facts["prize"]

    return [
        QAItem(
            question=f"Who solved the little problem in the kindergarten story?",
            answer=f"{p.name} helped solve it by moving the {blanket.label} and working with the teacher to clean the coal mark.",
        ),
        QAItem(
            question=f"What did the jest do in the story?",
            answer=f"The jest made everyone feel lighter and calmer, so the group could solve the problem kindly.",
        ),
        QAItem(
            question=f"Why was the coal a problem?",
            answer=f"The coal left a dark smudge, so the room was not ready yet for a cozy bedtime rest.",
        ),
        QAItem(
            question=f"What did the quail need by the end?",
            answer=f"The quail needed a quiet, safe place to curl up, and by the end it had one beside the clean space.",
        ),
        QAItem(
            question=f"What kind of story was this?",
            answer=f"It was a bedtime-style kindergarten story about problem solving, with a quail, coal, and a jest.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quail?",
            answer="A quail is a small bird. Quail are quick, soft-footed, and often stay close to the ground.",
        ),
        QAItem(
            question="What is coal?",
            answer="Coal is a black rock that can be used as fuel. It can also leave dark marks when it gets dusty or smudgy.",
        ),
        QAItem(
            question="What is a jest?",
            answer="A jest is a joke or a playful funny remark that can make people smile.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means noticing what is wrong and choosing a careful way to make it better.",
        ),
        QAItem(
            question="Why can bedtime stories feel calming?",
            answer="Bedtime stories can feel calming because they are gentle, quiet, and help the listener settle down for sleep.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    asp_set = set(asp.atoms(model, "valid_story"))
    py_set = {("kindergarten", "bedtime", "blanket"), ("kindergarten", "nap", "pillow")}
    if asp_set == py_set:
        print(f"OK: clingo gate matches Python ({len(py_set)} stories).")
        return 0
    print("MISMATCH between clingo and Python.")
    print("ASP:", sorted(asp_set))
    print("PY :", sorted(py_set))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Kindergarten bedtime problem-solving story world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or "kindergarten"
    activity = args.activity or rng.choice(list(ACTIVITIES))
    prize = args.prize or rng.choice(list(PRIZES))
    if not valid_combo(activity, prize):
        raise StoryError(explain_rejection(activity, prize))
    name = args.name or rng.choice(CHARACTER_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
    StoryParams(place="kindergarten", activity="bedtime", prize="blanket", name="Mina", trait="gentle"),
    StoryParams(place="kindergarten", activity="nap", prize="pillow", name="Theo", trait="curious"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        stories = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(stories)} compatible stories:")
        for s in stories:
            print(" ", s)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
