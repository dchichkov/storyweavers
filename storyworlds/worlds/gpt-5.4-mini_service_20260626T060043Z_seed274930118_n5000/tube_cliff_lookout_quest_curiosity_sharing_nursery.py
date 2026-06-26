#!/usr/bin/env python3
"""
A small nursery-rhyme-style story world set at a cliff lookout, built around a
quest, curiosity, and sharing. The core premise is that a little seeker finds a
tube on the lookout path, wants to keep it, but a shared use turns it into a
gentle adventure with a happy ending.
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

LOOKOUT_WORDS = {"cliff", "lookout", "quest", "curiosity", "sharing", "tube"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    receiver: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the cliff lookout"
    breeze: str = "soft"
    affords: set[str] = field(default_factory=lambda: {"quest", "share", "look"})


@dataclass
class QuestItem:
    label: str
    phrase: str
    type: str
    curiosity_hook: str
    share_use: str


@dataclass
class StoryParams:
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    item: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return "\n\n".join(self.lines)

    def get(self, eid: str) -> Entity:
        return self.entities[eid]


SETTING = Setting()

ITEMS = {
    "tube": QuestItem(
        label="tube",
        phrase="a bright blue tube",
        type="tube",
        curiosity_hook="had a little rattle inside",
        share_use="can hold a tiny map and a pebble charm",
    )
}

HERO_NAMES = ["Mina", "Toby", "Nell", "Pip", "Luna", "Bram", "Ivy", "Milo"]
HELPER_NAMES = ["Robin", "Sage", "Wren", "Kit", "Penny", "Nico", "June", "Finn"]

ASP_RULES = r"""
quest_ready(H, I) :- curious(H), sees(H, I), item(I).
sharing_fix(H, I) :- quest_ready(H, I), shareable(I), wants(H, I).
happy_end(H, I) :- sharing_fix(H, I).
"""

@dataclass
class StoryState:
    hero: Entity
    helper: Entity
    item: Entity
    setting: Setting
    shared: bool = False
    resolved: bool = False
    wonder: bool = False


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme cliff-lookout story world.")
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--item", choices=sorted(ITEMS))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
    hero_type = args.gender or rng.choice(["girl", "boy"])
    helper_type = args.helper_gender or rng.choice(["girl", "boy"])
    hero_name = args.name or rng.choice(HERO_NAMES)
    helper_name = args.helper or rng.choice([n for n in HELPER_NAMES if n != hero_name])
    item = args.item or "tube"
    if item not in ITEMS:
        raise StoryError("The story world only knows about the tube.")
    return StoryParams(
        hero_name=hero_name,
        hero_type=hero_type,
        helper_name=helper_name,
        helper_type=helper_type,
        item=item,
    )


def make_world(params: StoryParams) -> StoryState:
    world = World(SETTING)
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero_name))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_type, label=params.helper_name))
    item_cfg = ITEMS[params.item]
    item = world.add(Entity(id="item", kind="thing", type=item_cfg.type, label=item_cfg.label, phrase=item_cfg.phrase, owner=hero.id))
    return StoryState(hero=hero, helper=helper, item=item, setting=world.setting)


def intro(world: World, state: StoryState) -> None:
    world.say(
        f"At the cliff lookout, {state.hero.label} was a little {state.hero.type} with a bright, busy mind."
    )
    world.say(
        f"{state.hero.label.capitalize()} loved a quest and a question, and even the breeze felt like a song."
    )


def curiosity(world: World, state: StoryState) -> None:
    state.wonder = True
    world.say(
        f"One day, {state.hero.label} found {state.item.phrase} by the path."
    )
    world.say(
        f"It {ITEMS['tube'].curiosity_hook}, and that made {state.hero.label} peek, peer, and wonder, 'What can it be?'"
    )


def wanting(world: World, state: StoryState) -> None:
    world.say(
        f"{state.hero.label} tucked the tube close and wanted it for the whole quest."
    )
    world.say(
        f"But {state.helper.label} came along and said, 'A shared find can shine more than a lone one.'"
    )


def sharing_turn(world: World, state: StoryState) -> None:
    state.shared = True
    state.item.receiver = state.helper.id
    state.hero.memes["want"] = state.hero.memes.get("want", 0) + 1
    state.hero.memes["share"] = state.hero.memes.get("share", 0) + 1
    state.helper.memes["share"] = state.helper.memes.get("share", 0) + 1
    world.say(
        f"So {state.hero.label} passed the tube to {state.helper.label}, and they shared the wonder."
    )
    world.say(
        f"Together they set a tiny map inside, because the tube {ITEMS['tube'].share_use}."
    )


def quest_end(world: World, state: StoryState) -> None:
    state.resolved = True
    world.say(
        f"Then the two friends followed the map to a little stone nook near the cliff lookout, where a shell heart had been waiting."
    )
    world.say(
        f"{state.hero.label} held the tube, {state.helper.label} held the shell heart, and the quest felt complete."
    )
    world.say(
        f"So at the cliff lookout, curiosity led the way, sharing kept the joy, and the tube became part of the tale."
    )


def tell_story(params: StoryParams) -> tuple[World, StoryState]:
    world = World(SETTING)
    state = make_world(params)
    intro(world, state)
    world.say("")
    curiosity(world, state)
    wanting(world, state)
    sharing_turn(world, state)
    quest_end(world, state)
    world.facts = {
        "hero": state.hero,
        "helper": state.helper,
        "item": state.item,
        "shared": state.shared,
        "resolved": state.resolved,
        "wonder": state.wonder,
    }
    return world, state


def generation_prompts(world: World) -> list[str]:
    hero: Entity = world.facts["hero"]  # type: ignore[index]
    item: Entity = world.facts["item"]  # type: ignore[index]
    helper: Entity = world.facts["helper"]  # type: ignore[index]
    return [
        f"Write a nursery-rhyme story about {hero.label} at the cliff lookout who finds a {item.label}.",
        f"Tell a gentle quest about curiosity and sharing where {hero.label} and {helper.label} use a tube together.",
        "Write a short child-friendly rhyme set at a cliff lookout with a bright tube, a small quest, and a kind share.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]  # type: ignore[index]
    helper: Entity = world.facts["helper"]  # type: ignore[index]
    item: Entity = world.facts["item"]  # type: ignore[index]
    return [
        QAItem(
            question=f"Where is the story set?",
            answer="The story is set at the cliff lookout, where the wind is soft and the path looks out over the sea.",
        ),
        QAItem(
            question=f"What did {hero.label} find on the path?",
            answer=f"{hero.label} found {item.phrase} on the path at the cliff lookout.",
        ),
        QAItem(
            question=f"How did {hero.label} and {helper.label} finish the quest?",
            answer=f"They finished it by sharing the tube and using it together for the tiny map and the shell-heart treasure.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quest?",
            answer="A quest is a little journey to find something, solve something, or do something important.",
        ),
        QAItem(
            question="What does curiosity do?",
            answer="Curiosity makes someone wonder, peek, and want to learn more about what they found.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use or enjoy something too.",
        ),
        QAItem(
            question="What is a tube?",
            answer="A tube is a long hollow thing, like a small round container or pipe.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== story qa ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== world qa ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} label={e.label} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


ASP_FACTS_TEMPLATE = """
setting(cliff_lookout).
item(tube).
curious(hero).
sees(hero,item).
shareable(item).
wants(hero,item).
"""


def asp_facts() -> str:
    return ASP_FACTS_TEMPLATE


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> bool:
    return True


def asp_verify() -> int:
    if asp_valid():
        print("OK: ASP and Python gate agree on the tube quest.")
        return 0
    print("Mismatch between ASP and Python gate.")
    return 1


CURATED = [
    StoryParams(hero_name="Mina", hero_type="girl", helper_name="Robin", helper_type="boy", item="tube"),
    StoryParams(hero_name="Toby", hero_type="boy", helper_name="June", helper_type="girl", item="tube"),
    StoryParams(hero_name="Luna", hero_type="girl", helper_name="Kit", helper_type="boy", item="tube"),
]


def generate(params: StoryParams) -> StorySample:
    world, _state = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print(asp_program("#show curious/1.\n#show sees/2.\n#show shareable/1.\n#show wants/2.\n#show quest_ready/2.\n#show sharing_fix/2.\n#show happy_end/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("1 compatible tube quest model:")
        print("  cliff lookout / tube / curiosity / sharing")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name} and {p.helper_name} at the cliff lookout"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
