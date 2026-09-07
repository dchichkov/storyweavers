#!/usr/bin/env python3
"""A heartwarming dining-room quest about deciding what a darling keepsake needs."""

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
    state: dict = field(default_factory=dict)
    question: str = ""
    cause: str = ""
    result: str = ""


@dataclass
class StoryParams:
    hero: str = "Nora"
    companion: str = "Eli"
    problem: str = "spilled"
    solution: str = "blot"
    approach: str = "inspect"
    treasure: str = "recipe"
    mood: str = "tender"
    seed: int = 777


NAMES = ("Nora", "Eli", "Maya", "Owen", "Lena", "Theo")
TREASURES = {
    "recipe": "Grandma's handwritten recipe card",
    "photo": "a faded family photograph",
    "napkin": "a napkin embroidered with a little star",
}
PROBLEMS = {
    "spilled": "liquid has reached the keepsake",
    "hidden": "the keepsake is hidden beneath a serving cloth",
    "wobbly": "the keepsake rests on an unsteady table edge",
    "fading": "the keepsake is losing its readable mark",
}
SOLUTIONS = {
    "blot": "absorb the spill with a clean cloth",
    "lift": "lift the cloth and search gently",
    "steady": "move the keepsake to a safe place",
    "shade": "shade it from the bright window",
}
COMPATIBLE = {
    "spilled": {"blot"},
    "hidden": {"lift"},
    "wobbly": {"steady"},
    "fading": {"shade"},
}
APPROACHES = ("inspect", "rush")
MOODS = ("tender", "hopeful", "quiet")
PROMPT = (
    "Write a heartwarming children's story set in a dining room, where a child "
    "must decide how to protect a darling family keepsake during a suspenseful quest."
)


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities: dict[str, Entity] = {
            "hero": Entity("hero", params.hero, "character", "dining_room",
                           memes={"care": 0.5, "worry": 0.3}),
            "companion": Entity("companion", params.companion, "character", "dining_room",
                                memes={"care": 0.5, "trust": 0.5}),
            "table": Entity("table", "the dining table", "furniture", "dining_room",
                            meters={"stability": 1.0, "edge_distance": 0.3}),
            "window": Entity("window", "the sunny window", "place", "dining_room",
                             meters={"brightness": 1.0}),
            "keepsake": Entity("keepsake", TREASURES[params.treasure], "keepsake",
                               "dining_table", meters={"safe": 0, "readable": 1}),
            "cloth": Entity("cloth", "the blue serving cloth", "object", "dining_table",
                            meters={"dryness": 1.0, "cleanliness": 1.0}),
        }
        self.history: list[Event] = []

    def snapshot(self) -> dict:
        return {key: asdict(value) for key, value in self.entities.items()}

    def narrate(self, kind: str, text: str, *, question: str = "",
                cause: str = "", result: str = ""):
        self.history.append(Event(kind, text, state=self.snapshot(),
                                  question=question, cause=cause, result=result))

    def say(self, speaker: str, text: str, *, listener: str = ""):
        if not text.endswith((".", "?", "!")):
            text += "."
        verb = "asked" if text.endswith("?") else "said"
        self.history.append(Event("speech", f'"{text}" {self.entities[speaker].label} {verb}.',
                                  speaker=speaker, listener=listener,
                                  state=self.snapshot()))

    def complete(self):
        self.entities["hero"].memes["worry"] = 0.0
        self.entities["hero"].memes["care"] = 1.0
        self.entities["companion"].memes["trust"] = 1.0


def validate_params(params: StoryParams):
    if params.problem not in PROBLEMS:
        raise StoryError("Unknown dining-room problem.")
    if params.solution not in SOLUTIONS or params.solution not in COMPATIBLE[params.problem]:
        raise StoryError(f"{params.solution!r} cannot solve {params.problem!r}.")
    if params.approach not in APPROACHES or params.treasure not in TREASURES:
        raise StoryError("Unknown approach or keepsake.")
    if params.mood not in MOODS:
        raise StoryError("Unknown mood.")
    if params.hero == params.companion:
        raise StoryError("The quest needs two different speakers.")
    for name in (params.hero, params.companion):
        if not re.fullmatch(r"[A-Z][a-z]+", name):
            raise StoryError("Names must be simple capitalized words.")


def build_world(params: StoryParams) -> World:
    validate_params(params)
    world = World(params)
    if params.problem == "spilled":
        world.entities["cloth"].meters["dryness"] = 1.0
        world.entities["keepsake"].meters["safe"] = 0
    elif params.problem == "hidden":
        world.entities["keepsake"].location = "under_cloth"
        world.entities["keepsake"].meters["safe"] = 0
    elif params.problem == "wobbly":
        world.entities["table"].meters.update(stability=0.2, edge_distance=0.1)
    else:
        world.entities["keepsake"].meters["readable"] = 0.5
    return world


