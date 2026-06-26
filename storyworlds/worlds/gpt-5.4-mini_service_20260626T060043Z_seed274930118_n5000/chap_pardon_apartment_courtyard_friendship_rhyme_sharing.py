#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/chap_pardon_apartment_courtyard_friendship_rhyme_sharing.py
=========================================================================================================================

A small standalone fairy-tale storyworld set in an apartment courtyard.

Seed tale idea:
A little chap loves to rhyme under the courtyard ivy. He has one sweet bun and
one bright ribbon charm, but he does not want to share. A friend says, "Pardon,"
and the chap learns that friendship can grow when rhyme and sharing are both
kept in the heart.

The world model tracks:
- physical meters: how many things are shared, held back, or softened by use
- emotional memes: friendship, pride, shame, joy, apology

The story is intentionally narrow and constraint-checked: the central tension is
whether a small chap will share a treasured thing in the apartment courtyard,
and the resolution is a believable change of heart.
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
    owner: Optional[str] = None
    with_whom: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"boy", "chap", "prince", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "maid", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the apartment courtyard"
    affords: set[str] = field(default_factory=lambda: {"rhyme", "sharing"})


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    shareable: bool = True
    precious: bool = False


@dataclass
class StoryParams:
    place: str
    item: str
    name: str
    friend_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.trace_log: list[str] = []

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


def _r_friendship(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    friend = world.get("friend")
    if hero.memes.get("kindness", 0.0) >= THRESHOLD and friend.memes.get("kindness", 0.0) >= THRESHOLD:
        sig = ("friendship",)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["friendship"] = hero.memes.get("friendship", 0.0) + 1
            friend.memes["friendship"] = friend.memes.get("friendship", 0.0) + 1
            out.append("Their friendship grew warm as a lantern glow.")
    return out


def _r_sharing(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    item = world.get("item")
    friend = world.get("friend")
    if hero.memes.get("sharing", 0.0) >= THRESHOLD and item.meters.get("shared", 0.0) < THRESHOLD:
        sig = ("shared", item.id)
        if sig not in world.fired:
            world.fired.add(sig)
            item.meters["shared"] = 1
            friend.meters["gifted"] = friend.meters.get("gifted", 0.0) + 1
            out.append(f"The {item.label} was shared at last.")
    return out


CAUSAL_RULES = [_r_friendship, _r_sharing]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def build_scene(params: StoryParams) -> World:
    world = World(Setting(place=params.place))
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type="chap",
        label=params.name,
        meters={"holding_back": 0.0, "shared": 0.0},
        memes={"pride": 1.0, "joy": 0.5, "friendship": 0.0, "sharing": 0.0, "apology": 0.0},
    ))
    friend = world.add(Entity(
        id="friend",
        kind="character",
        type="girl",
        label=params.friend_name,
        meters={"waiting": 0.0},
        memes={"kindness": 1.0, "longing": 1.0, "friendship": 0.0},
    ))
    item = world.add(Entity(
        id="item",
        kind="thing",
        type=params.item,
        label=ITEMS[params.item].label,
        phrase=ITEMS[params.item].phrase,
        owner=hero.id,
        meters={"shared": 0.0},
    ))
    world.facts.update(hero=hero, friend=friend, item=item, params=params)
    return world


def intro(world: World) -> None:
    hero = world.get("hero")
    item = world.get("item")
    world.say(
        f"In the apartment courtyard, a small chap named {hero.label} liked to hum a rhyme "
        f"beside the ivy wall."
    )
    world.say(
        f"He kept {hero.pronoun('possessive')} {item.label} close, for it was {item.phrase}."
    )


def tension(world: World) -> None:
    hero = world.get("hero")
    friend = world.get("friend")
    item = world.get("item")
    hero.memes["pride"] += 1
    hero.meters["holding_back"] += 1
    world.say(
        f"Then {friend.label} came to the stone bench and said, "
        f'"Pardon, kind chap, may I share {item.it()} and rhyme with you?"'
    )
    world.say(
        f"{hero.label} wanted to keep {item.it()} all to himself, so he folded {hero.pronoun('possessive')} arms "
        f"and hid the {item.label} behind {hero.pronoun('possessive')} back."
    )


def turn(world: World) -> None:
    hero = world.get("hero")
    friend = world.get("friend")
    item = world.get("item")
    hero.memes["shame"] = hero.memes.get("shame", 0.0) + 1
    world.say(
        f"But the courtyard felt quiet without the second voice, and the rhyme went thin and lonely."
    )
    world.say(
        f"{hero.label} looked at {friend.label}'s patient face and whispered, "
        f'"Pardon me. I forgot that a shared rhyme sounds sweeter."'
    )
    hero.memes["apology"] += 1
    hero.memes["sharing"] += 1
    hero.memes["kindness"] = hero.memes.get("kindness", 0.0) + 1
    friend.memes["kindness"] = friend.memes.get("kindness", 0.0) + 1
    item.meters["shared"] = 1
    propagate(world, narrate=False)


