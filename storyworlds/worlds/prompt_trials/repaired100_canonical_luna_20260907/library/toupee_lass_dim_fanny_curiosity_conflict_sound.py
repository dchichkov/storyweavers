#!/usr/bin/env python3
"""A small space adventure about a toupee, Lass-Dim, and Fanny."""

from __future__ import annotations

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
    kind: str
    location: str
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
    hero: str = "Lass-Dim"
    friend: str = "Fanny"
    object: str = "toupee"
    problem: str = "lost_signal"
    solution: str = "follow_sound"
    style: str = "Space Adventure"
    seed: int = 777


OBJECTS = {
    "toupee": {
        "label": "the silver toupee",
        "location": "cargo_bay",
        "sound": "whir-whir",
        "clue": "a tiny silver comb",
    },
    "helmet": {
        "label": "the moon helmet",
        "location": "cargo_bay",
        "sound": "plink-plink",
        "clue": "a blue scratch",
    },
    "map": {
        "label": "the star map",
        "location": "cargo_bay",
        "sound": "beep-beep",
        "clue": "a glowing corner",
    },
}

PROBLEMS = {"lost_signal": "signal", "blocked_door": "door", "dark_corridor": "light"}
SOLUTIONS = {"follow_sound": "signal", "tap_panel": "door", "carry_beacon": "light"}
NAMES = ("Lass-Dim", "Fanny", "Zora", "Pip", "Milo")
PROMPT = (
    "Write a dialogue-rich children's Space Adventure about Lass-Dim and Fanny, "
    "a toupee, curiosity, conflict, and useful sound effects."
)


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities = {
            "hero": Entity("hero", params.hero, "character", "bridge",
                           memes={"curiosity": 1.0, "worry": 0.4, "trust": 0.5}),
            "friend": Entity("friend", params.friend, "character", "bridge",
                            memes={"curiosity": 0.8, "worry": 0.5, "trust": 0.5}),
            "object": Entity("object", OBJECTS[params.object]["label"], "thing",
                             OBJECTS[params.object]["location"],
                             meters={"found": 0, "signal": 0}),
            "door": Entity("door", "the cargo-bay door", "machine", "cargo_bay",
                           meters={"open": 0}),
        }
        self.history: list[Event] = []

    def snapshot(self) -> dict:
        return {key: asdict(value) for key, value in self.entities.items()}

    def narrate(self, kind: str, text: str, *, question="", cause="", result=""):
        self.history.append(Event(kind, text, question, cause, result, self.snapshot()))

    def say(self, speaker: str, text: str):
        label = self.entities[speaker].label
        verb = "asked" if text.endswith("?") else "said"
        self.history.append(Event("speech", f'"{text}" {label} {verb}.',
                                  state=self.snapshot()))

    def settle(self):
        for key in ("hero", "friend"):
            self.entities[key].memes["trust"] = 1.0
            self.entities[key].memes["worry"] = 0.0


def validate_params(params: StoryParams):
    if params.problem not in PROBLEMS or params.solution not in SOLUTIONS:
        raise StoryError("Unknown problem or solution.")
    if PROBLEMS[params.problem] != SOLUTIONS[params.solution]:
        raise StoryError("That solution does not address the selected space problem.")
    if params.object not in OBJECTS:
        raise StoryError("Unknown adventure object.")
    if params.hero == params.friend:
        raise StoryError("The two space explorers need different names.")
    if any(not re.fullmatch(r"[A-Z][A-Za-z-]+", n) for n in (params.hero, params.friend)):
        raise StoryError("Explorer names must begin with a capital letter.")


def build_world(params: StoryParams) -> World:
    validate_params(params)
    return World(params)


def follow_sound(world: World):
    obj = world.entities["object"]
    if obj.meters.get("signal") != 1:
        raise StoryError("The explorers must switch on the object's signal first.")
    obj.location = "under_console"
    obj.meters["found"] = 1


def tap_panel(world: World):
    door = world.entities["door"]
    if door.location != "cargo_bay":
        raise StoryError("The explorers must reach the cargo-bay panel.")
    door.meters["open"] = 1


