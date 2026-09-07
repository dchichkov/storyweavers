#!/usr/bin/env python3
"""A bedtime story about a nose, a shared secret, and a gentle clue."""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

_here = Path(__file__).resolve()
for parent in [_here.parent, *_here.parents]:
    if (parent / "results.py").exists():
        sys.path.insert(0, str(parent))
        break
from pathlib import Path as _StoryPath
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
sys.path.insert(0, str(_storyworlds_root))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None


@dataclass
class Event:
    kind: str
    actor: str
    target: str
    text: str
    cause: str
    result: str


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.history: list[Event] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def record(self, kind: str, actor: str, target: str, text: str,
               cause: str, result: str) -> None:
        self.history.append(Event(kind, actor, target, text, cause, result))
        self.say(text)

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass(frozen=True)
class PathSpec:
    problem: str
    solution: str
    clue: str
    actions: tuple[str, ...]
    change: str
    ending: str


PATHS = {
    "sleepy_nose": {
        "share": PathSpec(
            "a tickly nose kept the child awake",
            "share the bedtime story with a stuffed rabbit",
            "the rabbit's long ears had heard every quiet story before",
            ("notice_tickle", "share_story", "settle"),
            "the child felt less alone and the tickle faded",
            "two friends slept beneath the moon-shaped quilt",
        ),
        "breathe": PathSpec(
            "a tickly nose kept the child awake",
            "breathe slowly with a parent",
            "the warm lamp made a calm circle beside the bed",
            ("notice_tickle", "slow_breaths", "settle"),
            "the child learned that slow breaths could make room for sleep",
            "the child's nose rested quietly above a soft blanket",
        ),
    },
    "missing_moon": {
        "share": PathSpec(
            "the child's moon night-light was missing",
            "ask a sibling to share their little lamp",
            "the pillow still held a pale crescent-shaped mark",
            ("notice_missing", "share_lamp", "settle"),
            "the children made one gentle pool of light together",
            "the shared lamp glowed between their beds",
        ),
        "search": PathSpec(
            "the child's moon night-light was missing",
            "search calmly with a parent",
            "the charging cord curled beside the bedtime books",
            ("notice_missing", "search_lamp", "settle"),
            "the child found the lamp without turning the room upside down",
            "the moon lamp shone from its familiar shelf",
        ),
    },
    "unfinished_song": {
        "share": PathSpec(
            "the child could not remember the last line of a lullaby",
            "share the first lines with a grandparent",
            "the old music box played three soft notes",
            ("notice_song", "share_song", "settle"),
            "the missing line returned when the song became a shared song",
            "the lullaby floated gently into the dark",
        ),
        "hum": PathSpec(
            "the child could not remember the last line of a lullaby",
            "hum the tune and let the ending arrive",
            "the music box paused exactly where the lost line belonged",
            ("notice_song", "hum_song", "settle"),
            "the child found a new quiet ending",
            "the last hum curled up like a sleepy bird",
        ),
    },
    "worrying_shadow": {
        "share": PathSpec(
            "a coat-shaped shadow looked frightening on the wall",
            "share the worry with a sibling",
            "the shadow moved whenever the night breeze moved the coat",
            ("notice_shadow", "share_worry", "settle"),
            "the shadow became an ordinary coat again",
            "the coat hung harmlessly while the children dreamed",
        ),
        "lamp": PathSpec(
            "a coat-shaped shadow looked frightening on the wall",
            "turn on the small bedside lamp",
            "the coat's wooden button made the shadow's round spot",
            ("notice_shadow", "turn_lamp", "settle"),
            "the child understood what the shadow was made of",
            "the button shone while the wall grew still",
        ),
    },
}

