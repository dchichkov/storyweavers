#!/usr/bin/env python3
"""
Story world: a small fairy tale about a defective lantern, a warning seen in
advance, and a transformation earned through careful problem solving.
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

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    hero_name: str = "Luna"
    helper_name: str = "Mira"
    village: str = "Moonbell"
    task: str = "guide the lantern parade"
    warning: str = "the blue flame will fail at the old bridge"
    material: str = "moon-silver thread"
    seed: Optional[int] = None


VILLAGES = ["Moonbell", "Thistledown", "Rosemere", "Starling Vale"]
HERO_NAMES = ["Luna", "Elin", "Tessa", "Nell", "Ivy"]
HELPER_NAMES = ["Mira", "Pip", "Orla", "Bram", "Suri"]
TASKS = [
    "guide the lantern parade",
    "light the winter feast",
    "lead the children home through the mist",
    "welcome the returning birds",
]
MATERIALS = ["moon-silver thread", "dragonfly glass", "sun-gold wire", "willow crystal"]

ASP_RULES = r"""
hero(H) :- hero_name(H).
helper(H) :- helper_name(H).
lantern(L) :- lantern_name(L).
defective(L) :- lantern_state(L, defective).
foreseen(P) :- warning(P).
solved(P) :- problem(P), repair(P).
transformed(L) :- lantern_state(L, transformed).
safe(L) :- transformed(L), tested(L).
lesson_learned(H) :- hero(H), learned(H).
"""


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.lines: list[str] = []

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


def asp_facts() -> str:
    import asp

    facts = [
        asp.fact("hero_name", "hero"),
        asp.fact("helper_name", "helper"),
        asp.fact("lantern_name", "lantern"),
        asp.fact("lantern_state", "lantern", "defective"),
        asp.fact("lantern_state", "lantern", "transformed"),
        asp.fact("warning", "flame_failure"),
        asp.fact("problem", "flame_failure"),
        asp.fact("repair", "flame_failure"),
        asp.fact("tested", "lantern"),
        asp.fact("learned", "hero"),
    ]
    return "\n".join(facts)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(
        asp_program(
            "#show defective/1.\n"
            "#show foreseen/1.\n"
            "#show solved/1.\n"
            "#show transformed/1.\n"
            "#show safe/1.\n"
            "#show lesson_learned/1."
        )
    )
    found = {
        (symbol.name, tuple(
            arg.string if arg.type == arg.type.String
            else arg.number if arg.type == arg.type.Number
            else arg.name
            for arg in symbol.arguments
        ))
        for symbol in model
    }
    wanted = {
        ("defective", ("lantern",)),
        ("foreseen", ("flame_failure",)),
        ("solved", ("flame_failure",)),
        ("transformed", ("lantern",)),
        ("safe", ("lantern",)),
        ("lesson_learned", ("hero",)),
    }
    if found == wanted:
        print("OK: ASP and Python parity looks good.")
        return 0
    print("MISMATCH between ASP and Python reasoning.")
    print("ASP:", sorted(found))
    print("PY :", sorted(wanted))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A fairy tale about a defective lantern and a careful transformation."
    )
    parser.add_argument("--name")
    parser.add_argument("--helper")
    parser.add_argument("--village", choices=VILLAGES)
    parser.add_argument("--task")
    parser.add_argument("--material", choices=MATERIALS)
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
    hero = args.name or rng.choice(HERO_NAMES)
    possible_helpers = [name for name in HELPER_NAMES if name != hero]
    helper = args.helper or rng.choice(possible_helpers)
    if hero == helper:
        raise StoryError("The hero and helper must be different characters.")
    return StoryParams(
        hero_name=hero,
        helper_name=helper,
        village=args.village or rng.choice(VILLAGES),
        task=args.task or rng.choice(TASKS),
        material=args.material or rng.choice(MATERIALS),
    )


def generate(params: StoryParams) -> StorySample:
    if params.hero_name == params.helper_name:
        raise StoryError("The hero and helper must be different characters.")
    if params.village not in VILLAGES:
        raise StoryError(f"Unknown village: {params.village}.")
    if params.material not in MATERIALS:
        raise StoryError(f"Unknown material: {params.material}.")

    rng = random.Random(
        params.seed
        if params.seed is not None
        else f"{params.hero_name}:{params.helper_name}:{params.village}:{params.material}"
    )
    world = World()

    hero = world.add(Entity(
        id="hero",
        kind="character",
        label=params.hero_name,
        phrase=f"young {params.hero_name}",
        meters={"courage": 1.0, "doubt": 0.0},
        memes={"hope": 1.0, "wisdom": 0.0},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        label=params.helper_name,
        phrase=f"watchful {params.helper_name}",
        meters={"attention": 1.0},
        memes={"patience": 1.0},
    ))
    lantern = world.add(Entity(
        id="lantern",
        kind="object",
        label="defective lantern",
        phrase=rng.choice([
            "a little lantern with a crooked copper cage",
            "an old lantern whose blue flame trembled in its glass",
            "a bright-looking lantern with a loose silver hinge",
        ]),
        owner="hero",
        meters={"light": 0.5, "stability": 0.2, "defect": 1.0},
        memes={"promise": 1.0, "worry": 1.0},
    ))

    world.say(
        f"In the fairy-tale village of {params.village}, {params.hero_name} was chosen to "
        f"{params.task}."
    )
    world.say(
        f"For the journey, {params.hero_name} carried {lantern.phrase}, a gift that looked "
        "brighter than any ordinary lamp."
    )
    world.say(
        f"At dawn, three blue sparks slipped from the lantern and curled toward the old bridge."
    )
    world.say(
        f"“Why do the sparks fly that way?” {params.hero_name} asked."
    )
    world.say(
        f"“They are showing us something,” {params.helper_name} replied. "
        "“Let us remember the warning before we trust the light.”"
    )
    world.say(
        f"The two friends watched closely and saw the flame shrink whenever the lantern swung."
    )
    world.say(
        f"That foreshadowing mattered, for the lantern was defective: its loose hinge let "
        "wind enter whenever the path grew narrow."
    )

    hero.meters["doubt"] = 1.0
    lantern.meters["defect"] = 1.0
    world.say(
        f"At twilight, the parade reached the old bridge, and the blue flame flickered almost out."
    )
    world.say(
        f"“I can run across and hold it high,” {params.hero_name} said."
    )
    world.say(
        f"“That may make the wind worse,” {params.helper_name} answered. "
        "“What did the sparks tell us?”"
    )
    world.say(
        f"{params.hero_name} remembered the warning: the flame would fail at the bridge."
    )
    world.say(
        f"Instead of rushing, {params.hero_name} placed the lantern on a flat stone while "
        f"{params.helper_name} examined the hinge."
    )
    world.say(
        f"They found a hair-thin crack beside the hinge and noticed that the bridge wind "
        "entered through it."
    )
    world.say(
        f"Together they cleaned the crack, folded a strip of bark around the hinge, and "
        f"fastened it with {params.material}."
    )
    world.say(
        f"Then {params.helper_name} held the lantern still while {params.hero_name} tested "
        "it with three gentle swings."
    )

    lantern.label = "transformed bridge lantern"
    lantern.phrase = "a transformed lantern with a steady blue heart"
    lantern.meters["light"] = 1.0
    lantern.meters["stability"] = 1.0
    lantern.meters["defect"] = 0.0
    lantern.memes["worry"] = 0.0
    lantern.memes["promise"] = 2.0
    hero.meters["doubt"] = 0.0
    hero.memes["wisdom"] = 1.0

    world.say(
        f"The repair transformed the defective lantern into a strong bridge lantern."
    )
    world.say(
        f"Its blue flame held steady even when the evening wind hurried beneath the bridge."
    )
    world.say(
        f"“The warning did not mean we must fear the bridge,” {params.hero_name} said. "
        "“It meant we should prepare.”"
    )
    world.say(
        f"“And the best magic was paying attention,” {params.helper_name} said."
    )
    world.say(
        f"With the transformed lantern lighting every step, the children crossed safely, "
        f"and {params.hero_name} led the parade into {params.village}."
    )
    world.say(
        f"From then on, the villagers called the blue flame the Lantern of Second Chances."
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        lantern=lantern,
        village=params.village,
        warning="the blue flame will fail at the old bridge",
        problem="the loose hinge lets bridge wind enter",
        repair=f"bark and {params.material} seal the hinge",
        transformed=True,
        tested=True,
        lesson="A warning is useful when it leads to careful action.",
    )

    prompts = [
        f"Tell a fairy tale about {params.hero_name} and a defective lantern in {params.village}.",
        f"Include foreshadowing when blue sparks warn about the old bridge, then show problem solving and transformation.",
        f"Write a child-facing tale in which {params.hero_name} learns to study a warning before acting.",
    ]
    story_qa = [
        QAItem(
            question="What was defective about the lantern?",
            answer="A loose hinge let the bridge wind enter, making the blue flame flicker and nearly go out.",
        ),
        QAItem(
            question="What foreshadowed the trouble at the bridge?",
            answer="Three blue sparks curled toward the old bridge, and the flame shrank whenever the lantern swung.",
        ),
        QAItem(
            question="How did the friends solve the problem?",
            answer=f"They cleaned the crack, wrapped bark around the hinge, and fastened it with {params.material}.",
        ),
        QAItem(
            question="How was the lantern transformed?",
            answer="The repair turned the defective lantern into a steady bridge lantern whose blue flame stayed bright in the wind.",
        ),
        QAItem(
            question="What lesson did Luna learn?",
            answer="Luna learned that a warning is useful when it leads to careful action rather than fear or rushing.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a clue early in a story that hints at something important that will happen later.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means observing a difficulty, finding its cause, and choosing a careful way to fix it.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a meaningful change that makes a person or thing different from how it was before.",
        ),
    ]

    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- trace ---")
        for key, entity in sample.world.entities.items():
            print(f"{key}: {entity.label} meters={entity.meters} memes={entity.memes}")
    if qa:
        print("\n== prompts ==")
        for prompt in sample.prompts:
            print(prompt)
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program(
            "#show defective/1.\n"
            "#show foreseen/1.\n"
            "#show solved/1.\n"
            "#show transformed/1.\n"
            "#show safe/1.\n"
            "#show lesson_learned/1."
        ))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        print(asp_program(
            "#show defective/1.\n"
            "#show foreseen/1.\n"
            "#show solved/1.\n"
            "#show transformed/1.\n"
            "#show safe/1.\n"
            "#show lesson_learned/1."
        ))
        for symbol in asp.one_model(asp_program(
            "#show defective/1.\n"
            "#show foreseen/1.\n"
            "#show solved/1.\n"
            "#show transformed/1.\n"
            "#show safe/1.\n"
            "#show lesson_learned/1."
        )):
            print(symbol)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, village in enumerate(VILLAGES):
            params = StoryParams(
                hero_name=HERO_NAMES[index % len(HERO_NAMES)],
                helper_name=HELPER_NAMES[index % len(HELPER_NAMES)],
                village=village,
                task=TASKS[index % len(TASKS)],
                material=MATERIALS[index % len(MATERIALS)],
                seed=base_seed + index,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < max(1, args.n) and index < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + index))
            params.seed = base_seed + index
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            index += 1

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