def carry_beacon(world: World):
    hero = world.entities["hero"]
    obj = world.entities["object"]
    if obj.meters.get("found") != 1:
        raise StoryError("The beacon cannot light a corridor until it is found.")
    hero.meters["beacon"] = 1


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    hero = world.entities["hero"].label
    friend = world.entities["friend"].label
    item = OBJECTS[params.object]
    thing = item["label"]

    world.narrate(
        "beginning",
        f"On the little starship Comet Finch, {hero} and {friend} checked the cargo bay "
        f"before jumping to the blue moon. A {thing} rested in a supply crate.",
    )

    if params.problem == "lost_signal":
        world.say("hero", f"Why is the {thing} humming inside the crate?")
        world.say("friend", "Do not open it yet. The ship is shaking.")
        world.narrate(
            "conflict",
            f"{hero} wanted to investigate, but {friend} pointed at the warning lights. "
            f"Then the crate vanished behind a sliding panel. Whirr!",
            question="Why did the explorers lose the signal?",
            cause=f"{thing.capitalize()} slipped behind the cargo panel while the ship shook.",
            result="The explorers could hear it but could not see where it had gone.",
        )
        world.say("hero", "Curiosity may help us find it.")
        world.say("friend", "Or curiosity may make us lose the whole cargo bay.")
        world.say("hero", "Listen first. I hear a soft sound.")
        world.say("friend", f"What sound does the {thing} make?")
        world.entities["object"].meters["signal"] = 1
        world.say("hero", f"It goes {item['sound']} near the floor.")
        world.say("friend", "Then we can follow the sound instead of guessing.")
        follow_sound(world)
        world.narrate(
            "turn",
            f"They crouched beside the console. {item['sound'].capitalize()}! The sound grew loud, "
            f"and {friend} spotted {item['clue']} under the panel.",
            question="How did they find the hidden object?",
            cause=f"{hero} listened for the object's {item['sound']} signal.",
            result=f"They followed the sound and found {thing} under the console.",
        )
        world.say("friend", "You were right to be curious, but we needed a careful plan.")
        world.say("hero", "And you were right that rushing would be risky.")
        world.say("friend", "Together, we can ask questions before pressing buttons.")
        world.say("hero", "That sounds like a captain's rule.")
        world.narrate(
            "ending",
            f"{hero} placed {thing} safely on the shelf. Its little signal answered with "
            f"one cheerful {item['sound']} as Comet Finch sailed toward the moon.",
            question="What did the explorers learn about curiosity?",
            cause="Curiosity helped them notice the sound, while caution kept them from rushing.",
            result="They learned to investigate bravely and carefully together.",
        )

    elif params.problem == "blocked_door":
        world.say("hero", "The cargo door will not open. I should pull it harder.")
        world.say("friend", "Stop! The red panel says gentle taps.")
        world.narrate(
            "conflict",
            f"The door stayed shut. {hero} tugged once, and the ship answered, " 
            "KLANG! A loose toolbox wobbled beside the panel.",
            question="Why did the cargo door remain closed?",
            cause=f"{hero} tried pulling instead of using the panel's gentle tapping signal.",
            result="The door's safety lock stayed on.",
        )
        world.say("hero", "Maybe the door is hiding a space monster.")
        world.say("friend", "Or maybe it is waiting for us to read the instructions.")
        world.say("hero", "What sound should the panel make?")
        world.say("friend", "Tap-tap, then wait.")
        tap_panel(world)
        world.narrate(
            "turn",
            f"{hero} tapped the panel. Tap-tap! The red light turned green, and the door rolled open.",
            question="How did the explorers open the door?",
            cause="They followed the panel's instruction to tap twice and wait.",
            result="The safety lock released and the cargo door opened.",
        )
        world.say("friend", "Your question about a monster made me laugh.")
        world.say("hero", "Your careful reading saved us from a very loud tug.")
        world.say("friend", "Curiosity is best when it listens.")
        world.say("hero", "And conflict is smaller when we talk.")
        world.narrate(
            "ending",
            f"Beyond the open door, starlight shone over {thing}. The panel gave one soft "
            "beep, as if the ship agreed with them.",
            question="What changed after the door opened?",
            cause="The explorers stopped pulling and listened to the sound pattern on the panel.",
            result="They opened the door safely by cooperating.",
        )

    else:
        world.say("hero", "The corridor is dark. I will race through it.")
        world.say("friend", "Please do not race where you cannot see.")
        world.narrate(
            "conflict",
            f"The corridor swallowed the explorers' boots. Clunk! {hero} bumped a storage bin, "
            "and the moon map slid across the floor.",
            question="Why was racing through the corridor dangerous?",
            cause="The corridor was dark, so objects and safe steps could not be seen.",
            result=f"{hero} bumped a bin and nearly lost {thing}.",
        )
        world.say("hero", "I want to know what is at the end.")
        world.say("friend", "Then let us carry a light and move together.")
        world.say("hero", "Can the object help us find the way?")
        world.say("friend", "Yes, if we find it first.")
        world.entities["object"].meters["signal"] = 1
        follow_sound(world)
        carry_beacon(world)
        world.narrate(
            "turn",
            f"They followed {item['sound']} to the console and found {thing}. "
            f"When {hero} lifted it, a warm beam swept across the corridor. Fwoosh!",
            question="How did they light the dark corridor?",
            cause=f"They followed the object's sound and found it under the console.",
            result=f"{hero} carried the object as a beacon, lighting the path.",
        )
        world.say("friend", "Now we can see each safe step.")
        world.say("hero", "And I can still be curious without running.")
        world.say("friend", "That is a brave kind of careful.")
        world.say("hero", "Let us explore the moon together.")
        world.narrate(
            "ending",
            f"The beacon painted a golden path to the moon hatch. {hero} and {friend} "
            f"walked side by side while {thing} hummed softly.",
            question="What did the explorers learn in the dark?",
            cause="They used the found object as a beacon instead of rushing blindly.",
            result="They explored safely by sharing curiosity and caution.",
        )

    world.settle()
    sample = StorySample(
        params=params,
        story="\n\n".join(e.text for e in world.history),
        prompts=[PROMPT],
        story_qa=[
            QAItem(e.question, f"{e.cause} {e.result}")
            for e in world.history if e.question
        ],
        world_qa=[
            QAItem("What kind of storyworld is this?", "It is a Space Adventure about explorers solving a problem with curiosity, cooperation, and sound clues."),
            QAItem("Who are the explorers?", f"{hero} and {friend} are the explorers aboard Comet Finch."),
        ],
        world=world,
    )
    check_sample(sample)
    return sample


