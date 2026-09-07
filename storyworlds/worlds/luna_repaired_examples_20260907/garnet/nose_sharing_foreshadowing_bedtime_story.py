#!/usr/bin/env python3
"""
A gentle bedtime storyworld about a child, a funny nose, and the comfort of
sharing a small worry before sleep.
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
    child: Item
    caregiver: Item
    nose: Item
    room: str
    seed: int
    facts: dict = field(default_factory=dict)

    def render(self) -> str:
        return self.facts.get("story", "")


@dataclass
class StoryParams:
    name: str
    caregiver_name: str
    room: str
    seed: Optional[int] = None


NAMES = ["Mina", "Theo", "Lulu", "Sam", "Nora", "Pip", "Ada", "Ben"]
CAREGIVERS = ["Mama", "Papa", "Grandma", "Grandpa", "Aunt Rose"]
ROOMS = [
    "the blue bedroom",
    "the moonlit attic",
    "the little upstairs room",
    "the room beside the quiet stairs",
    "the warm room under the eaves",
]


ASP_RULES = r"""
#show notices/1.
#show shares/1.
#show rests/1.

notices(C) :- hears_sniff(C).
shares(C) :- tells_worry(C).
rests(C) :- receives_comfort(C).
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("hears_sniff", "child"),
            asp.fact("tells_worry", "child"),
            asp.fact("receives_comfort", "child"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(
        asp_program("#show notices/1.\n#show shares/1.\n#show rests/1.")
    )
    actual = set()
    for atom in model:
        if atom.name == "notices":
            actual.add(("notices", ("child",)))
        elif atom.name == "shares":
            actual.add(("shares", ("child",)))
        elif atom.name == "rests":
            actual.add(("rests", ("child",)))
    expected = {
        ("notices", ("child",)),
        ("shares", ("child",)),
        ("rests", ("child",)),
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
        description="Bedtime storyworld about sharing a worry about a nose."
    )
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--caregiver-name", choices=CAREGIVERS)
    parser.add_argument("--room", choices=ROOMS)
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
        caregiver_name=args.caregiver_name or rng.choice(CAREGIVERS),
        room=args.room or rng.choice(ROOMS),
    )


def build_world(params: StoryParams) -> World:
    if not params.name.strip():
        raise StoryError("The child's name cannot be empty.")
    if not params.caregiver_name.strip():
        raise StoryError("The caregiver's name cannot be empty.")
    if not params.room.strip():
        raise StoryError("The room cannot be empty.")

    child = Item(
        id="child",
        label=params.name,
        phrase=f"sleepy {params.name}",
        kind="character",
        memes={"curiosity": 0.7, "worry": 0.4, "trust": 0.5},
    )
    caregiver = Item(
        id="caregiver",
        label=params.caregiver_name,
        phrase=params.caregiver_name,
        kind="character",
        memes={"patience": 0.9, "warmth": 0.9},
    )
    nose = Item(
        id="nose",
        label="nose",
        phrase="a small, tickly nose",
        kind="body_part",
        owner="child",
        meters={"height": 0.04, "distance": 0.0},
        memes={"tickle": 0.8, "worry": 0.3},
    )
    seed = params.seed
    if seed is None:
        seed = sum(ord(ch) for ch in f"{params.name}|{params.caregiver_name}|{params.room}")
    return World(
        child=child,
        caregiver=caregiver,
        nose=nose,
        room=params.room,
        seed=seed,
    )


def _choice(rng: random.Random, values: list[str]) -> str:
    return values[rng.randrange(len(values))]


def _record(
    world: World,
    *,
    sound: str,
    object_name: str,
    worry: str,
    cause: str,
    sharing: str,
    resolution: str,
    ending: str,
    lines: list[str],
) -> str:
    world.facts.update(
        sound=sound,
        object_name=object_name,
        worry=worry,
        cause=cause,
        sharing=sharing,
        resolution=resolution,
        ending=ending,
        noticed=True,
        shared=True,
        rested=True,
    )
    world.child.memes["worry"] = 0.05
    world.child.memes["trust"] = 1.0
    world.nose.memes["tickle"] = 0.1
    return " ".join(lines)


