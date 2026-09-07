#!/usr/bin/env python3
"""
A tiny nursery-rhyme storyworld about gingham magic.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import asdict, dataclass, field
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from pathlib import Path as _StoryPath
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
sys.path.insert(0, str(_storyworlds_root))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Fabric:
    id: str
    label: str
    pattern: str
    strength: int
    magic: str


@dataclass
class Character:
    id: str
    name: str
    kind: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    characters: dict[str, Character] = field(default_factory=dict)
    fabric: Fabric | None = None
    magic_active: bool = False
    magic_goal: str = ""
    magic_result: str = ""
    paragraphs: list[str] = field(default_factory=list)
    facts: dict[str, Any] = field(default_factory=dict)

    def add(self, character: Character) -> None:
        self.characters[character.id] = character

    def say(self, text: str) -> None:
        self.paragraphs.append(text)

    def render(self) -> str:
        return "\n\n".join(self.paragraphs)


@dataclass
class StoryParams:
    fabric: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    object_name: str
    object_kind: str
    rhyme_place: str
    seed: int | None = None


FABRICS = {
    "gingham": Fabric(
        id="gingham",
        label="gingham",
        pattern="small blue-and-white checks",
        strength=4,
        magic="stitches lost things back into a happy pattern",
    ),
    "red_gingham": Fabric(
        id="red_gingham",
        label="red gingham",
        pattern="bright red-and-white checks",
        strength=5,
        magic="makes brave little pockets for helpful things",
    ),
    "green_gingham": Fabric(
        id="green_gingham",
        label="green gingham",
        pattern="fresh green-and-white checks",
        strength=4,
        magic="coaxes sleepy seeds to wake",
    ),
}

OBJECTS = {
    "moon": ("the moon", "moon", "a silver moon"),
    "button": ("a button", "button", "a round button"),
    "kite": ("a kite", "kite", "a paper kite"),
    "bell": ("a bell", "bell", "a tiny bell"),
}

PLACES = {
    "garden": ("the garden gate", "garden"),
    "meadow": ("the meadow brook", "meadow"),
    "kitchen": ("the kitchen chair", "kitchen"),
    "hill": ("the little hill", "hill"),
}

NAMES = {
    "girls": ["Mabel", "Nell", "Pip", "Daisy", "Rose"],
    "boys": ["Bram", "Tom", "Finn", "Jack", "Wren"],
}


def pronoun(gender: str, case: str = "subject") -> str:
    table = {
        "girl": {"subject": "she", "object": "her", "possessive": "her"},
        "boy": {"subject": "he", "object": "him", "possessive": "his"},
    }
    return table[gender][case]


def validate(params: StoryParams) -> None:
    if params.fabric not in FABRICS:
        raise StoryError(f"Unknown fabric: {params.fabric}")
    if params.object_kind not in OBJECTS:
        raise StoryError(f"Unknown magical object: {params.object_kind}")
    if params.rhyme_place not in PLACES:
        raise StoryError(f"Unknown place: {params.rhyme_place}")
    if params.child == params.helper:
        raise StoryError("The child and helper must have different names.")
    if not params.object_name.strip():
        raise StoryError("The magical object needs a name.")


def cast_magic(world: World) -> None:
    assert world.fabric is not None
    child = world.characters["child"]
    helper = world.characters["helper"]
    child.memes["wonder"] = child.memes.get("wonder", 0) + 1
    helper.memes["kindness"] = helper.memes.get("kindness", 0) + 1
    world.magic_active = True
    world.say(
        f"{child.name} held the {world.fabric.label} square beneath the moon. "
        f'"Little checks, wake and see—can you work your magic for me?" '
        f"{child.name} asked."
    )
    world.say(
        f'"Magic listens best to a careful heart," said {helper.name}. '
        f'"Tell it what must be mended, and let us help instead of grabbing."'
    )
    world.say(
        f"{child.name} nodded. \"Please bring back {world.magic_goal}.\" "
        f"{helper.name} placed one hand on the cloth, and {child.name} placed "
        f"the other."
    )
    world.say(
        f"Check by check, the gingham shimmered. A blue spark skipped, a white "
        f"spark winked, and the {world.magic_goal} came dancing home."
    )
    world.magic_result = f"The {world.magic_goal} returned safely through kind magic."
    child.meters["helpfulness"] = child.meters.get("helpfulness", 0) + 1
    helper.meters["helpfulness"] = helper.meters.get("helpfulness", 0) + 1


def build_world(params: StoryParams) -> World:
    validate(params)
    world = World()
    fabric = FABRICS[params.fabric]
    world.fabric = fabric
    child = Character(
        id="child",
        name=params.child,
        kind="child",
        role="seeker",
        meters={"curiosity": 1},
        memes={"wonder": 0},
    )
    helper = Character(
        id="helper",
        name=params.helper,
        kind="child",
        role="helper",
        meters={"kindness": 1},
        memes={"kindness": 0},
    )
    world.add(child)
    world.add(helper)
    place, place_word = PLACES[params.rhyme_place]
    object_label, object_kind, object_phrase = OBJECTS[params.object_kind]
    world.magic_goal = params.object_name
    world.facts.update(
        fabric=fabric,
        child=child,
        helper=helper,
        place=place,
        place_word=place_word,
        object_label=object_label,
        object_kind=object_kind,
        object_phrase=object_phrase,
    )
    world.say(
        f"On {place}, where the {place_word} winds blow, {params.child} found "
        f"a square of {fabric.label}, {fabric.pattern} in a row."
    )
    world.say(
        f"It had slipped from a pocket beside {object_label}, and the little "
        f"{object_kind} had vanished with a soft silver sound."
    )
    world.say(
        f'"Oh dear, oh dear, my {params.object_name} is gone!" cried '
        f"{params.child}. \"I need it before the stars come on.\""
    )
    world.say(
        f"{params.helper} came skipping by. \"Do not fear, do not fret. "
        f"We will look together, and perhaps we are not done yet.\""
    )
    world.say(
        f"The gingham gave a tiny twitch. Its checks shone bright, and a warm "
        f"wind curled around the cloth. {params.child} saw that the pattern was "
        f"not ordinary at all."
    )
    cast_magic(world)
    world.say(
        f"They laughed in a ring as the {params.object_name} settled in "
        f"{params.child}'s hands. Then the gingham rested, quiet and square, "
        f"while two friends danced in the {place_word} air."
    )
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a gentle nursery rhyme about {f['child'].name} finding magical "
        f"{f['fabric'].label} that helps recover {world.magic_goal}.",
        f"Tell a rhyming story in {f['place_word']} where two children use "
        f"kindness and Magic instead of arguing.",
        f"Write a child-facing tale featuring gingham, a lost {f['object_kind']}, "
        "a brief dialogue exchange, and a joyful ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            f"Where did {f['child'].name} find the {f['fabric'].label}?",
            f"{f['child'].name} found the {f['fabric'].label} on {f['place']}."
        ),
        QAItem(
            f"What did {world.magic_goal} do in the story?",
            f"The {world.magic_goal} had disappeared, and the magical gingham helped bring it back."
        ),
        QAItem(
            f"Who helped {f['child'].name} use the magic?",
            f"{f['helper'].name} helped by placing a hand on the gingham and speaking kindly."
        ),
        QAItem(
            "How did the story end?",
            f"The {world.magic_goal} returned safely, and the two children danced together."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is gingham?",
            "Gingham is a woven cloth with a repeated checked pattern, often made from two colors."
        ),
        QAItem(
            "What does magic mean in a story?",
            "Magic is an imaginary power that can make unusual and wonderful things happen."
        ),
        QAItem(
            "Why is it helpful to work together?",
            "Working together lets people share ideas and solve a problem with care."
        ),
    ]


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


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for character in world.characters.values():
        lines.append(
            f"{character.name}: role={character.role}, meters={character.meters}, "
            f"memes={character.memes}"
        )
    lines.append(f"fabric={world.fabric.id if world.fabric else None}")
    lines.append(f"magic_active={world.magic_active}")
    lines.append(f"magic_result={world.magic_result}")
    return "\n".join(lines)


ASP_RULES = r"""
magic_possible :- fabric(gingham), lost_object.
resolved :- magic_possible, kind_help.
#show resolved/0.
"""


def asp_facts() -> str:
    return "\n".join(
        [
            "fabric(gingham).",
            "lost_object.",
            "kind_help.",
        ]
    )


def asp_program() -> str:
    return asp_facts() + "\n" + ASP_RULES


def asp_verify() -> int:
    try:
        import asp
        model = asp.one_model(asp_program())
        if asp.atoms(model, "resolved"):
            print("OK: ASP magic resolution succeeded.")
            return 0
        print("MISMATCH: ASP did not resolve the magical story.")
        return 1
    except ImportError:
        print("ASP verification requires clingo.")
        return 1


CURATED = [
    StoryParams("gingham", "Mabel", "girl", "Bram", "boy", "Moonbeam", "moon", "garden"),
    StoryParams("red_gingham", "Nell", "girl", "Finn", "boy", "Button-Bright", "button", "kitchen"),
    StoryParams("green_gingham", "Wren", "boy", "Daisy", "girl", "Skybell", "bell", "meadow"),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A nursery-rhyme world of gingham Magic.")
    parser.add_argument("--fabric", choices=FABRICS)
    parser.add_argument("--child")
    parser.add_argument("--child-gender", choices=["girl", "boy"])
    parser.add_argument("--helper")
    parser.add_argument("--helper-gender", choices=["girl", "boy"])
    parser.add_argument("--object-name")
    parser.add_argument("--object-kind", choices=OBJECTS)
    parser.add_argument("--place", choices=PLACES, dest="rhyme_place")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    fabric = args.fabric or rng.choice(sorted(FABRICS))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    child_pool = NAMES["girls" if child_gender == "girl" else "boys"]
    helper_pool = NAMES["girls" if helper_gender == "girl" else "boys"]
    child = args.child or rng.choice(child_pool)
    helper_choices = [name for name in helper_pool if name != child]
    helper = args.helper or rng.choice(helper_choices)
    object_kind = args.object_kind or rng.choice(sorted(OBJECTS))
    object_name = args.object_name or rng.choice(
        {
            "moon": ["Moonbeam", "Silver Moon"],
            "button": ["Button-Bright", "Roundy"],
            "kite": ["Bluewing", "Dart"],
            "bell": ["Skybell", "Tinkle"],
        }[object_kind]
    )
    place = args.rhyme_place or rng.choice(sorted(PLACES))
    params = StoryParams(
        fabric=fabric,
        child=child,
        child_gender=child_gender,
        helper=helper,
        helper_gender=helper_gender,
        object_name=object_name,
        object_kind=object_kind,
        rhyme_place=place,
    )
    validate(params)
    return params


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
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        try:
            import asp
            model = asp.one_model(asp_program())
            print("resolved:", bool(asp.atoms(model, "resolved")))
        except ImportError:
            print("ASP mode requires clingo.")
        return

    rng = random.Random(args.seed)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        for index in range(args.n):
            params = resolve_params(args, random.Random(rng.randrange(2**31)))
            params.seed = args.seed
            samples.append(generate(params))

    if args.json:
        payload = [sample.to_dict() for sample in samples]
        print(json.dumps(payload[0] if len(payload) == 1 else payload, indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### story {index + 1}" if len(samples) > 1 else "",
        )
        if index + 1 < len(samples):
            print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()
