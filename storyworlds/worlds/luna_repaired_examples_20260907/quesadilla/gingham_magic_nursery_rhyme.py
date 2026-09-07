#!/usr/bin/env python3
"""
A gentle nursery-rhyme storyworld about a gingham cloth and a little bit of magic.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


SETTINGS = (
    "a moonlit nursery",
    "a little cottage kitchen",
    "a garden beside the sleepy lane",
    "a warm room beneath the attic stars",
)

CHILDREN = (
    ("Mira", "girl"),
    ("Tom", "boy"),
    ("Pip", "child"),
    ("Nell", "girl"),
)

HELPERS = (
    ("Grandma Rose", "woman"),
    ("Mother May", "woman"),
    ("Papa Ben", "man"),
    ("Auntie June", "woman"),
)

OBJECTS = (
    {
        "item": "a tiny silver bell",
        "place": "the windowsill",
        "wish": "a warm goodnight song",
        "trouble": "the night had grown too quiet",
        "magic": "three blue stars",
        "ending": "the bell chimed softly until every dream was bright",
    },
    {
        "item": "a little wooden spoon",
        "place": "the kitchen shelf",
        "wish": "a bowl of moonlight porridge",
        "trouble": "the supper pot was empty",
        "magic": "a golden sunbeam",
        "ending": "the spoon rested beside a full warm bowl",
    },
    {
        "item": "a red mitten",
        "place": "the coat peg",
        "wish": "a path through the snow",
        "trouble": "the garden gate was hidden white",
        "magic": "a flock of glowing fireflies",
        "ending": "the mitten waved farewell beside the open gate",
    },
    {
        "item": "a blue ribbon",
        "place": "the toy chest",
        "wish": "a dance for a sleepy moon",
        "trouble": "the moon looked lonely overhead",
        "magic": "a silver skipping rope",
        "ending": "the ribbon curled like a smile beneath the moon",
    },
)

VERSE_REACTIONS = (
    "clapped twice and counted to three",
    "whispered a rhyme beneath a blanket",
    "tapped one toe upon the floor",
    "curtsied gently and closed one eye",
)

ENDINGS = (
    "Then hush-a-bye, and softly glow; the magic knew just where to go.",
    "So round and round the moonbeams flew, and all the nursery dreams came true.",
    "The stars said, “Rest,” the shadows sighed, and quiet magic tucked them inside.",
)


@dataclass
class StoryParams:
    seed: int | None = None
    child_name: str = "Mira"
    child_type: str = "girl"
    helper_name: str = "Grandma Rose"
    helper_type: str = "woman"
    setting: str = SETTINGS[0]
    item: str = OBJECTS[0]["item"]
    place: str = OBJECTS[0]["place"]
    wish: str = OBJECTS[0]["wish"]
    trouble: str = OBJECTS[0]["trouble"]
    magic: str = OBJECTS[0]["magic"]
    ending: str = OBJECTS[0]["ending"]
    reaction: str = VERSE_REACTIONS[0]
    final_rhyme: str = ENDINGS[0]
    samples: list = field(default_factory=list)


@dataclass
class Entity:
    id: str
    label: str
    kind: str = "thing"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.fired: set[str] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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


def build_world(params: StoryParams) -> World:
    world = World(params)
    child = world.add(Entity("child", params.child_name, "character", memes={"wonder": 1.0}))
    helper = world.add(Entity("helper", params.helper_name, "character", memes={"care": 1.0}))
    cloth = world.add(Entity("gingham", "a red-and-white gingham cloth", "cloth", meters={"softness": 1.0}))
    charm = world.add(Entity("charm", params.item, "magical thing", memes={"magic": 0.0}))

    world.facts.update(child=child, helper=helper, cloth=cloth, charm=charm)

    world.say(
        f"In {params.setting}, where sleepy shadows lay, {params.child_name} found "
        f"a red-and-white gingham cloth at break of day."
    )
    world.say(
        f"It covered {params.item} in {params.place}, with a little silver sparkle "
        f"and a moonbeam face."
    )

    world.para()
    world.say(
        f'"Dear gingham cloth," said {params.child_name}, "please help me tonight. '
        f"I wish for {params.wish}, and {params.trouble}."'
    )
    world.say(
        f"{params.child_name} {params.reaction}; the gingham squares began to glow, "
        f"and a tiny bell gave a bright ding-ding sound."
    )
    cloth.memes["listening"] = 1.0
    charm.memes["magic"] = 1.0
    world.fired.add("wish_heard")

    world.para()
    world.say(
        f"Then out of the gingham came {params.magic}, twinkling in a row. "
        f"They spun around the room and made the sleepy shadows go."
    )
    world.say(
        f"{params.helper_name} came softly in and smiled at the sight. "
        f'"Kind magic grows from caring hearts," {params.helper_name} said that night.'
    )
    helper.memes["joy"] = 1.0
    child.memes["hope"] = 1.0
    world.fired.add("magic_answered")

    world.para()
    world.say(
        f"{params.ending}. {params.child_name} folded the gingham carefully and "
        f"placed it beside {params.item} for another helpful day."
    )
    world.say(params.final_rhyme)
    world.fired.add("story_resolved")
    child.memes["peace"] = 1.0
    cloth.meters["warmth"] = 1.0
    return world


ASP_RULES = r"""
has(gingham).
has(charm).
makes_wish(child).
cares_for(helper, child).
magic_answered :- has(gingham), has(charm), makes_wish(child), cares_for(helper, child).
resolved :- magic_answered.
#show magic_answered/0.
#show resolved/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("has", "gingham"),
            asp.fact("has", "charm"),
            asp.fact("makes_wish", "child"),
            asp.fact("cares_for", "helper", "child"),
        ]
    )


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    magic = asp.atoms(model, "magic_answered")
    resolved = asp.atoms(model, "resolved")
    if magic == [()] and resolved == [()]:
        sample = generate(resolve_params(argparse.Namespace(seed=7), random.Random(7)))
        if "gingham" in sample.story.lower() and "magic" in sample.story.lower():
            print("OK: ASP, Python, and generated story agree.")
            return 0
    print("MISMATCH between ASP, Python, and generated story.")
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    seed = getattr(args, "seed", None)
    if seed is None:
        seed = 0
    child_name, child_type = CHILDREN[seed % len(CHILDREN)]
    helper_name, helper_type = HELPERS[(seed // 2) % len(HELPERS)]
    obj = OBJECTS[(seed // 3) % len(OBJECTS)]
    return StoryParams(
        seed=seed,
        child_name=child_name,
        child_type=child_type,
        helper_name=helper_name,
        helper_type=helper_type,
        setting=rng.choice(SETTINGS),
        item=obj["item"],
        place=obj["place"],
        wish=obj["wish"],
        trouble=obj["trouble"],
        magic=obj["magic"],
        ending=obj["ending"],
        reaction=rng.choice(VERSE_REACTIONS),
        final_rhyme=rng.choice(ENDINGS),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    child = world.facts["child"]
    helper = world.facts["helper"]
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            "Write a nursery rhyme about gingham cloth and gentle magic.",
            f"Tell how {child.label} makes a wish in {params.setting}.",
            f"Show how {helper.label} explains that caring hearts can make magic.",
        ],
        story_qa=[
            QAItem(
                question=f"What did {child.label} find in {params.place}?",
                answer=f"{child.label} found {params.item} covered by a red-and-white gingham cloth in {params.place}.",
            ),
            QAItem(
                question=f"What did {child.label} wish for?",
                answer=f"{child.label} wished for {params.wish} because {params.trouble}.",
            ),
            QAItem(
                question="How did the gingham cloth help?",
                answer=f"The gingham cloth glowed and brought out {params.magic}, which solved the trouble and made the room bright.",
            ),
            QAItem(
                question=f"What did {helper.label} say about the magic?",
                answer=f"{helper.label} said that kind magic grows from caring hearts.",
            ),
        ],
        world_qa=[
            QAItem(
                question="What is gingham?",
                answer="Gingham is a woven fabric with a simple checked pattern, often made from two colors.",
            ),
            QAItem(
                question="What is magic in this nursery rhyme?",
                answer="Magic is the wondrous power that lets the gingham cloth answer a kind wish and bring comfort.",
            ),
        ],
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A gingham magic nursery-rhyme world.")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        print("magic_answered:", asp.atoms(model, "magic_answered"))
        print("resolved:", asp.atoms(model, "resolved"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    count = len(OBJECTS) if args.all else max(1, args.n)
    samples = []
    for index in range(count):
        seed = base_seed + index
        params = resolve_params(argparse.Namespace(seed=seed), random.Random(seed))
        samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
