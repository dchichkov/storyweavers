#!/usr/bin/env python3
"""
A small stand-alone pirate tale about a historic shutter, friendship, and problem solving.
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
class StoryParams:
    child: str
    friend: str
    captain: str
    island: str
    shutter: str
    clue: str
    incident: int = 0
    premise: int = 0
    ending: int = 0
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


CHILDREN = ["Luna", "Milo", "Nia", "Pip", "Tessa", "Kai", "Rafi", "Zara"]
FRIENDS = ["Bea", "Finn", "Mara", "Otis", "Suki", "Theo", "Wren", "Juno"]
CAPTAINS = ["Captain Coral", "Captain Flint", "Captain Marigold", "Captain Bluebeard"]
ISLANDS = ["Cannonball Cay", "Moonbeam Isle", "Shellbell Island", "Whispering Key"]
SHUTTERS = [
    "the old red shutter",
    "the carved blue shutter",
    "the round brass shutter",
    "the weathered green shutter",
]
CLUES = [
    "a brass compass",
    "a striped feather",
    "a silver button",
    "a tiny map",
]

INCIDENTS = [
    {
        "lead": "The historic shutter guarded the lighthouse door, and a moon-shaped keyhole gleamed beneath its rusty latch.",
        "trigger": "A gust slammed the shutter shut before anyone could study the tiny marks around the keyhole.",
        "risk": "Without the marks, the crew might miss the safe path to the lighthouse bell.",
        "action": "{child} held the lantern low while {friend} noticed that the hinges made three short taps.",
        "resolution": "Together, they tapped the shutter three times. The latch clicked, and the old door opened without a creak.",
        "cause": "a gust slammed the historic shutter before the clue could be read",
        "deed": "held the lantern low while listening with {friend}",
        "result": "the friends copied the hinge rhythm and opened the shutter safely",
    },
    {
        "lead": "The historic shutter was painted with tiny ships, each one pointing toward a different part of the harbor.",
        "trigger": "A loose board dropped in front of the shutter and covered the ship that held the real clue.",
        "risk": "The pirates could sail the wrong way and circle the island until breakfast.",
        "action": "{friend} tried to pull the board, but {child} found a rope loop and showed how to lift it instead.",
        "resolution": "The board rose gently, revealing a painted star. Captain Coral steered by that star and found the hidden cove.",
        "cause": "a fallen board hid the clue on the historic shutter",
        "deed": "found a rope loop and helped lift the board without breaking it",
        "result": "the star clue appeared and guided the ship to the hidden cove",
    },
    {
        "lead": "At sunset, the historic shutter reflected orange light across the lighthouse floor like a bright wooden treasure map.",
        "trigger": "A crab scuttled behind the shutter and nudged its latch from the other side.",
        "risk": "The shutter began to swing toward a shelf of precious glass signal bottles.",
        "action": "{child} called, 'Hold the bottles!' {friend} slid a coil of soft rope beneath the shutter to stop its swing.",
        "resolution": "Captain Flint moved the crab to a tide pool, and the friends tied the shutter open with a safe knot.",
        "cause": "a crab nudged the historic shutter toward fragile signal bottles",
        "deed": "warned the crew and used a soft rope to stop the shutter",
        "result": "the bottles stayed safe and the shutter was secured with a knot",
    },
    {
        "lead": "The historic shutter carried a faded picture of two pirates sharing one treasure chest.",
        "trigger": "When the sea fog rolled in, the picture vanished behind a wet gray veil.",
        "risk": "The crew could no longer tell which carved arrow pointed toward the old friendship chest.",
        "action": "{friend} remembered the arrow's shape, while {child} counted the boards from the bottom up.",
        "resolution": "Their two clues met at the same mark. Beneath it, they found the chest, filled with letters from long-ago friends.",
        "cause": "sea fog hid the arrows carved into the historic shutter",
        "deed": "combined a remembered arrow with a careful board count",
        "result": "the friends found the chest of letters beneath the matching mark",
    },
    {
        "lead": "The historic shutter creaked open to reveal a row of old brass bells.",
        "trigger": "One bell rang by itself, and a gust began pulling a map toward the open window.",
        "risk": "The map might fly into the sea before the crew learned where the treasure was buried.",
        "action": "{child} grabbed one corner while {friend} placed a smooth shell on the map's other edge.",
        "resolution": "The map stayed flat. Its dotted trail led to a garden where the treasure turned out to be a basket of sweet oranges.",
        "cause": "a gust pulled the treasure map toward the open window",
        "deed": "held one corner while {friend} weighted the other with a shell",
        "result": "the map stayed safe and led the crew to an orange garden",
    },
    {
        "lead": "The historic shutter had a secret sliding panel, polished smooth by sailors' hands.",
        "trigger": "The panel stuck halfway, leaving a narrow opening and a muffled rattle inside.",
        "risk": "Prying it open could damage the old wood and lose whatever waited within.",
        "action": "{friend} listened to the rattle while {child} sprinkled a little sand along the lower groove.",
        "resolution": "The sand showed where the panel rubbed. After they brushed that spot clean, the panel slid open to reveal the missing ship's bell.",
        "cause": "the secret panel jammed while something rattled behind it",
        "deed": "listened and used sand to find the panel's rubbing point",
        "result": "the friends freed the panel and recovered the missing ship's bell",
    },
]

PREMISES = [
    "{child} sailed with {friend} aboard Captain Coral's little ship, the Jolly Juniper.",
    "On a warm morning, {child} and {friend} rowed toward {island} with Captain Flint and a very serious parrot.",
    "The crew's map pointed to {island}, where an historic shutter was said to hide a secret left by two old friends.",
    "After a night of stars and calm waves, {child} and {friend} reached {island} before breakfast.",
    "Captain Marigold promised a treasure hunt, but {child} and {friend} soon learned that the first treasure was a puzzle.",
    "The Jolly Juniper dropped anchor beside {island}. At its highest hill stood a lighthouse with an historic shutter.",
]

ENDINGS = [
    "That evening, {child} and {friend} painted a small new star beside the old clue. It marked the place where teamwork had saved the day.",
    "The crew shared the treasure beneath a striped sail. {child} and {friend} kept the best prize: a friendship knot tied from the same rope.",
    "As the ship sailed home, the lighthouse shutter flashed in the sunset. Its wooden creak sounded almost like a cheerful goodbye.",
    "Captain Bluebeard placed the clue in the ship's log and wrote, 'Two clever friends solve more than one lonely pirate ever can.'",
    "The friends returned the old treasure to its shelf, then shared oranges on deck while the parrot shouted, 'Aha, mateys!'",
    "Moonlight silvered the historic shutter. {child} and {friend} smiled because the old mystery had gained a brand-new chapter.",
]

ASP_RULES = r"""
#show valid/3.
#show valid_story/5.

