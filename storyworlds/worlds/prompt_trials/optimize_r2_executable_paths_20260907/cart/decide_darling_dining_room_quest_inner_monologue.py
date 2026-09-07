#!/usr/bin/env python3
"""Decide, Darling: a tiny dining-room quest about choosing where a surprise belongs."""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

_ROOT = Path(__file__).resolve()
for parent in _ROOT.parents:
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
    kind: str
    location: str
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
    hero: str = "Nora"
    helper: str = "Pip"
    problem: str = "empty_place"
    solution: str = "window"
    approach: str = "notice"
    treasure: str = "jam_tart"
    seed: int = 777


NAMES = ("Nora", "Milo", "Lena", "Owen", "Iris", "Theo")
TREASURES = {
    "jam_tart": ("a strawberry jam tart", "a red berry"),
    "paper_crown": ("a folded paper crown", "a golden star"),
    "warm_bread": ("a warm loaf of bread", "a brown loaf"),
}
APPROACHES = ("notice", "wonder")

PATHS = {
    ("empty_place", "window"): {
        "problem": "the birthday plate had no welcoming place",
        "clue": "the evening light reached the window table",
        "actions": ("inspect_window", "carry_plate"),
        "ending": "window",
    },
    ("empty_place", "center"): {
        "problem": "the birthday plate had no welcoming place",
        "clue": "everyone could see the center of the table",
        "actions": ("clear_center", "carry_plate"),
        "ending": "center",
    },
    ("dim_room", "lamp"): {
        "problem": "the dining room was too dim for a small celebration",
        "clue": "the brass lamp had a safe empty hook",
        "actions": ("find_lamp", "light_lamp"),
        "ending": "lamp",
    },
    ("dim_room", "curtains"): {
        "problem": "the dining room was too dim for a small celebration",
        "clue": "the curtains were hiding the last daylight",
        "actions": ("open_curtains", "light_lamp"),
        "ending": "curtains",
    },
    ("wobbly_table", "folded_cloth"): {
        "problem": "the table wobbled whenever anyone touched it",
        "clue": "a folded cloth waited in the sideboard",
        "actions": ("find_cloth", "steady_table"),
        "ending": "folded_cloth",
    },
    ("wobbly_table", "short_leg"): {
        "problem": "the table wobbled whenever anyone touched it",
        "clue": "one table leg stood shorter than the others",
        "actions": ("inspect_leg", "steady_table"),
        "ending": "short_leg",
    },
    ("lost_spoon", "napkin"): {
        "problem": "the little celebration spoon had disappeared",
        "clue": "the blue napkins had been folded in pairs",
        "actions": ("search_napkins", "find_spoon"),
        "ending": "napkin",
    },
    ("lost_spoon", "drawer"): {
        "problem": "the little celebration spoon had disappeared",
        "clue": "the shallow drawer had a narrow silver shape inside",
        "actions": ("open_drawer", "find_spoon"),
        "ending": "drawer",
    },
}

PROBLEMS = {
    "empty_place": "birthday_plate",
    "dim_room": "darkness",
    "wobbly_table": "wobble",
    "lost_spoon": "missing_spoon",
}
SOLUTIONS = {
    "window": "birthday_plate",
    "center": "birthday_plate",
    "lamp": "darkness",
    "curtains": "darkness",
    "folded_cloth": "wobble",
    "short_leg": "wobble",
    "napkin": "missing_spoon",
    "drawer": "missing_spoon",
}
PROMPT = (
    "Write a heartwarming children's Quest in a dining room where a child must decide, "
    "darling, while an inner monologue and gentle suspense lead to a kind solution."
)


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities = {
            "hero": Entity("hero", params.hero, "character", "dining room",
                           memes={"courage": 0.4, "warmth": 0.7}),
            "helper": Entity("helper", params.helper, "character", "dining room",
                             memes={"patience": 0.8, "trust": 0.6}),
            "table": Entity("table", "the dining table", "furniture", "dining room",
                            meters={"level": 0.0}),
            "light": Entity("light", "the dining-room light", "fixture", "dining room",
                            meters={"brightness": 0.2}),
            "quest": Entity("quest", "the small celebration", "quest", "dining room",
                            meters={"solved": 0.0}),
        }
        self.history: list[Event] = []

    def snapshot(self) -> dict:
        return {key: asdict(entity) for key, entity in self.entities.items()}

    def narrate(self, kind: str, text: str, *, question: str = "",
                cause: str = "", result: str = "") -> None:
        self.history.append(Event(kind, text, question=question, cause=cause,
                                  result=result, state=self.snapshot()))

    def say(self, speaker: str, text: str, *, listener: str = "") -> None:
        if speaker not in self.entities:
            raise StoryError("Unknown speaker.")
        label = self.entities[speaker].label
        verb = "asked" if text.endswith("?") else "said"
        self.history.append(Event("speech", f'"{text}" {label} {verb}.',
                                  speaker=speaker, listener=listener,
                                  state=self.snapshot()))

    def think(self, text: str) -> None:
        label = self.entities["hero"].label
        self.history.append(Event("inner_monologue",
                                  f"{label} thought, *{text}*",
                                  speaker="hero", state=self.snapshot()))

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
                QAItem("Where did the quest happen?",
                       "The quest happened in the dining room.")
            ],
            world=self,
        )


