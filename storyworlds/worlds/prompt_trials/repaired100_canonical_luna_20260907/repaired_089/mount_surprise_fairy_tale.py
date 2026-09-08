#!/usr/bin/env python3
"""
Storyworld: mount_surprise_fairy_tale

A tiny fairy-tale world about a gentle mount, a hidden surprise, and a
kindness that changes what a traveler expects.
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
class Creature:
    id: str
    name: str
    kind: str
    role: str
    home: str
    meters: dict[str, float] = field(
        default_factory=lambda: {"height": 0.0, "distance": 0.0, "trust": 0.0}
    )
    memes: dict[str, float] = field(
        default_factory=lambda: {"surprise": 0.0, "worry": 0.0, "joy": 0.0}
    )


@dataclass
class Thing:
    id: str
    label: str
    kind: str
    owner: str = ""
    meters: dict[str, float] = field(
        default_factory=lambda: {"weight": 0.0, "brightness": 0.0, "safety": 0.0}
    )


@dataclass
class StoryParams:
    hero_name: str
    mount_name: str
    guide_name: str
    kingdom: str
    mount_kind: str
    treasure: str
    surprise: str
    path: str
    telling_mode: str = "dawn"
    seed: Optional[int] = None


MOUNTS = {
    "moon pony": {
        "names": ["Comet", "Silver", "Dewdrop", "Star"],
        "homes": ["Cloud Meadow", "the quiet hill stable"],
        "colors": ["silver", "blue-gray", "white"],
    },
    "forest stag": {
        "names": ["Hazel", "Briar", "Clover", "Moss"],
        "homes": ["the whispering forest", "the greenwood clearing"],
        "colors": ["russet", "golden-brown", "deep chestnut"],
    },
    "sun camel": {
        "names": ["Saffron", "Amber", "Dune", "Sol"],
        "homes": ["the singing desert", "the palace garden"],
        "colors": ["honey-gold", "copper", "warm sand"],
    },
    "river dragon": {
        "names": ["Ripple", "Pearl", "Rain", "Brook"],
        "homes": ["the blue river cave", "the reed-fringed marsh"],
        "colors": ["green", "misty blue", "jade"],
    },
}

HERO_NAMES = ["Luna", "Mira", "Tessa", "Nell", "Pia", "Elio"]
GUIDE_NAMES = ["Mara", "Bram", "Iris", "Oren", "Faye", "Rowan"]

KINGDOMS = [
    "the kingdom of Bellflower",
    "the kingdom of Brightwater",
    "the kingdom of Rosegate",
    "the kingdom of Lanterns",
    "the kingdom of Little Dawn",
]

TREASURES = [
    "a small golden crown",
    "a silver seed",
    "a blue glass key",
    "a pearl bell",
    "a ruby apple",
    "a folded star map",
]

SURPRISES = [
    {
        "name": "a hidden garden",
        "clue": "a warm green scent drifted from behind the mountain stones",
        "reveal": "a secret garden blooming inside the hollow mount",
        "result": "the flowers opened into a safe resting place for every tired traveler",
        "lesson": "a steep journey may hide a gentle welcome",
        "ending": "That night, lantern flowers shone beneath the mount while the grateful villagers shared warm bread.",
    },
    {
        "name": "a sleeping bell",
        "clue": "a faint silver ringing answered whenever the mount placed one careful hoof",
        "reveal": "an old bell resting in a crystal chamber beneath the mount",
        "result": "the bell rang clearly and guided lost travelers home through the mist",
        "lesson": "quiet clues deserve patient listening",
        "ending": "From then on, the bell beneath the mount chimed whenever a traveler found the safe road.",
    },
    {
        "name": "a family of stars",
        "clue": "tiny lights flickered in the mount's shadow, although the sky was still bright",
        "reveal": "a nest of fallen stars tucked safely under the mount's broad saddle ridge",
        "result": "the stars rose one by one and returned a soft glow to the evening sky",
        "lesson": "a small mystery can belong to a much larger story",
        "ending": "At sunset, the returned stars winked above the mount, and Luna waved to each one.",
    },
    {
        "name": "a hidden bridge",
        "clue": "the mount's hoofprints filled with shining water instead of ordinary rain",
        "reveal": "a clear underground stream flowing beneath the mountain path",
        "result": "the stream lifted a stone bridge into place across the dangerous ravine",
        "lesson": "careful steps can reveal help that haste would miss",
        "ending": "The new bridge glittered below the mount, and no traveler had to fear the ravine again.",
    },
    {
        "name": "a tiny queen",
        "clue": "a bright red door appeared where plain rock had stood before",
        "reveal": "a tiny queen and her people living in a warm chamber inside the mount",
        "result": "the little kingdom offered its brightest lantern to guide Luna toward the castle",
        "lesson": "important friends may live in places no one thinks to search",
        "ending": "The tiny queen's lantern glowed beside the castle gate, brighter than any torch.",
    },
]

PATHS = [
    "the winding road above the valley",
    "the misty pass behind the castle",
    "the moonlit trail over the hills",
    "the narrow road beside the ravine",
    "the old path through the cloud grass",
]

TELLING_MODES = (
    "dawn",
    "question",
    "prophecy",
    "storm",
    "market",
    "quiet",
    "celebration",
    "moonlight",
)

REFLECTIONS = (
    '{hero} touched the mount\'s mane and whispered, "We will not hurry past a mystery."',
    '"Perhaps the surprise is waiting for someone who notices," {hero} said, and {guide} nodded.',
    '{guide} asked, "What does the clue tell us?" {hero} looked again before answering.',
    '{hero} drew a little map in the dust so that neither traveler would forget the strange sign.',
    'Instead of guessing, {hero} counted three breaths and listened to the mount beneath them.',
    '"A surprise is not always a prize," {hero} said. "Sometimes it is a chance to help."',
)

CLOSINGS = (
    '"You trusted the journey," said {guide}, "and the journey trusted you back."',
    '"I expected treasure," {hero} replied, "but kindness was the brightest treasure of all."',
    '{mount} bowed its head, and {hero} promised never to laugh at a small clue again.',
    'The travelers marked the safe path with blue ribbons so others could find the hidden wonder.',
    'From that day onward, children climbed the mount gently, hoping to discover something kind.',
)


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.creatures: dict[str, Creature] = {}
        self.things: dict[str, Thing] = {}
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
    if params.mount_kind not in MOUNTS:
        raise StoryError(f"Unknown mount kind: {params.mount_kind}")
    if params.surprise not in {item["name"] for item in SURPRISES}:
        raise StoryError(f"Unknown surprise: {params.surprise}")

    surprise = next(item for item in SURPRISES if item["name"] == params.surprise)
    world = World(params)

    hero = Creature("hero", params.hero_name, "child traveler", "seeker", params.kingdom)
    mount = Creature("mount", params.mount_name, params.mount_kind, "faithful mount", params.path)
    guide = Creature("guide", params.guide_name, "wise guide", "helper", params.kingdom)

    saddle = Thing("saddle", "a red traveling saddle", "gear", owner=hero.name)
    treasure = Thing("treasure", params.treasure, "expected treasure")
    marker = Thing("marker", "a blue ribbon", "safe-path marker")

    mount.meters["height"] = 1.4
    mount.meters["distance"] = 8.0
    mount.meters["trust"] = 1.0
    saddle.meters["safety"] = 1.0
    treasure.meters["brightness"] = 0.8
    marker.meters["safety"] = 1.0

    world.creatures.update({hero.id: hero, mount.id: mount, guide.id: guide})
    world.things.update({saddle.id: saddle, treasure.id: treasure, marker.id: marker})

    openings = {
        "dawn": f"At dawn in {params.kingdom}, {hero.name} climbed onto {params.mount_name}, a gentle {params.mount_kind}, to travel along {params.path}.",
        "question": f'"Will the mount carry us over the pass?" {params.hero_name} asked as the road rose above {params.kingdom}.',
        "prophecy": f"An old prophecy said that a faithful mount would lead a child toward wonder. That morning, {params.hero_name} set out from {params.kingdom}.",
        "storm": f"After a silver storm crossed {params.kingdom}, {params.hero_name} and {params.mount_name} began carefully along {params.path}.",
        "market": f"At the busy market of {params.kingdom}, {params.hero_name} heard a rumor about a wonder hidden beyond {params.path}.",
        "quiet": f"The bells of {params.kingdom} had just gone quiet when {params.hero_name} and {params.mount_name} started up {params.path}.",
        "celebration": f"On the morning of the kingdom's great celebration, {params.hero_name} chose the oldest road, {params.path}, and mounted {params.mount_name}.",
        "moonlight": f"Under a pale moon, {params.hero_name} rode {params.mount_name} away from {params.kingdom} and toward the high road.",
    }

    world.say(openings[params.telling_mode])
    world.say(f"{params.mount_name} carried {params.hero_name} steadily, but the road climbed toward a dark mount of stone where ordinary maps ended.")
    world.say(f"{params.hero_name} hoped to find {params.treasure}.")
    world.para()

    hero.memes["worry"] += 0.4
    mount.memes["worry"] += 0.2
    world.say(f"At the mount's foot, {params.mount_name} stopped. Its ears pointed toward the rocks, and {params.hero_name} saw that {surprise['clue']}.")
    world.say(f'"Why have you stopped?" {params.hero_name} asked. "{params.mount_name}, is there something beyond those stones?"')
    world.say(f'"The mount hears what hurried travelers miss," said {params.guide_name}, who had followed them up the path. "Step down, listen, and do not force the way."')
    world.say(random.Random((params.seed or 0) ^ 0x51A7).choice(REFLECTIONS).format(hero=params.hero_name, guide=params.guide_name))
    world.para()

    mount.memes["surprise"] += 1.0
    hero.memes["surprise"] += 1.0
    hero.meters["trust"] += 1.0
    world.say(f"{params.hero_name} slipped from the saddle and placed one hand on the warm stone. A hidden door opened, revealing {surprise['reveal']}.")
    world.say(f'"That is not the treasure I expected," said {params.hero_name}.')
    world.say(f'"It is a surprise, not a promise," answered {params.guide_name}. "Now we must decide what kindness it needs."')
    world.say(f"{params.mount_name} lowered its head. {params.hero_name} understood and chose to help rather than grab the first shining thing.")
    world.para()

    hero.meters["trust"] += 1.0
    mount.meters["trust"] += 1.0
    marker.meters["safety"] += 1.0
    world.say(f"Together, they {surprise['result']}. The expected {params.treasure} remained untouched until the hidden wonder was safe.")
    world.say(f"Then {params.mount_name} carried {params.hero_name} back along {params.path}, while {params.guide_name} tied {marker.label} beside the safe turn.")
    world.say(f"{params.hero_name} learned that {surprise['lesson']}. The surprise had changed the journey because it changed what the traveler chose to do.")
    world.say(random.Random((params.seed or 0) ^ 0xA11CE).choice(CLOSINGS).format(hero=params.hero_name, guide=params.guide_name, mount=params.mount_name))
    world.say(surprise["ending"])

    world.facts.update(
        hero=hero,
        mount=mount,
        guide=guide,
        saddle=saddle,
        treasure=treasure,
        marker=marker,
        surprise=surprise,
        path=params.path,
        kingdom=params.kingdom,
        expected_treasure=params.treasure,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Creature = f["hero"]
    mount: Creature = f["mount"]
    surprise: dict[str, str] = f["surprise"]
    return [
        f"Write a fairy tale about {hero.name} traveling on {mount.name}, a faithful mount, toward a surprise at a mysterious mount.",
        f"Tell a child-friendly story in which {hero.name} expects treasure but discovers {surprise['name']} and chooses kindness.",
        f"Write a fairy tale where a mount notices a clue, a guide gives advice, and a hidden wonder changes the hero's decision.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Creature = f["hero"]
    mount: Creature = f["mount"]
    guide: Creature = f["guide"]
    surprise: dict[str, str] = f["surprise"]
    return [
        QAItem(
            question=f"What was {hero.name} hoping to find?",
            answer=f"{hero.name} was hoping to find {f['expected_treasure']}, but the journey brought a more meaningful surprise.",
        ),
        QAItem(
            question=f"Why did {mount.name} stop at the mount?",
            answer=f"{mount.name} stopped because {surprise['clue']}. The mount noticed a clue that hurried travelers might have missed.",
        ),
        QAItem(
            question=f"What did {hero.name} discover?",
            answer=f"{hero.name} discovered {surprise['reveal']}. It was a surprise hidden inside the stone mount.",
        ),
        QAItem(
            question=f"How did {hero.name} and {guide.name} respond to the surprise?",
            answer=f"They listened carefully and {surprise['result']}. They helped before reaching for the expected treasure.",
        ),
        QAItem(
            question="What lesson did the fairy tale teach?",
            answer=f"The tale taught that {surprise['lesson']}. The ending showed this through a safe path and a wonder cared for instead of seized.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mount?",
            answer="A mount is an animal or creature that carries a rider, such as a pony, stag, camel, or magical dragon.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that is discovered or happens suddenly.",
        ),
        QAItem(
            question="What makes a fairy tale?",
            answer="A fairy tale is a magical story with wonder, unusual creatures or events, and a meaningful choice or lesson.",
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
    lines = ["--- trace ---"]
    for creature in world.creatures.values():
        lines.append(
            f"{creature.id}: kind={creature.kind} "
            f"meters={dict(creature.meters)} memes={dict(creature.memes)}"
        )
    for thing in world.things.values():
        lines.append(
            f"{thing.id}: label={thing.label} kind={thing.kind} "
            f"meters={dict(thing.meters)}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
% The fairy-tale gate requires a mount, an unexpected discovery, and a kind choice.
fairy_tale(S) :- story(S), has_mount(S), has_surprise(S), chooses_kindness(S).
has_mount(S) :- story(S), mount_present(S).
has_surprise(S) :- story(S), surprise_revealed(S).
chooses_kindness(S) :- story(S), helps_hidden_wonder(S).
"""


