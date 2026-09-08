#!/usr/bin/env python3
"""
A gentle ghost story about a smooth transformation foretold by small signs.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE
while ROOT != os.path.dirname(ROOT) and not os.path.exists(os.path.join(ROOT, "results.py")):
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.label:
            self.label = self.type


@dataclass
class Place:
    name: str = "the old house"
    threshold: float = 2.0


@dataclass
class StoryParams:
    place: str = "old house"
    hero: str = "Luna"
    companion: str = "Milo"
    ghost: str = "Ada"
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]

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


ARCS = [
    {
        "routine": "polished the dusty banister until it felt smooth beneath her palm",
        "omen": "three pale footprints appeared on the floor where nobody had walked",
        "clue": "the footprints stopped beside a locked blue door",
        "fear": "someone unseen was waiting inside",
        "cause": "the ghost of Ada had been following the old path to her childhood room",
        "action": "Luna unlocked the door and placed a warm lamp beside the empty bed",
        "message": "I have been looking for the way home",
        "change": "the cold hallway became a smooth, shining passage",
        "ending": "a single pale footprint faded beside the warm lamp",
    },
    {
        "routine": "ran a cloth over the round table until its wood grew smooth and bright",
        "omen": "a silver teacup moved one inch whenever the clock chimed",
        "clue": "the cup always pointed toward the staircase",
        "fear": "the house wanted someone to climb into the dark",
        "cause": "Ada's spirit was guiding Luna toward the room where her old letters lay",
        "action": "carried the cup upstairs and opened the forgotten writing desk",
        "message": "Please let my words travel farther than I did",
        "change": "the staircase changed from a steep shadow into an easy, moonlit climb",
        "ending": "the silver cup rested quietly beside the opened letters",
    },
    {
        "routine": "smoothed a torn curtain while rain tapped softly against the windows",
        "omen": "a cool breath curled the curtain into the shape of a little wave",
        "clue": "the wave pointed toward a cracked mirror",
        "fear": "a face might appear behind Luna's own reflection",
        "cause": "Ada was trapped in the mirror's old memory of the house",
        "action": "covered the crack with a blue ribbon and spoke Ada's name aloud",
        "message": "I am not the shadow you saw",
        "change": "the broken reflection became a smooth pool of moonlight",
        "ending": "the ribbon fluttered once, then lay still around the mirror",
    },
    {
        "routine": "sandpapered a small wooden box until its lid slid smooth as a stone",
        "omen": "the box opened by itself when the hallway lamp blinked",
        "clue": "inside lay a key wrapped in a faded green thread",
        "fear": "the key might unlock something that should stay buried",
        "cause": "Ada had left a farewell token for the person brave enough to listen",
        "action": "used the key on the garden gate and carried the box beneath the old tree",
        "message": "The house can breathe when someone remembers",
        "change": "the dark garden transformed into a soft path of fireflies",
        "ending": "the empty box held only a little moonlight beneath the tree",
    },
]


def tell_story(params: StoryParams) -> World:
    if params.hero == params.companion:
        raise StoryError("The hero and companion must have different names.")
    if params.hero == params.ghost or params.companion == params.ghost:
        raise StoryError("The ghost must have a different name from the living characters.")

    world = World(Place())
    hero = world.add(Entity(params.hero, "character", "girl", params.hero))
    companion = world.add(Entity(params.companion, "character", "boy", params.companion))
    ghost = world.add(Entity(params.ghost, "spirit", "ghost", params.ghost))

    hero.memes["curiosity"] = 1.0
    companion.memes["courage"] = 1.0
    ghost.memes["longing"] = 2.0
    ghost.meters["visibility"] = 0.0

    arc = ARCS[(params.seed or 0) % len(ARCS)]
    world.facts.update(
        hero=hero,
        companion=companion,
        ghost=ghost,
        arc=arc,
        transformation=False,
        foreshadowing=True,
    )

    world.say(
        f"At dusk, {hero.id} and {companion.id} entered {world.place.name}. "
        f"{hero.id} {arc['routine']}, while {companion.id} held a lantern close."
    )
    world.say(
        f"The house was quiet, but it did not feel empty. {arc['omen'].capitalize()}. "
        f"It was the first warning that the night would not remain ordinary."
    )
    world.para()

    world.say(
        f"{hero.id} followed the sign and found that {arc['clue']}. "
        f"{companion.id} swallowed. They wondered whether {arc['fear']}."
    )
    world.say(
        f'"Did you leave these signs for us?" {hero.id} asked. '
        f'"I did not," {companion.id} said, "but I think someone wants us to keep looking."'
    )
    hero.memes["fear"] = 1.0
    companion.memes["fear"] = 1.0

    world.say(
        f"A pale figure appeared at the end of the hall. It was {ghost.id}, almost transparent, "
        f"and {ghost.id} whispered, \"{arc['message']}.\""
    )
    ghost.meters["visibility"] = 1.0
    ghost.memes["longing"] = 1.0
    world.say(
        f"Then they understood: {arc['cause']}. The frightening clues had been a foreshadowing, "
        f"not a threat."
    )
    world.say(
        f"Together, they {arc['action']}. {hero.id} said, \"You can stop wandering now.\" "
        f"{companion.id} answered, \"We will help you find the last step.\""
    )
    world.para()

    world.facts["transformation"] = True
    hero.memes["fear"] = 0.0
    companion.memes["fear"] = 0.0
    hero.memes["trust"] = 1.0
    companion.memes["trust"] = 1.0
    ghost.memes["peace"] = 2.0
    ghost.meters["visibility"] = 0.0

    world.say(
        f"The moment the promise was made, {arc['change']}. "
        f"The ghost grew lighter until only a gentle glow remained."
    )
    world.say(
        f"At dawn, {arc['ending']}. {hero.id} and {companion.id} left the house together, "
        f"knowing that a haunting can transform when someone answers it with kindness."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    arc = f["arc"]
    return [
        "Write a gentle ghost story in which smooth changes reveal a hidden goodbye.",
        f"Tell a story about {f['hero'].id} following this foreshadowing: {arc['omen']}.",
        f"Write a child-friendly haunting where {f['ghost'].id} transforms from a wandering ghost into a peaceful memory.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    arc = f["arc"]
    hero: Entity = f["hero"]
    companion: Entity = f["companion"]
    ghost: Entity = f["ghost"]
    return [
        QAItem(
            question=f"What were {hero.id} and {companion.id} doing when the first strange sign appeared?",
            answer=f"{hero.id} was {arc['routine']}, while {companion.id} held a lantern nearby.",
        ),
        QAItem(
            question="What foreshadowing warned them that the house was not ordinary?",
            answer=f"The warning was that {arc['omen']}.",
        ),
        QAItem(
            question=f"What did {ghost.id} want?",
            answer=f"{ghost.id} wanted to say, \"{arc['message']}\".",
        ),
        QAItem(
            question="How did the living characters help the ghost?",
            answer=f"They {arc['action']}.",
        ),
        QAItem(
            question="What transformation happened at the end?",
            answer=f"{arc['change']}. The ghost became peaceful and faded away.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a ghost story?",
            answer="A ghost story is a tale about a spirit or strange presence, often with a mystery to solve.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a small clue that hints at something important later in a story.",
        ),
        QAItem(
            question="What does transformation mean?",
            answer="Transformation means changing from one form, condition, or feeling into another.",
        ),
        QAItem(
            question="What does smooth mean?",
            answer="Smooth means even and gentle, without rough bumps or sudden difficulty.",
        ),
    ]


ASP_RULES = r"""
tension :- omen.
haunting :- tension.
message_revealed :- haunting, listener_kind.
transformation :- message_revealed, helping.
peaceful :- transformation.
#show peaceful/0.
#show transformation/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("omen"),
            asp.fact("listener_kind"),
            asp.fact("helping"),
        ]
    )


