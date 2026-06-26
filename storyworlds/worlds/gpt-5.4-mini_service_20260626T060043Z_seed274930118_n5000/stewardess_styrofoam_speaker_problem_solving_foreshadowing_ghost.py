#!/usr/bin/env python3
"""
A standalone storyworld for a tiny ghost-story domain with problem solving and
foreshadowing.

Premise:
- A stewardess on a late-night flight hears a strange speaker crackling in the
  cabin.
- A harmless styrofoam object becomes an eerie clue.
- The stewardess uses observation, calm, and a small problem-solving turn to
  uncover a friendly ghostly cause and quiet the cabin.

The world is deliberately small and constraint-checked:
- The speaker can buzz, whisper, or crackle.
- The styrofoam clue can drift, cling, or reveal a hidden shape.
- The stewardess can investigate, ask for help, and solve the problem.

The story stays child-facing, concrete, and spooky-but-gentle.
"""

from __future__ import annotations

import argparse
import dataclasses
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"stewardess", "woman", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"man", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the airplane cabin"
    affords: set[str] = field(default_factory=set)


@dataclass
class Clue:
    label: str
    phrase: str
    kind: str
    surface: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    symptom: str
    cause: str
    rumor: str
    fix: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: set[str]
    requires: set[str]
    used_for: str
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTING = Setting(
    place="the airplane cabin",
    affords={"investigate", "listen", "solve"},
)

PROBLEMS = {
    "speaker_ghost": Problem(
        id="speaker_ghost",
        symptom="a crackling whisper from the speaker",
        cause="a tiny ghost was trapped behind the speaker grille",
        rumor="something invisible was trying to get attention",
        fix="open the panel, speak kindly, and free the little ghost",
        keyword="speaker",
        tags={"ghost", "speaker", "whisper"},
    ),
    "styrofoam_tap": Problem(
        id="styrofoam_tap",
        symptom="a tapping sound against the seat pocket",
        cause="a loose styrofoam cup was knocking in the air vent",
        rumor="the cabin was haunted by a tapping spirit",
        fix="remove the cup and tuck it safely away",
        keyword="styrofoam",
        tags={"styrofoam", "tap"},
    ),
}

TOOLS = {
    "flashlight": Tool(
        id="flashlight",
        label="a small flashlight",
        phrase="a small flashlight",
        helps={"investigate", "solve"},
        requires={"dark"},
        used_for="shine into the shadows",
        tags={"light", "dark"},
    ),
    "blanket": Tool(
        id="blanket",
        label="a warm blanket",
        phrase="a warm blanket",
        helps={"comfort"},
        requires=set(),
        used_for="make things feel calmer",
        tags={"calm"},
    ),
}

CLUES = {
    "styrofoam": Clue(
        label="styrofoam",
        phrase="a white styrofoam cup",
        kind="styrofoam",
        surface="the seat pocket",
        tags={"styrofoam", "light", "float"},
    ),
    "speaker": Clue(
        label="speaker",
        phrase="the overhead speaker grille",
        kind="speaker",
        surface="the front panel",
        tags={"speaker", "voice", "sound"},
    ),
}

