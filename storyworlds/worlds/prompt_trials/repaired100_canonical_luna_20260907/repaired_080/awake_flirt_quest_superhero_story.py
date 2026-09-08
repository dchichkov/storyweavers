#!/usr/bin/env python3
"""
Standalone storyworld: an awake flirt quest in a superhero story.

Luna discovers that being awake to another person's feelings can turn a
seemingly silly flirt into a brave, respectful quest to help a city.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class World:
    city: str
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def get(self, entity_id: str) -> Entity:
        if entity_id not in self.entities:
            raise StoryError(f"Unknown entity: {entity_id}")
        return self.entities[entity_id]

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
    hero_name: str
    friend_name: str
    city: str = "Starbridge"
    quest: int = 0
    opening: int = 0
    flirt: int = 0
    ending: int = 0
    seed: Optional[int] = None


HERO_NAMES = ["Luna", "Nova", "Mira", "Zara", "Tess", "Ari"]
FRIEND_NAMES = ["Kai", "Jules", "Robin", "Sam", "Eli", "Pax"]
GIRL_NAMES = {"Luna", "Nova", "Mira", "Zara", "Tess"}
BOY_NAMES = {"Kai", "Eli", "Pax"}

CITIES = ["Starbridge", "Brightfall", "Moonport", "Cloudhaven", "Sunspire"]

QUESTS = [
    {
        "danger": "a runaway storm-drone was circling the school tower",
        "clue": "tiny blue feathers stuck to the drone's propeller",
        "plan": "followed the feather trail to the roof garden",
        "help": "the rooftop pigeons had carried away its guiding ribbon",
        "repair": "returned the ribbon, slowed the drone with a gentle signal, and guided it back to its charging nest",
        "result": "the storm-drone began sprinkling rain only on the thirsty garden beds",
        "image": "a rainbow arched over the school while the rescued drone hummed like a happy bee",
        "lesson": "A hero stays awake to small clues and listens before rushing into danger.",
    },
    {
        "danger": "the moon-powered bridge had gone dark during the evening rush",
        "clue": "a trail of silver buttons led beneath the bridge",
        "plan": "crawled carefully along the maintenance path beneath the river",
        "help": "a parade robot had borrowed the buttons as decorations and jammed the light panel",
        "repair": "removed the buttons, reset the panel, and taught the robot to ask before borrowing",
        "result": "the bridge shone again, and every traveler crossed safely",
        "image": "the bright bridge reflected in the river like a long silver smile",
        "lesson": "Awareness turns a confusing problem into a solvable one, especially when kindness guides the repair.",
    },
    {
        "danger": "a giant comic-book balloon was tugging loose from the city festival",
        "clue": "its golden string was caught on the bell of the old clock tower",
        "plan": "climbed the tower with a safety line while the crowd moved to a clear square",
        "help": "the festival wind had twisted the string around the bell",
        "repair": "freed the string, tied a stronger knot, and lowered the balloon before it could drift away",
        "result": "children received their festival hero balloon without anyone getting hurt",
        "image": "the balloon floated above the square, its painted star glowing in the sunset",
        "lesson": "A superpower matters most when it protects people and notices what they need.",
    },
    {
        "danger": "the city library's story-lights were flashing messages from every window",
        "clue": "one blinking pattern matched the rhythm of a trapped elevator bell",
        "plan": "checked the library's quiet service hall instead of guessing from the street",
        "help": "a sleepy maintenance cat had stepped on the emergency panel",
        "repair": "freed the panel, thanked the cat, and reset the lights to spell a calm all-clear",
        "result": "the readers returned to their books and the elevator opened safely",
        "image": "every library window glowed with one peaceful word: WELCOME",
        "lesson": "Staying awake to what others say can reveal a problem hidden behind a bright display.",
    },
]

OPENINGS = [
    "At dawn, the city woke beneath clouds shaped like enormous capes.",
    "One bright afternoon, the rooftops glittered as if the sun had dropped a sack of stars.",
    "At sunset, every window in the city flashed orange, and even the pigeons looked heroic.",
    "Before breakfast, the city siren sang one polite note and then fell mysteriously silent.",
    "On a breezy morning, the skyline wore a scarf of golden fog.",
]

FLIRT_LINES = [
    '"You look heroic when you are thinking," said {friend}, then quickly looked at the pavement.',
    '"If bravery had a smile, it might look like yours," {friend} said.',
    '"I saved you the brightest signal flare," said {friend}. "That may be a tiny flirt, but it is a sincere one."',
    '"You make impossible missions look almost cheerful," {friend} told {hero}.',
    '"I like how you notice everyone," said {friend}. "That is a very attractive superpower."',
]

RESPONSES = [
    '"Then stay beside me and help me notice the next clue," said {hero}.',
    '"Thank you," said {hero}. "Your honest words make me braver, not distracted."',
    '"That is kind," {hero} replied. "Let us save the city first, and celebrate afterward."',
    '"I was awake enough to hear that," said {hero} with a grin.',
    '"You can flirt after we make a safe plan," {hero} said. "Deal?"',
]

ENDINGS = [
    "When the danger passed, Luna and her friend shared a warm drink beneath the first evening star.",
    "The city cheered, but the two heroes mostly smiled at each other beside the quiet control panel.",
    "Afterward, they wrote the clue in the team notebook and drew two stars beside it.",
    "The rescued machine blinked once, as if it understood that teamwork could be dazzling.",
    "From that night on, the city called careful listening a superpower of its own.",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate an awake, flirty superhero quest story.")
    parser.add_argument("--hero-name")
    parser.add_argument("--friend-name")
    parser.add_argument("--city", default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        hero_name=args.hero_name or rng.choice(HERO_NAMES),
        friend_name=args.friend_name or rng.choice(FRIEND_NAMES),
        city=args.city or rng.choice(CITIES),
        quest=rng.randrange(len(QUESTS)),
        opening=rng.randrange(len(OPENINGS)),
        flirt=rng.randrange(len(FLIRT_LINES)),
        ending=rng.randrange(len(ENDINGS)),
    )


def build_world(params: StoryParams) -> World:
    hero_type = "girl" if params.hero_name in GIRL_NAMES else "boy" if params.hero_name in BOY_NAMES else "person"
    friend_type = "girl" if params.friend_name in GIRL_NAMES else "boy" if params.friend_name in BOY_NAMES else "person"
    world = World(params.city)
    hero = world.add(Entity("Hero", "character", hero_type, params.hero_name))
    friend = world.add(Entity("Friend", "character", friend_type, params.friend_name))
    threat = world.add(Entity("Threat", "danger", "machine", "the city danger"))
    world.facts.update(hero=hero, friend=friend, threat=threat, params=params)
    return world


def tell(world: World) -> None:
    params: StoryParams = world.facts["params"]
    hero: Entity = world.facts["hero"]
    friend: Entity = world.facts["friend"]
    quest = QUESTS[params.quest % len(QUESTS)]
    world.facts["quest"] = quest

    world.say(OPENINGS[params.opening % len(OPENINGS)])
    world.say(
        f"In {world.city}, {hero.label} was a superhero who could hear a loose hinge squeak from three blocks away. "
        f"{friend.label} was their quick-thinking partner, carrying a bright blue rescue scarf."
    )
    world.say(
        f"They were both wide awake when {quest['danger']}. The city needed a quest, and the two heroes were ready."
    )

    world.para()
    hero.memes["awake"] = 1
    friend.memes["awake"] = 1
    world.say(f"{hero.label} did not charge forward. {hero.pronoun()} noticed that {quest['clue']}.")
    world.say(f"That small clue changed the plan: they {quest['plan']}.")
    world.say(
        FLIRT_LINES[params.flirt % len(FLIRT_LINES)].format(hero=hero.label, friend=friend.label)
    )
    world.say(
        RESPONSES[params.flirt % len(RESPONSES)].format(hero=hero.label, friend=friend.label)
    )
    friend.memes["flirt"] = 1

    world.para()
    world.say(f"At the heart of the problem, they learned that {quest['help']}.")
    world.say(
        f"Because {hero.label} stayed awake to the evidence and {friend.label} stayed close, they {quest['repair']}."
    )
    threat.meters["resolved"] = 1
    hero.memes["brave"] = 1
    friend.memes["trust"] = 1
    world.say(f"At once, {quest['result']}.")
    world.say(
        f'"You were right to notice the little thing," said {friend.label}. '
        f'"And you were right to make room for my idea," {hero.label} replied.'
    )

    world.para()
    world.say(quest["lesson"])
    world.say(f"In the final sight, {quest['image']}.")
    world.say(ENDINGS[params.ending % len(ENDINGS)])
    world.facts.update(
        resolved=True,
        clue=quest["clue"],
        help=quest["help"],
        repair=quest["repair"],
        result=quest["result"],
        image=quest["image"],
    )


def generation_prompts(world: World) -> list[str]:
    params: StoryParams = world.facts["params"]
    quest = world.facts["quest"]
    return [
        f"Write a child-friendly superhero story about {params.hero_name} and {params.friend_name} on an awake quest in {params.city}.",
        f"Include a gentle flirt that changes how the heroes cooperate, then resolve this danger: {quest['danger']}.",
        f"Use the clue '{quest['clue']}' to make the quest causal, brave, and hopeful.",
    ]


def story_qa(world: World) -> list[QAItem]:
    params: StoryParams = world.facts["params"]
    hero: Entity = world.facts["hero"]
    friend: Entity = world.facts["friend"]
    quest = world.facts["quest"]
    return [
        QAItem(
            question=f"What danger did {hero.label} and {friend.label} face?",
            answer=f"They faced {quest['danger']}, which threatened people in {params.city}.",
        ),
        QAItem(
            question="What clue did the heroes notice?",
            answer=f"They noticed that {quest['clue']}. The clue helped them choose a safer plan.",
        ),
        QAItem(
            question=f"How did {friend.label}'s flirt affect the quest?",
            answer=f"{friend.label} offered a kind, honest flirt, and the exchange made the partners trust one another while they worked.",
        ),
        QAItem(
            question="How was the problem repaired?",
            answer=f"The heroes learned that {quest['help']}, then they {quest['repair']}.",
        ),
        QAItem(
            question="How did the ending show that the quest succeeded?",
            answer=f"The danger was resolved: {quest['result']}. The final image was that {quest['image']}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a superhero?",
            answer="A superhero is a person with unusual abilities or courage who uses them to help and protect others.",
        ),
        QAItem(
            question="What does awake mean?",
            answer="Awake means alert and not asleep, ready to notice what is happening.",
        ),
        QAItem(
            question="What does flirt mean?",
            answer="To flirt means to show gentle romantic interest through kind, playful, or admiring words.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a purposeful journey or mission to solve a problem or reach an important goal.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---", f"city: {world.city}"]
    for entity in world.entities.values():
        details = []
        if entity.meters:
            details.append(f"meters={entity.meters}")
        if entity.memes:
            details.append(f"memes={entity.memes}")
        lines.append(f"{entity.id}: {' '.join(details) if details else '(quiet)'}")
    return "\n".join(lines)


ASP_RULES = r"""
awake(hero).
awake(friend).
flirt(friend).
quest(active).
noticed(hero) :- awake(hero), quest(active).
trust(friend) :- flirt(friend), noticed(hero).
resolved :- trust(friend), repaired.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("awake", "hero"),
            asp.fact("awake", "friend"),
            asp.fact("flirt", "friend"),
            asp.fact("quest", "active"),
            asp.fact("repaired"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(
        asp_program(
            "#show noticed/1. #show trust/1. #show resolved/0."
        )
    )
    atom_text = {str(atom) for atom in model}
    required = {"noticed(hero)", "trust(friend)", "resolved"}
    if not required.issubset(atom_text):
        raise StoryError("ASP parity failed: awake/flirt quest resolution atoms were missing")
    for params in CURATED:
        sample = generate(params)
        if not sample.world or not sample.world.facts.get("resolved"):
            raise StoryError("Python verification failed: curated story did not resolve")
        if "awake" not in sample.story.lower() and "wide awake" not in sample.story.lower():
            raise StoryError("Python verification failed: story omitted awake state")
        if "flirt" not in sample.story.lower():
            raise StoryError("Python verification failed: story omitted flirt state")
    print("OK: ASP and Python parity verified across curated stories.")
    return 0


def asp_valid() -> str:
    return asp_program("#show noticed/1. #show trust/1. #show resolved/0.")


CURATED = [
    StoryParams("Luna", "Kai", "Starbridge", 0, 0, 0, 0),
    StoryParams("Nova", "Jules", "Moonport", 1, 2, 2, 1),
    StoryParams("Mira", "Robin", "Cloudhaven", 2, 3, 4, 3),
    StoryParams("Zara", "Sam", "Brightfall", 3, 1, 1, 4),
]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def emit(
    sample: StorySample,
    *,
    trace: bool = False,
    qa: bool = False,
    header: str = "",
) -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show noticed/1. #show trust/1. #show resolved/0."))
        return

    if args.verify:
        try:
            raise SystemExit(asp_verify())
        except ImportError as exc:
            raise SystemExit(f"ASP verification requires clingo: {exc}")

    if args.asp:
        try:
            import asp
            model = asp.one_model(asp_valid())
        except ImportError as exc:
            raise SystemExit(f"ASP mode requires clingo: {exc}")
        print("\n".join(str(atom) for atom in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < max(1, args.n):
            seed = base_seed + index
            index += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
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
        header = ""
        if args.all:
            header = f"### {sample.params.hero_name} and {sample.params.friend_name} in {sample.params.city}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
