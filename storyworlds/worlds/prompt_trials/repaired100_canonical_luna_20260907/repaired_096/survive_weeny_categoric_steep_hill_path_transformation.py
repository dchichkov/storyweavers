#!/usr/bin/env python3
"""
A gentle bedtime storyworld about surviving a steep hill path through a weeny
transformation and a little magic.
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
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    id: str
    label: str
    affordances: set[str]


@dataclass
class Transformation:
    id: str
    small_form: str
    changed_form: str
    trigger: str
    gift: str


@dataclass
class Magic:
    id: str
    object_label: str
    rule: str
    light: str


@dataclass
class World:
    setting: Setting
    hero: Entity
    helper: Entity
    transformation: Transformation
    magic: Magic
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = {
    "steep_hill_path": Setting(
        "steep_hill_path",
        "the steep hill path",
        {"climbing", "resting", "moonlight"},
    )
}

TRANSFORMATIONS = {
    "weeny_to_wise": Transformation(
        "weeny_to_wise",
        "a weeny field mouse",
        "a bright-footed little guide",
        "kindness offered at the hardest step",
        "seeing safe footholds that others missed",
    )
}

MAGIC = {
    "moonbutton": Magic(
        "moonbutton",
        "a silver moon-button",
        "it shines only when someone chooses care over speed",
        "a soft blue path of light",
    )
}

NAMES = ["Luna", "Mira", "Nell", "Pip"]
TRAITS = ["curious", "patient", "gentle", "brave"]

TALES = [
    {
        "id": "loose_stones",
        "trouble": "the upper stones had loosened after a night of rain",
        "danger": "a hurried climber could slip toward the thorn bushes",
        "clue": "tiny wet tracks stopped beside a flat stone",
        "action": "Luna placed small twigs beside the loose stones so no one would step there",
        "turn": "the safest route was not the straightest route but a winding shelf beside the moss",
        "resolution": "the travelers crossed one careful step at a time",
        "ending": "the hill wore a necklace of blue moonlight beneath the sleepy stars",
    },
    {
        "id": "fallen_branch",
        "trouble": "a fallen branch blocked the narrowest part of the path",
        "danger": "the only gap beneath it was too low for anyone carrying a lantern",
        "clue": "a warm golden spark trembled under a curled leaf",
        "action": "Luna tucked her moon-button beneath the branch and watched the shadows move",
        "turn": "the magic revealed a wider passage around the back of the hill",
        "resolution": "everyone followed the longer path and kept both hands free",
        "ending": "the branch became a bed for sleepy birds while the travelers reached the top",
    },
    {
        "id": "misty_turn",
        "trouble": "mist hid the bend where the steep path divided",
        "danger": "the bright-looking trail ended at a crumbling ledge",
        "clue": "a weeny bellflower leaned away from the dangerous edge",
        "action": "Luna listened to the bellflower and marked the safe trail with pale pebbles",
        "turn": "the flower's tiny ringing matched the moon-button's glow",
        "resolution": "the group waited for one another and climbed by the marked trail",
        "ending": "the bellflower rang softly as dawn painted the hill pink",
    },
]

REFLECTIONS = [
    "A small helper can survive a great climb when care makes the next step clear.",
    "Being weeny does not mean being helpless; it can mean noticing what larger eyes overlook.",
    "Magic is kindest when it helps everyone move safely, not when it makes one traveler win.",
    "A slow path can be the wisest path when the hill is steep.",
]


@dataclass
class StoryParams:
    place: str
    transformation: str
    magic: str
    hero_name: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    return [
        (place, transformation, magic)
        for place in SETTINGS
        for transformation in TRANSFORMATIONS
        for magic in MAGIC
        if "climbing" in SETTINGS[place].affordances
    ]


def _lookup(mapping, key):
    if key not in mapping:
        raise StoryError(f"Unknown choice: {key}")
    return mapping[key]


def build_world(params: StoryParams) -> World:
    setting = _lookup(SETTINGS, params.place)
    transformation = _lookup(TRANSFORMATIONS, params.transformation)
    magic = _lookup(MAGIC, params.magic)
    if params.place != "steep_hill_path":
        raise StoryError("This bedtime tale belongs on the steep hill path.")
    hero = Entity(
        params.hero_name,
        "child",
        params.hero_name,
        meters={"height": 1.2, "energy": 8.0},
        memes={"curiosity": 7.0, "courage": 5.0},
    )
    helper = Entity(
        "weeny_mouse",
        "animal",
        "a weeny field mouse",
        meters={"height": 0.12, "energy": 6.0},
        memes={"notice": 9.0, "trust": 8.0},
    )
    world = World(setting, hero, helper, transformation, magic)
    rng = random.Random(params.seed)
    tale = TALES[rng.randrange(len(TALES))]
    reflection = REFLECTIONS[rng.randrange(len(REFLECTIONS))]
    question = rng.choice([
        f'"Should we hurry?" {params.hero_name} asked.',
        f'"Can a weeny mouse really help us?" {params.hero_name} whispered.',
        f'"What does the moon-button want us to notice?" {params.hero_name} asked.',
    ])
    answer = rng.choice([
        '"Slow feet can still reach a high place," said the mouse.',
        '"Look low, little friend. The safe way is hiding there," said the mouse.',
        '"It shines for care," said the mouse. "Not for rushing."',
    ])

    world.facts.update(
        tale=tale,
        reflection=reflection,
        question=question,
        answer=answer,
        transformation_note="the weeny mouse grew just large enough to guide the travelers",
        changed=True,
    )

    world.say(
        f"Once, at bedtime, {params.hero_name}, a {params.trait} child, stood at the foot of "
        f"{setting.label}. The hill rose steeply into the sleepy sky."
    )
    world.say(
        f"Beside {params.hero_name} waited {helper.label}, so small that one warm mitten could shelter him. "
        f"Together they hoped to survive the climb and carry a lantern to the cottage above."
    )
    world.say(f"But {tale['trouble']}. {tale['danger'].capitalize()}.")
    world.para()
    world.say(
        f"{params.hero_name} held up {magic.object_label}. Its rule was simple: {magic.rule}."
    )
    world.say(question)
    world.say(answer)
    world.say(
        f"Then the mouse pointed to the first clue: {tale['clue']}. "
        f"{params.hero_name} stopped looking at the whole hill and looked only at the next step."
    )
    world.say(f"Together, they {tale['action']}.")
    world.para()
    world.say(
        f"When the moon-button shone, a {magic.light} curled around the mouse. "
        f"In a gentle {transformation.id.replace('_', ' ')}, the {transformation.small_form} became "
        f"{transformation.changed_form}. The change lasted only while courage was needed."
    )
    world.say(f"The transformation showed them that {tale['turn']}.")
    world.say(f"So {tale['resolution']}. The mouse used {transformation.gift}.")
    world.para()
    world.say(
        f"At last, {params.hero_name} placed the lantern beside the cottage door. "
        f"The mouse became weeny again and curled beside the warm light."
    )
    world.say(f"{tale['ending']}.")
    world.say(f"Before sleep, {params.hero_name} remembered: {reflection}")
    return world


def generation_prompts(world: World) -> list[str]:
    tale = world.facts["tale"]
    return [
        f"Write a bedtime story about surviving a steep hill path with a weeny magical helper after {tale['trouble']}.",
        "Tell a gentle story featuring a Transformation and Magic, where a small creature changes to help everyone travel safely.",
        "Write a child-facing adventure in which careful choices matter more than speed.",
    ]


def story_qa(world: World) -> list[QAItem]:
    tale = world.facts["tale"]
    return [
        QAItem(
            "What danger did the travelers face?",
            f"They faced {tale['trouble']}, and {tale['danger']}.",
        ),
        QAItem(
            "How did the weeny helper change?",
            f"The weeny mouse became {world.transformation.changed_form} when the moon-button's magic was needed.",
        ),
        QAItem(
            "What did the moon-button reveal?",
            f"It revealed that {tale['turn']}.",
        ),
        QAItem(
            "How did the travelers survive the climb?",
            f"They survived by moving carefully: {tale['resolution']}.",
        ),
        QAItem(
            "What lesson did Luna learn?",
            f"Luna learned that {world.facts['reflection']}",
        ),
    ]


KNOWLEDGE = [
    QAItem(
        "What is a transformation?",
        "A transformation is a change from one form or condition into another.",
    ),
    QAItem(
        "What is magic in a bedtime story?",
        "Magic is a wondrous power that can make an impossible or mysterious event happen.",
    ),
    QAItem(
        "What does weeny mean?",
        "Weeny means very small.",
    ),
    QAItem(
        "What does categoric mean?",
        "Categoric means definite and without exceptions or uncertainty.",
    ),
    QAItem(
        "What helps someone survive a difficult journey?",
        "Careful choices, useful help, patience, and attention to danger can help someone survive a difficult journey.",
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(KNOWLEDGE)


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
    lines.append("\n== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}\nA: {item.answer}")
    lines.append("\n== World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}\nA: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
#show valid/3.
valid(P, T, M) :- place(P), transformation(T), magic(M), affords(P, climbing).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("place", place))
        for affordance in sorted(setting.affordances):
            lines.append(asp.fact("affords", place, affordance))
    for transformation in TRANSFORMATIONS:
        lines.append(asp.fact("transformation", transformation))
    for magic in MAGIC:
        lines.append(asp.fact("magic", magic))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_choices = set(valid_combos())
    asp_choices = set(asp_valid_combos())
    if python_choices != asp_choices:
        print("ASP/Python parity check failed.")
        print("Only in Python:", sorted(python_choices - asp_choices))
        print("Only in ASP:", sorted(asp_choices - python_choices))
        return 1
    for seed in range(3):
        params = StoryParams(
            "steep_hill_path",
            "weeny_to_wise",
            "moonbutton",
            "Luna",
            "gentle",
            seed,
        )
        sample = generate(params)
        if not sample.story or "steep hill path" not in sample.story:
            print("Generated story check failed.")
            return 1
    print(f"OK: ASP/Python parity and generated stories verified ({len(python_choices)} combos).")
    return 0


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in (world.hero, world.helper):
        lines.append(
            f"{entity.label}: meters={entity.meters}; memes={entity.memes}"
        )
    lines.append(f"setting={world.setting.label}")
    lines.append(f"transformation={world.transformation.id}")
    lines.append(f"magic={world.magic.id}")
    lines.append(f"resolved={world.facts.get('changed', False)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Bedtime storyworld about surviving a steep hill path."
    )
    parser.add_argument("--place", choices=SETTINGS)
    parser.add_argument("--transformation", choices=TRANSFORMATIONS)
    parser.add_argument("--magic", choices=MAGIC)
    parser.add_argument("--name")
    parser.add_argument("--trait", choices=TRAITS)
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.transformation:
        combos = [c for c in combos if c[1] == args.transformation]
    if args.magic:
        combos = [c for c in combos if c[2] == args.magic]
    if not combos:
        raise StoryError("No compatible steep hill path story choices were found.")
    place, transformation, magic = rng.choice(combos)
    return StoryParams(
        place=place,
        transformation=transformation,
        magic=magic,
        hero_name=args.name or rng.choice(NAMES),
        trait=args.trait or rng.choice(TRAITS),
        seed=args.seed,
    )


def emit(sample: StorySample, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(
        "steep_hill_path",
        "weeny_to_wise",
        "moonbutton",
        "Luna",
        "gentle",
        960202609,
    )
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        for place, transformation, magic in asp_valid_combos():
            print(f"{place}: {transformation} + {magic}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        for index in range(max(0, args.n)):
            seed = base_seed + index
            local_args = argparse.Namespace(**vars(args))
            local_args.seed = seed
            params = resolve_params(local_args, random.Random(seed))
            params.seed = seed
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
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