def resolution(world: World) -> None:
    hero = world.get("hero")
    friend = world.get("friend")
    item = world.get("item")
    world.say(
        f"So {hero.label} placed the {item.label} between them, and the two friends took turns with the rhyme."
    )
    world.say(
        f"They laughed softly under the apartment windows, and the little chap's heart felt light at last."
    )


def tell(params: StoryParams) -> World:
    world = build_scene(params)
    intro(world)
    world.para()
    tension(world)
    world.para()
    turn(world)
    resolution(world)
    world.facts["resolved"] = True
    return world


def item_at_risk(item: Item) -> bool:
    return item.shareable and item.precious


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for item_id, item in ITEMS.items():
        if item_at_risk(item):
            combos.append(("apartment_courtyard", "friendship_rhyme_sharing", item_id))
    return combos


@dataclass
class ASPInputs:
    place: str
    item: str


ASP_RULES = r"""
at_risk(Item) :- item(Item), shareable(Item), precious(Item).
compatible_story(Place, Item) :- setting(Place), place_ok(Place), at_risk(Item).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", "apartment_courtyard"), asp.fact("place_ok", "apartment_courtyard")]
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        if item.shareable:
            lines.append(asp.fact("shareable", item_id))
        if item.precious:
            lines.append(asp.fact("precious", item_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible_story/2."))
    return sorted(set(asp.atoms(model, "compatible_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("only python:", sorted(py - cl))
    print("only asp:", sorted(cl - py))
    return 1


ITEMS = {
    "bun": Item(id="bun", label="honey bun", phrase="a sweet honey bun", shareable=True, precious=True),
    "ribbon": Item(id="ribbon", label="silk ribbon", phrase="a bright silk ribbon charm", shareable=True, precious=True),
    "book": Item(id="book", label="rhyme-book", phrase="a little rhyme-book with gold corners", shareable=True, precious=True),
}

NAMES = ["Pip", "Toby", "Milo", "Nico", "Arin", "Bram"]
FRIENDS = ["Luna", "Mira", "Tess", "Wren", "Elsa", "Ivy"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale storyworld: chap, pardon, friendship, rhyme, sharing.")
    ap.add_argument("--place", choices=["apartment_courtyard"], default="apartment_courtyard")
    ap.add_argument("--item", choices=list(ITEMS))
    ap.add_argument("--name")
    ap.add_argument("--friend-name")
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
    item = args.item or rng.choice(list(ITEMS))
    if item not in ITEMS:
        raise StoryError("Unknown item.")
    name = args.name or rng.choice(NAMES)
    friend = args.friend_name or rng.choice([n for n in FRIENDS if n != name])
    return StoryParams(place="apartment_courtyard", item=item, name=name, friend_name=friend)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    item = f["item"]
    friend = f["friend"]
    return [
        f"Write a fairy tale about a chap in an apartment courtyard who must learn friendship, rhyme, and sharing.",
        f"Tell a gentle story where {hero.label} keeps a {item.label} too tightly until {friend.label} says pardon.",
        f"Write a child-friendly tale in which a chap and a friend turn a lonely rhyme into a shared one.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.get("hero")
    friend = world.get("friend")
    item = world.get("item")
    return [
        QAItem(
            question=f"Where does the story happen?",
            answer="The story happens in the apartment courtyard, beside the ivy wall and the stone bench.",
        ),
        QAItem(
            question=f"What did {hero.label} not want to do at first?",
            answer=f"At first, {hero.label} did not want to share the {item.label} with {friend.label}.",
        ),
        QAItem(
            question=f"What word did {friend.label} say before asking to join in?",
            answer='She said, "Pardon," before asking to share and rhyme together.',
        ),
        QAItem(
            question=f"What changed by the end?",
            answer=f"By the end, {hero.label} shared the {item.label}, and the two friends made the rhyme sweeter together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is sharing?",
            answer="Sharing means letting someone else use or enjoy something with you instead of keeping it all for yourself.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a pair of words or lines that sound alike at the end, which makes songs and poems fun to hear.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is a kind bond between people who care about each other and like spending time together.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== Prompts ==", *[f"- {p}" for p in sample.prompts], "", "== Story QA =="]
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    parts.append("")
    parts.append("== World QA ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(
            f"{e.id}: kind={e.kind} type={e.type} meters={ {k:v for k,v in e.meters.items() if v} } memes={ {k:v for k,v in e.memes.items() if v} }"
        )
    return "\n".join(lines)


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


def asp_verify_wrapper() -> int:
    return asp_verify()


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify_wrapper())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:")
        for place, item in combos:
            print(f"  {place}  {item}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(StoryParams(place="apartment_courtyard", item=item, name="Pip", friend_name="Luna")) for item in ITEMS]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
