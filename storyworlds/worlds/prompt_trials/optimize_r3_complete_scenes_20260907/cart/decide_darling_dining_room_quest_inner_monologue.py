#!/usr/bin/env python3
"""A darling dining-room quest about deciding kindly under suspense."""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
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
    beliefs: dict[str, str] = field(default_factory=dict)


@dataclass
class Event:
    kind: str
    text: str
    question: str = ""
    cause: str = ""
    result: str = ""
    speaker: str = ""
    listener: str = ""


@dataclass
class StoryParams:
    hero: str = "Mara"
    darling: str = "Pip"
    path: str = "lantern"
    seed: int = 777


NAMES = ("Mara", "Nia", "Lena", "Owen", "Theo", "June")
DARLINGS = ("Pip", "Bram", "Clover", "Milo", "Wren")
PATHS = ("lantern", "cake", "letter")
PROMPT = (
    "Write a heartwarming dining-room quest with suspense and inner monologue, "
    "in which a child must decide kindly after learning a surprising fact."
)


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities = {
            "hero": Entity("hero", params.hero, "character", "dining_room",
                           memes={"courage": 0.4, "kindness": 0.7}),
            "darling": Entity("darling", params.darling, "character", "dining_room",
                              memes={"hope": 0.5, "trust": 0.6}),
            "table": Entity("table", "the dining table", "furniture", "dining_room",
                            meters={"seats": 4}),
        }
        self.history: list[Event] = []

    def scene(self, text: str, *, question: str = "", cause: str = "",
              result: str = ""):
        self.history.append(Event("scene", text, question, cause, result))

    def say(self, who: str, text: str, *, to: str = ""):
        speaker = self.entities[who].label
        self.history.append(Event("speech", f'"{text}" {speaker} said.',
                                  speaker=who, listener=to))

    def snapshot(self) -> dict:
        return {key: asdict(value) for key, value in self.entities.items()}

    def sample(self) -> StorySample:
        qa = [
            QAItem(event.question, f"{event.cause} {event.result}")
            for event in self.history if event.question
        ]
        return StorySample(
            params=self.params,
            story="\n\n".join(event.text for event in self.history),
            prompts=[PROMPT],
            story_qa=qa,
            world_qa=[
                QAItem("What kind of room was in the story?",
                       "The story took place in a dining room."),
                QAItem("What did deciding help the characters do?",
                       "Deciding helped the characters act kindly and finish their quest together."),
            ],
            world=self,
        )


def validate_params(params: StoryParams):
    if params.path not in PATHS:
        raise StoryError("The quest path must be lantern, cake, or letter.")
    if params.hero == params.darling:
        raise StoryError("The two characters need different names.")
    if not params.hero or not params.darling:
        raise StoryError("Both characters need names.")


