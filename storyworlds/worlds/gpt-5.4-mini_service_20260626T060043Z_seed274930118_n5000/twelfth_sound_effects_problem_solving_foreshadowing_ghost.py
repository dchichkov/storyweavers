#!/usr/bin/env python3
"""
storyworlds/worlds/twelfth_sound_effects_problem_solving_foreshadowing_ghost.py
================================================================================

A small standalone story world about a gentle ghost story with sound effects,
problem solving, and foreshadowing.

Seed tale:
---
On the twelfth chime of the old house clock, Maya heard a soft whooo from the
hallway. She and her grandmother were trying to find the missing music box key
before bedtime. A chilly draft, a tiny clink, and a dusty footprint kept
showing up in different rooms, like the house was leaving clues on purpose.

Maya followed the sounds to the attic. There, she found a shy ghost named Pip
nudging a loose board with a glowing finger. Under the board was the key, and
beside it was the music box itself. Pip had not stolen anything; he had been
trying to help. Maya thanked Pip, the box opened with a click, and the house
filled with a soft little song.

World model ideas:
---
- Physical meters: sound, chill, dust, stuckness, light, relief, solved.
- Emotional memes: worry, curiosity, bravery, trust, surprise, joy.
- Story beats:
    setup -> twelfth sound and foreshadowed clues
    tension -> missing key and spooky signs
    turn -> the child reasons about the clues
    resolution -> the ghost is friendly and the problem is solved

This script keeps the prose authored and state-driven, while still exposing a
small ASP twin for the reasonableness gate.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

TWELFTH = 12
THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    friendly: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "grandmother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "grandfather", "uncle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.kind == "ghost":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    clock_chimes: int = TWELFTH
    has_attic: bool = True
    has_hallway: bool = True


@dataclass
class Problem:
    id: str
    missing: str
    place: str
    sound_hint: str
    foreshadow: str
    solution_sound: str
    solution_action: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Ghost:
    id: str
    label: str
    phrase: str
    sound: str
    help_method: str
    hint_method: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _speaker_name(e: Entity) -> str:
    return e.label or e.id


def _article(name: str) -> str:
    return "an" if name[:1].lower() in "aeiou" else "a"


def _possessive_name(name: str) -> str:
    return f"{name}'s"


def _sound(world: World, text: str, meter: str = "sound") -> None:
    world.say(text)
    world.facts[meter] = world.facts.get(meter, 0.0) + 1.0


def _introduce(world: World, child: Entity, adult: Entity, problem: Problem, ghost: Ghost) -> None:
    world.say(
        f"On the twelfth chime of the old house clock, {child.id} heard "
        f"{ghost.sound} drift down the hallway."
    )
    world.say(
        f"{child.id} was staying in {world.setting.place} with {adult.label}, "
        f"and they were looking for the missing {problem.missing}."
    )
    child.memes["curiosity"] += 1
    child.memes["worry"] += 1
    world.facts["clue"] = problem.foreshadow


def _foreshadow(world: World, child: Entity, problem: Problem) -> None:
    world.say(
        f"A chilly draft slipped under the door, and a tiny {problem.foreshadow} "
        f"appeared where no one had seen it before."
    )
    world.say(
        f"{child.id} remembered the strange signs from earlier: the draft, the "
        f"little sound, and the way the attic door seemed to wait."
    )
    child.memes["curiosity"] += 1
    child.memes["bravery"] += 1
    world.facts["foreshadowed"] = True


def _search(world: World, child: Entity, adult: Entity, problem: Problem, ghost: Ghost) -> None:
    world.para()
    world.say(
        f"{child.id} and {adult.label} followed the clues. Creak, creak went the "
        f"stairs. Tap-tap, tap-tap answered the hallway floor."
    )
    world.say(
        f"They checked the sitting room, then the hall, then the attic stairs "
        f"where the air felt colder."
    )
    world.say(
        f"At last, {child.id} noticed a dusty footprint pointing toward the "
        f"{problem.place}."
    )
    child.memes["problem_solving"] = child.memes.get("problem_solving", 0.0) + 1.0
    world.facts["searched"] = True


def _reveal(world: World, child: Entity, ghost: Ghost, problem: Problem) -> None:
    world.say(
        f"In the attic, {ghost.id} floated near a loose board and made a soft "
        f"{ghost.sound} sound, like a whisper with a smile."
    )
    world.say(
        f'"I was not taking it," {ghost.id} said. "I was trying to help find '
        f"the {problem.missing}."'
    )
    world.say(
        f"{ghost.id} nudged the board with a glowing finger, and there was the "
        f"{problem.missing}, safe and shiny."
    )
    world.facts["ghost_helped"] = True
    world.facts["found"] = True


def _solve(world: World, child: Entity, adult: Entity, problem: Problem, ghost: Ghost) -> None:
    child.memes["trust"] += 1
    child.memes["joy"] += 1
    child.memes["worry"] = 0.0
    world.say(
        f"{child.id} smiled first, then laughed softly. The clues had been "
        f"leading to a helper all along."
    )
    world.say(
        f"{child.id} picked up the {problem.missing}, and the old box opened "
        f"with a bright click."
    )
    world.say(
        f"Then a tiny song spilled out: ding, ding, ding, all warm and gentle, "
        f"and the spooky house did not feel spooky anymore."
    )
    world.say(
        f"{adult.label} tucked the music box back in place, and {child.id} waved "
        f"goodbye to {ghost.id}."
    )
    world.say(
        f"By bedtime, the attic was quiet, the clock had finished its twelfth "
        f"chime, and the house felt friendly."
    )
    world.facts["solved"] = True


def tell(setting: Setting, problem: Problem, ghost: Ghost,
         child_name: str = "Maya", child_type: str = "girl",
         adult_label: str = "Grandma", adult_type: str = "grandmother") -> World:
    world = World(setting)
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_type,
        label=child_name,
    ))
    adult = world.add(Entity(
        id=adult_label,
        kind="character",
        type=adult_type,
        label=adult_label,
    ))
    spook = world.add(Entity(
        id=ghost.id,
        kind="ghost",
        type="ghost",
        label=ghost.label,
        phrase=ghost.phrase,
        friendly=True,
    ))

    world.facts.update(
        child=child,
        adult=adult,
        ghost=ghost,
        problem=problem,
        setting=setting,
    )

    _introduce(world, child, adult, problem, ghost)
    _foreshadow(world, child, problem)
    _search(world, child, adult, problem, ghost)
    _reveal(world, child, spook, problem)
    _solve(world, child, adult, problem, ghost)
    return world


SETTING = Setting(place="the old house on Briar Lane")

PROBLEMS = {
    "music_box_key": Problem(
        id="music_box_key",
        missing="music box key",
        place="attic board",
        sound_hint="clink",
        foreshadow="tiny clink",
        solution_sound="click",
        solution_action="open the music box",
        tags={"sound", "foreshadow", "problem_solving", "ghost"},
    ),
    "lantern_match": Problem(
        id="lantern_match",
        missing="lantern match",
        place="coat pocket",
        sound_hint="rustle",
        foreshadow="small rustle",
        solution_sound="snap",
        solution_action="light the lantern",
        tags={"sound", "foreshadow", "problem_solving", "ghost"},
    ),
}

GHOSTS = {
    "pip": Ghost(
        id="Pip",
        label="Pip",
        phrase="a shy little ghost",
        sound="whooo",
        help_method="nudging clues into place",
        hint_method="softly pointing with a glow",
        tags={"ghost", "sound"},
    ),
    "murmur": Ghost(
        id="Murmur",
        label="Murmur",
        phrase="a friendly attic ghost",
        sound="hushhh",
        help_method="leaving gentle hints",
        hint_method="floating near the clue",
        tags={"ghost", "sound"},
    ),
}

CHILDREN = ["Maya", "Nina", "Lena", "Iris", "Oona", "Tara"]
ADULTS = ["Grandma", "Aunt June", "Papa", "Mom"]
CHILD_TYPES = {"Maya": "girl", "Nina": "girl", "Lena": "girl", "Iris": "girl", "Oona": "girl", "Tara": "girl"}


@dataclass
class StoryParams:
    problem: str
    ghost: str
    name: str
    adult: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    return [(p, g) for p in PROBLEMS for g in GHOSTS]


def reasonableness_gate(params: StoryParams) -> None:
    if params.problem not in PROBLEMS:
        raise StoryError("Unknown problem choice.")
    if params.ghost not in GHOSTS:
        raise StoryError("Unknown ghost choice.")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short ghost story for a small child that uses the word "twelfth" and includes gentle sound effects.',
        f"Tell a story where {f['child'].id} hears a spooky sound in {f['setting'].place} and solves a small mystery with help from {f['ghost'].label}.",
        f"Write a child-friendly ghost story with clues like a draft, a tiny sound, and a kind surprise ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    adult = world.facts["adult"]
    ghost = world.facts["ghost"]
    problem = world.facts["problem"]
    return [
        QAItem(
            question=f"What did {child.id} hear on the twelfth chime?",
            answer=f"{child.id} heard {ghost.sound} drift down the hallway, which sounded spooky at first but turned out to be a clue.",
        ),
        QAItem(
            question=f"What was missing in the old house?",
            answer=f"The missing thing was the {problem.missing}. That was the little mystery {child.id} and {adult.label} needed to solve.",
        ),
        QAItem(
            question=f"How did {child.id} figure out where to look?",
            answer=f"{child.id} paid attention to the chilly draft, the tiny sound, and the dusty footprint, and those clues pointed to the attic.",
        ),
        QAItem(
            question=f"Who was making the spooky sound?",
            answer=f"It was {ghost.id}, a friendly ghost who was trying to help instead of scare anyone.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, the {problem.missing} was found, the music box opened, and the house felt friendly instead of spooky.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clue?",
            answer="A clue is a small piece of information that helps you solve a mystery.",
        ),
        QAItem(
            question="Why do sound effects matter in a story?",
            answer="Sound effects help you imagine what is happening, like a creak, a click, or a soft whooo in the dark.",
        ),
        QAItem(
            question="What does foreshadowing do?",
            answer="Foreshadowing gives early hints about something important that will matter later in the story.",
        ),
        QAItem(
            question="Can a ghost be friendly in a story?",
            answer="Yes. In a story, a ghost can be spooky-looking but still be kind and helpful.",
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        bits.append(f"kind={e.kind}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
problem_valid(P) :- problem(P).
ghost_valid(G) :- ghost(G).
valid_story(P, G) :- problem_valid(P), ghost_valid(G).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for gid in GHOSTS:
        lines.append(asp.fact("ghost", gid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a gentle ghost story with twelfth-chime sound effects and a solved mystery."
    )
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--ghost", choices=GHOSTS)
    ap.add_argument("--name", choices=CHILDREN)
    ap.add_argument("--adult", choices=ADULTS)
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
    if args.problem and args.ghost:
        reasonableness_gate(StoryParams(problem=args.problem, ghost=args.ghost, name="Maya", adult="Grandma"))
    combos = valid_combos()
    filtered = [c for c in combos
                if (args.problem is None or c[0] == args.problem)
                and (args.ghost is None or c[1] == args.ghost)]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    problem, ghost = rng.choice(sorted(filtered))
    name = args.name or rng.choice(CHILDREN)
    adult = args.adult or rng.choice(ADULTS)
    return StoryParams(problem=problem, ghost=ghost, name=name, adult=adult)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTING,
        PROBLEMS[params.problem],
        GHOSTS[params.ghost],
        child_name=params.name,
        child_type=CHILD_TYPES.get(params.name, "girl"),
        adult_label=params.adult,
        adult_type={"Grandma": "grandmother", "Aunt June": "aunt", "Papa": "father", "Mom": "mother"}.get(params.adult, "grandmother"),
    )
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
    StoryParams(problem="music_box_key", ghost="pip", name="Maya", adult="Grandma"),
    StoryParams(problem="lantern_match", ghost="murmur", name="Iris", adult="Aunt June"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} compatible story combos:\n")
        for combo in combos:
            print("  ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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
            header = f"### {p.name}: {p.problem} with {p.ghost}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
