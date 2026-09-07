#!/usr/bin/env python3
"""A gentle bedtime story about sharing a funny nose and noticing a clue early."""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pathlib import Path as _StoryPath
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
sys.path.insert(0, str(_storyworlds_root))
from results import QAItem, StoryError, StorySample


@dataclass
class Entity:
    id: str
    label: str
    kind: str = "thing"
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Event:
    kind: str
    text: str
    question: str = ""
    cause: str = ""
    result: str = ""
    state: dict = field(default_factory=dict)


@dataclass
class StoryParams:
    child: str = "Mia"
    companion: str = "Pip"
    nose: str = "button"
    sharing: str = "turns"
    clue: str = "warm"
    seed: int = 777


NAMES = ("Mia", "Noor", "Lily", "Sam", "Theo", "Ivy")
COMPANIONS = ("Pip", "Bun", "Moss", "Toto")
NOSES = {
    "button": ("a shiny red button nose", "red", "It felt warm in the moonlight."),
    "carrot": ("a soft carrot nose", "orange", "A sweet carrot smell drifted from it."),
    "acorn": ("a tiny acorn nose", "brown", "It made a faint wooden tap."),
}
CLUES = ("warm", "sweet", "tapping")
SHARING = ("turns", "blanket", "story")
PROMPT = (
    "Write a cozy bedtime story about a child sharing a funny nose with a sleepy "
    "companion, while an early clue helps them solve a small nighttime problem."
)


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities = {
            "child": Entity(
                "child",
                params.child,
                "character",
                "bedroom",
                memes={"curiosity": 1.0, "kindness": 0.7},
            ),
            "companion": Entity(
                "companion",
                params.companion,
                "companion",
                "bedroom",
                memes={"sleepiness": 0.8, "trust": 0.6},
            ),
            "nose": Entity(
                "nose",
                NOSES[params.nose][0],
                "prop",
                "bedside",
                meters={"held": 0, "shared": 0},
                memes={"silliness": 1.0},
            ),
            "lamp": Entity(
                "lamp",
                "the moon lamp",
                "lamp",
                "bedside",
                meters={"lit": 1},
            ),
        }
        self.history: list[Event] = []

    def snapshot(self) -> dict:
        return {key: asdict(value) for key, value in self.entities.items()}

    def narrate(
        self,
        kind: str,
        text: str,
        *,
        question: str = "",
        cause: str = "",
        result: str = "",
    ):
        self.history.append(
            Event(
                kind=kind,
                text=text,
                question=question,
                cause=cause,
                result=result,
                state=self.snapshot(),
            )
        )

    def sample(self) -> StorySample:
        story_qa = [
            QAItem(question=e.question, answer=f"{e.cause} {e.result}")
            for e in self.history
            if e.question
        ]
        world_qa = [
            QAItem(
                question="Why can sharing make a bedtime game feel kinder?",
                answer="Sharing lets each person have a turn and shows that the game belongs to everyone.",
            ),
            QAItem(
                question="Why is an early clue useful in a story?",
                answer="An early clue gives the characters a detail they can remember when a problem appears later.",
            ),
        ]
        return StorySample(
            params=self.params,
            story="\n\n".join(event.text for event in self.history),
            prompts=[PROMPT],
            story_qa=story_qa,
            world_qa=world_qa,
            world=self,
        )


def validate_params(params: StoryParams):
    if params.nose not in NOSES:
        raise StoryError("Choose a nose from the available nose shapes.")
    if params.sharing not in SHARING:
        raise StoryError("Choose a sharing method from turns, blanket, or story.")
    if params.clue not in CLUES:
        raise StoryError("Choose a clue that can be noticed and remembered.")
    if params.child == params.companion:
        raise StoryError("The child and companion need different names.")
    if any(not re.fullmatch(r"[A-Z][a-z]+", name) for name in (params.child, params.companion)):
        raise StoryError("Names must be simple capitalized names, such as Mia and Pip.")


def build_world(params: StoryParams) -> World:
    validate_params(params)
    world = World(params)
    world.entities["nose"].meters["clue_value"] = 1
    return world


def check_ending(world: World):
    nose = world.entities["nose"]
    companion = world.entities["companion"]
    if nose.meters["shared"] != 1:
        raise StoryError("The nose must be shared by the end.")
    if companion.location != "bed":
        raise StoryError("The sleepy companion must reach bed.")
    if companion.memes.get("trust", 0) < 1:
        raise StoryError("The final sharing should build trust.")


