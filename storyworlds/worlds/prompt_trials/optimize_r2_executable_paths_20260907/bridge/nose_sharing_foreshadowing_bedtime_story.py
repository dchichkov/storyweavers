#!/usr/bin/env python3
"""The Moonlit Nose: a gentle bedtime story about sharing a warm little scarf."""

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
    revealed: str = ""
    state: dict = field(default_factory=dict)


@dataclass
class StoryParams:
    child: str = "Lena"
    friend: str = "Pip"
    problem: str = "cold_nose"
    solution: str = "share_scarf"
    clue: str = "warm_breath"
    setting: str = "window_seat"
    seed: int = 777


NAMES = ("Lena", "Milo", "Nora", "Pip", "Tess", "Owen")
SETTINGS = {
    "window_seat": "the window seat",
    "garden_gate": "the little garden gate",
    "pine_step": "the step beneath the pine tree",
}
PROBLEMS = {
    "cold_nose": "cold",
    "shadow_nose": "shadow",
    "lost_scent": "scent",
    "sleepy_nose": "sleepy",
}
SOLUTIONS = {
    "share_scarf": "cold",
    "follow_moon": "shadow",
    "find_lavender": "scent",
    "hum_lullaby": "sleepy",
}
CLUES = {
    "warm_breath": "cold",
    "moonbeam": "shadow",
    "lavender": "scent",
    "soft_song": "sleepy",
}
PROMPT = (
    "Write a gentle bedtime story about two friends who notice a nose in trouble, "
    "share what they have, and follow an early clue to a kind solution."
)


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities = {
            "child": Entity(
                "child", params.child, "character", params.setting,
                memes={"curiosity": 0.6, "kindness": 0.8, "trust": 0.5},
            ),
            "friend": Entity(
                "friend", params.friend, "character", params.setting,
                memes={"worry": 0.5, "kindness": 0.8, "trust": 0.5},
            ),
            "nose": Entity(
                "nose", "the small nose", "body_part", params.setting,
                meters={"warmth": 0.0, "comfort": 0.2, "awake": 1.0},
                memes={"hope": 0.4},
            ),
            "scarf": Entity(
                "scarf", "the long blue scarf", "object", "child",
                meters={"length": 2.0, "shared": 0.0},
            ),
            "moon": Entity(
                "moon", "the round moon", "light", "sky",
                meters={"brightness": 1.0},
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

    def say(
        self,
        speaker: str,
        text: str,
        *,
        listener: str = "",
        reveal: str = "",
    ):
        actor = self.entities[speaker]
        if reveal:
            if not listener or reveal not in actor.beliefs:
                raise StoryError("A speaker cannot share a clue they have not learned.")
            self.entities[listener].beliefs[reveal] = actor.beliefs[reveal]
        tag = "asked" if text.endswith("?") else "said"
        self.history.append(
            Event(
                kind="speech",
                text=f'{actor.label} {tag}, "{text}"',
                speaker=speaker,
                listener=listener,
                revealed=reveal,
                state=self.snapshot(),
            )
        )

    def share_scarf(self):
        scarf = self.entities["scarf"]
        nose = self.entities["nose"]
        if self.entities["child"].location != self.params.setting:
            raise StoryError("The scarf's owner must be beside the cold nose.")
        scarf.meters["shared"] = 1.0
        scarf.location = "between_friends"
        nose.meters["warmth"] = 1.0
        nose.meters["comfort"] = 1.0

    def follow_moon(self):
        nose = self.entities["nose"]
        moon = self.entities["moon"]
        if self.entities["child"].beliefs.get("clue") != "moonbeam":
            raise StoryError("The moonbeam must be noticed before the friends follow it.")
        moon.meters["brightness"] = 1.2
        nose.location = "moonlit_step"
        nose.meters["comfort"] = 1.0

    def find_lavender(self):
        nose = self.entities["nose"]
        if self.entities["friend"].beliefs.get("clue") != "lavender":
            raise StoryError("The lavender scent must be noticed before it can guide them.")
        nose.location = "lavender_pot"
        nose.meters["comfort"] = 1.0

    def hum_lullaby(self):
        nose = self.entities["nose"]
        if self.entities["child"].beliefs.get("clue") != "soft_song":
            raise StoryError("The soft song must be chosen after the sleepy clue.")
        nose.meters["awake"] = 0.0
        nose.meters["comfort"] = 1.0

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
                    question="What did the friends learn about kindness?",
                    answer="They learned that sharing what they had could make a small worry feel safe and warm.",
                )
            ],
            world=self,
        )


