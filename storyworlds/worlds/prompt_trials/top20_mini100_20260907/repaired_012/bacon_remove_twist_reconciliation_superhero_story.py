#!/usr/bin/env python3
from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import hashlib
import json
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

from storyworlds.results import QAItem, StoryError, StorySample


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    setting: str
    heroes: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, str] = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)


@dataclass
class StoryParams:
    hero_name: str = "Nova"
    sidekick_name: str = "Byte"
    villain_name: str = "Twist"
    setting: str = "Sunset City"
    seed: Optional[int] = None


HERO_NAMES = ["Nova", "Lumen", "Spark", "Comet", "Beacon", "Mira", "Aster", "Pulse"]
SIDEKICK_NAMES = ["Byte", "Patch", "Zoom", "Echo", "Wisp", "Glint", "Tally", "Orbit"]
VILLAIN_NAMES = ["Twist", "Mire", "Hex", "Rift", "Cinder", "Shade", "Fray", "Quirk"]
SETTINGS = ["Sunset City", "Harbor Heights", "River Square", "Cloudline", "Maple Bay"]


def _stable_rng(params: StoryParams) -> random.Random:
    base = "|".join([params.hero_name, params.sidekick_name, params.villain_name, params.setting, str(params.seed)])
    h = hashlib.sha256(base.encode("utf-8")).digest()
    return random.Random(int.from_bytes(h[:8], "big"))


def _must_not_be_same(a: str, b: str, what: str) -> None:
    if a == b:
        raise StoryError(f"{what} must be different")


def _make_world(params: StoryParams) -> World:
    _must_not_be_same(params.hero_name, params.sidekick_name, "hero and sidekick")
    _must_not_be_same(params.hero_name, params.villain_name, "hero and villain")
    _must_not_be_same(params.sidekick_name, params.villain_name, "sidekick and villain")

    world = World(setting=params.setting)
    hero = Entity(id=params.hero_name, kind="character", type="hero", label="superhero")
    sidekick = Entity(id=params.sidekick_name, kind="character", type="sidekick", label="sidekick")
    villain = Entity(id=params.villain_name, kind="character", type="villain", label="villain")

    hero.meters["courage"] = 7.0
    sidekick.meters["courage"] = 5.0
    villain.meters["scheme"] = 6.0
    hero.memes["trust"] = 2.0
    sidekick.memes["trust"] = 2.0
    villain.memes["twist"] = 1.0

    world.heroes = {"hero": hero, "sidekick": sidekick, "villain": villain}
    return world


def _choose(rng: random.Random, seq: list[str]) -> str:
    return seq[rng.randrange(len(seq))]


def _story_plan(world: World, params: StoryParams) -> dict[str, str]:
    rng = _stable_rng(params)
    hero = world.heroes["hero"]
    sidekick = world.heroes["sidekick"]
    villain = world.heroes["villain"]

    openings = [
        f"In {world.setting}, {hero.id} and {sidekick.id} watched the rooftops from a bright patrol tower while a street vendor fried bacon on a cart below.",
        f"The night began in {world.setting}, where {hero.id} had just helped carry a tray of bacon sandwiches to the rescue station.",
    ]
    twists = [
        f"Then {villain.id} used a twisting mirror beam to spin the rescue bells around and around, and every alarm pointed back at the same block.",
        f"Suddenly, {villain.id} curled the sky-map with a twist ray, making the heroes circle the same street three times while the bacon cart vanished from sight.",
    ]
    conflict = [
        f'"We should chase the beam," {hero.id} said. "{sidekick.id}," replied, "We should remove the mirror first." Their disagreement made the crowd nervous.',
        f'"I can catch {villain.id} now," said {hero.id}. "{sidekick.id} shook their head. "Not until we remove the twisting gadget." For a moment, neither hero moved.',
    ]
    turn = [
        f"They paused beside the bacon cart, and the smell helped them breathe, think, and regain their courage. {sidekick.id} noticed the twist beam only worked when it hit the shiny cart lid.",
        f"A short bacon break calmed their rush. While they listened, {hero.id} saw that the beam bent every time it bounced off a metal lunch tray.",
    ]
    action = [
        f'{sidekick.id} said, "Let us remove the shiny lid first." {hero.id} nodded, lifted the lid away, and used a cape fold to block the beam.',
        f'"Good idea," said {hero.id}. Together they removed the mirror plate, then stepped in front of the twist ray with a clean shield pose.',
    ]
    reconcile = [
        f"{villain.id}'s twist machine clicked uselessly. {hero.id} and {sidekick.id} looked at each other, laughed, and promised to plan together next time.",
        f"The crooked beam fell flat, and {hero.id} reached out first. {sidekick.id} shook that hand, and their reconciliation felt as strong as a rescue siren.",
    ]
    ending = [
        f"By sunrise, the bacon cart was back on its wheels, the street was calm again, and {world.setting} shone under a straight, peaceful sky.",
        f"The last siren faded above {world.setting}, where the bacon smell drifted safely home and the heroes stood side by side, ready for the next call.",
    ]

    idx = rng.randrange(len(openings))
    return {
        "opening": openings[idx],
        "twist": twists[idx % len(twists)],
        "conflict": conflict[idx % len(conflict)],
        "turn": turn[idx % len(turn)],
        "action": action[idx % len(action)],
        "reconcile": reconcile[idx % len(reconcile)],
        "ending": ending[idx % len(ending)],
    }