child_name(X) :- child(X).
friend_name(X) :- friend(X).
island_name(X) :- island(X).
shutter_name(X) :- shutter(X).
clue_name(X) :- clue(X).

compatible(C, F, S) :-
    child_name(C),
    friend_name(F),
    shutter_name(S),
    C != F.

valid(C, F, S) :- compatible(C, F, S).
valid_story(C, F, I, S, K) :-
    valid(C, F, S),
    island_name(I),
    clue_name(K).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for value in CHILDREN:
        lines.append(asp.fact("child", value))
    for value in FRIENDS:
        lines.append(asp.fact("friend", value))
    for value in ISLANDS:
        lines.append(asp.fact("island", value))
    for value in SHUTTERS:
        lines.append(asp.fact("shutter", value))
    for value in CLUES:
        lines.append(asp.fact("clue", value))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    return [(child, friend, shutter) for child in CHILDREN for friend in FRIENDS for shutter in SHUTTERS if child != friend]


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted({tuple(atom) for atom in asp.atoms(model, "valid")})


def asp_verify() -> int:
    python_values = set(valid_combos())
    clingo_values = set(asp_valid_combos())
    if python_values == clingo_values:
        print(f"OK: clingo gate matches valid_combos() ({len(python_values)} combinations).")
        return 0
    print("MISMATCH between clingo and valid_combos().")
    print("Only in Python:", sorted(python_values - clingo_values))
    print("Only in clingo:", sorted(clingo_values - python_values))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    child = args.child or rng.choice(CHILDREN)
    friend = args.friend or rng.choice(FRIENDS)
    if child == friend:
        raise StoryError("The child and friend must have different names so their conversation is clear.")
    return StoryParams(
        child=child,
        friend=friend,
        captain=args.captain or rng.choice(CAPTAINS),
        island=args.island or rng.choice(ISLANDS),
        shutter=args.shutter or rng.choice(SHUTTERS),
        clue=args.clue or rng.choice(CLUES),
        incident=rng.randrange(len(INCIDENTS)),
        premise=rng.randrange(len(PREMISES)),
        ending=rng.randrange(len(ENDINGS)),
    )