def asp_facts(params: StoryParams) -> str:
    import asp

    return "\n".join(
        [
            asp.fact("story", "s1"),
            asp.fact("mount_present", "s1"),
            asp.fact("surprise_revealed", "s1"),
            asp.fact("helps_hidden_wonder", "s1"),
        ]
    )


def asp_program() -> str:
    params = StoryParams(
        hero_name="Luna",
        mount_name="Comet",
        guide_name="Mara",
        kingdom="the kingdom of Bellflower",
        mount_kind="moon pony",
        treasure="a small golden crown",
        surprise="a hidden garden",
        path="the winding road above the valley",
    )
    return f"{asp_facts(params)}\n{ASP_RULES}\n#show fairy_tale/1.\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    found = set(asp.atoms(model, "fairy_tale"))
    if found != {("s1",)}:
        print("MISMATCH: ASP did not recognize the fairy-tale pattern.")
        return 1

    sample = generate(
        StoryParams(
            hero_name="Luna",
            mount_name="Comet",
            guide_name="Mara",
            kingdom="the kingdom of Bellflower",
            mount_kind="moon pony",
            treasure="a small golden crown",
            surprise="a hidden garden",
            path="the winding road above the valley",
            seed=17,
        )
    )
    required = ("surprise", "mount", "garden")
    if not all(word in sample.story.lower() for word in required):
        print("MISMATCH: generated story does not exercise the verified domain.")
        return 1
    print("OK: ASP gate matches the Python fairy-tale world.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fairy-tale world about a mount, a surprise, and a kind choice."
    )
    parser.add_argument("--hero-name")
    parser.add_argument("--mount-name")
    parser.add_argument("--guide-name")
    parser.add_argument("--kingdom")
    parser.add_argument("--mount-kind", choices=sorted(MOUNTS))
    parser.add_argument("--treasure")
    parser.add_argument("--surprise", choices=sorted(item["name"] for item in SURPRISES))
    parser.add_argument("--path")
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
    mount_kind = args.mount_kind or rng.choice(sorted(MOUNTS))
    mount_data = MOUNTS[mount_kind]
    surprise = args.surprise or rng.choice(sorted(item["name"] for item in SURPRISES))
    return StoryParams(
        hero_name=args.hero_name or rng.choice(HERO_NAMES),
        mount_name=args.mount_name or rng.choice(mount_data["names"]),
        guide_name=args.guide_name or rng.choice(GUIDE_NAMES),
        kingdom=args.kingdom or rng.choice(KINGDOMS),
        mount_kind=mount_kind,
        treasure=args.treasure or rng.choice(TREASURES),
        surprise=surprise,
        path=args.path or rng.choice(PATHS),
        telling_mode=rng.choice(TELLING_MODES),
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
    StoryParams(
        hero_name="Luna",
        mount_name="Comet",
        guide_name="Mara",
        kingdom="the kingdom of Bellflower",
        mount_kind="moon pony",
        treasure="a small golden crown",
        surprise="a hidden garden",
        path="the winding road above the valley",
        telling_mode="dawn",
    ),
    StoryParams(
        hero_name="Mira",
        mount_name="Hazel",
        guide_name="Bram",
        kingdom="the kingdom of Brightwater",
        mount_kind="forest stag",
        treasure="a silver seed",
        surprise="a sleeping bell",
        path="the old path through the cloud grass",
        telling_mode="quiet",
    ),
    StoryParams(
        hero_name="Tessa",
        mount_name="Ripple",
        guide_name="Iris",
        kingdom="the kingdom of Rosegate",
        mount_kind="river dragon",
        treasure="a blue glass key",
        surprise="a hidden bridge",
        path="the narrow road beside the ravine",
        telling_mode="storm",
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
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
