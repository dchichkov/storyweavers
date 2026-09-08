#!/usr/bin/env python3
"""The Bun, the Teat, and the Gospel: curiosity follows a small mystery."""

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
    mystery: str = "missing_crumb"
    lesson: str = "look_closely"
    approach: str = "curious"
    seed: int = 777


NAMES = ("Luna", "Pip", "Mara", "Tobin", "Nell", "Otis")
APPROACHES = ("curious", "hasty")
MYSTERIES = {
    "missing_crumb": "a bun crumb vanished",
    "backward_page": "a gospel page turned backward",
    "cold_teat": "a teat cup was cold",
}
LESSONS = {
    "look_closely": "look_closely",
    "ask_kindly": "ask_kindly",
    "test_gently": "test_gently",
}

PROMPT = (
    "Write a fable-like children's story about Luna and a friend solving a small "
    "mystery involving a teat, a gospel, and a bun, where curiosity leads to a lesson learned."
)

ASP_RULES = """
solves(M,L) :- mystery(M), lesson(L), teaches(M,L).
#show solves/2.
"""


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities = {
            "hero": Entity(
                "hero", params.hero, "character", "chapel_yard",
                memes={"curiosity": 1.0, "patience": 0.4, "wisdom": 0.2},
            ),
            "helper": Entity(
                "helper", params.helper, "character", "chapel_yard",
                memes={"curiosity": 0.7, "patience": 0.6, "wisdom": 0.3},
            ),
            "bun": Entity(
                "bun", "a honey bun", "food", "bread_table",
                meters={"whole": 1.0, "crumbs": 0.0},
            ),
            "teat": Entity(
                "teat", "a blue teat cup", "cup", "chapel_yard",
                meters={"warmth": 1.0, "filled": 0.0},
            ),
            "gospel": Entity(
                "gospel", "the old gospel", "book", "lectern",
                meters={"pages": 12.0, "turned": 0.0},
            ),
        }
        self.history: list[Event] = []

    def snapshot(self) -> dict:
        return {key: asdict(value) for key, value in self.entities.items()}

    def narrate(self, kind: str, text: str, *, question="", cause="", result=""):
        self.history.append(Event(
            kind=kind, text=text, question=question, cause=cause,
            result=result, state=self.snapshot(),
        ))

    def say(self, speaker: str, text: str, *, to="", reveal="", tag="said"):
        actor = self.entities[speaker]
        if reveal:
            if not to or reveal not in actor.beliefs:
                raise StoryError("A character cannot share a fact they have not learned.")
            self.entities[to].beliefs[reveal] = actor.beliefs[reveal]
        if text.endswith("?") and tag == "said":
            tag = "asked"
        self.history.append(Event(
            kind="speech",
            text=f'"{text}" {actor.label} {tag}.',
            speaker=speaker,
            listener=to,
            revealed=reveal,
            state=self.snapshot(),
        ))

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
                QAItem(
                    "What does curiosity do in this fable?",
                    "Curiosity helps Luna pause, ask questions, and test the mystery instead of guessing.",
                ),
                QAItem(
                    "What is the lesson learned?",
                    "The lesson is to look closely, ask kindly, and test a guess before declaring it true.",
                ),
            ],
            world=self,
        )


def validate_params(params: StoryParams):
    if params.mystery not in MYSTERIES or params.lesson not in LESSONS:
        raise StoryError("Choose a mystery and a lesson from the available story choices.")
    if params.approach not in APPROACHES:
        raise StoryError("Choose either a curious or hasty approach.")
    if params.hero == params.helper:
        raise StoryError("The two speakers must have different names.")
    if any(not re.fullmatch(r"[A-Z][a-z]+", name) for name in (params.hero, params.helper)):
        raise StoryError("Names must be simple capitalized names, such as Luna and Pip.")


def build_world(params: StoryParams) -> World:
    validate_params(params)
    return World(params)


def solve_missing_crumb(world: World):
    h = world.entities["hero"]
    f = world.entities["helper"]
    bun = world.entities["bun"]

    world.say("hero", "The bun had a golden crumb beside it a moment ago.")
    world.say("helper", "Perhaps the wind ate it.")
    if world.params.approach == "hasty":
        h.memes["patience"] = 0.1
        world.say("hero", "Then the wind must be hiding under the table.")
        world.narrate(
            "failed_guess",
            "Luna peered beneath the table, but found only a blue teat cup and a sleepy beetle.",
        )
        world.say("helper", "Could we look before we blame the wind?")
    else:
        world.say("hero", "Let us look closely before we blame the wind.")
    h.beliefs["crumb"] = "a crumb trail leads toward the lectern"
    world.narrate(
        "clue",
        "Luna bent low. Three tiny crumbs curved from the bread table toward the lectern.",
        question="Why did Luna stop guessing about the missing crumb?",
        cause="She noticed a trail of crumbs leading away from the bun.",
        result="The trail gave her a clue to follow.",
    )
    world.say("hero", "Pip, do you see those crumbs by the gospel?")
    world.say("helper", "I do. They pass the teat cup and end beside the lectern.",
            to="hero", reveal="crumb")
    world.entities["gospel"].beliefs["secret"] = "the page was holding the crumb"
    world.narrate(
        "discovery",
        "Behind the gospel, Luna found the missing crumb pressed against a folded page.",
    )
    world.say("hero", "The gospel did not eat the crumb. It held it fast.")
    world.say("helper", "And the beetle carried the first crumbs on its back.")
    bun.meters["crumbs"] = 1.0
    world.entities["gospel"].meters["turned"] = 1.0
    world.narrate(
        "lesson",
        "Luna smiled and lifted the gospel gently. The crumb slipped free without tearing the page.",
        question="How did Luna solve the mystery of the missing crumb?",
        cause="She followed the tiny crumb trail from the bun to the lectern.",
        result="She found the crumb caught behind a folded page of the gospel.",
    )