def valid_combos() -> list[tuple[str, str]]:
    return list(PATHS)


def validate_params(params: StoryParams) -> None:
    if (params.problem, params.solution) not in PATHS:
        raise StoryError(
            f"{params.solution!r} is not compatible with {params.problem!r}."
        )
    if params.approach not in APPROACHES or params.treasure not in TREASURES:
        raise StoryError("Unknown approach or treasure.")
    if params.hero == params.helper:
        raise StoryError("The two characters need different names.")
    for name in (params.hero, params.helper):
        if not re.fullmatch(r"[A-Z][a-z]+", name):
            raise StoryError("Names must be simple capitalized names.")


def build_world(params: StoryParams) -> World:
    validate_params(params)
    world = World(params)
    thing, color = TREASURES[params.treasure]
    world.entities["treasure"] = Entity(
        "treasure", thing, "treasure", "sideboard",
        meters={"safe": 1.0}, memes={"meaning": 1.0}
    )
    world.entities["cloth"] = Entity(
        "cloth", "a folded cloth", "tool", "sideboard",
        meters={"thickness": 0.2}
    )
    world.entities["spoon"] = Entity(
        "spoon", "a little silver spoon", "utensil", "drawer",
        meters={"found": 0.0}
    )
    world.entities["color"] = Entity(
        "color", f"{color}", "detail", "dining room"
    )
    return world


def inspect_window(world: World) -> None:
    world.entities["hero"].beliefs["clue"] = "the evening light reaches the window table"
    world.narrate(
        "clue",
        "Nora peered at the window table. A soft stripe of evening light rested there.",
        question="What clue helped them choose the window table?",
        cause="The evening light reached the window table.",
        result="Nora learned that the small celebration could be seen there.",
    )


def carry_plate(world: World, destination: str) -> None:
    treasure = world.entities["treasure"]
    if "clue" not in world.entities["hero"].beliefs:
        raise StoryError("The child must learn where the treasure belongs before carrying it.")
    treasure.location = destination
    world.entities["quest"].meters["solved"] = 1.0
    world.narrate("quest_action",
                  f"They carried {treasure.label} carefully to {destination}.")


def clear_center(world: World) -> None:
    world.entities["hero"].beliefs["clue"] = "the center lets everyone see"
    world.entities["table"].meters["level"] = 1.0
    world.narrate(
        "clear_center",
        "They moved the salt cellar and made a bright little space in the center.",
        question="Why did they clear the center of the table?",
        cause="The center would let everyone see the celebration.",
        result="The plate could welcome every person at the table.",
    )


def find_lamp(world: World) -> None:
    world.entities["hero"].beliefs["clue"] = "the brass lamp has a safe empty hook"
    world.narrate(
        "clue",
        "Behind the sugar bowl, they found the brass lamp's empty hook.",
        question="What did they discover near the sugar bowl?",
        cause="The lamp had a safe empty hook.",
        result="They knew the lamp could brighten the room without being held.",
    )


def light_lamp(world: World) -> None:
    if "clue" not in world.entities["hero"].beliefs:
        raise StoryError("They need a safe lighting clue before lighting the room.")
    world.entities["light"].meters["brightness"] = 1.0
    world.entities["quest"].meters["solved"] = 1.0
    world.narrate("quest_action", "Pip hung the brass lamp on its hook, and warm light filled the room.")


def open_curtains(world: World) -> None:
    world.entities["hero"].beliefs["clue"] = "the curtains hide the last daylight"
    world.entities["light"].meters["brightness"] = 0.8
    world.narrate(
        "open_curtains",
        "Nora drew the curtains wide. The last daylight slipped across the plates.",
        question="How did they find more light?",
        cause="The curtains were hiding the last daylight.",
        result="Opening them brightened the dining room before the lamp was hung.",
    )


