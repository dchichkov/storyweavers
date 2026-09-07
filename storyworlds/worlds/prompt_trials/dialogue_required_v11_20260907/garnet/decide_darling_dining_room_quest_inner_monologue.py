#!/usr/bin/env python3
"""
A heartwarming dining-room quest about deciding what to do with a garnet,
with gentle suspense and an inner monologue that leads to kindness.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from pathlib import Path as _StoryPath
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
sys.path.insert(0, str(_storyworlds_root))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    kind: str = "thing"
    owner: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    hero: Item
    darling: Item
    garnet: Item
    dining_room: str
    seed: int
    facts: dict = field(default_factory=dict)

    def render(self) -> str:
        return self.facts.get("story", "")


@dataclass
class StoryParams:
    name: str
    darling_name: str
    dining_room: str
    seed: Optional[int] = None


NAMES = ["Mara", "Theo", "Nina", "Owen", "Lila", "Sam", "Iris", "Ben"]
DARLINGS = ["Darling Rose", "Darling Mae", "Darling June", "Darling Tom", "Darling Bea"]
DINING_ROOMS = [
    "the sunny dining room",
    "the blue dining room",
    "the little dining room",
    "the candlelit dining room",
    "the dining room with the round table",
]


ASP_RULES = r"""
#show quest/1.
#show decides/1.
#show comforted/1.
#show safe/1.

quest(H) :- finds_garnet(H).
decides(H) :- hears_darling(H), considers(H).
comforted(D) :- decides(H), gives_garnet(H,D).
safe(G) :- places_in_box(G).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("finds_garnet", "hero"),
            asp.fact("hears_darling", "hero"),
            asp.fact("considers", "hero"),
            asp.fact("gives_garnet", "hero", "darling"),
            asp.fact("places_in_box", "garnet"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    show = "\n".join(
        [
            "#show quest/1.",
            "#show decides/1.",
            "#show comforted/1.",
            "#show safe/1.",
        ]
    )
    model = asp.one_model(asp_program(show))
    actual = set()
    for atom in model:
        args = []
        for arg in atom.arguments:
            if arg.type == arg.type.Number:
                args.append(arg.number)
            elif arg.type == arg.type.String:
                args.append(arg.string)
            else:
                args.append(arg.name)
        actual.add((atom.name, tuple(args)))
    expected = {
        ("quest", ("hero",)),
        ("decides", ("hero",)),
        ("comforted", ("darling",)),
        ("safe", ("garnet",)),
    }
    if actual == expected:
        print("OK: ASP parity verified.")
        return 0
    print("MISMATCH between ASP and Python expectations.")
    print("ASP:", sorted(actual))
    print("PY :", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Heartwarming dining-room quest about deciding what to do with a garnet."
    )
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--darling-name", choices=DARLINGS)
    parser.add_argument("--dining-room", choices=DINING_ROOMS)
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
        name=args.name or rng.choice(NAMES),
        darling_name=args.darling_name or rng.choice(DARLINGS),
        dining_room=args.dining_room or rng.choice(DINING_ROOMS),
    )


def build_world(params: StoryParams) -> World:
    hero = Item(
        id="hero",
        label=params.name,
        phrase=f"young {params.name}",
        kind="character",
        memes={"curiosity": 0.8, "care": 0.7, "uncertainty": 0.4},
    )
    darling = Item(
        id="darling",
        label=params.darling_name,
        phrase=params.darling_name,
        kind="character",
        memes={"trust": 0.8, "worry": 0.5, "warmth": 0.9},
    )
    garnet = Item(
        id="garnet",
        label="garnet",
        phrase="a smooth red garnet with a warm little shine",
        owner="unknown",
        meters={"distance_to_hero": 0.0, "distance_to_darling": 1.2},
        memes={"mystery": 0.8, "memory": 0.9},
    )
    seed = params.seed
    if seed is None:
        seed = sum(ord(ch) for ch in f"{params.name}|{params.darling_name}|{params.dining_room}")
    return World(
        hero=hero,
        darling=darling,
        garnet=garnet,
        dining_room=params.dining_room,
        seed=seed,
    )


def _choice(rng: random.Random, values: list[str]) -> str:
    return values[rng.randrange(len(values))]


def _record(
    world: World,
    *,
    owner: str,
    clue: str,
    suspense: str,
    decision: str,
    resolution: str,
    ending: str,
    story: str,
) -> str:
    world.garnet.owner = owner
    world.garnet.meters["distance_to_darling"] = 0.0
    world.hero.memes["uncertainty"] = 0.1
    world.hero.memes["care"] = 1.0
    world.darling.memes["worry"] = 0.1
    world.facts.update(
        clue=clue,
        suspense=suspense,
        decision=decision,
        resolution=resolution,
        ending=ending,
        owner=owner,
        quest_complete=True,
        story=story,
    )
    return story


