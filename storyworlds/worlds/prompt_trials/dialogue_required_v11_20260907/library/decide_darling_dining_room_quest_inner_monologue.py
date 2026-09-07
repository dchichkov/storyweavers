#!/usr/bin/env python3
"""A darling decision in the dining room, told through a small quest and suspense."""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
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
    darling: str = "Pip"
    choice: str = "lantern"
    helper: str = "grandma"
    seed: int = 777


NAMES = ("Mara", "Pip", "Lena", "Owen", "Nia", "Theo")
CHOICES = ("lantern", "cake", "napkin")
HELPERS = ("grandma", "grandpa", "aunt")
PROMPT = (
    "Write a heartwarming dialogue-rich children's story set in a dining room "
    "where a darling must decide during a suspenseful quest."
)

CHOICE_DATA = {
    "lantern": {
        "object": "the brass lantern",
        "clue": "a warm golden glow",
        "place": "the sideboard",
        "ending": "The lantern glowed beside the plates, making the whole room feel ready for kindness.",
    },
    "cake": {
        "object": "the berry cake",
        "clue": "three blue berries",
        "place": "the pantry shelf",
        "ending": "The berry cake waited beneath its cover while everyone pulled their chairs close.",
    },
    "napkin": {
        "object": "the embroidered napkin",
        "clue": "a tiny red heart",
        "place": "the linen drawer",
        "ending": "The napkin lay beneath the birthday plate, its red heart bright as a promise.",
    },
}