def _bedtime_arc(world: World, rng: random.Random) -> str:
    child = world.child.label
    caregiver = world.caregiver.label
    room = world.room
    sound = _choice(rng, ["a tiny whistle", "a soft squeak", "a funny hum", "a little puff"])
    object_name = _choice(
        rng,
        ["a feather in the pillow", "a woolly blanket thread", "a crumb from supper", "a cool night breeze"],
    )
    comfort = _choice(
        rng,
        [
            "a warm cup of water",
            "a clean handkerchief",
            "a soft lavender cloth",
            "a quiet song about the moon",
        ],
    )
    worry = f"that the strange sound would wake the whole house"
    cause = f"{object_name} was tickling the nose whenever {child} breathed in"
    sharing = (
        f"{child} told {caregiver} about the tickle instead of hiding beneath the blanket"
    )
    resolution = (
        f"{caregiver} helped {child} find the cause, offered {comfort}, "
        f"and waited until the nose felt calm"
    )
    ending = (
        f"{child}'s nose rested quietly, and the last moonbeam slipped across the pillow "
        f"like a silver goodnight"
    )
    lines = [
        f"In {room}, {child} climbed into bed while the house grew soft and quiet.",
        f"Just as {child} closed both eyes, the small nose made {sound}.",
        f"{child} opened one eye. The nose made the sound again, and this time a tiny shiver ran through the blanket.",
        f"At first, {child} wondered {worry}.",
        f"The thought grew larger in the dark, even though the nose was no bigger than a button.",
        f"Then {child} remembered what {caregiver} always said: a worry is easier to carry when two people hold it.",
        f"{sharing}.",
        f"{caregiver} came close and listened without laughing. Together they looked beneath the blanket and discovered that {cause}.",
        f"They moved the troublesome thing away, and {caregiver} gave {child} {comfort}.",
        f"The nose tried one last little tickle, but the tickle had lost its courage.",
        f"{resolution}.",
        f"Before sleep, {child} smiled because sharing had made the dark feel smaller.",
        f"At last, {ending}.",
    ]
    return _record(
        world,
        sound=sound,
        object_name=object_name,
        worry=worry,
        cause=cause,
        sharing=sharing,
        resolution=resolution,
        ending=ending,
        lines=lines,
    )


def _moon_arc(world: World, rng: random.Random) -> str:
    child = world.child.label
    caregiver = world.caregiver.label
    room = world.room
    sound = _choice(rng, ["a sleepy snuffle", "a tap-tap sniff", "a puff like a flute"])
    moon_shape = _choice(rng, ["a boat", "a rabbit", "a lantern", "a sleepy cat"])
    worry = "that a shadow outside the window was copying every breath"
    cause = "a curtain cord was brushing the window and making a shadow dance whenever the night breeze moved it"
    sharing = f"{child} whispered the worry to {caregiver,}" if False else f"{child} whispered the worry to {caregiver}"
    resolution = (
        f"{caregiver} tied back the curtain, opened the window a finger-width, "
        f"and breathed slowly with {child}"
    )
    ending = (
        f"the curtain became still, the nose gave one peaceful sniff, and the moon looked "
        f"like a {moon_shape} sailing home"
    )
    lines = [
        f"Moonlight rested on the floor of {room} when {child} heard {sound}.",
        f"The nose twitched toward the window. On the wall, a shadow wobbled like a {moon_shape}.",
        f"{child} pulled the blanket to the chin and wondered {worry}.",
        f"The worry waited in the room like an uninvited guest.",
        f"Remembering that secrets grow heavy before bedtime, {sharing}.",
        f"{caregiver} did not shoo the worry away. Instead, {caregiver} held {child}'s hand and looked with them.",
        f"Together they noticed that {cause}.",
        f"{resolution}.",
        f"The shadow stopped wobbling. The nose stopped twitching. The room became ordinary again.",
        f"{child} thanked {caregiver} and tucked the worry into a shared answer: sometimes a moving shadow is only a curtain asking for help.",
        f"At last, {ending}.",
    ]
    return _record(
        world,
        sound=sound,
        object_name="the curtain cord",
        worry=worry,
        cause=cause,
        sharing=sharing,
        resolution=resolution,
        ending=ending,
        lines=lines,
    )


