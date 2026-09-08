#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


PLACES = {
    "bedroom": {
        "setting": "the moonlit bedroom",
        "objects": ("a tall bed", "a brass alarm clock", "a blue quilt", "a wooden wardrobe"),
    }
}
CHAR_NAMES = ("Luna", "Milo", "Nora", "Pip", "Tessa", "Jasper")
MOODS = ("bold", "curious", "patient", "watchful")
MYSTERIES = (
    {
        "title": "the vanished vote",
        "opening": "One enormous morning, Luna woke to find the golden star missing from the wall above her bed.",
        "flashback": "The night before, she had pinned the star there after every child in the house chose it as the bedroom's brightest treasure.",
        "clue": "a trail of silver thread ran from the wall to the wardrobe",
        "discovery": "the star had been caught on the wardrobe's tallest wooden antler",
        "action": "used the quilt as a safe landing cloth and coaxed the star down with a long ribbon",
        "result": "the star returned to the wall, where it shone over a new list naming every child's choice",
        "lesson": "a fair choice must be heard by everyone, even when one voice is very loud",
        "ending": "That night the star shone so fiercely that the bedroom moon asked it to dim its sparkle.",
        "sound": "clink",
    },
    {
        "title": "the locked toy council",
        "opening": "At breakfast time, the bedroom toys discovered that their tiny meeting box had vanished.",
        "flashback": "The evening before, Luna had promised that every toy could suggest one rule for the next day's grand pillow fort.",
        "clue": "a red button lay beneath the bed beside two fresh wheel tracks",
        "discovery": "the box had rolled into the shadow behind the rocking horse",
        "action": "asked the smallest toys to speak first and pulled the box out with a broom handle",
        "result": "the council opened again, and even the quietest wooden soldier got a turn",
        "lesson": "no one should be pushed aside just because they are small or hard to hear",
        "ending": "The pillow fort rose so high that its flag brushed the ceiling, but its door stayed wide for everyone.",
        "sound": "roll-roll",
    },
    {
        "title": "the thunderous missing key",
        "opening": "A thunderous crash shook the bedroom, and the little brass key to the memory drawer disappeared.",
        "flashback": "Before sleep, Luna had placed the key beside a drawing from the first day she had learned to read.",
        "clue": "a line of dust crossed the rug toward the alarm clock",
        "discovery": "the clock's spring had kicked the key behind its round brass back",
        "action": "turned off the clock, lifted it carefully, and returned the key to the drawer",
        "result": "the old drawing came out, and Luna remembered that every beginner deserves patient help",
        "lesson": "a mystery is easier when we remember what happened before the trouble began",
        "ending": "The clock ticked softly, as if it too had learned to give people time.",
        "sound": "boom",
    },
)

OPENINGS = (
    "In a bedroom taller than a mountain and twice as cozy, a remarkable mystery began.",
    "The bedroom had ordinary walls, but that morning its smallest clue looked enormous.",
    "Long ago, in a bedroom where socks marched like soldiers, Luna found a puzzle.",
    "The moon leaned through the window and saw that something important was missing.",
)
DIALOGUES = (
    ("I know who did it!", "A guess is not proof. Let us ask what the room remembers."),
    ("My voice should decide first!", "A fair mystery gives every voice a chance."),
    ("The clue is tiny!", "Then we must look carefully, not loudly."),
    ("I remember everything!", "Tell us what happened before the mystery began."),
)


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    type: str = "thing"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    location: Optional[str] = None
    carried_by: Optional[str] = None


@dataclass
class StoryParams:
    place: str
    hero: str
    helper: str
    mood: str
    seed: Optional[int] = None


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


