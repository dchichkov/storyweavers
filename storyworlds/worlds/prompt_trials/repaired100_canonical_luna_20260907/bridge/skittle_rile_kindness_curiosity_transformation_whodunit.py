#!/usr/bin/env python3
"""The Skittle Riddle: a kindness-and-curiosity whodunit."""

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
import random
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from results import QAItem, StoryError, StorySample


@dataclass
class Entity:
    id: str
    label: str
    kind: str = "thing"
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    beliefs: dict[str, str] = field(default_factory=dict)


@dataclass
class Event:
    kind: str
    text: str
    speaker: str = ""
    listener: str = ""
    question: str = ""
    cause: str = ""
    result: str = ""
    state: dict = field(default_factory=dict)


@dataclass
class StoryParams:
    hero: str = "Luna"
    friend: str = "Milo"
    culprit: str = "wind"
    clue: str = "blue"
    seed: int = 777


NAMES = ("Luna", "Milo", "Nia", "Owen", "Pia", "Tess")
CULPRITS = {
    "wind": "a playful gust",
    "raven": "a curious raven",
    "kitten": "a striped kitten",
}
CLUES = {
    "blue": "a blue thread",
    "feather": "a soft gray feather",
    "paw": "a tiny muddy paw mark",
}
PROMPT = (
    "Write a dialogue-rich children's whodunit in which Luna investigates a missing "
    "skittle with curiosity, kindness, and a surprising transformation."
)


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities = {
            "hero": Entity(
                "hero", params.hero, "character", memes={"curiosity": 0.5, "kindness": 0.5}
            ),
            "friend": Entity(
                "friend", params.friend, "character", memes={"curiosity": 0.5, "kindness": 0.5}
            ),
            "skittle": Entity(
                "skittle", "the red skittle", "candy", "cup",
                meters={"found": 0, "transformed": 0},
                memes={"mystery": 1.0},
            ),
            "clue": Entity(
                "clue", CLUES[params.clue], "clue", "garden",
                meters={"noticed": 0},
            ),
            "snack": Entity(
                "snack", "the shared snack jar", "container", "bench",
                meters={"pieces": 6},
            ),
        }
        self.history: list[Event] = []

    def snapshot(self) -> dict:
        return {key: asdict(value) for key, value in self.entities.items()}

    def narrate(self, kind: str, text: str, *, question="", cause="", result=""):
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

    def say(self, speaker: str, text: str, *, to=""):
        actor = self.entities[speaker]
        label = actor.label
        verb = "asked" if text.endswith("?") else "said"
        self.history.append(
            Event(
                kind="speech",
                text=f'"{text}" {label} {verb}.',
                speaker=speaker,
                listener=to,
                state=self.snapshot(),
            )
        )


def validate_params(params: StoryParams):
    if params.culprit not in CULPRITS or params.clue not in CLUES:
        raise StoryError("Choose a listed culprit and clue.")
    if params.hero == params.friend:
        raise StoryError("The two investigators need different names.")
    if any(not re.fullmatch(r"[A-Z][a-z]+", n) for n in (params.hero, params.friend)):
        raise StoryError("Names must be simple capitalized names, such as Luna and Milo.")


def build_world(params: StoryParams) -> World:
    validate_params(params)
    world = World(params)
    world.entities["culprit"] = Entity(
        "culprit",
        CULPRITS[params.culprit],
        "suspect",
        "garden",
        meters={"moved_skittle": 1},
        memes={"shyness": 0.4},
    )
    return world


