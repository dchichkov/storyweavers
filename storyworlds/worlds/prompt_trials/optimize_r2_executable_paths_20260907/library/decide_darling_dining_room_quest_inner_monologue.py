#!/usr/bin/env python3
"""Decide, Darling: a dining-room quest about choosing the right place for supper."""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve()
for parent in ROOT.parents:
    if (parent / "results.py").exists():
        sys.path.insert(0, str(parent))
        break

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
    speaker: str = ""
    listener: str = ""
    state: dict = field(default_factory=dict)


@dataclass
class StoryParams:
    hero: str = "Mara"
    helper: str = "Pip"
    problem: str = "find_napkins"
    solution: str = "follow_scent"
    dish: str = "stew"
    approach: str = "pause"
    seed: int = 777


PROBLEMS = {
    "find_napkins": "napkins",
    "choose_seat": "seat",
    "save_cake": "cake",
    "find_spoon": "spoon",
}

SOLUTIONS = {
    "follow_scent": "napkins",
    "count_chairs": "seat",
    "ask_grandma": "cake",
    "listen_drawer": "spoon",
}

DISHES = {
    "stew": ("a warm pot of vegetable stew", "the rosemary scent"),
    "pancakes": ("a stack of golden pancakes", "the buttery scent"),
    "soup": ("a bright bowl of tomato soup", "the basil scent"),
}

