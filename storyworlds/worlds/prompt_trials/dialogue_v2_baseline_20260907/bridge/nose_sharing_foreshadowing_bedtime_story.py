#!/usr/bin/env python3
"""A gentle bedtime story about a nose, a shared secret, and a small surprise."""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from pathlib import Path as _StoryPath
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
sys.path.insert(0, str(_storyworlds_root))
from results import QAItem, StoryError, StorySample


@dataclass
class Entity:
    id: str
    label: str
    kind: str
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
    child: str = "Nora"
    companion: str = "Pip"
    scent: str = "vanilla"
    keepsake: str = "a silver bell"
    sharing: str = "secret"
    seed: int = 777


NAMES = ("Nora", "Milo", "Lena", "Owen", "Iris", "Toby")
SCENTS = {
    "vanilla": "warm vanilla",
    "cinnamon": "sweet cinnamon",
    "rain": "the clean smell of rain",
}
KEEPSAKES = {
    "silver": "a silver bell",
    "blue": "a blue button",
    "gold": "a golden thread",
}
PROMPT = (
    "Write a gentle bedtime story in which a child and a small companion share "
    "a secret through a nose-led adventure, with a quiet foreshadowed surprise."
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
                memes={"curiosity": 1.0, "trust": 0.5},
            ),
            "companion": Entity(
                "companion",
                params.companion,
                "character",
                "bedroom",
                memes={"hope": 1.0, "trust": 0.5},
            ),
            "nose": Entity(
                "nose",
                "the little nose",
                "sense",
                "bedroom",
                meters={"scent_strength": 0.0, "noticed": 0},
            ),
            "keepsake": Entity(
                "keepsake",
                params.keepsake,
                "object",
                "under_pillow",
                meters={"found": 0, "shared": 0},
            ),
            "window": Entity(
                "window",
                "the moonlit window",
                "place",
                "bedroom",
                meters={"open": 0},
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
    ) -> None:
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

    def share(self) -> None:
        child = self.entities["child"]
        companion = self.entities["companion"]
        keepsake = self.entities["keepsake"]
        if not child.memes.get("knows_secret") or not companion.memes.get("knows_secret"):
            raise StoryError("The secret must be discovered before it can be shared.")
        if not keepsake.meters["found"]:
            raise StoryError("The keepsake must be found before it can be shared.")
        companion.memes["trust"] = 1.0
        child.memes["trust"] = 1.0
        keepsake.meters["shared"] = 1

    def sample(self) -> StorySample:
        return StorySample(
            params=self.params,
            story="\n\n".join(event.text for event in self.history),
            prompts=[PROMPT],
            story_qa=[
                QAItem(
                    question=event.question,
                    answer=f"{event.cause} {event.result}",
                )
                for event in self.history
                if event.question
            ],
            world_qa=[
                QAItem(
                    question="Why can a nose help someone notice a hidden thing?",
                    answer="A nose can notice a scent that points toward something nearby.",
                ),
                QAItem(
                    question="Why is sharing a secret an act of trust?",
                    answer="Sharing a secret lets another person hold something important with care.",
                ),
            ],
            world=self,
        )


def validate_params(params: StoryParams) -> None:
    if params.child == params.companion:
        raise StoryError("The child and companion need different names.")
    for name in (params.child, params.companion):
        if not name.isalpha() or not name[0].isupper():
            raise StoryError("Names must be simple capitalized words.")
    if params.scent not in SCENTS:
        raise StoryError("Choose a scent from the registered scent list.")
    if params.keepsake not in KEEPSAKES:
        raise StoryError("Choose a keepsake from the registered keepsake list.")
    if params.sharing != "secret":
        raise StoryError("This bedtime trial is built around sharing a secret.")