def solve_backward_page(world: World):
    h = world.entities["hero"]
    world.say("hero", "The gospel page is backward. Someone must have made a mistake.")
    world.say("helper", "Or perhaps the book is showing us something.")
    if world.params.approach == "hasty":
        h.memes["patience"] = 0.1
        world.say("hero", "I will turn it straight at once.")
        world.narrate(
            "failed_guess",
            "Luna reached for the page, but Pip placed one finger on the table.",
        )
        world.say("helper", "What if we read the marks before we move the page?")
    else:
        world.say("hero", "Let us read the marks before we move the page.")
    h.beliefs["page"] = "a crumb-shaped mark points beneath the lectern"
    world.narrate(
        "clue",
        "Along the backward page ran three brown dots, like crumbs marching in a line.",
        question="Why did Luna wait before turning the gospel page?",
        cause="The brown dots looked like a trail rather than a mistake.",
        result="She decided to study the clue before changing the book.",
    )
    world.say("hero", "Pip, where does the little trail point?")
    world.say("helper", "Under the lectern, beside the teat cup.", to="hero", reveal="page")
    world.entities["gospel"].meters["turned"] = 1.0
    world.entities["gospel"].beliefs["secret"] = "the page marked a hidden bun"
    world.narrate(
        "discovery",
        "They turned the page carefully and found the bun's missing golden crumb tucked beneath the lectern.",
    )
    world.say("hero", "The backward page was a sign, not a blunder.")
    world.say("helper", "A book can point with marks as well as words.")
    world.entities["bun"].meters["crumbs"] = 1.0
    world.narrate(
        "lesson",
        "Luna placed the crumb back beside the bun and left the gospel open to its quiet clue.",
        question="What did the backward gospel page reveal?",
        cause="Its brown marks formed a trail toward the lectern.",
        result="The trail led to the bun's missing crumb.",
    )


def solve_cold_teat(world: World):
    h = world.entities["hero"]
    teat = world.entities["teat"]
    world.say("hero", "The teat cup is cold, though it was warm at breakfast.")
    world.say("helper", "Then someone forgot it in the shade.")
    if world.params.approach == "hasty":
        h.memes["patience"] = 0.1
        world.say("hero", "I will pour it out and fill it again.")
        world.narrate(
            "failed_guess",
            "Luna lifted the teat cup, but saw a pale ring on the table beneath it.",
        )
        world.say("helper", "Before we fix it, may we find out what happened?")
    else:
        world.say("hero", "Let us find out what happened before we fix it.")
    h.beliefs["teat"] = "the cup was moved onto a cool gospel page"
    world.narrate(
        "clue",
        "The blue teat cup stood on the gospel, and the page beneath it felt cool as a cellar stone.",
        question="What clue helped Luna understand the cold teat cup?",
        cause="She saw that the cup had been resting on a cool page of the gospel.",
        result="The page had drawn warmth from the teat cup.",
    )
    world.say("hero", "Pip, did the gospel make the teat cup cold?")
    world.say("helper", "Yes. The page is cool, and the cup has been sitting on it.",
            to="hero", reveal="teat")
    teat.meters["warmth"] = 0.0
    world.entities["gospel"].meters["turned"] = 1.0
    world.narrate(
        "discovery",
        "They moved the teat cup to a sunny sill. The gospel page slowly warmed beneath the light.",
    )
    world.say("hero", "We needed a sunny sill, not a new drink.")
    world.say("helper", "A careful question saved the milk and the page.")
    world.entities["bun"].meters["crumbs"] = 1.0
    world.narrate(
        "lesson",
        "Luna placed a bun beside the cup, and both friends watched the warmth return.",
        question="How did Luna solve the mystery of the cold teat cup?",
        cause="She discovered that the cup had been resting on the cool gospel.",
        result="They moved it to a sunny sill and let it warm naturally.",
    )


