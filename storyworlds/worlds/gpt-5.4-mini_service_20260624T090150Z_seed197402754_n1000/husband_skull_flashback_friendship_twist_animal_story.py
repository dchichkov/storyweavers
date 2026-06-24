#!/usr/bin/env python3
"""
A small Animal-Story-style world about a husband, a skull, a flashback, a friendship,
and a twist.

Seed tale idea:
- A little animal husband finds a skull in a quiet place.
- He remembers a flashback about a friend who once loved spooky treasures.
- The husband tries to cheer a friend, but the skull becomes part of a twist.
- In the end, the skull is not scary at all; it helps the friends become closer.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    species: str = "animal"
    role: str = ""
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    held_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.species in {"dog", "bear", "fox", "cat", "rabbit", "mouse", "owl", "deer"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str
    detail: str
    quiet: bool = False


@dataclass
class StoryParams:
    setting: str
    husband: str
    friend: str
    skull: str
    seed: Optional[int] = None


SETTINGS = {
    "woods": Setting(place="the mossy woods", detail="The trees stood close together, and the leaves made a soft green ceiling."),
    "cave": Setting(place="a little cave", detail="The cave was dim and cool, with a pebble floor and a tiny echo."),
    "riverbank": Setting(place="the riverbank", detail="The water ticked against the stones, and reeds swayed in the breeze."),
    "barn": Setting(place="an old barn", detail="Dust floated in the sunny air, and hay made a soft golden nest."),
}

HUSBANDS = {
    "otter": ("otter husband", "Otto", "playful"),
    "badger": ("badger husband", "Bram", "steady"),
    "fox": ("fox husband", "Finn", "clever"),
    "rabbit": ("rabbit husband", "Robin", "gentle"),
}

FRIENDS = {
    "mouse": ("mouse friend", "Milo", "shy"),
    "owl": ("owl friend", "Oona", "wise"),
    "deer": ("deer friend", "Della", "careful"),
    "cat": ("cat friend", "Cleo", "bright"),
}

SKULLS = {
    "small": ("a small skull", "small"),
    "old": ("an old skull", "old"),
    "smooth": ("a smooth skull", "smooth"),
    "tiny": ("a tiny skull", "tiny"),
}

FLASHBACK_TRIGGER = "flashback"
FRIENDSHIP_TRIGGER = "friendship"
TWIST_TRIGGER = "twist"


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _is_scary_skull(skull: Entity) -> bool:
    return skull.label in {"small skull", "old skull", "smooth skull", "tiny skull"}


def _flashback(world: World, husband: Entity, friend: Entity, skull: Entity) -> None:
    if (FLASHBACK_TRIGGER, husband.id) in world.fired:
        return
    world.fired.add((FLASHBACK_TRIGGER, husband.id))
    husband.memes["remember"] = husband.memes.get("remember", 0) + 1
    world.say(
        f"Once, {husband.pronoun('subject')} had seen {friend.pronoun('object')} smile at a tiny treasure like this, "
        f"so {husband.pronoun('subject')} remembered that not every strange thing was bad."
    )
    world.facts["flashback"] = True


def _friendship(world: World, husband: Entity, friend: Entity, skull: Entity) -> None:
    if (FRIENDSHIP_TRIGGER, friend.id) in world.fired:
        return
    world.fired.add((FRIENDSHIP_TRIGGER, friend.id))
    friend.memes["warmth"] = friend.memes.get("warmth", 0) + 1
    husband.memes["care"] = husband.memes.get("care", 0) + 1
    world.say(
        f"{husband.label} carried {skull.label} to {friend.label} and said it was a special find, not a bad one."
    )
    world.say(
        f"{friend.label} listened closely, and the two friends sat together until the worry in the air felt smaller."
    )
    world.facts["friendship"] = True


def _twist(world: World, husband: Entity, friend: Entity, skull: Entity) -> None:
    if (TWIST_TRIGGER, skull.id) in world.fired:
        return
    world.fired.add((TWIST_TRIGGER, skull.id))
    world.say(
        f"Then came the twist: the skull was not a warning at all."
    )
    world.say(
        f"It had once belonged to a tiny theater prop left by a lost traveling show, and inside it was a folded note with a map."
    )
    world.say(
        f"The map led the two friends to a hidden berry patch, and their day turned from spooky to sweet."
    )
    skull.meters["meaning"] = skull.meters.get("meaning", 0) + 1
    world.facts["twist"] = True


def tell(setting: Setting, husband_cfg: tuple[str, str, str], friend_cfg: tuple[str, str, str], skull_cfg: tuple[str, str]) -> World:
    world = World(setting)
    husband_role, husband_name, husband_trait = husband_cfg
    friend_role, friend_name, friend_trait = friend_cfg
    skull_label, skull_kind = skull_cfg

    husband = world.add(Entity(
        id=husband_name,
        kind="character",
        species=husband_role.split()[0],
        role="husband",
        label=f"{husband_name} the {husband_role}",
        phrase=f"a {husband_trait} {husband_role}",
        traits=[husband_trait, "kind"],
        meters={"curiosity": 1},
        memes={"care": 1},
    ))
    friend = world.add(Entity(
        id=friend_name,
        kind="character",
        species=friend_role.split()[0],
        role="friend",
        label=f"{friend_name} the {friend_role}",
        phrase=f"a {friend_trait} {friend_role}",
        traits=[friend_trait, "gentle"],
        meters={"worry": 1},
        memes={"trust": 1},
    ))
    skull = world.add(Entity(
        id="skull",
        kind="thing",
        species="thing",
        role="treasure",
        label=skull_label,
        phrase=f"a {skull_kind} skull",
        owner=husband.id,
        held_by=husband.id,
        meters={"dust": 1},
        memes={"mystery": 1},
    ))

    world.say(
        f"{husband.label} lived near {setting.place} and liked quiet walks."
    )
    world.say(
        f"One day, {husband.pronoun('subject')} found {skull.label} on the ground."
    )
    world.say(setting.detail)

    world.para()
    world.say(
        f"{husband.pronoun('subject').capitalize()} felt a little uneasy at first, because the skull looked spooky in the dim light."
    )
    _flashback(world, husband, friend, skull)
    world.say(
        f"That memory made {husband.pronoun('object')} brave enough to bring the skull to {friend.label}."
    )
    _friendship(world, husband, friend, skull)

    world.para()
    _twist(world, husband, friend, skull)
    world.say(
        f"In the end, {husband.label} and {friend.label} shared berries by the water or under the trees, and the skull was just a curious thing that helped them find something good."
    )

    world.facts.update(
        husband=husband,
        friend=friend,
        skull=skull,
        setting=setting,
        husband_cfg=husband_cfg,
        friend_cfg=friend_cfg,
        skull_cfg=skull_cfg,
        resolved=True,
    )
    return world


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for h in HUSBANDS:
            for f in FRIENDS:
                for s in SKULLS:
                    combos.append((setting, h, f, s))
    return combos


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for hid in HUSBANDS:
        lines.append(asp.fact("husband_kind", hid))
    for fid in FRIENDS:
        lines.append(asp.fact("friend_kind", fid))
    for sk in SKULLS:
        lines.append(asp.fact("skull_kind", sk))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,H,F,K) :- setting(S), husband_kind(H), friend_kind(F), skull_kind(K).
#show valid/4.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    husband = f["husband"]
    friend = f["friend"]
    skull = f["skull"]
    return [
        f'Write a short animal story for a young child about {husband.id}, {friend.id}, and {skull.label}.',
        f"Tell a gentle story where a husband finds {skull.label}, remembers a flashback, and learns something kind about friendship.",
        f"Write an animal story with a spooky-looking object, a warm friendship, and a twist at the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    husband: Entity = f["husband"]
    friend: Entity = f["friend"]
    skull: Entity = f["skull"]
    setting: Setting = f["setting"]

    return [
        QAItem(
            question=f"Who found the skull in {setting.place}?",
            answer=f"{husband.label} found {skull.label} while walking through {setting.place}.",
        ),
        QAItem(
            question=f"What did the husband remember before he brought the skull to {friend.label}?",
            answer=f"{husband.label} remembered a flashback about a friend smiling at a strange little treasure, and that memory made him braver.",
        ),
        QAItem(
            question=f"What was the twist about the skull?",
            answer="The skull was not a scary warning at all. It was a theater prop with a folded note that led the friends to a hidden berry patch.",
        ),
        QAItem(
            question=f"How did friendship change the story?",
            answer=f"{husband.label} and {friend.label} began worried, but they listened to each other, sat together, and ended up sharing a happy discovery.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a skull?",
            answer="A skull is the bony shape inside the head of many animals, and people sometimes find old skulls in stories or nature.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when a story briefly remembers something that happened before the main moment.",
        ),
        QAItem(
            question="What does friendship mean?",
            answer="Friendship means caring about someone, sharing time with them, and helping each other feel safe and happy.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising change that makes the story turn in a new direction.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.kind:
            bits.append(f"kind={e.kind}")
        if e.species:
            bits.append(f"species={e.species}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label!r}")
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:8} {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({x[0] for x in world.fired})}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal-story world: husband, skull, flashback, friendship, twist.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--husband", choices=HUSBANDS)
    ap.add_argument("--friend", choices=FRIENDS)
    ap.add_argument("--skull", choices=SKULLS)
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
    combos = valid_combos()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.husband:
        combos = [c for c in combos if c[1] == args.husband]
    if args.friend:
        combos = [c for c in combos if c[2] == args.friend]
    if args.skull:
        combos = [c for c in combos if c[3] == args.skull]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    setting, husband, friend, skull = rng.choice(sorted(combos))
    return StoryParams(setting=setting, husband=husband, friend=friend, skull=skull)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], HUSBANDS[params.husband], FRIENDS[params.friend], SKULLS[params.skull])
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

    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:")
        for t in triples:
            print("  ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for setting in SETTINGS:
            for husband in HUSBANDS:
                for friend in FRIENDS:
                    for skull in SKULLS:
                        p = StoryParams(setting=setting, husband=husband, friend=friend, skull=skull)
                        samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