ASP_RULES = r"""
kind(flashback).
kind(mystery_to_solve).
kind(dialogue).
kind(tall_tale).
kind(disenfranchise).
setting(bedroom).
valid_story :- setting(bedroom), kind(flashback), kind(mystery_to_solve), kind(dialogue).
#show valid_story/0.
#show setting/1.
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A tall bedroom mystery about remembering every voice.")
    parser.add_argument("--place", choices=PLACES, default=None)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("setting", "bedroom"),
            asp.fact("kind", "flashback"),
            asp.fact("kind", "mystery_to_solve"),
            asp.fact("kind", "dialogue"),
            asp.fact("kind", "tall_tale"),
            asp.fact("kind", "disenfranchise"),
        ]
    )


def asp_program(show: str = "#show valid_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    valid = bool(asp.atoms(model, "valid_story"))
    if valid:
        print("OK: ASP accepts the bedroom flashback mystery.")
        return 0
    print("MISMATCH: ASP rejected the valid story.")
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or "bedroom"
    if place != "bedroom":
        raise StoryError("This domain is intentionally set in a bedroom.")
    hero = rng.choice(CHAR_NAMES)
    helper = rng.choice([name for name in CHAR_NAMES if name != hero])
    return StoryParams(place=place, hero=hero, helper=helper, mood=rng.choice(MOODS))


def _seed(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    raw = "|".join((params.place, params.hero, params.helper, params.mood))
    return int.from_bytes(hashlib.blake2b(raw.encode(), digest_size=8).digest(), "big")


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError("Unknown bedroom setting.")
    seed = _seed(params)
    rng = random.Random(seed)
    mystery = MYSTERIES[seed % len(MYSTERIES)]
    opening = OPENINGS[(seed // len(MYSTERIES)) % len(OPENINGS)]
    dialogue = DIALOGUES[(seed // (len(MYSTERIES) * len(OPENINGS))) % len(DIALOGUES)]
    meta = PLACES[params.place]

    hero = Entity(
        id=params.hero,
        kind="character",
        label="mystery solver",
        type="child",
        meters={"reach": 1.0, "attention": 1.0},
        memes={"curiosity": 1.0, "fairness": 0.5},
        location=params.place,
    )
    helper = Entity(
        id=params.helper,
        kind="character",
        label="remembering helper",
        type="child",
        meters={"reach": 0.8, "attention": 1.0},
        memes={"curiosity": 0.8, "fairness": 1.0},
        location=params.place,
    )
    clue = Entity(
        id="silver_clue",
        kind="object",
        label="silver thread",
        type="clue",
        meters={"length": 0.3},
        memes={"importance": 1.0},
        location=params.place,
    )
    world = World(place=meta["setting"], entities={hero.id: hero, helper.id: helper, clue.id: clue})

    world.say(opening)
    world.say(
        f"{params.hero}, a {params.mood} child with a memory as wide as the sky, shared the bedroom with {params.helper}."
    )
    world.say(f"The room held {meta['objects'][0]}, {meta['objects'][1]}, {meta['objects'][2]}, and {meta['objects'][3]}.")
    world.say(mystery["opening"])

    world.para()
    world.say(mystery["flashback"])
    world.say(f"{params.helper} pointed to {mystery['clue']}.")
    world.say(f"'{dialogue[0]},' said {params.hero}. '{dialogue[1]},' answered {params.helper}.")
    world.say(
        f"They did not blame the quietest toy or the nearest shadow. Instead, they reconstructed the evening and followed the clue."
    )
    world.say(f"The evidence revealed that {mystery['discovery']}.")

    world.para()
    world.say(f"Together, {params.hero} and {params.helper} {mystery['action']}.")
    world.say(f"Then {mystery['result']}.")
    world.say(
        f"No one was disenfranchised: every person and toy had a chance to speak, and the mystery was solved by listening rather than shouting."
    )
    world.say(f"The lesson was simple: {mystery['lesson'].capitalize()}.")
    world.say(mystery["ending"])

    hero.meters["attention"] = 1.5
    helper.memes["fairness"] = 1.5
    clue.memes["importance"] = 0.0
    world.trace = [
        "missing_object:noticed",
        f"flashback:remembered:{mystery['flashback']}",
        f"clue:found:{mystery['clue']}",
        f"mystery:solved:{mystery['discovery']}",
        "voices:included",
        f"resolution:{mystery['result']}",
    ]
    world.facts = {
        "setting": "bedroom",
        "title": mystery["title"],
        "flashback": mystery["flashback"],
        "clue": mystery["clue"],
        "discovery": mystery["discovery"],
        "resolution": mystery["result"],
        "lesson": mystery["lesson"],
        "disenfranchise": False,
    }

    prompts = [
        f"Write a Tall Tale bedroom mystery for {params.hero} and {params.helper} using a flashback and dialogue.",
        f"Show how {params.hero} solves {mystery['title']} without disenfranchising any voice.",
        "Tell a child-friendly mystery in which remembering the past reveals a surprising bedroom clue.",
    ]
    story_qa = [
        QAItem(
            question="What went missing in the bedroom mystery?",
            answer=f"{mystery['opening']} The missing object was the important item described at the start of the case.",
        ),
        QAItem(
            question="What did the flashback reveal?",
            answer=f"The flashback showed that {mystery['flashback'].lower()} This earlier event gave the detectives a fair starting point.",
        ),
        QAItem(
            question="What clue helped solve the mystery?",
            answer=f"They found that {mystery['clue']}. Following it revealed that {mystery['discovery']}.",
        ),
        QAItem(
            question="How did the characters avoid disenfranchising anyone?",
            answer=f"They let every person and toy speak before deciding. They solved the mystery by listening rather than allowing the loudest voice to rule.",
        ),
        QAItem(
            question="What lesson did the bedroom mystery teach?",
            answer=f"It taught that {mystery['lesson']}.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a flashback?",
            answer="A flashback is a part of a story that shows something that happened earlier.",
        ),
        QAItem(
            question="What is a mystery to solve?",
            answer="A mystery to solve is a puzzling problem that becomes clearer when characters gather clues and test ideas.",
        ),
        QAItem(
            question="What does disenfranchise mean?",
            answer="To disenfranchise someone means to unfairly take away their chance to participate, speak, or have a say.",
        ),
    ]
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print("--- world trace ---")
        for entity in sample.world.entities.values():
            print(
                f"  {entity.id}: {entity.kind} "
                f"location={entity.location} meters={entity.meters} memes={entity.memes}"
            )
        for item in sample.world.trace:
            print(f"  {item}")
    if qa:
        print("\n== prompts ==")
        for i, prompt in enumerate(sample.prompts, 1):
            print(f"{i}. {prompt}")
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


CURATED = [
    StoryParams("bedroom", "Luna", "Milo", "bold"),
    StoryParams("bedroom", "Nora", "Pip", "curious"),
    StoryParams("bedroom", "Tessa", "Jasper", "patient"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/0.\n#show setting/1."))
        print(asp.atoms(model, "valid_story"))
        print(asp.atoms(model, "setting"))
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        base = args.seed if args.seed is not None else random.randrange(2**31)
        for index in range(args.n):
            rng = random.Random(base + index)
            params = resolve_params(args, rng)
            params.seed = base + index
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {index + 1}" if len(samples) > 1 else "")
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
