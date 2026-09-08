#!/usr/bin/env python3
"""A gentle navy nursery rhyme about sharing and a happy ending."""

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
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    type: str
    label: str
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    lines: list[str] = field(default_factory=list)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    child: str = "Luna"
    friend: str = "Milo"
    helper: str = "Pip"
    setting: str = "the navy harbor"
    verse: int = 0
    opening: int = 0
    ending: int = 0
    cadence: int = 0


NAMES = ["Luna", "Nell", "Mina", "Tess", "Cora", "Wren"]
FRIENDS = ["Milo", "Theo", "Finn", "Ollie", "Sam"]
HELPERS = ["Pip", "Bibi", "Nia", "Jo", "Kit"]

OPENINGS = [
    "In the navy harbor, {child} wore a cap as blue as the sea.",
    "By the navy boats, {child} heard the gulls sing, 'Cheep-cheep-chee!'",
    "At the navy pier, {child} found a bright morning full of tide and tune.",
    "Along the navy shore, {child} skipped where little silver waves danced.",
    "The navy bell rang ding-dong-ding, and {child} came smiling to the pier.",
    "Under a navy sky, {child} carried a basket down to the friendly bay.",
]

VERSES = [
    {
        "object": "a round red apple",
        "need": "a hungry friend had no snack for the morning ride",
        "offer": "Half for you and half for me; sharing makes a happy sea!",
        "action": "{child} split the apple neatly, and {friend} smiled from ear to ear.",
        "result": "The two friends munched together while the navy boat bobbed twice.",
        "lesson": "When we share what we have, a little can become enough for two.",
        "ending": "The apple core made a tiny heart beside the navy oar.",
    },
    {
        "object": "a warm woolly scarf",
        "need": "a chilly friend shivered when the salt wind blew",
        "offer": "Wrap with me, and you will see: warm and kind is how we should be!",
        "action": "{child} wrapped one end around {friend}, leaving both friends cozy.",
        "result": "They waved to the sailors with one scarf fluttering like a happy flag.",
        "lesson": "Sharing comfort can warm more than one heart.",
        "ending": "The navy scarf danced in the breeze, snug as snug could be.",
    },
    {
        "object": "a shiny yellow pail",
        "need": "a friend needed a pail to gather shells for the harbor song",
        "offer": "Take a turn, then give to me; sharing makes a shell-filled sea!",
        "action": "{child} passed the pail back and forth, one turn each.",
        "result": "Soon the friends filled it with shells that clicked a bright rhythm.",
        "lesson": "Taking turns lets everyone join the fun.",
        "ending": "The shells sang click-clack in the pail beside the navy sea.",
    },
    {
        "object": "a little blue kite",
        "need": "a friend stood sadly because the breezy kite would not rise",
        "offer": "Hold the string with me, my dear; shared hands send the kite up clear!",
        "action": "{child} gave {friend} the spool while holding the kite's tail.",
        "result": "Together they lifted the kite over the navy mast.",
        "lesson": "A shared job can make a difficult task feel light.",
        "ending": "The blue kite sailed above the navy boats, high and free.",
    },
    {
        "object": "a basket of berry buns",
        "need": "a friend had forgotten lunch before the long harbor watch",
        "offer": "One for you and one for me; sweet sharing by the sea!",
        "action": "{child} offered a berry bun, then {friend} offered the last one back.",
        "result": "They ate together and saved a crumb for a little gull.",
        "lesson": "Sharing invites kindness to come back around.",
        "ending": "The gull gave a happy hop beside the navy bakery.",
    },
    {
        "object": "a bright brass bell",
        "need": "a friend could not find the path back from the misty pier",
        "offer": "Ring with me, and you will see; shared sounds can guide us safely!",
        "action": "{child} held the bell while {friend} rang it in a gentle beat.",
        "result": "The clear ding-dong led the friend safely back to the navy gate.",
        "lesson": "Sharing a useful tool can help a friend feel safe.",
        "ending": "Ding-dong rang the brass bell, and all were home by the sea.",
    },
]

