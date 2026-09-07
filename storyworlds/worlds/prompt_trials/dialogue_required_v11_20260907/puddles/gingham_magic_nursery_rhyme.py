#!/usr/bin/env python3
"""Gingham, a little magic, and a nursery-rhyme puddle adventure."""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pathlib import Path as _StoryPath
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
sys.path.insert(0, str(_storyworlds_root))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass(frozen=True)
class Setting:
    id: str
    name: str
    detail: str
    affords: set[str]


@dataclass(frozen=True)
class Magic:
    id: str
    name: str
    phrase: str
    effect: str
    cost: str


@dataclass(frozen=True)
class Rhyme:
    id: str
    name: str
    refrain: str
    image: str


SETTINGS = {
    "garden": Setting(
        "garden",
        "the gingham garden",
        "where mint leaves nodded beside a round stone pond",
        {"puddles", "rhyme"},
    ),
    "lane": Setting(
        "lane",
        "the gingham lane",
        "where puddles shone like buttons after rain",
        {"puddles", "rhyme"},
    ),
    "meadow": Setting(
        "meadow",
        "the gingham meadow",
        "where daisies wore bright drops of rain",
        {"puddles", "rhyme"},
    ),
}

MAGICS = {
    "thread": Magic(
        "thread",
        "the silver thread",
        "Stitch and shimmer, stripe and star!",
        "turns one plain puddle into a safe, sparkling stepping path",
        "the child must share the magic aloud",
    ),
    "button": Magic(
        "button",
        "the moon-button",
        "Button bright, make water light!",
        "makes a tiny moon-button glow wherever a puddle is safe",
        "the child must listen before choosing the next step",
    ),
    "ribbon": Magic(
        "ribbon",
        "the blue ribbon",
        "Round and round, keep feet on ground!",
        "ties a ribbon line around the deepest puddle",
        "the child must help a friend cross first",
    ),
}

RHYMES = {
    "rain": Rhyme("rain", "the rain rhyme", "Drip-drop, hop-hop, never fear the rain!", "silver drops"),
    "moon": Rhyme("moon", "the moon rhyme", "Step by step, bright moonlight, puddles turn to play!", "a pearly moon"),
    "bell": Rhyme("bell", "the bell rhyme", "Ting-a-ling, swing and sing, magic knows the way!", "a tiny bell"),
}

NAMES = ["Mabel", "Pip", "Nell", "Tom", "Lulu", "Bram"]
FRIENDS = ["Mouse", "Robin", "Duck"]
PROBLEMS = {
    "warning": {"solve": {"thread", "button", "ribbon"}},
    "surprise": {"solve": {"thread", "button", "ribbon"}},
}
TRAITS = ["brave", "curious", "kind", "bouncy"]


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Event:
    kind: str
    text: str
    cause: str
    result: str


class World:
    def __init__(self, setting: Setting, magic: Magic, rhyme: Rhyme) -> None:
        self.setting = setting
        self.magic = magic
        self.rhyme = rhyme
        self.entities: dict[str, Entity] = {}
        self.history: list[Event] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def record(self, kind: str, text: str, cause: str, result: str) -> None:
        self.history.append(Event(kind, text, cause, result))
        self.say(text)

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def valid_combos() -> list[tuple[str, str, str]]:
    return [
        (place, magic, rhyme)
        for place, setting in SETTINGS.items()
        if "puddles" in setting.affords
        for magic in MAGICS
        for rhyme in RHYMES
    ]


def build_world(params: "StoryParams") -> World:
    if (params.place, params.magic, params.rhyme) not in valid_combos():
        raise StoryError("That place, magic, and rhyme do not make a safe puddle story.")
    world = World(SETTINGS[params.place], MAGICS[params.magic], RHYMES[params.rhyme])
    child = world.add(Entity(params.name, "child", params.name))
    friend = world.add(Entity("friend", "friend", params.friend))
    cloth = world.add(Entity("cloth", "object", "the gingham cloth"))
    puddle = world.add(Entity("puddle", "object", "the deep puddle"))
    child.memes.update(joy=1, courage=0, kindness=0)
    cloth.meters["magic_ready"] = 1
    puddle.meters["deep"] = 1
    world.facts.update(child=child, friend=friend, cloth=cloth, puddle=puddle)
    return world