def check_sample(sample: StorySample):
    world = sample.world
    check_ending(world)
    if len(world.history) < 6:
        raise StoryError("The bedtime story needs a beginning, turn, and ending.")
    if len(sample.story_qa) < 3:
        raise StoryError("The story needs at least three grounded questions.")
    if "nose" not in sample.story.lower():
        raise StoryError("The story must keep the nose visible in its narrative.")
    if not any("earlier" in event.text.lower() or "remembered" in event.text.lower()
               for event in world.history):
        raise StoryError("The foreshadowed clue must return later.")


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    child = world.entities["child"]
    companion = world.entities["companion"]
    nose = world.entities["nose"]
    c, p = child.label, companion.label
    nose_text, color, clue_line = NOSES[params.nose]

    world.narrate(
        "beginning",
        f"At bedtime, {c} tucked {p} beneath the quilt and found {nose_text} "
        f"beside the moon lamp. It was the perfect nose for a quiet game.",
        question="What did the child find before bedtime?",
        cause=f"{c} found {nose_text} beside the moon lamp.",
        result=f"The funny nose became ready for a bedtime game.",
    )

    world.narrate(
        "foreshadowing",
        f"When {c} picked up the nose, {clue_line} "
        f"{c} smiled and remembered that small detail.",
        question="What clue did the child notice early?",
        cause=f"The nose gave a {params.clue} clue when {c} picked it up.",
        result=f"{c} remembered the clue instead of letting it slip away.",
    )

    if params.sharing == "turns":
        world.narrate(
            "sharing",
            f"{c} put the nose on and made a tiny royal bow. Then {c} handed it to {p}. "
            f"{p} wore it for one turn and giggled into the quilt.",
            question="How did the friends share the nose?",
            cause=f"{c} offered the nose to {p} after taking the first turn.",
            result="They gave each person one turn instead of keeping the nose for one person.",
        )
    elif params.sharing == "blanket":
        world.narrate(
            "sharing",
            f"{c} placed the nose on the quilt between them. "
            f"Each friend could touch it, admire it, and leave it in the middle.",
            question="How did the friends share the nose?",
            cause=f"{c} placed the nose in the middle of the quilt.",
            result="Both friends could enjoy it without pulling it away from each other.",
        )
    else:
        world.narrate(
            "sharing",
            f"{c} and {p} passed the nose while telling a sleepy story. "
            f"Every time the nose changed hands, the story gained another silly sentence.",
            question="How did the friends share the nose?",
            cause=f"They passed the nose while adding sentences to their shared story.",
            result="The nose and the story belonged to both of them.",
        )
    nose.meters["shared"] = 1

    world.narrate(
        "turn",
        f"Then the moon lamp blinked out. The room became soft and dark, and {p} "
        f"could not find the quilt's edge.",
        question="What small problem happened?",
        cause="The moon lamp went dark while the friends were playing.",
        result=f"{p} could not find the quilt's edge in the dark.",
    )
    child.memes["curiosity"] += 0.2
    nose.meters["held"] = 1

    if params.clue == "warm":
        solution = (
            f"{c} remembered that the nose had felt warm. {c} held it low and followed "
            f"the warm little spot until it touched the quilt's edge."
        )
    elif params.clue == "sweet":
        solution = (
            f"{c} remembered the sweet smell from the nose. The scent was strongest "
            f"near the basket where the quilt had slipped down."
        )
    else:
        solution = (
            f"{c} remembered the faint tapping sound. The nose tapped against the "
            f"wooden bedpost beside the quilt's missing corner."
        )

    world.narrate(
        "solution",
        solution,
        question="How did the early clue help solve the problem?",
        cause=f"{c} used the {params.clue} clue noticed when the nose was first picked up.",
        result=f"{c} used the nose to find the quilt's edge in the dark.",
    )

    nose.location = "quilt_edge"
    companion.location = "bed"
    companion.memes["trust"] = 1.0
    child.memes["kindness"] = 1.0

    world.narrate(
        "ending",
        f"{c} pulled the quilt gently around {p}. The moon lamp glowed again, "
        f"and the little {color} nose rested between their pillows, ready to be shared "
        f"again tomorrow. Soon the room held only two slow breaths and one happy dream.",
        question="What changed by the end of the bedtime story?",
        cause=f"{c} shared the nose and used its remembered clue to help {p}.",
        result=f"{p} felt safe beneath the quilt, and the nose became a shared treasure.",
    )

    sample = world.sample()
    check_sample(sample)
    return sample