def valid_combos() -> list[tuple[str, str, str]]:
    return [
        (problem, solution, clue)
        for problem, needed in PROBLEMS.items()
        for solution, ability in SOLUTIONS.items()
        for clue, clue_for in CLUES.items()
        if needed == ability == clue_for
    ]


def validate_params(params: StoryParams):
    if (params.problem, params.solution, params.clue) not in valid_combos():
        raise StoryError(
            f"{params.solution!r} and {params.clue!r} do not form a compatible path for "
            f"{params.problem!r}."
        )
    if params.setting not in SETTINGS:
        raise StoryError("Unknown bedtime setting.")
    if params.child == params.friend:
        raise StoryError("The two speakers must have different names.")
    if any(not re.fullmatch(r"[A-Z][a-z]+", name) for name in (params.child, params.friend)):
        raise StoryError("Use simple capitalized names, such as Lena and Pip.")


def build_world(params: StoryParams) -> World:
    validate_params(params)
    world = World(params)
    return world


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    child = world.entities["child"]
    friend = world.entities["friend"]
    nose = world.entities["nose"]
    c, f = child.label, friend.label
    place = SETTINGS[params.setting]

    openings = {
        "window_seat": f"Before bed, {c} sat in {place} and watched the moon make a silver path across the floor.",
        "garden_gate": f"Before bed, {c} paused at {place}, where the evening flowers folded their petals.",
        "pine_step": f"Before bed, {c} rested on {place} while the pine branches whispered above.",
    }
    world.narrate(
        "beginning",
        openings[params.setting]
        + f" {f} came softly through the dimness, holding a little basket."
    )
    world.say("child", "You are quiet tonight. What is in the basket?", listener="friend")
    world.say("friend", "A sleepy nose is trying to find its way home.", listener="child")
    world.narrate(
        "foreshadowing",
        f"The small nose peeked from the basket. It trembled once, then turned toward the "
        f"quiet night, as if it already knew that one gentle thing would help.",
        question="What early sign hinted that the nose would need care?",
        cause="The nose trembled and turned toward the night instead of resting.",
        result="The friends understood that they should watch closely and help gently.",
    )

    if params.problem == "cold_nose":
        world.say("child", "Its tip is cold. May I feel the air near it?", listener="friend")
        world.say("friend", "Yes. My breath is warm, but the night is colder.", listener="child")
        child.beliefs["clue"] = "warm_breath"
        world.say(
            "child",
            "The warm breath is a clue. We can share my scarf.",
            listener="friend",
            reveal="clue",
        )
        world.say("friend", "Will there be enough scarf for both of us?", listener="child")
        world.say("child", "If we sit close, there will be enough warmth.", listener="friend")
        world.share_scarf()
        world.narrate(
            "sharing",
            f"{c} wrapped one end of the long blue scarf around {f} and tucked the other end "
            f"near the small nose. They left a little loop loose so the nose could breathe.",
            question="Why did the friends share the scarf?",
            cause="The nose was cold, and their warm breath showed them that gentle warmth was needed.",
            result="They shared one scarf between them and warmed the nose without covering its breath.",
        )
        world.say("friend", "It is warmer now, but I still feel a tiny shiver.", listener="child")
        world.say("child", "Then we will stay until the shiver becomes a sigh.", listener="friend")
        ending = f"The blue scarf made a soft bridge between {c}, {f}, and the sleepy nose."

    elif params.problem == "shadow_nose":
        world.say("child", "The nose keeps turning away. What is it seeing?", listener="friend")
        world.say("friend", "A moonbeam is resting beside the step.", listener="child")
        friend.beliefs["clue"] = "moonbeam"
        world.say(
            "friend",
            "The moonbeam may show it a safe path.",
            listener="child",
            reveal="clue",
        )
        world.say("child", "Let us follow the light slowly.", listener="friend")
        world.follow_moon()
        world.narrate(
            "following",
            f"They followed the pale moonbeam to the quiet step. The nose stopped turning when "
            f"the silver light touched its whiskers.",
            question="Why did the friends follow the moonbeam?",
            cause="The nose kept turning toward a patch of silver light.",
            result="They followed it slowly and found a calm, moonlit place where the nose could rest.",
        )
        world.say("friend", "The shadow is not chasing us here.", listener="child")
        world.say("child", "No. The moon is only showing us where to be gentle.", listener="friend")
        ending = f"Under the moonbeam, the small nose settled like a button on a quiet coat."

    elif params.problem == "lost_scent":
        world.say("friend", "The nose is sniffing for something it cannot find.", listener="child")
        world.say("child", "I smell lavender near the old pot.", listener="friend")
        friend.beliefs["clue"] = "lavender"
        world.say(
            "friend",
            "Then the lavender can guide it home.",
            listener="child",
            reveal="clue",
        )
        world.say("child", "We will follow the scent, not pull the basket.", listener="friend")
        world.find_lavender()
        world.narrate(
            "following",
            f"Step by step, they carried the basket toward the lavender pot. The nose lifted, "
            f"and its worried sniff became a small, pleased sigh.",
            question="How did the friends help the lost nose?",
            cause="The nose was searching for a familiar scent, and lavender was nearby.",
            result="They followed the lavender scent carefully until the nose relaxed beside the pot.",
        )
        world.say("friend", "It remembered this smell.", listener="child")
        world.say("child", "Sometimes a tiny scent can be a big welcome.", listener="friend")
        ending = f"The lavender leaves nodded over the basket while the small nose dreamed of home."

    else:
        world.say("child", "The nose is drooping. Is it hurt?", listener="friend")
        world.say("friend", "No. It is simply sleepy, and the night is very soft.", listener="child")
        child.beliefs["clue"] = "soft_song"
        world.say(
            "child",
            "A soft song may tell it that bedtime is safe.",
            listener="friend",
            reveal="clue",
        )
        world.say("friend", "Will you sing the first line?", listener="child")
        world.say("child", "Only if you hum the second.", listener="friend")
        world.hum_lullaby()
        world.narrate(
            "lullaby",
            f"{c} sang one quiet line, and {f} hummed the next. The nose grew still as the "
            f"little tune curled around the room.",
            question="Why did the friends sing and hum?",
            cause="The nose was sleepy, and their soft voices could make the night feel safe.",
            result="They made a shared lullaby, and the nose relaxed into peaceful sleep.",
        )
        world.say("friend", "It is sleeping now.", listener="child")
        world.say("child", "Then let the last note be a blanket.", listener="friend")
        ending = f"The last note floated down like a blanket and rested beside the sleeping nose."

    nose.memes["hope"] = 1.0
    child.memes["trust"] = 1.0
    friend.memes["trust"] = 1.0
    world.narrate(
        "ending",
        ending
        + f" {c} and {f} stayed together until the moon climbed high, then carried the "
        f"peaceful little basket toward the warm bedroom light.",
    )
    sample = world.sample()
    check_sample(sample)
    return sample


