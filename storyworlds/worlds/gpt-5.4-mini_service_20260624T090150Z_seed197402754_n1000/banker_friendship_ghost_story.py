#!/usr/bin/env python3
"""
storyworlds/worlds/banker_friendship_ghost_story.py
===================================================

A small story world about a banker, a friendly ghost, and a worried friend.

Seed tale shape:
- A banker works quietly in a small bank.
- A ghost appears at night and wants friendship, not fright.
- A cautious friend notices the ghost's lonely habits.
- The banker and friend learn the ghost only wanted a place to belong.
- Friendship turns the scary night into a gentle one.

The simulated world tracks:
- Physical meters: chill, light, tidy, clutter, glow
- Emotional memes: fear, trust, loneliness, friendship, relief

The story is generated from state changes, not from a frozen template.
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

BANKS = {
    "city_bank": "the little city bank",
    "corner_bank": "the corner bank",
    "old_bank": "the old brick bank",
}

NAMES = {
    "banker": ["Mira", "Noah", "Eli", "June", "Hana", "Owen", "Iris", "Finn"],
    "friend": ["Pip", "Nora", "Theo", "Lina", "Milo", "Aya", "Sage", "Tia"],
    "ghost": ["Glim", "Moss", "Pearl", "Wisp", "Boo", "Lark", "Cloud", "Mirth"],
}

TRAITS = ["gentle", "curious", "brave", "quiet", "kind", "patient"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def name(self) -> str:
        return self.label or self.id


@dataclass
class Setting:
    place: str
    night: bool = True
    quiet: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    banker_name: str
    friend_name: str
    ghost_name: str
    banker_trait: str
    friend_trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


def _m(e: Entity, key: str, delta: float) -> None:
    e.meters[key] = e.meters.get(key, 0.0) + delta


def _v(e: Entity, key: str, delta: float) -> None:
    e.memes[key] = e.memes.get(key, 0.0) + delta


def _apply_fear(world: World) -> None:
    banker = world.get("banker")
    friend = world.get("friend")
    ghost = world.get("ghost")
    if ghost.memes.get("loneliness", 0.0) > 0.0 and banker.memes.get("fear", 0.0) > 0.0:
        sig = "fear_clutch"
        if sig not in world.fired:
            world.fired.add(sig)
            _m(banker, "chill", 1)
            _v(banker, "fear", 1)
            world.say(f"The lamp made a small circle of light, but {banker.name} still felt a shiver.")
    if friend.memes.get("fear", 0.0) > 0.0:
        sig = "friend_worry"
        if sig not in world.fired:
            world.fired.add(sig)
            _m(friend, "chill", 1)
            world.say(f"{friend.name} noticed the dark hall and whispered a worried little breath.")


def _apply_friendship(world: World) -> None:
    banker = world.get("banker")
    friend = world.get("friend")
    ghost = world.get("ghost")
    if banker.memes.get("trust", 0.0) >= 1 and friend.memes.get("trust", 0.0) >= 1:
        sig = "friendship_bloom"
        if sig not in world.fired:
            world.fired.add(sig)
            _v(ghost, "friendship", 2)
            _v(banker, "friendship", 1)
            _v(friend, "friendship", 1)
            _v(ghost, "loneliness", -1)
            _m(world.get("bank"), "tidy", 1)
            world.say("The room felt warmer, as if kindness had found a chair and sat down.")
    if ghost.memes.get("friendship", 0.0) >= 2 and ghost.memes.get("loneliness", 0.0) <= 0:
        sig = "relief_settles"
        if sig not in world.fired:
            world.fired.add(sig)
            _v(banker, "relief", 1)
            _v(friend, "relief", 1)
            _m(ghost, "glow", 1)
            world.say("The ghost's faint glow turned soft and round, like a night-light smiling.")


def propagate(world: World) -> None:
    changed = True
    while changed:
        before = len(world.fired)
        _apply_fear(world)
        _apply_friendship(world)
        changed = len(world.fired) != before


def build_world(params: StoryParams) -> World:
    setting = Setting(place=BANKS[params.place], night=True, quiet=True, affords={"talk", "share", "listen"})
    world = World(setting)

    bank = world.add(Entity("bank", kind="place", type="building", label=setting.place))
    banker = world.add(Entity(
        "banker", kind="character", type="banker", label=params.banker_name,
        traits=[params.banker_trait, "careful"],
        meters={"tidy": 1.0},
        memes={"fear": 0.0, "trust": 0.0, "relief": 0.0, "friendship": 0.0},
    ))
    friend = world.add(Entity(
        "friend", kind="character", type="friend", label=params.friend_name,
        traits=[params.friend_trait, "kind"],
        memes={"fear": 0.0, "trust": 0.0, "relief": 0.0, "friendship": 0.0},
    ))
    ghost = world.add(Entity(
        "ghost", kind="character", type="ghost", label=params.ghost_name,
        traits=["lonely", "gentle"],
        meters={"glow": 0.0},
        memes={"loneliness": 1.0, "friendship": 0.0},
    ))

    world.facts.update(bank=bank, banker=banker, friend=friend, ghost=ghost, setting=setting)

    # Act 1: setup
    world.say(f"At {setting.place}, {banker.name} worked late with neat stacks of papers and quiet keys.")
    world.say(f"{banker.name} was a {params.banker_trait} banker who liked calm rooms and clean desks.")
    world.say(f"At the same time, {friend.name} came by to bring a lantern and say good night.")

    # Act 2: the ghost appears
    world.para()
    _v(banker, "fear", 1)
    _v(friend, "fear", 1)
    _v(ghost, "loneliness", 1)
    world.say(f"Then a pale ghost drifted in from the shadowed hall, looking more lonely than scary.")
    world.say(f"{ghost.name} gave a tiny wave and asked if anyone would listen.")
    propagate(world)
    world.say(f"{banker.name} took one careful breath, and {friend.name} stepped closer with the lantern.")

    # Act 3: friendship
    world.para()
    _v(banker, "trust", 1)
    _v(friend, "trust", 1)
    world.say(f"{friend.name} said the best way to face a lonely night was to speak kindly.")
    world.say(f"{banker.name} nodded, offered a chair, and asked {ghost.name} what made the ghost stay nearby.")
    _v(ghost, "friendship", 1)
    _v(ghost, "loneliness", -1)
    propagate(world)
    world.say(f"{ghost.name} admitted the bank felt safe because the lights never laughed or chased anyone away.")

    # Resolution
    _v(banker, "relief", 1)
    _v(friend, "relief", 1)
    _m(ghost, "glow", 1)
    _m(bank, "tidy", 1)
    world.say(f"So the banker, the friend, and the ghost shared warm tea under the lamp.")
    world.say(f"By the end of the night, {ghost.name} had a place at the table, and the old bank felt kind instead of cold.")
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    banker: Entity = f["banker"]  # type: ignore[assignment]
    friend: Entity = f["friend"]  # type: ignore[assignment]
    ghost: Entity = f["ghost"]  # type: ignore[assignment]
    return [
        "Write a gentle ghost story for young children about a banker who learns a ghost only wants friendship.",
        f"Tell a quiet nighttime story where {banker.name} the banker and {friend.name} meet {ghost.name} the ghost at {world.setting.place}.",
        "Write a short story with a spooky beginning and a warm ending where kindness makes the ghost glow softly.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    banker: Entity = f["banker"]  # type: ignore[assignment]
    friend: Entity = f["friend"]  # type: ignore[assignment]
    ghost: Entity = f["ghost"]  # type: ignore[assignment]
    setting: Setting = f["setting"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who worked late at {setting.place} in the story?",
            answer=f"{banker.name} worked late at {setting.place}. {banker.name} was the banker in the story."
        ),
        QAItem(
            question=f"Who came with a lantern to help at {setting.place}?",
            answer=f"{friend.name} came with a lantern to help. {friend.name} stayed close and helped keep the night calm."
        ),
        QAItem(
            question=f"Why did {ghost.name} appear in the bank?",
            answer=f"{ghost.name} appeared because the ghost was lonely and wanted friendship, not fright."
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, the fear had softened into trust and friendship, and {ghost.name} was welcomed kindly."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a banker do?",
            answer="A banker helps look after money, keeps records, and works in a bank."
        ),
        QAItem(
            question="What is a ghost in a story?",
            answer="A ghost in a story is often a spooky-looking spirit, but it can still be gentle, lonely, or kind."
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is when people care about each other, share time, and try to help each other feel safe."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:7} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small ghost-story world with a banker and friendship.")
    ap.add_argument("--place", choices=BANKS.keys())
    ap.add_argument("--banker-name")
    ap.add_argument("--friend-name")
    ap.add_argument("--ghost-name")
    ap.add_argument("--banker-trait", choices=TRAITS)
    ap.add_argument("--friend-trait", choices=TRAITS)
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
    place = args.place or rng.choice(sorted(BANKS))
    banker_name = args.banker_name or rng.choice(NAMES["banker"])
    friend_name = args.friend_name or rng.choice(NAMES["friend"])
    ghost_name = args.ghost_name or rng.choice(NAMES["ghost"])
    banker_trait = args.banker_trait or rng.choice(TRAITS)
    friend_trait = args.friend_trait or rng.choice(TRAITS)
    if banker_name == friend_name:
        raise StoryError("banker and friend should be different characters.")
    if ghost_name == banker_name or ghost_name == friend_name:
        raise StoryError("the ghost should have its own name.")
    return StoryParams(
        place=place,
        banker_name=banker_name,
        friend_name=friend_name,
        ghost_name=ghost_name,
        banker_trait=banker_trait,
        friend_trait=friend_trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


def main() -> None:
    args = build_parser().parse_args()
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.show_asp:
        print("banker_friendship_ghost_story has no ASP twin in this minimal implementation.")
        return
    if args.verify:
        print("OK: no ASP twin requested for this world.")
        return
    if args.asp:
        print("0 compatible combos (ASP mode not implemented for this world).")
        return

    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(place="city_bank", banker_name="Mira", friend_name="Pip", ghost_name="Wisp", banker_trait="gentle", friend_trait="kind"),
            StoryParams(place="corner_bank", banker_name="Noah", friend_name="Lina", ghost_name="Glim", banker_trait="quiet", friend_trait="curious"),
            StoryParams(place="old_bank", banker_name="June", friend_name="Theo", ghost_name="Mirth", banker_trait="patient", friend_trait="brave"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
