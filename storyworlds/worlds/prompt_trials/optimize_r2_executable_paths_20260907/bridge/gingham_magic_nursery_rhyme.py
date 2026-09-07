#!/usr/bin/env python3
"""Gingham Magic: a nursery-rhyme story about mending a moonlit banner."""

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
    state: dict = field(default_factory=dict)


@dataclass
class StoryParams:
    hero: str = "Pip"
    friend: str = "Mara"
    problem: str = "torn"
    solution: str = "silver"
    creature: str = "moon_moth"
    seed: int = 777


NAMES = ("Pip", "Mara", "Nell", "Toby", "Wren", "Faye")
PROBLEMS = {
    "torn": "A thorn tore the gingham banner.",
    "dim": "The magic squares lost their glow.",
    "tangled": "The banner's ribbon became tangled.",
    "missing": "One blue gingham square was missing.",
}
SOLUTIONS = {
    "silver": "silver_thread",
    "sugar": "sugar_song",
    "bell": "moon_bell",
    "button": "star_button",
}
COMPATIBLE = {
    "torn": {"silver", "button"},
    "dim": {"sugar", "bell"},
    "tangled": {"bell", "silver"},
    "missing": {"button", "sugar"},
}
CREATURES = {
    "moon_moth": "the moon moth",
    "rain_crow": "the rain crow",
    "star_mouse": "the star mouse",
}
PROMPT = (
    "Write a dialogue-rich Nursery Rhyme about two children using Magic to repair "
    "a gingham moon-banner before the village bedtime parade."
)


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities = {
            "hero": Entity("hero", params.hero, "character", memes={"courage": 0.5, "trust": 0.5}),
            "friend": Entity("friend", params.friend, "character", memes={"wisdom": 0.5, "trust": 0.5}),
            "banner": Entity("banner", "the gingham moon-banner", "banner",
                             location="washing_line", meters={"magic": 1, "mended": 0, "bright": 1}),
            "creature": Entity("creature", CREATURES[params.creature], "helper",
                               location="moon_garden", meters={"helped": 0}),
            "parade": Entity("parade", "the bedtime parade", "event",
                             location="village_lane", meters={"ready": 0}),
        }
        self.history: list[Event] = []

    def snapshot(self) -> dict:
        return {key: asdict(value) for key, value in self.entities.items()}

    def narrate(self, kind: str, text: str, *, question="", cause="", result=""):
        self.history.append(Event(kind, text, question=question, cause=cause,
                                  result=result, state=self.snapshot()))

    def say(self, speaker: str, text: str, *, listener=""):
        if text.endswith("?"):
            verb = "asked"
        else:
            verb = "said"
        self.history.append(Event(
            "speech", f'"{text}" {self.entities[speaker].label} {verb}.',
            speaker=speaker, listener=listener, state=self.snapshot()))

    def sample(self) -> StorySample:
        return StorySample(
            params=self.params,
            story="\n\n".join(event.text for event in self.history),
            prompts=[PROMPT],
            story_qa=[
                QAItem(event.question, f"{event.cause} {event.result}")
                for event in self.history if event.question
            ],
            world_qa=[
                QAItem("What kind of cloth was the banner made from?",
                       "The banner was made from gingham cloth."),
                QAItem("What made the banner special?",
                       "Magic made its checked squares shine in moonlight."),
            ],
            world=self,
        )


def valid_combos() -> list[tuple[str, str]]:
    return [(problem, solution) for problem in PROBLEMS for solution in COMPATIBLE[problem]]


def validate_params(params: StoryParams):
    if (params.problem, params.solution) not in valid_combos():
        raise StoryError(
            f"The {params.solution!r} magic cannot repair the {params.problem!r} banner problem."
        )
    if params.creature not in CREATURES:
        raise StoryError("Choose a known moonlit helper.")
    if params.hero == params.friend:
        raise StoryError("The two rhyme-makers need different names.")
    if any(not re.fullmatch(r"[A-Z][a-z]+", name)
           for name in (params.hero, params.friend)):
        raise StoryError("Names must be simple capitalized words, such as Pip and Mara.")


def build_world(params: StoryParams) -> World:
    validate_params(params)
    return World(params)


