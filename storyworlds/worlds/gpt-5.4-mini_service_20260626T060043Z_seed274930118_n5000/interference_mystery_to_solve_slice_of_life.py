#!/usr/bin/env python3
"""
storyworlds/worlds/interference_mystery_to_solve_slice_of_life.py
=================================================================

A small slice-of-life storyworld about a gentle mystery caused by
interference: a child wants to enjoy an ordinary moment, but a strange
buzz, hiss, or crackle gets in the way. The solution comes from noticing
details, testing a few ideas, and moving the source of the trouble.

Premise used to build the world:
- A child is trying to enjoy a quiet everyday thing at home.
- A bit of interference makes a device act wrong.
- The child and parent investigate together.
- They find the cause and fix it.
- The ending proves the ordinary moment is peaceful again.

The world model tracks physical meters and emotional memes, and the prose is
driven by those state changes rather than a frozen template.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    worn_by: Optional[str] = None
    source_of: str = ""

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    key: str
    label: str
    afford: set[str] = field(default_factory=set)


@dataclass
class Problem:
    key: str
    symptom: str
    clue: str
    cause_kind: str
    cause_label: str
    fix_label: str
    fix_action: str
    solved_image: str


@dataclass
class StoryParams:
    place: str
    problem: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place, problem: Problem):
        self.place = place
        self.problem = problem
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

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
        import copy
        clone = World(self.place, self.problem)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


PLACES = {
    "living_room": Place("living_room", "the living room", {"listen", "read"}),
    "kitchen": Place("kitchen", "the kitchen", {"listen", "snack"}),
    "bedroom": Place("bedroom", "the bedroom", {"listen", "read"}),
}

PROBLEMS = {
    "radio_static": Problem(
        key="radio_static",
        symptom="a crackly static",
        clue="the sound got worse when the small charger was plugged in",
        cause_kind="charger",
        cause_label="the phone charger",
        fix_label="the charger",
        fix_action="unplug the charger and move it away",
        solved_image="the song came through clear and warm",
    ),
    "lamp_hum": Problem(
        key="lamp_hum",
        symptom="a low humming buzz",
        clue="the noise changed when the reading lamp was turned on",
        cause_kind="lamp",
        cause_label="the desk lamp",
        fix_label="the lamp",
        fix_action="switch off the lamp for a moment",
        solved_image="the room went soft and quiet again",
    ),
    "toy_whine": Problem(
        key="toy_whine",
        symptom="a tiny whining whistle",
        clue="the whistle followed the toy car with the blinking lights",
        cause_kind="toy",
        cause_label="the blinking toy car",
        fix_label="the toy car",
        fix_action="roll the toy car into the hall",
        solved_image="the music and the room finally matched",
    ),
}


GIRL_NAMES = ["Mia", "Nora", "Lina", "Ava", "Zoe", "Ruby", "Ella"]
BOY_NAMES = ["Ben", "Leo", "Milo", "Theo", "Owen", "Finn", "Max"]
TRAITS = ["curious", "quiet", "careful", "thoughtful", "patient", "gentle"]


def invalid_combo(place: str, problem: str) -> Optional[str]:
    if place not in PLACES:
        return "unknown place"
    if problem not in PROBLEMS:
        return "unknown problem"
    if "listen" not in PLACES[place].afford:
        return "that place doesn't support the listening story"
    return None


def choose_fix_problem(problem: Problem) -> str:
    return problem.fix_action


def build_story(world: World, params: StoryParams) -> World:
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        memes={"curiosity": 0.0, "calm": 0.0, "joy": 0.0, "worry": 0.0},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=params.parent,
        label="the parent",
        memes={"calm": 0.0, "care": 0.0},
    ))
    device = world.add(Entity(
        id="device",
        type="thing",
        label="the little speaker",
        phrase="a little speaker",
        owner=hero.id,
        caretaker=parent.id,
        meters={"static": 0.0},
    ))
    cause = world.add(Entity(
        id="cause",
        type=world.problem.cause_kind,
        label=world.problem.cause_label,
        phrase=world.problem.cause_label,
        source_of="interference",
    ))

    world.say(f"{hero.id} was a {params.trait} little {params.gender} who liked quiet afternoons in {world.place.label}.")
    world.say(f"{hero.id} loved listening to songs on {device.label} while {parent.label} tidied up nearby.")
    world.say(f"One day, {device.label} made {world.problem.symptom} instead of a clear tune.")

    world.para()
    world.say(f"{hero.id} frowned and listened closer.")
    world.say(f"{world.problem.clue.capitalize()}, {hero.pronoun('possessive')} {parent.type if params.parent in {'mother', 'father'} else 'parent'} noticed.")
    hero.memes["worry"] += 1.0
    hero.memes["curiosity"] += 1.0
    device.meters["static"] += 1.0

    world.say(f"{hero.id} looked around the room like {hero.pronoun()} was solving a tiny puzzle.")
    world.say(f"{parent.pronoun('subject').capitalize()} said, 'Let's check what is making the interference.'")

    world.para()
    world.say(f"They tried one small change at a time.")
    if world.problem.key == "radio_static":
        world.say(f"When {parent.label} unplugged {cause.label}, the crackle softened right away.")
    elif world.problem.key == "lamp_hum":
        world.say(f"When the lamp was switched off, the humming buzz dropped almost to nothing.")
    else:
        world.say(f"When {cause.label} was rolled into the hall, the whistle stopped chasing the sound.")
    world.say(f"That was the clue they needed.")

    world.para()
    world.say(f"They used {choose_fix_problem(world.problem)}.")
    device.meters["static"] = 0.0
    hero.memes["worry"] = 0.0
    hero.memes["joy"] += 1.0
    parent.memes["care"] += 1.0
    parent.memes["calm"] += 1.0

    world.say(f"Then {world.problem.solved_image}, and {hero.id} smiled so wide it made the whole room feel easy.")
    world.say(f"{hero.id} sat back down and listened all the way through while {parent.label} folded the last towel.")
    world.say(f"It was just an ordinary day again, only quieter and nicer than before.")

    world.facts.update(
        hero=hero,
        parent=parent,
        device=device,
        cause=cause,
        problem=world.problem,
        place=world.place,
        params=params,
        solved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    problem = f["problem"]
    place = f["place"]
    return [
        f'Write a slice-of-life mystery story for a young child about "{problem.key}" in {place.label}.',
        f"Tell a gentle story where {hero.id} notices interference, investigates, and finds the cause.",
        f"Write a short home story about a small sound problem that gets solved by looking carefully.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    problem = f["problem"]
    place = f["place"]
    return [
        QAItem(
            question=f"What was the mystery in {place.label}?",
            answer=f"The mystery was {problem.symptom}, a kind of interference that made the room's sound go wrong.",
        ),
        QAItem(
            question=f"What clue helped {hero.id} and {parent.label} solve it?",
            answer=f"The clue was that {problem.clue}. That pointed them toward the source of the trouble.",
        ),
        QAItem(
            question=f"How did they fix the problem?",
            answer=f"They fixed it by {choose_fix_problem(problem)}.",
        ),
        QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt happy and calm again when {problem.solved_image} and the room was peaceful.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is interference?",
            answer="Interference is when one signal or sound gets in the way of another one, so it sounds crackly, buzzy, or mixed up.",
        ),
        QAItem(
            question="What do you do when a mystery has a clue?",
            answer="You look carefully, try a sensible idea, and use the clue to figure out what is causing the problem.",
        ),
        QAItem(
            question="Why do people move a noisy device away?",
            answer="People move a noisy device away because distance can stop one thing from disturbing another thing nearby.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== story qa ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== world qa ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"{e.id}: {e.type} " + " ".join(bits))
    return "\n".join(lines)


@dataclass
class StoryChoice:
    place: str
    problem: str


CURATED = [
    StoryParams(place="living_room", problem="radio_static", name="Mia", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="bedroom", problem="lamp_hum", name="Leo", gender="boy", parent="father", trait="careful"),
    StoryParams(place="kitchen", problem="toy_whine", name="Nora", gender="girl", parent="mother", trait="thoughtful"),
]


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pk, place in PLACES.items():
        lines.append(asp.fact("place", pk))
        for a in sorted(place.afford):
            lines.append(asp.fact("affords", pk, a))
    for prk, problem in PROBLEMS.items():
        lines.append(asp.fact("problem", prk))
        lines.append(asp.fact("symptom", prk, problem.symptom))
        lines.append(asp.fact("cause_kind", prk, problem.cause_kind))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Problem) :- place(Place), problem(Problem), affords(Place, listen).

#show valid/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(p, pr) for p in PLACES for pr in PROBLEMS if "listen" in PLACES[p].afford}
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches python gate ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("python-only:", sorted(py - cl))
    print("clingo-only:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life mystery storyworld about interference.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
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
    if args.place and args.problem:
        if invalid_combo(args.place, args.problem):
            raise StoryError("That combination does not make a good interference mystery.")
    place = args.place or rng.choice(list(PLACES))
    problem = args.problem or rng.choice(list(PROBLEMS))
    gender = args.gender or rng.choice(["girl", "boy"])
    parent = args.parent or rng.choice(["mother", "father"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, problem=problem, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    place = PLACES[params.place]
    problem = PROBLEMS[params.problem]
    world = build_world(place, problem, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def build_world(place: Place, problem: Problem, params: StoryParams) -> World:
    world = World(place, problem)
    return build_story(world, params)


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
        vals = asp_valid()
        print(f"{len(vals)} valid (place, problem) pairs:")
        for place, problem in vals:
            print(f"  {place}  {problem}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(100, args.n * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
