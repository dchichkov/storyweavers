#!/usr/bin/env python3
"""
A small animal-story world with foreshadowing and problem solving.

Premise:
A young raccoon wears favorite overalls every day. He has a habit of rummaging
near berry bushes. One day he finds a snake's shed skin and hears a warning
about venom in the marsh. When a problem appears, he uses a clever plan to stay
safe, help a friend, and keep his overalls clean.
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

ANIMAL_TYPES = {
    "raccoon": {"pronoun": "he", "possessive": "his", "object": "him"},
    "fox": {"pronoun": "she", "possessive": "her", "object": "her"},
    "rabbit": {"pronoun": "she", "possessive": "her", "object": "her"},
    "badger": {"pronoun": "he", "possessive": "his", "object": "him"},
}

SETTINGS = {
    "marsh": "the marsh",
    "berry_patch": "the berry patch",
    "woodland": "the woodland path",
    "riverbank": "the riverbank",
}

HABITS = {
    "rummage": "rummaging through roots and leaves",
    "sniff": "sniffing out berries and seeds",
    "skip_stones": "skipping stones by the water",
    "collect": "collecting shiny things in a pouch",
}

PROBLEMS = {
    "snake_warning": "a warning about a snake with venom",
    "thorn_patch": "a patch of thorny vines",
    "mud_puddle": "a deep mud puddle",
}

SOLUTIONS = {
    "stick_bridge": "laying a little stick bridge",
    "back_away": "backing away slowly and taking another path",
    "share_overalls": "using the extra overalls as a dry cover",
    "wash_and_wait": "washing up first and waiting for safer weather",
}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        info = ANIMAL_TYPES.get(self.type, {"pronoun": "it", "possessive": "its", "object": "it"})
        if case == "subject":
            return info["pronoun"]
        if case == "possessive":
            return info["possessive"]
        return info["object"]


@dataclass
class StoryParams:
    animal: str
    setting: str
    habit: str
    problem: str
    solution: str
    name: str
    seed: Optional[int] = None


@dataclass
class World:
    params: StoryParams
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


ASP_RULES = r"""
#show valid/4.

animal(raccoon;fox;rabbit;badger).
setting(marsh;berry_patch;woodland;riverbank).
habit(rummage;sniff;skip_stones;collect).
problem(snake_warning;thorn_patch;mud_puddle).
solution(stick_bridge;back_away;share_overalls;wash_and_wait).

compatible(raccoon, marsh, snake_warning, back_away).
compatible(raccoon, berry_patch, thorn_patch, stick_bridge).
compatible(fox, woodland, thorn_patch, back_away).
compatible(rabbit, riverbank, mud_puddle, share_overalls).
compatible(badger, woodland, snake_warning, wash_and_wait).

valid(A,S,P,L) :- compatible(A,S,P,L).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for a in ANIMAL_TYPES:
        lines.append(asp.fact("animal", a))
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for h in HABITS:
        lines.append(asp.fact("habit", h))
    for p in PROBLEMS:
        lines.append(asp.fact("problem", p))
    for sol in SOLUTIONS:
        lines.append(asp.fact("solution", sol))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def story_setup(world: World) -> tuple[Entity, Entity, Entity]:
    p = world.params
    hero = world.add(Entity(
        id=p.name,
        kind="character",
        type=p.animal,
        label=p.name,
        meters={"calm": 1.0, "caution": 0.0, "venom_risk": 0.0},
        memes={"habit": 1.0, "worry": 0.0, "hope": 0.0},
    ))
    overalls = world.add(Entity(
        id="overalls",
        type="overalls",
        label="overalls",
        phrase="blue overalls with a big front pocket",
        owner=hero.id,
        worn_by=hero.id,
        meters={"clean": 1.0, "sturdy": 1.0},
    ))
    friend = world.add(Entity(
        id="mole",
        kind="character",
        type="animal",
        label="Milo the mole",
        meters={"worry": 0.0},
        memes={"trust": 1.0},
    ))
    return hero, overalls, friend


def narrate(world: World) -> None:
    p = world.params
    hero, overalls, friend = story_setup(world)
    place = SETTINGS[p.setting]
    habit = HABITS[p.habit]
    problem = PROBLEMS[p.problem]
    solution = SOLUTIONS[p.solution]

    world.say(
        f"{hero.label} was a small {p.animal} who loved his overalls and had a habit of {habit}."
    )
    world.say(
        f"Every morning, {hero.label} tugged at the straps of the overalls and smiled, because they made him feel ready for a big day."
    )
    world.say(
        f"One bright day, he headed to {place}, and the wind made the reeds whisper like they were trying to tell a secret."
    )

    world.para()
    world.say(
        f"Along the way, {hero.label} found a shed snake skin near the mud, and that was the first foreshadowing that something tricky was close."
    )
    world.say(
        f"{friend.label} pointed to the marsh and said that {problem.replace('_', ' ')} meant they should be careful, because venom can hurt little animals."
    )
    hero.meters["venom_risk"] = 1.0
    hero.memes["worry"] = 1.0
    world.facts["foreshadowed"] = True

    world.para()
    world.say(
        f"Soon they came to a problem: a narrow gap blocked the trail, and the safest path was hidden by roots and wet leaves."
    )
    world.say(
        f"{hero.label} almost rushed ahead out of habit, but then he remembered the warning and stopped."
    )
    world.say(
        f"Instead of pushing forward, he used a problem-solving plan: {solution}."
    )

    if p.solution == "back_away":
        world.say(
            f"He stepped back slowly, and {friend.label} followed him to the higher ground, where the air smelled fresh and safe."
        )
    elif p.solution == "stick_bridge":
        world.say(
            f"He gathered tiny sticks with his paws and made a careful bridge so they could cross without touching the messy ground."
        )
    elif p.solution == "share_overalls":
        world.say(
            f"He wrapped the extra overalls around the slick spot, which kept the mud off his own clothes and gave the trail a dry edge."
        )
    else:
        world.say(
            f"They washed their paws in the stream first, waited for the breeze to clear the mist, and only then continued."
        )

    hero.meters["calm"] = 1.0
    hero.memes["hope"] = 1.0
    hero.memes["worry"] = 0.0
    overalls.meters["clean"] = 1.0
    world.facts["resolved"] = True
    world.facts["hero"] = hero
    world.facts["friend"] = friend
    world.facts["overalls"] = overalls


