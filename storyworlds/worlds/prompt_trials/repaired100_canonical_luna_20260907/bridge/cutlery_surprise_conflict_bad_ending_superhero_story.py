#!/usr/bin/env python3
"""Cutlery Surprise: a tiny superhero must solve a silverware conflict before dinner."""

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
    hero: str = "Luna"
    helper: str = "Pip"
    cutlery: str = "spoons"
    surprise: str = "magnet"
    conflict: str = "mixup"
    ending: str = "rescue"
    seed: int = 777


NAMES = ("Luna", "Pip", "Milo", "Zara", "Nia", "Theo")
CUTLERY = {
    "spoons": ("spoons", "spoon"),
    "forks": ("forks", "fork"),
    "knives": ("knives", "knife"),
}
SURPRISES = {
    "magnet": "a hidden magnet",
    "spring": "a jumping spring",
    "note": "a tiny secret note",
}
CONFLICTS = {
    "mixup": "the cutlery had been mixed into the wrong drawers",
    "stuck": "the cutlery drawer was stuck shut",
    "crash": "the cutlery tower was about to tumble",
}
ENDINGS = {
    "rescue": "rescue",
    "lesson": "lesson",
    "mess": "mess",
}

PROMPT = (
    "Write a child-facing superhero story in which Luna uses a brave but careful "
    "plan to solve a cutlery conflict, discovers a surprising object, and faces "
    "the consequences of a bad first ending."
)

ASP_RULES = """
usable_cutlery(C) :- cutlery(C).
valid_surprise(S) :- surprise(S).
valid_conflict(C) :- conflict(C).
story_state(C,S,F) :- cutlery(C), surprise(S), conflict(F).
#show story_state/3.
"""


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities = {
            "hero": Entity(
                "hero", params.hero, "character", "kitchen",
                memes={"courage": 1.0, "worry": 0.3, "trust": 0.5},
            ),
            "helper": Entity(
                "helper", params.helper, "character", "kitchen",
                memes={"courage": 0.5, "trust": 0.5},
            ),
            "drawer": Entity(
                "drawer", "the cutlery drawer", "container", "kitchen",
                meters={"stuck": 1, "open": 0},
            ),
            "cutlery": Entity(
                "cutlery", CUTLERY[params.cutlery][0], "cutlery", "drawer",
                meters={"sorted": 0, "safe": 0},
            ),
            "surprise": Entity(
                "surprise", SURPRISES[params.surprise], "mystery", "drawer",
                meters={"found": 0},
            ),
            "tower": Entity(
                "tower", "the cutlery tower", "stack", "table",
                meters={"height": 4, "stable": 0, "fallen": 0},
            ),
            "supper": Entity(
                "supper", "the supper table", "place", "kitchen",
                meters={"ready": 0},
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
        to: str = "",
        reveal: str = "",
    ):
        actor = self.entities[speaker]
        if reveal:
            if not to or reveal not in actor.beliefs:
                raise StoryError("A speaker cannot share a secret they do not know.")
            self.entities[to].beliefs[reveal] = actor.beliefs[reveal]
        tag = "asked" if text.endswith("?") else "said"
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
                    question=event.question,
                    answer=f"{event.cause} {event.result}",
                )
                for event in self.history
                if event.question
            ],
            world_qa=[
                QAItem(
                    question="What should a superhero do before grabbing dangerous cutlery?",
                    answer="A superhero should pause, ask for help, and make a careful plan before touching it.",
                )
            ],
            world=self,
        )


def valid_combos() -> list[tuple[str, str, str]]:
    return [
        (cutlery, surprise, conflict)
        for cutlery in CUTLERY
        for surprise in SURPRISES
        for conflict in CONFLICTS
    ]


def validate_params(params: StoryParams):
    if params.cutlery not in CUTLERY:
        raise StoryError("Choose a known kind of cutlery.")
    if params.surprise not in SURPRISES:
        raise StoryError("Choose a known surprise.")
    if params.conflict not in CONFLICTS:
        raise StoryError("Choose a known conflict.")
    if params.ending not in ENDINGS:
        raise StoryError("Choose a known ending.")
    if params.hero == params.helper:
        raise StoryError("The two speakers must have different names.")
    if any(
        not re.fullmatch(r"[A-Z][a-z]+", name)
        for name in (params.hero, params.helper)
    ):
        raise StoryError("Use simple capitalized names, such as Luna and Pip.")


def build_world(params: StoryParams) -> World:
    validate_params(params)
    return World(params)