def check_sample(sample: StorySample):
    world = sample.world
    params = sample.params
    nose = world.entities["nose"]
    if nose.meters["comfort"] < 1.0:
        raise StoryError("The nose must become comfortable before the bedtime ending.")
    if nose.memes["hope"] < 1.0:
        raise StoryError("The ending must show a changed emotional state.")
    speech = [event for event in world.history if event.kind == "speech"]
    if not any(event.speaker == "child" for event in speech) or not any(
        event.speaker == "friend" for event in speech
    ):
        raise StoryError("Both characters need spoken turns.")
    if not any(event.listener and event.revealed for event in speech):
        raise StoryError("A spoken exchange must pass a useful clue.")
    if len(sample.story_qa) < 2:
        raise StoryError("The story needs grounded questions and causal answers.")
    if any(
        token in sample.story
        for token in ("{", "}", "meters", "memes", "internal_id")
    ):
        raise StoryError("Internal scaffolding leaked into the story.")
    if params.problem == "cold_nose" and world.entities["scarf"].meters["shared"] != 1.0:
        raise StoryError("The cold-nose path must actually share the scarf.")


ASP_RULES = """
compatible(P,S,C) :- problem(P,K), solution(S,K), clue(C,K).
#show compatible/3.
"""


def asp_facts() -> str:
    from asp import fact

    facts = []
    for problem, kind in PROBLEMS.items():
        facts.append(fact("problem", problem, kind))
    for solution, kind in SOLUTIONS.items():
        facts.append(fact("solution", solution, kind))
    for clue, kind in CLUES.items():
        facts.append(fact("clue", clue, kind))
    return "\n".join(facts)


