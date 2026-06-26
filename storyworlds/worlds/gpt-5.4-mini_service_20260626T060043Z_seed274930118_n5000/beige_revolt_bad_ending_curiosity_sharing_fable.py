#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/beige_revolt_bad_ending_curiosity_sharing_fable.py
==============================================================================================================

A small fable-style storyworld about beige things, curiosity, sharing, and a revolt that ends badly.

Seed tale:
---
In a quiet warren near a dry orchard, a beige rabbit found a basket of pears set aside for the evening feast. The rabbit was curious and peeked under the cloth again and again. When the rabbit refused to share the best pears with the waiting animals, the others grew angry and began a little revolt. The basket spilled, the feast was ruined, and everyone went home hungry.

Narrative instruments:
- Curiosity increases the chance of opening, peeking, and meddling.
- Sharing is the only gentle way to keep the group calm.
- Refusing to share raises grievance; grievance can trigger a revolt.
- A revolt causes the ending to go bad: food is spilled, trust drops, and the group splits.

The prose is authored from the world state rather than a frozen paragraph. The ending is intentionally bad.
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

MORAL = "A small gift shared early can stop a big trouble later."
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
    caretakers: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    props: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ("spilled", "ruined", "shared", "opened"):
            self.meters.setdefault(k, 0.0)
        for k in ("curiosity", "grief", "grievance", "joy", "trust", "anger", "hunger"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"rabbit", "hare", "mouse", "squirrel", "fox", "badger"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    light: str
    afford: set[str] = field(default_factory=set)


@dataclass
class Gift:
    id: str
    label: str
    phrase: str
    kind: str
    shareable: bool = True
    beige: bool = False


@dataclass
class StoryParams:
    setting: str
    gift: str
    hero: str
    crowd: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[str] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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


SETTINGS = {
    "orchard": Setting(place="the dry orchard", light="golden", afford={"peek", "share", "revolt"}),
    "warren": Setting(place="the quiet warren", light="soft", afford={"peek", "share", "revolt"}),
    "meadow": Setting(place="the meadow edge", light="bright", afford={"peek", "share", "revolt"}),
}

GIFTS = {
    "pears": Gift(id="pears", label="pears", phrase="a basket of ripe pears", kind="fruit", shareable=True, beige=True),
    "cakes": Gift(id="cakes", label="cakes", phrase="a tray of little cakes", kind="food", shareable=True, beige=True),
    "nuts": Gift(id="nuts", label="nuts", phrase="a bowl of roasted nuts", kind="food", shareable=True, beige=True),
}

HEROES = {
    "rabbit": {"type": "rabbit", "label": "rabbit"},
    "hare": {"type": "hare", "label": "hare"},
    "mouse": {"type": "mouse", "label": "mouse"},
    "squirrel": {"type": "squirrel", "label": "squirrel"},
}

CROWD = {
    "mice": ("mice", ["mouse", "mouse", "mouse"]),
    "hares": ("hares", ["hare", "hare", "rabbit"]),
    "forest_friends": ("forest friends", ["mouse", "hare", "squirrel"]),
}


def setup_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    world = World(setting)
    hero_type = HEROES[params.hero]["type"]
    hero = world.add(Entity(
        id="Hero",
        kind="character",
        type=hero_type,
        label="the beige wanderer",
        phrase="a small beige wanderer",
        meters={"spilled": 0.0, "ruined": 0.0, "shared": 0.0, "opened": 0.0},
        memes={"curiosity": 0.0, "grief": 0.0, "grievance": 0.0, "joy": 0.0, "trust": 1.0, "anger": 0.0, "hunger": 0.0},
    ))
    gift = GIFTS[params.gift]
    world.add(Entity(
        id="Gift",
        type=gift.kind,
        label=gift.label,
        phrase=gift.phrase,
        owner=hero.id,
        meters={"spilled": 0.0, "ruined": 0.0, "shared": 0.0, "opened": 0.0},
    ))
    crowd_name, crowd_kinds = CROWD[params.crowd]
    for i, kind in enumerate(crowd_kinds, 1):
        world.add(Entity(
            id=f"Friend{i}",
            kind="character",
            type=kind,
            label=f"{kind} friend",
            phrase=f"a small {kind}",
            meters={"spilled": 0.0, "ruined": 0.0, "shared": 0.0, "opened": 0.0},
            memes={"curiosity": 0.0, "grief": 0.0, "grievance": 0.0, "joy": 0.0, "trust": 1.0, "anger": 0.0, "hunger": 1.0},
        ))
    world.facts.update(hero=hero, gift=gift, crowd_name=crowd_name)
    return world


def nudge_curiosity(world: World) -> None:
    hero = world.get("Hero")
    hero.memes["curiosity"] += 1
    world.say(f"In {world.setting.place}, a beige {hero.type} found {world.get('Gift').phrase}.")
    world.say(f"The little creature leaned closer, because curiosity made the cloth seem full of secrets.")


def share_or_refuse(world: World, share: bool) -> None:
    hero = world.get("Hero")
    gift = world.get("Gift")
    friends = [e for e in world.entities.values() if e.kind == "character" and e.id != "Hero"]
    if share:
        gift.meters["shared"] += 1
        hero.memes["joy"] += 1
        hero.memes["trust"] += 1
        for f in friends:
            f.memes["joy"] += 1
            f.memes["trust"] += 1
        world.say(f"The beige {hero.type} shared the {gift.label} with the waiting crowd.")
        world.say("That gentle choice made the whole group feel warm and safe.")
    else:
        hero.memes["grievance"] += 1
        for f in friends:
            f.memes["grievance"] += 1
            f.memes["anger"] += 1
        world.say(f"But the beige {hero.type} kept the best pieces back and would not share.")
        world.say("The waiting animals looked at one another, and their patience turned sharp.")


def trigger_revolt(world: World) -> None:
    hero = world.get("Hero")
    gift = world.get("Gift")
    friends = [e for e in world.entities.values() if e.kind == "character" and e.id != "Hero"]
    if hero.memes["grievance"] >= THRESHOLD or any(f.memes["anger"] >= THRESHOLD for f in friends):
        if "revolt" in world.fired:
            return
        world.fired.add("revolt")
        world.say("Soon the group began a small revolt.")
        hero.memes["trust"] = max(0.0, hero.memes["trust"] - 1.0)
        gift.meters["spilled"] += 1
        gift.meters["ruined"] += 1
        hero.memes["grief"] += 1
        for f in friends:
            f.memes["hunger"] += 1
            f.memes["grief"] += 1
        world.say(f"The {gift.label} toppled onto the dust, and the feast was lost.")


def end_badly(world: World) -> None:
    hero = world.get("Hero")
    gift = world.get("Gift")
    if gift.meters["ruined"] >= THRESHOLD:
        world.say(f"When the sun went down, the beige {hero.type} sat beside the ruined {gift.label}.")
        world.say("The friends went home hungry, and the little warren felt quieter than before.")
        world.say(MORAL)


def tell(setting: Setting, gift: Gift, hero_kind: str, crowd: str, share_choice: bool) -> World:
    world = setup_world(StoryParams(setting=setting_key(setting), gift=gift.id, hero=hero_kind, crowd=crowd))
    hero = world.get("Hero")
    g = world.get("Gift")

    world.say(f"Once, in {setting.place}, there lived a beige {hero.type} with a restless heart.")
    world.say(f"It loved to look, listen, and ask why, which made curiosity grow strong inside it.")
    world.para()

    nudge_curiosity(world)
    world.say(f"At first, the {g.label} was meant for everyone, but the beige {hero.type} wanted it close.")
    share_or_refuse(world, share_choice)
    trigger_revolt(world)
    world.para()
    end_badly(world)

    world.facts.update(setting=setting, gift=gift, share_choice=share_choice)
    return world


def setting_key(setting: Setting) -> str:
    for k, v in SETTINGS.items():
        if v.place == setting.place:
            return k
    raise KeyError(setting.place)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    gift = args.gift or rng.choice(list(GIFTS))
    hero = args.hero or rng.choice(list(HEROES))
    crowd = args.crowd or rng.choice(list(CROWD))
    return StoryParams(setting=setting, gift=gift, hero=hero, crowd=crowd, seed=args.seed)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    g: Gift = f["gift"]
    return [
        f'Write a short fable about a beige animal, curiosity, and sharing, using the word "{g.label}".',
        f"Tell a child-friendly fable where a beige {world.get('Hero').type} learns too late that refusing to share can lead to revolt.",
        f"Write a small moral story in which curiosity opens the way to trouble, and sharing might have saved the day.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.get("Hero")
    gift = world.get("Gift")
    crowd_name = world.facts["crowd_name"]
    return [
        QAItem(
            question=f"What was the beige {hero.type} curious about?",
            answer=f"The beige {hero.type} was curious about {gift.phrase} in {world.setting.place}.",
        ),
        QAItem(
            question=f"Why did the {crowd_name} begin a revolt?",
            answer=f"They began a revolt because the beige {hero.type} would not share the {gift.label}.",
        ),
        QAItem(
            question=f"What happened to the {gift.label} at the end?",
            answer=f"The {gift.label} spilled onto the dust and was ruined, so the ending was bad.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting other creatures use or enjoy something too, not keeping it all for yourself.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the wish to look, ask, and find out more about something new.",
        ),
        QAItem(
            question="What is a revolt?",
            answer="A revolt is when a group rises up together because it feels angry or treated unfairly.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} meters={{{', '.join(f'{k}:{v}' for k, v in e.meters.items() if v)}}} memes={{{', '.join(f'{k}:{v}' for k, v in e.memes.items() if v)}}}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], GIFTS[params.gift], params.hero, params.crowd, share_choice=False)
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


ASP_RULES = r"""
hero_curious(H) :- curiosity(H).
refuse_share(H) :- curious(H), not shared(H).
anger(F) :- refused_share(H), friend(F).
revolt :- anger(F).
bad_ending :- revolt.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for gid, g in GIFTS.items():
        lines.append(asp.fact("gift", gid))
        if g.beige:
            lines.append(asp.fact("beige", gid))
    for h in HEROES:
        lines.append(asp.fact("hero_kind", h))
    for c in CROWD:
        lines.append(asp.fact("crowd_kind", c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable world about beige curiosity, sharing, and revolt.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--crowd", choices=CROWD)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


CURATED = [
    StoryParams(setting="orchard", gift="pears", hero="rabbit", crowd="forest_friends"),
    StoryParams(setting="warren", gift="nuts", hero="hare", crowd="hares"),
    StoryParams(setting="meadow", gift="cakes", hero="mouse", crowd="mice"),
]


def valid_combos() -> list[tuple[str, str, str, str]]:
    return [(s, g, h, c) for s in SETTINGS for g in GIFTS for h in HEROES for c in CROWD]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


def resolve_reasonable(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.gift and not GIFTS[args.gift].shareable:
        raise StoryError("That gift is not shareable, so it cannot support this fable.")
    choices = [c for c in valid_combos()
               if (args.setting is None or c[0] == args.setting)
               and (args.gift is None or c[1] == args.gift)
               and (args.hero is None or c[2] == args.hero)
               and (args.crowd is None or c[3] == args.crowd)]
    if not choices:
        raise StoryError("No valid combination matches the given options.")
    s, g, h, c = rng.choice(sorted(choices))
    return StoryParams(setting=s, gift=g, hero=h, crowd=c, seed=args.seed)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos")
        for row in combos[:50]:
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            try:
                params = resolve_reasonable(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
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
