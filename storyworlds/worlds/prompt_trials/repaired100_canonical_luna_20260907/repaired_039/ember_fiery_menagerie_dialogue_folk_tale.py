#!/usr/bin/env python3
"""A child-friendly folk tale about an ember, a fiery menagerie, and brave dialogue."""

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

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Person:
    name: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Creature:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    hero: str = "Luna"
    keeper: str = "Toma"
    place: str = "the hilltop menagerie"
    ember: str = "the moon-red ember"
    creature: str = "the little fire fox"


@dataclass
class World:
    params: StoryParams
    people: dict[str, Person] = field(default_factory=dict)
    creatures: dict[str, Creature] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


NAMES = ["Luna", "Mira", "Niko", "Sela", "Pip", "Oren"]
KEEPERS = ["Toma", "Baba", "Anya", "Grandmother Iva", "Uncle Ro"]
PLACES = [
    "the hilltop menagerie",
    "the lantern valley menagerie",
    "the old forest menagerie",
    "the village menagerie",
]
CREATURES = [
    ("the little fire fox", "fox"),
    ("the brass-winged bird", "bird"),
    ("the warm-footed bear", "bear"),
    ("the candle-antlered deer", "deer"),
]
EMBERS = [
    "the moon-red ember",
    "the sleeping ember",
    "the golden ember",
    "the last bright ember",
]


def make_world(params: StoryParams) -> World:
    world = World(params=params)
    hero = Person(params.hero, "young keeper")
    keeper = Person(params.keeper, "old keeper")
    creature = Creature(params.creature, params.creature.split()[-1])
    world.people = {hero.name: hero, keeper.name: keeper}
    world.creatures = {creature.name: creature}
    world.facts.update(
        ember=params.ember,
        place=params.place,
        creature=params.creature,
        cause="the ember had rolled beneath the creature's straw nest",
        danger="the nest began to smoke while the fiery animals grew frightened",
        clue="the smallest flame leaned toward the stone water bowl",
        method="Luna spoke calmly, then used the bowl to guide the ember onto bare earth",
        resolution="the ember cooled safely and the animals settled",
        lesson="a calm voice can make room for a wise deed",
        ending="the menagerie glowed softly beneath the evening stars",
        resolved=False,
    )
    return world