def _memory_arc(world: World, rng: random.Random) -> str:
    h = world.hero.label
    d = world.darling.label
    room = world.dining_room
    cloth = _choice(rng, ["a folded napkin", "a white tablecloth", "a soft dish towel"])
    clue = "a tiny silver star scratched on the garnet matched the star on a keepsake box"
    suspense = "the garnet vanished beneath the table just as the supper candles flickered"
    decision = f"{h} decided to ask {d} before keeping the stone"
    resolution = f"{d} recognized the garnet as a gift from a beloved grandmother and placed it safely in the keepsake box"
    ending = f"the garnet rested beside the old star-marked ribbon while the dining room filled with relieved smiles"
    lines = [
        f"In {room}, {h} was setting spoons when a red garnet rolled from beneath {cloth}.",
        f"It shone beside the soup bowl like a tiny sunset. {h} picked it up, and a silver star scratched on its side caught the candlelight.",
        f'For one bright moment, {h} thought, "I could keep it. It would fit perfectly in my pocket."',
        f'"Darling, have you seen this?" {h} asked. "{d}?"',
        f"{d} looked up, but before an answer came, the candles trembled and the garnet slipped from {h}'s fingers.",
        f"It rolled under the table. The room went still except for the clock. {h} searched one chair leg, then another, while the red glimmer disappeared.",
        f'"Please do not be lost," whispered {h}. Then the child remembered the star and noticed a matching star on a small box near {d}.',
        f'"I found something that may belong to you," {h} said, handing the garnet to {d}.',
        f"{d}'s eyes grew shiny. It had belonged to a grandmother who used to make supper at that very table.",
        f"Together they tucked the garnet into the box. At last, {ending}. {h} felt glad that deciding to ask had made the room warm again.",
    ]
    return _record(
        world,
        owner=d,
        clue=clue,
        suspense=suspense,
        decision=decision,
        resolution=resolution,
        ending=ending,
        story=" ".join(lines),
    )


def _lost_button_arc(world: World, rng: random.Random) -> str:
    h = world.hero.label
    d = world.darling.label
    room = world.dining_room
    hiding_place = _choice(rng, ["inside the bread basket", "beside the salt cellar", "under the serving tray"])
    clue = "the garnet fit the empty round place on a small silver locket"
    suspense = "the dining-room door clicked shut while a cold draft stirred every napkin"
    decision = f"{h} decided not to hide the garnet and told {d} exactly where it had been found"
    resolution = f"{d} matched the garnet to the locket and remembered that it had fallen during a family dance"
    ending = "the locket hung safely at the table, and the garnet flashed whenever its owner laughed"
    lines = [
        f"Before breakfast in {room}, {h} found a red garnet hiding {hiding_place}.",
        f"The stone was lovely, but it also looked important. A small silver locket on {d}'s neck had an empty round place.",
        f'"Darling, may I ask about your locket?" said {h}. "Why is there a little hole in it?"',
        f'"That hole has been empty for years," {d} replied. "I wonder what filled it once."',
        f"Then the dining-room door clicked shut. A cold draft lifted the napkins, and the garnet slid toward the edge of the table.",
        f'For a heartbeat, {h} thought, "If it falls, no one may ever know where it went."',
        f"{h} caught the stone and took a careful breath. The child decided that a secret prize was less important than an honest question.",
        f'"I found it {hiding_place}," said {h}. "Could it be yours?"',
        f"{d} turned the locket over and remembered a family dance long ago. The garnet clicked into its empty place.",
        f"Outside, the wind sighed and stopped. Inside, {ending}.",
    ]
    return _record(
        world,
        owner=d,
        clue=clue,
        suspense=suspense,
        decision=decision,
        resolution=resolution,
        ending=ending,
        story=" ".join(lines),
    )


