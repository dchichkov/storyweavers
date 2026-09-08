#!/usr/bin/env python3
"""
A heartwarming storyworld about Luna, a sociable child, and the joy of sharing
a rhyme with a friend.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    type: str = "thing"
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    held_by: Optional[str] = None


@dataclass
class StoryParams:
    seed: Optional[int] = None
    hero_name: str = "Luna"
    friend_name: str = "Milo"
    place: str = "the little library garden"
    prop: str = "a red paper kite"
    scenario_id: int = 0
    telling_mode: int = 0
    detail_variant: int = 0


@dataclass
class World:
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


PLACES = [
    "the little library garden",
    "the sunny school courtyard",
    "the market square beside the fountain",
    "the hill behind the community hall",
]

HERO_NAMES = ["Luna", "Ari", "Nia", "Maya", "Tessa"]
FRIEND_NAMES = ["Milo", "Sam", "Ollie", "Ben", "Pip"]

PROPS = [
    "a red paper kite",
    "a yellow tin drum",
    "a basket of warm rolls",
    "a blue storybook",
    "a jar of sparkling marbles",
]

SCENARIOS = [
    {
        "title": "the kite song",
        "opening": "Luna carried a red paper kite to the garden, where the breeze made its tail dance",
        "need": "Milo sat beneath the apple tree with no game to play",
        "clue": "the kite's long tail had two loose ribbons",
        "action": "Luna offered one ribbon to Milo and held the other",
        "rhyme": "Share a string, let friendship sing",
        "result": "the kite climbed higher because two pairs of hands guided it",
        "lesson": "sharing can turn one small treasure into a joy that belongs to two people",
        "ending": "the kite floated above them like a bright smile",
    },
    {
        "title": "the library rhyme",
        "opening": "Luna found a blue storybook on the garden bench and opened it to a page of silly rhymes",
        "need": "Milo wished he could read the funny words but felt shy about asking",
        "clue": "Milo's eyes followed every picture while his fingers traced the first line",
        "action": "Luna moved close, shared the book, and let Milo choose the next page",
        "rhyme": "A page we share is joy to spare",
        "result": "Milo read the last couplet aloud, and Luna clapped for him",
        "lesson": "sharing a chance can help a quiet friend find a brave voice",
        "ending": "the open book rested between them, full of new places to visit",
    },
    {
        "title": "the market melody",
        "opening": "Luna brought a little tin drum to the market square and tapped a gentle beat",
        "need": "Milo stood nearby with a poem but did not know how to begin it",
        "clue": "the poem's short lines matched the drum's steady rhythm",
        "action": "Luna shared the drum and invited Milo to speak between the beats",
        "rhyme": "Tap a beat, make words meet",
        "result": "Milo's poem sounded bold while Luna kept the rhythm beside him",
        "lesson": "sharing the spotlight lets everyone's gift be heard",
        "ending": "the fountain seemed to sparkle along with their friendly little show",
    },
    {
        "title": "the warm basket",
        "opening": "Luna carried a basket of warm rolls up the hill after helping at the community hall",
        "need": "Milo had forgotten his snack and tried to smile even though his stomach rumbled",
        "clue": "the basket held more rolls than Luna could eat",
        "action": "Luna shared two warm rolls and saved one for Milo's little sister",
        "rhyme": "Bread we share shows that we care",
        "result": "Milo stopped pretending he was fine and thanked Luna with a bright grin",
        "lesson": "noticing another person's need is the first step toward kindness",
        "ending": "crumbs dotted the picnic cloth while the sunset painted the hill gold",
    },
]


WORLD_KNOWLEDGE = [
    QAItem(
        question="What does sociable mean?",
        answer="Sociable means friendly and happy to spend time with other people.",
    ),
    QAItem(
        question="What is sharing?",
        answer="Sharing means letting another person use, enjoy, or receive part of something with you.",
    ),
    QAItem(
        question="What is a rhyme?",
        answer="A rhyme is a word or line with a matching sound, often used in poems and songs.",
    ),
    QAItem(
        question="Why can sharing feel heartwarming?",
        answer="Sharing can feel heartwarming because it helps people feel included, cared for, and connected.",
    ),
]

ASP_RULES = r"""
can_share(hero, friend) :- sociable(hero), friend(friend).
kind_choice(hero, friend) :- can_share(hero, friend), has_extra(hero).
happy_ending :- kind_choice(hero, friend), rhyme_used.
valid_story :- happy_ending.
#show valid_story/0.
"""


def build_world(params: StoryParams) -> World:
    rng = random.Random(params.seed if params.seed is not None else 0)
    scenario = SCENARIOS[params.scenario_id % len(SCENARIOS)]
    place = params.place
    hero = Entity(
        id="hero",
        kind="character",
        type="child",
        label=params.hero_name,
        traits=["sociable", "thoughtful", rng.choice(["cheerful", "gentle", "welcoming"])],
        meters={"warmth": 1.0, "confidence": 0.8},
        memes={"kindness": 1.0, "loneliness": 0.0},
    )
    friend = Entity(
        id="friend",
        kind="character",
        type="child",
        label=params.friend_name,
        traits=["quiet", "creative"],
        meters={"confidence": 0.3, "belonging": 0.2},
        memes={"shyness": 1.0, "happiness": 0.1},
    )
    gift = Entity(
        id="shared_item",
        kind="thing",
        type="prop",
        label=params.prop,
        traits=["shareable"],
        held_by="hero",
        meters={"joy": 1.0},
    )
    world = World()
    world.add(hero)
    world.add(friend)
    world.add(gift)

    openings = [
        f"In {place}, {params.hero_name} noticed that the day seemed ready for a little friendship.",
        f"The morning sun warmed {place}, and {params.hero_name} arrived with a sociable smile.",
        f"At {place}, every bird seemed to have a song, and {params.hero_name} wanted everyone to feel welcome.",
    ]
    world.say(openings[params.telling_mode % len(openings)])
    world.say(f"{scenario['opening'].capitalize()}.")
    world.say(f"Nearby, {scenario['need']}.")

    world.para()
    world.say(f"{params.hero_name} noticed that {scenario['clue']}.")
    world.say(f'"Would you like to join me?" {params.hero_name} asked.')
    world.say(f'"I would, but I do not know if I can," {params.friend_name} replied.')
    world.say(f'"We can try together," said {params.hero_name}. "There is enough joy for both of us."')
    world.say(f"{params.hero_name} {scenario['action']}.")
    world.say(f'Together they said, "{scenario["rhyme"]}."')
    world.say(f"{scenario['result'].capitalize()}.")

    hero.memes["kindness"] += 1.0
    hero.meters["warmth"] += 1.0
    friend.meters["confidence"] += 1.0
    friend.meters["belonging"] += 1.0
    friend.memes["shyness"] = 0.0
    friend.memes["happiness"] += 1.0

    world.para()
    world.say(f"{params.friend_name} laughed softly, then smiled more widely.")
    world.say(f'"Thank you for sharing with me," {params.friend_name} said.')
    world.say(f'"Thank you for sharing your smile with me," {params.hero_name} answered.')
    world.say(f"Their rhyme became a small promise: {scenario['lesson'].capitalize()}.")
    world.say(f"By the end, {scenario['ending'].capitalize()}.")

    world.facts.update(
        hero=hero,
        friend=friend,
        gift=gift,
        scenario=scenario,
        place=place,
        shared=True,
        rhyme=scenario["rhyme"],
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    scenario = world.facts["scenario"]
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    return [
        f"Write a heartwarming story about sociable {hero.label} sharing something with {friend.label}.",
        f"Create a child-friendly rhyme about sharing at {world.facts['place']}.",
        f"Tell how {hero.label}'s kindness helps {friend.label} feel included.",
        f"End with a concrete image showing that the friendship has grown.",
    ]


def story_qa(world: World) -> list[QAItem]:
    scenario = world.facts["scenario"]
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    return [
        QAItem(
            question=f"What did {hero.label} share?",
            answer=f"{hero.label} shared {world.facts['gift'].label} with {friend.label}, making room for both children to enjoy it together.",
        ),
        QAItem(
            question=f"Why did {hero.label} decide to share?",
            answer=f"{hero.label} noticed that {scenario['need']} and chose to include {friend.label} instead of enjoying the moment alone.",
        ),
        QAItem(
            question="What rhyme did the children say?",
            answer=f'The children said, "{scenario["rhyme"]}" as they shared the activity.',
        ),
        QAItem(
            question=f"How did sharing change {friend.label}?",
            answer=f"Sharing helped {friend.label} feel included and more confident. {friend.label} joined in and ended the story with a bright smile.",
        ),
        QAItem(
            question="What lesson did the story show?",
            answer=f"The story showed that {scenario['lesson']}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(WORLD_KNOWLEDGE)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("sociable", "hero"),
            asp.fact("friend", "friend"),
            asp.fact("has_extra", "hero"),
            asp.fact("rhyme_used"),
        ]
    )


def asp_program(show: str = "#show valid_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def python_reasonable(params: StoryParams) -> None:
    if not params.hero_name or not params.friend_name:
        raise StoryError("Both children need names.")
    if params.hero_name == params.friend_name:
        raise StoryError("The sociable child and the friend must have different names.")
    if params.place not in PLACES:
        raise StoryError("The place must be one of the registered story places.")
    if params.prop not in PROPS:
        raise StoryError("The shared item must be one of the registered story items.")


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    actual = bool(asp.atoms(model, "valid_story"))
    expected = True
    if actual != expected:
        print("MISMATCH between ASP and Python reasonableness gate.")
        return 1
    for scenario_id in range(len(SCENARIOS)):
        params = StoryParams(scenario_id=scenario_id)
        python_reasonable(params)
        sample = generate(params)
        if not sample.world or not sample.world.facts["shared"]:
            print("Generated story failed its sharing check.")
            return 1
        if "said" not in sample.story or not sample.world.facts["rhyme"]:
            print("Generated story failed its dialogue or rhyme check.")
            return 1
    print("OK: ASP gate matches Python gate and generated stories.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A heartwarming storyworld about sociable sharing and rhyme."
    )
    parser.add_argument("--hero-name", choices=HERO_NAMES)
    parser.add_argument("--friend-name", choices=FRIEND_NAMES)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--prop", choices=PROPS)
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
    params = StoryParams(
        seed=None,
        hero_name=args.hero_name or rng.choice(HERO_NAMES),
        friend_name=args.friend_name or rng.choice(FRIEND_NAMES),
        place=args.place or rng.choice(PLACES),
        prop=args.prop or rng.choice(PROPS),
        scenario_id=rng.randrange(len(SCENARIOS)),
        telling_mode=rng.randrange(3),
        detail_variant=rng.randrange(8),
    )
    python_reasonable(params)
    return params


def generate(params: StoryParams) -> StorySample:
    python_reasonable(params)
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        lines.append(
            f"  {entity.id:10} ({entity.type:9}) "
            f"traits={entity.traits} meters={meters} memes={memes}"
        )
    lines.append(f"  shared={world.facts.get('shared')} rhyme={world.facts.get('rhyme')!r}")
    return "\n".join(lines)


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


CURATED = [
    StoryParams(hero_name="Luna", friend_name="Milo", place=PLACES[0], prop=PROPS[0], scenario_id=0),
    StoryParams(hero_name="Ari", friend_name="Sam", place=PLACES[1], prop=PROPS[3], scenario_id=1),
    StoryParams(hero_name="Nia", friend_name="Ollie", place=PLACES[2], prop=PROPS[1], scenario_id=2),
    StoryParams(hero_name="Maya", friend_name="Ben", place=PLACES[3], prop=PROPS[2], scenario_id=3),
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

        model = asp.one_model(asp_program())
        atoms = asp.atoms(model, "valid_story")
        print(f"{len(atoms)} valid story pattern(s).")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < max(1, args.n) and attempt < max(50, args.n * 50):
            rng = random.Random(base_seed + attempt)
            params = resolve_params(args, rng)
            params.seed = base_seed + attempt
            sample = generate(params)
            attempt += 1
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
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
