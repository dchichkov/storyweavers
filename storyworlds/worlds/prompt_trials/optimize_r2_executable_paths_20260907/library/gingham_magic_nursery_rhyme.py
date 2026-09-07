#!/usr/bin/env python3
"""Gingham Magic: a nursery-rhyme tale of a little cloth and a helpful spell."""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

_HERE = Path(__file__).resolve()
for parent in (_HERE.parent, *_HERE.parents):
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
    hero: str = "Pip"
    helper: str = "Mara"
    problem: str = "lost_star"
    solution: str = "ribbon_ladder"
    verse: str = "moon"
    seed: int = 777


@dataclass(frozen=True)
class Path:
    problem: str
    solution: str
    clue: str
    actions: tuple[str, ...]
    change: str
    ending: str


PROBLEMS = {
    "lost_star": "find a fallen star",
    "silent_bell": "wake a silent bell",
    "thirsty_garden": "water a thirsty garden",
    "cold_lantern": "warm a cold lantern",
}

SOLUTIONS = {
    "ribbon_ladder": "lost_star",
    "silver_thimble": "lost_star",
    "clap_rhyme": "silent_bell",
    "wind_song": "silent_bell",
    "dew_dance": "thirsty_garden",
    "gingham_cup": "thirsty_garden",
    "sunny_pocket": "cold_lantern",
    "candle_chant": "cold_lantern",
}

PATHS = {
    ("lost_star", "ribbon_ladder"): Path(
        "lost_star", "ribbon_ladder", "the star is beneath the blue gingham bench",
        ("lift_gingham", "tie_ribbon", "climb"),
        "the star is returned to the sky",
        "The star winked above the roof, bright as a button on the night.",
    ),
    ("lost_star", "silver_thimble"): Path(
        "lost_star", "silver_thimble", "the thimble can scoop moonlight from the well",
        ("find_thimble", "scoop_moonlight", "pour"),
        "the moonlight carries the star upward",
        "The star sailed home in a silver stream, and the well shone blue.",
    ),
    ("silent_bell", "clap_rhyme"): Path(
        "silent_bell", "clap_rhyme", "the bell wakes when a steady rhyme keeps time",
        ("tap_gingham", "clap_rhyme", "ring"),
        "the bell sings for the village",
        "The bell rang ding-dong, while gingham squares danced in the breeze.",
    ),
    ("silent_bell", "wind_song"): Path(
        "silent_bell", "wind_song", "the bell needs a breath from the north wind",
        ("open_gate", "sing_wind", "ring"),
        "the bell catches the wind",
        "The bell chimed softly, and the north wind twirled its blue ribbon.",
    ),
    ("thirsty_garden", "dew_dance"): Path(
        "thirsty_garden", "dew_dance", "the flowers open when dew is gathered at dawn",
        ("gather_dew", "dance_dew", "pour"),
        "the garden drinks the dawn",
        "The roses raised their heads, each wearing a bright drop like a crown.",
    ),
    ("thirsty_garden", "gingham_cup"): Path(
        "thirsty_garden", "gingham_cup", "the magic gingham cup fills beside the old stone",
        ("fold_cup", "say_charm", "pour"),
        "the gingham cup gives the garden water",
        "The garden glittered, and every gingham check held a tiny rainbow.",
    ),
    ("cold_lantern", "sunny_pocket"): Path(
        "cold_lantern", "sunny_pocket", "a pocket stitched with gingham can hold one sunbeam",
        ("open_pocket", "catch_beam", "light"),
        "the lantern glows with stored sunlight",
        "The lantern glowed like a small sunrise in the lane.",
    ),
    ("cold_lantern", "candle_chant"): Path(
        "cold_lantern", "candle_chant", "a candle answers a warm three-line chant",
        ("place_candle", "chant", "light"),
        "the lantern warms the dark lane",
        "The lantern shone gold, and sleepy windows opened one by one.",
    ),
}