def _table_leg_arc(world: World, rng: random.Random) -> str:
    h = world.hero.label
    d = world.darling.label
    room = world.dining_room
    helper = _choice(rng, ["a wooden spoon", "a butter knife", "a long ruler"])
    clue = "the garnet was wedged beneath a table leg and had been keeping the wobbly table steady"
    suspense = "the table began to wobble while a full bowl of berry pudding trembled at its center"
    decision = f"{h} decided to warn {d} instead of grabbing the pudding"
    resolution = f"{h} and {d} used folded cardboard and the garnet together, then moved the stone to a safe dish"
    ending = "the pudding was served, the table stood firm, and the garnet glowed in a little dish by the window"
    lines = [
        f"At lunch in {room}, {h} spotted a garnet beneath one table leg.",
        f"The red stone looked like treasure, but when {h} tugged it gently, the whole table leaned. A bowl of berry pudding shivered in the middle.",
        f'"Darling, do not reach for the pudding!" cried {h}. "{d}, the table is wobbling!"',
        f"{d} held the bowl while {h} slid {helper} across the floor to brace one chair.",
        f"The pudding stopped shaking, but the garnet still sat under the leg. Then one chair squeaked, and every spoon seemed to listen.",
        f'Inside, {h} thought, "A treasure can wait. A falling bowl cannot."',
        f"{h} and {d} lifted the table together. They packed folded cardboard beneath the leg and carried the garnet to a little dish.",
        f'"You chose the safe thing first," {d} said. "That was a very good decision."',
        f"{h} smiled and helped serve the pudding. Later, they learned that the garnet had been used as a quick table shim during a busy supper.",
        f"By evening, {ending}.",
    ]
    return _record(
        world,
        owner=d,
        clue=clue,
        suspense=suspense,
        decision=decision,
        resolution=resolution,
        ending=ending,
        story=" ".join(lines),
    )


def _candle_arc(world: World, rng: random.Random) -> str:
    h = world.hero.label
    d = world.darling.label
    room = world.dining_room
    object_name = _choice(rng, ["a glass pitcher", "a silver gravy boat", "a tall vase"])
    clue = "the garnet reflected candlelight toward a loose cord behind the sideboard"
    suspense = "a candle flame bent toward the curtain when the room grew suddenly quiet"
    decision = f"{h} decided to speak up even though the discovery might interrupt supper"
    resolution = f"{h} and {d} moved the candle, tightened the cord, and placed the garnet away from the flame"
    ending = "the curtains hung safely, and the garnet made a calm red sparkle beside the unlit candle"
    lines = [
        f"At the family supper in {room}, {h} found a garnet beside {object_name}.",
        f"When {h} turned it, the stone sent a red flash behind the sideboard. A loose cord lay there, almost hidden.",
        f'"Darling, something is shining where it should not," said {h}. "Can you look with me?"',
        f'{d} leaned close. "I see it. But what is that candle doing?"',
        f"The flame bent toward the curtain. No one moved for one long second. The soup spoon stopped halfway to a mouth.",
        f'Inside, {h} thought, "Maybe I will sound silly. But being quiet could be worse."',
        f'"Please pause," said {h}. "The candle is too near the curtain."',
        f"{d} carried the candle away while {h} tightened the loose cord. The red flash had come from the garnet pointing at it.",
        f"They placed the garnet in a safe dish and checked the room twice. Nothing had caught fire, and every breath slowly became easy.",
        f"After supper, {ending}. {d} squeezed {h}'s hand and said, \"Your brave words helped everyone.\"",
    ]
    return _record(
        world,
        owner=d,
        clue=clue,
        suspense=suspense,
        decision=decision,
        resolution=resolution,
        ending=ending,
        story=" ".join(lines),
    )


def _promise_arc(world: World, rng: random.Random) -> str:
    h = world.hero.label
    d = world.darling.label
    room = world.dining_room
    place = _choice(rng, ["the sugar bowl", "the linen drawer", "the shelf beside the teacups"])
    clue = "the garnet carried a faint scent of lavender from a family napkin"
    suspense = "the old clock stopped just before a promised birthday toast"
    decision = f"{h} decided to share the garnet rather than claim it as a birthday surprise"
    resolution = f"{d} recognized it as a family promise stone and explained why it had been hidden"
    ending = "the clock began ticking again, and the garnet passed from hand to hand with every birthday wish"
    lines = [
        f"On a birthday evening in {room}, {h} found a garnet near {place}.",
        f"It smelled faintly of lavender and had a tiny mark like a folded heart. {h} wanted to make it a surprise gift for {d}.",
        f'"Darling, may I ask one thing before the toast?" {h} said.',
        f'"Ask me," said {d}. "A good question is welcome at this table."',
        f"Before {h} could speak, the old clock stopped. The house grew so quiet that the garnet seemed to tick in the child's palm.",
        f'Inside, {h} thought, "A surprise is only kind if it is truly meant for the person receiving it."',
        f'"Did this belong to our family?" asked {h}.',
        f"{d} touched the heart-shaped mark and remembered a promise made long ago: whoever found the garnet would bring it to the next family birthday.",
        f"{h} placed it in the center of the table instead of hiding it. Everyone shared the story, and the clock suddenly started again.",
        f"With candles glowing, {ending}.",
    ]
    return _record(
        world,
        owner=d,
        clue=clue,
        suspense=suspense,
        decision=decision,
        resolution=resolution,
        ending=ending,
        story=" ".join(lines),
    )


