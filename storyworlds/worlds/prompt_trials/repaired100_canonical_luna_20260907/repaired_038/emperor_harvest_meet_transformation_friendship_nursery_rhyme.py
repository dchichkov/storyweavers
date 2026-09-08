#!/usr/bin/env python3
"""
A tiny nursery-rhyme storyworld about an emperor who meets a harvest helper,
changes through friendship, and learns that sharing makes a full basket sweeter.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass(frozen=True)
class Companion:
    id: str
    name: str
    kind: str
    phrase: str
    gift: str
    rhyme: str


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple[str, ...]] = field(default_factory=set)

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


COMPANIONS = {
    "wren": Companion(
        "wren",
        "Wren",
        "bird",
        "a bright brown wren with a silver bell on one foot",
        "three red apples",
        "Peck and pack, bring plenty back!",
    ),
    "mole": Companion(
        "mole",
        "Moss",
        "mole",
        "a gentle mole with a blue harvest scarf",
        "a basket of golden potatoes",
        "Dig and bring, share everything!",
    ),
    "fox": Companion(
        "fox",
        "Fenn",
        "fox",
        "a small fox with a russet tail and a leaf crown",
        "a bundle of yellow pears",
        "Gather near, friendship is dear!",
    ),
    "bee": Companion(
        "bee",
        "Bibi",
        "bee",
        "a busy bee wearing a poppy-red cap",
        "a jar of wildflower honey",
        "Buzz and cheer, good friends are here!",
    ),
}

NAMES = ["Luna", "Mira", "Nell", "Tavi", "Pip", "Rumi"]
ADJECTIVES = ["grand", "proud", "lonely", "golden", "young", "kind"]
OPENINGS = [
    "On a bright harvest morn",
    "By the barley gate",
    "When the red sun rose",
    "At the turn of autumn",
    "Beneath the moon-pale barn",
    "Before the market bell",
]
REFLECTIONS = [
    "A crown may shine, but a kind friend makes the heart shine brighter.",
    "A harvest grows best when many helping hands make room at the table.",
    "Friendship can transform a proud little heart into a generous one.",
    "The fullest basket is the one that leaves room for another.",
    "A ruler who listens can turn a lonely day into a merry one.",
]
ROLES = ["emperor", "empress", "prince", "princess"]


@dataclass
class StoryParams:
    companion: str
    name: str
    role: str
    adjective: str
    opening: int
    reflection: int
    seed: Optional[int] = None


def _meter(entity: Entity, key: str, value: float) -> None:
    entity.meters[key] = value


def _meme(entity: Entity, key: str, value: float) -> None:
    entity.memes[key] = entity.memes.get(key, 0.0) + value


def tell(params: StoryParams) -> World:
    companion = COMPANIONS[params.companion]
    world = World()
    ruler = world.add(Entity(params.name, "character", f"{params.adjective} {params.role}"))
    friend = world.add(Entity(companion.id, companion.kind, companion.name))
    basket = world.add(Entity("basket", "object", "harvest basket"))
    field = world.add(Entity("field", "place", "pumpkin field"))

    world.facts.update(
        ruler=ruler,
        friend=friend,
        basket=basket,
        field=field,
        companion=companion,
        reflection=REFLECTIONS[params.reflection % len(REFLECTIONS)],
    )

    opening = OPENINGS[params.opening % len(OPENINGS)]
    world.say(
        f"{opening}, {params.name}, an {params.adjective} {params.role}, "
        "stood beside a field where pumpkins, pears, and grain waited for harvest."
    )
    world.say(
        f"The emperor's crown was bright, but the harvest basket was empty. "
        f'"I will gather every sheaf myself," said {params.name}. "Then all will know I am the finest ruler."'
    )
    _meter(ruler, "pride", 1.0)
    _meter(basket, "fullness", 0.0)
    _meter(field, "harvest_ready", 1.0)
    _meme(ruler, "loneliness", 1.0)
    world.para()

    world.say(
        f"Just then, {companion.phrase}, came hopping, digging, padding, or buzzing down the lane."
    )
    world.say(
        f'"Good day! May I help you harvest?" asked {companion.name}. '
        f'"No," said {params.name}. "An emperor needs no help."'
    )
    world.say(
        f'{companion.name} tilted a head and sang, "{companion.rhyme}"'
    )
    world.say(
        f"At that moment, a wind shook the tall grain, and one heavy bundle rolled toward the muddy ditch."
    )
    _meter(field, "risk", 1.0)
    _meme(ruler, "worry", 1.0)
    world.para()

    world.say(
        f'"I cannot lift it alone," admitted {params.name}. '
        f'"Will you help me, {companion.name}?"'
    )
    world.say(
        f'"Gladly," said {companion.name}. "You pull the ribbon, and I will push from the other side."'
    )
    world.say(
        f"Together they tugged. The bundle slid from the mud, and {companion.name} laughed while "
        f"{params.name} laughed too."
    )
    _meter(ruler, "pride", 0.0)
    _meter(ruler, "friendship", 1.0)
    _meter(basket, "fullness", 1.0)
    _meter(field, "risk", 0.0)
    _meme(ruler, "loneliness", -1.0)
    _meme(ruler, "joy", 1.0)
    _meme(friend, "trust", 1.0)
    world.fired.add(("transformation", params.name))
    world.say(
        f"Then a transformation came: the stiff golden crown became a soft wreath of wheat, "
        f"and {params.name}'s proud voice became a warm one."
    )
    world.say(
        f'"A crown is lighter when friends help carry its duties," said {params.name}. '
        f'"Please share the harvest with me."'
    )
    world.para()

    world.say(
        f"So {params.name} and {companion.name} filled the basket with {companion.gift}, "
        "and they carried it to the village table."
    )
    world.say(
        f"They saved the largest piece for the smallest child, the sweetest piece for the oldest neighbor, "
        f"and a bright piece for each other."
    )
    world.say(
        f"The harvest bell rang: ding-ding, sing-sing! "
        f"{companion.name} repeated, "{companion.rhyme}""
    )
    world.say(
        f"From that day on, {params.name} was known not only as an emperor, but as a friend. "
        f"{world.facts['reflection']}"
    )
    world.say(
        f"At sunset, the wheat wreath rested beside the full basket, while {params.name} and "
        f"{companion.name} walked home beneath one wide orange sky."
    )
    world.facts["resolved"] = True
    world.facts["transformed"] = True
    return world


def valid_combos() -> list[str]:
    return sorted(COMPANIONS)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    companion = args.companion or rng.choice(valid_combos())
    if companion not in COMPANIONS:
        raise StoryError(f"Unknown harvest companion: {companion}.")
    return StoryParams(
        companion=companion,
        name=args.name or rng.choice(NAMES),
        role=args.role or rng.choice(ROLES),
        adjective=args.adjective or rng.choice(ADJECTIVES),
        opening=rng.randrange(len(OPENINGS)),
        reflection=rng.randrange(len(REFLECTIONS)),
    )


def generation_prompts(world: World) -> list[str]:
    companion: Companion = world.facts["companion"]
    ruler: Entity = world.facts["ruler"]
    return [
        f"Write a nursery rhyme about an emperor named {ruler.id} who meets {companion.name} during a harvest.",
        f"Tell a friendship story in which {ruler.id} changes from proud to generous.",
        f"Write a child-friendly harvest tale with a magical transformation and a repeated rhyme: {companion.rhyme}",
    ]


def story_qa(world: World) -> list[QAItem]:
    ruler: Entity = world.facts["ruler"]
    companion: Companion = world.facts["companion"]
    return [
        QAItem(
            "Who did the emperor meet in the field?",
            f"{ruler.id} met {companion.name}, {companion.phrase}.",
        ),
        QAItem(
            "Why did the emperor ask for help?",
            f"A heavy harvest bundle rolled toward a muddy ditch, and {ruler.id} could not lift it alone.",
        ),
        QAItem(
            "What transformation happened?",
            f"The emperor's stiff golden crown became a soft wreath of wheat, showing that {ruler.id}'s proud heart had become warmer and more generous.",
        ),
        QAItem(
            "How did friendship change the harvest?",
            f"{ruler.id} and {companion.name} worked together, filled the basket, and shared the harvest with the village.",
        ),
        QAItem(
            "What proved that the emperor had changed?",
            f"{ruler.id} shared the best pieces with neighbors and walked home happily with {companion.name}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a harvest?",
            "A harvest is the gathering of crops, fruit, grain, or other food when they are ready.",
        ),
        QAItem(
            "What is an emperor?",
            "An emperor is a ruler who governs an empire, a large land or group of lands.",
        ),
        QAItem(
            "Why can friendship help people?",
            "Friendship can bring trust, encouragement, shared ideas, and help when a task is difficult.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
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


ASP_RULES = r"""
friendship_story :- emperor(E), meets(E,F), harvest_ready(H), transformed(E).
valid_companion(C) :- companion(C).
harvest_ready(field).
transformed(E) :- changed(E).
"""


def asp_facts() -> str:
    import asp

    lines = []
    for cid, companion in COMPANIONS.items():
        lines.append(asp.fact("companion", cid))
        lines.append(asp.fact("brings", cid, companion.gift))
    lines.append(asp.fact("emperor", "ruler"))
    lines.append(asp.fact("meets", "ruler", "friend"))
    lines.append(asp.fact("changed", "ruler"))
    return "\n".join(lines)


def asp_program(show: str = "#show valid_companion/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_companions() -> list[str]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(str(x[0]) for x in asp.atoms(model, "valid_companion"))


def asp_verify() -> int:
    py = set(valid_combos())
    clingo_values = set(asp_valid_companions())
    if py != clingo_values:
        print("MISMATCH between Python and ASP companion registries.")
        print("Only in Python:", sorted(py - clingo_values))
        print("Only in ASP:", sorted(clingo_values - py))
        return 1
    for companion in valid_combos():
        params = StoryParams(companion, "Luna", "emperor", "kind", 0, 0, 1)
        sample = generate(params)
        if not sample.story or "harvest" not in sample.story.lower():
            print(f"Generated story check failed for {companion}.")
            return 1
    print(f"OK: ASP/Python parity verified for {len(py)} companions and generated stories.")
    return 0


def generate(params: StoryParams) -> StorySample:
    if params.companion not in COMPANIONS:
        raise StoryError(f"Invalid companion: {params.companion}.")
    world = tell(params)
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Nursery-rhyme world of an emperor, a harvest, and friendship."
    )
    parser.add_argument("--companion", choices=sorted(COMPANIONS))
    parser.add_argument("--name")
    parser.add_argument("--role", choices=ROLES)
    parser.add_argument("--adjective", choices=ADJECTIVES)
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


CURATED = [
    StoryParams("wren", "Luna", "emperor", "proud", 0, 0),
    StoryParams("mole", "Mira", "empress", "lonely", 1, 1),
    StoryParams("fox", "Nell", "prince", "grand", 2, 2),
    StoryParams("bee", "Tavi", "princess", "young", 3, 3),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_companion/1."))
        return

    if args.verify:
        raise SystemExit(asp_verify())

    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show valid_companion/1."))
        print(sorted(asp.atoms(model, "valid_companion")))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        for index in range(max(args.n * 20, 20)):
            if len(samples) >= args.n:
                break
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
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