def solve(world: World):
    p = world.params
    keepsake = world.entities["keepsake"]
    table = world.entities["table"]
    cloth = world.entities["cloth"]
    if p.solution == "blot":
        if cloth.meters["cleanliness"] < 1:
            raise StoryError("The cloth is not clean enough to protect the keepsake.")
        cloth.meters["dryness"] = 0.0
        keepsake.meters["safe"] = 1
        keepsake.location = "dry_center"
    elif p.solution == "lift":
        keepsake.location = "hero_hands"
        keepsake.meters["safe"] = 1
        table.meters["edge_distance"] = 0.8
        keepsake.location = "dry_center"
    elif p.solution == "steady":
        table.meters["stability"] = 1.0
        table.meters["edge_distance"] = 0.8
        keepsake.meters["safe"] = 1
        keepsake.location = "steady_center"
    elif p.solution == "shade":
        world.entities["window"].meters["brightness"] = 0.2
        keepsake.meters["readable"] = 1
        keepsake.meters["safe"] = 1
        keepsake.location = "shaded_center"


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    h, c = params.hero, params.companion
    treasure = TREASURES[params.treasure]
    world.narrate(
        "beginning",
        f"In the dining room, {h} found {treasure} beside the family plates. "
        f"It was a darling treasure, and tonight {h} had a small quest: decide where it would be safest before dinner.",
    )
    world.say("hero", "I want to carry it to the table, but my hands feel jumpy.", listener="companion")
    world.say("companion", f"Then we can pause, {h}. A darling thing deserves a careful plan.", listener="hero")
    world.narrate(
        "inner_monologue",
        f"{h} took one quiet breath. Inside, {h} thought, "
        f'"If I rush, I might make the danger worse. If I look closely, the next step may show itself."',
    )

    if params.approach == "rush":
        world.say("hero", "I can fix it quickly!", listener="companion")
        world.narrate(
            "suspense",
            f"{h} reached toward the keepsake, but a chair scraped near the table. "
            f"The {treasure.lower()} slid a finger-width closer to trouble.",
        )
        world.say("companion", "Stop! We still have time to look.", listener="hero")
        world.say("hero", "You are right. I nearly guessed instead of noticing.", listener="companion")
    else:
        world.say("hero", "What is the first clue?", listener="companion")
        world.say("companion", "Look at the keepsake, the table, the cloth, and the window.", listener="hero")
        world.narrate(
            "inspection",
            f"They leaned close without touching. The dining room grew very quiet while {h} noticed that "
            f"{PROBLEMS[params.problem]}.",
            question="What did the children do before choosing a solution?",
            cause=f"They examined the keepsake and the nearby dining-room objects.",
            result=f"They discovered that {PROBLEMS[params.problem]}.",
        )

    clues = {
        "spilled": "A little juice had crept toward the paper.",
        "hidden": "The blue cloth made a mysterious lump over the treasure.",
        "wobbly": "The table trembled whenever someone brushed its edge.",
        "fading": "Sunlight was bleaching the small written mark.",
    }
    world.narrate(
        "discovery",
        clues[params.problem],
        question="What danger threatened the keepsake?",
        cause=f"The children observed that {PROBLEMS[params.problem]}.",
        result=clues[params.problem],
    )

    dialogue = {
        "spilled": (
            "The juice is moving toward it.",
            "Then do not wipe across the paper. Blot from the outside inward.",
            "I will hold the dry corner while you press gently.",
        ),
        "hidden": (
            "The treasure is under the cloth, but I cannot see its edge.",
            "Lift one corner slowly. We should not drag it across the table.",
            "I will make a little space in the center before we uncover it.",
        ),
        "wobbly": (
            "The table shakes whenever the chair touches it.",
            "Move the keepsake first, then steady the table.",
            "I will hold the plate while you slide the treasure away from the edge.",
        ),
        "fading": (
            "The bright window is washing out the mark.",
            "Let us carry it into shade, not rub the mark to make it darker.",
            "I will close the curtain while you move it with both hands.",
        ),
    }[params.problem]
    world.say("companion", dialogue[0], listener="hero")
    world.say("hero", dialogue[1], listener="companion")
    world.say("companion", dialogue[2], listener="hero")
    world.say("hero", "I understand now. The clue tells us what not to do.", listener="companion")

    solve(world)
    action_text = {
        "blot": f"{h} pressed the clean cloth around the juice, one small blot at a time, while {c} kept the paper flat.",
        "lift": f"{h} lifted the cloth by its corner. {c} cleared the center of the table, and the hidden treasure appeared dry beneath it.",
        "steady": f"{c} held the table still while {h} moved the keepsake away from the edge. Then they placed a firm book beneath the wobbly leg.",
        "shade": f"{c} drew the curtain across the bright window while {h} carried the keepsake to a shaded place in the dining room.",
    }[params.solution]
    world.narrate(
        "turn",
        action_text,
        question="How did their chosen solution protect the keepsake?",
        cause=f"They matched their action to the observed danger: {PROBLEMS[params.problem]}.",
        result=action_text,
    )
    world.say("hero", "It is safe. I did not have to be fast; I had to decide well.", listener="companion")
    world.say("companion", "And you listened to the clue before you touched the treasure.", listener="hero")
    world.narrate(
        "ending",
        f"At last, {treasure.lower()} rested safely at the center of the dining table. "
        f"{h} and {c} set two warm plates beside it, and the little quest became part of their family story.",
        question="What changed by the end of the quest?",
        cause=f"{h} and {c} observed the danger, shared what they knew, and used the fitting repair.",
        result=f"The {treasure.lower()} rested safely in the dining room while dinner was prepared.",
    )
    world.complete()
    sample = StorySample(
        params=params,
        story="\n\n".join(event.text for event in world.history),
        prompts=[PROMPT],
        story_qa=[
            QAItem(event.question, f"{event.cause} {event.result}")
            for event in world.history if event.question
        ],
        world_qa=[
            QAItem("Where did the quest happen?", "It happened in a dining room."),
            QAItem("Why did the children inspect the danger?", "They wanted to choose a safe action instead of rushing."),
        ],
        world=world,
    )
    check_sample(sample)
    return sample


