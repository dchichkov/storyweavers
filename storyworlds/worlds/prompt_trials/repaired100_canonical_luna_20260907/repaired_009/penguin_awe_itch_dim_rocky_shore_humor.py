#!/usr/bin/env python3
"""
A small detective storyworld on a rocky shore, where a penguin's dim itch
reveals a funny mystery and a kind solution.
"""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    label: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class Case:
    id: str
    clue: str
    suspicion: str
    reveal: str
    action: str
    ending: str
    answer: str


@dataclass(frozen=True)
class StoryParams:
    place: str
    penguin: str
    detective: str
    case: str
    opening: int = 0
    turn: int = 0
    ending: int = 0
    seed: Optional[int] = None


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = {
    "rocky_shore": "the rocky shore",
}

PENGUINS = ["Pip", "Pebble", "Waddle", "Moss", "Tuck", "Biscuit"]
DETECTIVES = ["Detective Mira", "Inspector Finn", "Detective Jo", "Agent Coral"]

CASES = {
    "dim_shell": Case(
        id="dim_shell",
        clue="a little blue shell had stopped shining beside the tide pool",
        suspicion="someone had stolen its sparkle",
        reveal="the shell was covered by a tiny patch of seaweed",
        action="lifted the seaweed and rinsed the shell with clear seawater",
        ending="the shell blinked in the sun, and the penguin gasped with awe",
        answer="The dim shell was hidden under a patch of seaweed.",
    ),
    "missing_feather": Case(
        id="missing_feather",
        clue="one bright feather had vanished from the penguin's lucky hat",
        suspicion="a sneaky gull had carried it away",
        reveal="the feather was tucked under a warm rock",
        action="rolled the rock aside and rescued the feather",
        ending="the penguin wore the hat backward and called it a detective disguise",
        answer="The missing feather was under a warm rock.",
    ),
    "mysterious_tracks": Case(
        id="mysterious_tracks",
        clue="strange wiggly tracks crossed the wet sand",
        suspicion="a sea monster had visited during breakfast",
        reveal="the tracks came from a sleepy octopus dragging a scarf",
        action="followed the trail and returned the scarf to the octopus",
        ending="the octopus bowed, while the penguin laughed so hard that he sneezed",
        answer="The tracks belonged to an octopus dragging a scarf.",
    ),
    "itchy_pebble": Case(
        id="itchy_pebble",
        clue="the penguin's flipper had an itch that would not quit",
        suspicion="a detective-sized mystery had crawled into his feathers",
        reveal="a round pebble was stuck in the fold of his scarf",
        action="removed the pebble and gave the scarf a careful shake",
        ending="the penguin's itch-dim faded, and he bowed to the pebble as if it were a criminal",
        answer="A round pebble was caught in the penguin's scarf.",
    ),
}