def make_story(params: "StoryParams") -> World:
    world = build_world(params)
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    friend: Entity = world.facts["friend"]  # type: ignore[assignment]
    cloth: Entity = world.facts["cloth"]  # type: ignore[assignment]
    puddle: Entity = world.facts["puddle"]  # type: ignore[assignment]
    setting = world.setting
    magic = world.magic
    rhyme = world.rhyme

    world.record(
        "arrival",
        f"{params.name} skipped to {setting.name}, {setting.detail}. "
        f"{params.name} wore a little gingham cape, and {rhyme.image} winked in every drop. "
        f"{rhyme.refrain}",
        "The rain had filled the puddles, and the child wanted to play.",
        "The gingham cape and the puddle became part of a new adventure.",
    )

    world.para()
    if params.problem == "warning":
        text = (
            f'The deepest puddle blocked the path. "{params.name}, wait!" called {params.friend}. '
            f'"I see it," said {params.name}, "but how shall we cross?" '
            f'The gingham cloth gave a tiny silver shake. '
            f'"I have an idea," said {params.name}.'
        )
        cause = "The deep puddle could soak small shoes and hide a slippery stone."
        result = "The child stopped to find a careful way across."
    else:
        text = (
            f'{params.name} hopped once, then twice, when the gingham cape began to glow. '
            f'"Did your cape just sparkle?" asked {params.friend}. '
            f'"It did!" said {params.name}. "But magic needs a wise choice."'
        )
        cause = "The gingham cloth held a little magic that woke near the puddle."
        result = "The child learned that magic should be used carefully."
    world.record("problem", text, cause, result)

    world.para()
    child.memes["courage"] += 1
    child.memes["kindness"] += 1
    cloth.meters["enchanted"] = 1
    puddle.meters["safe_path"] = 1
    if params.magic == "thread":
        solution = (
            f'{params.name} held up {magic.name} and spoke clearly: "{magic.phrase}" '
            f'Silver stitches danced from the gingham cloth to the puddle, making bright stepping stones. '
            f'"You go first," said {params.name} to {params.friend}. '
            f'"Thank you!" said {params.friend}, and across they went.'
        )
    elif params.magic == "button":
        solution = (
            f'{params.name} pressed {magic.name} and listened. '
            f'"Do you hear the quiet side?" asked {params.friend}. '
            f'"Yes," said {params.name}. "The moon-button is showing us the safe steps." '
            f'The glowing button marked a little path around the deep place.'
        )
    else:
        solution = (
            f'{params.name} unwound {magic.name} and made a shining line. '
            f'"I will help you first," said {params.name}. '
            f'"Then I can follow," said {params.friend}. '
            f'The ribbon circled the deep puddle and left a dry way beside it.'
        )
    world.record(
        "magic",
        solution,
        magic.cost.capitalize() + ".",
        "The magic made a safe path, and the friends crossed together.",
    )

    world.para()
    child.memes["joy"] += 2
    puddle.meters["crossed"] = 1
    world.record(
        "ending",
        f'{params.name} and {params.friend} reached the other side. '
        f'They sang, "{rhyme.refrain}" The gingham cape shone softly, '
        f'and the puddle kept one small star of magic for tomorrow.',
        "The friends listened, shared the magic, and used the safe path.",
        "They crossed safely and left the magic ready for another rainy day.",
    )
    world.facts["resolved"] = True
    return world


@dataclass
class StoryParams:
    place: str
    magic: str
    rhyme: str
    name: str
    friend: str
    trait: str
    problem: str = "warning"
    seed: Optional[int] = None


KNOWLEDGE = {
    "gingham": QAItem(
        "What is gingham?",
        "Gingham is a woven cloth with a simple checked pattern, often made from two colors.",
    ),
    "magic": QAItem(
        "What is magic in this story?",
        "Magic is a make-believe power that helps the gingham cloth show a safe way across the puddle.",
    ),
    "puddle": QAItem(
        "Why should a child be careful near a deep puddle?",
        "A deep puddle can hide a slippery stone and soak shoes, so a child should stop and choose a safe path.",
    ),
}


def generation_prompts(world: World) -> list[str]:
    p = world.facts["child"]
    return [
        f"Write a Nursery Rhyme story about {p.label}, gingham, puddles, and {world.magic.name}.",
        f"Tell a magical story in which a child and a friend use {world.rhyme.name} to cross a puddle safely.",
    ]


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem("Why did the child stop at the puddle?", world.history[1].result),
        QAItem("How did the magic help?", world.history[2].result),
        QAItem("What happened at the end?", world.history[3].result),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [KNOWLEDGE["gingham"], KNOWLEDGE["magic"], KNOWLEDGE["puddle"]]


