#!/usr/bin/env python3
"""
Storyworld: shampoo_john_characteristic_sharing_bad_ending_suspense

A tiny pirate tale about John, a bottle of shampoo, sharing, and the suspense
of a bad ending that can still be repaired by a generous choice.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Character:
    id: str
    name: str
    role: str
    trait: str
    meters: dict[str, float] = field(default_factory=lambda: {"suspense": 0.0, "kindness": 0.0, "risk": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"worry": 0.0, "trust": 0.0, "pride": 0.0})


@dataclass
class Object:
    id: str
    label: str
    kind: str
    owner: str = ""
    location: str = ""
    meters: dict[str, float] = field(default_factory=lambda: {"full": 1.0, "risk": 0.0})


@dataclass
class StoryParams:
    hero_name: str
    friend_name: str
    captain_name: str
    ship: str
    island: str
    shampoo: str
    characteristic: str
    sharing_style: str
    suspense_style: str
    seed: Optional[int] = None


NAMES = {
    "hero": ["John", "Tom", "Sam", "Leo"],
    "friend": ["Mara", "Pip", "Nell", "Ruby"],
    "captain": ["Captain Coral", "Captain Flint", "Captain Blue", "Captain Pearl"],
}

SHIPS = ["the Bright Parrot", "the Sea Bell", "the Laughing Gull", "the Moonlit Minnow"]
ISLANDS = ["Coconut Key", "Whisper Reef", "Shellback Island", "Starfish Cove"]
SHAMPOOS = ["coconut shampoo", "mint shampoo", "lemon shampoo", "sea-salt shampoo"]
CHARACTERISTICS = ["generous", "curious", "patient", "brave"]
SHARING_STYLES = ["one careful scoop", "a fair turn", "a little bottle passed around", "a promise to refill it"]
SUSPENSE_STYLES = ["a sudden wave", "a darkening cloud", "a creaking deck", "a distant pirate bell"]


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.characters: dict[str, Character] = {}
        self.objects: dict[str, Object] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def render(self) -> str:
        paragraphs: list[str] = []
        current: list[str] = []
        for line in self.lines:
            if line == "":
                if current:
                    paragraphs.append(" ".join(current))
                    current = []
            else:
                current.append(line)
        if current:
            paragraphs.append(" ".join(current))
        return "\n\n".join(paragraphs)


def build_world(params: StoryParams) -> World:
    if params.hero_name.lower() != "john":
        raise StoryError("The canonical shampoo tale requires the hero name John.")
    if not params.shampoo.strip():
        raise StoryError("Shampoo must be named so the sharing choice has a real object.")
    if params.characteristic not in CHARACTERISTICS:
        raise StoryError(f"Unknown characteristic: {params.characteristic}.")
    if params.sharing_style not in SHARING_STYLES:
        raise StoryError(f"Unknown sharing style: {params.sharing_style}.")
    if params.suspense_style not in SUSPENSE_STYLES:
        raise StoryError(f"Unknown suspense style: {params.suspense_style}.")

    world = World(params)
    john = Character("john", params.hero_name, "young deckhand", params.characteristic)
    friend = Character("friend", params.friend_name, "shipmate", "tired but hopeful")
    captain = Character("captain", params.captain_name, "captain", "watchful")
    shampoo = Object("shampoo", params.shampoo, "bottle", owner="john", location="the wash bucket")

    world.characters.update({"john": john, "friend": friend, "captain": captain})
    world.objects["shampoo"] = shampoo

    world.say(
        f"On the pirate ship {params.ship}, young {john.name} found a bottle of {shampoo.label} "
        f"beside the wash bucket as the crew sailed toward {params.island}."
    )
    world.say(
        f"{friend.name} had salt in their hair and only a few drops of water left, while "
        f"{john.name} held the bottle close and remembered that being {john.trait} was a "
        f"characteristic worth showing, not merely saying."
    )
    world.say(
        f'"Please, John," {friend.name} said. "Could I wash with some of that shampoo?"'
    )
    world.say(
        f'"It is mine," {john.name} answered, tightening a hand around the bottle. '
        f'"But perhaps I can decide after I see how much is left."'
    )
    john.meters["suspense"] += 1
    john.meters["risk"] += 1
    friend.memes["worry"] += 1
    world.para()

    world.say(
        f"Then came {params.suspense_style}. The ship lurched, the wash bucket slid toward the rail, "
        f"and the shampoo nearly rolled into the hungry sea."
    )
    world.say(
        f'"John, catch it!" cried {captain.name}. "And remember, a thing kept too tightly can be lost by itself."'
    )
    world.say(
        f"{john.name} grabbed the bottle just in time, but the cap popped open. "
        f"A bright ribbon of {shampoo.label} dribbled across the deck."
    )
    shampoo.meters["full"] = 0.55
    shampoo.meters["risk"] = 1.0
    john.memes["worry"] += 1
    john.meters["suspense"] += 1
    world.para()

    world.say(
        f"{friend.name} looked at the small remaining pool. "
        f'"There may not be enough for both of us," they whispered. '
        f'"If you keep it all, I will still have salty hair when we reach the island."'
    )
    world.say(
        f"{john.name} glanced at the rail. A second wave was rising, and the bottle stood near its path. "
        f"The suspense tightened like a rope in a storm."
    )
    world.say(
        f'"Let us share it now," {john.name} said. "I will use {params.sharing_style}, and you can help me hold the bucket."'
    )
    world.say(
        f"{friend.name} smiled. " + '"Then I will save the rinse water for the deck plants."'
    )
    john.meters["kindness"] += 1
    friend.meters["kindness"] += 1
    john.memes["trust"] += 1
    friend.memes["trust"] += 1
    world.para()

    world.say(
        f"John poured a little shampoo into {friend.name}'s palm, then a little into his own. "
        f"They scrubbed quickly and rinsed with care while the captain steadied the bucket."
    )
    world.say(
        f"The second wave swept across the deck, but the empty bottle was already tucked safely under a rope. "
        f"No one slipped, and the bad ending that had seemed ready to happen passed them by."
    )
    shampoo.owner = "john and friend"
    shampoo.location = "under a securing rope"
    shampoo.meters["full"] = 0.0
    shampoo.meters["risk"] = 0.0
    captain.meters["kindness"] += 1
    world.say(
        f"{captain.name} nodded. 'A pirate can guard treasure and still share it when a shipmate needs help.'"
    )
    world.say(
        f"{john.name} learned that sharing {shampoo.label} did not leave him with less courage. "
        f"It made his {john.trait} characteristic visible to everyone on deck."
    )
    world.say(
        f'"Next voyage, we will bring two bottles," {john.name} promised. '
        f'"Next voyage," {friend.name} replied, "we will share before the storm asks us to."'
    )
    world.say(
        f"At sunset, {params.ship} reached {params.island}; {john.name} and {friend.name}'s clean hair shone "
        f"like little flags of friendship above the quiet sea."
    )

    world.facts.update(
        john=john,
        friend=friend,
        captain=captain,
        shampoo=shampoo,
        ship=params.ship,
        island=params.island,
        characteristic=params.characteristic,
        suspense=params.suspense_style,
        sharing=params.sharing_style,
        bad_ending="The shampoo could have been lost and the shipmate left unwashed.",
        result="John shared the remaining shampoo before the second wave could carry it away.",
        lesson="sharing can turn a frightening moment into trust",
        ending=f"{params.hero_name} and {params.friend_name}'s clean hair shone like little flags of friendship above the quiet sea",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a pirate tale about John sharing {f['shampoo'].label} with {f['friend'].name}.",
        f"Tell a suspenseful story on {f['ship']} where a bad ending is avoided when John shows his {f['characteristic']} characteristic.",
        f"Write a child-friendly sea adventure in which {f['suspense']} threatens to carry away the shampoo, but sharing saves the friendship.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    john: Character = f["john"]
    friend: Character = f["friend"]
    shampoo: Object = f["shampoo"]
    return [
        QAItem(
            question=f"Why did {friend.name} ask {john.name} for shampoo?",
            answer=f"{friend.name} had salt in their hair and only a few drops of water left, so they asked {john.name} to share the {shampoo.label}.",
        ),
        QAItem(
            question=f"What suspenseful danger threatened the shampoo?",
            answer=f"A wave made the ship lurch, and the shampoo nearly rolled into the sea. Later, a second wave threatened the bottle again.",
        ),
        QAItem(
            question="What would the bad ending have been?",
            answer=f"The bad ending would have been losing the shampoo and leaving {friend.name} with salty hair, but John chose to share before that happened.",
        ),
        QAItem(
            question=f"How did {john.name} show his characteristic?",
            answer=f"John showed his {f['characteristic']} characteristic by sharing the remaining shampoo with {friend.name} instead of keeping it all.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"John and {friend.name} washed safely, reached the island, and their clean hair shone like little flags of friendship above the quiet sea.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means willingly giving another person a fair chance to use or enjoy something.",
        ),
        QAItem(
            question="What is suspense?",
            answer="Suspense is the feeling of waiting anxiously to learn what will happen next.",
        ),
        QAItem(
            question="What is a characteristic?",
            answer="A characteristic is a quality or feature that helps describe a person, such as being generous or patient.",
        ),
        QAItem(
            question="What is shampoo used for?",
            answer="Shampoo is a liquid used with water to clean hair.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for character in world.characters.values():
        lines.append(
            f"{character.id}: role={character.role} trait={character.trait} "
            f"meters={dict(character.meters)} memes={dict(character.memes)}"
        )
    for obj in world.objects.values():
        lines.append(
            f"{obj.id}: label={obj.label} owner={obj.owner} location={obj.location} "
            f"meters={dict(obj.meters)}"
        )
    return "\n".join(lines)


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


ASP_RULES = r"""
story(S) :- john(S), shampoo(S), sharing(S), suspense(S), repaired_bad_ending(S).
pirate_tale(S) :- story(S), characteristic_shown(S).
repaired_bad_ending(S) :- danger(S), share_choice(S).
"""


def asp_facts(params: StoryParams) -> str:
    import asp
    return "\n".join(
        [
            asp.fact("john", "s1"),
            asp.fact("shampoo", "s1"),
            asp.fact("sharing", "s1"),
            asp.fact("suspense", "s1"),
            asp.fact("danger", "s1"),
            asp.fact("share_choice", "s1"),
            asp.fact("repaired_bad_ending", "s1"),
            asp.fact("characteristic_shown", "s1"),
        ]
    )


def asp_program() -> str:
    params = StoryParams(
        hero_name="John",
        friend_name="Mara",
        captain_name="Captain Coral",
        ship="the Bright Parrot",
        island="Coconut Key",
        shampoo="coconut shampoo",
        characteristic="generous",
        sharing_style="one careful scoop",
        suspense_style="a sudden wave",
    )
    return f"{asp_facts(params)}\n{ASP_RULES}\n#show pirate_tale/1.\n#show story/1.\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    found = set(asp.atoms(model, "pirate_tale"))
    if found != {("s1",)}:
        print("MISMATCH: ASP did not recognize the repaired pirate tale.")
        return 1
    sample = generate(
        StoryParams(
            hero_name="John",
            friend_name="Mara",
            captain_name="Captain Coral",
            ship="the Bright Parrot",
            island="Coconut Key",
            shampoo="coconut shampoo",
            characteristic="generous",
            sharing_style="one careful scoop",
            suspense_style="a sudden wave",
        )
    )
    required = ("shampoo", "John", "share", "wave", "friendship")
    if not all(word.lower() in sample.story.lower() for word in required):
        print("MISMATCH: generated story lacks required narrative evidence.")
        return 1
    print("OK: ASP and Python gates agree; generated story exercised.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Pirate tale about John, shampoo, sharing, and suspense.")
    parser.add_argument("--hero-name")
    parser.add_argument("--friend-name")
    parser.add_argument("--captain-name")
    parser.add_argument("--ship")
    parser.add_argument("--island")
    parser.add_argument("--shampoo")
    parser.add_argument("--characteristic", choices=CHARACTERISTICS)
    parser.add_argument("--sharing-style", choices=SHARING_STYLES)
    parser.add_argument("--suspense-style", choices=SUSPENSE_STYLES)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        hero_name=args.hero_name or "John",
        friend_name=args.friend_name or rng.choice(NAMES["friend"]),
        captain_name=args.captain_name or rng.choice(NAMES["captain"]),
        ship=args.ship or rng.choice(SHIPS),
        island=args.island or rng.choice(ISLANDS),
        shampoo=args.shampoo or rng.choice(SHAMPOOS),
        characteristic=args.characteristic or rng.choice(CHARACTERISTICS),
        sharing_style=args.sharing_style or rng.choice(SHARING_STYLES),
        suspense_style=args.suspense_style or rng.choice(SUSPENSE_STYLES),
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


CURATED = [
    StoryParams(
        hero_name="John",
        friend_name="Mara",
        captain_name="Captain Coral",
        ship="the Bright Parrot",
        island="Coconut Key",
        shampoo="coconut shampoo",
        characteristic="generous",
        sharing_style="one careful scoop",
        suspense_style="a sudden wave",
    ),
    StoryParams(
        hero_name="John",
        friend_name="Pip",
        captain_name="Captain Flint",
        ship="the Sea Bell",
        island="Whisper Reef",
        shampoo="mint shampoo",
        characteristic="patient",
        sharing_style="a fair turn",
        suspense_style="a creaking deck",
    ),
    StoryParams(
        hero_name="John",
        friend_name="Ruby",
        captain_name="Captain Pearl",
        ship="the Moonlit Minnow",
        island="Starfish Cove",
        shampoo="sea-salt shampoo",
        characteristic="brave",
        sharing_style="a promise to refill it",
        suspense_style="a darkening cloud",
    ),
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
        print(asp.one_model(asp_program()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(50, args.n * 20):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            index += 1

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
