#!/usr/bin/env python3
"""
A small Tall Tale storyworld about Neurotic Nell, a nervous giant whose kindness
must learn to walk beside caution.
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

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str
    danger: str


@dataclass
class StoryParams:
    place: str
    giant: str
    child: str
    bell: str
    danger: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Tale:
    warning: str
    problem: str
    clue: str
    temptation: str
    method: str
    consequence: str
    repair: str
    lesson: str
    ending: str


TALES = [
    Tale(
        "the valley bell rang twice before breakfast",
        "a silver storm cloud was rolling toward the village",
        "the cloud's shadow stopped at the old bridge",
        "to grab the cloud with both enormous hands",
        "counted the thunderbeats and tested the bridge with one careful toe",
        "the bridge was cracked, and a careless giant step could have sent everyone into the river",
        "laid fallen pine trunks across the crack and guided the villagers over one at a time",
        "Kindness needs caution, especially when a helpful heart is bigger than a mountain.",
        "the village children crossed safely while the storm drummed softly on the new wooden path",
    ),
    Tale(
        "the moonlit scarecrow pointed toward the wheat field",
        "a runaway wagon was rolling downhill toward the sleeping barns",
        "three blue feathers spun in the wagon's wheel",
        "to leap in front of the wagon and stop it with her forehead",
        "watched its path from behind a stone wall and rolled a hay bale beneath its wheel",
        "the wagon would have crushed the grain gate if she had rushed without looking",
        "built a low earth ramp and tied a bright warning ribbon beside the hill",
        "A kind deed is safest when courage pauses long enough to notice the danger.",
        "the wagon rested beside the barn, and every horse munched calmly in the dawn",
    ),
    Tale(
        "the village well hummed a tune no one had taught it",
        "the well rope was fraying above a deep, dark shaft",
        "one red thread had caught on a thorn below the rim",
        "to yank the rope loose with all her giant strength",
        "tied a second rope around the stone post and lowered a lantern before touching the first",
        "a sudden pull could have dropped the bucket and frightened the children gathered nearby",
        "replaced the rope and fenced the well with bright painted rails",
        "Careful kindness protects the helper as well as the people being helped.",
        "fresh water splashed into the bucket while the painted rails shone like sunrise",
    ),
    Tale(
        "the tallest pine whispered the baker's name",
        "a flock of geese was trapped on a floating patch of ice",
        "the ice was thinning in a circle around the smallest goose",
        "to stomp into the pond and scoop up the whole flock",
        "threw warm blankets across the bank and made a quiet path with flat stones",
        "one giant splash could have broken the ice beneath every goose",
        "called the miller to bring a boat and kept the shore still until help arrived",
        "Gentle patience can be stronger than a very large rescue.",
        "the geese waddled home in a golden line behind the grateful miller",
    ),
    Tale(
        "a brass rooster crowed from the locked watchtower",
        "the tower's top stair had vanished during the night",
        "dust on the remaining step showed that loose stones had fallen inward",
        "to climb the tower by jumping from roof to roof",
        "circled the tower and listened for hollow stones before choosing a safer entrance",
        "one heroic leap could have shaken the whole tower onto the market square",
        "braced the doorway and carried the trapped rooster down through the wide lower gate",
        "Even a tall tale should leave room for a careful step.",
        "the brass rooster crowed from a safe perch while the tower waited for builders",
    ),
]

OPENINGS = [
    "In the kingdom of Bramblewide, people told tales so tall that birds nested in their endings.",
    "Long ago, beyond seven blue hills, lived a giant whose footsteps made teacups tremble.",
    "The villagers said no one had ever been kinder—or more neurotic—than the giant who guarded their road.",
    "At the edge of a valley wider than a whale's yawn stood a giant with a very worried heart.",
    "Every morning, the giant checked the sky, the stones, the bridges, and then checked them once more.",
]

DIALOGUE = [
    '"I must help at once!" cried the giant. "Please look first," said the child.',
    '"What if everyone is hurt?" asked the giant. "Then let us make a safe plan," replied the child.',
    '"My kindness is ready!" boomed the giant. "Good," said the child, "and let caution lead it."',
    '"I can fix this in one enormous blink," said the giant. "One careful blink is better," answered the child.',
]

CLOSINGS = [
    "From that day on, the giant still worried, but worried while making sensible plans.",
    "The villagers cheered, for the giant had learned that careful help can be grander than sudden help.",
    "And whenever danger whispered, the giant listened before kindness lifted a finger.",
    "The child wrote the lesson on a sign so large that clouds read it from above.",
]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict[str, object] = {}

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_world(params: StoryParams) -> World:
    setting = Setting(params.place, params.danger)
    world = World(setting)
    giant = world.add(Entity(
        "giant", "character", "giant", params.giant,
        meters={"height": 12.0, "caution": 0.0},
        memes={"kindness": 1.0, "worry": 0.0, "relief": 0.0},
    ))
    child = world.add(Entity(
        "child", "character", "child", params.child,
        meters={"height": 1.2, "caution": 1.0},
        memes={"kindness": 1.0, "wisdom": 1.0},
    ))
    bell = world.add(Entity(
        "bell", "thing", "bell", params.bell,
        meters={"ring": 0.0},
        memes={},
    ))
    place = world.add(Entity(
        "place", "thing", "setting", params.place,
        meters={"danger": 1.0, "safe": 0.0},
        memes={},
    ))
    return world


def tell(world: World, params: StoryParams) -> World:
    seed = params.seed
    if seed is None:
        seed = sum((i + 1) * ord(c) for i, c in enumerate(
            "|".join((params.place, params.giant, params.child, params.bell, params.danger))
        ))
    rng = random.Random(seed ^ 0xC0A17)
    tale = rng.choice(TALES)
    opening = rng.choice(OPENINGS)
    dialogue = rng.choice(DIALOGUE)
    closing = rng.choice(CLOSINGS)

    giant = world.entities["giant"]
    child = world.entities["child"]
    bell = world.entities["bell"]
    place = world.entities["place"]

    world.say(opening)
    world.say(
        f"{giant.label} was a neurotic giant, so kind that {giant.label.lower()} "
        f"carried lost beetles home and so cautious that {giant.label.lower()} counted "
        f"each toe before crossing a puddle."
    )
    world.say(
        f"Little {child.label} lived nearby and understood that a worried heart could "
        f"still make a very brave friend."
    )

    world.para()
    bell.meters["ring"] = 1.0
    giant.memes["worry"] = 1.0
    world.say(f"That morning, the {bell.label} rang, and {tale.warning}.")
    world.say(f"Then {tale.problem}. The danger was close enough to make the ground tremble.")
    world.say(dialogue)

    world.para()
    place.meters["danger"] = 1.0
    giant.meters["caution"] = 0.0
    world.say(f"{giant.label} leaned forward, ready to help, but {tale.clue}.")
    world.say(
        f"The giant's kind heart shouted, {tale.temptation.capitalize()}, "
        f"but {child.label} raised a small hand."
    )
    world.say(
        f'"Wait. Your size can save us only if your steps are safe," said {child.label}. '
        f'"Let us watch, measure, and choose."'
    )
    world.say(
        f"{giant.label} swallowed a nervous gulp, listened to {child.label}, and {tale.method}."
    )
    giant.meters["caution"] = 1.0
    giant.memes["worry"] = 0.5
    world.fired.add("caution-chosen")

    world.para()
    world.say(f"At last, they understood the danger: {tale.consequence.capitalize()}.")
    world.say(
        f"Because kindness had joined hands with caution, {giant.label} could help without "
        f"turning a rescue into a new disaster."
    )
    world.say(f"Together, the giant and the child {tale.repair}.")
    place.meters["danger"] = 0.0
    place.meters["safe"] = 1.0
    giant.memes["worry"] = 0.0
    giant.memes["relief"] = 1.0
    world.fired.add("danger-ended")

    world.para()
    world.say(f"{tale.ending.capitalize()}.")
    world.say(f"{closing} {tale.lesson}")
    world.say(f"The villagers rang the {bell.label} once for kindness and twice for caution.")

    world.facts.update(
        tale=tale,
        giant=giant,
        child=child,
        bell=bell,
        place=place,
        danger=params.danger,
        setting=params.place,
    )
    return world


PLACES = {
    "Bramblewide Valley": "a silver storm cloud",
    "Whaleback Hill": "a runaway wagon",
    "Moonwell Village": "a fraying well rope",
    "Frostmere": "a floating patch of ice",
    "Copperwatch": "a crumbling tower",
}

GIANTS = ["Nell", "Mara", "Bram", "Talla", "Orin", "Pella"]
CHILDREN = ["Pip", "Luma", "Toby", "Nia", "Cora", "Finn"]
BELLS = ["the blue valley bell", "the moon bell", "the brass warning bell", "the little tower bell"]

ASP_RULES = r"""
safe_place(P) :- place(P), danger(P), cautious(P), kindness(P), repaired(P).
#show safe_place/1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for place in PLACES:
        lines.append(asp.fact("place", place))
        lines.append(asp.fact("danger", place))
    lines.append(asp.fact("cautious", "tale"))
    lines.append(asp.fact("kindness", "tale"))
    lines.append(asp.fact("repaired", "tale"))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A neurotic giant learns cautious kindness.")
    parser.add_argument("--place", choices=list(PLACES))
    parser.add_argument("--giant")
    parser.add_argument("--child")
    parser.add_argument("--bell")
    parser.add_argument("--danger", choices=list(PLACES.values()))
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    return StoryParams(
        place=place,
        giant=args.giant or rng.choice(GIANTS),
        child=args.child or rng.choice(CHILDREN),
        bell=args.bell or rng.choice(BELLS),
        danger=args.danger or PLACES[place],
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    tale: Tale = f["tale"]  # type: ignore[assignment]
    return [
        "Write a Tall Tale about a neurotic giant whose kindness must learn caution.",
        f"Tell how {f['giant'].label} helped safely when {tale.problem}.",
        f"Write a suspenseful child-facing story in {f['setting']} using the clue that {tale.clue}.",
    ]


def story_questions(world: World) -> list[QAItem]:
    f = world.facts
    tale: Tale = f["tale"]  # type: ignore[assignment]
    giant: Entity = f["giant"]  # type: ignore[assignment]
    child: Entity = f["child"]  # type: ignore[assignment]
    return [
        QAItem(
            f"Why was {giant.label} called neurotic?",
            f"{giant.label} worried about many dangers and checked things repeatedly, even while trying to be kind.",
        ),
        QAItem(
            f"What danger did {giant.label} notice in {f['setting']}?",
            f"{tale.problem.capitalize()}.",
        ),
        QAItem(
            f"What clue helped {giant.label} and {child.label} understand the danger?",
            f"They noticed that {tale.clue}.",
        ),
        QAItem(
            f"How did {child.label} change the giant's plan?",
            f"{child.label} asked the giant to pause, watch, measure, and choose a safe method instead of rushing.",
        ),
        QAItem(
            "How did kindness and caution work together?",
            f"They used the giant's strength carefully, so they could {tale.repair} without creating a new danger.",
        ),
        QAItem(
            "What lesson did the tale teach?",
            tale.lesson,
        ),
    ]


def world_questions(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What does caution mean?",
            "Caution means noticing possible danger and acting carefully.",
        ),
        QAItem(
            "What is kindness?",
            "Kindness is caring about others and trying to help them.",
        ),
        QAItem(
            "What makes suspense in a story?",
            "Suspense grows when a danger is near and readers wait to learn what will happen.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: kind={entity.kind} type={entity.type} "
            f"meters={dict(entity.meters)} memes={dict(entity.memes)}"
        )
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_questions(world),
        world_qa=world_questions(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool, qa: bool, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show place/1."))
    found = {row[0] for row in asp.atoms(model, "place")}
    expected = set(PLACES)
    if found != expected:
        print("ASP/Python registry mismatch.")
        return 1
    if not all(generate(StoryParams(
        place=p,
        giant="Nell",
        child="Pip",
        bell="the moon bell",
        danger=PLACES[p],
        seed=i,
    )).story for i, p in enumerate(PLACES)):
        print("Generated story verification failed.")
        return 1
    print(f"OK: ASP/Python parity and generated stories ({len(expected)} places).")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show place/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show place/1."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for i, place in enumerate(PLACES):
            params = StoryParams(
                place=place,
                giant=GIANTS[i % len(GIANTS)],
                child=CHILDREN[i % len(CHILDREN)],
                bell=BELLS[i % len(BELLS)],
                danger=PLACES[place],
                seed=base_seed + i,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < max(1, args.n):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            sample = generate(params)
            index += 1
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)

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