def apply_seeded_structure(params: StoryParams, seed: int) -> None:
    params.incident = seed % len(INCIDENTS)
    params.premise = (seed // len(INCIDENTS)) % len(PREMISES)
    params.ending = (seed // 5) % len(ENDINGS)


def generate(params: StoryParams) -> StorySample:
    incident = INCIDENTS[params.incident % len(INCIDENTS)]
    values = {
        "child": params.child,
        "friend": params.friend,
        "captain": params.captain,
        "island": params.island,
        "shutter": params.shutter,
        "clue": params.clue,
    }

    world = World()
    child = world.add(Entity(params.child, "character", params.child, memes={"curiosity": 1.0}))
    friend = world.add(Entity(params.friend, "character", params.friend, memes={"friendship": 1.0}))
    captain = world.add(Entity(params.captain, "character", params.captain))
    shutter = world.add(Entity("historic_shutter", "artifact", params.shutter, meters={"swing": 0.0}, memes={"history": 1.0}))
    clue = world.add(Entity("clue", "artifact", params.clue, memes={"mystery": 1.0}))

    world.say(PREMISES[params.premise % len(PREMISES)].format(**values))
    world.say(f"{params.captain} lowered the anchor near {params.island}. 'Keep your eyes open,' said the captain. 'Old things often tell new stories.'")
    world.say(incident["lead"].format(**values))

    world.para()
    shutter.meters["swing"] = 1.0
    clue.memes["mystery"] = 1.0
    world.say(incident["trigger"].format(**values))
    world.say(incident["risk"].format(**values))
    world.say(f'"I see one part of the puzzle," said {params.child}. "Tell me yours," said {params.friend}.')
    world.say(incident["action"].format(**values))

    world.para()
    shutter.meters["swing"] = 0.0
    shutter.memes["safe"] = 1.0
    child.memes["confidence"] = 1.0
    friend.memes["confidence"] = 1.0
    friend.memes["friendship"] = 2.0
    world.say(incident["resolution"].format(**values))
    world.say(f'"We solved it together," said {params.child}. {params.friend} grinned. "A pirate crew needs more than one good idea."')
    world.say(ENDINGS[params.ending % len(ENDINGS)].format(**values))

    world.facts.update(
        child=params.child,
        friend=params.friend,
        captain=params.captain,
        island=params.island,
        shutter=params.shutter,
        clue=params.clue,
        incident=params.incident % len(INCIDENTS),
        suspense_cause=incident["cause"],
        helpful_action=incident["deed"].format(**values),
        result=incident["result"],
        friendship=True,
        problem_solved=True,
        historic=True,
    )

    prompts = [
        "Write a child-friendly pirate tale about friendship and problem solving around a historic shutter.",
        f"Tell a pirate adventure in which {params.child} and {params.friend} use different clues to solve a mystery on {params.island}.",
        f"Write a suspenseful but gentle tale featuring {params.shutter}, teamwork, a helpful captain, and a happy ending.",
    ]

    story_qa = [
        QAItem(
            question="Who solved the shutter mystery?",
            answer=f"{params.child} and {params.friend} solved it together by sharing what each of them noticed.",
        ),
        QAItem(
            question="What caused the problem?",
            answer=f"The problem began when {incident['cause']}.",
        ),
        QAItem(
            question=f"How did {params.child} help?",
            answer=f"{params.child} {incident['deed'].format(**values)}.",
        ),
        QAItem(
            question="How did friendship help the crew?",
            answer=f"Friendship helped because the two friends listened to each other and combined their clues instead of working alone.",
        ),
        QAItem(
            question="What changed by the end?",
            answer=f"{incident['result'].capitalize()}. The historic shutter was safe, and the crew could continue its voyage.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a shutter?",
            answer="A shutter is a movable cover for a window or opening, often made of wood or metal.",
        ),
        QAItem(
            question="Why can an old shutter be historic?",
            answer="An old shutter can be historic because it may have survived from an earlier time and carry marks, stories, or designs from people who used it.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means noticing a difficulty, thinking of possible answers, and choosing a safe way to fix it.",
        ),
        QAItem(
            question="How does friendship help solve problems?",
            answer="Friendship helps because friends can listen, share different ideas, encourage one another, and work as a team.",
        ),
        QAItem(
            question="What is a pirate tale?",
            answer="A pirate tale is an adventure story about sailors, ships, islands, discoveries, and bold but thoughtful choices.",
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
        details = []
        if entity.meters:
            details.append(f"meters={entity.meters}")
        if entity.memes:
            details.append(f"memes={entity.memes}")
        lines.append(f"  {entity.id:18} ({entity.kind:9}) {' '.join(details)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A pirate tale about a historic shutter, friendship, and problem solving.")
    parser.add_argument("--child", choices=CHILDREN)
    parser.add_argument("--friend", choices=FRIENDS)
    parser.add_argument("--captain", choices=CAPTAINS)
    parser.add_argument("--island", choices=ISLANDS)
    parser.add_argument("--shutter", choices=SHUTTERS)
    parser.add_argument("--clue", choices=CLUES)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def build_curated() -> list[StoryParams]:
    return [
        StoryParams("Luna", "Bea", "Captain Coral", "Cannonball Cay", "the old red shutter", "a brass compass", 0, 0, 0),
        StoryParams("Milo", "Finn", "Captain Flint", "Moonbeam Isle", "the carved blue shutter", "a striped feather", 1, 1, 1),
        StoryParams("Nia", "Mara", "Captain Marigold", "Shellbell Island", "the round brass shutter", "a silver button", 2, 2, 2),
        StoryParams("Pip", "Otis", "Captain Bluebeard", "Whispering Key", "the weathered green shutter", "a tiny map", 3, 3, 3),
    ]


CURATED = build_curated()


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
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
        print(asp_program("#show valid_story/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combinations = asp_valid_combos()
        print(f"{len(combinations)} compatible child-friend-shutter combinations:\n")
        for child, friend, shutter in combinations[:40]:
            print(f"  {child}, {friend} -> {shutter}")
        if len(combinations) > 40:
            print(f"  ... and {len(combinations) - 40} more")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(50, args.n * 50):
            seed = base_seed + attempt
            attempt += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as error:
                print(error)
                return
            params.seed = seed
            apply_seeded_structure(params, seed)
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
            header = f"### {sample.params.child}: the historic shutter on {sample.params.island}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
