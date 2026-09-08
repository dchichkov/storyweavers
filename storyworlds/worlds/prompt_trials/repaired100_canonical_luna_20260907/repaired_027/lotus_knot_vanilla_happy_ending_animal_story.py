#!/usr/bin/env python3
"""
A gentle animal story about a lotus, a knot, and vanilla, with a happy ending.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

for _parent in Path(__file__).resolve().parents:
    if (_parent / "storyworlds" / "results.py").is_file():
        sys.path.insert(0, str(_parent / "storyworlds"))
        break

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ("safe", "tangled", "dry", "shared"):
            self.meters.setdefault(key, 0.0)
        for key in ("curiosity", "worry", "kindness", "relief", "trust"):
            self.memes.setdefault(key, 0.0)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    animal: str = "Luna"
    friend: str = "Pip"
    lotus: str = "pink lotus"
    knot: str = "garden knot"
    vanilla: str = "vanilla flower"
    setting: str = "a quiet pond garden"
    feature: str = "Happy Ending"
    style: str = "Animal Story"


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def get(self, key: str) -> Entity:
        return self.entities[key]

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


NAMES = ["Luna", "Mimi", "Clover", "Nell", "Poppy", "Tilly"]
FRIENDS = ["Pip", "Bram", "Niko", "Moss", "Wren", "Bibi"]
LOTUSES = ["pink lotus", "white lotus", "blue lotus", "golden lotus"]
KNOTS = ["garden knot", "vine knot", "ribbon knot", "reed knot"]
VANILLAS = ["vanilla flower", "vanilla pod", "vanilla blossom"]


@dataclass(frozen=True)
class Arc:
    problem: str
    warning: str
    mistake: str
    consequence: str
    clue: str
    repair: str
    result: str
    lesson: str
    ending: str


ARCS = [
    Arc(
        problem="A warm breeze had tugged a little basket toward the pond's deepest water.",
        warning="Please loosen the knot slowly, because a rushed tug may pull the lotus with it",
        mistake="pulled hard on the knot to make the basket move quickly",
        consequence="The knot tightened around a lotus stem, and the flower bent low over the water.",
        clue="one pale root still held the stem beneath the mud",
        repair="held the basket steady while Pip loosened the knot one loop at a time",
        result="the lotus lifted upright without losing a single petal",
        lesson="Gentle patience can mend what hurried strength might break.",
        ending="By sunset, the lotus opened beside the rescued basket, and its vanilla-sweet smell floated across the pond.",
    ),
    Arc(
        problem="The animals were preparing a tiny picnic beside a pond full of blooming lotuses.",
        warning="Keep the vanilla bowl away from the loose vine knot",
        mistake="tossed the vine knot playfully beside the picnic cloth",
        consequence="The knot caught the bowl, and vanilla cream began sliding toward the pond.",
        clue="a broad lotus leaf floated like a green little tray",
        repair="guided the bowl onto the lotus leaf while Pip untied the vine",
        result="the vanilla cream reached the picnic table instead of the water",
        lesson="A playful idea is only good when it keeps other things safe.",
        ending="Everyone shared vanilla treats beneath the lotus leaves, laughing at the clean, dry cloth.",
    ),
    Arc(
        problem="A young duckling had found a bright knot caught beneath a lotus leaf.",
        warning="Ask for help before reaching into deep water",
        mistake="stretched across the pond alone to grab the knot",
        consequence="One paw slipped, and the duckling splashed into the cool water.",
        clue="the lotus leaf made a safe bridge close to the shore",
        repair="called to Pip and followed the lotus leaf back to shallow water",
        result="the duckling climbed out while the friends freed the knot with a reed",
        lesson="Calling for help is a brave way to protect both friends and self.",
        ending="The duckling dried beside a vanilla-scented flower while the freed knot became a toy on shore.",
    ),
    Arc(
        problem="The garden keeper had placed a vanilla flower near the pond for the bees.",
        warning="Do not drag the knot across the soft flower bed",
        mistake="dragged the knot over the flowers while pretending it was a treasure rope",
        consequence="The knot caught a stem, and the vanilla flower tipped toward the mud.",
        clue="a lotus leaf held a cool drop of water beside the bent stem",
        repair="used the water drop to freshen the flower while Pip lifted the knot away",
        result="the vanilla flower stood straight before the bees arrived",
        lesson="When a game causes harm, stopping to care is more important than winning.",
        ending="The bees hummed around the vanilla flower, and Luna placed the knot safely in a basket.",
    ),
    Arc(
        problem="Rain had filled the pond, and a lotus seed pod rested beside a tangled knot.",
        warning="Watch your step near the slippery bank",
        mistake="raced along the bank without looking at the wet stones",
        consequence="A quick slide sent the knot rolling toward the lotus seed pod.",
        clue="a sturdy root made a dry path around the puddle",
        repair="followed the root path and stopped the knot with a vanilla-scented cloth",
        result="the seed pod remained safe, ready to grow another lotus",
        lesson="Looking carefully helps a small animal make a large difference.",
        ending="New lotus seeds slept safely in the mud, while the friends walked home beneath the rain.",
    ),
]


def make_world(params: StoryParams) -> World:
    world = World(params)
    animal = world.add(Entity("animal", "character", "small_animal", params.animal))
    friend = world.add(Entity("friend", "character", "friend", params.friend))
    lotus = world.add(Entity("lotus", "plant", "lotus", params.lotus))
    knot = world.add(Entity("knot", "object", "knot", params.knot))
    vanilla = world.add(Entity("vanilla", "plant", "vanilla", params.vanilla))

    animal.memes["curiosity"] = 1.0
    animal.memes["kindness"] = 1.0
    friend.memes["trust"] = 1.0
    lotus.meters["safe"] = 1.0
    vanilla.meters["safe"] = 1.0
    knot.meters["tangled"] = 1.0
    return world


def tell(params: StoryParams) -> World:
    world = make_world(params)
    animal = world.get("animal")
    friend = world.get("friend")
    lotus = world.get("lotus")
    knot = world.get("knot")
    vanilla = world.get("vanilla")

    value = params.seed if params.seed is not None else sum(
        ord(ch) for ch in "|".join(
            (params.animal, params.friend, params.lotus, params.knot, params.vanilla)
        )
    )
    arc = ARCS[value % len(ARCS)]
    order = (value // len(ARCS)) % 3

    world.say(
        f"In {params.setting}, {animal.label} the little animal lived beside a pond "
        f"where a {lotus.label} opened each morning."
    )
    world.say(
        f"{friend.label} often visited with a {vanilla.label}, and together they kept "
        f"a bright {knot.label} for small garden jobs."
    )
    world.para()
    world.say(arc.problem)
    world.say(f"{friend.label} called, \"{arc.warning}.\"")
    world.say(f"\"I will be careful,\" {animal.label} promised, although curiosity made the knot look exciting.")

    animal.memes["curiosity"] += 1.0
    animal.memes["worry"] += 1.0
    knot.meters["tangled"] += 1.0

    if order == 0:
        world.say(f"But {animal.label} {arc.mistake}.")
        world.say(arc.consequence)
    elif order == 1:
        world.say(f"The warning was sensible, but {animal.label} {arc.mistake}.")
        world.say(f"That was when {arc.consequence.lower()}")
    else:
        world.say(f"{animal.label} wanted to help quickly and {arc.mistake}.")
        world.say(f"At once, everyone saw the trouble: {arc.consequence}")

    world.para()
    world.say(f"{animal.label} felt worried, but did not hide the mistake.")
    world.say(f"\"I need your help,\" {animal.label} said. \"What should we notice first?\"")
    world.say(f"{friend.label} answered, \"Look closely. {arc.clue.capitalize()}.\"")
    world.say(f"Together, the friends chose to {arc.repair}.")

    animal.memes["worry"] = 0.0
    animal.memes["kindness"] += 1.0
    animal.memes["relief"] += 1.0
    friend.memes["trust"] += 1.0
    lotus.meters["safe"] = 1.0
    knot.meters["tangled"] = 0.0
    vanilla.meters["safe"] = 1.0

    world.say(f"The careful work mattered: {arc.result}.")
    world.say(f"{friend.label} smiled. \"You told the truth and stayed to help.\"")
    world.say(f"{animal.label} smiled back. \"Friends can untie trouble together.\"")

    world.para()
    world.say(f"{animal.label} learned that {arc.lesson}")
    world.say(arc.ending)

    world.facts.update(
        animal=animal,
        friend=friend,
        lotus=lotus,
        knot=knot,
        vanilla=vanilla,
        arc=arc,
        params=params,
        resolved=True,
    )
    return world


def story_qa(world: World) -> list[QAItem]:
    params = world.facts["params"]
    animal = world.facts["animal"]
    friend = world.facts["friend"]
    arc = world.facts["arc"]
    lotus = world.facts["lotus"]
    knot = world.facts["knot"]
    vanilla = world.facts["vanilla"]

    return [
        QAItem(
            question=f"Who is the animal story about in {params.setting}?",
            answer=f"It is about {animal.label}, a little animal who lives near a pond with a {lotus.label}.",
        ),
        QAItem(
            question=f"What warning did {friend.label} give about the {knot.label}?",
            answer=f"{friend.label} warned that {arc.warning}. The warning was meant to protect the {lotus.label} and the nearby garden.",
        ),
        QAItem(
            question=f"What went wrong with the {knot.label}?",
            answer=f"{animal.label} {arc.mistake}, and then {arc.consequence}",
        ),
        QAItem(
            question=f"What clue helped {animal.label} repair the trouble?",
            answer=f"{friend.label} pointed out that {arc.clue}. That clue showed the friends a safer way to act.",
        ),
        QAItem(
            question=f"How did the friends use kindness to solve the problem?",
            answer=f"They {arc.repair}. Because they worked gently together, {arc.result}.",
        ),
        QAItem(
            question=f"What happened to the {vanilla.label} at the happy ending?",
            answer=f"The {vanilla.label} remained safe, and its sweet smell joined the rescued {lotus.label} at the peaceful ending.",
        ),
        QAItem(
            question="What lesson did the animal learn?",
            answer=f"{arc.lesson} The animal also learned that telling the truth gives friends a chance to help.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a lotus?",
            answer="A lotus is a water-loving plant with broad leaves and a beautiful flower that can grow in a pond.",
        ),
        QAItem(
            question="What is a knot?",
            answer="A knot is a place where string, rope, vine, or ribbon is looped and tightened.",
        ),
        QAItem(
            question="What is vanilla?",
            answer="Vanilla is a sweet-smelling flavor and spice that comes from the fruit of a flowering plant.",
        ),
        QAItem(
            question="Why is it helpful to ask a friend for help?",
            answer="Asking a friend for help can make a difficult or unsafe problem easier to solve carefully.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    params = world.facts["params"]
    arc = world.facts["arc"]
    return [
        f"Write an Animal Story about {params.animal}, a {params.lotus}, a {params.knot}, and a {params.vanilla}.",
        f"Tell a gentle story in {params.setting} where {params.animal} learns to {arc.lesson.lower()}",
        f"Create a {params.feature.lower()} animal tale in which friends repair trouble near a lotus pond.",
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        lines.append(
            f"  {entity.id:8} ({entity.type:12}) "
            f"meters={meters} memes={memes}"
        )
    lines.append(f"  resolved: {world.facts.get('resolved', False)}")
    return "\n".join(lines)


ASP_RULES = r"""
% The animal begins with a knot and a warning.
has_item(animal, knot).
warned(animal).

