#!/usr/bin/env python3
"""Nose Sharing: a gentle bedtime story about noticing a promise before sharing."""

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
    revealed: str = ""
    question: str = ""
    cause: str = ""
    result: str = ""
    state: dict = field(default_factory=dict)


@dataclass
class StoryParams:
    hero: str = "Mina"
    friend: str = "Ollie"
    problem: str = "sneeze"
    solution: str = "cedar"
    approach: str = "ask"
    object: str = "lantern"
    seed: int = 777


NAMES = ("Mina", "Ollie", "Nora", "Pip", "Lena", "Theo")
OBJECTS = {
    "lantern": "the little moon lantern",
    "bell": "the silver bedtime bell",
    "blanket": "the starry blanket",
}
PROBLEMS = {
    "sneeze": "cedar",
    "itch": "wash",
    "cold": "share",
    "dark": "lantern",
}
SOLUTIONS = {
    "cedar": "cedar",
    "wash": "wash",
    "share": "share",
    "lantern": "lantern",
}
APPROACHES = ("ask", "guess")

PROMPT = (
    "Write a gentle bedtime story about two friends sharing a comforting object, "
    "noticing a small nose-related problem, and changing their plan with care."
)


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities = {
            "hero": Entity(
                "hero", params.hero, "character", memes={"calm": 0.4, "trust": 0.6}
            ),
            "friend": Entity(
                "friend", params.friend, "character", memes={"calm": 0.5, "trust": 0.6}
            ),
            "object": Entity(
                "object",
                OBJECTS[params.object],
                "comfort",
                "window_seat",
                meters={"shared": 0, "warmth": 1},
            ),
            "nose": Entity(
                "nose",
                "a small nose",
                "body",
                "friend",
                meters={"itch": 1, "breath": 1},
                memes={"comfort": 0.2},
            ),
            "garden": Entity(
                "garden",
                "the moon garden",
                "place",
                "outside_window",
                meters={"cedar_scent": 1, "distance": 3},
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

    def say(self, speaker: str, text: str, *, to="", reveal="", tag="said"):
        actor = self.entities[speaker]
        if reveal:
            if not to or reveal not in actor.beliefs:
                raise StoryError("A speaker cannot share information they do not know.")
            self.entities[to].beliefs[reveal] = actor.beliefs[reveal]
        if text.endswith("?") and tag == "said":
            tag = "asked"
        self.history.append(
            Event(
                kind="speech",
                text=f'"{text}" {actor.label} {tag}.',
                speaker=speaker,
                listener=to,
                revealed=reveal,
                state=self.snapshot(),
            )
        )

    def sample(self) -> StorySample:
        return StorySample(
            params=self.params,
            story="\n\n".join(event.text for event in self.history),
            prompts=[PROMPT],
            story_qa=[
                QAItem(
                    event.question,
                    f"{event.cause} {event.result}",
                )
                for event in self.history
                if event.question
            ],
            world_qa=[
                QAItem(
                    "Why is sharing easier when friends listen first?",
                    "Listening helps friends notice what another person needs before deciding what to give.",
                ),
                QAItem(
                    "What can a nose notice?",
                    "A nose can notice scents, dust, warmth, and the need for a gentle pause.",
                ),
            ],
            world=self,
        )


ASP_RULES = """
works(P,S) :- problem(P,N), solution(S,N).
#show works/2.
"""


def valid_combos() -> list[tuple[str, str]]:
    return [
        (problem, solution)
        for problem, need in PROBLEMS.items()
        for solution, skill in SOLUTIONS.items()
        if need == skill
    ]


def asp_facts() -> str:
    from asp import fact

    return "\n".join(
        [fact("problem", key, value) for key, value in PROBLEMS.items()]
        + [fact("solution", key, value) for key, value in SOLUTIONS.items()]
    )


def asp_combos() -> set[tuple[str, str]]:
    from asp import atoms, one_model

    return set(atoms(one_model(asp_facts() + "\n" + ASP_RULES), "works"))


def validate_params(params: StoryParams):
    if (params.problem, params.solution) not in valid_combos():
        raise StoryError(
            f"{params.solution!r} cannot help with {params.problem!r}; choose a compatible path."
        )
    if params.approach not in APPROACHES or params.object not in OBJECTS:
        raise StoryError("Unknown approach or comfort object.")
    if params.hero == params.friend:
        raise StoryError("The two friends must have different names.")
    if any(
        not re.fullmatch(r"[A-Z][a-z]+", name)
        for name in (params.hero, params.friend)
    ):
        raise StoryError("Use simple capitalized names, such as Mina and Ollie.")


def build_world(params: StoryParams) -> World:
    validate_params(params)
    return World(params)


def calm(world: World):
    world.entities["nose"].meters["itch"] = 0
    world.entities["nose"].memes["comfort"] = 1
    for key in ("hero", "friend"):
        world.entities[key].memes["calm"] = 1
        world.entities[key].memes["trust"] = 1


def generate(params: StoryParams) -> StorySample:
    rng = random.Random(params.seed)
    world = build_world(params)
    hero, friend = world.entities["hero"], world.entities["friend"]
    h, f = hero.label, friend.label
    comfort = world.entities["object"].label

    openings = [
        f"At bedtime, {h} and {f} sat beneath the quiet window. Between them glowed {comfort}.",
        f"The moon climbed above the roof while {h} carried {comfort} to the window seat where {f} was waiting.",
        f"Before sleep, {h} found {f} beside the window, watching silver light gather around {comfort}.",
    ]
    world.narrate(
        "beginning",
        rng.choice(openings)
        + f" They had promised to share it until the last star blinked.",
    )
    world.say("hero", "We can take turns holding it.")
    world.say("friend", "That sounds cozy. I want to share the first turn.")

    if params.approach == "guess":
        world.say("hero", "Here, you hold it close.")
        world.entities["object"].location = "friend"
        world.entities["object"].meters["shared"] += 1
        world.entities["nose"].meters["itch"] += 1
        failed = {
            "sneeze": f"{f}'s nose wrinkled when a cedar smell drifted in from the open window.",
            "itch": f"{f} rubbed their nose, which had begun to itch beneath the warm blanket.",
            "cold": f"{f} shivered when the cool night air touched their nose.",
            "dark": f"The lantern's glow slipped behind a pillow, and {f} could not see the path to bed.",
        }[params.problem]
        world.narrate("first_try", failed)
        world.say("friend", "Wait. My nose is telling me something.")
        world.say("hero", "I thought sharing meant handing it over quickly.")
    else:
        world.say("hero", "Before we share it, what would feel best?")
        world.say("friend", "Let me notice the room. My nose feels a little unsure.")
        observations = {
            "sneeze": f"{f} sniffed the air and noticed cedar dust drifting from the moon garden.",
            "itch": f"{f} touched their nose and noticed a crumb of blanket fluff tickling it.",
            "cold": f"{f} held out a hand and noticed the window had let a chilly ribbon inside.",
            "dark": f"{f} looked toward the bed and noticed the corner by the rug was too dim.",
        }
        world.narrate("observation", observations[params.problem])

    friend.beliefs["need"] = params.problem

    if params.problem == "sneeze":
        world.say(
            "friend",
            "The cedar smell is making my nose sneeze. Could we close the window?",
            to="hero",
            reveal="need",
        )
        world.say("hero", "Then the moon garden will be quieter too.")
        world.say("friend", "Yes, and we can still share the lantern.")
        world.say("hero", "I will close the window while you keep the lantern safe.")
        world.entities["garden"].meters["cedar_scent"] = 0
        world.entities["nose"].meters["breath"] = 1
        world.narrate(
            "close_window",
            f"{h} eased the window shut. The cedar scent stayed in the garden, and {f} held {comfort} in the calm room.",
            question="Why did the friends close the window?",
            cause="A cedar scent from the moon garden was tickling the friend's nose.",
            result="They closed the window so the scent would stay outside while they continued sharing the lantern.",
        )
        world.say("friend", "My nose feels quiet now.")
        world.say("hero", "Then the light can visit both of us.")

    elif params.problem == "itch":
        world.say(
            "friend",
            "A bit of fluff is tickling my nose. May we brush the blanket first?",
            to="hero",
            reveal="need",
        )
        world.say("hero", "I will hold the lantern while you shake it outside.")
        world.say("friend", "Thank you. I did not want to sneeze on our bedtime glow.")
        world.entities["object"].meters["warmth"] = 1
        world.entities["nose"].meters["itch"] = 0
        world.narrate(
            "brush_blanket",
            f"{f} carried the blanket to the porch and gave it one soft shake. {h} kept {comfort} glowing by the door.",
            question="What did they do about the tickle in the friend's nose?",
            cause="A loose bit of blanket fluff was making the nose itch.",
            result="They brushed the blanket outside before settling down to share the comfort object.",
        )
        world.say("hero", "The fluff flew away like a tiny gray moth.")
        world.say("friend", "And now the blanket feels ready for two sleepers.")

    elif params.problem == "cold":
        world.say(
            "friend",
            "My nose feels cold. Could you share the blanket edge before I hold the lantern?",
            to="hero",
            reveal="need",
        )
        world.say("hero", "Of course. We can make one warm nest instead of two little corners.")
        world.say("friend", "That is better than pretending I am warm.")
        world.entities["object"].meters["warmth"] = 2
        world.entities["object"].meters["shared"] += 1
        world.entities["nose"].meters["breath"] = 1
        world.narrate(
            "share_warmth",
            f"{h} lifted the blanket edge, and {f} tucked close beside them. Together they made room for the glow of {comfort}.",
            question="How did sharing solve the friend's cold nose?",
            cause="Cool air had reached the friend's face before the bedtime turn.",
            result="The friends shared the blanket edge, making one warm nest around the lantern.",
        )
        world.say("friend", "Now the warmth belongs to both of us.")
        world.say("hero", "That is the nicest kind of sharing.")

    else:
        world.say(
            "friend",
            "The corner by the rug is dark. Can we carry the lantern together?",
            to="hero",
            reveal="need",
        )
        world.say("hero", "You hold the handle, and I will watch the rug.")
        world.say("friend", "Then neither of us has to feel our way alone.")
        world.entities["object"].location = "beside_bed"
        world.entities["object"].meters["shared"] += 1
        world.narrate(
            "carry_light",
            f"{h} and {f} carried {comfort} across the rug, one hand on its handle and one hand ready to help.",
            question="Why did the friends carry the lantern together?",
            cause="The path to bed was too dark for the friend to cross comfortably.",
            result="They shared the handle and moved the lantern beside the bed so the path was bright.",
        )
        world.say("hero", "The rug has a silver edge now.")
        world.say("friend", "And the shadows know where to sleep.")

    calm(world)
    world.entities["object"].location = "between_beds"
    world.entities["object"].meters["shared"] += 1
    world.narrate(
        "ending",
        rng.choice(
            [
                f"At last, {comfort} rested between their beds. {h} and {f} listened to the quiet room, where even a small nose could be heard breathing peacefully.",
                f"The moon shone through the closed curtains. {comfort} glowed between the pillows, and both friends settled beneath a kinder, warmer silence.",
                f"One star appeared, then another. The shared comfort waited between the beds while {h} and {f} drifted toward dreams.",
            ]
        ),
        question="What changed by the end of the bedtime story?",
        cause=f"The friends listened when {f}'s nose noticed a need instead of rushing through the sharing.",
        result="They changed their plan, cared for one another, and placed the comfort object between their beds.",
    )
    sample = world.sample()
    check_sample(sample)
    return sample


def check_ending(world: World):
    if world.entities["nose"].meters["itch"] != 0:
        raise StoryError("The nose must be comfortable at the ending.")
    if world.entities["object"].location != "between_beds":
        raise StoryError("The shared comfort object must end between the beds.")
    if world.entities["object"].meters["shared"] < 1:
        raise StoryError("The object must genuinely be shared.")
    if any(world.entities[key].memes["trust"] < 1 for key in ("hero", "friend")):
        raise StoryError("The friends must finish trusting one another.")


def check_sample(sample: StorySample):
    world = sample.world
    check_ending(world)
    speeches = [event for event in world.history if event.kind == "speech"]
    if len(speeches) < 2:
        raise StoryError("The story needs a sustained back-and-forth conversation.")
    if any(not any(event.speaker == key for event in speeches) for key in ("hero", "friend")):
        raise StoryError("Both friends need several spoken turns.")
    if not any(event.revealed for event in speeches):
        raise StoryError("The dialogue must share useful information.")
    if len(sample.story_qa) < 2:
        raise StoryError("The story needs grounded questions and answers.")
    if any(token in sample.story for token in ("{", "}", "None", "meters")):
        raise StoryError("Internal scaffolding leaked into the story.")
    if not sample.story.rstrip().endswith("."):
        raise StoryError("The story must have a complete ending.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--hero")
    parser.add_argument("--friend")
    parser.add_argument("--problem", choices=tuple(PROBLEMS))
    parser.add_argument("--solution", choices=tuple(SOLUTIONS))
    parser.add_argument("--approach", choices=APPROACHES)
    parser.add_argument("--object", choices=tuple(OBJECTS))
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    candidates = [
        pair
        for pair in valid_combos()
        if (args.problem is None or pair[0] == args.problem)
        and (args.solution is None or pair[1] == args.solution)
    ]
    if not candidates:
        raise StoryError("That solution does not fit the selected nose problem.")
    problem, solution = rng.choice(candidates)
    hero = args.hero or rng.choice([name for name in NAMES if name != args.friend])
    friend = args.friend or rng.choice([name for name in NAMES if name != hero])
    params = StoryParams(
        hero=hero,
        friend=friend,
        problem=problem,
        solution=solution,
        approach=args.approach or rng.choice(APPROACHES),
        object=args.object or rng.choice(tuple(OBJECTS)),
        seed=args.seed,
    )
    validate_params(params)
    return params


def verify():
    if set(valid_combos()) != asp_combos():
        raise StoryError("Python and ASP disagree about valid paths.")
    tested = 0
    for problem, solution in valid_combos():
        for approach in APPROACHES:
            for obj in OBJECTS:
                sample = generate(
                    StoryParams(
                        problem=problem,
                        solution=solution,
                        approach=approach,
                        object=obj,
                    )
                )
                check_sample(sample)
                tested += 1
    print(f"OK: {tested} stories; {len(valid_combos())} Python/ASP-compatible paths.")


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
            print(json.dumps(sorted(asp_combos())))
            return 0

        rng = random.Random(args.seed)
        if args.all:
            choices = [
                (problem, solution, approach)
                for problem, solution in valid_combos()
                for approach in APPROACHES
                if (args.problem is None or problem == args.problem)
                and (args.solution is None or solution == args.solution)
                and (args.approach is None or approach == args.approach)
            ]
            if not choices:
                raise StoryError("No compatible paths match these options.")
            params_list = []
            for problem, solution, approach in choices:
                fields = vars(args).copy()
                fields.update(
                    problem=problem,
                    solution=solution,
                    approach=approach,
                )
                params_list.append(resolve_params(argparse.Namespace(**fields), rng))
        else:
            params_list = [resolve_params(args, rng) for _ in range(args.n)]

        samples = [generate(params) for params in params_list]
        if args.json:
            payload = [sample.to_dict() for sample in samples]
            print(
                json.dumps(
                    payload[0] if len(payload) == 1 else payload,
                    ensure_ascii=False,
                    indent=2,
                )
            )
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


if __name__ == "__main__":
    raise SystemExit(main())