PLACES = {
    "bedroom": "the quiet bedroom",
    "attic_room": "the little attic room",
    "guest_room": "the warm guest room",
}
NAMES = ("Lila", "Mara", "Nina", "Owen", "Theo", "Sam")
SIBLINGS = ("Milo", "Ivy", "Jonah", "Rose")
PARENTS = ("mother", "father", "grandmother")
PROBLEMS = tuple(PATHS)
SOLUTIONS = ("share", "breathe", "search", "hum", "lamp")
NIGHT_DETAILS = (
    "Rain whispered against the window.",
    "The hallway clock made a soft, round tick.",
    "A silver moon rested on the curtains.",
    "The house had settled into its nighttime hush.",
)


@dataclass
class StoryParams:
    place: str
    problem: str
    solution: str
    name: str
    helper: str
    parent: str
    night_detail: str
    seed: Optional[int] = None


def valid_paths() -> list[tuple[str, str]]:
    return sorted((problem, solution)
                  for problem, choices in PATHS.items()
                  for solution in choices)


def validate(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError("That bedtime place is not supported.")
    if params.problem not in PATHS:
        raise StoryError("That nighttime problem is not supported.")
    if params.solution not in PATHS[params.problem]:
        raise StoryError("That solution does not fit this bedtime problem.")
    if params.name == params.helper:
        raise StoryError("The child and helper must have different names.")
    if not params.name or not params.helper:
        raise StoryError("Both the child and helper need names.")


def make_world(params: StoryParams) -> World:
    validate(params)
    spec = PATHS[params.problem][params.solution]
    world = World()
    child = world.add(Entity(
        params.name, "character", params.name,
        memes={"curiosity": 1.0, "tiredness": 1.0},
    ))
    helper = world.add(Entity(
        params.helper, "character", params.helper,
        memes={"kindness": 1.0},
    ))
    parent = world.add(Entity(params.parent, "character", params.parent))
    nose = world.add(Entity(
        "nose", "body", "small nose", owner=child.id,
        meters={"awake": 0.0, "tickle": 0.0},
    ))
    bed = world.add(Entity("bed", "place", "bed"))
    if params.problem == "missing_moon":
        world.add(Entity("lamp", "object", "moon night-light", owner=child.id))
    elif params.problem == "unfinished_song":
        world.add(Entity("song", "song", "lullaby", owner=child.id))
    elif params.problem == "worrying_shadow":
        world.add(Entity("shadow", "physical_effect", "coat-shaped shadow"))
    world.facts.update(
        child=child, helper=helper, parent=parent, nose=nose, bed=bed,
        spec=spec, params=params, resolved=False, shared=False,
    )

    child_word = "her" if params.name in {"Lila", "Mara", "Nina", "Rose", "Ivy"} else "his"
    world.record(
        "arrival", child.id, bed.id,
        f"{params.name} climbed into bed in {PLACES[params.place]}. "
        f"{params.night_detail} {child_word.capitalize()} small nose peeked above the blanket, "
        f"and the room seemed ready to keep a secret.",
        "bedtime had arrived",
        "the child was tucked in and listening to the night",
    )
    world.para()

    if params.problem == "sleepy_nose":
        notice = (
            f"{params.name}'s nose began to tickle just as "
            f"{params.parent} kissed the blanket good night."
        )
        nose.meters["tickle"] = 1.0
        nose.meters["awake"] = 1.0
        world.record(
            "notice_tickle", child.id, nose.id,
            f'{notice} "{params.name}, are you ready to sleep?" '
            f"{params.parent.capitalize()} asked. "
            f'"My nose says not yet," {params.name} whispered.',
            "the nose tickled when the room grew quiet",
            "the child told someone what was keeping sleep away",
        )
    elif params.problem == "missing_moon":
        world.record(
            "notice_missing", child.id, "lamp",
            f'{params.name} reached for the moon night-light, but the little lamp '
            f'was gone. "The moon disappeared," {params.name} said. '
            f'"Let us look gently," {params.parent} replied.',
            "the familiar lamp was not on its shelf",
            "the child asked for help instead of rushing",
        )
    elif params.problem == "unfinished_song":
        world.record(
            "notice_song", child.id, "song",
            f'{params.name} sang, "Sleep now, little star," and then forgot the next line. '
            f'"The song lost its way," {params.name} said. '
            f'"Songs can find their way home," {params.parent} answered.',
            "the familiar lullaby stopped before its ending",
            "the child shared the worry about forgetting",
        )
    else:
        world.record(
            "notice_shadow", child.id, "shadow",
            f"A coat-shaped shadow stretched across the wall. "
            f'"There is something tall beside me," {params.name} said. '
            f'"I hear you," {params.parent} replied, staying close.',
            "the moving coat made a strange shape in the dark",
            "the child spoke instead of hiding the worry",
        )

    world.para()
    execute_solution(world, params)
    finish(world)
    return world


def execute_solution(world: World, params: StoryParams) -> None:
    spec: PathSpec = world.facts["spec"]
    child: Entity = world.facts["child"]
    helper: Entity = world.facts["helper"]
    parent: Entity = world.facts["parent"]
    nose: Entity = world.facts["nose"]

    if params.solution == "share":
        world.facts["shared"] = True
        child.memes["bravery"] = child.memes.get("bravery", 0) + 1
        helper.memes["kindness"] += 1
        if params.problem == "sleepy_nose":
            text = (
                f'"Will you hear one story with me?" {params.name} asked. '
                f'"I will," {params.helper} said, climbing onto the rug. '
                f"{params.name} shared the story of a fox who tucked a tiny star "
                f"under its nose. Before the story ended, the tickle had softened."
            )
        elif params.problem == "missing_moon":
            text = (
                f'"You can share my lamp," {params.helper} offered. '
                f'"Then the moon can shine for both of us," {params.name} said. '
                f"{params.helper} carried the lamp between their beds."
            )
        elif params.problem == "unfinished_song":
            text = (
                f'"I remember the beginning," {params.name} said. '
                f'"I remember the middle," {params.helper} replied. '
                f"They sang their pieces together, and the forgotten line came back."
            )
        else:
            text = (
                f'"That shadow worries me," {params.name} said. '
                f'"We can look at it together," {params.helper} answered. '
                f"They watched the coat sway and noticed its wooden button."
            )
        world.record("share", child.id, helper.id, text, spec.clue, spec.change)
    elif params.solution == "breathe":
        nose.meters["tickle"] = 0.0
        nose.meters["awake"] = 0.0
        child.memes["calm"] = 1.0
        text = (
            f'"Put one hand near your nose," {params.parent} said. '
            f'"In slowly, and out slowly." {params.name} breathed with '
            f"{params.parent}, counting three quiet breaths. "
            f"The warm lamp made a calm circle beside the bed."
        )
        world.record("slow_breaths", child.id, parent.id, text, spec.clue, spec.change)
    elif params.solution == "search":
        world.add(Entity("cord", "object", "charging cord"))
        world.facts["found"] = True
        text = (
            f'"Let us follow the cord," {params.parent} said. '
            f'"There it is, beside the bedtime books!" {params.name} cried. '
            f"They found the moon lamp tucked behind a pillow."
        )
        world.record("search_lamp", child.id, parent.id, text, spec.clue, spec.change)
    elif params.solution == "hum":
        child.memes["creativity"] = 1.0
        text = (
            f'"I do not know the last line," {params.name} said. '
            f'"You may make a little one," {params.parent} replied. '
            f"{params.name} hummed a new ending, soft as a sleepy bird."
        )
        world.record("hum_song", child.id, parent.id, text, spec.clue, spec.change)
    elif params.solution == "lamp":
        world.add(Entity("button", "object", "wooden button"))
        world.facts["found"] = True
        text = (
            f'"May I turn on the lamp?" {params.name} asked. '
            f'"Yes, and then we can see," {params.parent} said. '
            f"The light showed the coat, its sleeve, and the round button making the shadow."
        )
        world.record("turn_lamp", child.id, parent.id, text, spec.clue, spec.change)
    else:
        raise StoryError("No action is defined for that solution.")


def finish(world: World) -> None:
    params: StoryParams = world.facts["params"]
    spec: PathSpec = world.facts["spec"]
    child: Entity = world.facts["child"]
    nose: Entity = world.facts["nose"]
    child.memes["tiredness"] = 0.0
    nose.meters["awake"] = 0.0
    nose.meters["tickle"] = 0.0
    world.facts["resolved"] = True
    world.record(
        "settle", child.id, "bed",
        f"{spec.ending.capitalize()}. {params.parent.capitalize()} tucked "
        f"{params.name} in, and {params.name} smiled. "
        f'"Good night," {params.name} whispered. "Good night," came the answer.',
        spec.change,
        "the child rested safely after sharing or solving the worry",
    )


def prompts(world: World) -> list[str]:
    p: StoryParams = world.facts["params"]
    spec: PathSpec = world.facts["spec"]
    return [
        f"Write a bedtime story about {p.name}'s nose and a nighttime worry that "
        f"is solved by choosing to {spec.solution}.",
        f"Tell a gentle story set in {PLACES[p.place]} where {p.name} shares a "
        f"feeling with {p.helper} or {p.parent}, notices an early clue, and settles to sleep.",
    ]


def story_qa(world: World) -> list[QAItem]:
    questions = {
        "arrival": "How did the bedtime scene begin?",
        "notice_tickle": "Why did the child stay awake?",
        "notice_missing": "What was missing?",
        "notice_song": "What happened to the lullaby?",
        "notice_shadow": "Why did the shadow seem frightening?",
        "share": "How did sharing help?",
        "slow_breaths": "What did the child do with the parent?",
        "search_lamp": "How did the child find the lamp?",
        "hum_song": "How did the child finish the song?",
        "turn_lamp": "What did the lamp reveal?",
        "settle": "How did the story end?",
    }
    return [
        QAItem(question=questions[event.kind],
               answer=f"{event.cause.capitalize()} {event.result}.")
        for event in world.history if event.kind in questions
    ]


KNOWLEDGE = {
    "sleepy_nose": QAItem(
        "Why can a nose tickle?",
        "A nose can tickle when dust, dry air, or a tiny irritation bothers the inside of it."
    ),
    "missing_moon": QAItem(
        "What does a night-light do?",
        "A night-light makes a small, gentle glow that helps a room feel less dark."
    ),
    "unfinished_song": QAItem(
        "Why can singing help at bedtime?",
        "A quiet song can make bedtime feel steady and peaceful while the body gets ready to rest."
    ),
    "worrying_shadow": QAItem(
        "What makes a shadow?",
        "A shadow appears when an object blocks light, so its shape falls across a wall or floor."
    ),
}


def world_qa(world: World) -> list[QAItem]:
    return [KNOWLEDGE[world.facts["params"].problem],
            QAItem("Why is sharing a worry helpful?",
                   "Sharing a worry lets another person understand it and offer comfort or help.")]


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("\n== Story questions ==")
    for item in sample.story_qa:
        lines += [f"Q: {item.question}", f"A: {item.answer}"]
    lines.append("\n== World knowledge ==")
    for item in sample.world_qa:
        lines += [f"Q: {item.question}", f"A: {item.answer}"]
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(f"  {entity.id}: meters={meters} memes={memes}")
    lines.append("--- events ---")
    for event in world.history:
        lines.append(f"  {event.kind}: {event.text}")
    return "\n".join(lines)


ASP_RULES = r"""
at_risk(sleepy_nose, nose).
at_risk(missing_moon, lamp).
at_risk(unfinished_song, song).
at_risk(worrying_shadow, shadow).
compatible(P, S) :- path(P, S).
resolved(P, S) :- compatible(P, S).
"""


def asp_facts() -> str:
    import importlib
    asp = importlib.import_module("asp")
    return "\n".join(
        asp.fact("path", problem, solution)
        for problem, solution in valid_paths()
    )


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n#show resolved/2.\n"


def verify() -> int:
    expected = set(valid_paths())
    for problem, solution in sorted(expected):
        params = StoryParams(
            place="bedroom",
            problem=problem,
            solution=solution,
            name="Lila",
            helper="Milo",
            parent="mother",
            night_detail=NIGHT_DETAILS[0],
        )
        sample = generate(params)
        world = sample.world
        assert world is not None and world.facts["resolved"]
        assert len(sample.story_qa) >= 3
        assert all(q.answer.endswith(".") for q in sample.story_qa)
        assert all(event.actor in world.entities for event in world.history)
        assert all(event.target in world.entities for event in world.history)
        assert "{" not in sample.story and "}" not in sample.story
        assert params.name in sample.story
        assert (params.helper if solution == "share" else params.parent) in sample.story
        assert "Good night" in sample.story
    try:
        import importlib
        asp = importlib.import_module("asp")
        model = asp.one_model(asp_program())
        actual = set(asp.atoms(model, "resolved"))
        if actual != expected:
            print("MISMATCH: ASP and Python paths differ.")
            return 1
    except ImportError:
        pass
    print(f"OK: {len(expected)} executable bedtime paths verified.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--place", choices=sorted(PLACES))
    parser.add_argument("--problem", choices=sorted(PROBLEMS))
    parser.add_argument("--solution", choices=sorted(SOLUTIONS))
    parser.add_argument("--name")
    parser.add_argument("--helper")
    parser.add_argument("--parent", choices=PARENTS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    candidates = [
        (problem, solution)
        for problem, solution in valid_paths()
        if args.problem is None or problem == args.problem
        if args.solution is None or solution == args.solution
    ]
    if not candidates:
        raise StoryError("The requested problem and solution are incompatible.")
    problem, solution = rng.choice(candidates)
    name = args.name or rng.choice(NAMES)
    helper_choices = [x for x in SIBLINGS if x != name]
    helper = args.helper or rng.choice(helper_choices)
    return StoryParams(
        place=args.place or rng.choice(tuple(PLACES)),
        problem=problem,
        solution=solution,
        name=name,
        helper=helper,
        parent=args.parent or rng.choice(PARENTS),
        night_detail=rng.choice(NIGHT_DETAILS),
    )


CURATED = [
    StoryParams("bedroom", "sleepy_nose", "share", "Lila", "Milo", "mother", NIGHT_DETAILS[0]),
    StoryParams("attic_room", "sleepy_nose", "breathe", "Theo", "Ivy", "father", NIGHT_DETAILS[1]),
    StoryParams("guest_room", "missing_moon", "share", "Nina", "Rose", "grandmother", NIGHT_DETAILS[2]),
    StoryParams("bedroom", "missing_moon", "search", "Owen", "Milo", "mother", NIGHT_DETAILS[3]),
    StoryParams("attic_room", "unfinished_song", "share", "Mara", "Jonah", "grandmother", NIGHT_DETAILS[2]),
    StoryParams("guest_room", "unfinished_song", "hum", "Sam", "Ivy", "father", NIGHT_DETAILS[0]),
    StoryParams("bedroom", "worrying_shadow", "share", "Lila", "Rose", "mother", NIGHT_DETAILS[1]),
    StoryParams("attic_room", "worrying_shadow", "lamp", "Theo", "Milo", "father", NIGHT_DETAILS[3]),
]


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.n < 1:
        raise SystemExit("-n must be at least 1")
    if args.verify:
        raise SystemExit(verify())
    if args.show_asp:
        print(f"{asp_facts()}\n{ASP_RULES}")
        return
    if args.asp:
        print("Compatible bedtime paths:")
        for problem, solution in valid_paths():
            print(f"  {problem}: {solution}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        payload = [sample.to_dict() for sample in samples]
        print(json.dumps(payload[0] if len(payload) == 1 else payload,
                         indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.problem} / {p.solution}"
        elif len(samples) > 1:
            header = f"### bedtime story {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i + 1 < len(samples):
            print("\n" + "=" * 68 + "\n")


if __name__ == "__main__":
    main()
