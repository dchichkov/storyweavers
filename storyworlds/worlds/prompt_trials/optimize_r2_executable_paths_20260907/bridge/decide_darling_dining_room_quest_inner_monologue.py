#!/usr/bin/env python3
"""A heartwarming dining-room quest about deciding together.

Darling's small supper quest becomes a suspenseful search when the serving spoon
vanishes. Inner thoughts matter, but spoken questions and answers change the
plan, reveal clues, and bring the table together.
"""

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
    hero: str = "Mara"
    darling: str = "June"
    problem: str = "missing_spoon"
    solution: str = "follow_sound"
    approach: str = "listen"
    dish: str = "stew"
    seed: int = 777


NAMES = ("Mara", "June", "Nell", "Owen", "Tessa", "Cal")
DISHES = {
    "stew": "warm vegetable stew",
    "pudding": "golden rice pudding",
    "soup": "tomato soup",
}
APPROACHES = ("listen", "rush")
PROBLEMS = {
    "missing_spoon": ("follow_sound", "The serving spoon is missing from the dining table."),
    "dark_corner": ("carry_lantern", "A shadowy corner hides the basket of bread."),
    "wobbly_table": ("steady_leg", "One table leg trembles when the plates are set down."),
}
SOLUTIONS = {
    "follow_sound": "follow_sound",
    "look_under": "look_under",
    "carry_lantern": "carry_lantern",
    "move_candle": "move_candle",
    "steady_leg": "steady_leg",
    "add_book": "add_book",
}