def generate(params: StoryParams) -> StorySample:
    world = _make_world(params)
    plan = _story_plan(world, params)
    hero = world.heroes["hero"]
    sidekick = world.heroes["sidekick"]
    villain = world.heroes["villain"]

    hero.meters["courage"] = 8.0
    sidekick.meters["courage"] = 8.0
    villain.meters["scheme"] = 0.0
    hero.memes["trust"] = 6.0
    sidekick.memes["trust"] = 6.0
    villain.memes["twist"] = 0.0

    world.facts = {
        "opening": plan["opening"],
        "twist": plan["twist"],
        "conflict": plan["conflict"],
        "turn": plan["turn"],
        "action": plan["action"],
        "reconcile": plan["reconcile"],
        "ending": plan["ending"],
    }

    story = "\n\n".join(
        [
            plan["opening"],
            plan["twist"],
            plan["conflict"],
            plan["turn"],
            plan["action"],
            plan["reconcile"],
            plan["ending"],
        ]
    )

    prompts = [
        "Write a superhero story that starts with bacon, includes a twist, and ends in reconciliation.",
        f"Tell a child-friendly action tale about {hero.id} and {sidekick.id} stopping {villain.id} after a strange twist device.",
        "Write a short story where heroes remove a problem, talk it out, and save the day together.",
    ]

    story_qa = [
        QAItem(
            question="Who were the heroes in the story?",
            answer=f"The heroes were {hero.id} and {sidekick.id}, who worked together in {world.setting}.",
        ),
        QAItem(
            question="What caused the big problem?",
            answer=plan["twist"],
        ),
        QAItem(
            question="What did the heroes remove to stop the twist?",
            answer=f"They removed the shiny lid and the mirror plate that helped the twist beam bounce around.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"{plan['reconcile']} {plan['ending']}",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising turn that changes what the characters think is happening.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation means making peace again after a disagreement or conflict.",
        ),
        QAItem(
            question="What does remove mean?",
            answer="Remove means to take something away from where it is so it no longer causes a problem.",
        ),
    ]

    return StorySample(
        params=params,
        story=story,
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


ASP_RULES = r"""
story_has(hero; sidekick; villain).
valid_story :- story_has(hero), story_has(sidekick), story_has(villain).
valid_story :- twist, remove, reconciliation.
#show valid_story/0.
"""


def asp_facts() -> str:
    from storyworlds import asp

    return "\n".join(
        [
            asp.fact("story_has", "hero"),
            asp.fact("story_has", "sidekick"),
            asp.fact("story_has", "villain"),
            asp.fact("twist"),
            asp.fact("remove"),
            asp.fact("reconciliation"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        from storyworlds import asp
    except Exception as e:
        print(f"ASP unavailable: {e}")
        return 1
    model = asp.one_model(asp_program("#show valid_story/0."))
    if any(sym.name == "valid_story" for sym in model):
        print("OK: ASP twin recognizes the superhero story pattern.")
        return 0
    print("MISMATCH: ASP twin did not validate the story pattern.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld with bacon, twist, remove, and reconciliation.")
    ap.add_argument("--hero-name")
    ap.add_argument("--sidekick-name")
    ap.add_argument("--villain-name", choices=VILLAIN_NAMES)
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero_name or rng.choice(HERO_NAMES)
    sidekick = args.sidekick_name or rng.choice([n for n in SIDEKICK_NAMES if n != hero])
    villain = args.villain_name or rng.choice(VILLAIN_NAMES)
    while villain in {hero, sidekick}:
        villain = rng.choice(VILLAIN_NAMES)
    setting = args.setting or rng.choice(SETTINGS)
    return StoryParams(hero_name=hero, sidekick_name=sidekick, villain_name=villain, setting=setting, seed=args.seed)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    lines.append(f"setting={world.setting}")
    for key, ent in world.heroes.items():
        lines.append(f"{key}: {ent.id} meters={ent.meters} memes={ent.memes}")
    lines.append("facts:")
    for k, v in world.facts.items():
        lines.append(f"  {k}: {v}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("1 compatible superhero story pattern: twist + remove + reconciliation")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("Nova", "Byte", "Twist", "Sunset City", base_seed),
            StoryParams("Spark", "Patch", "Rift", "Harbor Heights", base_seed + 1),
            StoryParams("Beacon", "Echo", "Quirk", "River Square", base_seed + 2),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            params = resolve_params(args, rng)
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