APPROACHES = ("pause", "hurry")
NAMES = ("Mara", "Pip", "Nia", "Owen", "Lena", "Toby")
PROMPT = (
    "Write a heartwarming children's story about a small quest in a dining room, "
    "where a careful decision and an inner thought bring two friends together."
)


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities = {
            "hero": Entity(
                "hero", params.hero, "character", "dining_room",
                memes={"worry": 0.7, "trust": 0.5},
            ),
            "helper": Entity(
                "helper", params.helper, "character", "dining_room",
                memes={"worry": 0.3, "trust": 0.6},
            ),
            "table": Entity(
                "table", "the dining table", "furniture", "dining_room",
                meters={"ready": 0},
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

    def say(self, who: str, text: str, *, to: str = "", tag: str = "said"):
        speaker = self.entities[who].label
        if text.endswith("?") and tag == "said":
            tag = "asked"
        self.history.append(
            Event(
                kind="speech",
                text=f'"{text}" {speaker} {tag}.',
                speaker=who,
                listener=to,
                state=self.snapshot(),
            )
        )


def valid_combos() -> list[tuple[str, str]]:
    return [
        (problem, solution)
        for problem, need in PROBLEMS.items()
        for solution, skill in SOLUTIONS.items()
        if need == skill
    ]


def validate_params(params: StoryParams):
    if (params.problem, params.solution) not in valid_combos():
        raise StoryError(
            f"{params.solution!r} cannot solve {params.problem!r}; "
            "choose a compatible quest path."
        )
    if params.dish not in DISHES or params.approach not in APPROACHES:
        raise StoryError("Unknown dish or approach.")
    if params.hero == params.helper:
        raise StoryError("The quest needs two different speakers.")
    if any(not re.fullmatch(r"[A-Z][a-z]+", n) for n in (params.hero, params.helper)):
        raise StoryError("Names must be simple capitalized words, such as Mara and Pip.")


def build_world(params: StoryParams) -> World:
    validate_params(params)
    world = World(params)
    meal, scent = DISHES[params.dish]
    world.entities["meal"] = Entity(
        "meal", meal, "food", "kitchen",
        meters={"warm": 1, "served": 0},
        memes={"comfort": 0.8},
    )
    world.entities["clue"] = Entity(
        "clue", scent, "clue", "dining_room",
        meters={"noticed": 0},
    )
    return world


def finish(world: World):
    hero = world.entities["hero"]
    helper = world.entities["helper"]
    table = world.entities["table"]
    meal = world.entities["meal"]
    if not table.meters.get("ready") or not meal.meters.get("served"):
        raise StoryError("The meal must reach a ready table.")
    if hero.memes["trust"] < 1 or helper.memes["trust"] < 1:
        raise StoryError("The friends must finish with shared trust.")


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    hero = world.entities["hero"].label
    helper = world.entities["helper"].label
    meal, scent = DISHES[params.dish]

    world.narrate(
        "opening",
        f"In the dining room, {hero} saw {meal} waiting in the kitchen. "
        f"The long table gleamed, but supper could not begin until one little quest was finished.",
    )
    world.say("hero", "We need to get everything ready before Grandma rings the bell.")
    world.say("helper", "Then let us decide what to do first.")

    if params.problem == "find_napkins":
        world.narrate(
            "problem",
            f"The napkins were missing. {hero} looked beneath the table, while {helper} watched the quiet hallway.",
            question="Why could the friends not begin supper?",
            cause="The napkins were not on the dining table.",
            result="The friends had to search before serving the meal.",
        )
        world.say("hero", "I could hurry through every room.")
        world.say("helper", "Or we could pause and notice what the room is telling us.")
        if params.approach == "hurry":
            world.narrate(
                "suspense",
                f"{hero} rushed toward the pantry, but stopped when a faint {scent} drifted past the chairs.",
            )
        else:
            world.narrate(
                "suspense",
                f"{hero} closed their eyes. Under the clink of plates came a faint {scent} from the sideboard.",
            )
        world.entities["clue"].meters["noticed"] = 1
        world.say("hero", "The smell is leading us somewhere.")
        world.say("helper", "Follow it, darling. A clue can be quiet and still be true.")
        world.entities["clue"].location = "sideboard"
        world.entities["table"].meters["ready"] = 0
        world.narrate(
            "turn",
            f"Behind the sideboard, {hero} found a basket of folded napkins beside the spice jars.",
            question="How did the friends find the napkins?",
            cause=f"They noticed {scent} and followed the clue to the sideboard.",
            result="They found the folded napkins beside the spice jars.",
        )
        world.say("hero", "I thought I had to search faster.")
        world.say("helper", "You only needed to listen longer.")
        world.entities["table"].meters["ready"] = 1
        world.entities["meal"].location = "dining_room"
        world.entities["meal"].meters["served"] = 1

    elif params.problem == "choose_seat":
        world.narrate(
            "problem",
            f"Four chairs stood around the table, but one was wobbly. {hero} wanted to choose quickly before anyone noticed.",
            question="Why did the friends need to choose a seat carefully?",
            cause="One dining-room chair was wobbly.",
            result="A quick choice could make someone spill supper.",
        )
        world.say("hero", "I will take the first chair I see.")
        world.say("helper", "Wait. Should we count the chairs and test them?")
        if params.approach == "hurry":
            world.narrate("suspense", f"{hero} reached for the nearest chair, and its wooden leg gave a tiny creak.")
        else:
            world.narrate("suspense", f"{hero} paused. The nearest chair leaned just enough to make the spoons tremble.")
        world.say("hero", "That chair is warning us.")
        world.say("helper", "Then count, darling, and choose the steady one.")
        world.entities["table"].meters["ready"] = 1
        world.entities["meal"].location = "dining_room"
        world.entities["meal"].meters["served"] = 1
        world.narrate(
            "turn",
            f"They counted four chairs and tested each leg. {hero} chose the sturdy chair beside {helper}.",
            question="How did the friends avoid the wobbly chair?",
            cause="They counted and tested every chair instead of choosing the nearest one.",
            result="They sat in two steady chairs beside each other.",
        )
        world.say("hero", "A slow decision kept the stew from tipping.")
        world.say("helper", "And it left room for both of us.")
    elif params.problem == "save_cake":
        world.narrate(
            "problem",
            f"A small cake waited in the kitchen, but a warm patch of sunlight crept toward it.",
            question="Why did the friends need to move the cake?",
            cause="Sunlight was warming the cake before supper.",
            result="They needed to find a safer place for it.",
        )
        world.say("hero", "I can hide it under a cloth.")
        world.say("helper", "Ask Grandma first, darling. She may know its best place.")
        if params.approach == "hurry":
            world.narrate("suspense", f"{hero} lifted the cloth, but the cake's icing had begun to soften.")
        else:
            world.narrate("suspense", f"{hero} watched one bright square of sunlight reach the cake stand.")
        world.say("hero", "Grandma, where should the cake wait?")
        world.say("helper", "She says the cool shelf by the blue bowl.")
        world.entities["meal"].location = "cool_shelf"
        world.entities["table"].meters["ready"] = 1
        world.entities["meal"].meters["served"] = 1
        world.narrate(
            "turn",
            f"They carried the cake to the cool shelf by the blue bowl, where its icing stayed smooth.",
            question="How did the friends protect the cake?",
            cause="They asked Grandma instead of guessing where to hide it.",
            result="They placed it on the cool shelf by the blue bowl.",
        )
        world.say("hero", "Asking made the right place easy to find.")
        world.say("helper", "A good question can be part of a quest.")
    else:
        world.narrate(
            "problem",
            f"The soup was ready, but one spoon was missing from the dining table.",
            question="Why did the friends search for a spoon?",
            cause="The soup had no spoon for one hungry guest.",
            result="They needed to find the missing spoon before supper.",
        )
        world.say("hero", "I will open every drawer.")
        world.say("helper", "Listen first. Metal makes a tiny song.")
        if params.approach == "hurry":
            world.narrate("suspense", f"{hero} pulled one drawer, then another, while the soup cooled.")
        else:
            world.narrate("suspense", f"{hero} held still. From the side drawer came a faint silver chime.")
        world.say("hero", "There! I heard it.")
        world.say("helper", "Follow the sound, darling.")
        world.entities["clue"].location = "side_drawer"
        world.entities["table"].meters["ready"] = 1
        world.entities["meal"].location = "dining_room"
        world.entities["meal"].meters["served"] = 1
        world.narrate(
            "turn",
            f"Inside the side drawer, {hero} found the spoon beneath a folded tablecloth.",
            question="How did the friends find the spoon?",
            cause="They listened for a silver chime from the side drawer.",
            result="They found the spoon beneath the folded tablecloth.",
        )
        world.say("hero", "The quietest clue was the best one.")
        world.say("helper", "You noticed it because you stopped to decide.")

    world.entities["hero"].memes.update(worry=0.0, trust=1.0)
    world.entities["helper"].memes.update(worry=0.0, trust=1.0)
    world.narrate(
        "ending",
        f"{hero} placed the last thing on the dining table. {helper} smiled as the bell rang, "
        f"and the warm meal waited between them like a welcome.",
        question="What changed by the end of the quest?",
        cause="The friends listened to a clue and made a careful decision together.",
        result="The dining table became ready, and they could share supper with calm hearts.",
    )
    finish(world)
    story = "\n\n".join(event.text for event in world.history)
    sample = StorySample(
        params=params,
        story=story,
        prompts=[PROMPT],
        story_qa=[
            QAItem(event.question, f"{event.cause} {event.result}")
            for event in world.history
            if event.question
        ],
        world_qa=[
            QAItem(
                "What setting does this story use?",
                "It takes place in a dining room prepared for a shared meal.",
            ),
            QAItem(
                "What helps the characters solve the quest?",
                "They notice a clue, speak honestly, and decide together.",
            ),
        ],
        world=world,
    )
    check_sample(sample)
    return sample


def check_sample(sample: StorySample):
    world = sample.world
    finish(world)
    speech = [e for e in world.history if e.kind == "speech"]
    if len(speech) < 2:
        raise StoryError("The story needs a sustained spoken exchange.")
    if not any(e.speaker == "hero" for e in speech) or not any(e.speaker == "helper" for e in speech):
        raise StoryError("Both characters must speak.")
    if not any("darling" in e.text.lower() for e in speech):
        raise StoryError("The dialogue must include the requested affectionate word.")
    if len(sample.story_qa) < 3:
        raise StoryError("The story needs grounded questions and answers.")
    if re.search(r"\{[^}]+\}", sample.story):
        raise StoryError("Unresolved template text remains in the story.")


ASP_RULES = """
valid(P,S) :- problem(P,N), solution(S,N).
#show valid/2.
"""


def asp_facts() -> str:
    from asp import fact
    facts = [
        *(fact("problem", p, need) for p, need in PROBLEMS.items()),
        *(fact("solution", s, skill) for s, skill in SOLUTIONS.items()),
    ]
    return "\n".join(facts)


def asp_combos() -> set[tuple[str, str]]:
    from asp import atoms, one_model
    return set(atoms(one_model(asp_facts() + "\n" + ASP_RULES), "valid"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--hero")
    parser.add_argument("--helper")
    parser.add_argument("--problem", choices=tuple(PROBLEMS))
    parser.add_argument("--solution", choices=tuple(SOLUTIONS))
    parser.add_argument("--dish", choices=tuple(DISHES))
    parser.add_argument("--approach", choices=APPROACHES)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    choices = [
        pair for pair in valid_combos()
        if (args.problem is None or pair[0] == args.problem)
        and (args.solution is None or pair[1] == args.solution)
    ]
    if not choices:
        raise StoryError("No compatible quest path matches those choices.")
    problem, solution = rng.choice(choices)
    hero = args.hero or rng.choice(NAMES)
    helper_choices = [n for n in NAMES if n != hero and n != args.hero]
    helper = args.helper or rng.choice(helper_choices)
    params = StoryParams(
        hero=hero,
        helper=helper,
        problem=problem,
        solution=solution,
        dish=args.dish or rng.choice(tuple(DISHES)),
        approach=args.approach or rng.choice(APPROACHES),
        seed=args.seed,
    )
    validate_params(params)
    return params


def verify():
    if set(valid_combos()) != asp_combos():
        raise StoryError("Python and ASP disagree about compatible quest paths.")
    tested = 0
    for problem, solution in valid_combos():
        for approach in APPROACHES:
            for dish in DISHES:
                sample = generate(
                    StoryParams(
                        problem=problem,
                        solution=solution,
                        approach=approach,
                        dish=dish,
                    )
                )
                check_sample(sample)
                tested += 1
    print(f"OK: {tested} story states; {len(valid_combos())} compatible paths.")


def emit(sample: StorySample, *, trace=False, qa=False, header=""):
    if header:
        print(header)
    print(sample.story)
    if qa:
        for item in sample.story_qa:
            print(f"\nQ: {item.question}\nA: {item.answer}")
    if trace:
        print(
            "\nTRACE\n"
            + json.dumps(
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
                (problem, solution, approach)
                for problem, solution in valid_combos()
                for approach in APPROACHES
                if (args.problem is None or problem == args.problem)
                and (args.solution is None or solution == args.solution)
                and (args.approach is None or approach == args.approach)
            ]
            if not paths:
                raise StoryError("No paths match the selected filters.")
            params_list = [
                resolve_params(
                    argparse.Namespace(
                        **{
                            **vars(args),
                            "problem": problem,
                            "solution": solution,
                            "approach": approach,
                        }
                    ),
                    rng,
                )
                for problem, solution, approach in paths
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