def generation_prompts(world: World) -> list[str]:
    p = world.params
    return [
        f'Write an animal story for young children that includes "venom", "habit", and "overalls".',
        f"Tell a gentle story about {p.name}, a {p.animal}, who must solve a problem without ignoring a warning.",
        f"Write a short foreshadowing story where a small animal notices danger early and uses a clever plan.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {p.name}, a small {p.animal} who loves his overalls and has a helpful habit.",
        ),
        QAItem(
            question="What warning did the animal notice before the problem got bigger?",
            answer="He noticed a shed snake skin near the marsh, which foreshadowed that venom could be nearby.",
        ),
        QAItem(
            question="How did the animal solve the problem?",
            answer=f"He stopped, thought carefully, and used {SOLUTIONS[p.solution].replace('_', ' ')} instead of rushing ahead.",
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer="The danger was handled, the overalls stayed clean, and the animal finished the day feeling calm and proud.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is venom?",
            answer="Venom is a poison that some animals make to protect themselves or catch food.",
        ),
        QAItem(
            question="What are overalls?",
            answer="Overalls are clothes with straps and legs that cover most of the body and help keep other clothes clean.",
        ),
        QAItem(
            question="What does a habit mean?",
            answer="A habit is something someone does again and again until it becomes a regular way of acting.",
        ),
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is when a story gives a small hint early on that something important will happen later.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World knowledge ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world with venom, habit, and overalls.")
    ap.add_argument("--animal", choices=sorted(ANIMAL_TYPES))
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--habit", choices=sorted(HABITS))
    ap.add_argument("--problem", choices=sorted(PROBLEMS))
    ap.add_argument("--solution", choices=sorted(SOLUTIONS))
    ap.add_argument("--name")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    animal = args.animal or rng.choice(list(ANIMAL_TYPES))
    setting = args.setting or rng.choice(list(SETTINGS))
    habit = args.habit or rng.choice(list(HABITS))
    problem = args.problem or rng.choice(list(PROBLEMS))
    solution = args.solution or rng.choice(list(SOLUTIONS))
    name = args.name or rng.choice(["Pip", "Nico", "Luna", "Toby", "Mina"])

    explicit = [args.animal, args.setting, args.habit, args.problem, args.solution]
    if explicit.count(None) < 5:
        valid = {
            ("raccoon", "marsh", "rummage", "snake_warning", "back_away"),
            ("fox", "woodland", "sniff", "thorn_patch", "back_away"),
            ("rabbit", "riverbank", "skip_stones", "mud_puddle", "share_overalls"),
            ("badger", "berry_patch", "collect", "snake_warning", "wash_and_wait"),
            ("raccoon", "berry_patch", "rummage", "thorn_patch", "stick_bridge"),
        }
        if (animal, setting, habit, problem, solution) not in valid:
            raise StoryError("The chosen animal, setting, problem, and solution do not fit together well.")

    return StoryParams(animal=animal, setting=setting, habit=habit, problem=problem, solution=solution, name=name)


def generate(params: StoryParams) -> StorySample:
    world = World(params)
    narrate(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
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


CURATED = [
    StoryParams(animal="raccoon", setting="marsh", habit="rummage", problem="snake_warning", solution="back_away", name="Pip"),
    StoryParams(animal="fox", setting="woodland", habit="sniff", problem="thorn_patch", solution="back_away", name="Luna"),
    StoryParams(animal="rabbit", setting="riverbank", habit="skip_stones", problem="mud_puddle", solution="share_overalls", name="Toby"),
    StoryParams(animal="badger", setting="berry_patch", habit="collect", problem="snake_warning", solution="wash_and_wait", name="Mina"),
]


def asp_verify() -> int:
    import asp
    program = asp_program("#show valid/4.")
    model = asp.one_model(program)
    clingo_set = set(asp.atoms(model, "valid"))
    python_set = {
        ("raccoon", "marsh", "snake_warning", "back_away"),
        ("fox", "woodland", "thorn_patch", "back_away"),
        ("rabbit", "riverbank", "mud_puddle", "share_overalls"),
        ("badger", "berry_patch", "snake_warning", "wash_and_wait"),
        ("raccoon", "berry_patch", "thorn_patch", "stick_bridge"),
    }
    if clingo_set == python_set:
        print(f"OK: clingo gate matches python set ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and python sets:")
    print("clingo only:", sorted(clingo_set - python_set))
    print("python only:", sorted(python_set - clingo_set))
    return 1


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid()
        print(f"{len(combos)} compatible story combos:")
        for item in combos:
            print(" ", item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < args.n * 50:
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