ASP_RULES = """
clue(warm).
clue(sweet).
clue(tapping).
sharing(turns).
sharing(blanket).
sharing(story).
nose(button).
nose(carrot).
nose(acorn).
valid(N,S,C) :- nose(N), sharing(S), clue(C).
#show valid/3.
"""


def asp_facts() -> str:
    from asp import fact

    return "\n".join(
        [fact("nose", name) for name in NOSES]
        + [fact("sharing", name) for name in SHARING]
        + [fact("clue", name) for name in CLUES]
    )


def asp_combos() -> set[tuple[str, str, str]]:
    from asp import atoms, one_model

    return set(atoms(one_model(ASP_RULES), "valid"))


def valid_combos() -> list[tuple[str, str, str]]:
    return [(nose, sharing, clue) for nose in NOSES for sharing in SHARING for clue in CLUES]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--child")
    parser.add_argument("--companion")
    parser.add_argument("--nose", choices=tuple(NOSES))
    parser.add_argument("--sharing", choices=SHARING)
    parser.add_argument("--clue", choices=CLUES)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    nose, sharing, clue = rng.choice(valid_combos())
    child = args.child or rng.choice(NAMES)
    companion = args.companion or rng.choice([x for x in COMPANIONS if x != child])
    params = StoryParams(
        child=child,
        companion=companion,
        nose=args.nose or nose,
        sharing=args.sharing or sharing,
        clue=args.clue or clue,
        seed=args.seed,
    )
    validate_params(params)
    return params


def verify():
    if set(valid_combos()) != asp_combos():
        raise StoryError("Python and ASP disagree on valid story combinations.")
    tested = 0
    for nose, sharing, clue in valid_combos():
        sample = generate(
            StoryParams(
                child="Mia",
                companion="Pip",
                nose=nose,
                sharing=sharing,
                clue=clue,
            )
        )
        check_sample(sample)
        tested += 1
    print(f"OK: {tested} story states; {len(valid_combos())} ASP-compatible combinations.")


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = ""):
    if header:
        print(header)
    print(sample.story)
    if qa:
        for item in sample.story_qa:
            print(f"\nQ: {item.question}\nA: {item.answer}")
    if trace:
        print("\nTRACE")
        print(
            json.dumps(
                {
                    "entities": sample.world.snapshot(),
                    "history": [asdict(event) for event in sample.world.history],
                },
                indent=2,
            )
        )


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        if args.n < 1:
            raise StoryError("-n must be positive.")
        if args.show_asp:
            print(asp_facts() + "\n" + ASP_RULES)
            return 0
        if args.verify:
            verify()
            return 0
        if args.asp:
            print(json.dumps(sorted(asp_combos())))
            return 0

        rng = random.Random(args.seed)
        if args.all:
            combinations = [
                combo
                for combo in valid_combos()
                if args.nose is None or combo[0] == args.nose
                if args.sharing is None or combo[1] == args.sharing
                if args.clue is None or combo[2] == args.clue
            ]
            if not combinations:
                raise StoryError("No combinations match the selected options.")
            params_list = [
                StoryParams(
                    child=args.child or "Mia",
                    companion=args.companion or "Pip",
                    nose=nose,
                    sharing=sharing,
                    clue=clue,
                    seed=args.seed,
                )
                for nose, sharing, clue in combinations
            ]
        else:
            params_list = [resolve_params(args, rng) for _ in range(args.n)]

        samples = [generate(params) for params in params_list]
        if args.json:
            payload = [sample.to_dict() for sample in samples]
            print(json.dumps(payload[0] if len(payload) == 1 else payload, indent=2, ensure_ascii=False))
        else:
            for index, sample in enumerate(samples):
                emit(
                    sample,
                    trace=args.trace,
                    qa=args.qa,
                    header=f"\n### Story {index + 1}\n" if len(samples) > 1 else "",
                )
        return 0
    except StoryError as exc:
        parser.error(str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