GHOST_NAMES = ["Mina", "June", "Iris", "Luna", "Poppy", "Nia"]
STAFF_NAMES = ["Ava", "Maya", "Tess", "Eve"]
MOODS = ["calm", "curious", "steady", "brave", "gentle"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    clue: str
    problem: str
    name: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def clue_is_relevant(problem: Problem, clue: Clue) -> bool:
    return clue.kind in problem.tags or clue.kind in problem.keyword


def fix_is_plausible(problem: Problem) -> bool:
    return problem.id in PROBLEMS


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for pid, p in PROBLEMS.items():
        for cid, c in CLUES.items():
            if clue_is_relevant(p, c) and fix_is_plausible(p):
                out.append((pid, cid))
    return out


def explain_rejection(problem: Problem, clue: Clue) -> str:
    return (
        f"(No story: {clue.label} does not plausibly point to {problem.id}. "
        f"Choose the matching clue for the haunting.)"
    )


# ---------------------------------------------------------------------------
# Simulation helpers
# ---------------------------------------------------------------------------

def _speaker_noise(world: World) -> bool:
    return world.facts.get("speaker_noise", False)


def _clue_visible(world: World) -> bool:
    return world.facts.get("clue_visible", False)


def setup_world(params: StoryParams) -> World:
    world = World(SETTING)
    stewardess = world.add(Entity(
        id=params.name,
        kind="character",
        type="stewardess",
        label="the stewardess",
        meters={"courage": 1.0},
        memes={"curiosity": 1.0, "calm": 1.0, "unease": 0.0},
    ))
    world.add(Entity(
        id="passenger",
        kind="character",
        type="girl",
        label="a little passenger",
        meters={"sleepiness": 1.0},
        memes={"fear": 0.0},
    ))
    world.add(Entity(
        id="speaker",
        type="speaker",
        label="the speaker",
        phrase="the overhead speaker",
    ))
    world.add(Entity(
        id="clue",
        type=CLUES[params.clue].kind,
        label=CLUES[params.clue].label,
        phrase=CLUES[params.clue].phrase,
    ))
    world.add(Entity(
        id="tool",
        type="tool",
        label=TOOLS["flashlight"].label,
        phrase=TOOLS["flashlight"].phrase,
    ))
    world.facts["stewardess"] = stewardess
    world.facts["problem"] = PROBLEMS[params.problem]
    world.facts["clue"] = CLUES[params.clue]
    world.facts["tool"] = TOOLS["flashlight"]
    return world


def introduce(world: World) -> None:
    s = world.facts["stewardess"]
    trait = s.memes.get("calm", 0.0)
    world.say(
        f"{s.id} was a {random.choice(MOODS)} stewardess who knew how to stay quiet when a room felt strange."
    )
    world.say(
        f"On a late flight, {s.pronoun()} noticed that even a tiny sound could make a cabin feel bigger than it was."
    )


def foreshadow(world: World) -> None:
    p = world.facts["problem"]
    clue = world.facts["clue"]
    s = world.facts["stewardess"]
    if clue.kind == "speaker":
        world.facts["speaker_noise"] = True
        world.say(
            f"At first, there was only a soft crackle from the speaker, like someone whispering from far away."
        )
        world.say(
            f"{s.id} glanced up, because that kind of noise could mean there was a hidden reason waiting to be found."
        )
    else:
        world.facts["clue_visible"] = True
        world.say(
            f"Then {s.id} saw {clue.phrase} tucked where it should not have been."
        )
        world.say(
            f"It looked harmless, but it was the sort of small thing that sometimes points to a bigger mystery."
        )
    world.facts["foreshadow"] = p.rumor


def problem_rises(world: World) -> None:
    p = world.facts["problem"]
    s = world.facts["stewardess"]
    world.say(
        f"Before long, the strange sign made the whole cabin feel uneasy, and even the sleeping passengers stirred."
    )
    world.say(
        f"{s.id} did not panic. {s.pronoun().capitalize()} listened, looked, and decided to solve the mystery instead."
    )
    world.facts["unease"] = True


def solve_problem(world: World) -> None:
    p = world.facts["problem"]
    clue = world.facts["clue"]
    s = world.facts["stewardess"]
    if clue.kind == "speaker":
        world.say(
            f"{s.id} moved carefully to the front panel, opened it a little, and found a tiny ghost caught behind the speaker grille."
        )
        world.say(
            f'The little ghost was not scary at all; it only wanted to say, "I am here."'
        )
        world.say(
            f"{s.id} smiled, spoke softly, and helped the ghost slip free."
        )
        world.say(
            f"At once, the crackling stopped, and the cabin felt warm and ordinary again."
        )
    else:
        world.say(
            f"{s.id} picked up the {clue.label}, carried it to the trash, and checked the vent behind the seat pocket."
        )
        world.say(
            f"The tapping stopped right away, and the cabin's hush returned like a blanket being folded smooth."
        )
    world.facts["resolved"] = True
    world.facts["ending_image"] = "quiet cabin"


def end_image(world: World) -> None:
    s = world.facts["stewardess"]
    if world.facts.get("problem").id == "speaker_ghost":
        world.say(
            f"In the end, {s.id} stood under the silent speaker while the little ghost floated away like a speck of moonlight."
        )
    else:
        world.say(
            f"In the end, {s.id} tucked the styrofoam clue away, and the airplane felt peaceful and small again."
        )


def tell(params: StoryParams) -> World:
    world = setup_world(params)
    introduce(world)
    world.para()
    foreshadow(world)
    problem_rises(world)
    world.para()
    solve_problem(world)
    end_image(world)
    return world


# ---------------------------------------------------------------------------
# QA and prompts
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    p = world.facts["problem"]
    clue = world.facts["clue"]
    return [
        f'Write a short ghost story for young children that includes a stewardess, a {clue.label}, and a speaker.',
        f"Tell a gentle spooky story where a stewardess notices {p.symptom} and solves it kindly.",
        f"Write a problem-solving story with foreshadowing that begins with {clue.phrase} and ends calmly.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["problem"]
    clue = world.facts["clue"]
    s = world.facts["stewardess"]
    qa = [
        QAItem(
            question=f"Who noticed the strange thing in the airplane cabin?",
            answer=f"{s.id} the stewardess noticed it first, because she was paying attention to the little signs in the cabin.",
        ),
        QAItem(
            question=f"What early clue hinted that something was wrong?",
            answer=f"The story first showed {clue.phrase}, which foreshadowed a bigger mystery in the cabin.",
        ),
        QAItem(
            question=f"What problem did the stewardess solve?",
            answer=f"She solved the mystery of {p.symptom} and found the true cause behind it.",
        ),
    ]
    if world.facts.get("resolved"):
        qa.append(
            QAItem(
                question="How did the story end?",
                answer="The stewardess fixed the problem kindly, and the cabin became quiet and peaceful again.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a stewardess?",
            answer="A stewardess is a person who helps people on an airplane and keeps the flight calm and safe.",
        ),
        QAItem(
            question="What is styrofoam?",
            answer="Styrofoam is a very light material that can be used for cups and packing, and it can float or tap around easily.",
        ),
        QAItem(
            question="What is a speaker?",
            answer="A speaker is a device that plays sound so people can hear announcements or music.",
        ),
        QAItem(
            question="What does foreshadowing do in a story?",
            answer="Foreshadowing gives an early clue that something important will happen later.",
        ),
        QAItem(
            question="What is problem solving in a story?",
            answer="Problem solving is when a character thinks carefully and finds a way to fix a trouble.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A clue is relevant when it matches the problem's theme.
relevant(P, C) :- problem(P), clue(C), problem_tag(P, T), clue_tag(C, T).

% A problem has a valid fix when its fix rule is available.
has_fix(P) :- problem(P), fixable(P).

% A story is valid when the selected clue is relevant and the problem can be solved.
valid_story(P, C) :- relevant(P, C), has_fix(P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("fixable", pid))
        lines.append(asp.fact("problem_symptom", pid, p.symptom))
        for t in sorted(p.tags):
            lines.append(asp.fact("problem_tag", pid, t))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        for t in sorted(c.tags):
            lines.append(asp.fact("clue_tag", cid, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in clingo:", sorted(clingo_set - python_set))
    print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Params / generation
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    problem: str
    clue: str
    name: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small ghost-story world with problem solving and foreshadowing.")
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=MOODS)
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
    combos = valid_combos()
    if args.problem and args.clue:
        if (args.problem, args.clue) not in combos:
            raise StoryError(explain_rejection(PROBLEMS[args.problem], CLUES[args.clue]))
    filtered = [
        c for c in combos
        if (args.problem is None or c[0] == args.problem)
        and (args.clue is None or c[1] == args.clue)
    ]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    problem, clue = rng.choice(sorted(filtered))
    name = args.name or rng.choice(GHOST_NAMES + STAFF_NAMES)
    trait = args.trait or rng.choice(MOODS)
    return StoryParams(problem=problem, clue=clue, name=name, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  facts: {sorted(world.facts.keys())}")
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
    StoryParams(problem="speaker_ghost", clue="speaker", name="Mina", trait="calm"),
    StoryParams(problem="styrofoam_tap", clue="styrofoam", name="Tess", trait="curious"),
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
        models = asp_valid_combos()
        print(f"{len(models)} compatible problem/clue combos:")
        for p, c in models:
            print(f"  {p:16} {c}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