def solve_mystery(world: World):
    clue = world.entities["clue"]
    skittle = world.entities["skittle"]
    culprit = world.entities["culprit"]
    clue.meters["noticed"] = 1
    skittle.location = "garden"
    skittle.meters["found"] = 1
    culprit.memes["shyness"] = 0.0
    if world.params.culprit == "wind":
        skittle.meters["transformed"] = 1
        skittle.memes["mystery"] = 0.0


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    h = world.entities["hero"].label
    f = world.entities["friend"].label
    clue = world.entities["clue"].label
    culprit = world.entities["culprit"].label

    world.narrate(
        "beginning",
        f"{h} placed one bright red skittle beside the snack jar on the garden bench. "
        f"When {h} turned to fetch a napkin, the skittle vanished. {f} was the only friend nearby.",
    )
    world.say("hero", "My red skittle is gone. Did you see who took it?")
    world.say("friend", "I saw a flash near the flower bed, but I did not take it.")
    world.say("hero", "Then we need clues, not guesses.")
    world.say("friend", "Good. Let us look gently, so we do not scare anyone away.")

    world.entities["hero"].memes["curiosity"] = 1.0
    world.entities["friend"].memes["curiosity"] = 1.0
    world.narrate(
        "investigation",
        f"They followed a faint trail from the bench to the flower bed. Beside a leaf lay {clue}.",
        question="Why did the friends investigate the garden?",
        cause="The skittle had disappeared and a faint trail led toward the flower bed.",
        result="They chose to inspect real clues instead of blaming the nearby friend.",
    )
    world.say("hero", f"This {clue} might tell us more. What do you think it means?")
    world.say("friend", "It means someone or something brushed past the flowers.")
    world.say("hero", "Could the wind have carried the skittle?")
    world.say("friend", "Maybe, but let us check where the trail ends.")

    world.narrate(
        "clue",
        f"The trail stopped beneath a broad leaf. A small red shine peeked from its edge, while {culprit} watched from behind the flowers.",
        question="What clue did the investigators find?",
        cause=f"A trail led from the bench, and {clue} rested beside the flower bed.",
        result="They found the skittle beneath a leaf and noticed the quiet suspect nearby.",
    )
    world.say("hero", "There you are! Did you move the skittle?")
    world.say("friend", "Wait. The little watcher looks frightened.")
    world.say("hero", "You are right. We can ask without scolding.")
    world.say("friend", "Perhaps it was trying to help, not make us upset.")

    if params.culprit == "wind":
        world.narrate(
            "reveal",
            f"A sudden breeze lifted the leaf. The skittle rolled into the sunlight, and {culprit} fluttered harmlessly through the flowers.",
            question="Who moved the skittle?",
            cause="A gust had pushed the skittle from the bench and tucked it beneath the leaf.",
            result="The mystery changed from a theft into a small accident.",
        )
    elif params.culprit == "raven":
        world.narrate(
            "reveal",
            f"{culprit.capitalize()} hopped forward and nudged the leaf aside. It had carried the shiny skittle to its nest, thinking it was a jewel.",
            question="Why did the suspect move the skittle?",
            cause="The raven mistook the bright candy for a jewel.",
            result="The friends discovered curiosity rather than bad intent.",
        )
    else:
        world.narrate(
            "reveal",
            f"{culprit.capitalize()} peeked out and pushed the skittle forward with one careful paw. It had rolled the candy away while chasing the clue.",
            question="Why did the suspect move the skittle?",
            cause="The kitten had batted the candy while playing.",
            result="The friends learned that the disappearance was playful, not mean.",
        )

    world.say("hero", "We found it. Would you like to help us share it?")
    world.say("friend", "A mystery can end with kindness.")
    world.entities["hero"].memes["kindness"] = 1.0
    world.entities["friend"].memes["kindness"] = 1.0
    world.entities["snack"].meters["pieces"] -= 1
    world.entities["skittle"].location = "shared"
    world.entities["skittle"].meters["transformed"] = 1
    world.entities["skittle"].memes["mystery"] = 0.0

    world.narrate(
        "transformation",
        f"{h} broke the skittle into tiny colorful pieces and placed them in the shared snack jar. "
        f"The missing candy had transformed a worry into a welcome.",
        question="How did the friends respond after solving the mystery?",
        cause="They learned that the skittle had been moved by accident or curiosity.",
        result="They shared the candy instead of punishing the harmless suspect.",
    )
    world.say("hero", "Next time, I will ask before I decide what happened.")
    world.say("friend", "And I will help look for clues before I make a guess.")
    world.narrate(
        "ending",
        f"The garden grew quiet. {h} and {f} watched the flowers sway while {culprit} stayed close to the shared jar. "
        "The skittle was gone, but their kindness made the little mystery bright.",
    )

    sample = StorySample(
        params=params,
        story="\n\n".join(event.text for event in world.history),
        prompts=[PROMPT],
        story_qa=[
            QAItem(event.question, f"{event.cause} {event.result}")
            for event in world.history
            if event.question
        ],
        world_qa=[
            QAItem(
                "What does curiosity help the investigators do?",
                "Curiosity helps them look for evidence and ask questions before deciding what happened.",
            ),
            QAItem(
                "What kind choice do the friends make?",
                "They share the skittle and treat the harmless suspect gently instead of blaming it.",
            ),
        ],
        world=world,
    )
    check_sample(sample)
    return sample


