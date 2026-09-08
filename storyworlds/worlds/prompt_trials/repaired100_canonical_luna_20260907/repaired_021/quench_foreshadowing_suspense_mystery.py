#!/usr/bin/env python3
"""
A small mystery story world about quenching a hidden lantern before nightfall.

The story uses foreshadowing and suspense: small clues appear before the danger
is clear, then the characters must reason together and act before a dry wind
turns a lantern spark into a fire.
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
ROOT = HERE
while ROOT != os.path.dirname(ROOT) and not os.path.exists(os.path.join(ROOT, "results.py")):
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    phrase: str = ""
    location: str = ""
    held_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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


@dataclass
class StoryParams:
    detective: str
    helper: str
    setting: str = "the old clock garden"
    clue: str = "a trail of damp blue footprints"
    seed: Optional[int] = None


NAMES = ["Luna", "Milo", "Pip", "Nora", "Cleo", "Toby", "Ivy", "Jasper"]
SETTINGS = ["the old clock garden", "the moonlit ferry yard", "the quiet museum courtyard"]
CLUES = [
    "a trail of damp blue footprints",
    "three silver drops beneath the gate",
    "a scorched feather beside the fountain",
    "a line of soot on the stone wall",
]

@dataclass(frozen=True)
class Case:
    title: str
    opening: str
    clue_meaning: str
    second_clue: str
    danger: str
    question: str
    solution: str
    ending: str


CASES = (
    Case(
        "the blue footprints",
        "At dusk, the garden bell rang once even though nobody had touched it.",
        "The footprints were too wet to belong to a bird, yet they ended beside the locked lantern shed.",
        "A cold breeze carried the smell of ash from behind the shed.",
        "Inside, a small oil lantern still burned beneath a pile of dry leaves.",
        '"Why would wet tracks lead to a burning lantern?"',
        "Luna followed the marks to a rain barrel, while the helper found a loose roof tile. They filled a pail and poured it over the hidden flame.",
        "The blue footprints belonged to a gardener who had tried to carry water in the dark; the quenched lantern left only a curl of harmless steam.",
    ),
    Case(
        "the silver drops",
        "A tiny silver key appeared on the fountain rim before the evening lights came on.",
        "The drops formed a careful path toward a cabinet that no one remembered opening.",
        "Behind the cabinet came a faint ticking sound, like a match burning very slowly.",
        "A cracked candle inside the cabinet leaned toward a curtain in the dry wind.",
        '"If the ticking is a warning, what is it warning us about?"',
        "Luna pulled the curtain clear while the helper fetched fountain water. Together they tipped the water onto the candle and quenched the hidden flame.",
        "The key had fallen from the caretaker's ring, and the ticking was a loose clock spring; both clues had pointed toward the neglected candle.",
    ),
    Case(
        "the scorched feather",
        "A black feather floated down just as the last child left the courtyard.",
        "Its warm edge showed that it had passed close to a flame, but no lamp stood nearby.",
        "A thin ribbon of smoke curled from the old ticket booth.",
        "A forgotten stove ember glowed beneath a basket of paper tickets.",
        '"Can a little ember make a big mystery?"',
        "Luna moved the paper basket away while the helper carried water from the fountain. Their quick teamwork quenched the ember before it caught.",
        "The feather had drifted from a rooftop nest, and the ember explained its singed edge and the secret smoke.",
    ),
    Case(
        "the soot line",
        "A clean white moth landed on a wall marked by one fresh line of soot.",
        "The line ran from the storage room to a stack of folded festival cloth.",
        "Under the cloth, something clicked and then went silent.",
        "A covered lantern had tipped against the fabric, and its wick still glowed red.",
        '"Why would the room go quiet when we came near?"',
        "Luna lifted the cloth with a stick while the helper opened the window and brought water. They quenched the glowing wick safely.",
        "The clicking had been a loose lantern handle, and the soot line showed exactly where the danger had traveled.",
    ),
)


OPENINGS = (
    "Luna, a careful young detective, met {helper} in {setting} just before night.",
    "In {setting}, Luna was checking the shadows when {helper} noticed something strange.",
    "The first star had appeared above {setting} when Luna opened a fresh mystery notebook.",
)

REALIZATIONS = (
    "Luna remembered that clues do not merely tell what happened; they can point toward what is about to happen.",
    "The strange signs now formed a warning, not a puzzle to admire from a safe distance.",
    "Luna understood that the quietest clue might be the most urgent one.",
)

THANKS = (
    '"You noticed the first clue," Luna said. "Thank you for helping me follow it."',
    '"Your question kept us from guessing," Luna said. "Thank you for thinking carefully."',
    '"We solved this together," Luna said. "Thank you for acting before the danger grew."',
)


def choose_case(params: StoryParams) -> tuple[Case, str, str, str]:
    seed = params.seed or 0
    case = CASES[seed % len(CASES)]
    opening = OPENINGS[(seed // len(CASES)) % len(OPENINGS)]
    realization = REALIZATIONS[(seed // (len(CASES) * len(OPENINGS))) % len(REALIZATIONS)]
    thanks = THANKS[(seed // (len(CASES) * len(OPENINGS) * len(REALIZATIONS))) % len(THANKS)]
    return case, opening, realization, thanks


def build_world(params: StoryParams) -> World:
    if params.detective == params.helper:
        raise StoryError("detective and helper must have different names")
    if params.setting not in SETTINGS:
        raise StoryError(f"unknown setting: {params.setting}")
    if params.clue not in CLUES:
        raise StoryError(f"unknown clue: {params.clue}")

    world = World()
    detective = world.add(Entity(
        id=params.detective, kind="character", type="detective",
        label="detective", traits=["curious", "careful"],
        meters={"calm": 1.0, "time": 1.0},
        memes={"curiosity": 1.0, "courage": 1.0},
    ))
    helper = world.add(Entity(
        id=params.helper, kind="character", type="helper",
        label="helper", traits=["observant", "brave"],
        meters={"calm": 1.0, "time": 1.0},
        memes={"attention": 1.0, "trust": 1.0},
    ))
    lantern = world.add(Entity(
        id="lantern", kind="thing", type="lantern",
        label="lantern", phrase="a small oil lantern",
        location="hidden room", meters={"flame": 0.8, "danger": 0.7},
    ))
    water = world.add(Entity(
        id="water", kind="thing", type="water",
        label="water", phrase="a pail of water",
        location="rain barrel", meters={"amount": 1.0},
    ))

    case, opening, realization, thanks = choose_case(params)
    values = {
        "detective": detective.id,
        "helper": helper.id,
        "setting": params.setting,
        "clue": params.clue,
    }

    world.say(opening.format(**values))
    world.say(f"{detective.id} carried a notebook, and {helper.id} carried a small brass cup for collecting clues.")
    world.para()
    world.say(case.opening)
    world.say(f"Near the path, they found {params.clue}.")
    world.say(case.clue_meaning)
    world.say(case.second_clue)
    detective.memes["suspense"] = 1.0
    helper.memes["worry"] = 1.0
    world.say(case.question)
    world.para()
    world.say(realization)
    world.say(case.danger)
    lantern.meters["danger"] = 1.0
    world.say(f'"We must quench it before the dry wind reaches it," {detective.id} said.')
    world.say(f'"I will find water, and you watch the flame," {helper.id} replied.')
    world.say(case.solution)
    lantern.meters["flame"] = 0.0
    lantern.meters["danger"] = 0.0
    water.meters["amount"] = 0.0
    detective.memes["courage"] += 1.0
    helper.memes["trust"] += 1.0
    world.say(thanks)
    world.para()
    world.say(case.ending)
    world.say("The mystery was solved, but Luna kept the first clues in her notebook, because a small warning can protect a whole night.")

    world.facts.update(
        detective=detective,
        helper=helper,
        lantern=lantern,
        water=water,
        case=case,
        setting=params.setting,
        clue=params.clue,
        danger=case.danger,
        solution=case.solution,
        ending=case.ending,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective: Entity = f["detective"]  # type: ignore[assignment]
    helper: Entity = f["helper"]  # type: ignore[assignment]
    return [
        f"Write a child-friendly mystery about {detective.id} and {helper.id} following clues before they must quench a hidden flame.",
        f"Create a suspenseful story set in {f['setting']} with foreshadowing, a lantern, water, and a safe ending.",
        f"Tell a gentle mystery in which the clue '{f['clue']}' helps two friends prevent danger.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective: Entity = f["detective"]  # type: ignore[assignment]
    helper: Entity = f["helper"]  # type: ignore[assignment]
    case: Case = f["case"]  # type: ignore[assignment]
    return [
        QAItem(
            question="Who investigated the mystery?",
            answer=f"{detective.id} investigated the mystery with help from {helper.id}.",
        ),
        QAItem(
            question="What early clue foreshadowed the danger?",
            answer=f"The early clue was {f['clue']}. It led the friends toward the hidden trouble before they could see the flame.",
        ),
        QAItem(
            question="Why did the mystery become suspenseful?",
            answer=f"It became suspenseful because {case.danger} The friends had to act before the danger grew.",
        ),
        QAItem(
            question="How did the friends quench the danger?",
            answer=f"{case.solution}",
        ),
        QAItem(
            question="What final image shows that the mystery was solved?",
            answer=f"{case.ending} The flame was gone and the place was safe.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does quench mean?",
            answer="To quench something means to put out a fire or satisfy a strong thirst, often with water.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is an early hint that prepares us for something important that will happen later.",
        ),
        QAItem(
            question="What is suspense?",
            answer="Suspense is the feeling of wondering what will happen next while an important outcome is still uncertain.",
        ),
    ]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Mystery story world about quenching hidden danger.")
    parser.add_argument("--detective", choices=NAMES)
    parser.add_argument("--helper", choices=NAMES)
    parser.add_argument("--setting", choices=SETTINGS)
    parser.add_argument("--clue", choices=CLUES)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    detective = args.detective or rng.choice(NAMES)
    choices = [name for name in NAMES if name != detective]
    helper = args.helper or rng.choice(choices)
    return StoryParams(
        detective=detective,
        helper=helper,
        setting=args.setting or rng.choice(SETTINGS),
        clue=args.clue or rng.choice(CLUES),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id:10} ({entity.type:9}) "
            f"location={entity.location or '-'} meters={entity.meters} memes={entity.memes}"
        )
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.extend(["", "== story qa =="])
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


ASP_RULES = r"""
character(X) :- detective(X).
character(X) :- helper(X).
dangerous(L) :- lantern(L), flame(L), not quenched(L).
safe(L) :- lantern(L), quenched(L).
solved(D,H,L) :- detective(D), helper(H), lantern(L), safe(L).
#show solved/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for name in NAMES:
        lines.append(asp.fact("detective", name))
        lines.append(asp.fact("helper", name))
    lines.append(asp.fact("lantern", "lantern"))
    lines.append(asp.fact("flame", "lantern"))
    lines.append(asp.fact("quenched", "lantern"))
    return "\n".join(lines)


