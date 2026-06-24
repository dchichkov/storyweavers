#!/usr/bin/env python3
"""
Standalone storyworld: a small superhero tale with humor and a lesson learned.

Seed idea:
- A kid hero tries to solve a silly city problem with too much confidence.
- A harmless mishap turns into a lesson about teamwork and paying attention.
- The ending proves the hero learned something, while keeping the tone playful.

This world models a tiny superhero domain with:
- physical meters: strength, speed, splash, damage, tidiness, gadget_charge
- emotional memes: pride, worry, courage, relief, delight, teamwork

Story style:
- child-facing superhero story
- concrete action
- a humorous turn
- a clear lesson learned at the end
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.meters:
            self.meters = {
                "strength": 0.0,
                "speed": 0.0,
                "splash": 0.0,
                "damage": 0.0,
                "tidiness": 0.0,
                "gadget_charge": 0.0,
            }
        if not self.memes:
            self.memes = {
                "pride": 0.0,
                "worry": 0.0,
                "courage": 0.0,
                "relief": 0.0,
                "delight": 0.0,
                "teamwork": 0.0,
            }

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)

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


@dataclass
class HeroSpec:
    name: str
    type: str
    trait: str
    codename: str


@dataclass
class ProblemSpec:
    id: str
    label: str
    mishap: str
    risk: str
    fix_hint: str
    humor: str
    required_meter: str
    required_memes: tuple[str, str]


@dataclass
class SidekickSpec:
    id: str
    label: str
    type: str
    helper_line: str
    fix_action: str


SETTINGS = {
    "city": "the busy city square",
    "school": "the schoolyard",
    "museum": "the tiny museum hall",
    "park": "the playground park",
}

HEROES = [
    HeroSpec("Maya", "girl", "curious", "Captain Comet"),
    HeroSpec("Leo", "boy", "brave", "Thunder Kid"),
    HeroSpec("Nia", "girl", "silly", "The Bubble Bolt"),
    HeroSpec("Owen", "boy", "quick", "Mini Meteor"),
]

PROBLEMS = {
    "abcd": ProblemSpec(
        id="abcd",
        label="the alphabet drone",
        mishap="kept dropping glitter letters all over the street",
        risk="it could tangle the parade banner",
        fix_hint="a careful plan",
        humor="it sneezed out a perfect little 'achoo' of alphabet confetti",
        required_meter="splash",
        required_memes=("pride", "worry"),
    ),
    "kite": ProblemSpec(
        id="kite",
        label="the runaway kite",
        mishap="was zigzagging above the roofs like a paper fish",
        risk="it might snag on a tall clocktower",
        fix_hint="a long, gentle climb",
        humor="it waved as if it knew the whole town was watching",
        required_meter="speed",
        required_memes=("courage", "worry"),
    ),
    "puddle_robot": ProblemSpec(
        id="puddle_robot",
        label="a squeaky puddle robot",
        mishap="kept rolling into puddles and making funny squeaks",
        risk="it could short out its own music box",
        fix_hint="dry shoes and a towel",
        humor="every squeak sounded like a tiny trumpet honk",
        required_meter="splash",
        required_memes=("delight", "worry"),
    ),
}

SIDEKICKS = [
    SidekickSpec("mop", "Mop Mouse", "mouse", "It waved a tiny mop and offered help.", "mopped the mess"),
    SidekickSpec("drone", "Dot Drone", "robot", "It beeped politely and pointed to the safe path.", "scanned the route"),
    SidekickSpec("cap", "Captain Cap", "adult", "It smiled and said the safest hero plans are the smartest.", "held the ladder"),
]


@dataclass
class StoryParams:
    place: str
    hero: str
    problem: str
    sidekick: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld with a lesson learned and a little humor.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hero", choices=[h.name for h in HEROES])
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--sidekick", choices=[s.id for s in SIDEKICKS])
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
    place = args.place or rng.choice(list(SETTINGS))
    hero = args.hero or rng.choice([h.name for h in HEROES])
    problem = args.problem or rng.choice(list(PROBLEMS))
    sidekick = args.sidekick or rng.choice([s.id for s in SIDEKICKS])
    return StoryParams(place=place, hero=hero, problem=problem, sidekick=sidekick)


def _hero_spec(name: str) -> HeroSpec:
    for h in HEROES:
        if h.name == name:
            return h
    raise StoryError("unknown hero")


def _problem_spec(pid: str) -> ProblemSpec:
    return PROBLEMS[pid]


def _sidekick_spec(sid: str) -> SidekickSpec:
    for s in SIDEKICKS:
        if s.id == sid:
            return s
    raise StoryError("unknown sidekick")


def reasonableness_gate(params: StoryParams) -> None:
    if params.place == "museum" and params.problem == "abcd":
        raise StoryError("The alphabet drone is too loud for the tiny museum hall in this storyworld.")
    if params.place == "park" and params.problem == "puddle_robot":
        return
    if params.problem == "abcd" and params.sidekick == "cap":
        return


def ASP_RULES = r"""
hero(H) :- hero_name(H).
problem(P) :- problem_name(P).
sidekick(S) :- sidekick_name(S).
place(Pl) :- place_name(Pl).