def asp_program(show: str = "#show peaceful/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_outcome() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show peaceful/0.\n#show transformation/0."))
    return sorted(set(asp.atoms(model, "peaceful") + asp.atoms(model, "transformation")))


def asp_verify() -> int:
    expected = [(), ()]
    actual = asp_outcome()
    if actual == expected:
        print("OK: ASP and Python agree that the ghost becomes peaceful through transformation.")
        for seed in range(8):
            sample = generate(StoryParams(seed=seed))
            if not sample.story or "ghost" not in sample.story.lower():
                print("FAIL: generated story check failed.")
                return 1
        return 0
    print(f"MISMATCH: expected={expected} actual={actual}")
    return 1


NAMES = ["Luna", "Ivy", "Nora", "Mara", "June", "Tess"]
COMPANIONS = ["Milo", "Theo", "Owen", "Finn", "Sam", "Eli"]
GHOSTS = ["Ada", "Rose", "Evelyn", "Clara", "Mae"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A gentle transformation ghost story.")
    parser.add_argument("--place", choices=["old house"], default=None)
    parser.add_argument("--hero", choices=NAMES, default=None)
    parser.add_argument("--companion", choices=COMPANIONS, default=None)
    parser.add_argument("--ghost", choices=GHOSTS, default=None)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(NAMES)
    companion_choices = [x for x in COMPANIONS if x != hero]
    companion = args.companion or rng.choice(companion_choices)
    ghost_choices = [x for x in GHOSTS if x not in {hero, companion}]
    ghost = args.ghost or rng.choice(ghost_choices)
    return StoryParams(
        place=args.place or "old house",
        hero=hero,
        companion=companion,
        ghost=ghost,
        seed=args.seed,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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
        lines.append(
            f"  {entity.id}: kind={entity.kind}, meters={entity.meters}, memes={entity.memes}"
        )
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show peaceful/0.\n#show transformation/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_outcome())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params = StoryParams(
            place="old house",
            hero="Luna",
            companion="Milo",
            ghost="Ada",
            seed=base_seed,
        )
        samples = [generate(params)]
    else:
        seen: set[str] = set()
        index = 0
        target = max(1, args.n)
        while len(samples) < target and index < max(target * 20, 20):
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
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
