#!/usr/bin/env python3
"""
A small heartwarming storyworld about a frightened child, a spoonful of caviar,
and a flashback that turns fear into courage.
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
from collections import defaultdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))


@dataclass
class Place:
    id: str
    label: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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


@dataclass(frozen=True)
class Arc:
    key: str
    opening: tuple[str, str]
    fear: tuple[str, str]
    flashback: tuple[str, str]
    courage: tuple[str, str]
    ending: tuple[str, str]
    danger: str
    method: str
    result: str


ARCS = (
    Arc(
        "dark_kitchen",
        (
            "In the old kitchen, Lina helped her grandmother set out tiny bowls for supper.",
            "One bowl held glossy black caviar that glittered like wet stars.",
        ),
        (
            "Then the pantry door slammed in the wind, and the sudden bang seemed to terrify Lina.",
            '"I cannot go near that door," she whispered. "What if the dark is waiting?"',
        ),
        (
            "Lina remembered a winter night when she had been afraid of thunder.",
            'Grandmother had held her hand and said, "Fear can knock loudly, but courage can answer softly."',
        ),
        (
            '"Will you stand beside me?" Lina asked. "Every step," said Grandmother.',
            "Together they opened the door, found only a loose broom, and tied it safely back in place.",
        ),
        (
            "Lina returned to the table and placed one brave spoonful of caviar on Grandmother's plate.",
            "The black pearls shone beside the warm bread, and the kitchen felt bright enough for both of them.",
        ),
        "a banging pantry door",
        "remembering a trusted hand and checking the sound with a helper",
        "Lina learned that a frightening noise can have a small, ordinary cause",
    ),
    Arc(
        "harbor_storm",
        (
            "At the harbor café, Milo carried a tray while Aunt Rosa prepared a celebration supper.",
            "A little dish of caviar sat beneath a glass cover, waiting for the guests.",
        ),
        (
            "A rope snapped against the pier with a crack that seemed to terrify Milo.",
            '"The boats are in trouble," he cried. "I heard a terrible roar!"',
        ),
        (
            "He remembered his first boat ride, when Aunt Rosa had shown him how to watch the calm space between waves.",
            '"Look closely," she had told him then. "A big sound does not always mean a big danger."',
        ),
        (
            '"Can we look together?" Milo asked. "Yes, and we will keep one hand on the rail," said Aunt Rosa.',
            "They checked the pier and discovered that the rope had only struck an empty barrel.",
        ),
        (
            "Milo carried the caviar to the table with careful steps and a proud smile.",
            "Outside, the boats rocked gently, while inside, everyone shared supper and stories.",
        ),
        "a rope cracking against the pier",
        "using a remembered safety lesson and inspecting the sound together",
        "Milo discovered that careful looking can shrink a frightening mystery",
    ),
    Arc(
        "attic_shadow",
        (
            "Nora visited the sunny houseboat with her grandfather and helped polish the supper table.",
            "A crystal dish of caviar waited in the middle like a bowl of tiny moons.",
        ),
        (
            "A tall shadow crossed the attic wall, and it seemed to terrify Nora.",
            '"The shadow is moving!" she said. "Please do not leave me alone."',
        ),
        (
            "She remembered a summer afternoon when Grandfather had taught her to make shadow animals with a lamp.",
            '"Shadows borrow their shapes," he had said. "We can find what they borrowed."',
        ),
        (
            '"Let us find the shape together," Nora said. "A fine plan," Grandfather replied.',
            "They climbed the steps, opened the little window, and found a coat swinging from a hook.",
        ),
        (
            "Nora laughed and carried a spoonful of caviar back downstairs for Grandfather.",
            "The coat stopped swinging, and the attic shadow became just a coat again.",
        ),
        "a coat moving in a draft",
        "recalling a lesson about shadows and tracing the shape to its source",
        "Nora changed a scary shadow into a familiar coat",
    ),
    Arc(
        "garden_gate",
        (
            "In the garden, Sami helped his mother prepare a picnic beneath the apple tree.",
            "They packed bread, berries, and a small jar of caviar for a special treat.",
        ),
        (
            "The garden gate creaked open by itself, and the long squeak seemed to terrify Sami.",
            '"Something is coming in," he said. "I do not like that sound."',
        ),
        (
            "He remembered a rainy morning when his mother had taught him to listen for the difference between wind and footsteps.",
            '"Listen twice," she had said. "Then choose what the sound tells you."',
        ),
        (
            '"Will you listen with me?" Sami asked. "Of course," said his mother.',
            "They listened again and saw a vine pulling the gate in the breeze, so they tied the vine to a post.",
        ),
        (
            "Sami set the caviar beside the picnic bread and watched the gate rest quietly.",
            "The apple leaves whispered overhead, and his brave heart felt peaceful under the tree.",
        ),
        "a gate pulled by a vine",
        "listening twice with a trusted helper",
        "Sami found a gentle cause and made the gate safe",
    ),
)


@dataclass
class StoryParams:
    place: str
    child_name: str
    helper_name: str
    child_gender: str = "child"
    helper_gender: str = "adult"
    seed: Optional[int] = None
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))


PLACES = {
    "kitchen": Place("kitchen", "the old kitchen", {"home", "warm"}),
    "harbor": Place("harbor", "the harbor café", {"water", "busy"}),
    "houseboat": Place("houseboat", "the sunny houseboat", {"water", "home"}),
    "garden": Place("garden", "the garden", {"green", "home"}),
}

CHILDREN = ["Lina", "Milo", "Nora", "Sami"]
HELPERS = ["Grandmother", "Aunt Rosa", "Grandfather", "Mother"]

CURATED = [
    StoryParams("kitchen", "Lina", "Grandmother"),
    StoryParams("harbor", "Milo", "Aunt Rosa"),
    StoryParams("houseboat", "Nora", "Grandfather"),
    StoryParams("garden", "Sami", "Mother"),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A heartwarming flashback story about fear and caviar.")
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--child")
    parser.add_argument("--helper")
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
    child = args.child or rng.choice(CHILDREN)
    helper = args.helper or rng.choice([name for name in HELPERS if name != child])
    return StoryParams(place, child, helper, seed=args.seed)


def tell(params: StoryParams) -> World:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}.")
    if not params.child_name.strip() or not params.helper_name.strip():
        raise StoryError("Both the child and helper need names.")
    if params.child_name == params.helper_name:
        raise StoryError("The child and helper must have different names.")

    rng = random.Random(params.seed if params.seed is not None else sum(map(ord, params.child_name + params.place)))
    arc = ARCS[rng.randrange(len(ARCS))]
    world = World(PLACES[params.place])
    child = world.add(Entity("child", "character", "child", params.child_name))
    helper = world.add(Entity("helper", "character", "adult", params.helper_name))
    dish = world.add(Entity("caviar", "object", "food", "caviar"))
    threat = world.add(Entity("fright", "event", "sound", arc.danger))

    child.memes["fear"] = 1.0
    child.meters["distance_from_danger"] = 1.0
    dish.meters["present"] = 1.0

    values = {"child": params.child_name, "helper": params.helper_name}
    for line in arc.opening:
        world.say(line.format(**values))
    world.para()

    for line in arc.fear:
        world.say(line.format(**values))
    world.para()

    child.memes["remembered_care"] = 1.0
    world.facts["flashback"] = True
    for line in arc.flashback:
        world.say(line.format(**values))
    world.para()

    child.memes["fear"] = 0.0
    child.memes["courage"] = 1.0
    child.meters["distance_from_danger"] = 0.0
    helper.memes["comfort"] = 1.0
    for line in arc.courage:
        world.say(line.format(**values))
    world.para()

    dish.meters["shared"] = 1.0
    child.memes["joy"] = 1.0
    for line in arc.ending:
        world.say(line.format(**values))

    world.facts.update(
        child=child,
        helper=helper,
        dish=dish,
        threat=threat,
        arc=arc,
        danger=arc.danger,
        method=arc.method,
        result=arc.result,
        ending=arc.ending[-1].format(**values),
        caviar_shared=True,
        fear_resolved=True,
    )
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    facts = world.facts
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            "Write a heartwarming children's story using the words terrify and caviar.",
            f"Tell a story in {world.place.label} where {params.child_name} faces {facts['danger']} and remembers loving help.",
            "Use a brief Flashback to show how a trusted adult helps a child become brave.",
        ],
        story_qa=[
            QAItem(
                "What seemed to terrify the child?",
                f"{params.child_name} was frightened by {facts['danger']}.",
            ),
            QAItem(
                "How did the child become brave?",
                f"{params.child_name} used a remembered lesson and {facts['method']}. {facts['result'].capitalize()}.",
            ),
            QAItem(
                "What showed that the child felt peaceful at the end?",
                f"The ending showed the change: {facts['ending']}",
            ),
        ],
        world_qa=[
            QAItem(
                "What is caviar?",
                "Caviar is a food made from fish eggs, often served in a small dish.",
            ),
            QAItem(
                "Why can a flashback help a character?",
                "A flashback can show an earlier memory that gives a character useful knowledge, comfort, or courage.",
            ),
        ],
        world=world,
    )


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(f"  {entity.id}: meters={meters} memes={memes}")
    lines.append(f"  flashback_used={world.facts.get('flashback')}")
    lines.append(f"  fear_resolved={world.facts.get('fear_resolved')}")
    return "\n".join(lines)


ASP_RULES = r"""
frightened(child) :- fear(child).
remembered(child) :- flashback(child).
brave(child) :- remembered(child), helper_present(helper).
shared(caviar) :- brave(child).
peaceful(child) :- brave(child), shared(caviar).
#show brave/1.
#show peaceful/1.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("fear", "child"),
            asp.fact("flashback", "child"),
            asp.fact("helper_present", "helper"),
            asp.fact("caviar", "caviar"),
        ]
    )


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(asp.atoms(model, "brave"))


def asp_verify() -> int:
    try:
        import asp
        model = asp.one_model(asp_program())
        brave = asp.atoms(model, "brave")
        peaceful = asp.atoms(model, "peaceful")
        if ("child",) not in brave or ("child",) not in peaceful:
            print("ASP parity check failed.")
            return 1
        sample = generate(StoryParams("kitchen", "Lina", "Grandmother", seed=1))
        if not sample.story.strip() or "caviar" not in sample.story.lower():
            print("Story generation check failed.")
            return 1
    except Exception as exc:
        print(f"Verification failed: {exc}")
        return 1
    print("OK: smoke tests passed.")
    return 0


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
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        for index in range(max(1, args.n)):
            seed = base_seed + index
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