compatible(Pl, P, S) :- place(Pl), problem(P), sidekick(S), not bad_combo(Pl, P, S).

bad_combo("museum", "abcd", _).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for h in HEROES:
        lines.append(asp.fact("hero_name", h.name))
    for p in PROBLEMS:
        lines.append(asp.fact("problem_name", p))
    for s in SIDEKICKS:
        lines.append(asp.fact("sidekick_name", s.id))
    for pl in SETTINGS:
        lines.append(asp.fact("place_name", pl))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show compatible/3."))
    clingo_set = set(asp.atoms(model, "compatible"))
    python_set = set()
    for pl in SETTINGS:
        for p in PROBLEMS:
            for s in SIDEKICKS:
                if not (pl == "museum" and p == "abcd"):
                    python_set.add((pl, p, s.id))
    if clingo_set == python_set:
        print(f"OK: clingo gate matches python ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH")
    return 1


def _do_scene(world: World, hero: Entity, problem: ProblemSpec, sidekick: SidekickSpec) -> None:
    world.say(f"{hero.label} was {hero.traits[0]} and wore a bright cape called {hero.facts['codename']}.")
    world.say(f"At {world.place}, {problem.label} {problem.mishap}.")
    hero.memes["pride"] += 1
    hero.meters[problem.required_meter] += 1
    world.say(f"{hero.label} grinned and said, 'I can fix this fast!'")
    hero.memes["worry"] += 1
    world.say(f"But then {problem.humor}, and everybody blinked and laughed.")
    world.say(f"{sidekick.label} arrived. {sidekick.helper_line}")
    hero.memes["teamwork"] += 1
    hero.meters["tidiness"] += 1
    hero.memes["courage"] += 1
    hero.memes["relief"] += 1
    world.say(f"Together they {sidekick.fix_action}, which kept {problem.risk} from happening.")
    world.say(f"{hero.label} learned that a real hero asks for help when the plan needs a second pair of eyes.")
    world.say(f"By the end, the street was tidy, the crowd was smiling, and {hero.label} bowed with a sheepish grin.")


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    hero_spec = _hero_spec(params.hero)
    problem = _problem_spec(params.problem)
    sidekick = _sidekick_spec(params.sidekick)

    world = World(place=SETTINGS[params.place])
    hero = world.add(Entity(id=hero_spec.name, kind="character", type=hero_spec.type, label=hero_spec.name, traits=[hero_spec.trait]))
    hero.facts = {"codename": hero_spec.codename}
    world.facts.update(hero=hero_spec.name, problem=problem.id, sidekick=sidekick.id, place=params.place, codename=hero_spec.codename)

    _do_scene(world, hero, problem, sidekick)

    prompts = [
        "Write a short superhero story where a child hero learns a lesson after a funny mistake.",
        f"Tell a humorous story about {hero_spec.codename} and {problem.label}.",
        "Make the ending show that the hero learned to be careful and ask for help.",
    ]
    story_qa = [
        QAItem(
            question=f"What did {hero.label} learn in the story?",
            answer="The hero learned that being brave also means asking for help and making a careful plan.",
        ),
        QAItem(
            question=f"Why did everyone laugh during the problem at {params.place}?",
            answer=f"Everyone laughed because {problem.humor}, which made the moment funny instead of scary.",
        ),
        QAItem(
            question=f"Who helped {hero.label} with the fix?",
            answer=f"{sidekick.label} helped by staying calm and doing the safe part of the job.",
        ),
    ]
    world_qa = [
        QAItem(question="What is a superhero?", answer="A superhero is a person who helps others and solves big problems with courage and good choices."),
        QAItem(question="What is teamwork?", answer="Teamwork means people work together and share the job so it goes better."),
        QAItem(question="What does it mean to learn a lesson?", answer="It means a character understands a better way to act after something happens."),
    ]
    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
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


CURATED = [
    StoryParams(place="city", hero="Maya", problem="abcd", sidekick="drone"),
    StoryParams(place="park", hero="Leo", problem="puddle_robot", sidekick="mop"),
    StoryParams(place="school", hero="Nia", problem="kite", sidekick="cap"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show compatible/3."))
        combos = sorted(set(asp.atoms(model, "compatible")))
        for combo in combos[:20]:
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