def bad_attempt(world: World):
    drawer = world.entities["drawer"]
    tower = world.entities["tower"]
    drawer.meters["stuck"] = 1
    tower.meters["height"] = 5
    tower.meters["stable"] = 0
    tower.meters["fallen"] = 1
    world.entities["hero"].memes["worry"] += 0.8


def discover(world: World):
    drawer = world.entities["drawer"]
    surprise = world.entities["surprise"]
    drawer.meters["open"] = 1
    drawer.meters["stuck"] = 0
    surprise.meters["found"] = 1
    world.entities["hero"].beliefs["secret"] = world.params.surprise


def repair(world: World):
    drawer = world.entities["drawer"]
    cutlery = world.entities["cutlery"]
    tower = world.entities["tower"]
    drawer.meters.update(open=1, stuck=0)
    cutlery.meters.update(sorted=1, safe=1)
    tower.meters.update(height=3, stable=1, fallen=0)
    world.entities["helper"].beliefs["secret"] = world.params.surprise


def check_ending(world: World):
    if world.entities["tower"].meters["fallen"]:
        raise StoryError("The final cutlery tower must be safe.")
    if not world.entities["cutlery"].meters["sorted"]:
        raise StoryError("The cutlery must be sorted before supper.")
    if not world.entities["supper"].meters["ready"]:
        raise StoryError("The supper table must be ready at the ending.")


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    hero, helper = params.hero, params.helper
    kind_plural, kind_singular = CUTLERY[params.cutlery]
    surprise_text = SURPRISES[params.surprise]

    world.narrate(
        "beginning",
        f"{hero} wore a bright towel like a cape and called herself Captain Luna. "
        f"Before supper, she promised to arrange the {kind_plural} while {helper} carried cups to the table.",
    )
    world.say("hero", "I can save supper before anyone notices a thing!")
    world.say("helper", "A real superhero checks the danger first.")
    world.narrate(
        "conflict",
        f"The {CONFLICTS[params.conflict]}. "
        f"Forks, {kind_plural}, and serving spoons leaned together in a wobbly tower.",
        question="What problem stopped the children from setting the table?",
        cause=f"The {kind_plural} were unsafe because {CONFLICTS[params.conflict]}.",
        result="The children needed to slow down and make a careful plan.",
    )

    world.say("hero", "I will pull the drawer as hard as I can.")
    world.say("helper", "Wait. Harder is not always safer.")
    bad_attempt(world)
    world.narrate(
        "bad_ending",
        f"Luna tugged too quickly. The drawer stayed stuck, and the cutlery tower crashed with a loud clatter. "
        f"Nothing broke, but supper was no longer ready, and Luna's cape caught on a chair.",
        question="Why did Luna's first plan fail?",
        cause="She pulled the stuck drawer without checking the leaning cutlery tower.",
        result="The tower fell, so the kitchen became messier instead of safer.",
    )
    world.say("hero", "Oh no. My superhero ending was a terrible one.")
    world.say("helper", "Then let us give the story a better ending. What can we observe?")
    world.say("hero", "The drawer is stuck, and something shiny is hiding behind it.")
    discover(world)
    world.narrate(
        "surprise",
        f"Behind the drawer, Luna found {surprise_text}. It had been pressing against the runners and stopping the drawer.",
        question="What surprising thing did Luna find?",
        cause="The stuck drawer hid an unexpected object behind its runners.",
        result=f"She discovered {surprise_text}, which explained why the drawer would not open.",
    )
    world.say("helper", "Do you know what it is?")
    world.say("hero", "Not yet. I know it is causing the trouble, so I will not yank it.")
    world.say("helper", "Good. I will steady the tower while you slide the object away.")
    repair(world)
    world.narrate(
        "repair",
        f"{hero} moved the hidden object aside while {helper} held the tower. "
        f"Together they placed the {kind_plural} in their own spaces and made a short, steady stack.",
        question="How did the children repair the kitchen?",
        cause=f"They identified {surprise_text} as the cause of the stuck drawer and stabilized the tower.",
        result=f"They sorted the {kind_plural} and made the cutlery safe for supper.",
    )
    world.say("hero", "Now the drawer opens with one gentle hand.")
    world.say("helper", "And the tower stands because we worked together.")
    world.entities["supper"].meters["ready"] = 1
    if params.ending == "mess":
        world.narrate(
            "ending",
            f"They set the table, but Luna left the hidden object in the walkway. "
            f"It bumped a chair and made one last little clink. The supper was ready, yet the heroes had learned that a repair needs a tidy finish too.",
            question="What lesson remained after the rescue?",
            cause="The children fixed the drawer but forgot to put the surprising object away.",
            result="Supper could begin, but the loose object showed that careful heroes finish every part of a job.",
        )
    elif params.ending == "lesson":
        world.narrate(
            "ending",
            f"They set the {kind_plural} beside the plates and put {surprise_text} into a safe box. "
            f"Luna folded her towel cape and smiled at the quiet drawer.",
            question="How did the final scene show that Luna had changed?",
            cause="She had learned to replace a rushed action with observation and teamwork.",
            result="She stored the surprise safely and finished the table carefully.",
        )
    else:
        world.narrate(
            "ending",
            f"They set the {kind_plural} beside the plates, and the drawer glided shut. "
            f"Luna raised her towel cape while {helper} lifted a cup. This time, their superhero ending was calm, safe, and ready for supper.",
            question="What proved that the rescue worked?",
            cause="The children sorted the cutlery, steadied the tower, and stored the surprise safely.",
            result="The drawer closed smoothly and the supper table was ready.",
        )
    world.entities["hero"].memes["worry"] = 0.0
    world.entities["hero"].memes["trust"] = 1.0
    world.entities["helper"].memes["trust"] = 1.0
    sample = world.sample()
    check_sample(sample)
    return sample