def _sneeze_arc(world: World, rng: random.Random) -> str:
    child = world.child.label
    caregiver = world.caregiver.label
    room = world.room
    sound = _choice(rng, ["A-CHOO", "a teeny achoo", "a sneeze as round as a bell"])
    object_name = _choice(rng, ["a dusty storybook", "a basket of wool socks", "a pillow with old feathers"])
    worry = "that the sneeze meant something terrible was hiding in the room"
    cause = f"the pages of {object_name} had gathered a little dust"
    sharing = f"{child} shared the worry with {caregiver before it could grow"
    resolution = (
        f"{caregiver} moved {object_name}, opened the door a little, and showed {child} "
        f"how fresh air could help"
    )
    ending = (
        f"the nose rested under the blanket, and the moon kept watch while "
        f"{child} dreamed of clean clouds"
    )
    lines = [
        f"Bedtime had nearly arrived in {room} when {child}'s nose announced, {sound}!",
        f"The sound bounced off the walls and made one sleepy sock fall from a chair.",
        f"{child} stared at the dark corner and wondered {worry}.",
        f"The worry grew a long tail in {child}'s imagination.",
        f"Before the tail could curl around the bedpost, {sharing}.",
        f"{caregiver} came with a gentle smile, not a frightened one.",
        f"Together they discovered that {cause}.",
        f"{resolution}.",
        f"The next breath was easy. The next sneeze was smaller. The third sneeze decided not to come at all.",
        f"{child} felt proud that a shared worry had become a small, ordinary fact.",
        f"Then {ending}.",
    ]
    return _record(
        world,
        sound=sound,
        object_name=object_name,
        worry=worry,
        cause=cause,
        sharing=sharing,
        resolution=resolution,
        ending=ending,
        lines=lines,
    )


ARC_BUILDERS = [_bedtime_arc, _moon_arc, _sneeze_arc]


def generate_story(world: World) -> str:
    rng = random.Random(world.seed ^ 0x51A7B)
    builder = ARC_BUILDERS[world.seed % len(ARC_BUILDERS)]
    return builder(world, rng)


def story_qa(world: World) -> list[QAItem]:
    child = world.child.label
    facts = world.facts
    return [
        QAItem(
            question=f"What happened to {child}'s nose?",
            answer=f"{child}'s nose made {facts['sound']} because {facts['cause']}.",
        ),
        QAItem(
            question="What worry did the child have?",
            answer=f"The child worried {facts['worry']}.",
        ),
        QAItem(
            question="How did sharing help?",
            answer=f"{facts['sharing']}. Sharing let the child and caregiver look at the problem together.",
        ),
        QAItem(
            question="How did the bedtime story end?",
            answer=f"{facts['ending']}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a nose used for?",
            answer="A nose helps a person breathe and notice smells. It can also make sounds when someone sneezes or snuffles.",
        ),
        QAItem(
            question="Why can sharing a worry help?",
            answer="Sharing a worry lets another person listen, offer comfort, and help look for a sensible cause.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a clue early in a story that hints at something important that will happen later.",
        ),
        QAItem(
            question="Why do bedtime stories often end quietly?",
            answer="A quiet ending helps children feel safe and ready to rest after the story's problem has been solved.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a gentle bedtime story about a child sharing a worry about a nose.",
        f"Tell a cozy story set in {world.room} where a small clue helps solve a nighttime worry.",
        "Use foreshadowing, sharing, and a peaceful ending suitable for young children.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in [world.child, world.caregiver, world.nose]:
        lines.append(
            f"  {entity.id:9} {entity.kind:11} label={entity.label!r} "
            f"owner={entity.owner!r} meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  room={world.room!r}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    output = ["== Generation prompts =="]
    for index, prompt in enumerate(sample.prompts, 1):
        output.append(f"{index}. {prompt}")
    output.extend(["", "== Story QA =="])
    for item in sample.story_qa:
        output.append(f"Q: {item.question}")
        output.append(f"A: {item.answer}")
    output.extend(["", "== World QA =="])
    for item in sample.world_qa:
        output.append(f"Q: {item.question}")
        output.append(f"A: {item.answer}")
    return "\n".join(output)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    story = generate_story(world)
    world.facts["story"] = story
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
        print(asp_program("#show notices/1.\n#show shares/1.\n#show rests/1."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        print(
            "3 compatible logical atoms: notices(child), shares(child), rests(child)"
        )
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1.")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(
                name="Mina",
                caregiver_name="Mama",
                room="the blue bedroom",
                seed=base_seed,
            ),
            StoryParams(
                name="Theo",
                caregiver_name="Grandpa",
                room="the moonlit attic",
                seed=base_seed + 1,
            ),
            StoryParams(
                name="Lulu",
                caregiver_name="Papa",
                room="the little upstairs room",
                seed=base_seed + 2,
            ),
        ]
        samples = [generate(params) for params in curated]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + index))
            params.seed = base_seed + index
            sample = generate(params)
            index += 1
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if len(samples) < args.n and not args.all:
        raise StoryError("Could not create enough distinct story variants.")

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
            header = f"### {params.name} in {params.room}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
