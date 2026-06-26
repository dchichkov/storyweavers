#!/usr/bin/env python3
"""
storyworlds/worlds/scrounge_imply_friendship_humor_folk_tale.py
===============================================================

A small folk-tale storyworld about scrounging, implying, friendship, and humor.

Seed tale:
---
In a village at the edge of a deep wood, a thin little fox named Pella had almost
nothing in her basket. She liked to scrounge for useful scraps, but she was shy
about asking for help. One evening, she found a bent spoon, a bright ribbon, and
half a honey cake. She wanted to keep them all, yet she also wanted the village
children to think she was generous and clever.

Then Pella met a crow who was known for speaking in hints. The crow implied that
a true friend shares a snack before the moon climbs high. Pella pretended not
to understand, but she felt her cheeks warm. At last she divided the cake, tied
the ribbon to the basket, and shared the spoon for stirring berry tea. The crow
laughed, the children laughed, and Pella learned that friendship can begin with
a small, funny choice.

World idea:
- Physical meters: basket fullness, scraps, tea, moonlight, and the value of found goods.
- Emotional memes: hunger, caution, pride, friendship, humor, trust, and shame.
- The story turns when an implication is understood and a selfish scrounge becomes
  a generous share.
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
    kind: str = "thing"   # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        mapping = {"subject": "it", "object": "it", "possessive": "its"}
        if self.type in {"fox", "girl", "woman", "mother"}:
            mapping = {"subject": "she", "object": "her", "possessive": "her"}
        elif self.type in {"boy", "man", "father", "crow"}:
            mapping = {"subject": "he", "object": "him", "possessive": "his"}
        return mapping[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    village: str
    woods: bool = False
    market: bool = False
    inn: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Good:
    id: str
    label: str
    phrase: str
    kind: str
    value: str
    source: str
    useful_for: set[str] = field(default_factory=set)
    shareable: bool = True
    precious: bool = False


@dataclass
class Trick:
    id: str
    verb: str
    hint: str
    reveal: str
    object_word: str
    effect: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    trick: str
    good: str
    hero: str
    hero_kind: str
    friend: str
    friend_kind: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

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
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        c.fired = set(self.fired)
        return c

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class Rule:
    name: str
    apply: callable


def _r_scrounge(world: World) -> list[str]:
    out = []
    hero = world.get(world.facts["hero"].id)
    if hero.memes.get("hunger", 0) < THRESHOLD:
        return out
    sig = ("scrounge", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.meters["scraps"] = hero.meters.get("scraps", 0) + 1
    hero.memes["caution"] = hero.memes.get("caution", 0) + 1
    out.append(f"{hero.id} went scrounging for a little something useful.")
    return out


def _r_friendship(world: World) -> list[str]:
    out = []
    hero = world.get(world.facts["hero"].id)
    friend = world.get(world.facts["friend"].id)
    if hero.memes.get("understanding", 0) < THRESHOLD:
        return out
    sig = ("friendship", hero.id, friend.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["friendship"] = hero.memes.get("friendship", 0) + 1
    friend.memes["friendship"] = friend.memes.get("friendship", 0) + 1
    hero.memes["trust"] = hero.memes.get("trust", 0) + 1
    friend.memes["trust"] = friend.memes.get("trust", 0) + 1
    out.append(f"That small choice made the air feel kinder between them.")
    return out


CAUSAL_RULES = [Rule("scrounge", _r_scrounge), Rule("friendship", _r_friendship)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tell(place: Place, trick: Trick, good: Good, hero_name: str, hero_kind: str,
         friend_name: str, friend_kind: str) -> World:
    world = World(place)
    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_kind, label=hero_kind,
        meters={"scraps": 0, "value": 0}, memes={"hunger": 1, "pride": 1, "caution": 0}
    ))
    friend = world.add(Entity(
        id=friend_name, kind="character", type=friend_kind, label=friend_kind,
        meters={}, memes={"wit": 1, "humor": 1, "friendship": 0, "trust": 0}
    ))
    good_ent = world.add(Entity(
        id=good.id, type=good.kind, label=good.label, phrase=good.phrase,
        owner=hero.id, caretaker=friend.id, plural=good.kind.endswith("s"),
        meters={"value": 1}, memes={}
    ))
    world.facts.update(hero=hero, friend=friend, good=good_ent, trick=trick, place=place)

    world.say(f"In {place.name}, there lived a little {hero_kind} named {hero_name}.")
    world.say(f"{hero_name} liked to scrounge for useful scraps, because the road of the village was long and the cupboard was often light.")
    world.say(f"One day, {hero_name} found {good.phrase} and tucked {good_ent.it()} into {hero_name}'s basket.")
    world.para()
    world.say(f"Near the well, a clever {friend_kind} named {friend_name} spoke in a sly way.")
    world.say(f'{"“"}{trick.hint}{"”"} {friend_name} said, and that was how {friend_name} implied {trick.reveal}.')
    world.say(f"{hero_name} pretended not to hear the joke, but {hero_name} kept thinking about it.")
    hero.memes["understanding"] = 1
    hero.memes["humor"] = hero.memes.get("humor", 0) + 1
    hero.memes["shame"] = hero.memes.get("shame", 0) + 1
    world.para()
    world.say(f"At last, {hero_name} shared the {good.label}, and that tiny act felt warmer than any hearth.")
    hero.memes["friendship"] = hero.memes.get("friendship", 0) + 1
    friend.memes["friendship"] = friend.memes.get("friendship", 0) + 1
    hero.memes["trust"] = hero.memes.get("trust", 0) + 1
    propagate(world)
    world.say(f"By moonrise, the basket was lighter, but the friendship was heavier.")
    world.facts["resolved"] = True
    return world


PLACES = {
    "village_edge": Place(name="the village edge", village="village", woods=True, market=True, affords={"scrounge", "gather"}),
    "market_square": Place(name="the market square", village="village", market=True, affords={"scrounge", "trade"}),
    "river_path": Place(name="the river path", village="village", woods=True, affords={"scrounge"}),
}

TRICKS = {
    "imply_friendship": Trick(
        id="imply_friendship",
        verb="imply",
        hint="A true friend shares a snack before the moon climbs high",
        reveal="a friend should share",
        object_word="snack",
        effect="understanding",
        keyword="friendship",
        tags={"friendship", "humor", "imply"},
    ),
    "imply_help": Trick(
        id="imply_help",
        verb="imply",
        hint="A kind helper leaves a crumb on the doorstep",
        reveal="someone is asking for help kindly",
        object_word="crumb",
        effect="understanding",
        keyword="help",
        tags={"friendship", "humor", "imply"},
    ),
}

GOODS = {
    "honey_cake": Good(
        id="honey_cake",
        label="honey cake",
        phrase="half a honey cake",
        kind="cake",
        value="sweet",
        source="market",
        useful_for={"share"},
        precious=True,
    ),
    "berry_tea": Good(
        id="berry_tea",
        label="berry tea",
        phrase="a little pot of berry tea",
        kind="tea",
        value="warm",
        source="wellhouse",
        useful_for={"share"},
    ),
    "bright_ribbon": Good(
        id="bright_ribbon",
        label="bright ribbon",
        phrase="a bright ribbon",
        kind="ribbon",
        value="pretty",
        source="roadside",
        useful_for={"gift"},
    ),
}

HEROES = ["Pella", "Nori", "Mina", "Tessa", "Luma"]
FRIENDS = ["Crow", "Marten", "Wren", "Otter", "Hare"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for tid, trick in TRICKS.items():
            for gid, good in GOODS.items():
                if "friendship" in trick.tags and good.shareable and place.affords:
                    combos.append((pid, tid, gid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small folk-tale world about scrounging and implied friendship.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--trick", choices=TRICKS)
    ap.add_argument("--good", choices=GOODS)
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--hero-kind", choices=["fox", "mouse", "girl", "boy"])
    ap.add_argument("--friend-kind", choices=["crow", "marten", "wren", "otter", "hare"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.trick is None or c[1] == args.trick)
              and (args.good is None or c[2] == args.good)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, trick, good = rng.choice(sorted(combos))
    hero_kind = args.hero_kind or rng.choice(["fox", "mouse", "girl", "boy"])
    friend_kind = args.friend_kind or rng.choice(["crow", "marten", "wren", "otter", "hare"])
    hero = args.name or rng.choice(HEROES)
    friend = args.friend or rng.choice(FRIENDS)
    return StoryParams(place=place, trick=trick, good=good, hero=hero, hero_kind=hero_kind,
                       friend=friend, friend_kind=friend_kind)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short folk tale about a {f["hero"].type} named {f["hero"].id} who scrounges for a small treasure and learns friendship through humor.',
        f'Create a gentle story where {f["friend"].id} implies a kind lesson and {f["hero"].id} responds by sharing {f["good"].phrase}.',
        f'Write a child-facing story with the words "scrounge" and "imply" that ends with two neighbors laughing together.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    good = f["good"]
    trick = f["trick"]
    return [
        QAItem(
            question=f"Who scrounged for something useful in the village?",
            answer=f"{hero.id}, a little {hero.type}, scrounged for useful scraps in {world.place.name}."
        ),
        QAItem(
            question=f"What did {friend.id} imply with a joke?",
            answer=f"{friend.id} implied {trick.reveal} by saying, {trick.hint.lower()}."
        ),
        QAItem(
            question=f"What did {hero.id} share at the end?",
            answer=f"{hero.id} shared {good.phrase}, and that helped turn the moment into friendship."
        ),
        QAItem(
            question=f"Why did the story feel funny?",
            answer=f"It felt funny because {friend.id} spoke in hints, and {hero.id} had to understand the joke before the two friends could laugh together."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What does it mean to scrounge?", answer="To scrounge means to search around for small useful things, often with a little effort."),
        QAItem(question="What does imply mean?", answer="To imply means to suggest something without saying it directly."),
        QAItem(question="What is friendship?", answer="Friendship is a kind bond between people who care about each other and want to help."),
        QAItem(question="Why can humor help friends?", answer="Humor can help because a shared laugh can make people feel close and safe together."),
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
    lines.append("== (3) World knowledge questions ==")
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
hero_scrounges(H) :- hero(H).
understands(H) :- hint_heard(H), joke_implied.
friendship(H,F) :- understands(H), friend(F).
humor_event(H,F) :- joke_implied, hero(H), friend(F).
valid(P,T,G) :- place(P), trick(T), good(G), shares(G).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
        for a in sorted(PLACES[pid].affords):
            lines.append(asp.fact("affords", pid, a))
    for tid in TRICKS:
        lines.append(asp.fact("trick", tid))
        lines.append(asp.fact("joke_implied"))
    for gid, g in GOODS.items():
        lines.append(asp.fact("good", gid))
        if g.shareable:
            lines.append(asp.fact("shares", gid))
    for h in HEROES:
        lines.append(asp.fact("hero", h))
    for f in FRIENDS:
        lines.append(asp.fact("friend", f))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
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


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], TRICKS[params.trick], GOODS[params.good],
                 params.hero, params.hero_kind, params.friend, params.friend_kind)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        models = asp_valid_combos()
        print(f"{len(models)} compatible combos:")
        for m in models:
            print(" ", m)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        for place, trick, good in valid_combos():
            params = StoryParams(place=place, trick=trick, good=good, hero="Pella",
                                 hero_kind="fox", friend="Crow", friend_kind="crow")
            samples.append(generate(params))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