ENDINGS = [
    "Then the navy moon came up, and two happy friends sang, 'Share and care, everywhere!'",
    "The harbor hummed a little rhyme: 'Sharing turns a tide to shine!'",
    "Home they went with hearts aglow, singing softly, 'Share as you go!'",
    "The navy waves went swish and sway; sharing made a splendid day.",
]

CADENCES = [
    "A little share, a little cheer, can make a friend feel very near.",
    "One for you and one for me; kindness sails across the sea.",
    "Round and round the good deed flew, from one small hand to one friend too.",
    "A giving hand and smiling face can make a bright and friendly place.",
]


ASP_RULES = r"""
#show sharing/2.
#show happy_ending/1.

sharing(A, B) :- offers(A, B).
happy_ending(S) :- sharing(A, B), solved(S), kind(A), kind(B).
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("kind", "child"),
            asp.fact("kind", "friend"),
            asp.fact("offers", "child", "friend"),
            asp.fact("solved", "navy_sharing"),
        ]
    )


def asp_program(show: str = "#show sharing/2.\n#show happy_ending/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Nursery-rhyme storyworld about navy sharing and a happy ending."
    )
    parser.add_argument("--child", choices=NAMES)
    parser.add_argument("--friend", choices=FRIENDS)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--setting", default="the navy harbor")
    parser.add_argument("--verse", type=int, choices=range(len(VERSES)))
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
    setting = args.setting.strip() if args.setting else "the navy harbor"
    if not setting.startswith(("the ", "a ", "an ")):
        setting = "the " + setting
    if "navy" not in setting.lower():
        raise StoryError("setting must include the word navy")
    return StoryParams(
        seed=args.seed,
        child=args.child or rng.choice(NAMES),
        friend=args.friend or rng.choice(FRIENDS),
        helper=args.helper or rng.choice(HELPERS),
        setting=setting,
        verse=args.verse if args.verse is not None else rng.randrange(len(VERSES)),
        opening=rng.randrange(len(OPENINGS)),
        ending=rng.randrange(len(ENDINGS)),
        cadence=rng.randrange(len(CADENCES)),
    )


def generate(params: StoryParams) -> StorySample:
    if params.child == params.friend:
        raise StoryError("child and friend must have different names")
    if "navy" not in params.setting.lower():
        raise StoryError("the setting must remain a navy setting")

    verse = VERSES[params.verse % len(VERSES)]
    world = World()

    child = world.add(
        Entity(
            id="child",
            type="child",
            label=params.child,
            meters={"energy": 0.8, "warmth": 0.6},
            memes={"kindness": 0.8, "joy": 0.5},
        )
    )
    friend = world.add(
        Entity(
            id="friend",
            type="friend",
            label=params.friend,
            meters={"energy": 0.4, "warmth": 0.3},
            memes={"hope": 0.3, "joy": 0.2},
        )
    )
    helper = world.add(
        Entity(
            id="helper",
            type="helper",
            label=params.helper,
            meters={"energy": 0.7},
            memes={"cheer": 0.7},
        )
    )
    shared = world.add(
        Entity(
            id="shared_item",
            type="object",
            label=verse["object"],
            owner=child.id,
            meters={"whole": 1.0},
            memes={"usefulness": 0.8},
        )
    )

    def fill(text: str) -> str:
        return text.format(
            child=child.label,
            friend=friend.label,
            helper=helper.label,
            setting=params.setting,
        )

    world.say(fill(OPENINGS[params.opening % len(OPENINGS)]))
    world.say(
        f"{child.label} carried {verse['object']} to the pier, while "
        f"{friend.label} watched the navy boats glide near."
    )
    world.say(f"But {friend.label} {verse['need']}.")
    world.say(
        f"{friend.label} asked, '{verse['object'].capitalize()} looks useful. "
        f"May I have a turn?'"
    )
    world.say(f"{child.label} replied, '{verse['offer']}'")
    world.say(fill(verse["action"]))
    world.say(fill(CADENCES[params.cadence % len(CADENCES)]))
    world.say(fill(verse["result"]))

    child.meters["energy"] = 0.9
    friend.meters["warmth"] = 0.9
    friend.memes["hope"] = 0.9
    friend.memes["joy"] = 0.9
    child.memes["joy"] = 0.9
    shared.owner = "shared"
    shared.meters["shared"] = 1.0

    world.say(
        f"{helper.label} clapped and said, 'Hooray! When we share, "
        f"there is more happiness to spare.'"
    )
    world.say(f"Happy ending: {fill(verse['lesson'])}")
    world.say(fill(verse["ending"]))
    world.say(fill(ENDINGS[params.ending % len(ENDINGS)]))

    world.facts.update(
        child=child,
        friend=friend,
        helper=helper,
        shared_item=shared,
        verse=verse,
        setting=params.setting,
        navy=True,
        sharing=True,
        happy_ending=True,
        rhyme=True,
    )

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    verse = facts["verse"]
    child = facts["child"]
    friend = facts["friend"]
    return [
        f"Write a nursery rhyme about {child.label} sharing {verse['object']} with {friend.label} in a navy harbor.",
        f"Tell a child-friendly navy story with a brief dialogue, a sharing lesson, rhyming lines, and a happy ending.",
        f"Create a gentle rhyme where {child.label} and {friend.label} take turns with {verse['object']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    child = facts["child"]
    friend = facts["friend"]
    helper = facts["helper"]
    verse = facts["verse"]
    return [
        QAItem(
            question=f"What did {child.label} share with {friend.label}?",
            answer=f"{child.label} shared {verse['object']} with {friend.label} at the navy harbor.",
        ),
        QAItem(
            question=f"How did {friend.label} feel after the sharing?",
            answer=f"{friend.label} felt warm, hopeful, and joyful because {child.label} included them.",
        ),
        QAItem(
            question="What did the helper say?",
            answer=(
                f"{helper.label} said, 'Hooray! When we share, there is more happiness to spare.'"
            ),
        ),
        QAItem(
            question="What lesson did the story teach?",
            answer=f"The story taught that {verse['lesson'].lower()}",
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended happily with the friends together by the navy water, singing a little rhyme about sharing.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting another person use, enjoy, or receive part of something we have.",
        ),
        QAItem(
            question="Why can taking turns be fair?",
            answer="Taking turns gives each person a chance to join in and enjoy the activity.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a poem or verse with words that have matching or similar ending sounds.",
        ),
        QAItem(
            question="What does navy describe in this storyworld?",
            answer="Navy describes the deep blue color and the sea-and-sailor setting around the harbor.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for index, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{index}. {prompt}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id:11} ({entity.type:7}) "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


def asp_valid() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "sharing")))


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    sharing = set(asp.atoms(model, "sharing"))
    endings = set(asp.atoms(model, "happy_ending"))
    if sharing == {("child", "friend")} and endings == {("navy_sharing",)}:
        print("OK: clingo parity matches Python gate.")
        return 0
    print("MISMATCH between clingo and Python gate.")
    print("  clingo sharing:", sorted(sharing))
    print("  clingo happy endings:", sorted(endings))
    return 1


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
    StoryParams(child="Luna", friend="Milo", helper="Pip", verse=0),
    StoryParams(child="Nell", friend="Theo", helper="Bibi", verse=2, opening=1, ending=2, cadence=1),
    StoryParams(child="Mina", friend="Finn", helper="Nia", verse=5, opening=4, ending=3, cadence=3),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        facts = asp_valid()
        print(f"{len(facts)} ASP-suggested sharing facts")
        for fact in facts:
            print(fact)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        index = 0
        limit = max(50, args.n * 30)
        while len(samples) < args.n and index < limit:
            params = resolve_params(args, random.Random(base_seed + index))
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            index += 1

    if not samples:
        raise StoryError("no stories could be generated")

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.child}: navy sharing rhyme"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