NAMES = ("Pip", "Mara", "Tess", "Bram", "Nell", "Odo")
VERSES = {
    "moon": "Star above, star below, up the silver ladder go",
    "bell": "Ding and dong, keep time strong, wake the morning with a song",
    "garden": "Drop by drop, never stop, wake the flowers at the top",
    "lantern": "Warm and bright, chase the night, make a little golden light",
}
OPENINGS = (
    "By the gingham gate, where the small blue squares met the moonlit lane,",
    "Under a gingham awning, neat as a checkerboard crown,",
    "Beside a gingham basket, red and white and round,",
)
MIDDLES = (
    "The magic stirred with a tickle and a twirl.",
    "A silver spark hopped from square to square.",
    "The cloth gave a tiny shiver, as if it knew the rhyme.",
)


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities: dict[str, Entity] = {
            "hero": Entity("hero", params.hero, "character",
                           memes={"courage": 0.5, "hope": 0.5}),
            "helper": Entity("helper", params.helper, "character",
                             memes={"kindness": 0.7, "trust": 0.5}),
            "gingham": Entity("gingham", "the gingham cloth", "magic_cloth",
                              "gingham_gate", meters={"magic": 1, "folds": 0}),
            "goal": Entity("goal", "the village wonder", "goal",
                           "hidden", meters={"solved": 0}),
        }
        self.history: list[Event] = []

    def snapshot(self) -> dict:
        return {key: asdict(value) for key, value in self.entities.items()}

    def narrate(self, kind: str, text: str, *, question: str = "",
                cause: str = "", result: str = "") -> None:
        self.history.append(Event(kind, text, question, cause, result,
                                  state=self.snapshot()))

    def say(self, who: str, text: str, *, to: str = "") -> None:
        label = self.entities[who].label
        verb = "asked" if text.endswith("?") else "said"
        self.history.append(Event("speech", f'"{text}" {label} {verb}.',
                                  speaker=who, listener=to,
                                  state=self.snapshot()))

    def act(self, action: str) -> None:
        cloth = self.entities["gingham"]
        goal = self.entities["goal"]
        if action == "lift_gingham":
            cloth.location = "blue_bench"
            cloth.meters["folds"] += 1
        elif action == "tie_ribbon":
            cloth.meters["ribbon"] = 1
        elif action == "climb":
            if not cloth.meters.get("ribbon"):
                raise StoryError("The ribbon ladder must be tied before anyone climbs.")
            goal.location = "sky"
            goal.meters["solved"] = 1
        elif action == "find_thimble":
            self.entities["thimble"] = Entity("thimble", "the silver thimble",
                                              "tool", "well_stone",
                                              meters={"moonlight": 0})
        elif action == "scoop_moonlight":
            if "thimble" not in self.entities:
                raise StoryError("The silver thimble must be found first.")
            self.entities["thimble"].meters["moonlight"] = 1
        elif action == "pour":
            if self.params.problem == "lost_star":
                if not self.entities.get("thimble", Entity("", "", "").meters).meters.get("moonlight", 0) and not cloth.meters.get("dew"):
                    raise StoryError("A magical carrying method is needed before pouring.")
                goal.location = "sky"
                goal.meters["solved"] = 1
            else:
                if not cloth.meters.get("dew") and not cloth.meters.get("cup_water"):
                    raise StoryError("The garden needs gathered water before pouring.")
                goal.location = "garden"
                goal.meters["solved"] = 1
        elif action == "tap_gingham":
            cloth.meters["rhythm"] = 1
        elif action == "clap_rhyme":
            cloth.meters["rhythm"] = 1
        elif action == "ring":
            if not cloth.meters.get("rhythm") and self.params.solution != "wind_song":
                raise StoryError("The bell needs a steady rhythm before it can ring.")
            goal.meters["solved"] = 1
            goal.location = "bell_tower"
        elif action == "open_gate":
            cloth.meters["wind"] = 1
        elif action == "sing_wind":
            if not cloth.meters.get("wind"):
                raise StoryError("The gate must be opened before the wind song.")
            goal.meters["solved"] = 1
            goal.location = "bell_tower"
        elif action == "gather_dew":
            cloth.meters["dew"] = 1
        elif action == "dance_dew":
            if not cloth.meters.get("dew"):
                raise StoryError("Dew must be gathered before the dew dance.")
        elif action == "fold_cup":
            cloth.meters["folds"] += 1
            cloth.meters["cup_water"] = 1
        elif action == "say_charm":
            if not cloth.meters.get("cup_water"):
                raise StoryError("The gingham cup must be folded before its charm.")
        elif action == "open_pocket":
            cloth.meters["pocket"] = 1
        elif action == "catch_beam":
            if not cloth.meters.get("pocket"):
                raise StoryError("The sunny pocket must be opened first.")
            cloth.meters["sunbeam"] = 1
        elif action == "light":
            if not cloth.meters.get("sunbeam") and self.params.solution != "candle_chant":
                raise StoryError("The lantern needs a captured sunbeam.")
            goal.meters["solved"] = 1
            goal.location = "lantern_lane"
        elif action == "place_candle":
            cloth.meters["candle"] = 1
        elif action == "chant":
            if not cloth.meters.get("candle"):
                raise StoryError("The candle must be placed before the chant.")
            cloth.meters["warmth"] = 1
        else:
            raise StoryError(f"Unknown action: {action}")

    def sample(self) -> StorySample:
        return StorySample(
            params=self.params,
            story="\n\n".join(event.text for event in self.history),
            prompts=["Write a magical nursery rhyme about gingham helping two friends solve a village problem."],
            story_qa=[
                QAItem(event.question, f"{event.cause} {event.result}")
                for event in self.history if event.question
            ],
            world_qa=[
                QAItem("What made the gingham cloth special?",
                       "It carried a small magic that answered a careful rhyme and a kind plan.")
            ],
            world=self,
        )


