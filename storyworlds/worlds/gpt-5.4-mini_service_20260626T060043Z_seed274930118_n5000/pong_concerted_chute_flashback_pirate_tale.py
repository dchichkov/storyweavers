#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/pong_concerted_chute_flashback_pirate_tale.py
===========================================================================================================================

A tiny pirate-tale storyworld with a flashback beat:
a crew once got a pong ball stuck in a chute, and now they return with
concerted teamwork to guide cargo safely below deck.

The domain is intentionally small and classical:
- pirate crew on a ship at a dock
- a chute that can carry cargo to the hold
- a noisy pong ball that can jam the chute
- a flashback to an earlier mishap
- a concerted plan that fixes the problem

The generated story always has:
- a beginning with the crew and the cargo
- a flashback revealing the earlier trouble
- a turn where a joint plan is needed
- an ending image proving the cargo arrived safely
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

HARD_THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"captain", "pirate", "mate", "sailor"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"woman", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"crew"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the docked ship"
    afford: str = "chute"


@dataclass
class Cargo:
    label: str
    phrase: str
    kind: str
    size: str
    risky_to_chute: bool = True


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    helper_name: str
    cargo: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.flashback_seen = False

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.flashback_seen = self.flashback_seen
        clone.facts = dict(self.facts)
        return clone


def normalize(s: str) -> str:
    return s.strip().lower().replace(" ", "_")


CARGOES = {
    "barrel": Cargo("barrel", "a barrel of apple cider", "barrel", "heavy"),
    "crates": Cargo("crates", "two crates of lamp oil", "crates", "stacked"),
    "fish": Cargo("fish", "a basket of silver fish", "fish", "slippery"),
}

NAMES = ["Mara", "Finn", "Rook", "Lila", "Jory", "Nell", "Bram", "Sera"]
HELPERS = ["cook", "first mate", "deckhand"]
HERO_TYPES = ["captain", "pirate", "mate"]


def story_intro(world: World, hero: Entity, helper: Entity, cargo: Entity) -> None:
    world.say(
        f"Captain {hero.label} stood on the {world.setting.place} with {helper.label}, "
        f"and {cargo.phrase} waited by the chute."
    )
    world.say(
        f"The crew wanted to send {cargo.label} below deck before the tide turned."
    )


def trigger_flashback(world: World, hero: Entity) -> None:
    hero.memes["unease"] = hero.memes.get("unease", 0) + 1
    world.flashback_seen = True
    world.say(
        f"Then Captain {hero.label} remembered a flashback: last time, a pong ball "
        f"had rolled into the chute and made the whole passage pong and jam."
    )


def concerted_plan(world: World, hero: Entity, helper: Entity, cargo: Entity) -> None:
    hero.memes["resolve"] = hero.memes.get("resolve", 0) + 1
    helper.memes["helping"] = helper.memes.get("helping", 0) + 1
    world.say(
        f"So the two of them made a concerted plan: {helper.label} would steady the top, "
        f"and Captain {hero.label} would guide {cargo.label} down slow and straight."
    )


def resolve_scene(world: World, hero: Entity, helper: Entity, cargo: Entity) -> None:
    cargo.meters["in_hold"] = 1
    world.say(
        f"Together they worked the chute cleanly, and {cargo.phrase} slid into the hold "
        f"without a bump."
    )
    world.say(
        f"At the end, Captain {hero.label} grinned as the hold door shut, the deck was clear, "
        f"and no pong ball was left to cause trouble."
    )