ASP_RULES = r"""
safe_fix(M) :- magic(M).
valid(Place, Magic, Rhyme) :- setting(Place), safe_fix(Magic), rhyme(Rhyme).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for key in SETTINGS:
        lines.append(asp.fact("setting", key))
    for key in MAGICS:
        lines.append(asp.fact("magic", key))
    for key in RHYMES:
        lines.append(asp.fact("rhyme", key))
    return "\n".join(lines)


def asp_valid_combos() -> list[tuple]:
    import asp
    program = asp_facts() + "\n" + ASP_RULES + "\n#show valid/3.\n"
    return sorted(set(asp.atoms(asp.one_model(program), "valid")))


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id}: {entity.kind}, meters={entity.meters}, memes={entity.memes}"
        )
    lines.append("--- events ---")
    for event in world.history:
        lines.append(f"  {event.kind}: {event.text}")
    return "\n".join(lines)


def check_sample(sample: StorySample) -> None:
    world = sample.world
    assert world is not None
    assert world.facts["resolved"]
    assert "gingham" in sample.story.lower()
    assert len(sample.story_qa) == 3
    assert all(item.answer.endswith(".") for item in sample.story_qa)
    assert all(event.text in sample.story for event in world.history)
    assert all(marker not in sample.story for marker in ("{", "}", "meters=", "memes="))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Gingham Magic Nursery Rhyme storyworld.")
    parser.add_argument("--place", choices=SETTINGS)
    parser.add_argument("--magic", choices=MAGICS)
    parser.add_argument("--rhyme", choices=RHYMES)
    parser.add_argument("--name")
    parser.add_argument("--friend", choices=FRIENDS)
    parser.add_argument("--trait", choices=TRAITS)
    parser.add_argument("--problem", choices=PROBLEMS)
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
    choices = valid_combos()
    filtered = [
        c for c in choices
        if args.place is None or c[0] == args.place
        if args.magic is None or c[1] == args.magic
        if args.rhyme is None or c[2] == args.rhyme
    ]
    if not filtered:
        raise StoryError("No valid place, magic, and rhyme combination matches those options.")
    place, magic, rhyme = rng.choice(filtered)
    return StoryParams(
        place=place,
        magic=magic,
        rhyme=rhyme,
        name=args.name or rng.choice(NAMES),
        friend=args.friend or rng.choice(FRIENDS),
        trait=args.trait or rng.choice(TRAITS),
        problem=args.problem or rng.choice(sorted(PROBLEMS)),
    )


def generate(params: StoryParams) -> StorySample:
    if params.name in {"friend", "cloth", "puddle"}:
        raise StoryError("The child's name must not collide with a world object.")
    world = make_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("\n== Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("\n== World knowledge ==")
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
        print("\n" + format_qa(sample))


def verify() -> int:
    import asp
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    expected = {(p, m, r) for p, m, r in py}
    if asp_set != expected:
        print("MISMATCH: ASP and Python choices differ.")
        return 1
    for combo in sorted(py):
        sample = generate(
            StoryParams(
                place=combo[0],
                magic=combo[1],
                rhyme=combo[2],
                name="Mabel",
                friend="Mouse",
                trait="kind",
            )
        )
        check_sample(sample)
    print(f"OK: {len(py)} ASP/Python combinations and story checks.")
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.n < 1:
        raise SystemExit("-n must be at least 1")
    if args.show_asp:
        print(asp_facts() + "\n" + ASP_RULES)
        return
    if args.verify:
        raise SystemExit(verify())
    if args.asp:
        for combo in asp_valid_combos():
            print("  " + " ".join(combo))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for i, combo in enumerate(valid_combos()):
            samples.append(
                generate(
                    StoryParams(
                        place=combo[0],
                        magic=combo[1],
                        rhyme=combo[2],
                        name=NAMES[i % len(NAMES)],
                        friend=FRIENDS[i % len(FRIENDS)],
                        trait=TRAITS[i % len(TRAITS)],
                        seed=base_seed + i,
                    )
                )
            )
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        payload = samples[0].to_dict() if len(samples) == 1 else [s.to_dict() for s in samples]
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 or args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