def path_for(params: StoryParams) -> Path:
    try:
        return PATHS[(params.problem, params.solution)]
    except KeyError as exc:
        raise StoryError("That magical solution does not fit the chosen problem.") from exc


def validate_params(params: StoryParams) -> None:
    path_for(params)
    if params.hero == params.helper:
        raise StoryError("The two characters need different names.")
    if any(not re.fullmatch(r"[A-Z][a-z]+", name)
           for name in (params.hero, params.helper)):
        raise StoryError("Names must be simple capitalized words.")
    if params.verse not in VERSES:
        raise StoryError("Unknown nursery-rhyme verse.")


def build_world(params: StoryParams) -> World:
    validate_params(params)
    return World(params)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    path = path_for(params)
    hero = world.entities["hero"].label
    helper = world.entities["helper"].label
    opening = OPENINGS[params.seed % len(OPENINGS)]
    middle = MIDDLES[(params.seed // 3) % len(MIDDLES)]
    world.narrate(
        "opening",
        f"{opening} {hero} and {helper} found a village wonder in trouble. "
        f"{hero} held the gingham cloth, and its checks glimmered with Magic.",
        question="What problem did the friends discover?",
        cause=f"They found that {path.problem.replace('_', ' ')} needed help.",
        result=f"They decided to use the gingham cloth and the clue that {path.clue}.",
    )
    world.say("hero", f"What shall we do with this gingham, {helper}?")
    world.say("helper", f"Listen for its clue: {path.clue}.")
    world.say("hero", "Then we will try the kindest plan, one step at a time.")
    world.narrate("clue", f"{middle} The clue pointed toward {path.clue}.")
    for action in path.actions:
        world.act(action)
        if action == path.actions[0]:
            world.narrate("first_action",
                          f"{hero} began carefully, while {helper} watched the magic squares.")
        elif action == path.actions[-1]:
            world.narrate("turn",
                          f"{helper} spoke the rhyme, and {hero} followed through. "
                          f"The magic changed the trouble into a path home.",
                          question="How did the friends solve the problem?",
                          cause=f"They followed the clue by using {path.solution.replace('_', ' ')}.",
                          result=path.change + ".")
    world.say("helper", "Look! The magic worked because we listened and helped.")
    world.say("hero", "And the gingham kept every promise in its little squares.")
    world.narrate("ending", f"{path.ending} {VERSES[params.verse]}.",
                   question="What showed that their solution worked?",
                   cause=f"The final step of {path.solution.replace('_', ' ')} changed the village wonder.",
                   result=path.ending)
    check_sample(world.sample())
    return world.sample()


def check_sample(sample: StorySample) -> None:
    world = sample.world
    if world.entities["goal"].meters.get("solved") != 1:
        raise StoryError("The story must reach a solved state.")
    speech = [e for e in world.history if e.kind == "speech"]
    if not any(e.speaker == "hero" for e in speech) or not any(e.speaker == "helper" for e in speech):
        raise StoryError("Both characters need spoken dialogue.")
    if len(speech) < 5:
        raise StoryError("The story needs a real back-and-forth exchange.")
    if len(sample.story_qa) < 2:
        raise StoryError("Grounded QA is missing.")
    if "{" in sample.story or "}" in sample.story:
        raise StoryError("Unresolved template text leaked into the story.")


ASP_RULES = """
compatible(P,S) :- problem(P,_), solution(S,P).
#show compatible/2.
"""


def asp_facts() -> str:
    from asp import fact
    lines = []
    for problem, need in PROBLEMS.items():
        lines.append(fact("problem", problem, need))
    for solution, need in SOLUTIONS.items():
        lines.append(fact("solution", solution, need))
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str]]:
    return list(PATHS)


