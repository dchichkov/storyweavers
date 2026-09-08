#!/usr/bin/env python3
"""
A tiny nursery-rhyme world about a wallop that becomes a lesson in kindness.
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

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_root, "results.py")):
    _root = os.path.dirname(_root)
sys.path.insert(0, _root)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    label: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity


@dataclass(frozen=True)
class Rhyme:
    opening: str
    quarrel: str
    wallop: str
    clue: str
    kindness: str
    resolution: str
    ending: str
    lesson: str
    sound: str


SETTINGS = {
    "nursery": "the little nursery",
    "playroom": "the moonlit playroom",
    "garden": "the rhyme-garden",
}

HEROES = ["Luna", "Pip", "Mabel", "Toby", "Nell"]
HELPERS = ["Mother Goose", "Grandma Wren", "Baker Bear", "Old Owl"]
TOYS = {
    "drum": "a round red drum",
    "bell": "a silver bell",
    "top": "a painted spinning top",
}
RHYMES = [
    Rhyme(
        "Luna skipped through the nursery while the moon tapped time on the pane.",
        "She and Pip both reached for the red drum, and neither wished to let go.",
        "In the tug and tumble, Luna gave the drum a wallop, and its little skin went POP!",
        "A quiet tear shone on Pip's cheek, and the crooked drumstick pointed to what had happened.",
        "Luna softened her voice, helped Pip gather the scattered buttons, and offered her own ribbon to mend the drum.",
        "Mother Goose showed them how to loosen the torn skin, share the drum by turns, and say sorry without hiding.",
        "Soon Luna tapped softly, Pip beat the steady part, and the drum sang a kinder song.",
        "A strong hand must still have a gentle heart.",
        "pop-pop, hush-hush",
    ),
    Rhyme(
        "In the rhyme-garden, Luna danced where the daisies nodded white.",
        "Pip claimed the silver bell, while Luna claimed it too, and their frowns grew wide.",
        "A hurried elbow gave the bell a wallop, sending it wobbling into the watering can.",
        "The bell made no bright ring; it gave one small, sad clink against the tin.",
        "Luna fetched the bell, held it carefully, and asked Pip how they could make the game fair.",
        "Old Owl dried the bell, and the children made a turn-taking rhyme for every player.",
        "The bell rang bright again, and each child danced when the rhyme named their name.",
        "Fair turns can turn a quarrel into music.",
        "clink, drip-drop",
    ),
    Rhyme(
        "Luna found the painted top beneath the playroom chair and spun it round and round.",
        "Pip wanted the next spin before Luna's turn had ended, so the two voices rose.",
        "Pip's foot gave the top a wallop, and the painted toy rolled beneath the cupboard.",
        "Its blue stripe stopped beside a dusty button, showing exactly where it had gone.",
        "Pip apologized, and Luna lay flat to reach beneath the cupboard while Pip held the lantern.",
        "Grandma Wren made a three-line waiting rhyme so every child knew when to spin.",
        "The top whirled in the center, and nobody needed to shove or shout.",
        "Patience gives play room to breathe.",
        "whirr, bump-bump",
    ),
]


@dataclass
class StoryParams:
    setting: str
    hero: str
    helper: str
    toy: str
    seed: Optional[int] = None


def reasonability_gate(setting: str, hero: str, helper: str, toy: str) -> bool:
    if setting not in SETTINGS:
        raise StoryError(f"unknown setting: {setting}")
    if hero not in HEROES:
        raise StoryError(f"unknown hero: {hero}")
    if helper not in HELPERS:
        raise StoryError(f"unknown helper: {helper}")
    if toy not in TOYS:
        raise StoryError(f"unknown toy: {toy}")
    if hero == helper:
        raise StoryError("the hero and helper must be different characters")
    return True


def tell(params: StoryParams) -> World:
    reasonability_gate(params.setting, params.hero, params.helper, params.toy)
    world = World(SETTINGS[params.setting])
    hero = world.add(Entity("hero", params.hero, "child", meters={"reach": 1.0}, memes={"kindness": 0.0}))
    friend = world.add(Entity("friend", "Pip" if params.hero != "Pip" else "Mabel", "child", memes={"trust": 0.0}))
    helper = world.add(Entity("helper", params.helper, "helper", memes={"wisdom": 1.0}))
    toy = world.add(Entity("toy", TOYS[params.toy], "toy", meters={"strength": 1.0}, memes={"joy": 1.0}))

    rhyme = RHYMES[(params.seed or 0) % len(RHYMES)]
    world.facts.update(hero=hero, friend=friend, helper=helper, toy=toy, rhyme=rhyme)
    hero.memes["kindness"] = 1.0
    hero.memes["anger"] = 0.0
    friend.memes["trust"] = 1.0
    world.facts["conflict"] = True
    world.facts["resolved"] = True
    return world


def render(world: World) -> str:
    f = world.facts
    hero, friend, helper, toy, r = f["hero"], f["friend"], f["helper"], f["toy"], f["rhyme"]
    return "\n\n".join(
        [
            f"{r.opening} {hero.label} carried {toy.label}, bright as a star.",
            f"{r.quarrel} {hero.label} cried, \"My turn!\" {friend.label} cried, \"My turn too!\"",
            f"{r.wallop} \"Oh dear,\" said {hero.label}. \"I did not mean to hurt the toy.\"",
            f"{r.clue} {friend.label} whispered, \"I wanted to play, not fight.\" "
            f"{hero.label} answered, \"Then let us fix it together.\"",
            f"{r.kindness} {helper.label} said, \"Kind words and careful hands can mend more than toys.\"",
            f"{r.resolution} {hero.label} said, \"You go first.\" {friend.label} replied, \"And I will share.\"",
            f"{r.ending} {r.sound} went the happy rhyme.",
            f"The nursery lesson was this: {r.lesson}",
        ]
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a nursery rhyme about {f['hero'].label}, a wallop, and a kindness that resolves a conflict.",
        f"Tell a child-friendly rhyme in which {f['hero'].label} repairs {f['toy'].label} after a quarrel.",
        f"Use the sound {f['rhyme'].sound} and end with the lesson: {f['rhyme'].lesson}",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    r = f["rhyme"]
    return [
        QAItem("Who caused the wallop?", f"{f['hero'].label} caused the wallop during a quarrel over {f['toy'].label}."),
        QAItem("What showed that someone was hurt by the conflict?", r.clue),
        QAItem("How did kindness change the situation?", r.kindness),
        QAItem("How was the conflict resolved?", r.resolution),
        QAItem("What lesson did the rhyme teach?", f"The rhyme taught that {r.lesson}"),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a wallop?", "A wallop is a hard hit or blow."),
        QAItem("What is kindness?", "Kindness means treating people and living things with care, respect, and helpful words."),
        QAItem("What is a conflict?", "A conflict is a disagreement or struggle between people who want different things."),
        QAItem("Why is saying sorry useful?", "Saying sorry can acknowledge harm and help people choose a better action together."),
    ]


def asp_facts() -> str:
    import asp
    lines = []
    for setting in SETTINGS:
        lines.append(asp.fact("setting", setting))
    for hero in HEROES:
        lines.append(asp.fact("hero", hero))
    for toy in TOYS:
        lines.append(asp.fact("toy", toy))
    lines.append(asp.fact("conflict", "quarrel"))
    lines.append(asp.fact("kindness", "repair"))
    return "\n".join(lines)


ASP_RULES = r"""
wallop_risk(T) :- toy(T), conflict(quarrel).
kind_choice(repair) :- kindness(repair), wallop_risk(_).
valid(S,T) :- setting(S), toy(T), kind_choice(repair).
"""


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n#show valid/2.\n"


def valid_combos() -> set[tuple[str, str]]:
    return {(s, t) for s in SETTINGS for t in TOYS}


def asp_valid_combos() -> set[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return set(asp.atoms(model, "valid"))


def asp_verify() -> int:
    try:
        actual = asp_valid_combos()
    except Exception as exc:
        print(f"ASP verification unavailable: {exc}")
        return 1
    expected = valid_combos()
    if actual != expected:
        print("MISMATCH between clingo and Python gate")
        print("python only:", sorted(expected - actual))
        print("clingo only:", sorted(actual - expected))
        return 1
    for seed in range(4):
        p = StoryParams("nursery", "Luna", "Mother Goose", "drum", seed)
        sample = generate(p)
        if not sample.story or "wallop" not in sample.story:
            return 1
    print(f"OK: clingo gate matches valid_combos() ({len(expected)} combos).")
    return 0


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts ==", *[f"- {p}" for p in sample.prompts], "", "== story qa =="]
    for item in sample.story_qa:
        lines += [f"Q: {item.question}", f"A: {item.answer}"]
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines += [f"Q: {item.question}", f"A: {item.answer}"]
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---", f"setting: {world.setting}"]
    for entity in world.entities.values():
        lines.append(f"  {entity.id}: {entity.kind}, meters={entity.meters}, memes={entity.memes}")
    lines.append(f"  conflict={world.facts['conflict']}, resolved={world.facts['resolved']}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=render(world),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A nursery-rhyme world about wallop, kindness, and conflict.")
    parser.add_argument("--setting", choices=SETTINGS)
    parser.add_argument("--hero", choices=HEROES)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--toy", choices=TOYS)
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
    return StoryParams(
        setting=args.setting or rng.choice(list(SETTINGS)),
        hero=args.hero or rng.choice(HEROES),
        helper=args.helper or rng.choice(HELPERS),
        toy=args.toy or rng.choice(list(TOYS)),
        seed=args.seed,
    )


def emit(sample: StorySample, *, trace: bool, qa: bool, header: str = "") -> None:
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
    if args.asp:
        import asp
        for atom in sorted(asp.atoms(asp.one_model(asp_program()), "valid")):
            print(atom)
        return

    base = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        for i, setting in enumerate(SETTINGS):
            samples.append(generate(StoryParams(setting, "Luna", "Mother Goose", "drum", base + i)))
    else:
        seen = set()
        for i in range(max(args.n, 0)):
            params = resolve_params(args, random.Random(base + i))
            params.seed = base + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)

    if args.json:
        print(json.dumps(samples[0].to_dict() if len(samples) == 1 else [s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