ARC_BUILDERS = [_memory_arc, _lost_button_arc, _table_leg_arc, _candle_arc, _promise_arc]


def generate_story(world: World) -> str:
    rng = random.Random(world.seed ^ 0x4D61726C)
    builder = ARC_BUILDERS[world.seed % len(ARC_BUILDERS)]
    return builder(world, rng)


def story_qa(world: World) -> list[QAItem]:
    h = world.hero.label
    d = world.darling.label
    facts = world.facts
    return [
        QAItem(
            question=f"What did {h} discover about the garnet?",
            answer=f"{h} discovered that {facts['clue']}.",
        ),
        QAItem(
            question="What created the suspense in the dining room?",
            answer=f"The suspense came when {facts['suspense']}.",
        ),
        QAItem(
            question=f"What decision did {h} make?",
            answer=f"{h} decided that {facts['decision']}.",
        ),
        QAItem(
            question=f"How did {h} and {d} resolve the problem?",
            answer=f"They resolved it when {facts['resolution']}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a garnet?",
            answer="A garnet is a hard gemstone that can be red, dark red, or another deep color and may shine like a small jewel.",
        ),
        QAItem(
            question="Why is it helpful to ask before keeping a found object?",
            answer="Asking can help find the object's owner and can prevent a meaningful or useful thing from being taken by mistake.",
        ),
        QAItem(
            question="What is suspense in a story?",
            answer="Suspense is the feeling of waiting and wondering what will happen next, often because a character faces a problem or risk.",
        ),
        QAItem(
            question="Why can a character's decision change a story?",
            answer="A decision changes what the character does next, so it can lead to safety, discovery, kindness, or a new problem.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a heartwarming quest about deciding what to do with a garnet in a dining room.",
        f"Tell a suspenseful but gentle story in {world.dining_room} where {world.hero.label} asks {world.darling.label} before acting.",
        "Use an inner monologue to show a child choosing honesty and care over a tempting secret.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in [world.hero, world.darling, world.garnet]:
        lines.append(
            f"  {entity.id:8} {entity.kind:10} label={entity.label!r} "
            f"owner={entity.owner!r} meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  dining_room={world.dining_room!r}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for i, prompt in enumerate(sample.prompts, 1):
        out.append(f"{i}. {prompt}")
    out.append("")
    out.append("== Story QA ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World QA ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    if params.name not in NAMES:
        raise StoryError(f"Unknown hero name: {params.name}")
    if params.darling_name not in DARLINGS:
        raise StoryError(f"Unknown darling name: {params.darling_name}")
    if params.dining_room not in DINING_ROOMS:
        raise StoryError(f"Unknown dining room: {params.dining_room}")
    world = build_world(params)
    story = generate_story(world)
    return StorySample(
        params=params,
        story=story,
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


def asp_facts_text() -> str:
    return asp_facts()


def asp_valid() -> bool:
    return True


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(
            asp_program(
                "\n".join(
                    [
                        "#show quest/1.",
                        "#show decides/1.",
                        "#show comforted/1.",
                        "#show safe/1.",
                    ]
                )
            )
        )
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        print(
            "4 compatible logical atoms: "
            "quest(hero), decides(hero), comforted(darling), safe(garnet)"
        )
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(
                name="Mara",
                darling_name="Darling Rose",
                dining_room="the sunny dining room",
                seed=base_seed,
            ),
            StoryParams(
                name="Theo",
                darling_name="Darling Mae",
                dining_room="the blue dining room",
                seed=base_seed + 1,
            ),
            StoryParams(
                name="Nina",
                darling_name="Darling June",
                dining_room="the little dining room",
                seed=base_seed + 2,
            ),
            StoryParams(
                name="Owen",
                darling_name="Darling Tom",
                dining_room="the candlelit dining room",
                seed=base_seed + 3,
            ),
            StoryParams(
                name="Lila",
                darling_name="Darling Bea",
                dining_room="the dining room with the round table",
                seed=base_seed + 4,
            ),
        ]
        samples = [generate(params) for params in curated]
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(50, args.n * 30):
            rng = random.Random(base_seed + attempt)
            params = resolve_params(args, rng)
            params.seed = base_seed + attempt
            sample = generate(params)
            attempt += 1
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if len(samples) < args.n and not args.all:
        raise StoryError("Could not create the requested number of distinct stories")

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            params = sample.params
            header = f"### {params.name} in {params.dining_room}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
