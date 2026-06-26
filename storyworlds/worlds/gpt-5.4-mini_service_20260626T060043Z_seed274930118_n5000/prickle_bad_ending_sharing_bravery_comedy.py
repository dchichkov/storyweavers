#!/usr/bin/env python3
"""
storyworlds/worlds/prickle_bad_ending_sharing_bravery_comedy.py
===============================================================

A tiny comedic story world about a brave child, a prickly thing, and a sharing
plan that goes a little wrong.

Seed premise:
- A child wants to share something prickly.
- The child is brave enough to try.
- The sharing attempt causes a bad ending, but the story stays playful and child-facing.

The domain is intentionally small so the simulated state can drive the prose:
one hero, one friend, one prickly object, one place, one attempt at sharing,
and one ending image that proves what changed.
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the picnic table"
    comfy: bool = True


@dataclass
class PrickleThing:
    id: str
    label: str
    phrase: str
    kind: str
    prickliness: float = 1.0
    shareable: bool = True
    messy: bool = True


@dataclass
class StoryParams:
    setting: str
    item: str
    hero_name: str
    hero_type: str
    friend_name: str
    friend_type: str
    seed: Optional[int] = None


SETTINGS = {
    "picnic": Setting(place="the picnic table", comfy=True),
    "porch": Setting(place="the porch step", comfy=False),
    "kitchen": Setting(place="the kitchen table", comfy=True),
}

PRICKLES = {
    "prickle": PrickleThing(
        id="prickle",
        label="prickle pear pie",
        phrase="a warm prickle pear pie with tiny shiny spikes on the crust",
        kind="pie",
        prickliness=1.0,
        shareable=True,
        messy=True,
    ),
    "bush": PrickleThing(
        id="bush",
        label="prickle bush bouquet",
        phrase="a silly bouquet of prickle bushes tied with ribbon",
        kind="bouquet",
        prickliness=1.5,
        shareable=False,
        messy=False,
    ),
}

HEROES = [
    ("Mina", "girl"),
    ("Toby", "boy"),
    ("Nia", "girl"),
    ("Ollie", "boy"),
]
FRIENDS = [
    ("Pip", "boy"),
    ("Mara", "girl"),
    ("Juno", "girl"),
    ("Zack", "boy"),
]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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

    def copy(self) -> "World":
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        w.fired = set(self.fired)
        return w


def _share_effects(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    friend = world.get("friend")
    item = world.get("item")
    if hero.memes.get("bravery", 0) >= THRESHOLD and hero.memes.get("sharing", 0) >= THRESHOLD:
        sig = ("share", item.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["joy"] = hero.memes.get("joy", 0) + 1
            friend.memes["joy"] = friend.memes.get("joy", 0) + 1
            out.append("They tried to split it fairly.")
    if item.meters.get("prickly", 0) >= THRESHOLD and not item.plural:
        sig = ("prick", item.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["ouch"] = hero.memes.get("ouch", 0) + 1
            friend.memes["ouch"] = friend.memes.get("ouch", 0) + 1
            out.append("It poked their fingers like a joke that would not stop.")
    if hero.memes.get("ouch", 0) >= THRESHOLD and friend.memes.get("ouch", 0) >= THRESHOLD:
        sig = ("mess", item.id)
        if sig not in world.fired:
            world.fired.add(sig)
            item.meters["broken"] = item.meters.get("broken", 0) + 1
            out.append("The slice slipped and landed upside down.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = _share_effects(world)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def setup_story(world: World, hero: Entity, friend: Entity, item: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} who loved {item.label} because it looked funny "
        f"and smelled sweet."
    )
    world.say(
        f"{hero.id} wanted to share it with {friend.id}, because {hero.id} was brave enough "
        f"to try the tricky part."
    )
    world.facts["hero"] = hero
    world.facts["friend"] = friend
    world.facts["item"] = item


def attempt_sharing(world: World, hero: Entity, friend: Entity, item: Entity) -> None:
    world.para()
    world.say(
        f"At {world.setting.place}, {hero.id} carried the {item.label} to the table "
        f"where {friend.id} was waiting."
    )
    hero.memes["sharing"] = hero.memes.get("sharing", 0) + 1
    hero.memes["bravery"] = hero.memes.get("bravery", 0) + 1
    friend.memes["hope"] = friend.memes.get("hope", 0) + 1
    world.say(f'"I can share it," {hero.pronoun("subject")} said, even though it had prickly bits.')
    propagate(world, narrate=True)
    if item.meters.get("broken", 0) >= THRESHOLD:
        world.say(
            f"The {item.label} tipped over, and the best-looking piece landed face down "
            f"with a tiny prickly sigh."
        )


def ending(world: World, hero: Entity, friend: Entity, item: Entity) -> None:
    world.para()
    if item.meters.get("broken", 0) >= THRESHOLD:
        world.say(
            f"{hero.id} and {friend.id} sat very still, then giggled at the silly mess."
        )
        world.say(
            f"In the end, the {item.label} was not neat at all; it was just a wobbly pile "
            f"of crumbs and prickles, and both children had to lick the frosting from their "
            f"fingers very carefully."
        )
    else:
        world.say(
            f"{hero.id} and {friend.id} managed to nibble the {item.label} without much trouble, "
            f"and they laughed at every tiny poke."
        )


def tell(setting: Setting, item_cfg: PrickleThing, hero_name: str, hero_type: str,
         friend_name: str, friend_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name))
    friend = world.add(Entity(id="friend", kind="character", type=friend_type, label=friend_name))
    item = world.add(Entity(id="item", type=item_cfg.kind, label=item_cfg.label, phrase=item_cfg.phrase))
    item.meters["prickly"] = item_cfg.prickliness
    setup_story(world, hero, friend, item)
    attempt_sharing(world, hero, friend, item)
    ending(world, hero, friend, item)
    world.facts.update(setting=setting, item_cfg=item_cfg)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    item = f["item"]
    return [
        f"Write a short comedy story for a young child about {hero.id} bravely sharing {item.label} with {friend.id}.",
        f"Tell a simple story where a brave child tries to share a prickly treat and the plan ends in a funny bad ending.",
        f"Make a gentle humorous story about sharing {item.label}, bravery, and a prickly mistake at {world.setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    item = world.facts["item"]
    broken = item.meters.get("broken", 0) >= THRESHOLD
    return [
        QAItem(
            question=f"Who was brave enough to share the {item.label}?",
            answer=f"{hero.id} was brave enough to share it with {friend.id}.",
        ),
        QAItem(
            question=f"What made the sharing plan tricky?",
            answer=f"It was tricky because the {item.label} had prickly bits that poked their fingers.",
        ),
        QAItem(
            question="Did the story end neatly?",
            answer="No. It ended in a funny bad ending, with the treat tipped over and crumbs everywhere."
            if broken else
            "Not quite; the children still had a messy moment even though they kept smiling.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is something prickly like?",
            answer="Something prickly has little sharp bits that can poke your fingers.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else have some of what you have, too.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery means doing something hard or a little scary anyway.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story q&a ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world q&a ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
prickly(item) :- item_kind(item, _), prickliness(item, P), P >= 1.
shared(H, F, I) :- bravery(H), sharing(H), friend(F), item(I).
bad_end(I) :- prickly(I), shared(_, _, I), broken(I).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, p in PRICKLES.items():
        lines.append(asp.fact("item_kind", pid, p.kind))
        lines.append(asp.fact("prickliness", pid, int(p.prickliness)))
        if p.shareable:
            lines.append(asp.fact("shareable", pid))
        if p.messy:
            lines.append(asp.fact("messy", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show prickly/1.\n#show shareable/1.\n"))
    asp_prickly = set(asp.atoms(model, "prickly"))
    py_prickly = {(pid,) for pid, p in PRICKLES.items() if p.prickliness >= 1}
    if asp_prickly != py_prickly:
        print("MISMATCH between ASP and Python.")
        print(" only in asp:", sorted(asp_prickly - py_prickly))
        print(" only in py:", sorted(py_prickly - asp_prickly))
        return 1
    print(f"OK: ASP matches Python on prickly items ({len(py_prickly)}).")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A comedic story world about sharing a prickly thing.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=PRICKLES)
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    item = args.item or rng.choice(list(PRICKLES))
    hero_name, hero_type = (args.name, "girl") if args.name else rng.choice(HEROES)
    friend_name, friend_type = (args.friend, "boy") if args.friend else rng.choice(FRIENDS)
    if hero_name == friend_name:
        raise StoryError("Hero and friend must be different.")
    return StoryParams(
        setting=setting,
        item=item,
        hero_name=hero_name,
        hero_type=hero_type,
        friend_name=friend_name,
        friend_type=friend_type,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        PRICKLES[params.item],
        params.hero_name,
        params.hero_type,
        params.friend_name,
        params.friend_type,
    )
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
        print(asp_program("#show prickly/1.\n#show shared/3.\n#show bad_end/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show prickly/1.\n#show shareable/1."))
        print("prickly items:", sorted(asp.atoms(model, "prickly")))
        print("shareable items:", sorted(asp.atoms(model, "shareable")))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("picnic", "prickle", "Mina", "girl", "Pip", "boy"),
            StoryParams("kitchen", "prickle", "Toby", "boy", "Mara", "girl"),
            StoryParams("porch", "bush", "Nia", "girl", "Zack", "boy"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