ASP_RULES = r"""
solvable(C) :- case(C), has_clue(C), has_reveal(C), has_action(C).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for cid, case in CASES.items():
        lines.extend([
            asp.fact("case", cid),
            asp.fact("has_clue", cid),
            asp.fact("has_reveal", cid),
            asp.fact("has_action", cid),
        ])
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid() -> set[tuple]:
    import asp
    model = asp.one_model(asp_program("#show solvable/1."))
    return set(asp.atoms(model, "solvable"))

def valid_cases() -> set[str]:
    return set(CASES)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A humorous penguin detective story on a rocky shore.")
    parser.add_argument("--place", choices=SETTINGS)
    parser.add_argument("--penguin")
    parser.add_argument("--detective")
    parser.add_argument("--case", choices=CASES)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    case = args.case or rng.choice(sorted(CASES))
    return StoryParams(
        place=args.place or "rocky_shore",
        penguin=args.penguin or rng.choice(PENGUINS),
        detective=args.detective or rng.choice(DETECTIVES),
        case=case,
        opening=rng.randrange(4),
        turn=rng.randrange(4),
        ending=rng.randrange(4),
    )


def build_world(params: StoryParams) -> World:
    if params.place not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.place}")
    if params.case not in CASES:
        raise StoryError(f"Unknown case: {params.case}")

    case = CASES[params.case]
    world = World(SETTINGS[params.place])
    penguin = world.add(Entity(
        "penguin",
        params.penguin,
        "penguin",
        meters={"itch": 0.0, "comfort": 0.0},
        memes={"awe": 0.0, "humor": 0.0, "curiosity": 1.0},
    ))
    detective = world.add(Entity(
        "detective",
        params.detective,
        "detective",
        meters={"clue": 0.0},
        memes={"patience": 1.0, "pride": 0.0},
    ))
    world.add(Entity("shore", "the rocky shore", "place", meters={"wetness": 1.0}))

    world.facts.update(case=case, penguin=penguin, detective=detective)

    openings = [
        f"{penguin.label} waddled along {world.place} wearing a red scarf and the serious expression of a detective who had misplaced his breakfast.",
        f"At dawn, {detective.label} arrived at {world.place}, where {penguin.label} stood beside the tide pool like a very round, very worried witness.",
        f"The rocks at {world.place} glittered under the morning sun. {penguin.label} did not glitter at all; he scratched one flipper and sighed.",
        f"{penguin.label} had promised to enjoy a quiet morning at {world.place}, but quiet mornings rarely survive a penguin with an itch.",
    ]
    world.say(openings[params.opening])
    world.say(f"The case began when {case.clue}.")
    penguin.meters["itch"] = 1.0
    world.para()

    world.say(f'"I have a clue," said {penguin.label}. "It is either important or hiding under my feathers."')
    world.say(f'"Every mystery starts with a question," replied {detective.label}. "What do you notice?"')
    world.say(f"{penguin.label} pointed toward the rocks. {case.suspicion.capitalize()}.")

    world.para()
    world.say(f"{detective.label} crouched low and examined the pebbles, seaweed, and damp sand.")
    world.say(f"The detective found a trail of small clues: {case.clue}.")
    detective.meters["clue"] = 1.0
    if params.turn % 2 == 0:
        world.say(f'"Do not flap before you think," said {detective.label}.')
    else:
        world.say(f'"Aha!" cried {penguin.label}. "My flipper says the answer is nearby."')
    world.say(f"After one careful search, they discovered that {case.reveal}.")
    world.say(f'The mystery changed from frightening to funny. "{case.action.capitalize()}," said {detective.label}.')
    penguin.meters["itch"] = 0.0
    penguin.meters["comfort"] = 1.0
    penguin.memes["awe"] = 1.0
    penguin.memes["humor"] = 1.0
    detective.memes["pride"] = 1.0

    world.para()
    endings = [
        f"{case.ending}. {detective.label} wrote the solution in a notebook, though the page got damp when {penguin.label} hugged it.",
        f"By sunset, {case.ending}. The two detectives shared a snack and agreed that the best clues sometimes tickle.",
        f"{case.ending}. Then {detective.label} pinned a tiny sign to the shore: NO SEA MONSTERS, OCTOPUSES WELCOME.",
        f"{case.ending}. {penguin.label} strutted home, certain that tomorrow's mystery would be less itchy and more snack-shaped.",
    ]
    world.say(endings[params.ending])
    return world


def prompts(world: World) -> list[str]:
    case: Case = world.facts["case"]
    penguin: Entity = world.facts["penguin"]
    return [
        f"Write a humorous detective story about {penguin.label}, a penguin on a rocky shore, solving a mystery involving {case.clue}.",
        "Tell a child-friendly detective tale with a penguin, awe, an itch-dim, and a funny reveal.",
        f"Create a rocky-shore mystery in which the clue is solved through careful looking rather than guessing.",
    ]


def story_qa(world: World) -> list[QAItem]:
    case: Case = world.facts["case"]
    penguin: Entity = world.facts["penguin"]
    detective: Entity = world.facts["detective"]
    return [
        QAItem("Who was the main detective?", f"{penguin.label} was the penguin witness, helped by {detective.label}."),
        QAItem("What problem started the mystery?", case.answer),
        QAItem("How did the detectives solve the case?", f"They solved it by looking carefully and then they {case.action}."),
        QAItem("What changed at the end?", f"{penguin.label}'s itch-dim faded, and the mystery ended with humor and awe."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a penguin?", "A penguin is a flightless seabird that swims well and uses its flippers to move through water."),
        QAItem("What is awe?", "Awe is a feeling of wonder when something seems especially beautiful, surprising, or grand."),
        QAItem("What is a rocky shore?", "A rocky shore is a coast where stones and rocks meet the sea."),
        QAItem("What does a detective do?", "A detective studies clues, asks questions, and uses careful reasoning to solve a mystery."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(f"{entity.label}: meters={meters} memes={memes}")
    return "\n".join(lines)


def emit(sample: StorySample, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_verify() -> int:
    py = {(case,) for case in valid_cases()}
    cl = asp_valid()
    if py == cl:
        print(f"OK: ASP and Python agree on {len(py)} valid cases.")
        return 0
    print("Mismatch between ASP and Python.")
    print("Only Python:", sorted(py - cl))
    print("Only ASP:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp or args.asp:
        print(asp_program("#show solvable/1."))
        return
    if args.verify:
        raise SystemExit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, case in enumerate(sorted(CASES)):
            rng = random.Random(base_seed + index)
            params = resolve_params(argparse.Namespace(
                place="rocky_shore",
                penguin=None,
                detective=None,
                case=case,
            ), rng)
            params = StoryParams(**{**params.__dict__, "seed": base_seed + index})
            samples.append(generate(params))
    else:
        for index in range(args.n):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params = StoryParams(**{**params.__dict__, "seed": base_seed + index})
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