def build_world(params: StoryParams) -> World:
    validate_params(params)
    world = World(params)
    if params.path == "lantern":
        world.entities["object"] = Entity(
            "object", "a little lantern", "thing", "sideboard",
            meters={"light": 0}, memes={"comfort": 0.0})
    elif params.path == "cake":
        world.entities["object"] = Entity(
            "object", "a covered cake", "food", "sideboard",
            meters={"slices": 4, "served": 0}, memes={"welcome": 0.0})
    else:
        world.entities["object"] = Entity(
            "object", "a blue envelope", "letter", "sideboard",
            meters={"opened": 0}, memes={"news": 0.0})
    return world


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    hero, darling = params.hero, params.darling
    obj = world.entities["object"]

    world.scene(
        f"In the dining room, {hero} found {darling} waiting beside the table. "
        f"A small quest had begun, but the quiet room made every little sound feel important."
    )

    if params.path == "lantern":
        world.scene(
            f"The dining-room lamp flickered, and the sideboard became a patch of shadow. "
            f"{hero} saw {obj.label} there, but its wick was cold. "
            f"{hero} wondered whether to light it alone or wait for help."
        )
        world.say("hero", "Did you put the lantern away, darling?")
        world.say("darling", "I did, but I cannot reach its matches. The dark makes me nervous.")
        world.entities["darling"].beliefs["matches"] = "in_drawer"
        world.entities["hero"].beliefs["matches"] = "in_drawer"
        world.scene(
            f"{hero} listened and learned that the matches were in the low drawer, not on the high shelf. "
            f"The suspense loosened when {darling} pointed to the drawer's moon-shaped handle.",
            question="Why did the quest seem difficult at first?",
            cause=f"The lamp was flickering and {darling} was nervous in the dark.",
            result="They needed to find the matches and light the lantern safely."
        )
        world.say("hero", "I will open the low drawer, and you can hold my sleeve.")
        world.say("darling", "Then I will know where you are.")
        world.entities["hero"].beliefs["plan"] = "light_together"
        world.entities["darling"].beliefs["plan"] = "light_together"
        world.scene(
            f"{hero} decided to bring {darling} along instead of rushing ahead. "
            f"Together they found the matches, lit the lantern, and set it in the middle of the table. "
            f"The warm circle of light reached both of their hands.",
            question="What did {hero} decide to do?",
            cause=f"{darling} explained that the matches were in the low drawer and that the dark felt scary.",
            result=f"{hero} decided to open the drawer while {darling} held onto {hero}'s sleeve."
        )
        obj.meters["light"] = 1
        obj.location = "table"
        obj.memes["comfort"] = 1.0
        world.say("darling", "The table looks ready for us now.")
        world.say("hero", "And the shadows do not get to choose our quest.")
        world.scene(
            f"The lantern glowed beside the plates, and {hero} and {darling} sat close together at the dining table. "
            f"The room was still quiet, but now its golden light made the quiet feel safe."
        )

    elif params.path == "cake":
        world.scene(
            f"A delicious smell curled around the dining room. "
            f"On the sideboard waited {obj.label}, while a soft thump came from beneath the table. "
            f"{hero} felt suspense prickle at the back of their neck."
        )
        world.say("hero", "Darling, did you hear that thump?")
        world.say("darling", "Yes. I hid the cake because I thought our guest had forgotten us.")
        world.entities["darling"].beliefs["cake_reason"] = "guest_late"
        world.entities["hero"].beliefs["cake_reason"] = "guest_late"
        world.scene(
            f"{hero} learned that {darling} had not been saving the cake selfishly. "
            f"{darling} was worried that their guest, Aunt Rose, would arrive late and find no welcome waiting.",
            question="Why had {darling} hidden the cake?",
            cause=f"{darling} feared that Aunt Rose would arrive late and miss the welcome.",
            result=f"{hero} understood that the hidden cake was meant to make the guest feel remembered."
        )
        world.say("hero", "We can decide together. Shall we save one slice and serve the rest?")
        world.say("darling", "Yes, and we can leave the slice under a clean cover for Aunt Rose.")
        world.entities["hero"].beliefs["plan"] = "share_and_save"
        world.entities["darling"].beliefs["plan"] = "share_and_save"
        world.scene(
            f"{hero} decided not to snatch the cake or scold {darling}. "
            f"They carried the plate to the table, served three slices, and covered the last slice with a bright bowl. "
            f"Then they placed a welcome card beside it.",
            question="How did {hero} solve the cake problem?",
            cause=f"{hero} learned that {darling} had hidden the cake because the guest might arrive late.",
            result="They shared three slices and saved one covered slice with a welcome card."
        )
        obj.meters["served"] = 3
        obj.location = "table"
        obj.memes["welcome"] = 1.0
        world.say("darling", "Now the table says, 'Come in,' even before Aunt Rose arrives.")
        world.say("hero", "That is a very sweet kind of waiting.")
        world.scene(
            f"The covered slice sat beside the welcome card, and three friends shared cake at the dining table. "
            f"When the front door finally opened, the whole room seemed to smile before anyone spoke."
        )

    else:
        world.scene(
            f"{hero} noticed {obj.label} trembling under a plate on the sideboard. "
            f"No one had written a name on it, and the ticking clock made the dining room feel full of suspense."
        )
        world.say("hero", "Darling, is this mysterious envelope yours?")
        world.say("darling", "It is, but I cannot decide whether to open it. It might change dinner.")
        world.entities["darling"].beliefs["fear"] = "news_about_grandma"
        world.entities["hero"].beliefs["fear"] = "news_about_grandma"
        world.scene(
            f"{hero} learned that {darling} was afraid the letter carried news about Grandma's journey. "
            f"Instead of grabbing it, {hero} waited until {darling} was ready to know the truth.",
            question="What information did {hero} learn about the envelope?",
            cause=f"{darling} explained that it might contain news about Grandma's journey.",
            result=f"{hero} understood why {darling} felt afraid to open it."
        )
        world.say("hero", "You do not have to open it alone. We can read it together at the table.")
        world.say("darling", "All right. Your hand can stay beside mine.")
        world.entities["hero"].beliefs["plan"] = "read_together"
        world.entities["darling"].beliefs["plan"] = "read_together"
        world.scene(
            f"{hero} decided that kindness mattered more than satisfying curiosity. "
            f"At the dining table, {darling} opened the envelope while {hero} kept a hand nearby. "
            f"The letter said Grandma's train was late, but she was safe and would arrive after supper.",
            question="Why did {hero} wait before opening the letter?",
            cause=f"{darling} was afraid the letter might contain troubling news about Grandma.",
            result=f"{hero} waited so they could read it together and help {darling} face the answer."
        )
        obj.meters["opened"] = 1
        obj.location = "table"
        obj.memes["news"] = 1.0
        world.say("darling", "I was scared of the waiting, not of the letter.")
        world.say("hero", "Then we can wait together, with room for one more plate.")
        world.scene(
            f"They set an extra plate at the dining table for Grandma. "
            f"The envelope lay open beside the salt, and {darling}'s shoulders relaxed as the two friends began supper."
        )

    check_sample(world.sample())
    return world.sample()


