#!/usr/bin/env python3
"""
A small child-facing mystery world about a scuttle, a contrived clue, and a
surprising explanation.
"""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class StoryState:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    place: str
    hero_name: str
    friend_name: str
    seed: Optional[int] = None
    mystery: int = 0
    opening: int = 0
    question: int = 0
    discovery: int = 0


SETTINGS = {
    "courtyard": Setting("the courtyard", {"scuttle", "observe"}),
    "library": Setting("the library", {"scuttle", "search"}),
    "greenhouse": Setting("the greenhouse", {"scuttle", "observe"}),
}

HERO_NAMES = ["Luna", "Mira", "Theo", "Iris", "Nico", "Sana"]
FRIEND_NAMES = ["Pip", "Jo", "Remy", "Bea", "Ollie", "Tess"]

MYSTERIES = [
    {
        "clue": "three silver buttons arranged in a careful line",
        "guess": "someone had left a secret trail",
        "sound": "a tiny scuttle sounded behind the flower boxes",
        "want": "follow the trail at once",
        "evidence": "the buttons all had damp soil on one side, while a little wheel track crossed the floor",
        "answer": "a wind-up beetle toy had rolled through the soil and dropped the buttons from its costume",
        "repair": "They cleaned the buttons, returned the toy to its basket, and swept the track away.",
        "surprise": "The mysterious trail had been contrived by a toy beetle, not by a secret visitor.",
        "ending": "When the toy beetle scuttled into its basket, the silver buttons glittered like a solved riddle.",
        "lesson": "a neat clue can be made to look more mysterious than it is",
    },
    {
        "clue": "a blue ribbon tied around the old watering can",
        "guess": "the ribbon marked a hidden message",
        "sound": "something scuttled beneath the can",
        "want": "lift the can quickly and read the message underneath",
        "evidence": "the knot matched a bow on the caretaker's tool cart, and a trail of seeds led toward it",
        "answer": "a curious mouse had dragged the ribbon while carrying seeds",
        "repair": "They set the can on a steady shelf, left the mouse a clear path, and told the caretaker what they found.",
        "surprise": "The ribbon had looked like a warning, but it was only part of a mouse's busy route.",
        "ending": "The watering can rested safely while the mouse scuttled home through a crack in the wall.",
        "lesson": "a small creature may be part of a mystery without being a danger",
    },
    {
        "clue": "a row of chalk arrows pointing toward a locked cupboard",
        "guess": "a hidden explorer had contrived a treasure hunt",
        "sound": "a soft scuttle came from inside the cupboard",
        "want": "try the handle before asking anyone",
        "evidence": "the arrows stopped at a loose chalk box, and the cupboard key hung in plain sight by the desk",
        "answer": "the wind had rolled the chalk box across the floor, making accidental arrows",
        "repair": "They left the cupboard locked, returned the key, and placed the chalk in a heavy tray.",
        "surprise": "The treasure map was an accident made by a rolling box and a draft.",
        "ending": "The chalk arrows were gone, but the cupboard still stood quietly beside the desk.",
        "lesson": "an exciting pattern may be accidental",
    },
    {
        "clue": "a paper moon dangling from a branch",
        "guess": "someone had contrived a signal in the night",
        "sound": "leaves scuttled along the path",
        "want": "climb the low branch to grab the moon",
        "evidence": "the paper was fastened with classroom string, and tiny footprints circled the tree",
        "answer": "a younger child had made a play moon, while squirrels had tugged the string",
        "repair": "They called for the teacher, lowered the paper moon with a long hook, and moved it to a safe display board.",
        "surprise": "The signal was really a pretend moon shaken by squirrels.",
        "ending": "The paper moon shone from its new board while the squirrels scuttled through the leaves.",
        "lesson": "asking for help protects both people and fragile clues",
    },
]

OPENINGS = [
    "{hero} and {friend} were crossing {place} when {hero} noticed something that did not belong.",
    "Rain had just stopped in {place}, and {hero} was showing {friend} how to notice clues without touching them.",
    "At the quietest part of the afternoon, {hero} and {friend} heard a strange sound in {place}.",
    "{hero} carried a small notebook through {place}; {friend} carried the questions.",
]

QUESTIONS = [
    '"What do you know for certain?" {hero} asked. "{friend}, tell me only what you saw."',
    '"Should we rush in?" {friend} asked. "No," said {hero}. "A mystery deserves careful feet."',
    '"Could the clue have another cause?" {hero} wondered. {friend} looked again instead of guessing.',
    '"We can investigate without disturbing anything," {hero} said. "Let us find one more fact."',
]