def apply_magic(world: World):
    banner = world.entities["banner"]
    problem = world.params.problem
    solution = world.params.solution
    if problem == "torn" and solution == "silver":
        banner.meters.update(magic=2, mended=1, bright=2)
    elif problem == "torn" and solution == "button":
        banner.meters.update(magic=2, mended=1, bright=2)
    elif problem == "dim" and solution == "sugar":
        banner.meters.update(magic=2, bright=3)
    elif problem == "dim" and solution == "bell":
        banner.meters.update(magic=2, bright=3)
    elif problem == "tangled" and solution == "bell":
        banner.meters.update(magic=2, mended=1, bright=2)
    elif problem == "tangled" and solution == "silver":
        banner.meters.update(magic=2, mended=1, bright=2)
    elif problem == "missing" and solution == "button":
        banner.meters.update(magic=2, mended=1, bright=2)
    elif problem == "missing" and solution == "sugar":
        banner.meters.update(magic=2, mended=1, bright=2)
    else:
        raise StoryError("The selected magic has no known effect on this banner.")
    world.entities["creature"].meters["helped"] = 1
    world.entities["parade"].meters["ready"] = 1


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    h, f = params.hero, params.friend
    creature = CREATURES[params.creature]
    world.narrate(
        "opening",
        f"By the moon's pale spoon, {h} and {f} hung a gingham banner above the lane. "
        f"Its red-and-white squares held a little Magic, and {creature} waited in the garden."
    )
    world.say("hero", "Shall we raise the banner for the bedtime parade?", listener="friend")
    world.say("friend", "Yes, but look closely. Its moonlight magic is not quite right.",
              listener="hero")

    problem_text = {
        "torn": "A thorn had torn one corner, and the loose threads fluttered like tiny flags.",
        "dim": "Several bright squares had gone dull, as if the moon had forgotten their names.",
        "tangled": "Its ribbon tails were knotted in a twist around the old apple branch.",
        "missing": "A blue square was gone, leaving a little window in the checked cloth.",
    }
    world.narrate("discovery", problem_text[params.problem])
    world.say("hero", "Could we pull it tight and hope the magic returns?", listener="friend")
    world.say("friend", "Hope is a start, but a rhyme needs the right small deed.",
              listener="hero")

    clues = {
        "torn": "The silver moon-thread shines wherever cloth needs joining.",
        "dim": "A sugar song can wake a sleeping sparkle, while a bell can call moonlight near.",
        "tangled": "The moon bell rings a path through knots, but silver thread can bind a loose loop.",
        "missing": "A star button can fill a hole, while a sugar song can ask the cloth to grow.",
    }
    world.narrate(
        "clue",
        f"{creature.capitalize()} fluttered down and whispered, \"{clues[params.problem]}\"",
        question="What clue helped the children choose their magic?",
        cause=clues[params.problem],
        result=f"{h} and {f} learned that {params.solution} was a suitable remedy."
    )
    world.say("hero", "Then we must use the magic that matches the trouble.", listener="friend")
    world.say("friend", "I will hold the banner. You begin the rhyme.", listener="hero")

    action_text = {
        ("torn", "silver"): f"{h} threaded silver moon-thread through the torn gingham corner.",
        ("torn", "button"): f"{f} set a star button over the torn gingham corner.",
        ("dim", "sugar"): f"{h} sang a sugar-sweet rhyme to the dull gingham squares.",
        ("dim", "bell"): f"{f} rang a moon bell beside each sleepy square.",
        ("tangled", "bell"): f"{h} rang the moon bell, and the knots loosened one by one.",
        ("tangled", "silver"): f"{f} looped silver thread around the ribbon and drew it straight.",
        ("missing", "button"): f"{h} fastened a star button where the blue gingham square was missing.",
        ("missing", "sugar"): f"{f} sang softly, and a new blue square grew from the cloth.",
    }
    world.narrate(
        "repair",
        action_text[(params.problem, params.solution)],
        question="How did the children repair the banner?",
        cause=PROBLEMS[params.problem],
        result=action_text[(params.problem, params.solution)]
    )
    apply_magic(world)
    world.say("friend", "The squares are shining again!", listener="hero")
    world.say("hero", "And the banner is ready to wave for everyone.", listener="friend")
    world.narrate(
        "test",
        f"{creature.capitalize()} tugged the lower edge. The gingham banner billowed, "
        "and not one thread, knot, or square came loose.",
        question="How did they know the repair worked?",
        cause="The helper tugged the banner after the magic was used.",
        result="It billowed brightly without coming loose."
    )
    world.say("hero", "One, two, moon, and star—shall we lead the lane?", listener="friend")
    world.say("friend", "Lead on, and let the gingham sparkle far.", listener="hero")
    world.narrate(
        "ending",
        f"The bedtime parade began. {h} carried the bright banner, {f} sang beside it, "
        f"and {creature} fluttered above like a silver comma in the sky."
    )
    sample = world.sample()
    check_sample(sample)
    return sample