% A careful repair produces a safe happy ending.
asks_for_help(animal).
works_together(animal, friend).
safe(lotus).
safe(vanilla).
untangled(knot).

happy_ending(animal) :-
    warned(animal),
    asks_for_help(animal),
    works_together(animal, friend),
    safe(lotus),
    safe(vanilla),
    untangled(knot).

#show happy_ending/1.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("has_item", "animal", "knot"),
            asp.fact("warned", "animal"),
            asp.fact("asks_for_help", "animal"),
            asp.fact("works_together", "animal", "friend"),
            asp.fact("safe", "lotus"),
            asp.fact("safe", "vanilla"),
            asp.fact("untangled", "knot"),
        ]
    )


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    found = {"happy_ending/1" if sym.name == "happy_ending" else "" for sym in model}
    if "happy_ending/1" in found:
        print("OK: ASP twin confirms the happy ending.")
        return 0
    print("MISMATCH: ASP twin did not derive happy_ending(animal).")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A gentle animal story about a lotus, a knot, and vanilla."
    )
    parser.add_argument("--animal", choices=NAMES)
    parser.add_argument("--friend", choices=FRIENDS)
    parser.add_argument("--lotus", choices=LOTUSES)
    parser.add_argument("--knot", choices=KNOTS)
    parser.add_argument("--vanilla", choices=VANILLAS)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        seed=args.seed,
        animal=args.animal or rng.choice(NAMES),
        friend=args.friend or rng.choice(FRIENDS),
        lotus=args.lotus or rng.choice(LOTUSES),
        knot=args.knot or rng.choice(KNOTS),
        vanilla=args.vanilla or rng.choice(VANILLAS),
    )


def generate(params: StoryParams) -> StorySample:
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


CURATED = [
    StoryParams(
        animal="Luna",
        friend="Pip",
        lotus="pink lotus",
        knot="garden knot",
        vanilla="vanilla flower",
    ),
    StoryParams(
        animal="Clover",
        friend="Wren",
        lotus="white lotus",
        knot="vine knot",
        vanilla="vanilla pod",
    ),
    StoryParams(
        animal="Mimi",
        friend="Bram",
        lotus="blue lotus",
        knot="reed knot",
        vanilla="vanilla blossom",
    ),
]


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
        print(" ".join(str(symbol) for symbol in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(50, args.n * 50):
            seed = base_seed + index
            index += 1
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
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
