#!/usr/bin/env python3
"""
Storyworld: shout_sound_effects_problem_solving_reconciliation_adventure
=========================================================================

A small adventure story domain about a child, a noisy shout, a mishap, and a
kind reconciliation. The simulated world tracks both physical state (meters)
and feelings (memes), then renders a child-facing tale with a clear turn and
resolution.

Premise:
- A child loves adventure sounds and exploring.
- A shout startles a friend and causes a small problem.
- The group uses careful problem solving to fix it.
- They reconcile and continue the adventure together.

This world keeps the focus on sound effects, problem solving, reconciliation,
and an adventure-like feel.
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
# Data model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    partner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ("noise", "mess", "lost", "fixed", "travel"):
            self.meters.setdefault(key, 0.0)
        for key in ("joy", "worry", "hurt", "anger", "relief", "friendship"):
            self.memes.setdefault(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        male = {"boy", "father", "dad", "man"}
        female = {"girl", "mother", "mom", "woman"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def them(self) -> str:
        return "them" if self.plural else "it"


@dataclass(frozen=True)
class Place:
    id: str
    label: str
    feature: str
    mood: str
    adventure_word: str


@dataclass(frozen=True)
class SoundEffect:
    id: str
    word: str
    followup: str
    causes: str


@dataclass(frozen=True)
class Problem:
    id: str
    label: str
    trouble: str
    fix: str
    requires: str


@dataclass(frozen=True)
class Reconciliation:
    id: str
    phrase: str
    result: str


@dataclass
class StoryParams:
    place: str
    sound: str
    problem: str
    name: str
    gender: str
    friend: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES: dict[str, Place] = {
    "trail": Place("trail", "the pine trail", "twisting roots", "windy", "explore"),
    "cave": Place("cave", "the echo cave", "echoing walls", "dark", "venture"),
    "bridge": Place("bridge", "the old rope bridge", "swaying boards", "high", "cross"),
    "river": Place("river", "the splashy riverbank", "shiny stones", "bright", "roam"),
}

SOUNDS: dict[str, SoundEffect] = {
    "shout": SoundEffect("shout", "shout", "a loud echo bounced back", "startled the friend"),
    "clang": SoundEffect("clang", "clang", "a bright ringing filled the air", "knocked over a tin marker"),
    "whoosh": SoundEffect("whoosh", "whoosh", "the breeze rushed past", "spooked a flock of birds"),
}

PROBLEMS: dict[str, Problem] = {
    "lost_map": Problem("lost_map", "lost map", "the map blew away", "follow the footprints and listen for clues", "the wind"),
    "scared_friend": Problem("scared_friend", "scared friend", "a friend felt hurt and upset", "apologize, explain, and fix the mistake", "a loud sound"),
    "blocked_path": Problem("blocked_path", "blocked path", "a fallen branch blocked the way", "work together and move it carefully", "strong hands"),
}

RECONCILIATIONS: dict[str, Reconciliation] = {
    "apology": Reconciliation("apology", "I'm sorry", "their friendship felt steady again"),
    "shared_task": Reconciliation("shared_task", "let's fix it together", "the team felt brave again"),
    "kind_echo": Reconciliation("kind_echo", "we can try again", "the adventure felt warm and safe"),
}

GIRL_NAMES = ["Ava", "Mila", "Nora", "Zoe", "Lina", "Ivy", "Maya"]
BOY_NAMES = ["Leo", "Finn", "Noah", "Theo", "Eli", "Max", "Owen"]
FRIENDS = ["friend", "buddy", "cousin", "neighbor"]
GENDERS = {"girl", "boy"}


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld with shout sound effects, problem solving, and reconciliation.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--sound", choices=sorted(SOUNDS))
    ap.add_argument("--problem", choices=sorted(PROBLEMS))
    ap.add_argument("--gender", choices=sorted(GENDERS))
    ap.add_argument("--friend")
    ap.add_argument("--name")
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


def compatible(place: Place, sound: SoundEffect, problem: Problem) -> bool:
    if sound.id == "shout" and problem.id == "scared_friend":
        return True
    if sound.id == "clang" and problem.id == "blocked_path":
        return True
    if sound.id == "whoosh" and problem.id == "lost_map":
        return True
    return False


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for p in PLACES.values():
        for s in SOUNDS.values():
            for pr in PROBLEMS.values():
                if compatible(p, s, pr):
                    out.append((p.id, s.id, pr.id))
    return out


def explain_rejection(sound: SoundEffect, problem: Problem) -> str:
    return f"(No story: {sound.word} does not fit the {problem.label} well enough for this adventure.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.sound and args.problem and not compatible(PLACES[next(iter(PLACES))], SOUNDS[args.sound], PROBLEMS[args.problem]):
        # The place does not matter for compatibility in this small domain.
        if (args.sound, args.problem) not in {(s, p) for _, s, p in valid_combos()}:
            raise StoryError(explain_rejection(SOUNDS[args.sound], PROBLEMS[args.problem]))

    combos = valid_combos()
    combos = [c for c in combos if (args.place is None or c[0] == args.place)
              and (args.sound is None or c[1] == args.sound)
              and (args.problem is None or c[2] == args.problem)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place_id, sound_id, problem_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    friend = args.friend or rng.choice(FRIENDS)
    return StoryParams(place=place_id, sound=sound_id, problem=problem_id, name=name, gender=gender, friend=friend)


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    world = World(PLACES[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    friend = world.add(Entity(id="friend", kind="character", type="friend", label=params.friend))
    sound = SOUNDS[params.sound]
    problem = PROBLEMS[params.problem]
    recon = RECONCILIATIONS["apology" if problem.id == "scared_friend" else "shared_task"]

    world.facts.update(hero=hero, friend=friend, sound=sound, problem=problem, recon=recon, params=params)

    hero.memes["joy"] += 1
    world.say(f"{hero.id} loved adventure days at {world.place.label}. {hero.pronoun().capitalize()} liked the {world.place.feature} and the chance to explore.")

    world.say(f"One day, {hero.id} and {friend.label} went to {world.place.label}. The air felt {world.place.mood}, like the world was waiting for a new path.")

    world.para()
    hero.meters["travel"] += 1
    hero.meters["noise"] += 1
    friend.memes["worry"] += 1
    world.say(f"Then {hero.id} gave a {sound.word}! {sound.followup}.")
    world.say(f"It {sound.causes}, and {friend.label} flinched.")

    problem_obj = problem
    friend.memes["hurt"] += 1
    hero.memes["worry"] += 1
    world.say(f"That made a {problem_obj.label}: {problem_obj.trouble}.")
    world.say(f"{hero.id} saw the trouble and knew {problem_obj.fix} would help.")

    world.para()
    hero.meters["fixed"] += 1
    world.say(f"{hero.id} took a deep breath, looked at {friend.label}, and started to solve the problem.")
    if problem_obj.id == "lost_map":
        hero.meters["lost"] += 1
        world.say(f"{hero.id} followed tiny footprints beside the trail and listened for the next clue.")
    elif problem_obj.id == "scared_friend":
        world.say(f"{hero.id} said {recon.phrase}, then explained that the shout was only meant as an adventure call.")
    else:
        world.say(f"{hero.id} and {friend.label} pushed the branch together, inch by inch, until the path opened.")

    world.say(f"That was careful problem solving, and soon the fix was done.")

    world.para()
    hero.memes["relief"] += 1
    hero.memes["friendship"] += 1
    friend.memes["relief"] += 1
    friend.memes["friendship"] += 1
    friend.memes["worry"] = 0.0
    hero.memes["worry"] = 0.0
    world.say(f"{friend.label} smiled again, and {recon.result}.")
    world.say(f"At the end, {hero.id} and {friend.label} kept exploring the {world.place.feature}, but this time they used a smaller voice and a kinder plan.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p: StoryParams = f["params"]
    sound: SoundEffect = f["sound"]
    problem: Problem = f["problem"]
    return [
        f'Write a short adventure story for a young child that includes the word "{sound.word}" and ends with reconciliation.',
        f"Tell a story about {p.name}, a {p.gender}, who makes a {sound.word} sound at {world.place.label} and then solves a {problem.label}.",
        f"Write a gentle adventure with sound effects, problem solving, and a happy reunion after a mistake.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p: StoryParams = f["params"]
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    sound: SoundEffect = f["sound"]
    problem: Problem = f["problem"]
    recon: Reconciliation = f["recon"]
    return [
        QAItem(
            question=f"Where did {hero.id} and {friend.label} go in the story?",
            answer=f"They went to {world.place.label}, where the trail felt like a real adventure.",
        ),
        QAItem(
            question=f"What sound did {hero.id} make that caused trouble?",
            answer=f"{hero.id} made a {sound.word}, and it startled {friend.label}.",
        ),
        QAItem(
            question=f"What was the problem in the middle of the story?",
            answer=f"The problem was {problem.label}: {problem.trouble}.",
        ),
        QAItem(
            question=f"How did {hero.id} fix the problem?",
            answer=f"{hero.id} used careful problem solving and then said {recon.phrase} so {friend.label} could feel better.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} and {friend.label} exploring together again, feeling calm and friendly.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a shout?",
            answer="A shout is a very loud voice sound that people can hear from far away.",
        ),
        QAItem(
            question="Why can loud sounds upset someone?",
            answer="A loud sound can startle someone because it happens suddenly and feels surprising.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means thinking carefully about a trouble and choosing a way to fix it.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people make up again after a problem and feel friendly and safe together.",
        ),
    ]


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(P) :- place_fact(P).
sound(S) :- sound_fact(S).
problem(P) :- problem_fact(P).

compatible(trail, shout, scared_friend).
compatible(cave, shout, scared_friend).
compatible(bridge, clang, blocked_path).
compatible(trail, whoosh, lost_map).

valid(Place, Sound, Problem) :- compatible(Place, Sound, Problem).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place_fact", p))
    for s in SOUNDS:
        lines.append(asp.fact("sound_fact", s))
    for pr in PROBLEMS:
        lines.append(asp.fact("problem_fact", pr))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    print("python-only:", sorted(py - cl))
    print("clingo-only:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Emit / main
# ---------------------------------------------------------------------------
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
    StoryParams(place="trail", sound="shout", problem="scared_friend", name="Ava", gender="girl", friend="buddy"),
    StoryParams(place="cave", sound="shout", problem="scared_friend", name="Leo", gender="boy", friend="cousin"),
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
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen: set[str] = set()
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
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
            header = f"### {p.name}: {p.sound} at {p.place} ({p.problem})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