def tell(params: StoryParams) -> World:
    world = World(Setting(place=params.place))
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero_name))
    helper = world.add(Entity(id="helper", kind="character", type="crew", label=params.helper_name))
    cargo = world.add(Entity(id="cargo", type=CARGOES[params.cargo].kind, label=CARGOES[params.cargo].label, phrase=CARGOES[params.cargo].phrase))
    chute = world.add(Entity(id="chute", type="chute", label="the chute"))
    pong = world.add(Entity(id="pong", type="ball", label="a pong ball"))

    world.facts.update(hero=hero, helper=helper, cargo=cargo, chute=chute, pong=pong)

    story_intro(world, hero, helper, cargo)
    world.para()
    trigger_flashback(world, hero)
    world.para()
    concerted_plan(world, hero, helper, cargo)
    resolve_scene(world, hero, helper, cargo)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    cargo = f["cargo"]
    return [
        f"Write a short pirate tale about Captain {hero.label}, a chute, and {cargo.label}, with a flashback about a pong ball.",
        f"Tell a child-friendly pirate story where the crew uses concerted teamwork to guide {cargo.phrase} down a chute.",
        f"Write a tiny seafaring story that includes pong, concerted, chute, and a memory from before the fix.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    cargo = f["cargo"]
    return [
        QAItem(
            question=f"Who worked with Captain {hero.label} to move {cargo.label} safely?",
            answer=f"{helper.label} worked with Captain {hero.label}, and they made a concerted plan together."
        ),
        QAItem(
            question="What did Captain " + hero.label + " remember before the plan?",
            answer="Captain " + hero.label + " remembered a flashback about a pong ball getting stuck in the chute."
        ),
        QAItem(
            question=f"What happened to {cargo.phrase} at the end of the story?",
            answer=f"{cargo.phrase} slid into the hold safely, and the chute stayed clear."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a chute?",
            answer="A chute is a slanted passage that helps things slide from one place to another."
        ),
        QAItem(
            question="What does concerted mean?",
            answer="Concerted means people work together in a careful, joined-up way."
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a scene that remembers something that happened earlier."
        ),
        QAItem(
            question="What is a pong ball?",
            answer="A pong ball is a small ball that can bounce and roll around quickly."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id}: {e.type} {e.label} {' '.join(bits)}")
    lines.append(f"  flashback_seen={world.flashback_seen}")
    return "\n".join(lines)


ASP_RULES = r"""
% The story is reasonable when cargo can go down a chute and the crew can act together.
can_use_chute(C) :- cargo(C), chute_available, not jammed_by_pong.

concerted_plan :- crew(H), crew(H2), H != H2.
valid_story :- can_use_chute(_), concerted_plan.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for cid, c in CARGOES.items():
        lines.append(asp.fact("cargo", cid))
        lines.append(asp.fact("cargo_kind", cid, c.kind))
    lines.append(asp.fact("chute_available"))
    lines.append(asp.fact("pong_present"))
    lines.append(asp.fact("story_style", "pirate_tale"))
    lines.append(asp.fact("feature", "flashback"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale world with a flashback, pong, concerted teamwork, and a chute.")
    ap.add_argument("--place", choices=["docked ship"], default="docked ship")
    ap.add_argument("--cargo", choices=sorted(CARGOES), default=None)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--hero-type", choices=HERO_TYPES)
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
    cargo = args.cargo or rng.choice(sorted(CARGOES))
    name = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice(HELPERS)
    hero_type = args.hero_type or rng.choice(HERO_TYPES)
    return StoryParams(place=args.place, hero_name=name, helper_name=helper, cargo=cargo, hero_type=hero_type)


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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def valid_story() -> bool:
    return True


def asp_verify() -> int:
    import asp

    program = asp_program("#show valid_story/0.")
    model = asp.one_model(program)
    has_valid = any(sym.name == "valid_story" for sym in model)
    py = valid_story()
    if has_valid == py:
        print("OK: ASP and Python gates agree.")
        return 0
    print("Mismatch between ASP and Python gates.")
    return 1


CURATED = [
    StoryParams(place="docked ship", hero_name="Mara", helper_name="first mate", cargo="barrel", hero_type="captain"),
    StoryParams(place="docked ship", hero_name="Finn", helper_name="deckhand", cargo="crates", hero_type="pirate"),
    StoryParams(place="docked ship", hero_name="Sera", helper_name="cook", cargo="fish", hero_type="mate"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show cargo_kind/2."))
        print(sorted(asp.atoms(model, "cargo_kind")))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