def asp_program(show: str = "#show solved/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    models = asp.solve(asp_program(), models=1)
    if not models:
        print("ASP verification failed: no model.")
        return 1
    solved = asp.atoms(models[0], "solved")
    if not solved:
        print("ASP verification failed: no solved case.")
        return 1
    for seed in range(8):
        params = StoryParams(
            detective=NAMES[seed % len(NAMES)],
            helper=NAMES[(seed + 1) % len(NAMES)],
            setting=SETTINGS[seed % len(SETTINGS)],
            clue=CLUES[seed % len(CLUES)],
            seed=seed,
        )
        sample = generate(params)
        if "quench" not in sample.story.lower():
            print("Python verification failed: generated story omitted quench.")
            return 1
        if sample.world is None or sample.world.entities["lantern"].meters["flame"] != 0.0:
            print("Python verification failed: lantern remains lit.")
            return 1
    print("OK: ASP/Python mystery parity verified.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.n < 1:
        raise StoryError("-n must be at least 1")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, case in enumerate(CASES):
            samples.append(generate(StoryParams(
                detective=NAMES[index % len(NAMES)],
                helper=NAMES[(index + 1) % len(NAMES)],
                setting=SETTINGS[index % len(SETTINGS)],
                clue=CLUES[index % len(CLUES)],
                seed=base_seed + index,
            )))
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(100, args.n * 30):
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