def asp_combos() -> set[tuple[str, str]]:
    from asp import atoms, one_model
    return set(atoms(one_model(asp_facts() + ASP_RULES), "compatible"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--hero")
    parser.add_argument("--helper")
    parser.add_argument("--problem", choices=tuple(PROBLEMS))
    parser.add_argument("--solution", choices=tuple(SOLUTIONS))
    parser.add_argument("--verse", choices=tuple(VERSES))
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    choices = [
        pair for pair in valid_combos()
        if args.problem is None or pair[0] == args.problem
    ]
    choices = [
        pair for pair in choices
        if args.solution is None or pair[1] == args.solution
    ]
    if not choices:
        raise StoryError("No compatible magical path matches those choices.")
    problem, solution = rng.choice(choices)
    hero = args.hero or rng.choice(NAMES)
    helper = args.helper or rng.choice(tuple(n for n in NAMES if n != hero))
    return StoryParams(hero=hero, helper=helper, problem=problem,
                       solution=solution, verse=args.verse or rng.choice(tuple(VERSES)),
                       seed=args.seed)


def verify() -> None:
    if set(valid_combos()) != asp_combos():
        raise StoryError("Python and ASP disagree about magical paths.")
    count = 0
    for problem, solution in valid_combos():
        for verse in VERSES:
            sample = generate(StoryParams(problem=problem, solution=solution,
                                           verse=verse, seed=count))
            check_sample(sample)
            count += 1
    print(f"OK: {count} executable stories; {len(valid_combos())} compatible paths.")


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
            pairs = [
                pair for pair in valid_combos()
                if args.problem is None or pair[0] == args.problem
            ]
            pairs = [
                pair for pair in pairs
                if args.solution is None or pair[1] == args.solution
            ]
            if not pairs:
                raise StoryError("No paths match the selected options.")
            params_list = [
                StoryParams(hero=args.hero or NAMES[i % len(NAMES)],
                            helper=args.helper or NAMES[(i + 1) % len(NAMES)],
                            problem=problem, solution=solution,
                            verse=args.verse or tuple(VERSES)[i % len(VERSES)],
                            seed=args.seed + i)
                for i, (problem, solution) in enumerate(pairs)
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
