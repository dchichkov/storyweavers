#!/usr/bin/env python3
"""
A standalone storyworld about a mother, a green clue, and a teamwork mystery.

A young helper and Mother investigate why a garden plant has stopped making
bright leaves. The mystery turns on chlorophyll: they situate the plant,
share observations, and transform its care together.
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
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(HERE)))))
sys.path.insert(0, os.path.join(ROOT, "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Garden:
    name: str
    light: str
    shelter: str


@dataclass
class Character:
    name: str
    kind: str
    role: str
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Plant:
    name: str = "the bean plant"
    leaf_color: str = "pale green"
    chlorophyll: float = 0.25
    moisture: float = 0.0
    light: float = 0.0
    health: float = 0.0
    transformed: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    child_name: str
    child_kind: str
    garden: str
    plant: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class MysteryCase:
    clue: str
    observation: str
    wrong_guess: str
    hidden_cause: str
    teamwork: str
    transformation: str
    ending: str
    object: str


GARDENS = {
    "windowsill": Garden("the sunny windowsill", "morning light", "a blue curtain"),
    "courtyard": Garden("the quiet courtyard", "soft afternoon light", "a brick wall"),
    "greenhouse": Garden("the little greenhouse", "filtered glass light", "a wooden bench"),
}

PLANTS = {
    "bean": "bean plant",
    "mint": "mint plant",
    "fern": "fern",
}

KINDS = ["mouse", "rabbit", "fox", "badger", "sparrow"]
NAMES = {
    "mouse": ["Luna", "Pip", "Nell"],
    "rabbit": ["Luna", "Tavi", "Mara"],
    "fox": ["Luna", "Fenn", "Cora"],
    "badger": ["Luna", "Bram", "Moss"],
    "sparrow": ["Luna", "Wren", "Iris"],
}

CASES = [
    MysteryCase(
        clue="one leaf had a bright green edge while its middle stayed pale",
        observation="a folded curtain covered the plant for most of the morning",
        wrong_guess="the plant was thirsty",
        hidden_cause="the curtain was stealing the light that chlorophyll needed",
        teamwork="Mother held the curtain aside while the child marked the sunlit spot",
        transformation="the plant was moved where a golden patch of light reached every leaf",
        ending="new green leaves opened like tiny flags beside the window",
        object="a brass sun marker",
    ),
    MysteryCase(
        clue="a dusty fingerprint crossed three leaves, but no leaf was torn",
        observation="the pot sat behind a tall watering can",
        wrong_guess="a beetle had eaten the green from the leaves",
        hidden_cause="the watering can blocked the light from one side",
        teamwork="Mother lifted the can while the child followed the shadow around the pot",
        transformation="the pot was situated on a low stand where light could circle it",
        ending="the leaves turned toward the open space and shone greener each day",
        object="a little wooden stand",
    ),
    MysteryCase(
        clue="a pale crescent appeared on the leaf nearest the wall",
        observation="the plant's brightest leaf faced the courtyard gate",
        wrong_guess="the crescent was a bite mark",
        hidden_cause="the plant was turning toward light and could not receive enough of it",
        teamwork="Mother watched the sun's path while the child situated the pot beside the gate",
        transformation="the plant was rotated gently each morning so all leaves shared the light",
        ending="a ring of healthy green leaves framed the stem",
        object="a smooth clay compass",
    ),
    MysteryCase(
        clue="the lowest leaves were pale, while the leaves above them were green",
        observation="a thick layer of fallen petals covered the soil and lower stem",
        wrong_guess="the roots had forgotten how to drink",
        hidden_cause="the petals trapped dampness and shaded the lower leaves",
        teamwork="Mother gathered the petals while the child checked the soil with one careful finger",
        transformation="the soil was cleared and the pot was given a bright, airy place",
        ending="the lowest leaves lifted toward the light instead of drooping",
        object="a woven garden scoop",
    ),
]

LESSONS = [
    "Mother always said that a mystery becomes smaller when two careful people share their clues.",
    "The old garden rule was simple: situate the living thing before deciding what it needs.",
    "Mother taught that teamwork is not two people doing the same job; it is two people noticing more together.",
    "A plant cannot explain its trouble with words, so its colors and shadows become its clues.",
]

OPENINGS = [
    "The garden was quiet except for bees humming beyond the glass.",
    "Morning light slid across the garden and touched every pot but one.",
    "In the little garden, each leaf seemed to keep a secret.",
    "The day began with a silver watering can and a puzzling patch of pale green.",
]


class World:
    def __init__(self, garden: Garden) -> None:
        self.garden = garden
        self.mother: Optional[Character] = None
        self.child: Optional[Character] = None
        self.plant = Plant()
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.plant.meters = {"light": 0.0, "health": 0.0, "chlorophyll": 0.25}
        self.plant.memes = {"mystery": 1.0, "hope": 0.0, "trust": 0.0}

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def mystery_present(world: World) -> bool:
    return world.plant.chlorophyll < 0.5 or world.plant.leaf_color != "green"


def inspect_clue(world: World) -> None:
    if "inspect" in world.fired:
        return
    world.fired.add("inspect")
    case: MysteryCase = world.facts["case"]
    world.say(
        f"Together they examined the plant. {case.clue.capitalize()}. "
        f"{case.observation.capitalize()}."
    )
    world.say(
        f'"Could it be that {case.wrong_guess}?" {world.child.name} asked. '
        f'"Let us situate the clues before we decide," Mother replied.'
    )
    world.child.memes["curiosity"] = 1.0
    world.plant.memes["mystery"] = 1.0


def share_clues(world: World) -> None:
    if "share" in world.fired:
        return
    if "inspect" not in world.fired:
        raise StoryError("The clues must be inspected before the team can share them.")
    world.fired.add("share")
    case: MysteryCase = world.facts["case"]
    world.say(
        f"Mother pointed to the shadows, and {world.child.name} pointed to the pale leaf. "
        f"{case.teamwork}. The two clues fit together."
    )
    world.mother.memes["teamwork"] = 1.0
    world.child.memes["teamwork"] = 1.0
    world.plant.memes["hope"] = 0.5


def transform_care(world: World) -> None:
    if "transform" in world.fired:
        return
    if "share" not in world.fired:
        raise StoryError("The plant cannot be transformed before the clues are shared.")
    world.fired.add("transform")
    case: MysteryCase = world.facts["case"]
    world.say(f"Then they worked side by side. {case.transformation}.")
    world.plant.light = 1.0
    world.plant.moisture = 0.7
    world.plant.chlorophyll = 1.0
    world.plant.health = 1.0
    world.plant.leaf_color = "green"
    world.plant.transformed = True
    world.plant.meters.update(light=1.0, health=1.0, chlorophyll=1.0)
    world.plant.memes.update(mystery=0.0, hope=1.0, trust=1.0)


def conclude(world: World) -> None:
    if "conclude" in world.fired:
        return
    world.fired.add("conclude")
    case: MysteryCase = world.facts["case"]
    if not world.plant.transformed:
        raise StoryError("A complete mystery story needs a transformed resolution.")
    world.say(
        f"The mystery was solved without a single frightened guess. {case.ending}. "
        f"Mother smiled, and {world.child.name} placed {case.object} beside the pot "
        f"to remember where the best light fell."
    )
    world.say(world.facts["lesson"])


def build_world(params: StoryParams) -> World:
    if params.garden not in GARDENS:
        raise StoryError(f"Unknown garden: {params.garden}")
    if params.plant not in PLANTS:
        raise StoryError(f"Unknown plant: {params.plant}")
    if params.child_kind not in KINDS:
        raise StoryError(f"Unknown child kind: {params.child_kind}")
    garden = GARDENS[params.garden]
    world = World(garden)
    world.child = Character(params.child_name, params.child_kind, "young investigator")
    world.mother = Character("Mother", "human", "garden guide")
    world.plant.name = f"the {PLANTS[params.plant]}"
    choice = params.seed
    if choice is None:
        key = f"{params.child_name}|{params.child_kind}|{params.garden}|{params.plant}"
        choice = sum((i + 1) * ord(c) for i, c in enumerate(key))
    world.facts["case"] = CASES[choice % len(CASES)]
    world.facts["opening"] = OPENINGS[(choice // len(CASES)) % len(OPENINGS)]
    world.facts["lesson"] = LESSONS[(choice * 3) % len(LESSONS)]
    world.facts["location"] = garden.name
    return world


def tell_story(world: World) -> None:
    child = world.child
    case: MysteryCase = world.facts["case"]
    world.say(
        f"{world.facts['opening']} In {world.garden.name}, {world.facts['location']} lived "
        f"{child.name}, a curious little {child.kind}, with Mother."
    )
    world.say(
        f"They cared for {world.plant.name}, but its leaves were {world.plant.leaf_color}. "
        "Something about the plant had changed, and no one knew why."
    )
    world.para()
    world.say(
        f"One morning, {child.name} called, 'Mother, come look! The green has gone missing.' "
        f"Mother answered, 'Then we will solve the mystery together.'"
    )
    if mystery_present(world):
        inspect_clue(world)
        share_clues(world)
        transform_care(world)
    world.para()
    conclude(world)
    world.facts.update(
        child=child,
        mother=world.mother,
        plant=world.plant,
        clue=case.clue,
        cause=case.hidden_cause,
        teamwork=case.teamwork,
        transformation=case.transformation,
        ending=case.ending,
        object=case.object,
        resolved=True,
    )


def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a child-friendly mystery about {world.child.name}, Mother, and chlorophyll in {world.garden.name}.",
        f"Tell a teamwork story in which the family must situate {world.plant.name} to solve a green-leaf mystery.",
        "Write a transformation fable where shared clues change how a plant is cared for.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    plant = f["plant"]
    return [
        QAItem(
            question=f"What mystery did {child.name} and Mother investigate?",
            answer=(
                f"They investigated why {plant.name} had pale leaves. The important clue was that "
                f"{f['clue']}, which showed that the plant was not receiving the conditions needed for healthy chlorophyll."
            ),
        ),
        QAItem(
            question="How did Mother and the child use teamwork?",
            answer=(
                f"Mother and the child shared different clues and worked side by side: {f['teamwork']}. "
                "Their observations helped them choose a careful solution instead of guessing."
            ),
        ),
        QAItem(
            question="What caused the plant's pale color?",
            answer=(
                f"The hidden cause was that {f['cause']}. Because chlorophyll helps leaves look green, "
                "the lack of suitable light made the plant's color fade."
            ),
        ),
        QAItem(
            question="What transformation proved that their solution worked?",
            answer=(
                f"They changed the plant's situation: {f['transformation']}. "
                f"Afterward, {f['ending']}."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is chlorophyll?",
            answer="Chlorophyll is the green substance in many plant cells that helps plants use light to make food.",
        ),
        QAItem(
            question="Why can a plant need light?",
            answer="A plant needs light to power photosynthesis, the process by which it makes food for growth.",
        ),
        QAItem(
            question="What does situate mean?",
            answer="To situate something means to place it in a particular position or setting.",
        ),
        QAItem(
            question="Why is teamwork useful in a mystery?",
            answer="Teamwork lets people compare different observations, so they can notice more clues and make a wiser decision.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
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
    return "\n".join(
        [
            "--- world model state ---",
            f"garden={world.garden.name}",
            f"child={world.child.name} ({world.child.kind})",
            f"plant={world.plant.name}",
            f"leaf_color={world.plant.leaf_color}",
            f"chlorophyll={world.plant.chlorophyll}",
            f"plant.meters={world.plant.meters}",
            f"plant.memes={world.plant.memes}",
            f"fired={sorted(world.fired)}",
        ]
    )


ASP_RULES = r"""
garden(G) :- garden_name(G).
kind(K) :- kind_name(K).
plant(P) :- plant_name(P).
valid(G,K,P) :- garden(G), kind(K), plant(P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for value in GARDENS:
        lines.append(asp.fact("garden_name", value))
    for value in KINDS:
        lines.append(asp.fact("kind_name", value))
    for value in PLANTS:
        lines.append(asp.fact("plant_name", value))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    return [(g, k, p) for g in GARDENS for k in KINDS for p in PLANTS]


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    model = asp.one_model(asp_program())
    cl = set(asp.atoms(model, "valid"))
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        for params in CURATED:
            sample = generate(params)
            if "chlorophyll" not in sample.story.lower() or not sample.world.plant.transformed:
                print("Generated-story verification failed.")
                return 1
        print("OK: generated stories resolve the transformation.")
        return 0
    print("MISMATCH between Python and ASP.")
    print("only in python:", sorted(py - cl))
    print("only in ASP:", sorted(cl - py))
    return 1


@dataclass
class _Args:
    garden: Optional[str] = None
    plant: Optional[str] = None
    kind: Optional[str] = None
    name: Optional[str] = None
    n: int = 1
    seed: Optional[int] = None
    all: bool = False
    trace: bool = False
    qa: bool = False
    json: bool = False
    asp: bool = False
    verify: bool = False
    show_asp: bool = False


CURATED = [
    StoryParams("Luna", "mouse", "windowsill", "bean"),
    StoryParams("Luna", "rabbit", "courtyard", "mint"),
    StoryParams("Luna", "sparrow", "greenhouse", "fern"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mystery storyworld about Mother, chlorophyll, teamwork, and transformation.")
    ap.add_argument("--garden", choices=GARDENS)
    ap.add_argument("--plant", choices=PLANTS)
    ap.add_argument("--kind", choices=KINDS)
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    kind = args.kind or rng.choice(KINDS)
    return StoryParams(
        child_name=args.name or rng.choice(NAMES[kind]),
        child_kind=kind,
        garden=args.garden or rng.choice(list(GARDENS)),
        plant=args.plant or rng.choice(list(PLANTS)),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
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
        for garden, kind, plant in valid_combos():
            print(f"{garden:12} {kind:10} {plant}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        seen = set()
        for i in range(max(args.n, 1) * 100):
            if len(samples) >= args.n:
                break
            seed = base_seed + i
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.child_name}: {sample.params.plant} mystery"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
