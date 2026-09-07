#!/usr/bin/env python3
"""A darling's dining-room quest: deciding what kindness can do."""

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
    hero: str = "Nora"
    darling: str = "Pip"
    quest: str = "find"
    clue: str = "napkin"
    seed: int = 777


NAMES = ("Nora", "Milo", "Lina", "Theo", "Ava", "Iris")
DARLINGS = ("Pip", "Biscuit", "Momo", "Clover")
QUESTS = {
    "find": "find the missing blue spoon",
    "prepare": "prepare a welcome table",
    "repair": "repair the lonely chair",
}
CLUES = {
    "napkin": "a folded napkin",
    "bell": "a tiny dinner bell",
    "ribbon": "a red ribbon",
}
PROMPT = (
    "Write a heartwarming children's story in a dining room where a child must "
    "decide how to help a darling friend complete a small quest, using suspense "
    "and gentle inner monologue."
)


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities = {
            "hero": Entity("hero", params.hero, "character", "dining_room",
                           memes={"hope": 0.5, "courage": 0.4, "care": 0.8}),
            "darling": Entity("darling", params.darling, "small_friend", "dining_room",
                              memes={"trust": 0.6, "loneliness": 0.7}),
            "table": Entity("table", "the dining table", "furniture", "dining_room",
                            meters={"places": 0}),
        }
        self.history: list[Event] = []

    def snapshot(self) -> dict:
        return {key: asdict(value) for key, value in self.entities.items()}

    def narrate(self, kind: str, text: str, *, question="", cause="", result=""):
        self.history.append(Event(kind=kind, text=text, question=question,
                                  cause=cause, result=result, state=self.snapshot()))

    def say(self, speaker: str, text: str, *, listener=""):
        if text.endswith("?"):
            verb = "asked"
        else:
            verb = "said"
        label = self.entities[speaker].label
        self.history.append(Event(kind="speech", text=f'"{text}" {label} {verb}.',
                                  speaker=speaker, listener=listener,
                                  state=self.snapshot()))

    def inner(self, text: str):
        self.history.append(Event(kind="inner_monologue",
                                  text=f"{self.entities['hero'].label} thought, {text}"))

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
                    "Why is listening useful during a quest?",
                    "Listening helps a friend share what matters before someone decides how to help."
                )
            ],
            world=self,
        )


def validate_params(params: StoryParams):
    if params.quest not in QUESTS or params.clue not in CLUES:
        raise StoryError("Choose a quest and clue from the available story choices.")
    if params.hero == params.darling:
        raise StoryError("The child and the darling friend need different names.")
    if any(not re.fullmatch(r"[A-Z][a-z]+", name)
           for name in (params.hero, params.darling)):
        raise StoryError("Names must be simple capitalized words, such as Nora and Pip.")


def build_world(params: StoryParams) -> World:
    validate_params(params)
    world = World(params)
    world.entities["quest_item"] = Entity(
        "quest_item", CLUES[params.clue], "clue", "sideboard",
        meters={"found": 0, "used": 0},
        beliefs={"purpose": "make the table feel welcoming"},
    )
    world.entities["spoon"] = Entity(
        "spoon", "the blue spoon", "utensil", "unknown",
        meters={"found": 0, "placed": 0},
    )
    world.entities["chair"] = Entity(
        "chair", "the small chair", "furniture", "dining_room",
        meters={"repaired": 0, "safe": 0},
    )
    world.entities["place_setting"] = Entity(
        "place_setting", "a warm place at the table", "welcome", "dining_room",
        meters={"ready": 0},
    )
    return world