def build_world(params: StoryParams) -> World:
    validate_params(params)
    world = World(params)
    world.entities["nose"].meters["scent_strength"] = 1.0
    return world


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    child = params.child
    companion = params.companion
    scent = SCENTS[params.scent]
    keepsake = params.keepsake
    nose = world.entities["nose"]
    child_entity = world.entities["child"]
    companion_entity = world.entities["companion"]
    found = world.entities["keepsake"]

    world.narrate(
        "beginning",
        f"At bedtime, {child} tucked the blankets beneath {companion}'s chin. "
        f"The room was quiet except for the moon making a pale square on the floor.",
    )
    world.narrate(
        "foreshadowing",
        f"Then {child}'s nose gave a tiny wiggle. It noticed {scent} drifting from somewhere "
        f"near the pillow, although neither friend had left a treat there.",
        question="What first hinted that something was hidden nearby?",
        cause=f"{child}'s nose noticed {scent} in the quiet bedroom.",
        result="The unusual scent gave the friends a clue to follow.",
    )
    nose.meters["noticed"] = 1

    world.narrate(
        "search",
        f"{child} lifted the pillow, but there was only a warm hollow beneath it. "
        f"{companion} listened as the scent curled toward the moonlit window.",
    )
    world.narrate(
        "conversation",
        f'"Should we tell each other what we are hoping for?" whispered {companion}. '
        f'{child} nodded, because a hope feels less heavy when two friends carry it.',
    )
    child_entity.memes["knows_secret"] = True
    companion_entity.memes["knows_secret"] = True

    world.narrate(
        "discovery",
        f"Together they followed the little nose past the bed and found {keepsake} beneath "
        f"the blanket chest. A narrow moonbeam shone across it like a path.",
        question="How did the friends find the hidden keepsake?",
        cause=f"The nose followed the smell of {scent} from the pillow toward the window.",
        result=f"The friends looked beneath the blanket chest and found {keepsake}.",
    )
    found.meters["found"] = 1

    world.narrate(
        "sharing",
        f"{child} picked up {keepsake}, then placed it in {companion}'s careful paws. "
        f'"It can belong to both of us," said {child}. "We can remember this night together."',
        question="What did the friends do with the keepsake?",
        cause=f"{child} wanted the discovery to be a shared memory.",
        result=f"{child} gave {keepsake} to {companion} so they could care for it together.",
    )
    world.share()

    world.narrate(
        "turn",
        f"At once, the old window gave a soft tap. Outside sat a sleepy moth, "
        f"drawn by the same warm scent. It carried a tiny note tied to its leg.",
    )
    world.narrate(
        "revelation",
        f"The note said, 'When you share what is precious, the night makes room for one "
        f"more friend.' {companion} held the note while {child} opened the window a finger's width.",
        question="What surprise followed their sharing?",
        cause="Their kindness made them ready to notice the visitor at the window.",
        result="A sleepy moth arrived with a note about making room for another friend.",
    )
    world.entities["window"].meters["open"] = 1
    world.entities["window"].location = "open_bedroom"

    world.narrate(
        "ending",
        f"The moth rested beside {keepsake}, and the three new friends watched the moon "
        f"climb the sky. Soon {child} and {companion} were tucked in again, their secret "
        f"safe between them and their noses quiet at last.",
    )
    sample = world.sample()
    check_sample(sample)
    return sample


def check_sample(sample: StorySample) -> None:
    world = sample.world
    if not world.entities["keepsake"].meters["found"]:
        raise StoryError("The story must include a real keepsake discovery.")
    if not world.entities["keepsake"].meters["shared"]:
        raise StoryError("The keepsake must be shared.")
    if world.entities["child"].memes["trust"] < 1 or world.entities["companion"].memes["trust"] < 1:
        raise StoryError("Sharing must deepen trust.")
    if not world.entities["nose"].meters["noticed"]:
        raise StoryError("The nose must drive the discovery.")
    if world.entities["window"].meters["open"] != 1:
        raise StoryError("The foreshadowed visitor must arrive through the opened window.")
    if len(sample.story_qa) < 3:
        raise StoryError("The story needs grounded questions and answers.")
    if any(not item.answer.strip() or "{" in item.answer for item in sample.story_qa):
        raise StoryError("Story answers must be complete natural-language explanations.")


ASP_RULES = """
sense(nose).
scent(S) :- scent_value(S).
keepsake(K) :- keepsake_value(K).
valid(S,K) :- scent(S), keepsake(K).
#show valid/2.
"""


def asp_facts() -> str:
    from asp import fact

    facts = [fact("scent_value", value) for value in SCENTS]
    facts += [fact("keepsake_value", value) for value in KEEPSAKES]
    return "\n".join(facts)


def asp_combos() -> set[tuple[str, str]]:
    from asp import atoms, one_model

    return set(atoms(one_model(asp_facts() + "\n" + ASP_RULES), "valid"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--child")
    parser.add_argument("--companion")
    parser.add_argument("--scent", choices=tuple(SCENTS))
    parser.add_argument("--keepsake", choices=tuple(KEEPSAKES))
    parser.add_argument("--sharing", choices=("secret",), default=None)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    child = args.child or rng.choice(NAMES)
    companion = args.companion or rng.choice([name for name in NAMES if name != child])
    params = StoryParams(
        child=child,
        companion=companion,
        scent=args.scent or rng.choice(tuple(SCENTS)),
        keepsake=args.keepsake or rng.choice(tuple(KEEPSAKES)),
        sharing=args.sharing or "secret",
        seed=args.seed,
    )
    validate_params(params)
    return params


def verify() -> None:
    expected = {(scent, keepsake) for scent in SCENTS for keepsake in KEEPSAKES}
    if expected != asp_combos():
        raise StoryError("Python and ASP disagree about registered bedtime combinations.")
    tested = 0
    for scent in SCENTS:
        for keepsake in KEEPSAKES:
            sample = generate(
                StoryParams(
                    child="Nora",
                    companion="Pip",
                    scent=scent,
                    keepsake=keepsake,
                )
            )
            check_sample(sample)
            tested += 1
    print(f"OK: {tested} bedtime stories; {len(expected)} ASP-compatible combinations.")


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
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
            print(json.dumps(sorted(asp_combos()), ensure_ascii=False))
            return 0

        rng = random.Random(args.seed)
        if args.all:
            params_list = [
                StoryParams(
                    child="Nora",
                    companion="Pip",
                    scent=scent,
                    keepsake=keepsake,
                    seed=args.seed,
                )
                for scent in SCENTS
                for keepsake in KEEPSAKES
            ]
        else:
            params_list = [resolve_params(args, rng) for _ in range(args.n)]

        samples = [generate(params) for params in params_list]
        if args.json:
            payload = [sample.to_dict() for sample in samples]
            print(json.dumps(payload[0] if len(payload) == 1 else payload, ensure_ascii=False, indent=2))
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