def find_cloth(world: World) -> None:
    world.entities["hero"].beliefs["clue"] = "a folded cloth can steady the table"
    world.narrate(
        "clue",
        "Pip found a folded cloth in the sideboard.",
        question="What useful object did Pip find?",
        cause="A folded cloth was waiting in the sideboard.",
        result="They had something soft to place beneath the short table edge.",
    )


def inspect_leg(world: World) -> None:
    world.entities["hero"].beliefs["clue"] = "one leg is shorter"
    world.narrate(
        "inspect_leg",
        "Nora knelt and saw that one table leg was a little shorter than the others.",
        question="Why did the table wobble?",
        cause="One table leg was shorter than the others.",
        result="They knew which side needed careful support.",
    )


def steady_table(world: World, method: str) -> None:
    if "clue" not in world.entities["hero"].beliefs:
        raise StoryError("They must identify the wobble before steadying the table.")
    world.entities["table"].meters["level"] = 1.0
    world.entities["quest"].meters["solved"] = 1.0
    if method == "folded_cloth":
        text = "They folded the cloth once more and tucked it under the short edge. The table stood still."
    else:
        text = "They slid a small wooden shim beneath the short leg. The table stood still."
    world.narrate("quest_action", text)


def search_napkins(world: World) -> None:
    world.entities["hero"].beliefs["clue"] = "the spoon may be beside the blue napkins"
    world.narrate(
        "search",
        "Nora lifted the blue napkins one by one, while suspense tickled her fingertips.",
        question="Where did Nora first search for the spoon?",
        cause="The blue napkins had been folded in pairs.",
        result="She checked each pair before searching somewhere else.",
    )


def open_drawer(world: World) -> None:
    world.entities["hero"].beliefs["clue"] = "the shallow drawer may hold the spoon"
    world.narrate(
        "search",
        "Pip opened the shallow drawer and listened to its tiny wooden creak.",
        question="Why did Pip open the shallow drawer?",
        cause="A narrow silver shape might be inside it.",
        result="The drawer became the next careful place to search.",
    )


def find_spoon(world: World) -> None:
    if "clue" not in world.entities["hero"].beliefs:
        raise StoryError("They must choose a search place before finding the spoon.")
    world.entities["spoon"].meters["found"] = 1.0
    world.entities["spoon"].location = "dining table"
    world.entities["quest"].meters["solved"] = 1.0
    world.narrate("quest_action", "A silver glint appeared, and they set the little spoon beside the plate.")


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    h, p = params.hero, params.helper
    item, _ = TREASURES[params.treasure]
    world.narrate(
        "beginning",
        f"{h} entered the dining room carrying {item}. {p} was arranging napkins, "
        f"but something about the little celebration was not ready."
    )
    world.say("hero", "The room feels as if it is waiting for us.", listener="helper")
    world.say("helper", "Then we have a quest. What should we fix first?", listener="hero")
    world.think("I want this surprise to feel just right, but I must decide, darling.")
    world.say("hero", "I will look closely before I choose.", listener="helper")

    actions = PATHS[(params.problem, params.solution)]["actions"]
    if params.problem == "empty_place":
        if params.approach == "wonder":
            world.say("helper", "Would you place the plate where the light can find it?", listener="hero")
            world.think("The window or the center? I need a reason, not a guess.")
        else:
            world.say("helper", "Notice which place will welcome every eye.", listener="hero")
        if params.solution == "window":
            inspect_window(world)
            world.say("hero", "The window table has the gentle light.", listener="helper")
            world.say("helper", "Then let us carry the surprise there.", listener="hero")
            carry_plate(world, "the window table")
        else:
            clear_center(world)
            world.say("hero", "The center lets everyone share the first look.", listener="helper")
            world.say("helper", "That sounds like a kind welcome.", listener="hero")
            carry_plate(world, "the center of the table")
    elif params.problem == "dim_room":
        if params.solution == "lamp":
            find_lamp(world)
            world.say("hero", "The lamp has a safe hook. May we use it?", listener="helper")
            world.say("helper", "Yes. Warm light is better than a hurried light.", listener="hero")
            light_lamp(world)
        else:
            open_curtains(world)
            world.say("hero", "The curtains were hiding the day.", listener="helper")
            world.say("helper", "Open them, and let the room wake gently.", listener="hero")
            light_lamp(world)
    elif params.problem == "wobbly_table":
        if params.solution == "folded_cloth":
            find_cloth(world)
            world.say("hero", "This cloth can make the table steady.", listener="helper")
            world.say("helper", "Try it softly. We need no noisy rescue.", listener="hero")
            steady_table(world, "folded_cloth")
        else:
            inspect_leg(world)
            world.say("hero", "The short leg is the trouble.", listener="helper")
            world.say("helper", "Then support that leg, darling.", listener="hero")
            steady_table(world, "short_leg")
    else:
        if params.solution == "napkin":
            search_napkins(world)
            world.say("hero", "No spoon here yet. I will check the folds once more.", listener="helper")
            world.say("helper", "Good quests reward patient fingers.", listener="hero")
            find_spoon(world)
        else:
            open_drawer(world)
            world.say("hero", "Listen! Something silver is waiting.", listener="helper")
            world.say("helper", "Open it slowly.", listener="hero")
            find_spoon(world)

    world.say("hero", "Will the surprise be ready in time?", listener="helper")
    world.say("helper", "It is ready because you looked, listened, and decided.", listener="hero")
    world.narrate(
        "ending",
        f"The dining room glowed with care. {item.capitalize()} rested safely, "
        f"and {h} smiled as the first footsteps approached the door.",
        question="How did the quest end?",
        cause="They followed the clue for the chosen solution and completed the needed action.",
        result="The dining room became ready for a warm shared moment.",
    )
    sample = world.sample()
    check_sample(sample)
    return sample


