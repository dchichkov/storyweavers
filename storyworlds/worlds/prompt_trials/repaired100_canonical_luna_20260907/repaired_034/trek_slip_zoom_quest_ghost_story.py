#!/usr/bin/env python3
"""
A small ghost-story world about a moonlit trek, a slippery bridge, and a brave zoom.

The story follows Luna and her friend Pip as they investigate a bell that rings in
an empty watchtower. A dangerous slip reveals that the ghost is not hunting them:
it is trying to guide them toward a lost child and a warm way home.
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

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
sys.path.insert(0, os.path.dirname(_storyworlds_dir))

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    hero: str = "Luna"
    companion: str = "Pip"
    place: str = "the misty hill"
    object_name: str = "the silver lantern"
    arc: int = 0
    seed: Optional[int] = None


@dataclass
class Entity:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    params: StoryParams
    hero: Entity
    companion: Entity
    ghost: Entity
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


HERO_NAMES = ["Luna", "Mara", "Nell", "Ivy", "Tess", "Wren"]
COMPANION_NAMES = ["Pip", "Ollie", "Bram", "Cleo", "Finn", "Mina"]
PLACES = [
    "the misty hill",
    "the old pine path",
    "the moonlit marsh",
    "the quiet orchard",
]
OBJECTS = [
    "the silver lantern",
    "the blue handbell",
    "the brass key",
    "the star-shaped locket",
]

ARCS = [
    {
        "premise": "The watchtower bell rang though its keeper had vanished many winters ago",
        "problem": "a pale light darted across the ravine and disappeared beyond a broken footbridge",
        "stake": "If the light went out, someone lost in the dark might never find the village path",
        "temptation": "zoom across the bridge before the ghost could reach it",
        "clue": "the bell rang three slow times whenever someone called for help",
        "action": "They tied a rope around an oak tree, tested each plank, and crossed one careful step at a time",
        "twist": "the ghost was the old keeper, and the pale light was his lantern pointing toward a child beneath the bridge",
        "resolution": "They lowered a basket, lifted the child safely, and carried the lantern back to the village",
        "lesson": "a frightening mystery can become a rescue when brave friends pause to listen",
        "ending": "the watchtower bell gave one gentle ring, and its light settled warmly in the village window",
        "question": "Why did the bell ring three times?",
        "answer": "It rang three times whenever someone nearby called for help.",
    },
    {
        "premise": "A ghostly whistle floated over the marsh at the end of every moonlit trek",
        "problem": "the sound led toward a slippery path where the stepping stones were hidden by fog",
        "stake": "Anyone rushing forward could slip into the cold, deep water",
        "temptation": "run after the whistle and zoom over the stones before it faded",
        "clue": "the whistle changed into a soft hum whenever Luna held up her lantern",
        "action": "They marked each stone with a twig, crawled low, and passed the lantern from hand to hand",
        "twist": "the ghost was humming to calm a frightened foal trapped on the far bank",
        "resolution": "They guided the foal across the marked stones and led it home beneath the lantern glow",
        "lesson": "slow steps and gentle listening can reveal the heart inside a haunting",
        "ending": "the foal nuzzled Luna's coat while the ghostly hum faded into the reeds",
        "question": "What did the ghostly whistle become when Luna raised the lantern?",
        "answer": "The whistle became a soft hum when Luna raised her lantern.",
    },
    {
        "premise": "Luna and Pip began a trek to find a missing music box in the ruined schoolhouse",
        "problem": "a floorboard gave a sudden slip beneath Pip's boot",
        "stake": "The music box and the friends might tumble into the dark room below",
        "temptation": "zoom ahead alone and grab the box before the creaking ghost caught up",
        "clue": "a tiny tune played whenever the loose board bent",
        "action": "They backed away, wedged the board with a ruler, and reached through the safe doorway together",
        "twist": "the ghost had hidden the music box to keep its lullaby playing for lonely children",
        "resolution": "They repaired the box and left it by the schoolhouse window for anyone who needed comfort",
        "lesson": "a strange warning may be asking for care rather than fear",
        "ending": "each night the music box played one bright note, and no child felt quite so alone",
        "question": "Why had the ghost hidden the music box?",
        "answer": "The ghost had hidden it so its lullaby could comfort lonely children.",
    },
    {
        "premise": "A silver footprint appeared each morning beside the garden gate",
        "problem": "the footprints made a twisting trek toward a hill covered in slick leaves",
        "stake": "The trail could vanish before Luna learned who needed help",
        "temptation": "zoom up the hill and ignore the wet leaves under her shoes",
        "clue": "every footprint pointed toward an empty birdhouse",
        "action": "They slowed their pace, swept away the leaves, and followed the trail with a lantern between them",
        "twist": "the ghost belonged to a gardener who was searching for a lost bluebird",
        "resolution": "They found the bird tangled in thread and freed it beside the empty birdhouse",
        "lesson": "careful attention can turn a spooky trail into a path to kindness",
        "ending": "the bluebird filled the garden with song, and the last silver footprint faded in the morning sun",
        "question": "What was the gardener ghost searching for?",
        "answer": "The gardener ghost was searching for a lost bluebird.",
    },
    {
        "premise": "The old lighthouse flashed once whenever Luna and Pip came near",
        "problem": "the cliff trail was wet, and Pip began to slip beside the black rocks",
        "stake": "A fall could send him toward the churning sea",
        "temptation": "zoom forward to catch the flashing light without checking the trail",
        "clue": "the lighthouse flashed again whenever Luna called Pip's name",
        "action": "They crouched low, joined hands, and moved toward the light only after each foothold was firm",
        "twist": "the ghost was a lighthouse keeper showing them a dry stairway cut into the cliff",
        "resolution": "They followed the stairway to a stranded sailor and guided him home",
        "lesson": "a true guide does not make you hurry; a true guide helps you stand",
        "ending": "the lighthouse shone steadily while the rescued sailor waved from the warm harbor",
        "question": "What did the lighthouse keeper's ghost show them?",
        "answer": "The ghost showed them a dry stairway cut into the cliff.",
    },
]

OPENINGS = [
    "The moon hung like a pale button above the hills",
    "Mist curled around the grass as evening folded over the path",
    "The first stars blinked when Luna opened the creaking gate",
    "A cold breeze moved through the trees without moving a single leaf",
    "The village windows glowed behind them as the dark trail climbed",
]

DIALOGUE_PAIRS = [
    ("Pip whispered, 'Did you hear that bell?'", "Luna answered, 'Yes, and it sounded like someone asking us to wait.'"),
    ("Luna asked, 'Should we hurry before the light vanishes?'", "Pip replied, 'No. If the ground is slippery, our first job is to stay together.'"),
    ("Pip said, 'That shadow looks like a ghost.'", "Luna answered, 'Then let us ask what it wants before we decide what it means.'"),
    ("Luna called, 'If you are guiding us, ring once.'", "Pip said, 'It rang. Let us follow the clue, not our fear.'"),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A child-friendly ghost storyworld about a trek, a slip, and a zooming quest."
    )
    parser.add_argument("--hero", choices=HERO_NAMES)
    parser.add_argument("--companion", choices=COMPANION_NAMES)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--object-name", choices=OBJECTS)
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
    hero = args.hero or rng.choice(HERO_NAMES)
    companions = [name for name in COMPANION_NAMES if name != hero]
    companion = args.companion or rng.choice(companions)
    place = args.place or rng.choice(PLACES)
    object_name = args.object_name or rng.choice(OBJECTS)
    if hero == companion:
        raise StoryError("The hero and companion must be different characters.")
    return StoryParams(
        hero=hero,
        companion=companion,
        place=place,
        object_name=object_name,
        arc=rng.randrange(len(ARCS)),
        seed=args.seed,
    )


def build_world(params: StoryParams) -> World:
    return World(
        params=params,
        hero=Entity(params.hero, "hero"),
        companion=Entity(params.companion, "companion"),
        ghost=Entity("the ghost", "ghost"),
    )


def simulate(world: World) -> None:
    params = world.params
    arc = ARCS[params.arc]
    rng = random.Random(params.seed)

    hero = world.hero
    companion = world.companion
    ghost = world.ghost

    hero.memes["curiosity"] = 1.0
    hero.memes["fear"] = 0.4
    companion.memes["caution"] = 1.0
    ghost.memes["helpfulness"] = 1.0

    world.facts.update(
        {
            "place": params.place,
            "object": params.object_name,
            "problem": arc["problem"],
            "clue": arc["clue"],
            "stake": arc["stake"],
            "resolved": False,
        }
    )

    opening = rng.choice(OPENINGS)
    world.say(
        f"{opening}. {hero.name} and {companion.name} began a quiet trek through "
        f"{params.place}, carrying {params.object_name} between them."
    )
    world.say(f"{arc['premise']}. Nobody in the village liked to speak of the ghost after sunset.")
    world.para()

    world.say(f"Then {arc['problem']}. {arc['stake']}.")
    world.say(f"For one quick moment, {hero.name} wanted to {arc['temptation']}.")
    first, second = rng.choice(DIALOGUE_PAIRS)
    world.say(f"{first} {second}")
    world.say(
        f"The friends remembered that a sudden zoom could become a dangerous slip, "
        f"so they chose a careful plan."
    )
    hero.memes["fear"] = 0.7
    hero.memes["patience"] = 1.0
    world.facts["temptation"] = arc["temptation"]

    world.para()
    world.say(f"They paused beside the path. {arc['clue']}.")
    world.say(f"{arc['action']}.")
    world.say(
        f"The pale shape appeared again, but it did not rush at them. "
        f"It lifted one transparent hand toward the hidden danger."
    )
    world.say(f"Then came the twist: {arc['twist']}.")
    hero.memes["understanding"] = 1.0
    ghost.memes["trust"] = 1.0
    world.facts["twist"] = arc["twist"]
    world.facts["solution"] = arc["resolution"]

    world.para()
    world.say(f"{arc['resolution']}.")
    world.say(
        f"{hero.name} looked at {companion.name} and said, "
        f"'The ghost was scary only because we did not know its kind purpose.'"
    )
    world.say(
        f"{companion.name} smiled. 'And our slow trek helped us notice what a fast zoom would have missed.'"
    )
    world.say(f"{arc['ending']}.")
    world.say(f"They left {params.object_name} shining beside the doorway as a sign of welcome.")
    world.facts["resolved"] = True
    world.facts["ending_image"] = arc["ending"]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    simulate(world)
    arc = ARCS[params.arc]

    prompts = [
        f"Write a child-friendly ghost story about {params.hero}'s trek through {params.place}.",
        f"Tell a Quest where a slip and a tempting zoom teach {params.hero} and {params.companion} to listen.",
        f"Create a gentle ghost mystery involving {params.object_name} and a surprising rescue.",
    ]

    story_qa = [
        QAItem(
            question=f"What risky action did {params.hero} first consider?",
            answer=f"{params.hero} first considered trying to {arc['temptation']}.",
        ),
        QAItem(
            question=f"What clue helped {params.hero} and {params.companion}?",
            answer=f"The clue was that {arc['clue']}.",
        ),
        QAItem(
            question="What was the surprising truth about the ghost?",
            answer=f"The surprising truth was that {arc['twist']}.",
        ),
        QAItem(
            question=f"How did {params.hero} and {params.companion} solve the problem?",
            answer=f"They solved it when {arc['resolution'].lower()}",
        ),
        QAItem(
            question="What lesson did the friends learn?",
            answer=f"They learned that {arc['lesson']}.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a ghost story?",
            answer="A ghost story is a tale about a mysterious spirit or haunting, often with a surprising or comforting explanation.",
        ),
        QAItem(
            question="What does it mean to trek?",
            answer="To trek means to take a long or careful journey on foot.",
        ),
        QAItem(
            question="Why can a slip be dangerous?",
            answer="A slip can be dangerous because a person may lose balance and fall, especially near water or a steep edge.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey taken to find something, solve a problem, or help someone.",
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in [world.hero, world.companion, world.ghost]:
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        lines.append(
            f"  {entity.name:14} ({entity.kind:10}) meters={meters} memes={memes}"
        )
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
#show valid/1.
#show quest/1.
#show safe_resolution/1.

valid(story) :- domain(ghost_quest), feature(trek), feature(slip), feature(zoom), feature(quest).
quest(story) :- valid(story), feature(quest).
safe_resolution(story) :- valid(story), outcome(rescue).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    facts = [
        asp.fact("domain", "ghost_quest"),
        asp.fact("feature", "trek"),
        asp.fact("feature", "slip"),
        asp.fact("feature", "zoom"),
        asp.fact("feature", "quest"),
        asp.fact("outcome", "rescue"),
    ]
    return "\n".join(facts)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show valid/1. #show quest/1. #show safe_resolution/1."))
    expected = {
        ("valid", ("story",)),
        ("quest", ("story",)),
        ("safe_resolution", ("story",)),
    }
    actual = {
        (name, args)
        for name in ("valid", "quest", "safe_resolution")
        for args in asp.atoms(model, name)
    }
    if actual != expected:
        print(f"MISMATCH: ASP facts were {sorted(actual)}")
        return 1

    for index, params in enumerate(CURATED):
        sample = generate(params)
        if not sample.story.strip() or not sample.world.facts.get("resolved"):
            print(f"MISMATCH: generated story {index + 1} did not resolve.")
            return 1
        if "zoom" not in sample.story or "slip" not in sample.story or "trek" not in sample.story:
            print(f"MISMATCH: generated story {index + 1} lost a required seed word.")
            return 1

    print("OK: ASP twin is consistent and generated stories resolve.")
    return 0


CURATED = [
    StoryParams(
        hero="Luna",
        companion="Pip",
        place="the misty hill",
        object_name="the silver lantern",
        arc=0,
        seed=101,
    ),
    StoryParams(
        hero="Mara",
        companion="Ollie",
        place="the old pine path",
        object_name="the blue handbell",
        arc=1,
        seed=202,
    ),
    StoryParams(
        hero="Ivy",
        companion="Finn",
        place="the quiet orchard",
        object_name="the star-shaped locket",
        arc=3,
        seed=303,
    ),
]


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
        print(asp_program("#show valid/1. #show quest/1. #show safe_resolution/1."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import storyworlds.asp as asp

        model = asp.one_model(
            asp_program("#show valid/1. #show quest/1. #show safe_resolution/1.")
        )
        print(asp.atoms(model, "valid"))
        print(asp.atoms(model, "quest"))
        print(asp.atoms(model, "safe_resolution"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        if args.n < 1:
            raise StoryError("-n must be at least 1.")
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(args.n * 30, 30):
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
        raise StoryError("Could not generate enough distinct stories.")

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
