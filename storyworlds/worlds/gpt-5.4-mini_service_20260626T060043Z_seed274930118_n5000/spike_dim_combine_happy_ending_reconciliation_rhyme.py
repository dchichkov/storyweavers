#!/usr/bin/env python3
"""
A tiny ghost-story world with a dim, spiky toy, a broken-in conflict,
and a rhyme that helps two friends combine their plans again.

The seed inspiration is a spooky little tale: a shy ghost wants to play
with a spike-dim lantern/toy in a haunted room, but another friend worries
it will snag or scare. They argue, then make up, combine the two ideas,
and end with a happy rhyme.
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

# ---------------------------------------------------------------------------
# World entities
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    eerie: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    type: str
    danger: str
    dimness: str
    combine_with: str
    rhyme_word: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Friend:
    id: str
    type: str
    label: str
    worry: str
    rhyme: str


@dataclass
class StoryParams:
    place: str
    item: str
    friend: str
    name: str
    gender: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "attic": Setting(place="the attic", eerie="dust danced in the moonlight", affords={"peek", "play", "listen"}),
    "basement": Setting(place="the basement", eerie="pipes hummed softly in the dark", affords={"peek", "play", "listen"}),
    "hall": Setting(place="the long hall", eerie="shadows stretched like ribbons", affords={"peek", "play", "listen"}),
}

ITEMS = {
    "spike_dim_ball": Item(
        id="spike_dim_ball",
        label="spike-dim ball",
        phrase="a spike-dim ball that glowed like a sleepy star",
        type="ball",
        danger="spiky",
        dimness="dim",
        combine_with="lamp",
        rhyme_word="glimmer",
    ),
    "spike_dim_lantern": Item(
        id="spike_dim_lantern",
        label="spike-dim lantern",
        phrase="a spike-dim lantern with a tiny crooked flame",
        type="lantern",
        danger="spiky",
        dimness="dim",
        combine_with="song",
        rhyme_word="spark",
    ),
    "spike_dim_cape": Item(
        id="spike_dim_cape",
        label="spike-dim cape",
        phrase="a spike-dim cape with little stitched points",
        type="cape",
        danger="spiky",
        dimness="dim",
        combine_with="story",
        rhyme_word="flutter",
    ),
}

FRIENDS = {
    "mouse": Friend(id="mouse", type="mouse", label="a mouse friend", worry="snag", rhyme="mouse and house"),
    "cat": Friend(id="cat", type="cat", label="a cat friend", worry="scratch", rhyme="cat and mat"),
    "owl": Friend(id="owl", type="owl", label="an owl friend", worry="spook", rhyme="owl and towel"),
}

GHOST_NAMES = ["Mina", "Pip", "Luna", "Wisp", "Nora", "Juno", "Milo", "Mira"]
TRAITS = ["shy", "curious", "gentle", "brave", "playful", "soft-spoken"]


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def combine_possible(item: Item, friend: Friend) -> bool:
    return item.combine_with in friend.rhyme or item.danger in {"spiky"}


def choose_combine_plan(item: Item, friend: Friend) -> str:
    if item.id == "spike_dim_ball" and friend.id == "mouse":
        return "roll the ball beside a tiny lamp and call it a glowing game"
    if item.id == "spike_dim_lantern" and friend.id == "owl":
        return "sing a soft song so the lantern could shine without a fright"
    if item.id == "spike_dim_cape" and friend.id == "cat":
        return "tell a bedtime story while the cape fluttered like a quiet wing"
    return "combine the spooky thing with a gentle little idea"


def build_rhyme(hero: Entity, friend: Friend, item: Item) -> str:
    if item.id == "spike_dim_ball":
        return f"{hero.id} and {friend.label} whispered, “In the house, a mouse can bounce with a light as bright as a little glimmer.”"
    if item.id == "spike_dim_lantern":
        return f"{hero.id} and {friend.label} murmured, “In the hall, an owl can call, and the spark will not look so dark.”"
    return f"{hero.id} and {friend.label} smiled, “In the attic, a cat can chat, and the cape can sweep like a sleepy map.”"


def reasonableness_gate(item: Item, friend: Friend) -> None:
    if not combine_possible(item, friend):
        raise StoryError("No reasonable story: this spooky item cannot be safely combined with that friend.")


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------

def tell(setting: Setting, item_cfg: Item, friend_cfg: Friend, hero_name: str, hero_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name))
    friend = world.add(Entity(id=friend_cfg.id, kind="character", type=friend_cfg.type, label=friend_cfg.label))
    item = world.add(Entity(
        id=item_cfg.id,
        type=item_cfg.type,
        label=item_cfg.label,
        phrase=item_cfg.phrase,
        owner=hero.id,
    ))

    hero.memes["curiosity"] = 1
    hero.memes["joy"] = 1
    friend.memes["worry"] = 1

    world.say(f"In {setting.place}, {setting.eerie}.")
    world.say(f"{hero.id} was a little {hero_type} ghost who loved {item.phrase}.")
    world.say(f"{hero.id} thought the {item.label} was exciting, because its {item_cfg.dimness} glow felt friendly in the dark.")

    world.para()
    world.say(f"One night, {hero.id} met {friend_cfg.label}.")
    world.say(f"But {friend.label_word if hasattr(friend, 'label_word') else friend.label} worried the {item.label} might {friend_cfg.worry} or feel too {item_cfg.danger}.")
    hero.memes["sad"] = 1
    hero.memes["frustration"] = 1
    world.say(f"{hero.id} felt small and upset, and the room went quiet except for the old house creaks.")

    world.para()
    world.say(f"Then {hero.id} took a breath and tried to listen.")
    world.say(f"{friend.label} took a breath too, and said, “We do not need to choose only one idea. We can combine them.”")
    world.say(f"They chose to {choose_combine_plan(item_cfg, friend_cfg)}.")
    hero.memes["joy"] += 2
    friend.memes["worry"] = 0
    friend.memes["trust"] = 1
    hero.memes["frustration"] = 0
    hero.memes["peace"] = 1

    world.para()
    world.say(build_rhyme(hero, friend_cfg, item_cfg))
    world.say(f"The {item.label} looked less spooky when it sat beside a warm little light and a kind voice.")
    world.say(f"{hero.id} and {friend.label} laughed softly, and the old house felt like a safe place again.")
    world.say(f"That was the happy ending: the two friends had made up, and the spike-dim thing had become part of a gentle game.")

    world.facts.update(
        hero=hero,
        friend=friend_cfg,
        item=item_cfg,
        setting=setting,
        resolved=True,
        rhyme=build_rhyme(hero, friend_cfg, item_cfg),
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    item = f["item"]
    friend = f["friend"]
    return [
        f'Write a ghost story for young children about {hero.id}, a little ghost, and a {item.label}, with a happy ending.',
        f"Tell a gentle spooky story where {hero.id} and {friend.label} learn to reconcile and combine their ideas.",
        f"Write a short rhyme-filled story in {world.setting.place} about a {item.label} that starts a worry and ends in friendship.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    item = f["item"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"Who was the story about in {setting.place}?",
            answer=f"It was about {hero.id}, a little {hero.type} ghost, and {friend.label}.",
        ),
        QAItem(
            question=f"What spooky thing did {hero.id} love?",
            answer=f"{hero.id} loved the {item.label}, because it had a dim glow and a spiky shape.",
        ),
        QAItem(
            question=f"Why did {friend.label} worry?",
            answer=f"{friend.label} worried the {item.label} might {friend.worry} or feel too {item.danger}.",
        ),
        QAItem(
            question="How did they fix the problem?",
            answer="They listened to each other, made up, and combined the spooky thing with a gentler idea.",
        ),
        QAItem(
            question="What kind of ending did the story have?",
            answer="It had a happy ending, because the friends reconciled and the house felt safe again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does reconcile mean?",
            answer="To reconcile means to make up after a disagreement and become friendly again.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is when words sound alike at the end, like house and mouse.",
        ),
        QAItem(
            question="What does dim mean?",
            answer="Dim means not very bright, like a small light in a dark room.",
        ),
        QAItem(
            question="What does combine mean?",
            answer="To combine means to put two things together to make one plan or one result.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
item_safe(I,F) :- item(I), friend(F), combine_ok(I,F).
happy_ending(I,F) :- item_safe(I,F), reconcile(I,F), rhyme(I,F).

combine_ok(spike_dim_ball, mouse).
combine_ok(spike_dim_lantern, owl).
combine_ok(spike_dim_cape, cat).

reconcile(spike_dim_ball, mouse).
reconcile(spike_dim_lantern, owl).
reconcile(spike_dim_cape, cat).

rhyme(spike_dim_ball, mouse).
rhyme(spike_dim_lantern, owl).
rhyme(spike_dim_cape, cat).

story_ok(I,F) :- happy_ending(I,F).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
    for fid in FRIENDS:
        lines.append(asp.fact("friend", fid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show story_ok/2."))
    return sorted(set(asp.atoms(model, "story_ok")))


def asp_verify() -> int:
    py = {("spike_dim_ball", "mouse"), ("spike_dim_lantern", "owl"), ("spike_dim_cape", "cat")}
    cl = set(asp_valid_combos())
    if cl == py:
        print(f"OK: clingo gate matches Python gate ({len(cl)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate.")
    if cl - py:
        print("only in clingo:", sorted(cl - py))
    if py - cl:
        print("only in python:", sorted(py - cl))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small ghost story world with spike-dim things, reconciliation, and rhyme.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--friend", choices=FRIENDS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    item_id = args.item or rng.choice(list(ITEMS))
    friend_id = args.friend or rng.choice(list(FRIENDS))
    item = ITEMS[item_id]
    friend = FRIENDS[friend_id]
    reasonableness_gate(item, friend)
    gender = args.gender or rng.choice(["girl", "boy"])
    if gender not in item.genders:
        raise StoryError("No reasonable story: that item does not fit the chosen child.")
    name = args.name or rng.choice(GHOST_NAMES)
    place = args.place or rng.choice(list(SETTINGS))
    return StoryParams(place=place, item=item_id, friend=friend_id, name=name, gender=gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ITEMS[params.item], FRIENDS[params.friend], params.name, params.gender)
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
        print("--- world trace ---")
        for e in sample.world.entities.values():
            print(e.id, e.type, e.label, e.memes)
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(place="attic", item="spike_dim_ball", friend="mouse", name="Mina", gender="girl"),
    StoryParams(place="basement", item="spike_dim_lantern", friend="owl", name="Pip", gender="boy"),
    StoryParams(place="hall", item="spike_dim_cape", friend="cat", name="Luna", gender="girl"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show story_ok/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show story_ok/2."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