def check_sample(sample: StorySample) -> None:
    world = sample.world
    if world.entities["quest"].meters["solved"] != 1.0:
        raise StoryError("The quest must reach a solved state.")
    speech = [e for e in world.history if e.kind == "speech"]
    if not any(e.speaker == "hero" for e in speech) or not any(e.speaker == "helper" for e in speech):
        raise StoryError("Both characters must speak.")
    if not any(e.kind == "inner_monologue" for e in world.history):
        raise StoryError("The story needs an inner monologue.")
    if len(sample.story_qa) < 2:
        raise StoryError("The story needs grounded question-and-answer pairs.")
    if any("{" in e.text or "}" in e.text for e in world.history):
        raise StoryError("Unresolved template text found.")


ASP_RULES = """
compatible(P,S) :- problem(P,Need), solution(S,Need).
#show compatible/2.
"""


def asp_facts() -> str:
    from asp import fact
    return "\n".join(
        [fact("problem", key, value) for key, value in PROBLEMS.items()]
        + [fact("solution", key, value) for key, value in SOLUTIONS.items()]
    )


def asp_combos() -> set[tuple[str, str]]:
    from asp import atoms, one_model
    return set(atoms(one_model(asp_facts() + "\n" + ASP_RULES), "compatible"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--hero")
    parser.add_argument("--helper")
    parser.add_argument("--problem", choices=tuple(PROBLEMS))
    parser.add_argument("--solution", choices=tuple(SOLUTIONS))
    parser.add_argument("--approach", choices=APPROACHES)
    parser.add_argument("--treasure", choices=tuple(TREASURES))
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
        raise StoryError("No compatible problem and solution choices remain.")
    problem, solution = rng.choice(choices)
    hero = args.hero or rng.choice(NAMES)
    helper = args.helper or rng.choice([n for n in NAMES if n != hero])
    return StoryParams(
        hero=hero,
        helper=helper,
        problem=problem,
        solution=solution,
        approach=args.approach or rng.choice(APPROACHES),
        treasure=args.treasure or rng.choice(tuple(TREASURES)),
        seed=args.seed,
    )


def verify() -> None:
    if asp_combos() != set(valid_combos()):
        raise StoryError("ASP and Python compatible paths disagree.")
    count = 0
    for problem, solution in valid_combos():
        for approach in APPROACHES:
            for treasure in TREASURES:
                generate(StoryParams(problem=problem, solution=solution,
                                     approach=approach, treasure=treasure))
                count += 1
    print(f"OK: {count} executable stories across {len(valid_combos())} paths.")


def emit(sample: StorySample, *, trace: bool, qa: bool, header: str = "") -> None:
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
            choices = [
                (problem, solution, approach)
                for problem, solution in valid_combos()
                for approach in APPROACHES
                if args.problem is None or problem == args.problem
                if args.solution is None or solution == args.solution
                if args.approach is None or approach == args.approach
            ]
            if not choices:
                raise StoryError("No compatible combinations match these options.")
            params_list = [
                StoryParams(
                    hero=args.hero or rng.choice(NAMES),
                    helper=args.helper or rng.choice([n for n in NAMES if n != (args.hero or "")]),
                    problem=problem,
                    solution=solution,
                    approach=approach,
                    treasure=args.treasure or rng.choice(tuple(TREASURES)),
                    seed=args.seed,
                )
                for problem, solution, approach in choices
            ]
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