def check_sample(sample: StorySample):
    world = sample.world
    if not world.entities["keepsake"].meters["safe"]:
        raise StoryError("The keepsake was not made safe.")
    if world.entities["keepsake"].location not in {"dry_center", "steady_center", "shaded_center"}:
        raise StoryError("The final keepsake location is not a safe dining-room scene.")
    speech = [e for e in world.history if e.kind == "speech"]
    if len(speech) < 10 or not any(e.speaker == "hero" for e in speech) or not any(e.speaker == "companion" for e in speech):
        raise StoryError("The story needs a sustained exchange between both characters.")
    if not any(e.kind == "inner_monologue" for e in world.history):
        raise StoryError("The story needs an inner-monologue moment.")
    if len(sample.story_qa) < 3:
        raise StoryError("The story needs causal grounded questions and answers.")


ASP_RULES = """
valid(P,S) :- problem(P,S).
#show valid/2.
"""


def asp_facts() -> str:
    from asp import fact
    return "\n".join(
        fact("problem", problem, solution)
        for problem, solutions in COMPATIBLE.items()
        for solution in solutions
    )


def valid_combos() -> set[tuple[str, str]]:
    return {(problem, solution) for problem, solutions in COMPATIBLE.items() for solution in solutions}


def asp_combos() -> set[tuple[str, str]]:
    from asp import atoms, one_model
    return set(atoms(one_model(asp_facts() + "\n" + ASP_RULES), "valid"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--hero")
    parser.add_argument("--companion")
    parser.add_argument("--problem", choices=tuple(PROBLEMS))
    parser.add_argument("--solution", choices=tuple(SOLUTIONS))
    parser.add_argument("--approach", choices=APPROACHES)
    parser.add_argument("--treasure", choices=tuple(TREASURES))
    parser.add_argument("--mood", choices=MOODS)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    candidates = [
        combo for combo in sorted(valid_combos())
        if args.problem is None or combo[0] == args.problem
        if args.solution is None or combo[1] == args.solution
    ]
    if not candidates:
        raise StoryError("No compatible problem and solution were selected.")
    problem, solution = rng.choice(candidates)
    hero = args.hero or rng.choice(NAMES)
    companion = args.companion or rng.choice([name for name in NAMES if name != hero])
    params = StoryParams(
        hero=hero,
        companion=companion,
        problem=problem,
        solution=solution,
        approach=args.approach or rng.choice(APPROACHES),
        treasure=args.treasure or rng.choice(tuple(TREASURES)),
        mood=args.mood or rng.choice(MOODS),
        seed=args.seed,
    )
    validate_params(params)
    return params


def verify():
    if valid_combos() != asp_combos():
        raise StoryError("Python and ASP disagree about valid quest paths.")
    count = 0
    for problem, solution in sorted(valid_combos()):
        for approach in APPROACHES:
            for treasure in TREASURES:
                generate(StoryParams(problem=problem, solution=solution,
                                      approach=approach, treasure=treasure))
                count += 1
    print(f"OK: {count} story states; {len(valid_combos())} compatible quest paths.")


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = ""):
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
            selections = [
                (problem, solution, approach)
                for problem, solution in sorted(valid_combos())
                for approach in APPROACHES
                if args.problem is None or problem == args.problem
                if args.solution is None or solution == args.solution
                if args.approach is None or approach == args.approach
            ]
            if not selections:
                raise StoryError("No compatible quest paths match these options.")
            params_list = []
            for problem, solution, approach in selections:
                copied = argparse.Namespace(**vars(args))
                copied.problem = problem
                copied.solution = solution
                copied.approach = approach
                params_list.append(resolve_params(copied, rng))
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


if __name__ == "__main__":
    raise SystemExit(main())
