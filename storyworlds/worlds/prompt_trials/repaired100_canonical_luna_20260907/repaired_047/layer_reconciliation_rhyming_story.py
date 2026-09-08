#!/usr/bin/env python3
"""
A standalone rhyming reconciliation storyworld about a careful layer.
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
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

STORYWORLDS_ROOT = Path(__file__).resolve().parents[2]
if str(STORYWORLDS_ROOT) not in sys.path:
    sys.path.insert(0, str(STORYWORLDS_ROOT))

from results import QAItem, StoryError, StorySample  # noqa: E402


ASP_RULES = r"""
setting(layer_garden).
has_reconciliation(layer_garden).
has_rhyme(layer_garden).
material(moss).
material(petal).
material(clay).
material(stone).
gentle(moss).
gentle(petal).
gentle(clay).
gentle(stone).
repair_plan(layer_garden) :- has_reconciliation(layer_garden), has_rhyme(layer_garden).
good_ending(layer_garden) :- repair_plan(layer_garden).
"""


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def bump_meter(self, key: str, amount: float = 1.0) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + amount

    def bump_meme(self, key: str, amount: float = 1.0) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + amount


@dataclass
class StoryParams:
    name: str
    friend: str
    layer: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Scenario:
    key: str
    opening: str
    trouble: str
    misunderstanding: str
    clue: str
    line_one: str
    line_two: str
    repair: str
    result: str
    lesson: str
    ending: str


@dataclass
class World:
    place: str = "layer garden"
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def get(self, entity_id: str) -> Entity:
        return self.entities[entity_id]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def trace(self) -> str:
        lines = ["--- world model state ---"]
        for entity in self.entities.values():
            bits = [
                f"meters={dict(entity.meters)}",
                f"memes={dict(entity.memes)}",
            ]
            lines.append(
                f"  {entity.id:8} ({entity.kind:10}) {entity.label!r} "
                + " ".join(bits)
            )
        lines.append(f"  facts: {self.facts}")
        return "\n".join(lines)


SCENARIOS = [
    Scenario(
        key="moss_stack",
        opening="Luna layered soft moss by the stream, making a green little dream.",
        trouble="Her friend Pip thought Luna had hidden the blue stones beneath the moss.",
        misunderstanding="Pip pulled the top layer away, and the careful stack began to sway.",
        clue="a blue stone peeked through a gap where two layers met",
        line_one='"I thought you took my stones away," said Pip, feeling gray.',
        line_two='"I saved them underneath, not out of sight," Luna replied, "to keep them dry and bright."',
        repair="lifted each layer together and placed the stones in a shared shining ring",
        result="The moss stayed snug, and every stone could be seen.",
        lesson="a clear word can mend a worry before it grows tall",
        ending="the green layer hugged the blue ring while both friends sang by the spring",
    ),
    Scenario(
        key="petal_roof",
        opening="Luna layered pink petals over a tiny den beside a fern.",
        trouble="Her friend Wren believed Luna had covered the doorway without asking again.",
        misunderstanding="Wren tugged at the petals, and the rosy roof began to bend.",
        clue="the lowest petals left a small door open beneath the fern",
        line_one='"You shut our home," cried Wren, with a fluttering tone.',
        line_two='"I left a door below," said Luna. "Let us look before we groan."',
        repair="curved the petals back, made the opening wider, and invited Wren to choose the last layer",
        result="The den had shade, fresh air, and a doorway both friends liked.",
        lesson="listening together can turn a mistaken fear into a plan",
        ending="the petal roof swayed like a pink boat, with two friends beneath its float",
    ),
    Scenario(
        key="clay_cake",
        opening="Luna layered clay in a round little cake for the festival at noon.",
        trouble="Her friend Moss thought Luna had used all the golden clay and left none to share.",
        misunderstanding="Moss pressed the cake flat, and its careful colors ran together.",
        clue="a golden stripe still rested in the bowl beside the work",
        line_one='"You kept the gold from me," said Moss with a frown.',
        line_two='"I saved half for your star," said Luna. "Please turn it around."',
        repair="reshaped the cake, added the saved gold, and let Moss press a bright star on top",
        result="The cake became a sun with a star that belonged to them both.",
        lesson="sharing what is saved can bring two plans into one",
        ending="their clay sun warmed the table, with a golden star shining fair",
    ),
    Scenario(
        key="stone_path",
        opening="Luna layered flat stones along a path where the tall grasses sway.",
        trouble="Her friend Reed thought Luna had moved the stepping stones away from the creek.",
        misunderstanding="Reed dragged one stone back, and the path made a crooked break.",
        clue="small footprints crossed the stones in a new zigzag line",
        line_one='"Your path is wrong," said Reed, "and now I cannot go."',
        line_two='"I followed the little feet," Luna answered. "Let us test it slow."',
        repair="walked the path together, shifted one stone, and marked the safest turn with a twig",
        result="The path led around the mud and brought both friends safely home.",
        lesson="a different idea may still be a useful way to roam",
        ending="the stone path curved beside the creek, and two sets of footprints met",
    ),
]


NAMES = ["Luna", "Mira", "Tavi", "Nell", "Kiko", "Suri"]
FRIENDS = ["Pip", "Wren", "Moss", "Reed", "Bram", "Iris"]
LAYERS = ["moss", "petal", "clay", "stone"]


def reasonableness_gate(params: StoryParams) -> None:
    if not params.name.strip():
        raise StoryError("The story needs a main character with a name.")
    if not params.friend.strip():
        raise StoryError("The story needs a friend for reconciliation.")
    if params.layer not in LAYERS:
        raise StoryError("The layer must be moss, petal, clay, or stone.")
    if params.name.strip().lower() == params.friend.strip().lower():
        raise StoryError("Reconciliation needs two different friends.")


def valid_params(rng: random.Random) -> StoryParams:
    name = rng.choice(NAMES)
    friend = rng.choice([item for item in FRIENDS if item.lower() != name.lower()])
    return StoryParams(
        name=name,
        friend=friend,
        layer=rng.choice(LAYERS),
        seed=rng.randrange(2**31),
    )


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("setting", "layer_garden"),
            asp.fact("has_reconciliation", "layer_garden"),
            asp.fact("has_rhyme", "layer_garden"),
            *[asp.fact("material", item) for item in LAYERS],
            *[asp.fact("gentle", item) for item in LAYERS],
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Rhyming reconciliation storyworld about layers."
    )
    parser.add_argument("--name")
    parser.add_argument("--friend")
    parser.add_argument("--layer", choices=LAYERS)
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
    params = valid_params(rng)
    if args.name:
        params.name = args.name
    if args.friend:
        params.friend = args.friend
    if args.layer:
        params.layer = args.layer
    reasonableness_gate(params)
    return params


def build_world(params: StoryParams) -> World:
    world = World()
    hero = world.add(Entity("hero", "character", params.name))
    friend = world.add(Entity("friend", "character", params.friend))
    layer = world.add(Entity("layer", "material", params.layer))
    world.facts.update(
        hero=hero,
        friend=friend,
        layer=layer,
        place=world.place,
        reconciliation=True,
        rhyme=True,
    )
    return world


def tell_story(world: World, params: StoryParams) -> None:
    rng = random.Random(params.seed if params.seed is not None else 0)
    scenario = next(
        (item for item in SCENARIOS if item.key.startswith(params.layer)),
        rng.choice(SCENARIOS),
    )
    hero = world.get("hero")
    friend = world.get("friend")
    layer = world.get("layer")

    hero.bump_meme("patience")
    friend.bump_meme("worry")
    layer.bump_meter("layers", 1)

    world.say(scenario.opening.replace("Luna", hero.label))
    world.say(
        f"{hero.label} worked with {layer.label}, layer by layer, "
        f"while {friend.label} watched nearby."
    )
    world.para()

    world.say(scenario.trouble.replace("Luna", hero.label).replace("Pip", friend.label))
    world.say(
        scenario.misunderstanding.replace("Luna", hero.label).replace("Pip", friend.label)
    )
    world.say(f"Then they noticed that {scenario.clue}.")
    world.say(
        scenario.line_one.replace("Pip", friend.label).replace("Luna", hero.label)
    )
    world.say(
        scenario.line_two.replace("Pip", friend.label).replace("Luna", hero.label)
    )
    world.para()

    friend.bump_meme("understanding")
    hero.bump_meme("trust")
    layer.bump_meter("shared_care", 1)
    world.say(
        f"Together, {hero.label} and {friend.label} {scenario.repair}."
    )
    world.say(scenario.result)
    world.say(f"They agreed that {scenario.lesson}.")
    world.para()

    hero.bump_meme("joy")
    friend.bump_meme("joy")
    world.say(
        f"They smiled, for a quarrel can fade when kind words are made. "
        f"{scenario.ending}"
    )

    world.facts.update(
        scenario=scenario.key,
        trouble=scenario.trouble,
        clue=scenario.clue,
        repair=scenario.repair,
        result=scenario.result,
        lesson=scenario.lesson,
        ending=scenario.ending,
        resolved=True,
    )


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"].label
    friend = world.facts["friend"].label
    layer = world.facts["layer"].label
    return [
        f"Write a rhyming story in which {hero} and {friend} reconcile over a {layer} layer.",
        f"Tell a child-friendly reconciliation tale about {hero}, {friend}, and careful layers.",
        "Write a gentle rhyming story where a misunderstanding is repaired through listening.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    hero = facts["hero"].label
    friend = facts["friend"].label
    layer = facts["layer"].label
    return [
        QAItem(
            question=f"What misunderstanding did {friend} have?",
            answer=str(facts["trouble"]),
        ),
        QAItem(
            question=f"What clue helped {hero} and {friend} understand the problem?",
            answer=f"They noticed that {facts['clue']}.",
        ),
        QAItem(
            question=f"How did {hero} and {friend} repair the {layer} work?",
            answer=f"Together, they {facts['repair']}.",
        ),
        QAItem(
            question="What changed after the friends talked and worked together?",
            answer=str(facts["result"]),
        ),
        QAItem(
            question="How did the ending show reconciliation?",
            answer=f"They agreed that {facts['lesson']}, and {facts['ending']}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a layer?",
            answer="A layer is one level or covering placed above or below another level.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means making peace after a disagreement and finding a way to understand each other again.",
        ),
        QAItem(
            question="Why can listening help friends reconcile?",
            answer="Listening helps friends learn what each person meant, so they can replace a misunderstanding with a fair plan.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
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


def asp_verify() -> int:
    import asp

    program = asp_program(
        "#show repair_plan/1.\n#show good_ending/1.\n#show gentle/1."
    )
    model = asp.one_model(program)
    actual = {
        (symbol.name, tuple(
            argument.name if argument.type != 1 else argument.string
            for argument in symbol.arguments
        ))
        for symbol in model
        if symbol.name in {"repair_plan", "good_ending", "gentle"}
    }
    expected = {
        ("repair_plan", ("layer_garden",)),
        ("good_ending", ("layer_garden",)),
        *{("gentle", layer) for layer in LAYERS},
    }
    if actual != expected:
        print("MISMATCH between ASP and Python reconciliation gate.")
        print("ASP:", sorted(actual))
        print("PY :", sorted(expected))
        return 1

    for seed in range(5):
        params = StoryParams("Luna", "Pip", LAYERS[seed % len(LAYERS)], seed=seed)
        sample = generate(params)
        if not sample.story or not sample.story_qa:
            print("MISMATCH: generated story was incomplete.")
            return 1
    print("OK: ASP twin matches the Python gate and generated stories.")
    return 0


def asp_list() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show good_ending/1."))
    return sorted(asp.atoms(model, "good_ending"))


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = build_world(params)
    tell_story(world, params)
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
        print(sample.world.trace())
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams("Luna", "Pip", "moss", seed=11),
    StoryParams("Mira", "Wren", "petal", seed=23),
    StoryParams("Tavi", "Moss", "clay", seed=37),
    StoryParams("Nell", "Reed", "stone", seed=49),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show repair_plan/1.\n#show good_ending/1."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        print("ASP-compatible reconciliation facts:")
        for item in asp_list():
            print(item)
        return

    rng = random.Random(
        args.seed if args.seed is not None else random.randrange(2**31)
    )
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(50, args.n * 50):
            params = resolve_params(
                args, random.Random(rng.randrange(2**31))
            )
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            attempts += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps(
                [sample.to_dict() for sample in samples],
                indent=2,
                ensure_ascii=False,
            ))
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