def check_sample(sample: StorySample):
    world = sample.world
    params = sample.params
    if not any(event.kind == "speech" and event.speaker == "hero" for event in world.history):
        raise StoryError("The hero must speak.")
    if not any(event.kind == "speech" and event.speaker == "darling" for event in world.history):
        raise StoryError("The darling must speak.")
    if not world.entities["hero"].beliefs.get("plan"):
        raise StoryError("The hero must make a decided plan.")
    if world.entities["darling"].beliefs.get("plan") != world.entities["hero"].beliefs["plan"]:
        raise StoryError("The characters must share the decided plan.")
    obj = world.entities["object"]
    if params.path == "lantern" and (obj.location != "table" or obj.meters["light"] != 1):
        raise StoryError("The lantern quest did not resolve.")
    if params.path == "cake" and (obj.location != "table" or obj.meters["served"] != 3):
        raise StoryError("The cake quest did not resolve.")
    if params.path == "letter" and (obj.location != "table" or obj.meters["opened"] != 1):
        raise StoryError("The letter quest did not resolve.")
    if len(sample.story_qa) < 2:
        raise StoryError("The story needs grounded questions and answers.")


ASP_RULES = """
valid(lantern,light_together).
valid(cake,share_and_save).
valid(letter,read_together).
#show valid/2.
"""


def asp_facts() -> str:
    from asp import fact
    return "\n".join(fact("path", path) for path in PATHS)


def asp_combos() -> set[tuple[str, str]]:
    from asp import atoms, one_model
    return set(atoms(one_model(asp_facts() + "\n" + ASP_RULES), "valid"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--hero")
    parser.add_argument("--darling")
    parser.add_argument("--path", choices=PATHS)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(NAMES)
    darling = args.darling or rng.choice(tuple(n for n in DARLINGS if n != hero))
    path = args.path or rng.choice(PATHS)
    params = StoryParams(hero=hero, darling=darling, path=path, seed=args.seed)
    validate_params(params)
    return params


def verify():
    if asp_combos() != {
        ("lantern", "light_together"),
        ("cake", "share_and_save"),
        ("letter", "read_together"),
    }:
        raise StoryError("ASP and Python story paths disagree.")
    count = 0
    for path in PATHS:
        sample = generate(StoryParams(path=path))
        check_sample(sample)
        count += 1
    print(f"OK: {count} story paths verified.")


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = ""):
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
            paths = [path for path in PATHS if args.path is None or path == args.path]
            if not paths:
                raise StoryError("No story paths match the selected options.")
            params_list = [
                resolve_params(argparse.Namespace(**vars(args), path=path), rng)
                for path in paths
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


if __name__ == "__main__":
    raise SystemExit(main())