ASP_RULES = """
compatible(P,S) :- problem(P,S).
compatible(P,S) :- problem(P,S2), repair(S), fits(S2,S).
#show compatible/2.
"""


def asp_facts() -> str:
    from asp import fact
    lines = []
    for problem, solutions in COMPATIBLE.items():
        for solution in solutions:
            lines.append(fact("problem", problem, solution))
    for solution in SOLUTIONS:
        lines.append(fact("repair", solution))
    for problem, solutions in COMPATIBLE.items():
        for solution in solutions:
            lines.append(fact("fits", problem, solution))
    return "\n".join(lines)


def asp_combos() -> set[tuple[str, str]]:
    from asp import atoms, one_model
    return set(atoms(one_model(asp_facts() + "\n" + ASP_RULES), "compatible"))


def check_sample(sample: StorySample):
    world = sample.world
    if sample.params.problem != "dim" and world.entities["banner"].meters["mended"] != 1:
        raise StoryError("The ending needs a repaired banner.")
    if world.entities["banner"].meters["bright"] < 2:
        raise StoryError("The Magic must visibly brighten the banner.")
    if world.entities["parade"].meters["ready"] != 1:
        raise StoryError("The parade must become ready.")
    speeches = [event for event in world.history if event.kind == "speech"]
    if not any(event.speaker == "hero" for event in speeches):
        raise StoryError("The hero needs a spoken turn.")
    if not any(event.speaker == "friend" for event in speeches):
        raise StoryError("The friend needs a spoken turn.")
    if len(speeches) < 8:
        raise StoryError("The story needs a real back-and-forth exchange.")
    if len(sample.story_qa) < 3:
        raise StoryError("The story needs grounded questions and answers.")
    if any(token in sample.story for token in ("{", "}", "None", "internal_")):
        raise StoryError("Unresolved internal text leaked into the story.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--hero")
    parser.add_argument("--friend")
    parser.add_argument("--problem", choices=tuple(PROBLEMS))
    parser.add_argument("--solution", choices=tuple(SOLUTIONS))
    parser.add_argument("--creature", choices=tuple(CREATURES))
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [
        pair for pair in sorted(valid_combos())
        if args.problem is None or pair[0] == args.problem
        if args.solution is None or pair[1] == args.solution
    ]
    if not combos:
        raise StoryError("No compatible problem and magic choices were found.")
    problem, solution = rng.choice(combos)
    hero = args.hero or rng.choice(NAMES)
    friend_choices = [name for name in NAMES if name != hero and name != args.hero]
    friend = args.friend or rng.choice(friend_choices)
    return StoryParams(
        hero=hero,
        friend=friend,
        problem=problem,
        solution=solution,
        creature=args.creature or rng.choice(tuple(CREATURES)),
        seed=args.seed,
    )


def verify():
    if set(valid_combos()) != asp_combos():
        raise StoryError("Python and ASP disagree about compatible magic paths.")
    count = 0
    for problem, solution in valid_combos():
        for creature in CREATURES:
            generate(StoryParams(problem=problem, solution=solution, creature=creature))
            count += 1
    print(f"OK: {count} story states; {len(valid_combos())} compatible magic paths.")


def emit(sample: StorySample, *, trace=False, qa=False, header=""):
    if header:
        print(header)
    print(sample.story)
    if qa:
        for item in sample.story_qa:
            print(f"\nQ: {item.question}\nA: {item.answer}")
    if trace:
        print("\nTRACE")
        print(json.dumps({
            "entities": sample.world.snapshot(),
            "history": [asdict(event) for event in sample.world.history],
        }, indent=2))


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
            params_list = []
            for problem, solution in valid_combos():
                if args.problem and problem != args.problem:
                    continue
                if args.solution and solution != args.solution:
                    continue
                params_list.append(StoryParams(
                    hero=args.hero or rng.choice(NAMES),
                    friend=args.friend or rng.choice(
                        [name for name in NAMES if name != (args.hero or "")]),
                    problem=problem,
                    solution=solution,
                    creature=args.creature or rng.choice(tuple(CREATURES)),
                    seed=args.seed,
                ))
        else:
            params_list = [resolve_params(args, rng) for _ in range(args.n)]

        samples = [generate(params) for params in params_list]
        if args.json:
            payload = [sample.to_dict() for sample in samples]
            print(json.dumps(payload[0] if len(payload) == 1 else payload,
                             ensure_ascii=False, indent=2))
        else:
            for index, sample in enumerate(samples):
                emit(sample, trace=args.trace, qa=args.qa,
                     header=f"\n### Story {index + 1}\n" if len(samples) > 1 else "")
        return 0
    except StoryError as exc:
        parser.error(str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