def perform_quest(world: World):
    params = world.params
    hero = world.entities["hero"]
    darling = world.entities["darling"]
    clue = world.entities["quest_item"]

    if params.quest == "find":
        spoon = world.entities["spoon"]
        if clue.meters["found"] != 1:
            raise StoryError("The clue must be noticed before it can guide the search.")
        spoon.location = "under_table"
        spoon.meters["found"] = 1
        spoon.meters["placed"] = 1
        clue.meters["used"] = 1
        world.entities["table"].meters["places"] = 1
        darling.location = "at_table"
        hero.memes["courage"] = 1.0
        world.narrate(
            "quest_complete",
            f"{hero.label} lifted the tablecloth and found {spoon.label} "
            f"beside a chair leg. {darling.label} carried it proudly to the table.",
            question="How did the clue help with the quest?",
            cause=f"The {clue.label} reminded {hero.label} to look carefully around the dining room.",
            result=f"{hero.label} searched under the table and found the blue spoon there.",
        )
    elif params.quest == "prepare":
        setting = world.entities["place_setting"]
        setting.meters["ready"] = 1
        clue.meters["found"] = 1
        clue.meters["used"] = 1
        world.entities["table"].meters["places"] = 1
        darling.location = "at_table"
        hero.memes["care"] = 1.0
        world.narrate(
            "quest_complete",
            f"They spread {clue.label} beside a plate, set out a cup, and left "
            f"the kindest chair facing the window.",
            question="What made the welcome table ready?",
            cause=f"They used {clue.label} as a small sign that someone was expected.",
            result="They added a place, a cup, and a friendly chair so the guest would feel remembered.",
        )
    else:
        chair = world.entities["chair"]
        chair.meters["repaired"] = 1
        chair.meters["safe"] = 1
        clue.meters["found"] = 1
        clue.meters["used"] = 1
        darling.location = "at_table"
        hero.memes["courage"] = 1.0
        world.narrate(
            "quest_complete",
            f"{hero.label} tied {clue.label} around the loose chair rung while "
            f"{darling.label} held the chair steady. The seat stopped wobbling.",
            question="Why did they repair the chair before sitting down?",
            cause="The chair wobbled, so using it immediately could have caused a tumble.",
            result=f"They tied {clue.label} around the loose rung and tested the chair safely.",
        )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    h = world.entities["hero"].label
    d = world.entities["darling"].label
    quest = QUESTS[params.quest]
    clue = CLUES[params.clue]

    world.narrate(
        "beginning",
        f"In the quiet dining room, {h} found {d} beneath the tablecloth. "
        f"The little darling had a quest: to {quest}. A clock ticked above the sideboard, "
        "and supper would begin when its long hand reached the twelve.",
    )
    world.say("darling", f"{h}, can you help me?")
    world.say("hero", "I can try. What must we decide first?")
    world.say("darling", f"We need to finish before the clock rings. I brought {clue}.")
    world.inner(
        "If I choose the wrong plan, the little quest may stay unfinished. "
        "But {d} asked me, so I should listen before I hurry."
    )
    world.entities["quest_item"].meters["found"] = 1
    world.entities["darling"].beliefs["purpose"] = "help the dining room welcome someone"
    world.narrate(
        "clue",
        f"{h} examined {clue}. It was small, but it pointed toward the dining room's "
        "hidden need: something had been forgotten near the table.",
        question="What did the child learn before choosing a plan?",
        cause=f"{d} explained the deadline and showed {clue}.",
        result=f"{h} learned that the quest was about making the dining room ready, not merely rushing.",
    )
    world.say("hero", "Darling, do you know who the table is waiting for?")
    world.say("darling", "Someone who may feel lonely if there is no place for them.")
    world.say("hero", "Then I decide to look gently, not grab everything at once.")
    world.say("darling", "I will watch the chair side while you check the table.")
    world.entities["hero"].memes["courage"] = 0.7

    world.narrate(
        "suspense",
        f"The clock hand crept closer to twelve. A spoon clinked somewhere in the "
        f"dining room, but neither friend could see it. {d} held {clue} tightly.",
        question="What created suspense in the dining room?",
        cause="The clock was nearing supper time while the needed object remained hidden.",
        result=f"{h} and {d} divided the search instead of giving up or making a noisy mess.",
    )
    world.say("darling", "Did you hear that? It came from under the table.")
    world.say("hero", "I heard it. Stay close, darling. We will find the answer together.")
    world.inner(
        "The shadows beneath the table looked deep, but courage did not mean feeling no fear. "
        "It meant taking one careful step with a friend."
    )
    perform_quest(world)
    world.say("darling", "You decided well. You listened before you acted.")
    world.say("hero", "You helped me decide. A quest is lighter when two hearts carry it.")
    world.narrate(
        "ending",
        f"The clock rang twelve just as {h} and {d} settled the last piece at the table. "
        f"At the doorway, a neighbor paused, saw the welcoming place, and smiled. "
        f"{d} tucked {clue} beside the plate, and the dining room felt bright enough for everyone.",
    )
    world.entities["darling"].memes["loneliness"] = 0.0
    world.entities["darling"].memes["trust"] = 1.0
    world.entities["hero"].memes["care"] = 1.0
    sample = world.sample()
    check_sample(sample)
    return sample