def check_sample(sample: StorySample):
    world = sample.world
    if world.entities["skittle"].location != "shared":
        raise StoryError("The skittle must reach the shared snack jar.")
    if not world.entities["skittle"].meters["transformed"]:
        raise StoryError("The mystery must transform into a kindness moment.")
    if any(world.entities[k].memes["kindness"] < 1 for k in ("hero", "friend")):
        raise StoryError("Both friends must complete the kindness change.")
    speeches = [e for e in world.history if e.kind == "speech"]
    if len(speeches) < 10 or any(sum(e.speaker == k for e in speeches) < 4 for k in ("hero", "friend")):
        raise StoryError("The whodunit needs a sustained exchange between both friends.")
    if len(sample.story_qa) < 3:
        raise StoryError("The story needs grounded questions and answers.")
    if not any("clue" in e.kind or e.kind == "investigation" for e in world.history):
        raise StoryError("The investigators must use a concrete clue.")


ASP_RULES = """
suspect(wind) :- culprit(wind).
suspect(raven) :- culprit(raven).
suspect(kitten) :- culprit(kitten).
valid_clue(C) :- clue(C).
mystery_resolves(C, S) :- valid_clue(C), suspect(S).
#show mystery_resolves/2.
"""


def asp_facts() -> str:
    from asp import fact
    return "\n".join(
        [fact("culprit", key) for key in CULPRITS]
        + [fact("clue", key) for key in CLUES]
    )


def asp_pairs() -> set[tuple[str, str]]:
    from asp import atoms, one_model
    return set(atoms(one_model(asp_facts() + "\n" + ASP_RULES), "mystery_resolves"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--hero")
    parser.add_argument("--friend")
    parser.add_argument("--culprit", choices=tuple(CULPRITS))
    parser.add_argument("--clue", choices=tuple(CLUES))
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(NAMES)
    friend = args.friend or rng.choice([n for n in NAMES if n != hero])
    params = StoryParams(
        hero=hero,
        friend=friend,
        culprit=args.culprit or rng.choice(tuple(CULPRITS)),
        clue=args.clue or rng.choice(tuple(CLUES)),
        seed=args.seed,
    )
    validate_params(params)
    return params


def verify():
    expected = {(culprit, clue) for culprit in CULPRITS for clue in CLUES}
    if asp_pairs() != expected:
        raise StoryError("Python and ASP disagree about mystery combinations.")
    total = 0
    for culprit in CULPRITS:
        for clue in CLUES:
            sample = generate(
                StoryParams(hero="Luna", friend="Milo", culprit=culprit, clue=clue)
            )
            check_sample(sample)
            total += 1
    print(f"OK: {total} story states; {len(expected)} ASP-compatible pairs.")


def emit(sample: StorySample, *, trace=False, qa=False, header=""):
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
            print(json.dumps(sorted(asp_pairs())))
            return 0

        rng = random.Random(args.seed)
        if args.all:
            params_list = [
                StoryParams(
                    hero=args.hero or "Luna",
                    friend=args.friend or "Milo",
                    culprit=culprit,
                    clue=clue,
                    seed=args.seed,
                )
                for culprit in CULPRITS
                for clue in CLUES
                if (args.culprit is None or args.culprit == culprit)
                and (args.clue is None or args.clue == clue)
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
