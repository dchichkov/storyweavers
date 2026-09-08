#!/usr/bin/env python3
"""
A small cautionary slice-of-life storyworld about connecting carefully.

Luna wants to connect two parts of a neighborhood garden project. A loose
bridge board and an eager shortcut create a small danger. By listening,
checking the fasteners, and asking for help, Luna repairs the connection and
learns that careful work keeps people close.
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

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", "..", ".."))
REPO_ROOT = os.path.dirname(ROOT)
for path in (REPO_ROOT, ROOT):
    if path not in sys.path:
        sys.path.insert(0, path)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Scene:
    place: str
    project: str
    connection: str
    warning: str


class World:
    def __init__(self, scene: Scene):
        self.scene = scene
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.events: list[str] = []

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


@dataclass(frozen=True)
class Arc:
    id: str
    need: str
    obstacle: str
    turn: str
    action: str
    result: str
    ending: str


SCENES = {
    "garden": Scene(
        place="the community garden",
        project="a watering line",
        connection="a short hose",
        warning="the ground near the shed was muddy",
    ),
    "library": Scene(
        place="the library courtyard",
        project="a reading corner",
        connection="a string of paper flags",
        warning="the stone path was slick from rain",
    ),
    "porch": Scene(
        place="the apartment porch",
        project="a row of herb pots",
        connection="a narrow shelf",
        warning="the shelf stood close to the railing",
    ),
}

ARCS = (
    Arc(
        "loose_board",
        "wanted to finish a helpful job before lunch",
        "One board in the little walkway rocked when Luna stepped near it.",
        "Luna noticed a bright screw lying in the dirt and realized the board had not been fastened at all.",
        "She stopped, told Sam what she had seen, and held the board steady while Sam brought a screwdriver.",
        "The board became safe, and the path connected the garden beds without a wobble.",
        "A line of muddy footprints crossed the repaired board, each one careful and sure.",
    ),
    Arc(
        "short_hose",
        "was eager to help the older neighbors",
        "The hose reached the first bed but pulled tight before it reached the second.",
        "Luna saw the strain lifting one corner of the tap and understood that a quick tug could break it.",
        "She asked Mr. Vale for a second hose, then connected the two with a soft rubber joiner.",
        "Water reached both beds without a burst pipe or a soaked pair of shoes.",
        "The last drops glittered on the leaves while the two connected hoses rested like a friendly bridge.",
    ),
    Arc(
        "paper_flags",
        "wanted the courtyard to look welcoming for story hour",
        "A gust pulled the flags toward a low branch, and the string began to snag.",
        "Instead of pulling harder, Luna traced the string and found a hidden thorn.",
        "She called to Nia, lowered the line, and wrapped the sharp branch with a cloth before tying the flags again.",
        "The flags connected the reading corner to the gate without tearing or scratching anyone.",
        "When the wind returned, the flags fluttered freely above the children arriving with books.",
    ),
    Arc(
        "shelf_gap",
        "had promised to help make space for fresh herbs",
        "A gap opened between the shelf and the porch post as soon as the first pot was placed.",
        "Luna heard the wood creak and realized the shelf needed support before anything else went on it.",
        "She moved the pots away, fetched a flat brace, and asked her aunt to check the level.",
        "The shelf held steady, and the herbs could share sunlight without leaning toward danger.",
        "Mint, basil, and thyme stood in a neat connected row, their leaves brushing the morning air.",
    ),
)

NAMES = ["Luna", "Milo", "Tessa", "Noor", "Cal"]
HELPERS = ["Sam", "Nia", "Mr. Vale", "Aunt Rosa", "Jo"]

OPENINGS = (
    "After breakfast, {name} went to {place} because she {need}.",
    "{name} carried a small tool bag to {place}. She {need}, and she hoped the work would be simple.",
    "The morning was ordinary until {name} decided to help {place}. She {need}.",
)

DIALOGUES = (
    '"Can we connect it now?" Luna asked. "First we check what might move," said {helper}.',
    '"It looks almost finished," Luna said. {helper} answered, "Almost is when careful eyes matter most."',
    'Luna pointed and said, "Something feels wrong." "{warning}," replied {helper}. "Let us stop and look."',
)

RESPONSES = (
    '"I am glad we checked," Luna said. {helper} nodded. "Careful work helps everyone."',
    'Luna smiled. "Now it can connect safely." {helper} replied, "And now we know why."',
    'The small repair made Luna breathe easier. "A shortcut is not always the quickest way," she said.',
)


@dataclass
class StoryParams:
    place: str
    child_name: str
    helper_name: str
    seed: Optional[int] = None


def _choose_type(name: str) -> str:
    return "girl" if name in {"Luna", "Tessa", "Noor"} else "boy"


def simulate(params: StoryParams) -> World:
    if params.place not in SCENES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.child_name == params.helper_name:
        raise StoryError("The child and helper must be different people.")
    scene = SCENES[params.place]
    rng = random.Random(params.seed if params.seed is not None else 0)
    arc = rng.choice(ARCS)
    opening = rng.choice(OPENINGS)
    dialogue = rng.choice(DIALOGUES)
    response = rng.choice(RESPONSES)

    world = World(scene)
    child = world.add(Entity(params.child_name, "character", _choose_type(params.child_name)))
    helper = world.add(Entity(params.helper_name, "character", "helper"))
    project = world.add(Entity("project", "thing", "project", scene.project))
    connection = world.add(Entity("connection", "thing", "connection", scene.connection))
    world.facts.update(
        child=child,
        helper=helper,
        project=project,
        connection=connection,
        arc=arc,
        dialogue=dialogue,
        response=response,
    )

    def fill(text: str) -> str:
        return text.format(
            name=child.id,
            helper=helper.id,
            place=scene.place,
            need=arc.need,
            warning=scene.warning,
        )

    world.say(fill(opening))
    world.say(
        f"She planned to connect {scene.project} with {scene.connection}, "
        "so neighbors could use the space together."
    )
    world.para()

    connection.meters["placed"] = 1.0
    child.memes["eager"] = 1.0
    world.say(arc.obstacle)
    world.events.append("A possible safety problem appeared before the connection was complete.")
    world.para()

    child.memes["cautious"] = 1.0
    world.say(fill(dialogue))
    world.say(arc.turn)
    world.say(arc.action)
    connection.meters["checked"] = 1.0
    connection.meters["connected"] = 1.0
    world.events.append("The characters paused, inspected the connection, and chose a safer method.")
    world.para()

    child.memes["relieved"] = 1.0
    world.say(arc.result)
    world.say(fill(response))
    world.say(arc.ending)
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    arc: Arc = world.facts["arc"]  # type: ignore[assignment]
    return [
        f"Write a cautionary slice-of-life story about {world.facts['child'].id} learning to connect things safely.",
        f"Tell a gentle story at {world.scene.place} where a small danger interrupts {arc.need}.",
        "Show dialogue, a careful pause, a helpful repair, and an ending image that proves the connection is safe.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    arc: Arc = world.facts["arc"]  # type: ignore[assignment]
    return [
        QAItem(
            f"Why was {child.id} working at {world.scene.place}?",
            f"{child.id} was there because she {arc.need}. She wanted to connect {world.scene.project} for everyone to use.",
        ),
        QAItem(
            "What warning showed that the first plan was unsafe?",
            f"{arc.obstacle} The warning mattered because rushing could have caused a fall, a break, or another small injury.",
        ),
        QAItem(
            f"How did {child.id} and {helper.id} solve the problem?",
            arc.action,
        ),
        QAItem(
            "What changed by the end of the story?",
            f"{arc.result} The connection was finished only after it had been checked and made safe.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "Why should someone stop when a connection seems loose?",
            "A loose connection can slip, break, or hurt someone, so stopping gives people time to inspect it and choose a safer repair.",
        ),
        QAItem(
            "Why is asking a helper useful?",
            "A helper may notice a risk, know the right tool, or hold something steady while the work is completed.",
        ),
        QAItem(
            "What does connect mean?",
            "To connect means to join two things so they can work together or form one useful path.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
reasonable(C,H,X) :- child(C), helper(H), connection(X), checked(X), connected(X).
safe_connection(X) :- connection(X), checked(X), connected(X).
caution_required(X) :- connection(X), placed(X), not checked(X).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    lines = [
        asp.fact("child", "luna"),
        asp.fact("helper", "sam"),
        asp.fact("connection", "link"),
        asp.fact("placed", "link"),
        asp.fact("checked", "link"),
        asp.fact("connected", "link"),
    ]
    return "\n".join(lines)


def asp_program(show: str = "#show reasonable/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program())
    if not model:
        print("ASP verification failed: no model.")
        return 1
    if ("luna", "sam", "link") not in set(asp.atoms(model, "reasonable")):
        print("ASP verification failed: expected reasonable connection.")
        return 1
    print("OK: ASP and Python safety conditions agree.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Cautionary connect slice-of-life storyworld.")
    parser.add_argument("--place", choices=sorted(SCENES))
    parser.add_argument("--child-name", choices=NAMES)
    parser.add_argument("--helper-name", choices=HELPERS)
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
    child = args.child_name or rng.choice(NAMES)
    helper = args.helper_name or rng.choice(HELPERS)
    if child == helper:
        raise StoryError("The child and helper must be different people.")
    return StoryParams(
        place=args.place or rng.choice(list(SCENES)),
        child_name=child,
        helper_name=helper,
        seed=rng.randrange(2**31),
    )


def generate(params: StoryParams) -> StorySample:
    world = simulate(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print("\n--- trace ---")
        for entity in sample.world.entities.values():
            print(entity.id, entity.type, dict(entity.meters), dict(entity.memes))
        print("events:", "; ".join(sample.world.events))
    if qa:
        print("\n" + format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp

        model = asp.one_model(asp_program())
        print("\n".join(str(atom) for atom in model))
        return

    seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        params_list = [
            StoryParams("garden", "Luna", "Sam", 101),
            StoryParams("library", "Tessa", "Nia", 202),
            StoryParams("porch", "Noor", "Aunt Rosa", 303),
        ]
    else:
        params_list = [
            resolve_params(args, random.Random(seed + i))
            for i in range(max(1, args.n))
        ]
    samples = [generate(params) for params in params_list]

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### story {i + 1}" if len(samples) > 1 else "",
        )
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
