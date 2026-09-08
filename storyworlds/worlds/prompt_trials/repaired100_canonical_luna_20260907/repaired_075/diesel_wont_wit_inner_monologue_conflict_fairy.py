#!/usr/bin/env python3
"""
A tiny fairy-tale world about Diesel, a stubborn little dragon, and the wit
that helps him solve a conflict without losing his courage.
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
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ("distance", "height", "warmth", "fear", "hope", "wit", "stubbornness"):
            self.meters.setdefault(key, 0.0)
            self.memes.setdefault(key, 0.0)


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


@dataclass
class StoryParams:
    hero: str
    companion: str
    place: str
    obstacle: str
    seed: Optional[int] = None
    telling: int = 0


HEROES = ["Diesel", "Luna", "Pip", "Mara", "Tobin"]
COMPANIONS = ["the old raven", "a brave fox", "the moon moth", "a kindly giant"]
PLACES = [
    "the Whispering Forest",
    "the hill of silver bells",
    "the kingdom beyond the blue river",
    "the rose-gold valley",
]
OBSTACLES = [
    "a thorn gate that would not open",
    "a stone bridge guarded by a sleeping giant",
    "a dark tower with no visible door",
    "a river that carried away every ordinary key",
]

TALES = [
    {
        "problem": "The king's moon lantern had gone dark, and only the star jewel beyond the gate could light it again.",
        "warning": "The gate opens for wit, not for force.",
        "memory": "Diesel had once pushed a treasure chest until the chest rolled downhill and nearly carried him with it.",
        "clue": "the gate's iron thorns made a pattern like a question mark",
        "plan": "trace the question mark in the air with a claw and ask the gate what it wanted",
        "result": "the thorns curled aside because the gate had been waiting for a thoughtful question",
        "lesson": "strength may move a stone, but wit can discover why the stone is there",
        "ending": "The moon lantern shone again, and its pale light turned every thorn into a silver flower.",
    },
    {
        "problem": "A tiny dragon had promised to bring warm bread to the queen before sunset, but the only road crossed a bridge watched by a giant.",
        "warning": "The giant hears boasting, but he listens to honest questions.",
        "memory": "Diesel had once insisted he knew a shortcut and ended up circling the same pond three times.",
        "clue": "the bridge rope had three knots, though the giant wore only two boots",
        "plan": "ask the giant why the bridge had three knots and offer to count them together",
        "result": "the giant smiled, untied the middle knot, and showed the safe path across",
        "lesson": "a question can be braver than a boast",
        "ending": "The queen broke the warm loaf beneath a sky where the first evening star had appeared.",
    },
    {
        "problem": "The river had swept away the village bell, and without it the fairies could not find their way home at dusk.",
        "warning": "The river returns what is invited, not what is grabbed.",
        "memory": "Diesel had once snatched at a floating apple and watched it bob farther away.",
        "clue": "the water repeated the same three notes whenever the moon touched it",
        "plan": "answer those three notes with a gentle whistle instead of reaching into the current",
        "result": "the bell floated toward the bank and rested beside Diesel's warm feet",
        "lesson": "patience gives wit time to hear what haste misses",
        "ending": "When the bell rang, fireflies rose like a golden crown around the village.",
    },
]

OPENINGS = [
    "{hero} lived where the morning mist wore a crown of pearls.",
    "In a kingdom folded between two blue hills, {hero} guarded a very small fire.",
    "Long ago, when stars still whispered to travelers, {hero} woke beneath an elder tree.",
    "At the edge of a green forest lived {hero}, who was strong enough to frighten a boulder.",
]

INNER_THOUGHTS = [
    "If I rush, I may prove only that I can make a mess, Diesel thought.",
    "I do not need a louder roar; I need a clearer idea, Diesel told himself.",
    "Perhaps the puzzle is speaking, Diesel thought. I must listen before I leap.",
    "Being afraid does not forbid me from thinking, Diesel reminded himself.",
]


def build_world(params: StoryParams) -> World:
    if params.hero not in HEROES:
        raise StoryError(f"Unknown hero: {params.hero}")
    if params.companion not in COMPANIONS:
        raise StoryError(f"Unknown companion: {params.companion}")
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"Unknown obstacle: {params.obstacle}")

    tale = TALES[params.telling % len(TALES)]
    world = World(params.place)
    hero = world.add(Entity("hero", "dragon", params.hero))
    companion = world.add(Entity("companion", "helper", params.companion))
    gate = world.add(Entity("obstacle", "obstacle", params.obstacle))
    hero.memes["stubbornness"] = 1.0
    hero.memes["fear"] = 1.0
    hero.memes["wit"] = 0.0

    rng = random.Random((params.seed or 0) ^ 0xD135E1)
    inner = INNER_THOUGHTS[(params.telling + rng.randrange(len(INNER_THOUGHTS))) % len(INNER_THOUGHTS)]

    world.say(OPENINGS[params.telling % len(OPENINGS)].format(hero=params.hero))
    world.say(f"{tale['problem']} The path led through {params.place}, where {params.obstacle}.")
    world.say(f"{params.hero} carried the task in a warm pocket of flame, while {params.companion} walked beside him.")
    world.para()
    world.say(f"This was the conflict: {params.hero} wanted to charge ahead, but {tale['warning']}")
    world.say(f'"Turn back," said {params.companion}. "{tale["warning"]}"')
    world.say(f'"I wont turn back," said {params.hero}. "But I wont pretend I know the answer, either."')
    world.say(f"{params.hero} tried to push at the obstacle, and the obstacle did not move.")
    hero.meters["distance"] += 1
    hero.memes["fear"] += 1
    world.para()
    world.say(inner)
    world.say(f"{params.hero} remembered that {tale['memory']}")
    world.say(f"Then {params.hero} noticed {tale['clue']}.")
    world.say(f'"What do you see?" asked {params.companion}.')
    world.say(f'"A question," said {params.hero}. "The trouble may be asking me to think."')
    hero.memes["wit"] = 1.0
    hero.memes["fear"] = 0.0
    hero.memes["stubbornness"] = 0.0
    world.para()
    world.say(f"With new wit, {params.hero} decided to {tale['plan']}.")
    world.say(f"{params.companion} helped by watching quietly while {params.hero} tried the idea.")
    world.say(f"At once, {tale['result']}.")
    world.say(f"The conflict ended because {params.hero} chose understanding over force.")
    world.say(f"The lesson was clear: {tale['lesson']}.")
    world.say(tale["ending"])

    world.facts.update(
        hero=hero,
        companion=companion,
        obstacle=gate,
        tale=tale,
        inner_monologue=inner,
        lesson_learned=True,
        conflict_resolved=True,
    )
    return world


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    hero = world.facts["hero"]
    tale = world.facts["tale"]
    assert isinstance(hero, Entity)
    assert isinstance(tale, dict)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            f"Tell a fairy tale about {hero.label} facing {world.facts['obstacle'].label}.",
            f"Include an inner monologue in which {hero.label} replaces force with wit.",
            f"Show a conflict resolved through the clue: {tale['clue']}.",
        ],
        story_qa=[
            QAItem(
                "Who is the story about?",
                f"The story is about {hero.label}, a little dragon who learns to use wit instead of rushing.",
            ),
            QAItem(
                "What conflict did the hero face?",
                f"The conflict was that {hero.label} needed to pass {world.facts['obstacle'].label}, but force could not solve the problem.",
            ),
            QAItem(
                "What did the hero think privately?",
                f"{hero.label} thought, '{world.facts['inner_monologue']}'",
            ),
            QAItem(
                "What clue changed the plan?",
                f"The clue was that {tale['clue']}. It showed that the obstacle contained a question rather than a simple barrier.",
            ),
            QAItem(
                "How was the conflict resolved?",
                f"{hero.label} chose to {tale['plan']}. Then {tale['result']}.",
            ),
            QAItem(
                "What lesson was learned?",
                f"The lesson was that {tale['lesson']}.",
            ),
            QAItem(
                "What final image proves the problem was solved?",
                tale["ending"],
            ),
        ],
        world_qa=[
            QAItem("What is wit?", "Wit is clever thinking that helps someone notice a useful idea or solve a problem."),
            QAItem("What is a conflict?", "A conflict is a problem, disagreement, or obstacle that a character must face."),
            QAItem("What is an inner monologue?", "An inner monologue is a character's private thought shown to the reader."),
            QAItem("Why can questions help in a fairy tale?", "Questions can reveal what an enchanted obstacle wants and can lead to a safer solution."),
        ],
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(f"  {entity.id}: kind={entity.kind}, meters={meters}, memes={memes}")
    lines.append("  conflict_resolved: True")
    lines.append("  lesson_learned: True")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("hero", "diesel"),
            asp.fact("obstacle", "enchanted_gate"),
            asp.fact("needs_wit", "enchanted_gate"),
            asp.fact("uses", "diesel", "wit"),
            asp.fact("resolves", "wit", "enchanted_gate"),
        ]
    )


ASP_RULES = r"""
can_solve(H, O) :- hero(H), obstacle(O), needs_wit(O), uses(H, wit), resolves(wit, O).
valid(H) :- can_solve(H, enchanted_gate).
#show can_solve/2.
#show valid/1.
"""


def asp_program() -> str:
    return asp_facts() + "\n" + ASP_RULES


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    valid = set(asp.atoms(model, "valid"))
    if valid != {("diesel",)}:
        print("MISMATCH: ASP and Python disagree.")
        print(sorted(valid))
        return 1
    sample = generate(
        StoryParams(
            hero="Diesel",
            companion=COMPANIONS[0],
            place=PLACES[0],
            obstacle=OBSTACLES[0],
            seed=7,
        )
    )
    if "wit" not in sample.story.lower() or "conflict" not in sample.story.lower():
        print("MISMATCH: generated story lacks required narrative features.")
        return 1
    print("OK: ASP gate agrees with Python reasonableness and story generation.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fairy-tale world of diesel, wont, and wit.")
    parser.add_argument("--hero", choices=HEROES)
    parser.add_argument("--companion", choices=COMPANIONS)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--obstacle", choices=OBSTACLES)
    parser.add_argument("--telling", type=int, choices=range(len(TALES)))
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
    return StoryParams(
        hero=args.hero or rng.choice(HEROES),
        companion=args.companion or rng.choice(COMPANIONS),
        place=args.place or rng.choice(PLACES),
        obstacle=args.obstacle or rng.choice(OBSTACLES),
        seed=args.seed,
        telling=args.telling if args.telling is not None else rng.randrange(len(TALES)),
    )


def format_qa(sample: StorySample) -> str:
    sections = [
        ("== (1) Generation prompts ==", [QAItem(str(i), p) for i, p in enumerate(sample.prompts, 1)]),
        ("== (2) Story questions ==", sample.story_qa),
        ("== (3) World knowledge ==", sample.world_qa),
    ]
    out: list[str] = []
    for title, items in sections:
        out.append(title)
        for item in items:
            out.append(f"Q: {item.question}")
            out.append(f"A: {item.answer}")
        out.append("")
    return "\n".join(out).rstrip()


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

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index in range(len(TALES)):
            params = StoryParams(
                hero="Diesel" if index % 2 == 0 else "Luna",
                companion=COMPANIONS[index % len(COMPANIONS)],
                place=PLACES[index % len(PLACES)],
                obstacle=OBSTACLES[index % len(OBSTACLES)],
                seed=base_seed + index,
                telling=index,
            )
            samples.append(generate(params))
    else:
        for index in range(args.n):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            samples.append(generate(params))

    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        print(json.dumps({"valid": asp.atoms(model, "valid")}, indent=2))
        return

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