def check_ending(world: World):
    if world.entities["bun"].meters["crumbs"] != 1.0:
        raise StoryError("The story must account for the missing bun crumb.")
    if world.entities["gospel"].meters["turned"] < 1.0:
        raise StoryError("The gospel must be examined during the mystery.")
    if not any(event.kind == "lesson" for event in world.history):
        raise StoryError("The story needs a clear lesson learned.")
    if not any(event.kind == "discovery" for event in world.history):
        raise StoryError("Curiosity must lead to a real discovery.")


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    h = world.entities["hero"].label
    f = world.entities["helper"].label

    world.narrate(
        "beginning",
        f"In a little chapel garden, {h} set a honey bun beside a blue teat cup. "
        f"Near the cup rested an old gospel, its pages quiet in the afternoon sun.",
    )
    world.say("hero", "The bun is for sharing after we finish our work.")
    world.say("helper", "And the gospel is for remembering wise things.")
    world.say("hero", "Then let us keep the teat cup safe between us.")

    if params.mystery == "missing_crumb":
        solve_missing_crumb(world)
    elif params.mystery == "backward_page":
        solve_backward_page(world)
    else:
        solve_cold_teat(world)

    world.narrate(
        "ending",
        f"At last, {h} and {f} shared the bun beside the teat cup. "
        "The gospel lay open, the mystery was small no longer, and their curiosity "
        "glowed brighter than the chapel bell.",
        question="What lesson did Luna learn?",
        cause="She followed evidence, listened to Pip, and tested her first guess.",
        result="She learned that patient curiosity finds truth more surely than a quick accusation.",
    )
    sample = world.sample()
    check_sample(sample)
    return sample


def check_sample(sample: StorySample):
    check_ending(sample.world)
    speeches = [event for event in sample.world.history if event.kind == "speech"]
    if len(speeches) < 10:
        raise StoryError("The fable needs a sustained exchange between the characters.")
    if sum(event.speaker == "hero" for event in speeches) < 4:
        raise StoryError("The hero needs enough spoken turns to change.")
    if sum(event.speaker == "helper" for event in speeches) < 4:
        raise StoryError("The helper needs enough spoken turns to matter.")
    if not any(event.revealed for event in speeches):
        raise StoryError("Dialogue must pass useful knowledge between characters.")
    if len(sample.story_qa) < 3:
        raise StoryError("The story needs grounded questions and natural answers.")
    if any(not item.answer.strip() or len(item.answer.split()) < 6 for item in sample.story_qa):
        raise StoryError("Story-grounded answers must be full explanations.")
    if sample.world.entities["hero"].memes["curiosity"] <= 0:
        raise StoryError("Curiosity must remain active in the ending.")


def valid_combos() -> list[tuple[str, str]]:
    return [
        ("missing_crumb", "look_closely"),
        ("backward_page", "look_closely"),
        ("cold_teat", "test_gently"),
    ]


def asp_facts() -> str:
    from asp import fact
    return "\n".join(
        [fact("mystery", mystery) for mystery in MYSTERIES]
        + [fact("lesson", lesson) for lesson in LESSONS]
        + [fact("teaches", mystery, lesson) for mystery, lesson in valid_combos()]
    )


def asp_combos() -> set[tuple[str, str]]:
    from asp import atoms, one_model
    return set(atoms(one_model(asp_facts() + "\n" + ASP_RULES), "solves"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--hero")
    parser.add_argument("--helper")
    parser.add_argument("--mystery", choices=tuple(MYSTERIES))
    parser.add_argument("--lesson", choices=tuple(LESSONS))
    parser.add_argument("--approach", choices=APPROACHES)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    choices = [
        pair for pair in valid_combos()
        if (args.mystery is None or pair[0] == args.mystery)
        and (args.lesson is None or pair[1] == args.lesson)
    ]
    if not choices:
        raise StoryError("That lesson does not fit the selected mystery.")
    mystery, lesson = rng.choice(choices)
    hero = args.hero or "Luna"
    helper = args.helper or rng.choice([name for name in NAMES if name != hero])
    params = StoryParams(
        hero=hero,
        helper=helper,
        mystery=mystery,
        lesson=lesson,
        approach=args.approach or rng.choice(APPROACHES),
        seed=args.seed,
    )
    validate_params(params)
    return params


def verify():
    if set(valid_combos()) != asp_combos():
        raise StoryError("Python and ASP disagree about mystery and lesson pairs.")
    tested = 0
    for mystery, lesson in valid_combos():
        for approach in APPROACHES:
            sample = generate(StoryParams(
                mystery=mystery,
                lesson=lesson,
                approach=approach,
                seed=777,
            ))
            check_sample(sample)
            tested += 1
    print(f"OK: {tested} story states; {len(valid_combos())} compatible mystery/lesson pairs.")


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
            choices = [
                (mystery, lesson, approach)
                for mystery, lesson in valid_combos()
                for approach in APPROACHES
                if (args.mystery is None or mystery == args.mystery)
                and (args.lesson is None or lesson == args.lesson)
                and (args.approach is None or approach == args.approach)
            ]
            if not choices:
                raise StoryError("No compatible combinations match these options.")
            params_list = [
                StoryParams(
                    hero=args.hero or "Luna",
                    helper=args.helper or rng.choice([name for name in NAMES if name != (args.hero or "Luna")]),
                    mystery=mystery,
                    lesson=lesson,
                    approach=approach,
                    seed=args.seed,
                )
                for mystery, lesson, approach in choices
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
