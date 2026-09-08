#!/usr/bin/env python3
"""
A small fable world about morning flooring, an inner worry, and a conflict
solved by patient cooperation.
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


ASP_RULES = r"""
morning_scene(floor).
has_crack(floor).
sees_warning(luna).
wants_haste(luna).
speaks_up(luna).
gets_help(luna).
repairs(floor).
shares_work(luna).
safe_floor(floor) :- has_crack(floor), sees_warning(luna), speaks_up(luna), gets_help(luna), repairs(floor).
wise_choice(luna) :- sees_warning(luna), speaks_up(luna), repairs(floor).
kind_ending(luna) :- safe_floor(floor), shares_work(luna).
"""

NAMES = ["Luna", "Milo", "Tessa", "Pip", "Nora", "Bram"]
HELPERS = ["Grandmother Fern", "Uncle Rowan", "Mira the Mouse", "Old Badger"]
PLACES = ["the little cottage", "the bakery kitchen", "the schoolhouse", "the warm barn"]
MATERIALS = ["oak boards", "smooth pine planks", "bright clay tiles", "flat river stones"]
TREATS = ["honey cakes", "warm porridge", "apple bread", "berry buns"]


@dataclass(frozen=True)
class Trial:
    name: str
    opening: str
    danger: str
    wish: str
    clue: str
    conflict: str
    action: str
    result: str
    lesson: str
    ending: str


TRIALS = [
    Trial(
        "the loose morning board",
        "Morning light slipped beneath the door of a small cottage.",
        "one board in the new flooring had lifted at its corner",
        "to sweep quickly and pretend the floor was finished",
        "a thin line of dust gathered beside the raised edge",
        "Luna's helper wanted to hurry before breakfast grew cold",
        "showed the loose board, moved the broom aside, and asked for a mallet",
        "the board was fastened firmly before anyone stumbled",
        "A quiet worry can be a useful warning when it is spoken aloud.",
        "The repaired flooring shone in the sun, and every step sounded steady.",
    ),
    Trial(
        "the slippery tiles",
        "At morning's first bell, the bakery smelled of warm bread.",
        "freshly washed tiles made a bright, slippery path near the oven",
        "to carry the bread across before the family arrived",
        "a bead of water rolled all the way to the flour bin",
        "the baker insisted that one careful dash would be enough",
        "placed a cloth runner over the tiles and carried the baskets together",
        "the bread reached the table without a fall",
        "Haste may boast loudly, but care knows the safer road.",
        "The clean flooring held a trail of floury footprints beside the golden loaves.",
    ),
    Trial(
        "the uneven schoolhouse floor",
        "The morning sun painted squares across the schoolhouse floor.",
        "two old planks rose higher than the others",
        "to cover the bump with a rug until lessons were over",
        "a small marble rolled toward the raised boards",
        "the caretaker said the children could simply walk around it",
        "marked the spot, fetched proper tools, and repaired the planks before class",
        "the children entered safely and the marble rolled straight",
        "A hidden trouble grows smaller when honest eyes agree to meet it.",
        "The rug was folded away, revealing smooth flooring ready for many learning feet.",
    ),
    Trial(
        "the barn doorway",
        "Morning dew glittered across the barn doorway.",
        "a damp patch had softened the wooden flooring",
        "to lead the goats through before the sun rose higher",
        "one hoofprint sank deeply into the wet wood",
        "the farmer feared that stopping would delay the market cart",
        "closed the doorway, spread dry straw, and replaced the weak boards",
        "the goats crossed safely after the flooring dried",
        "A pause taken for safety is not a failure to work.",
        "The goats trotted over strong boards while the market cart waited peacefully outside.",
    ),
]


@dataclass
class Character:
    id: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str
    time: str = "morning"


@dataclass
class World:
    setting: Setting
    hero: Character
    helper: Character
    material: str
    treat: str
    trial: Trial
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    name: str
    helper: str
    place: str
    material: str
    treat: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A morning flooring fable.")
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--material", choices=MATERIALS)
    parser.add_argument("--treat", choices=TREATS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("morning_scene", "floor"),
            asp.fact("has_crack", "floor"),
            asp.fact("sees_warning", "luna"),
            asp.fact("wants_haste", "luna"),
            asp.fact("speaks_up", "luna"),
            asp.fact("gets_help", "luna"),
            asp.fact("repairs", "floor"),
            asp.fact("shares_work", "luna"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show safe_floor/1.\n#show kind_ending/1."))
    found = set(asp.atoms(model, "safe_floor")) | set(asp.atoms(model, "kind_ending"))
    expected = {("floor",), ("luna",)}
    if found == expected:
        print("OK: ASP parity verified.")
        return 0
    print(f"MISMATCH: found {found}, expected {expected}")
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        name=args.name or rng.choice(NAMES),
        helper=args.helper or rng.choice(HELPERS),
        place=args.place or rng.choice(PLACES),
        material=args.material or rng.choice(MATERIALS),
        treat=args.treat or rng.choice(TREATS),
    )


def make_world(params: StoryParams) -> World:
    if params.name == params.helper:
        raise StoryError("The child and helper must have different names.")
    hero = Character(
        id=params.name,
        role="watchful child",
        meters={"attention": 0.9, "courage": 0.7, "haste": 0.4},
        memes={"worry": 0.5, "trust": 0.4},
    )
    helper = Character(
        id=params.helper,
        role="helper",
        meters={"strength": 0.8, "patience": 0.7},
        memes={"care": 0.8},
    )
    key = params.seed if params.seed is not None else sum(ord(c) for c in "|".join(vars(params).values() if False else [params.name, params.helper, params.place]))
    trial = TRIALS[key % len(TRIALS)]
    return World(
        setting=Setting(place=params.place),
        hero=hero,
        helper=helper,
        material=params.material,
        treat=params.treat,
        trial=trial,
    )


def tell(world: World) -> None:
    h, helper, trial = world.hero, world.helper, world.trial
    world.say(f"{trial.opening} In {world.setting.place}, {h.id} helped prepare the flooring with {world.material}.")
    world.say(
        f"{h.id} noticed that {trial.danger}. "
        f"Inside, a worried thought whispered, 'Perhaps I should say nothing and finish quickly.'"
    )
    world.para()
    world.say(
        f"But another thought answered, 'A small warning can prevent a large hurt.' "
        f'{h.id} said, "{trial.clue}"'
    )
    world.say(f'"We have no time to fuss," said {helper.id}. "{trial.conflict.capitalize()}."')
    world.say(f'"We have time to keep everyone safe," replied {h.id}. "Please look once more."')
    world.para()
    world.say(f"Together, they {trial.action}. Then {trial.result}.")
    world.say(
        f"When the work was done, they shared {world.treat} on the sound floor. "
        f"{h.id} felt the worry grow quiet because a truthful voice had changed the plan."
    )
    world.para()
    world.say(f"The little fable taught this: {trial.lesson} {trial.ending}")
    world.facts.update(
        danger=trial.danger,
        clue=trial.clue,
        action=trial.action,
        result=trial.result,
        conflict=trial.conflict,
        lesson=trial.lesson,
        ending=trial.ending,
    )


def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a child-facing fable about {world.hero.id}, a morning flooring danger, an inner monologue, and a conflict with {world.helper.id}.",
        f"Tell how the clue '{world.trial.clue}' changes the plan in {world.setting.place}.",
        f"End with a concrete image proving that the flooring became safe.",
    ]


def story_qa(world: World) -> list[QAItem]:
    h, helper, t = world.hero, world.helper, world.trial
    return [
        QAItem(
            f"What did {h.id} notice in the morning?",
            f"{h.id} noticed that {t.danger}. The clue was that {t.clue}.",
        ),
        QAItem(
            f"What did {h.id}'s inner monologue tell them to do?",
            f"The first worried thought told {h.id} to {t.wish}, but a wiser thought urged them to speak up.",
        ),
        QAItem(
            f"What conflict happened between {h.id} and {helper.id}?",
            f"{helper.id} wanted to hurry because {t.conflict}, while {h.id} argued for a safe inspection.",
        ),
        QAItem(
            "How was the flooring problem solved?",
            f"Together, they {t.action}. As a result, {t.result}.",
        ),
        QAItem(
            "What proved the ending was safe?",
            f"{t.ending} This showed that the repaired flooring could be used without fear.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "Why is flooring important?",
            "Flooring gives people a firm surface for walking, working, and sharing a room safely.",
        ),
        QAItem(
            "Why can an inner monologue help a character?",
            "An inner monologue lets readers hear a character's private worry and see how the character chooses between haste and care.",
        ),
        QAItem(
            "What makes a conflict useful in a fable?",
            "A conflict is useful when different choices create a problem that the characters resolve through evidence, conversation, and wise action.",
        ),
    ]


def dump_trace(world: World) -> str:
    return "\n".join(
        [
            "--- world model state ---",
            f"place={world.setting.place}",
            f"time={world.setting.time}",
            f"hero={world.hero.id} role={world.hero.role}",
            f"hero_meters={world.hero.meters}",
            f"hero_memes={world.hero.memes}",
            f"helper={world.helper.id} role={world.helper.role}",
            f"material={world.material}",
            f"treat={world.treat}",
            f"trial={world.trial.name}",
            f"danger={world.trial.danger}",
            f"clue={world.trial.clue}",
            f"result={world.trial.result}",
        ]
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    tell(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def curated() -> list[StoryParams]:
    return [
        StoryParams("Luna", "Grandmother Fern", "the little cottage", "oak boards", "honey cakes"),
        StoryParams("Milo", "Uncle Rowan", "the bakery kitchen", "smooth pine planks", "warm porridge"),
        StoryParams("Tessa", "Mira the Mouse", "the schoolhouse", "bright clay tiles", "apple bread"),
        StoryParams("Pip", "Old Badger", "the warm barn", "flat river stones", "berry buns"),
    ]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show safe_floor/1.\n#show kind_ending/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(
            asp_program(
                "#show morning_scene/1.\n#show safe_floor/1.\n#show wise_choice/1.\n#show kind_ending/1."
            )
        )
        print("\n".join(str(atom) for atom in model))
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1.")

    samples: list[StorySample]
    if args.all:
        samples = [generate(p) for p in curated()]
    else:
        base = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        for index in range(args.n):
            rng = random.Random(base + index)
            params = resolve_params(args, rng)
            params.seed = base + index
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