def asp_combos() -> set[tuple[str, str, str]]:
    from asp import atoms, one_model

    return set(atoms(one_model(asp_facts() + "\n" + ASP_RULES), "compatible"))


def verify():
    python_paths = set(valid_combos())
    if python_paths != asp_combos():
        raise StoryError("Python and ASP disagree about supported paths.")
    tested = 0
    for problem, solution, clue in valid_combos():
        sample = generate(
            StoryParams(
                child="Lena",
                friend="Pip",
                problem=problem,
                solution=solution,
                clue=clue,
                setting="window_seat",
            )
        )
        check_sample(sample)
        tested += 1
    print(f"OK: {tested} executable paths; Python and ASP agree.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--child")
    parser.add_argument("--friend")
    parser.add_argument("--problem", choices=tuple(PROBLEMS))
    parser.add_argument("--solution", choices=tuple(SOLUTIONS))
    parser.add_argument("--clue", choices=tuple(CLUES))
    parser.add_argument("--setting", choices=tuple(SETTINGS), default=None)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    paths = [
        path
        for path in valid_combos()
        if args.problem is None or path[0] == args.problem
        if args.solution is None or path[1] == args.solution
        if args.clue is None or path[2] == args.clue
    ]
    if not paths:
        raise StoryError("Those problem, solution, and clue choices are incompatible.")
    problem, solution, clue = rng.choice(paths)
    child = args.child or rng.choice(NAMES)
    friend_choices = [name for name in NAMES if name != child and name != args.child]
    friend = args.friend or rng.choice(friend_choices)
    params = StoryParams(
        child=child,
        friend=friend,
        problem=problem,
        solution=solution,
        clue=clue,
        setting=args.setting or rng.choice(tuple(SETTINGS)),
        seed=args.seed,
    )
    validate_params(params)
    return params


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
            paths = [
                path
                for path in valid_combos()
                if args.problem is None or path[0] == args.problem
                if args.solution is None or path[1] == args.solution
                if args.clue is None or path[2] == args.clue
            ]
            if not paths:
                raise StoryError("No supported paths match the selected options.")
            params_list = []
            for problem, solution, clue in paths:
                copied = argparse.Namespace(**vars(args))
                copied.problem = problem
                copied.solution = solution
                copied.clue = clue
                params_list.append(resolve_params(copied, rng))
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