ASP_RULES = """
reachable(Choice) :- option(Choice, _), clue(Choice, _), hiding_place(Choice, _).
#show reachable/1.
"""


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities = {
            "hero": Entity(
                "hero",
                params.hero,
                "character",
                "dining_room",
                memes={"worry": 0.4, "courage": 0.5, "warmth": 0.5},
            ),
            "darling": Entity(
                "darling",
                params.darling,
                "character",
                "dining_room",
                memes={"worry": 0.6, "courage": 0.4, "warmth": 0.7},
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

    def say(self, speaker: str, text: str, *, listener: str = ""):
        actor = self.entities[speaker]
        verb = "asked" if text.endswith("?") else "said"
        self.history.append(
            Event(
                kind="speech",
                text=f'"{text}" {actor.label} {verb}.',
                speaker=speaker,
                listener=listener,
                state=self.snapshot(),
            )
        )

    def sample(self) -> StorySample:
        return StorySample(
            params=self.params,
            story="\n\n".join(event.text for event in self.history),
            prompts=[PROMPT],
            story_qa=[
                QAItem(question=e.question, answer=f"{e.cause} {e.result}")
                for e in self.history
                if e.question
            ],
            world_qa=[
                QAItem(
                    question="Where does this story take place?",
                    answer="It takes place in a dining room with a table, chairs, and a sideboard.",
                ),
                QAItem(
                    question="What makes a good decision during a quest?",
                    answer="A good decision uses clues, listens to a helper, and cares about the people involved.",
                ),
            ],
            world=self,
        )


def validate_params(params: StoryParams):
    if params.choice not in CHOICES:
        raise StoryError("Choose a lantern, cake, or napkin quest.")
    if params.helper not in HELPERS:
        raise StoryError("Choose a known family helper.")
    if params.hero == params.darling:
        raise StoryError("The quest companions need different names.")
    if any(not re.fullmatch(r"[A-Z][a-z]+", name) for name in (params.hero, params.darling)):
        raise StoryError("Use simple capitalized names for the characters.")


def build_world(params: StoryParams) -> World:
    validate_params(params)
    world = World(params)
    data = CHOICE_DATA[params.choice]
    world.entities["quest_item"] = Entity(
        "quest_item",
        data["object"],
        "object",
        data["place"],
        meters={"found": 0, "safe": 0},
    )
    world.entities["dining_table"] = Entity(
        "dining_table",
        "the long dining table",
        "furniture",
        "dining_room",
        meters={"plates_ready": 1},
    )
    world.entities["helper"] = Entity(
        "helper",
        params.helper.title(),
        "character",
        "kitchen",
        memes={"patience": 1.0, "warmth": 1.0},
    )
    return world


def complete_ending(world: World):
    item = world.entities["quest_item"]
    if not item.meters.get("found") or not item.meters.get("safe"):
        raise StoryError("The quest item must be found and safely brought to the dining room.")
    for key in ("hero", "darling"):
        if world.entities[key].memes.get("courage", 0) < 1:
            raise StoryError("Both companions must gain courage before the ending.")


def check_sample(sample: StorySample):
    world = sample.world
    complete_ending(world)
    speeches = [event for event in world.history if event.kind == "speech"]
    if len(speeches) < 10:
        raise StoryError("The story needs a sustained back-and-forth conversation.")
    if not any(event.speaker == "hero" for event in speeches):
        raise StoryError("The hero must speak.")
    if not any(event.speaker == "darling" for event in speeches):
        raise StoryError("The darling must speak.")
    if len(sample.story_qa) < 3:
        raise StoryError("The story needs grounded questions and answers.")
    if "decide" not in sample.story.lower() or "darling" not in sample.story.lower():
        raise StoryError("The required seed words must appear naturally.")
    if any(not e.cause or not e.result for e in world.history if e.question):
        raise StoryError("Every story question needs a cause and consequence.")


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    hero = world.entities["hero"].label
    darling = world.entities["darling"].label
    helper = world.entities["helper"].label
    data = CHOICE_DATA[params.choice]
    item = data["object"]

    world.narrate(
        "beginning",
        f"In the dining room, {hero} set two blue plates on the long table. "
        f"{darling}, the family's darling little planner, held a folded map for a tiny supper quest. "
        "One important thing was missing.",
    )
    world.say("hero", f"Darling, did you decide where we should begin?")
    world.say("darling", f"I decided to look for {item}, but now the dining room feels very quiet.")
    world.narrate(
        "suspense",
        f"A clock gave one soft tick. Somewhere near the table, a small sound went tap, tap, tap. "
        f"{darling} squeezed the map while {hero} watched the shadows beside the sideboard.",
        question=f"Why did the quest feel suspenseful when they searched for {item}?",
        cause=f"They could hear a mysterious tapping sound but could not yet see {item}.",
        result="The quiet dining room made an ordinary search feel like a brave adventure.",
    )
    world.say("hero", "We can be scared and still look carefully.")
    world.say("darling", "I want to decide, but I do not know whether to search the sideboard or the pantry.")
    world.narrate(
        "inner_monologue",
        f"Inside {darling}'s thoughts, a tiny worried voice whispered, "
        "'What if I choose badly and spoil supper?' Then another voice answered, "
        "'A clue is better than a guess.'",
        question="What helped the darling make a careful decision?",
        cause=f"{darling} noticed that guessing felt frightening, while following a clue felt useful.",
        result=f"{darling} chose to look for evidence before choosing a hiding place.",
    )
    world.say("hero", f"What clue do you remember, {darling}?")
    world.say("darling", f"I remember {data['clue']} from the last time I saw it.")
    world.say("hero", f"Then we should search for {data['clue']}, not rush toward every shadow.")
    world.say("darling", "Will you come with me?")
    world.say("hero", "Every step of the quest.")

    world.narrate(
        "clue",
        f"Together they checked the tablecloth, the chair legs, and the gleaming dishes. "
        f"At last, {darling} spotted a faint trace of {data['clue']} leading toward {data['place']}.",
        question=f"How did they choose where to search for {item}?",
        cause=f"{darling} remembered {data['clue']} and followed its trail.",
        result=f"They decided that {data['place']} was more likely than a random hiding place.",
    )
    world.say("darling", f"The clue points to {data['place']}. I decide we should look there.")
    world.say("hero", "That is a brave and sensible decision.")
    world.say("darling", "But what if the tapping sound is something else?")
    world.say("hero", f"Then we will discover that together, and {helper} can help if we need help.")

    world.narrate(
        "helper",
        f"{helper} appeared in the kitchen doorway carrying a spoon. "
        f'"A quest is safest when brave explorers share what they know," {helper} said.',
        question="Why did the helper encourage the children to share what they knew?",
        cause=f"The helper saw that the children had a clue but were still worried about the tapping.",
        result="Sharing information gave them courage without taking the decision away from them.",
    )
    world.say("darling", f"We found a trail of {data['clue']} and heard tapping.")
    world.say("helper", "Then open the drawer slowly, and keep one hand on the table.")
    world.say("hero", "Ready, darling?")
    world.say("darling", "Ready.")

    world.entities["quest_item"].location = "dining_room"
    world.entities["quest_item"].meters.update(found=1, safe=1)
    world.entities["hero"].memes.update(courage=1.0, warmth=1.0)
    world.entities["darling"].memes.update(courage=1.0, warmth=1.0)
    world.narrate(
        "turn",
        f"{darling} opened the hiding place. There was {item}, safe and sound. "
        f"The tapping was only a spoon rolling against a wooden bowl.",
        question=f"What was the surprising cause of the suspense?",
        cause="The children had mistaken a spoon tapping inside a bowl for a mysterious danger.",
        result=f"They found {item} and learned that careful listening can turn fear into understanding.",
    )
    world.say("darling", "I thought the sound meant trouble.")
    world.say("hero", "It meant we had one more clue to understand.")
    world.say("helper", "And now the dining room is ready for its warmest part.")
    world.say("darling", "I decided to keep searching instead of giving up.")
    world.say("hero", "That decision brought the missing treasure home.")

    world.narrate(
        "ending",
        f"They carried {item} to the table and placed it beside the blue plates. "
        f"{data['ending']} {darling} smiled at the quiet clock, which no longer sounded frightening.",
        question="What changed by the end of the quest?",
        cause=f"{darling} used a remembered clue, listened to the helper, and chose to continue searching.",
        result=f"The missing treasure returned to the dining room, and the children felt proud of their shared decision.",
    )
    sample = world.sample()
    check_sample(sample)
    return sample


def valid_combos() -> list[tuple[str, str]]:
    return [(choice, "reachable") for choice in CHOICES]


def asp_facts() -> str:
    from asp import fact

    data = []
    for choice, values in CHOICE_DATA.items():
        data.extend(
            [
                fact("option", choice, values["object"]),
                fact("clue", choice, values["clue"]),
                fact("hiding_place", choice, values["place"]),
            ]
        )
    return "\n".join(data)


def asp_combos() -> set[tuple[str]]:
    from asp import atoms, one_model

    return set(atoms(one_model(asp_facts() + "\n" + ASP_RULES), "reachable"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--hero")
    parser.add_argument("--darling")
    parser.add_argument("--choice", choices=CHOICES)
    parser.add_argument("--helper", choices=HELPERS)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(NAMES)
    darling = args.darling or rng.choice([name for name in NAMES if name != hero])
    params = StoryParams(
        hero=hero,
        darling=darling,
        choice=args.choice or rng.choice(CHOICES),
        helper=args.helper or rng.choice(HELPERS),
        seed=args.seed,
    )
    validate_params(params)
    return params


def verify():
    if set(choice for choice, _ in valid_combos()) != {x[0] for x in asp_combos()}:
        raise StoryError("Python and ASP disagree about reachable quest choices.")
    tested = 0
    for choice in CHOICES:
        for helper in HELPERS:
            sample = generate(
                StoryParams(hero="Mara", darling="Pip", choice=choice, helper=helper)
            )
            check_sample(sample)
            tested += 1
    print(f"OK: {tested} story states; {len(CHOICES)} ASP-compatible quest choices.")


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
            params_list = [
                StoryParams(
                    hero=args.hero or "Mara",
                    darling=args.darling or "Pip",
                    choice=choice,
                    helper=args.helper or "grandma",
                    seed=args.seed,
                )
                for choice in CHOICES
            ]
            for params in params_list:
                validate_params(params)
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