ASP_RULES = """
valid(Q,C) :- quest(Q), clue(C).
#show valid/2.
"""


def asp_facts() -> str:
    from asp import fact
    return "\n".join(
        [fact("quest", key) for key in QUESTS]
        + [fact("clue", key) for key in CLUES]
    )


def asp_combos() -> set[tuple[str, str]]:
    from asp import atoms, one_model
    return set(atoms(one_model(asp_facts() + "\n" + ASP_RULES), "valid"))


def check_sample(sample: StorySample):
    world = sample.world
    hero = world.entities["hero"]
    darling = world.entities["darling"]
    clue = world.entities["quest_item"]
    if clue.meters["found"] != 1 or clue.meters["used"] != 1:
        raise StoryError("The quest clue must be found and used in the resolution.")
    if darling.memes["loneliness"] != 0.0 or darling.memes["trust"] < 1.0:
        raise StoryError("The ending must show the darling feeling welcomed.")
    speeches = [event for event in world.history if event.kind == "speech"]
    if len(speeches) < 8:
        raise StoryError("The story needs a sustained back-and-forth conversation.")
    if not any(event.speaker == "hero" for event in speeches) or not any(
        event.speaker == "darling" for event in speeches
    ):
        raise StoryError("Both characters must speak.")
    if not any(event.kind == "inner_monologue" for event in world.history):
        raise StoryError("The story must include inner monologue.")
    if len(sample.story_qa) < 3:
        raise StoryError("The story needs grounded questions and causal answers.")
    if hero.memes["care"] < 1.0:
        raise StoryError("The hero's caring decision must shape the ending.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--hero")
    parser.add_argument("--darling")
    parser.add_argument("--quest", choices=tuple(QUESTS))
    parser.add_argument("--clue", choices=tuple(CLUES))
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(NAMES)
    darling = args.darling or rng.choice([name for name in DARLINGS if name != hero])
    params = StoryParams(
        hero=hero,
        darling=darling,
        quest=args.quest or rng.choice(tuple(QUESTS)),
        clue=args.clue or rng.choice(tuple(CLUES)),
        seed=args.seed,
    )
    validate_params(params)
    return params


def verify():
    expected = {(quest, clue) for quest in QUESTS for clue in CLUES}
    if expected != asp_combos():
        raise StoryError("Python and ASP disagree about valid quest and clue combinations.")
    tested = 0
    for quest in QUESTS:
        for clue in CLUES:
            sample = generate(StoryParams(quest=quest, clue=clue))
            check_sample(sample)
            tested += 1
    print(f"OK: {tested} story states; {len(expected)} Python/ASP-compatible pairs.")


def emit(sample: StorySample, *, trace=False, qa=False, header=""):
    if header:
        print(header)
    print(sample.story)
    if qa:
        for item in sample.story_qa:
            print(f"\nQ: {item.question}\nA: {item.answer}")
    if trace:
        print("\nTRACE")
        print(json.dumps(
            dict(
                entities=sample.world.snapshot(),
                history=[asdict(event) for event in sample.world.history],
            ),
            indent=2,
        ))


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
            params_list = [
                StoryParams(
                    hero=args.hero or "Nora",
                    darling=args.darling or "Pip",
                    quest=quest,
                    clue=clue,
                    seed=args.seed,
                )
                for quest in QUESTS
                for clue in CLUES
                if (args.quest is None or args.quest == quest)
                and (args.clue is None or args.clue == clue)
            ]
            if not params_list:
                raise StoryError("No quest and clue combinations match these options.")
            for params in params_list:
                validate_params(params)
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
