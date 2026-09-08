#!/usr/bin/env python3
"""
A small rhyming storyworld set in an art room.

The domain centers on a bifocal lens, a foreshadowed mistake, reconciliation,
and a bad ending that teaches the children to slow down and repair harm.
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


SETTINGS = {
    "art_room": {
        "place": "the art room",
        "detail": "Paint cups lined the shelves, and bright paper made the art room glow.",
        "affords": {"painting", "repairing"},
    }
}

NAMES = ["Luna", "Milo", "Tess", "Arlo", "Pia", "Jonah"]
GENDERS = {
    "Luna": "girl",
    "Milo": "boy",
    "Tess": "girl",
    "Arlo": "boy",
    "Pia": "girl",
    "Jonah": "boy",
}
HELPERS = ["Ms. Vale", "Mr. Chen", "Aunt Bea"]
TRAITS = ["curious", "careful", "bold", "thoughtful", "playful"]

SCENES = [
    {
        "object": "a moon mural",
        "problem": "a blue paint tray tipped beside the drying paper",
        "foreshadow": "The bifocal glasses showed Luna both a tiny loose wheel and a broad blue puddle.",
        "mistake": "Luna watched the big puddle and missed the loose wheel, which rolled beneath the drying rack.",
        "plan": "The children moved the wet paper, found the wheel, and cleaned the floor before painting again.",
        "bad": "The first mural blurred into a blue streak, and its paper tore when they lifted it too soon.",
        "lesson": "a small warning can matter as much as a large mess",
        "ending": "The torn moon hung crookedly, a silver patch beside a blue stain.",
    },
    {
        "object": "a paper garden",
        "problem": "a glue bottle leaked near a basket of delicate leaves",
        "foreshadow": "Through the bifocal lens, Luna saw both the shining glue thread and the far-off basket.",
        "mistake": "She hurried toward the basket and left the glue bottle dripping behind her.",
        "plan": "The children capped the bottle, lifted the clean leaves, and asked the teacher how to mend the sticky paper.",
        "bad": "The glue dried in a hard wrinkle, and several paper leaves stuck together forever.",
        "lesson": "helping one trouble should not make another trouble worse",
        "ending": "The paper garden stood with one clumped corner, still green but no longer smooth.",
    },
    {
        "object": "a rainbow kite",
        "problem": "a red brush slid toward a cup filled with cloudy rinse water",
        "foreshadow": "The bifocal glasses made the near brush bristles and the far cup rim both clear.",
        "mistake": "Luna reached for the brush without noticing that her elbow nudged the cup.",
        "plan": "Her friends caught the cup, rinsed the brush, and told Luna why the warning had mattered.",
        "bad": "Gray water spilled across the kite, turning its rainbow into a dull, muddy smear.",
        "lesson": "seeing two distances is useful only when you pause before acting",
        "ending": "The kite still had a rainbow, but a brown cloud covered its brightest stripe.",
    },
    {
        "object": "a cardboard castle",
        "problem": "the tallest tower leaned against a shelf of glitter jars",
        "foreshadow": "The bifocal lens revealed a thin crack near the tower and a trembling jar far above it.",
        "mistake": "Luna pressed the tower straight before telling anyone about the crack.",
        "plan": "The children lowered the tower, emptied the shelf, and repaired the cardboard with a wide paper brace.",
        "bad": "The tower collapsed, and glitter burst over the floor like noisy golden snow.",
        "lesson": "a quick fix can fail when it ignores the first small sign",
        "ending": "The castle stood again, but glitter sparkled in its doorway like a warning.",
    },
]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    place: str
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


@dataclass
class StoryParams:
    place: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None
    scene: int = 0
    rhyme: int = 0
    beat: int = 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A rhyming art-room story about a bifocal lens, reconciliation, and a bad ending."
    )
    parser.add_argument("--place", choices=SETTINGS.keys())
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--gender", choices=["girl", "boy"])
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--trait", choices=TRAITS)
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
    name = args.name or rng.choice(NAMES)
    return StoryParams(
        place=args.place or "art_room",
        name=name,
        gender=args.gender or GENDERS[name],
        helper=args.helper or rng.choice(HELPERS),
        trait=args.trait or rng.choice(TRAITS),
        scene=rng.randrange(len(SCENES)),
        rhyme=rng.randrange(8),
        beat=rng.randrange(64),
    )


def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in SETTINGS:
        raise StoryError("The story must take place in the art room.")
    if params.gender not in {"girl", "boy"}:
        raise StoryError("The child must be a girl or a boy.")
    if params.name not in NAMES:
        raise StoryError("The child name is not in the story registry.")
    if params.helper not in HELPERS:
        raise StoryError("The helper is not in the story registry.")


def _build_world(params: StoryParams) -> World:
    reasonableness_gate(params)
    scene = SCENES[params.scene % len(SCENES)]
    world = World(place=SETTINGS[params.place]["place"])

    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
        meters={"attention": 0.7, "care": 0.8},
        memes={"pride": 0.5, "honesty": 0.8},
    ))
    friend = world.add(Entity(
        id="Friend",
        kind="character",
        type="child",
        label="Maya",
        meters={"helpfulness": 0.9},
        memes={"patience": 0.8},
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type="adult",
        label=params.helper,
        meters={"guidance": 1.0},
        memes={"fairness": 1.0},
    ))
    bifocal = world.add(Entity(
        id="Bifocal",
        kind="thing",
        type="bifocal",
        label="bifocal",
        phrase="a pair of bifocal glasses",
        owner=helper.id,
        meters={"near_focus": 1.0, "far_focus": 1.0},
        memes={"foreshadowing": 1.0},
    ))
    artwork = world.add(Entity(
        id="Artwork",
        kind="thing",
        type="artwork",
        label=scene["object"],
        phrase=scene["object"],
        meters={"beauty": 0.8, "damage": 0.0},
        memes={"hope": 0.7},
    ))

    world.say(
        f"In {world.place}, {params.name}, a {params.trait} {params.gender}, made {scene['object']} with Maya nearby."
    )
    world.say(
        f"The brushes swished, the paint pots gleamed, and the room sang, "
        f"'Make a bright design, make a bright design!'"
    )
    world.say(
        f"{params.helper} wore a bifocal lens: one part helped with things near, "
        f"and one part helped with things far."
    )
    world.say(
        f"{params.helper} smiled and said, \"A bifocal can show two views, but careful hands must still choose what to do.\""
    )
    world.say(
        f"Then {scene['problem']} appeared. {scene['foreshadow']}"
    )
    world.say(
        f"{params.name} saw the large trouble first and rushed toward it. "
        f"{scene['mistake']}"
    )
    world.say(
        f"Maya called, \"Wait, {params.name}! The little sign came first.\""
    )
    world.say(
        f"{params.name} answered, \"I thought I was helping. I am sorry I did not listen.\""
    )
    world.say(
        f"Maya replied, \"I was cross, but I can help you fix what happened.\""
    )
    world.say(
        f"That was reconciliation: not pretending the mistake was small, but joining hands to make the next choice kind."
    )
    world.para()
    world.say(
        f"{params.helper} pointed through the bifocal lens and said, "
        f"\"Near and far, both belong in our care. First we stop, then we share.\""
    )
    world.say(scene["plan"])
    world.say(
        f"They worked in a gentle rhyme: lift and lay, wipe and wait, "
        f"check the edge, then make it straight."
    )
    world.say(
        f"But the first rush had already left a mark. {scene['bad']}"
    )
    world.say(
        f"{params.name} lowered {params.name.split()[0] if ' ' in params.name else 'their'} head and said, "
        f"\"I wanted a perfect picture, but I made a bad ending.\""
    )
    world.say(
        f"{params.helper} answered, \"A bad ending is not the same as a bad child. "
        f"Tell the truth, repair what you can, and remember the warning.\""
    )
    world.say(
        f"Maya added, \"Next time we will look close and wide together.\""
    )
    world.say(scene["ending"])
    world.say(
        f"The room grew quiet, then kind. The lesson stayed bright: {scene['lesson']}."
    )

    artwork.meters["damage"] = 0.7
    child.memes["reconciled"] = 1.0
    child.memes["learned"] = 1.0
    world.facts.update(
        child=child,
        friend=friend,
        helper=helper,
        bifocal=bifocal,
        artwork=artwork,
        scene=scene,
        params=params,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    params = world.facts["params"]
    scene = world.facts["scene"]
    return [
        f"Write a rhyming story for children about {params.name} in an art room using a bifocal lens.",
        f"Include foreshadowing, reconciliation, dialogue, and a bad ending involving {scene['object']}.",
        f"Show how noticing both near and far clues could have prevented the art-room mistake.",
    ]


def story_qa(world: World) -> list[QAItem]:
    params = world.facts["params"]
    scene = world.facts["scene"]
    return [
        QAItem(
            question="Where did the story happen?",
            answer="The story happened in an art room filled with paint, paper, brushes, and art supplies.",
        ),
        QAItem(
            question="What was the bifocal used to show?",
            answer="The bifocal lens showed both a nearby warning and a farther part of the art-room problem.",
        ),
        QAItem(
            question="What foreshadowed the mistake?",
            answer=scene["foreshadow"],
        ),
        QAItem(
            question="How did reconciliation happen?",
            answer=f"{params.name} apologized for rushing, and Maya chose to help repair the damage instead of staying angry.",
        ),
        QAItem(
            question="Why was the ending bad?",
            answer=f"The rushed choice damaged {scene['object']}, so the artwork could be repaired but not made perfect again.",
        ),
        QAItem(
            question="What did the child learn?",
            answer=f"{params.name} learned that {scene['lesson']}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bifocal?",
            answer="A bifocal is a lens with two viewing areas, often helping someone see nearby and faraway things.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is an early clue that hints at something important that may happen later.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is making peace after a disagreement or mistake by speaking honestly and repairing trust.",
        ),
        QAItem(
            question="What is a bad ending?",
            answer="A bad ending is an outcome in which a problem causes harm or loss, even though the characters may still learn from it.",
        ),
        QAItem(
            question="Why should people be careful in an art room?",
            answer="People should be careful in an art room because spills, tools, and wet artwork can be damaged or cause someone to slip.",
        ),
    ]


ASP_RULES = r"""
#show coherent/1.
coherent(story) :- art_room, bifocal, foreshadowing, reconciliation, bad_ending, dialogue.
"""


def asp_facts() -> str:
    return "\n".join([
        "art_room.",
        "bifocal.",
        "foreshadowing.",
        "reconciliation.",
        "bad_ending.",
        "dialogue.",
    ])


def asp_program(show: str = "#show coherent/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        from asp import atoms, one_model
    except ImportError:
        return 0
    model = one_model(asp_program())
    return 0 if ("coherent", ("story",)) in atoms(model, "coherent") else 1


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id:8} ({entity.type:10}) "
            f"meters={entity.meters} memes={entity.memes}"
        )
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="art_room",
        name="Luna",
        gender="girl",
        helper="Ms. Vale",
        trait="curious",
        scene=0,
        rhyme=0,
        beat=3,
    ),
    StoryParams(
        place="art_room",
        name="Milo",
        gender="boy",
        helper="Mr. Chen",
        trait="bold",
        scene=2,
        rhyme=4,
        beat=17,
    ),
    StoryParams(
        place="art_room",
        name="Pia",
        gender="girl",
        helper="Aunt Bea",
        trait="thoughtful",
        scene=3,
        rhyme=6,
        beat=29,
    ),
]


def generate(params: StoryParams) -> StorySample:
    world = _build_world(params)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        print("1 coherent story: art room, bifocal, foreshadowing, reconciliation, bad ending, dialogue")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        for index in range(args.n):
            seed = base_seed + index
            rng = random.Random(seed)
            params = resolve_params(args, rng)
            params.seed = seed
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.name}: bifocal art-room rhyming story"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