ASP_RULES = r"""
#show valid/2.
setting(courtyard). setting(library). setting(greenhouse).
affords(courtyard,scuttle). affords(courtyard,observe).
affords(library,scuttle). affords(library,search).
affords(greenhouse,scuttle). affords(greenhouse,observe).
valid(P,A) :- setting(P), affords(P,A).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for name, setting in SETTINGS.items():
        lines.append(asp.fact("setting", name))
        for action in sorted(setting.affords):
            lines.append(asp.fact("affords", name, action))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def python_valid() -> list[tuple[str, str]]:
    return sorted((place, action) for place, setting in SETTINGS.items() for action in setting.affords)


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    expected = set(python_valid())
    actual = set(asp_valid())
    if expected == actual:
        print(f"OK: clingo gate matches python gate ({len(expected)} combinations).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("  only in clingo:", sorted(actual - expected))
    print("  only in Python:", sorted(expected - actual))
    return 1


def build_world(params: StoryParams) -> StoryState:
    if params.place not in SETTINGS:
        raise StoryError(f"Unknown place: {params.place}")
    setting = SETTINGS[params.place]
    mystery = MYSTERIES[params.mystery % len(MYSTERIES)]
    world = StoryState(setting)

    hero = world.add(Entity(
        params.hero_name, "character", "child",
        meters={"alertness": 0.8, "distance_to_clue": 2.0},
        memes={"curiosity": 0.7, "caution": 0.8},
    ))
    friend = world.add(Entity(
        params.friend_name, "character", "child",
        meters={"alertness": 0.7, "distance_to_clue": 2.0},
        memes={"curiosity": 0.9, "patience": 0.4},
    ))
    clue = world.add(Entity(
        "clue", "thing", "mystery_clue",
        label=mystery["clue"],
        meters={"distance_to_path": 1.0},
        memes={"mystery": 0.9},
    ))
    world.facts.update(hero=hero, friend=friend, clue=clue, mystery=mystery)

    world.say(OPENINGS[params.opening % len(OPENINGS)].format(
        hero=hero.id, friend=friend.id, place=setting.place
    ))
    world.say(f"There, they found {mystery['clue']}.")
    world.say(
        f'"Perhaps {mystery["guess"]}," said {friend.id}. '
        f'"Perhaps," replied {hero.id}, "but a guess is not an answer."'
    )

    world.para()
    world.say(f"Then {mystery['sound']}. {friend.id} wanted to {mystery['want']}.")
    world.say(QUESTIONS[params.question % len(QUESTIONS)].format(
        hero=hero.id, friend=friend.id
    ))
    world.say(
        f"They stayed on the clear path and noticed that {mystery['evidence']}."
    )
    world.say(
        f'{hero.id} pointed to the new clue. "Let us test the simplest explanation." '
        f'"That is a clever plan," {friend.id} said.'
    )
    hero.memes["caution"] = 1.0
    friend.memes["patience"] = 0.9
    world.facts["tension"] = True

    world.para()
    world.say(f"The caretaker arrived and listened. The surprise was that {mystery['answer']}.")
    world.say(mystery["repair"])
    world.say(
        f'"So the mystery was contrived by ordinary things," {friend.id} said. '
        f'"And careful noticing showed us how," {hero.id} replied.'
    )
    world.say(f"{mystery['surprise']} They smiled because the safe answer was more wonderful than the first guess.")
    world.say(
        f'{friend.id} learned that {mystery["lesson"]}, and the two friends left {setting.place} together.'
    )
    world.say(mystery["ending"])
    return world


def generation_prompts(world: StoryState) -> list[str]:
    mystery = world.facts["mystery"]
    return [
        f"Write a child-friendly mystery about {mystery['clue']}.",
        "Include a scuttle, a careful investigation, dialogue, and a surprising ordinary explanation.",
        "Show how characters contrive a safe test instead of rushing toward a mysterious clue.",
    ]


def story_qa(world: StoryState) -> list[QAItem]:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    mystery = world.facts["mystery"]
    place = world.setting.place
    return [
        QAItem(
            f"What clue did {hero.id} and {friend.id} notice in {place}?",
            f"They noticed {mystery['clue']}. They examined it from the clear path rather than disturbing it.",
        ),
        QAItem(
            f"What did {friend.id} first guess?",
            f"{friend.id} guessed that {mystery['guess']}, but that was only an exciting possibility.",
        ),
        QAItem(
            "What evidence changed their minds?",
            f"They found that {mystery['evidence']}. That clue pointed toward a safer, ordinary explanation.",
        ),
        QAItem(
            "What was the surprise?",
            f"The surprise was that {mystery['answer']}. The mystery came from ordinary movement, not a dangerous visitor.",
        ),
        QAItem(
            f"What did {friend.id} learn?",
            f"{friend.id} learned that {mystery['lesson']}. Careful observation helped both friends solve the mystery safely.",
        ),
    ]


def world_knowledge_qa(world: StoryState) -> list[QAItem]:
    return [
        QAItem(
            "What does scuttle mean?",
            "To scuttle means to move quickly with short steps, often like a small animal or insect.",
        ),
        QAItem(
            "What does contrive mean?",
            "To contrive means to plan or arrange something, often by using a clever method.",
        ),
        QAItem(
            "Why is it useful to check clues before touching them?",
            "Checking clues first can keep people safe and preserve the evidence needed to understand what happened.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: StoryState) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id:10} ({entity.type:14}) "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  setting: {world.setting.place}")
    lines.append(f"  facts: tension={world.facts.get('tension', False)}")
    return "\n".join(lines)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    if place not in SETTINGS:
        raise StoryError(f"Unknown place: {place}")
    hero = args.name or rng.choice(HERO_NAMES)
    friend = args.friend or rng.choice(FRIEND_NAMES)
    if hero == friend:
        friend = rng.choice([name for name in FRIEND_NAMES if name != hero])
    return StoryParams(
        place=place,
        hero_name=hero,
        friend_name=friend,
        mystery=rng.randrange(len(MYSTERIES)),
        opening=rng.randrange(len(OPENINGS)),
        question=rng.randrange(len(QUESTIONS)),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A mystery storyworld about scuttling clues and surprising explanations."
    )
    parser.add_argument("--place", choices=SETTINGS)
    parser.add_argument("--name")
    parser.add_argument("--friend")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combinations = asp_valid()
        print(f"{len(combinations)} valid combinations:\n")
        for place, action in combinations:
            print(f"  {place:12} {action}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in SETTINGS:
            params = StoryParams(
                place=place,
                hero_name=f"{place.title()}Luna",
                friend_name=f"{place.title()}Friend",
                mystery=list(SETTINGS).index(place) % len(MYSTERIES),
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < max(0, args.n) and attempt < max(50, args.n * 20):
            rng = random.Random(base_seed + attempt)
            attempt += 1
            params = resolve_params(args, rng)
            params.seed = base_seed + attempt
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