def check_sample(sample: StorySample):
    world = sample.world
    check_ending(world)
    speeches = [event for event in world.history if event.kind == "speech"]
    if len(speeches) < 10:
        raise StoryError("The story needs a sustained back-and-forth conversation.")
    if not any(event.speaker == "hero" for event in speeches):
        raise StoryError("The hero must speak.")
    if not any(event.speaker == "helper" for event in speeches):
        raise StoryError("The helper must speak.")
    if not any(event.revealed for event in speeches):
        raise StoryError("The conversation must pass on useful information.")
    if len(sample.story_qa) < 4:
        raise StoryError("The story needs grounded questions and answers.")
    if world.entities["hero"].memes["trust"] < 1:
        raise StoryError("The hero must end by trusting the teamwork.")


def asp_facts() -> str:
    from asp import fact

    facts = []
    for key in CUTLERY:
        facts.append(fact("cutlery", key))
    for key in SURPRISES:
        facts.append(fact("surprise", key))
    for key in CONFLICTS:
        facts.append(fact("conflict", key))
    return "\n".join(facts)


def asp_combos() -> set[tuple[str, str, str]]:
    from asp import atoms, one_model

    symbols = one_model(asp_facts() + "\n" + ASP_RULES)
    return set(atoms(symbols, "story_state"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--hero")
    parser.add_argument("--helper")
    parser.add_argument("--cutlery", choices=tuple(CUTLERY))
    parser.add_argument("--surprise", choices=tuple(SURPRISES))
    parser.add_argument("--conflict", choices=tuple(CONFLICTS))
    parser.add_argument("--ending", choices=tuple(ENDINGS))
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(NAMES)
    helper_choices = [name for name in NAMES if name != hero]
    helper = args.helper or rng.choice(helper_choices)
    params = StoryParams(
        hero=hero,
        helper=helper,
        cutlery=args.cutlery or rng.choice(tuple(CUTLERY)),
        surprise=args.surprise or rng.choice(tuple(SURPRISES)),
        conflict=args.conflict or rng.choice(tuple(CONFLICTS)),
        ending=args.ending or rng.choice(tuple(ENDINGS)),
        seed=args.seed,
    )
    validate_params(params)
    return params


def verify():
    expected = set(valid_combos())
    actual = asp_combos()
    if expected != actual:
        raise StoryError("Python and ASP disagree about valid story states.")
    tested = 0
    for cutlery, surprise, conflict in valid_combos():
        for ending in ENDINGS:
            sample = generate(
                StoryParams(
                    cutlery=cutlery,
                    surprise=surprise,
                    conflict=conflict,
                    ending=ending,
                )
            )
            check_sample(sample)
            tested += 1
    print(f"OK: {tested} story states; {len(expected)} ASP-compatible combinations.")


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
            params_list = []
            for cutlery, surprise, conflict in valid_combos():
                for ending in ENDINGS:
                    fields = vars(args).copy()
                    fields.update(
                        cutlery=cutlery,
                        surprise=surprise,
                        conflict=conflict,
                        ending=ending,
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
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