PROMPT = (
    "Write a heartwarming, dialogue-rich children's story set in a dining room, "
    "where a darling quest uses suspense, an inner monologue, and a careful decision."
)


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities = {
            "hero": Entity(
                "hero",
                params.hero,
                "character",
                "dining_room",
                memes={"hope": 0.7, "worry": 0.3, "trust": 0.5},
            ),
            "darling": Entity(
                "darling",
                params.darling,
                "character",
                "dining_room",
                memes={"hope": 0.7, "worry": 0.4, "trust": 0.5},
            ),
            "table": Entity(
                "table",
                "the dining table",
                "furniture",
                "dining_room",
                meters={"steady": 1, "plates": 0},
            ),
            "spoon": Entity(
                "spoon",
                "the silver serving spoon",
                "utensil",
                "unknown",
                meters={"found": 0},
            ),
            "basket": Entity(
                "basket",
                "the bread basket",
                "food",
                "unknown",
                meters={"found": 0},
            ),
            "lantern": Entity(
                "lantern",
                "the little lantern",
                "light",
                "sideboard",
                meters={"lit": 0},
            ),
            "meal": Entity(
                "meal",
                f"the bowl of {DISHES[params.dish]}",
                "food",
                "kitchen",
                meters={"ready": 1, "served": 0},
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

    def say(self, speaker: str, text: str, *, listener: str = "") -> None:
        actor = self.entities[speaker]
        verb = "asked" if text.rstrip().endswith("?") else "said"
        self.history.append(
            Event(
                kind="speech",
                text=f'"{text}" {actor.label} {verb}.',
                speaker=speaker,
                listener=listener,
                state=self.snapshot(),
            )
        )

    def think(self, speaker: str, text: str) -> None:
        actor = self.entities[speaker]
        self.history.append(
            Event(
                kind="inner_monologue",
                text=f"{actor.label} thought, {text}",
                speaker=speaker,
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
                    question=event.question,
                    answer=f"{event.cause} {event.result}",
                )
                for event in self.history
                if event.question
            ],
            world_qa=[
                QAItem(
                    question="Where did the quest take place?",
                    answer="The quest took place in the dining room.",
                ),
                QAItem(
                    question="What made the quest suspenseful?",
                    answer="The family had to discover the hidden problem before the meal could be served.",
                ),
            ],
            world=self,
        )


def valid_combos() -> list[tuple[str, str]]:
    return [
        (problem, solution)
        for problem, (needed, _) in PROBLEMS.items()
        for solution, capability in SOLUTIONS.items()
        if needed == capability
    ]


def validate_params(params: StoryParams) -> None:
    if (params.problem, params.solution) not in valid_combos():
        raise StoryError(
            f"{params.solution!r} cannot solve {params.problem!r}; choose a compatible solution."
        )
    if params.approach not in APPROACHES:
        raise StoryError("Choose either the careful listening approach or the rushing approach.")
    if params.dish not in DISHES:
        raise StoryError("Unknown supper dish.")
    if params.hero == params.darling:
        raise StoryError("The two dining-room helpers need different names.")
    if any(not re.fullmatch(r"[A-Z][a-z]+", name) for name in (params.hero, params.darling)):
        raise StoryError("Use simple capitalized names, such as Mara and June.")


def build_world(params: StoryParams) -> World:
    validate_params(params)
    world = World(params)
    if params.problem == "missing_spoon":
        world.entities["spoon"].location = "under_chair"
    elif params.problem == "dark_corner":
        world.entities["basket"].location = "curtain_corner"
    else:
        world.entities["table"].meters["steady"] = 0
        world.entities["table"].location = "dining_room"
    return world


def solve_quest(world: World) -> None:
    params = world.params
    hero = world.entities["hero"]
    darling = world.entities["darling"]
    table = world.entities["table"]

    if hero.beliefs.get("problem") != params.problem:
        raise StoryError("The helpers must understand the observed problem before solving it.")

    if params.problem == "missing_spoon":
        spoon = world.entities["spoon"]
        if params.solution == "follow_sound":
            if spoon.location != "under_chair":
                raise StoryError("The spoon's clink must lead to its actual hiding place.")
            spoon.location = "under_chair"
            spoon.meters["found"] = 1
            hero.beliefs["spoon_found"] = "The spoon is under the chair."
        elif params.solution == "look_under":
            raise StoryError("This path is not registered for the missing spoon quest.")
        else:
            raise StoryError("The chosen solution does not address the missing spoon.")
    elif params.problem == "dark_corner":
        lantern = world.entities["lantern"]
        basket = world.entities["basket"]
        if params.solution == "carry_lantern":
            lantern.meters["lit"] = 1
            basket.location = "curtain_corner"
            basket.meters["found"] = 1
            hero.beliefs["basket_found"] = "The bread basket is beside the curtain."
        elif params.solution == "move_candle":
            raise StoryError("This quest needs the lantern's wider light.")
        else:
            raise StoryError("The chosen solution does not address the dark corner.")
    elif params.problem == "wobbly_table":
        if params.solution == "steady_leg":
            table.meters["steady"] = 1
            table.meters["book"] = 0
        elif params.solution == "add_book":
            table.meters["steady"] = 1
            table.meters["book"] = 1
        else:
            raise StoryError("The chosen solution does not steady the table.")

    hero.memes["worry"] = 0.0
    darling.memes["worry"] = 0.0
    hero.memes["trust"] = 1.0
    darling.memes["trust"] = 1.0


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    h = world.entities["hero"].label
    d = world.entities["darling"].label
    dish = DISHES[params.dish]

    world.narrate(
        "opening",
        f"In the dining room, {h} carried a bowl of {dish} toward the table. "
        f"{d} had folded the napkins into little boats, and the whole supper waited for one last touch.",
    )
    world.say("hero", f"{d}, darling, may I decide where the bowl goes?", listener="darling")
    world.say(
        "darling",
        "Decide with me. The table has a mystery before it has a meal.",
        listener="hero",
    )
    world.think(
        "hero",
        "I wanted everything to look ready, but a good quest began with noticing what was not right.",
    )

    if params.problem == "missing_spoon":
        world.narrate(
            "problem",
            "The silver serving spoon was nowhere beside the bowl. A tiny clink came from the dark space near the chairs.",
            question="What first problem interrupted supper?",
            cause="The serving spoon was missing from the dining table.",
            result="The helpers paused before serving the warm food.",
        )
        world.entities["darling"].beliefs["problem"] = "missing_spoon"
        world.say("darling", "Did you hear that, or did the quiet make a wish?")
        if params.approach == "rush":
            world.say("hero", "I will grab every spoon in the kitchen.")
            world.narrate(
                "rush",
                f"{h} hurried toward the kitchen, but {d} caught the bowl before it tipped.",
            )
            world.say("darling", "Wait. A loud search may hide a soft clue.")
            world.say("hero", "You are right. Let us listen before we decide.")
        else:
            world.say("hero", "I heard a clink. Should we follow it?")
            world.say("darling", "Yes, but slowly, so the chairs do not make their own thunder.")
        world.think("hero", "Please be somewhere close, little spoon.")
        world.narrate(
            "clue",
            f"They stood still. Another bright clink rang beneath the nearest chair, and {h} noticed a small silver gleam.",
            question="What clue changed their plan?",
            cause="A second clink and a silver gleam came from beneath a chair.",
            result="They decided to follow the sound instead of searching wildly.",
        )
        world.entities["hero"].beliefs["problem"] = "missing_spoon"
        world.say("hero", "There you are, hiding under the chair.")
        world.say("darling", "Can you reach it without bumping the table?")
        solve_quest(world)
        world.narrate(
            "repair",
            f"{h} knelt and drew out the serving spoon. {d} polished its handle with a napkin and placed it beside the bowl.",
            question="How did the helpers recover the missing spoon?",
            cause="They followed the spoon's sound and looked beneath the chair.",
            result="They retrieved it gently without disturbing the supper table.",
        )
    elif params.problem == "dark_corner":
        world.narrate(
            "problem",
            "The bread basket was missing from the table. The corner beside the curtain held a deep, uncertain shadow.",
            question="What first problem interrupted supper?",
            cause="The bread basket was hidden in a dark corner of the dining room.",
            result="The helpers needed light before reaching into the shadow.",
        )
        world.entities["darling"].beliefs["problem"] = "dark_corner"
        world.say("darling", "I think the basket is near the curtain, but I cannot see its handle.")
        if params.approach == "rush":
            world.say("hero", "I will dash over and pull it out.")
            world.narrate("rush", f"{h} took one quick step toward the shadow.")
            world.say("darling", "Stop, darling. A brave quest still needs careful feet.")
            world.say("hero", "Then we will bring the light first.")
        else:
            world.say("hero", "Should we reach into the dark?")
            world.say("darling", "No. Let us carry the lantern so the corner can tell us the truth.")
        world.think("hero", "The shadow felt large, but a little light might make it small.")
        world.narrate(
            "clue",
            f"A pale stripe under the curtain showed where the lantern's glow could reach.",
            question="What clue changed their plan?",
            cause="The curtain's pale stripe showed that the corner was close enough to light safely.",
            result="They chose to carry the lantern before touching the hidden basket.",
        )
        world.entities["hero"].beliefs["problem"] = "dark_corner"
        world.say("hero", "I will carry the lantern. You can watch the path.")
        world.say("darling", "And I will tell you when I see the basket.")
        solve_quest(world)
        world.narrate(
            "repair",
            f"{h} lit the little lantern. Its warm circle reached the curtain, where {d} found the bread basket resting safely beside the wall.",
            question="How did the helpers find the bread basket?",
            cause="They carried a lit lantern toward the curtain corner.",
            result="The light revealed the basket without anyone stumbling into the shadow.",
        )
    else:
        world.narrate(
            "problem",
            "When {0} set down two plates, one table leg trembled. The spoons gave a nervous little rattle.".format(h),
            question="What first problem interrupted supper?",
            cause="One leg of the dining table wobbled when plates were placed on it.",
            result="The helpers had to make the table safe before serving the meal.",
        )
        world.entities["darling"].beliefs["problem"] = "wobbly_table"
        world.say("darling", "The table is dancing, but I do not think it knows the steps.")
        if params.approach == "rush":
            world.say("hero", "I can hold it while we eat.")
            world.narrate("rush", f"{h} pressed one hand against the table.")
            world.say("darling", "That would leave you holding supper all evening.")
            world.say("hero", "Then we need a lasting choice, not a brave pose.")
        else:
            world.say("hero", "Should I hold the table while you bring the plates?")
            world.say("darling", "No. Let us find what is missing beneath the leg.")
        world.think("hero", "A tiny uneven place could make the whole table uncertain.")
        world.narrate(
            "clue",
            "A folded book on the sideboard was just the right thickness to steady the uneven leg.",
            question="What clue changed their plan?",
            cause="The helpers noticed that the table leg needed a small, firm support.",
            result="They decided to use a suitable book instead of holding the table by hand.",
        )
        world.entities["hero"].beliefs["problem"] = "wobbly_table"
        world.say("hero", "May we use the blue book under the leg?")
        world.say("darling", "Yes. It is strong enough, and we can return it after supper.")
        solve_quest(world)
        world.narrate(
            "repair",
            f"{h} slid the blue book beneath the leg while {d} watched the tabletop. The rattling stopped, and the plates sat calmly.",
            question="How did the helpers steady the table?",
            cause="They found a firm book that matched the uneven space under the leg.",
            result="They slid it beneath the leg, making the table steady enough for supper.",
        )

    world.entities["table"].meters["plates"] = 2
    world.entities["meal"].meters["served"] = 1
    world.say("darling", "Now we can serve the meal. You listened before you decided.")
    world.say("hero", "And you made the suspense feel less scary, darling.")
    world.narrate(
        "ending",
        f"Together they carried the {dish} to the steady table. "
        f"The lantern glowed, the napkin boats waited, and the recovered supper things shone in the warm dining-room light.",
        question="What proved that their quest was complete?",
        cause="The missing dining-room problem had been solved and the meal was ready.",
        result=f"They served the {dish} together at a safe, welcoming table.",
    )
    check_sample(world.sample())
    return world.sample()


ASP_RULES = """
compatible(P,S) :- problem(P,N), solution(S,N).
#show compatible/2.
"""


def asp_facts() -> str:
    from asp import fact

    facts = [
        fact("problem", problem, needed)
        for problem, (needed, _) in PROBLEMS.items()
    ]
    facts += [
        fact("solution", solution, capability)
        for solution, capability in SOLUTIONS.items()
    ]
    return "\n".join(facts)


def asp_combos() -> set[tuple[str, str]]:
    from asp import atoms, one_model

    return set(atoms(one_model(asp_facts() + "\n" + ASP_RULES), "compatible"))


def check_sample(sample: StorySample) -> None:
    world = sample.world
    params = sample.params
    table = world.entities["table"]
    meal = world.entities["meal"]
    if meal.meters["served"] != 1:
        raise StoryError("The meal must be served at the end.")
    if params.problem == "missing_spoon" and world.entities["spoon"].meters["found"] != 1:
        raise StoryError("The missing spoon must really be recovered.")
    if params.problem == "dark_corner" and world.entities["basket"].meters["found"] != 1:
        raise StoryError("The bread basket must really be found.")
    if params.problem == "wobbly_table" and table.meters["steady"] != 1:
        raise StoryError("The table must really become steady.")
    speech = [event for event in world.history if event.kind == "speech"]
    if not any(event.speaker == "hero" and event.listener == "darling" for event in speech):
        raise StoryError("The story needs a spoken exchange between both helpers.")
    if not any(event.speaker == "darling" and event.listener == "hero" for event in speech):
        raise StoryError("The story needs a spoken exchange between both helpers.")
    if not any(event.kind == "inner_monologue" for event in world.history):
        raise StoryError("The story needs an inner monologue.")
    if len(sample.story_qa) < 3:
        raise StoryError("The story needs grounded questions and answers.")
    if any(token in sample.story for token in ("{", "}", "None")):
        raise StoryError("The story contains an unresolved template.")
    if any(world.entities[key].memes["trust"] < 1 for key in ("hero", "darling")):
        raise StoryError("The helpers must finish with trust.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--hero")
    parser.add_argument("--darling")
    parser.add_argument("--problem", choices=tuple(PROBLEMS))
    parser.add_argument("--solution", choices=tuple(SOLUTIONS))
    parser.add_argument("--approach", choices=APPROACHES)
    parser.add_argument("--dish", choices=tuple(DISHES))
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
        raise StoryError("That solution does not address the selected problem.")
    problem, solution = rng.choice(candidates)
    hero = args.hero or rng.choice([name for name in NAMES if name != args.darling])
    darling = args.darling or rng.choice([name for name in NAMES if name != hero])
    params = StoryParams(
        hero=hero,
        darling=darling,
        problem=problem,
        solution=solution,
        approach=args.approach or rng.choice(APPROACHES),
        dish=args.dish or rng.choice(tuple(DISHES)),
        seed=args.seed,
    )
    validate_params(params)
    return params


def verify() -> None:
    if set(valid_combos()) != asp_combos():
        raise StoryError("Python and ASP disagree on compatible paths.")
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
    print(f"OK: {tested} story states; {len(valid_combos())} Python/ASP-compatible paths.")


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
                values = vars(args).copy()
                values.update(problem=problem, solution=solution, approach=approach)
                params_list.append(resolve_params(argparse.Namespace(**values), rng))
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
