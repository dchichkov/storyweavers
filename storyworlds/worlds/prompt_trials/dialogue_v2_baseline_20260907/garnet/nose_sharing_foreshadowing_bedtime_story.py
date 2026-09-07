#!/usr/bin/env python3
"""
A gentle bedtime storyworld about a nose, a small secret, and the comfort of
sharing before sleep.
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
class Entity:
    id: str
    label: str
    kind: str
    owner: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    child: Entity
    caregiver: Entity
    nose: Entity
    room: str
    seed: int
    facts: dict = field(default_factory=dict)


@dataclass
class StoryParams:
    name: str
    caregiver_name: str
    room: str
    seed: Optional[int] = None


NAMES = ["Mina", "Theo", "Lulu", "Sam", "Nora", "Pip", "Ada", "Ben"]
CAREGIVERS = ["Mama", "Papa", "Grandma", "Grandpa", "Aunt Rose"]
ROOMS = [
    "the moonlit bedroom",
    "the little attic room",
    "the blue bedroom",
    "the room beside the quiet garden",
    "the warm room under the eaves",
]


ASP_RULES = r"""
#show notices/1.
#show shares/1.
#show rests/1.

notices(child) :- nose_glows.
shares(child) :- tells_secret.
rests(child) :- shares(child), caregiver_listens.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("nose_glows"),
            asp.fact("tells_secret"),
            asp.fact("caregiver_listens"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(
        asp_program(
            "#show notices/1.\n#show shares/1.\n#show rests/1."
        )
    )
    found = set()
    for atom in model:
        if atom.name == "notices":
            found.add(("notices", "child"))
        elif atom.name == "shares":
            found.add(("shares", "child"))
        elif atom.name == "rests":
            found.add(("rests", "child"))
    expected = {
        ("notices", "child"),
        ("shares", "child"),
        ("rests", "child"),
    }
    if found == expected:
        print("OK: ASP parity verified.")
        return 0
    print("MISMATCH between ASP and Python expectations.")
    print("ASP:", sorted(found))
    print("PY :", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Bedtime storyworld about sharing a nose-shaped secret."
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
    child = Entity(
        id="child",
        label=params.name,
        kind="child",
        meters={"sleepiness": 0.25, "distance_to_bed": 2.0},
        memes={"curiosity": 0.8, "worry": 0.35, "trust": 0.75},
    )
    caregiver = Entity(
        id="caregiver",
        label=params.caregiver_name,
        kind="caregiver",
        meters={"distance_to_bed": 1.0},
        memes={"patience": 0.95, "warmth": 0.9},
    )
    nose = Entity(
        id="nose",
        label="nose",
        kind="body_part",
        owner="child",
        meters={"distance_to_face": 0.0, "glow": 0.0},
        memes={"scent_memory": 0.7, "tickle": 0.4},
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
    discovery: str,
    foreshadowing: str,
    trouble: str,
    cause: str,
    sharing: str,
    resolution: str,
    ending: str,
    lines: list[str],
) -> str:
    world.facts.update(
        discovery=discovery,
        foreshadowing=foreshadowing,
        trouble=trouble,
        cause=cause,
        sharing=sharing,
        resolution=resolution,
        ending=ending,
        noticed=True,
        shared=True,
        rested=True,
    )
    world.nose.meters["glow"] = 1.0
    world.child.memes["worry"] = 0.08
    world.child.memes["trust"] = 0.98
    world.child.meters["sleepiness"] = 1.0
    return " ".join(lines)


def _moon_dust_arc(world: World, rng: random.Random) -> str:
    h = world.child.label
    c = world.caregiver.label
    room = world.room
    speck = _choice(
        rng,
        ["a silver speck", "a pale blue shimmer", "a tiny pearl of light"],
    )
    sound = _choice(
        rng,
        ["a soft whistle", "a sleepy hum", "a breathy ping"],
    )
    discovery = f"{speck} was hiding beside {h}'s nose"
    foreshadowing = f"the nose had tingled whenever the moonbeam crossed the pillow"
    trouble = "the moon-dust began sneezing bright sparks across the room"
    cause = "the spark had slipped into the warm fold beside the nose and tickled it"
    sharing = f"{h} told {c} about the tingling instead of keeping the secret alone"
    resolution = (
        f"{c} listened, folded a cool cloth, and helped {h} breathe slowly until "
        f"the moon-dust floated safely into a glass of water"
    )
    ending = (
        f"{h} and {c} watched the last spark settle while the nose gave one tiny "
        f"'{sound}' and then grew peaceful"
    )
    lines = [
        f"In {room}, {h} was almost asleep when the nose began to tingle.",
        f"It had tingled each night whenever a moonbeam crossed the pillow, but {h} had said nothing.",
        f"Tonight {h} rubbed the nose gently and saw {speck} glowing beside it.",
        f"The child held very still. Then the nose gave {sound}, and bright specks "
        f"skittered over the blanket.",
        f'"Oh dear," whispered {h}. "My nose is keeping the stars awake."',
        f"{c} came quietly to the bedside. {h} shared the secret, and {c} did not laugh or hurry.",
        f"{c} listened to the tickle, placed a cool cloth near the nose, and guided "
        f"{h} through slow breaths. The moon-dust drifted into a waiting glass.",
        f"By the time the room grew still, {sharing}.",
        f"At last, {ending}. Then {h} slept, knowing a small worry becomes softer when it is shared.",
    ]
    return _record(
        world,
        discovery=discovery,
        foreshadowing=foreshadowing,
        trouble=trouble,
        cause=cause,
        sharing=sharing,
        resolution=resolution,
        ending=ending,
        lines=lines,
    )


def _bread_arc(world: World, rng: random.Random) -> str:
    h = world.child.label
    c = world.caregiver.label
    room = world.room
    scent = _choice(
        rng,
        ["warm cinnamon bread", "honey toast", "fresh oat cakes"],
    )
    object_name = _choice(
        rng,
        ["a red button", "a wooden bead", "a yellow bead"],
    )
    discovery = f"the nose could smell {scent} from far away"
    foreshadowing = "the nose had twitched each time the evening wind came from the kitchen"
    trouble = f"{h} followed the scent and found {object_name} lodged beneath a basket"
    cause = f"the basket had been covering a warm loaf of {scent}, while the loose {object_name} tickled the nose"
    sharing = f"{h} called for {c} and shared both the scent and the strange tickle"
    resolution = (
        f"{c} lifted the basket, removed the {object_name} safely, and shared a "
        f"small piece of {scent} with {h}"
    )
    ending = "the nose rested above a smiling mouth while the kitchen smell faded into dreams"
    lines = [
        f"That night in {room}, {h}'s nose woke before the rest of the child.",
        f"It had twitched whenever the evening wind came from the kitchen, though {h} had only smiled and turned over.",
        f"Now the nose smelled {scent}. It also felt a funny little tickle.",
        f"{h} followed the scent past the slippers and found {object_name} beneath a basket.",
        f'"My nose knows something," whispered {h}. "But I do not know what it knows."',
        f"{c} arrived with a sleepy candle. {h} shared the scent and the tickle instead of poking underneath alone.",
        f"Together they lifted the basket. The warm bread was safe, and the loose {object_name} had been tickling the nose.",
        f"{c} removed it carefully and offered {h} a small piece of {scent}.",
        f"Then {h} returned to bed. Soon {ending}. The nose, the bread, and the moon all settled down together.",
    ]
    return _record(
        world,
        discovery=discovery,
        foreshadowing=foreshadowing,
        trouble=trouble,
        cause=cause,
        sharing=sharing,
        resolution=resolution,
        ending=ending,
        lines=lines,
    )


def _rain_arc(world: World, rng: random.Random) -> str:
    h = world.child.label
    c = world.caregiver.label
    room = world.room
    scent = _choice(
        rng,
        ["rain on the roof", "wet lavender", "the sleepy garden"],
    )
    discovery = f"the nose could find a hidden drip by smelling {scent}"
    foreshadowing = "the nose had noticed a cool, damp feeling near the curtain before bedtime"
    trouble = "a tiny roof leak began dripping toward the storybooks"
    cause = "the rain had slipped through a loose tile and the nose noticed the damp air first"
    sharing = f"{h} shared the nose's warning with {c}"
    resolution = (
        f"{c} moved the books, placed a bowl beneath the drip, and tucked a cloth "
        f"around the loose window edge"
    )
    ending = "the bowl caught the last drop like a little silver bell"
    lines = [
        f"Rain whispered over {room}, and {h} tucked beneath the blanket.",
        f"Earlier, the nose had noticed a cool damp feeling near the curtain, but it seemed too small to mention.",
        f"Now the nose smelled {scent}. Drip.",
        f"Another drop landed beside the bedtime storybooks.",
        f'"My nose is telling me something," said {h}, sitting up.',
        f"{h} shared the warning with {c}, who listened as carefully as if the nose were reading a map.",
        f"{c} moved the books, set down a bowl, and tucked a cloth around the loose window edge.",
        f"The drip slowed. The room grew warm again. {h} thanked the nose for noticing first.",
        f"At last, {ending}. {h} fell asleep to the gentle rhythm of rain kept safely outside.",
    ]
    return _record(
        world,
        discovery=discovery,
        foreshadowing=foreshadowing,
        trouble=trouble,
        cause=cause,
        sharing=sharing,
        resolution=resolution,
        ending=ending,
        lines=lines,
    )


def _dream_arc(world: World, rng: random.Random) -> str:
    h = world.child.label
    c = world.caregiver.label
    room = world.room
    dream_shape = _choice(
        rng,
        ["a purple elephant", "a round cloud", "a tiny sailing boat"],
    )
    discovery = f"the nose could make a dream feel real by remembering a gentle scent"
    foreshadowing = "the nose had remembered a faint flower smell before the dream began"
    trouble = f"{dream_shape} grew enormous whenever {h} tried to hide the dream"
    cause = "the hidden worry made every dream-picture grow larger"
    sharing = f"{h} described the dream to {c}, sharing its shape and its frightening feeling"
    resolution = (
        f"{c} named the dream aloud, opened the curtain to the real moon, and "
        f"breathed slowly with {h}"
    )
    ending = "the dream-shape became a small paper picture tucked beneath the pillow"
    lines = [
        f"At bedtime in {room}, {h}'s nose remembered a faint flower smell.",
        f"The nose had noticed it before the dream began, like a quiet bell that nobody else could hear.",
        f"When {h} closed both eyes, {dream_shape} floated across the ceiling.",
        f"It grew larger each time {h} tried to hide the dream under the blanket.",
        f'"Go away," whispered {h}. The dream only became wider and wobblier.',
        f"{c} sat beside the bed. {h} shared the dream's shape and the frightened feeling.",
        f"{c} named the dream aloud, opened the curtain to the real moon, and breathed slowly with {h}.",
        f"The dream shrank from a giant picture to a little patch of color.",
        f"By midnight, {ending}. The nose remembered flowers, the child remembered calm, and sleep returned.",
    ]
    return _record(
        world,
        discovery=discovery,
        foreshadowing=foreshadowing,
        trouble=trouble,
        cause=cause,
        sharing=sharing,
        resolution=resolution,
        ending=ending,
        lines=lines,
    )


def _lantern_arc(world: World, rng: random.Random) -> str:
    h = world.child.label
    c = world.caregiver.label
    room = world.room
    animal = _choice(rng, ["a sleepy mouse", "a little moth", "a shivering wren"])
    discovery = f"the nose could smell {animal} hiding near the blanket chest"
    foreshadowing = "the nose had caught a soft dusty smell whenever the floorboard creaked"
    trouble = f"{animal} became frightened and tugged the bedtime lantern's ribbon"
    cause = "the animal had entered through a crack and was looking for a warm place"
    sharing = f"{h} shared the nose's clue with {c} before reaching into the dark"
    resolution = (
        f"{c} lifted the blanket chest lid slowly, placed a crumb outside, and "
        f"guided {animal} back toward the garden"
    )
    ending = "the lantern rested safely on the table, and tiny footsteps faded into the grass"
    lines = [
        f"The lantern glowed softly in {room} while {h} prepared for sleep.",
        f"The nose had caught a dusty smell whenever the floorboard creaked, but {h} thought it was only an old board.",
        f"Then {h} heard a rustle near the blanket chest.",
        f"{animal} peeped out and tugged the lantern's ribbon. The flame wobbled.",
        f'"I smell a small visitor," whispered {h}. "I think it is scared."',
        f"{h} shared the clue with {c} before reaching into the dark.",
        f"{c} lifted the lid slowly, placed a crumb outside, and showed {animal} the way to the garden.",
        f"The little visitor hurried out. {h} and {c} watched until the grass became still.",
        f"Then {ending}. The nose had noticed, sharing had helped, and the whole room could sleep.",
    ]
    return _record(
        world,
        discovery=discovery,
        foreshadowing=foreshadowing,
        trouble=trouble,
        cause=cause,
        sharing=sharing,
        resolution=resolution,
        ending=ending,
        lines=lines,
    )


ARCS = [_moon_dust_arc, _bread_arc, _rain_arc, _dream_arc, _lantern_arc]


def generate_story(world: World) -> str:
    rng = random.Random(world.seed ^ 0x4E4F5345)
    builder = ARCS[world.seed % len(ARCS)]
    return builder(world, rng)


def story_qa(world: World) -> list[QAItem]:
    h = world.child.label
    facts = world.facts
    return [
        QAItem(
            question=f"What did {h}'s nose notice?",
            answer=f"{h}'s nose noticed that {facts['discovery']}.",
        ),
        QAItem(
            question="What clue came before the trouble?",
            answer=f"Before the trouble, {facts['foreshadowing']}.",
        ),
        QAItem(
            question=f"How did {h} use sharing to solve the problem?",
            answer=f"{h} shared the clue with the caregiver, and {facts['resolution']}.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"The story ended when {facts['ending']}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a nose help a person do?",
            answer="A nose helps a person breathe and notice smells in the air.",
        ),
        QAItem(
            question="Why can sharing a worry help?",
            answer="Sharing a worry lets another person understand it and may bring comfort or useful help.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is an early clue that quietly hints at something important that will happen later.",
        ),
        QAItem(
            question="Why is bedtime a good setting for a gentle story?",
            answer="Bedtime is quiet and comforting, so a gentle story can help a child feel safe and ready to sleep.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a gentle bedtime story about a child whose nose notices an important clue.",
        f"Tell a soothing story set in {world.room} where sharing turns a small worry into comfort.",
        "Use foreshadowing, a nose, and a calm ending to show why it is good to tell someone what you notice.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in [world.child, world.caregiver, world.nose]:
        lines.append(
            f"  {entity.id:9} {entity.kind:10} label={entity.label!r} "
            f"owner={entity.owner!r} meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  room={world.room!r}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for index, prompt in enumerate(sample.prompts, 1):
        out.append(f"{index}. {prompt}")
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
    world = build_world(params)
    story = generate_story(world)
    if not story.strip():
        raise StoryError("Generated story is empty.")
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
        print(
            asp_program(
                "#show notices/1.\n#show shares/1.\n#show rests/1."
            )
        )
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        print(
            "3 compatible logical atoms: "
            "notices(child), shares(child), rests(child)"
        )
        return

    base_seed = (
        args.seed if args.seed is not None else random.randrange(2**31)
    )
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(
                name="Mina",
                caregiver_name="Mama",
                room="the moonlit bedroom",
                seed=101,
            ),
            StoryParams(
                name="Theo",
                caregiver_name="Grandpa",
                room="the blue bedroom",
                seed=102,
            ),
            StoryParams(
                name="Lulu",
                caregiver_name="Papa",
                room="the little attic room",
                seed=103,
            ),
            StoryParams(
                name="Nora",
                caregiver_name="Grandma",
                room="the warm room under the eaves",
                seed=104,
            ),
            StoryParams(
                name="Sam",
                caregiver_name="Aunt Rose",
                room="the room beside the quiet garden",
                seed=105,
            ),
        ]
        samples = [generate(params) for params in curated]
    else:
        seen: set[str] = set()
        index = 0
        limit = max(50, args.n * 20)
        while len(samples) < args.n and index < limit:
            params = resolve_params(args, random.Random(base_seed + index))
            params.seed = base_seed + index
            sample = generate(params)
            index += 1
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if not samples:
        raise StoryError("No stories could be generated.")

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(
                json.dumps(
                    [sample.to_dict() for sample in samples],
                    indent=2,
                    ensure_ascii=False,
                )
            )
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