def generate_story_world(params: StoryParams) -> World:
    world = make_world(params)
    p = params
    rng = random.Random(p.seed if p.seed is not None else 0)
    f = world.facts

    world.say(
        f"Long ago, {p.hero} watched over {p.place}, where every creature carried a little warmth in its heart."
    )
    world.say(
        f"One evening, {p.hero} found {p.ember} glowing beside {p.creature}, while the fiery menagerie blinked in the dusk."
    )
    world.say(
        f'"Keep your paws still," {p.hero} told {p.creature}. "I will learn what this ember wants."'
    )
    world.para()

    world.say(f"{f['danger'].capitalize()}.")
    world.say(
        f'"The flames are dancing too high," cried {p.keeper}. "Do not rush, Luna!"'
        if p.hero == "Luna"
        else f'"The flames are dancing too high," cried {p.keeper}. "Do not rush, {p.hero}!"'
    )
    world.say(
        f'"If I shout, the animals will scatter," {p.hero} answered. "I will listen first."'
    )
    world.say(f"Then {p.hero} noticed a clue: {f['clue']}.")
    world.para()

    world.say(
        f"{p.keeper} held the gate open. {p.hero} crouched low and spoke to the frightened animals."
    )
    world.say(
        f'"Little fox, step left. Brass-winged bird, stay on your perch. Bear, breathe slowly," said {p.hero}.'
    )
    world.say(
        f"The creatures listened because {p.hero}'s words were gentle and clear."
    )
    world.say(f"{p.hero} {f['method']}.")
    world.say(
        rng.choice(
            [
                "The old keeper carried a wet cloth, but Luna needed only the right path and a steady hand.",
                "No creature was chased, and no one grabbed at the shining coal.",
                "The menagerie grew quiet enough for everyone to hear the ember's faint hiss.",
            ]
        )
    )
    world.para()

    world.say(
        f"The ember dimmed. {f['resolution'].capitalize()}, and the fiery animals pressed close to one another."
    )
    world.say(
        f'"You saved us by speaking before acting," said {p.keeper}.'
    )
    world.say(
        f'"Your question saved us," {p.hero} replied. "You reminded me to notice the clue."'
    )
    world.say(f"The old keeper smiled. \"{f['lesson'].capitalize()}.\"")
    world.say(f"That night, {f['ending']}.")
    world.say(
        f"{p.creature.capitalize()} curled beside the cool ember, and {p.hero} knew that courage could sound like a kind voice."
    )

    hero = world.people[p.hero]
    keeper = world.people[p.keeper]
    creature = world.creatures[p.creature]
    hero.meters.update(calm=1.0, danger=0.0)
    hero.memes.update(courage=1.0, listening=1.0)
    keeper.memes.update(guidance=1.0, trust=1.0)
    creature.meters.update(warmth=0.7, safety=1.0)
    creature.memes.update(trust=1.0)
    f["resolved"] = True
    f["dialogue_changed_action"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.params
    return [
        f"Write a folk tale about {p.hero}, {p.ember}, and a fiery menagerie.",
        f"Use dialogue to show how {p.hero} safely helps {p.creature} in {p.place}.",
        "Tell a gentle story in which listening reveals the right way to solve a danger.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p, f = world.params, world.facts
    return [
        QAItem(
            "What danger came to the menagerie?",
            f"{f['danger'].capitalize()}. The smoke and frightened animals made the menagerie unsafe.",
        ),
        QAItem(
            "What clue did the hero notice?",
            f"{f['clue'].capitalize()}. It showed the safest direction for moving the ember.",
        ),
        QAItem(
            "How did dialogue change what the hero did?",
            f'{p.keeper} warned, "Do not rush," and {p.hero} answered that they would listen first. That exchange helped {p.hero} stay calm, notice the clue, and guide the ember instead of chasing the animals.',
        ),
        QAItem(
            "How was the ember made safe?",
            f"{f['method'].capitalize()}. The ember cooled on bare earth without hurting a creature.",
        ),
        QAItem(
            "What lesson did the folk tale teach?",
            f"The tale taught that {f['lesson']}. Calm words can help people notice a wise action.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is an ember?",
            "An ember is a small, still-glowing piece of wood or coal left after a fire. It can remain hot even when there are no tall flames.",
        ),
        QAItem(
            "Why should people move carefully near fire?",
            "Fire can spread quickly and burn people, animals, or homes. People should stay calm, keep a safe distance, and ask a responsible helper for aid.",
        ),
        QAItem(
            "Why is dialogue useful during a problem?",
            "Dialogue lets people share warnings, clues, and plans. Clear words can change a hurried action into a safer one.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"{i}. {x}" for i, x in enumerate(sample.prompts, 1))
    lines.append("\n== Story QA ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("\n== World QA ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def validate(params: StoryParams) -> None:
    if params.hero == params.keeper:
        raise StoryError("hero and keeper must be different characters")
    if not params.hero.strip() or not params.keeper.strip():
        raise StoryError("character names must not be empty")
    if params.creature not in dict(CREATURES):
        raise StoryError("creature must come from the menagerie registry")


ASP_RULES = r"""
hero(H) :- hero_name(H).
keeper(K) :- keeper_name(K).
ember(E) :- ember_name(E).
creature(C) :- creature_name(C).
dialogue_guides(H, K, E) :- hero(H), keeper(K), ember(E), warned(K), listens(H).
safe_menagerie(H, E, C) :- dialogue_guides(H, _, E), creature(C), guided(H, E), cooled(E).
folk_tale(H, E, C) :- safe_menagerie(H, E, C).
#show folk_tale/3.
"""


def asp_facts(params: StoryParams | None = None) -> str:
    import asp

    p = params or StoryParams()
    return "\n".join(
        [
            asp.fact("hero_name", p.hero),
            asp.fact("keeper_name", p.keeper),
            asp.fact("ember_name", p.ember),
            asp.fact("creature_name", p.creature),
            asp.fact("warned", p.keeper),
            asp.fact("listens", p.hero),
            asp.fact("guided", p.hero, p.ember),
            asp.fact("cooled", p.ember),
        ]
    )


def asp_program(params: StoryParams | None = None) -> str:
    return f"{asp_facts(params)}\n{ASP_RULES}"


def asp_verify() -> int:
    import asp

    p = StoryParams()
    validate(p)
    atoms = asp.atoms(asp.one_model(asp_program(p)), "folk_tale")
    sample = generate(p)
    good = bool(atoms) and sample.world.facts["resolved"] and sample.world.facts["dialogue_changed_action"]
    print("OK: ASP and Python agree on the dialogue-led fiery menagerie tale." if good else "MISMATCH: ASP/Python parity failed.")
    return 0 if good else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hero", choices=NAMES)
    parser.add_argument("--keeper", choices=KEEPERS)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--ember", choices=EMBERS)
    parser.add_argument("--creature", choices=[x[0] for x in CREATURES])
    parser.add_argument("--seed", type=int)
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
        hero=args.hero or rng.choice(NAMES),
        keeper=args.keeper or rng.choice(KEEPERS),
        place=args.place or rng.choice(PLACES),
        ember=args.ember or rng.choice(EMBERS),
        creature=args.creature or rng.choice([x[0] for x in CREATURES]),
    )


def generate(params: StoryParams) -> StorySample:
    validate(params)
    world = generate_story_world(params)
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
    if trace and sample.world:
        f = sample.world.facts
        print(
            "\n--- trace ---\n"
            f"ember={f['ember']}\n"
            f"danger={f['danger']}\n"
            f"clue={f['clue']}\n"
            f"resolved={f['resolved']}"
        )
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
        import asp

        atoms = asp.atoms(asp.one_model(asp_program()), "folk_tale")
        print("1 compatible folk tale." if atoms else "0 compatible folk tales.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    count = len(NAMES) if args.all else args.n
    for i in range(count):
        seed = base_seed + i
        params = resolve_params(args, random.Random(seed))
        params.seed = seed
        samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {i + 1}" if len(samples) > 1 else "",
        )
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