ASP_RULES = """
valid(P,S) :- problem(P,N), solution(S,N).
#show valid/2.
"""


def asp_facts() -> str:
    from asp import fact
    return "\n".join(
        [fact("problem", p, need) for p, need in PROBLEMS.items()]
        + [fact("solution", s, need) for s, need in SOLUTIONS.items()]
    )


def valid_combos() -> list[tuple[str, str]]:
    return [
        (problem, solution)
        for problem, need in PROBLEMS.items()
        for solution, capability in SOLUTIONS.items()
        if need == capability
    ]


def asp_combos() -> set[tuple[str, str]]:
    from asp import atoms, one_model
    return set(atoms(one_model(asp_facts() + ASP_RULES), "valid"))


def check_sample(sample: StorySample):
    world = sample.world
    if world.entities["hero"].memes["trust"] < 1 or world.entities["friend"].memes["trust"] < 1:
        raise StoryError("The explorers must resolve their conflict.")
    if len(sample.story_qa) < 3:
        raise StoryError("The story needs at least three grounded questions.")
    speech = [e for e in world.history if e.kind == "speech"]
    if len(speech) < 12:
        raise StoryError("The explorers need a sustained back-and-forth exchange.")
    if not any("!" in e.text for e in world.history):
        raise StoryError("The story needs clear sound effects.")
    if world.params.problem == "lost_signal" and not world.entities["object"].meters["found"]:
        raise StoryError("The lost object must be found.")
    if world.params.problem == "blocked_door" and not world.entities["door"].meters["open"]:
        raise StoryError("The cargo door must open.")
    if world.params.problem == "dark_corridor" and not world.entities["hero"].meters.get("beacon"):
        raise StoryError("The corridor must be lit by the beacon.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--hero")
    parser.add_argument("--friend")
    parser.add_argument("--object", choices=tuple(OBJECTS))
    parser.add_argument("--problem", choices=tuple(PROBLEMS))
    parser.add_argument("--solution", choices=tuple(SOLUTIONS))
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    choices = [
        pair for pair in valid_combos()
        if args.problem is None or pair[0] == args.problem
        if args.solution is None or pair[1] == args.solution
    ]
    if not choices:
        raise StoryError("No compatible problem and solution were selected.")
    problem, solution = rng.choice(choices)
    hero = args.hero or rng.choice(NAMES)
    friend = args.friend or rng.choice([n for n in NAMES if n != hero])
    params = StoryParams(
        hero=hero,
        friend=friend,
        object=args.object or rng.choice(tuple(OBJECTS)),
        problem=problem,
        solution=solution,
        seed=args.seed,
    )
    validate_params(params)
    return params


def verify():
    if set(valid_combos()) != asp_combos():
        raise StoryError("Python and ASP disagree about valid combinations.")
    count = 0
    for problem, solution in valid_combos():
        for obj in OBJECTS:
            sample = generate(StoryParams(
                problem=problem, solution=solution, object=obj, seed=42
            ))
            check_sample(sample)
            count += 1
    print(f"OK: {count} story states; {len(valid_combos())} compatible pairs.")


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
            "history": [asdict(e) for e in sample.world.history],
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
                if args.problem and args.problem != problem:
                    continue
                if args.solution and args.solution != solution:
                    continue
                local = argparse.Namespace(**vars(args))
                local.problem = problem
                local.solution = solution
                params_list.append(resolve_params(local, rng))
            if not params_list:
                raise StoryError("No combinations match the selected filters.")
        else:
            params_list = [resolve_params(args, rng) for _ in range(args.n)]

        samples = [generate(params) for params in params_list]
        if args.json:
            payload = [sample.to_dict() for sample in samples]
            print(json.dumps(payload[0] if len(payload) == 1 else payload,
                             ensure_ascii=False, indent=2))
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
