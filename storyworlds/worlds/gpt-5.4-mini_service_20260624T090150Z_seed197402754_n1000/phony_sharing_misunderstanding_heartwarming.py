#!/usr/bin/env python3
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


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    shared_with: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str
    vibe: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Gift:
    id: str
    label: str
    phrase: str
    value: str
    delight: str


@dataclass
class ShareItem:
    id: str
    label: str
    phrase: str
    type: str
    cherished_by: set[str]
    share_kind: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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


@dataclass
class StoryParams:
    setting: str
    gift: str
    item: str
    name: str
    gender: str
    friend: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "kitchen": Setting(place="the kitchen", vibe="warm", affords={"sharing"}),
    "playroom": Setting(place="the playroom", vibe="cozy", affords={"sharing"}),
    "garden": Setting(place="the garden", vibe="bright", affords={"sharing"}),
}

GIFTS = {
    "cookies": Gift("cookies", "cookies", "a plate of cookies", "sweet", "smile"),
    "blanket": Gift("blanket", "blanket", "a soft blanket", "soft", "snuggle"),
    "crayons": Gift("crayons", "crayons", "a box of crayons", "colorful", "draw"),
}

ITEMS = {
    "toy": ShareItem("toy", "toy", "a favorite toy", "toy", {"girl", "boy"}, "play"),
    "book": ShareItem("book", "book", "a picture book", "book", {"girl", "boy"}, "read"),
    "swing": ShareItem("swing", "swing", "a backyard swing", "swing", {"girl", "boy"}, "take turns"),
}

GIRL_NAMES = ["Mia", "Lena", "Nora", "Ava", "Ruby", "Zoe"]
BOY_NAMES = ["Leo", "Ben", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["gentle", "curious", "careful", "kind", "patient"]


class ReasonableGate:
    @staticmethod
    def valid(setting: Setting, gift: Gift, item: ShareItem) -> bool:
        return "sharing" in setting.affords and item.type in {"toy", "book", "swing"} and gift.value in {"sweet", "soft", "colorful"}

    @staticmethod
    def explain(setting: Setting, gift: Gift, item: ShareItem) -> str:
        return (
            f"(No story: {gift.label} and {item.label} do not make a believable sharing scene "
            f"in {setting.place}. Please choose a different combination.)"
        )


def world_state(world: World) -> dict[str, Entity]:
    return world.entities


def add_memes(ent: Entity, **kwargs) -> None:
    for k, v in kwargs.items():
        ent.memes[k] = ent.memes.get(k, 0.0) + v


def add_meters(ent: Entity, **kwargs) -> None:
    for k, v in kwargs.items():
        ent.meters[k] = ent.meters.get(k, 0.0) + v


def tell(setting: Setting, gift: Gift, item: ShareItem, hero_name: str, hero_type: str, friend_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    friend = world.add(Entity(id="Friend", kind="character", type=friend_type, label="the friend"))
    present = world.add(Entity(id="gift", type=gift.id, label=gift.label, phrase=gift.phrase, owner=hero.id))
    share_item = world.add(Entity(id="item", type=item.type, label=item.label, phrase=item.phrase, owner=hero.id))

    world.say(f"{hero.id} was a {trait} little {hero.type} who loved {gift.delight} things and quiet afternoons.")
    world.say(f"One day, {hero.id}'s {friend.label} brought {present.phrase}, and {hero.id} also had {share_item.phrase}.")
    world.say(f"{hero.id} wanted to share everything, because sharing made the room feel bigger and kinder.")

    world.para()
    add_memes(hero, joy=1)
    add_memes(friend, hope=1)
    if item.id == "toy":
        world.say(f"They sat on a soft rug in {world.setting.place}.")
    elif item.id == "book":
        world.say(f"They settled at a little table in {world.setting.place}.")
    else:
        world.say(f"They paused together in {world.setting.place}, with sunshine making the edges of things glow.")

    world.say(f"Then a misunderstanding popped up like a tiny bump in a smooth road.")
    add_memes(friend, confusion=1)
    add_memes(hero, worry=1)

    world.say(
        f"When {hero.id} handed over {present.label}, {friend.pronoun('subject')} thought {hero.id} meant to keep the {share_item.label} all to {hero.id}."
    )
    world.say(
        f"{hero.id} looked sad for a moment, because that was phony to the real wish in {hero.pronoun('possessive')} heart."
    )

    world.para()
    add_memes(hero, honesty=1)
    world.say(
        f"So {hero.id} said, 'Oh no, I mean to share it with you. I was trying to be kind, not tricky.'"
    )
    add_memes(friend, relief=1)
    add_memes(friend, joy=1)
    add_memes(hero, love=1)
    add_memes(hero, worry=-1)
    add_memes(friend, confusion=-1)
    share_item.shared_with = friend.id
    present.shared_with = friend.id
    add_meters(share_item, shared=1)
    add_meters(present, shared=1)

    if item.id == "book":
        world.say(
            f"Then they opened the {share_item.label} together and pointed to the pictures one by one."
        )
    elif item.id == "toy":
        world.say(
            f"Then they took turns with the {share_item.label}, each waiting politely for a turn."
        )
    else:
        world.say(
            f"Then they shared the {share_item.label}, tucking it around both of them like a tiny warm cloud."
        )
    world.say(
        f"Soon both children were smiling, and {world.setting.place} felt warm and safe again."
    )

    world.facts.update(
        hero=hero,
        friend=friend,
        gift=present,
        item=share_item,
        gift_cfg=gift,
        item_cfg=item,
        setting=setting,
        trait=trait,
        misunderstanding=True,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        f'Write a heartwarming story for a child named {hero.id} about sharing and a small misunderstanding.',
        f"Tell a gentle story where {hero.id} seems phony for a moment, then explains the truth and shares kindly.",
        f"Write a short story set in {world.setting.place} where two children misunderstand a shared thing and then fix it.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    item = f["item"]
    gift = f["gift"]
    trait = f["trait"]
    return [
        QAItem(
            question=f"What kind of child was {hero.id}?",
            answer=f"{hero.id} was a {trait} little {hero.type} who wanted to share kindly.",
        ),
        QAItem(
            question=f"What did {hero.id} and {friend.label} misunderstand?",
            answer=f"They misunderstood who the {item.label} was for, but {hero.id} explained that it was meant to be shared.",
        ),
        QAItem(
            question=f"What did {hero.id} do after the misunderstanding?",
            answer=f"{hero.id} spoke honestly, shared the {item.label}, and turned the moment into a happy one.",
        ),
        QAItem(
            question=f"Why did the story mention something phony?",
            answer=f"It was phony because the misunderstanding made {hero.id} seem tricky for a moment, but {hero.id} was really trying to be kind.",
        ),
        QAItem(
            question=f"What was the warm ending image in the story?",
            answer=f"{hero.id} and {friend.label} shared the {item.label} and smiled together in {world.setting.place}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is sharing?",
            answer="Sharing means letting someone else use, hold, or enjoy something with you.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when people think something different from what was meant.",
        ),
        QAItem(
            question="Why is it good to tell the truth during a misunderstanding?",
            answer="Telling the truth helps everyone understand each other and feel better again.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.shared_with:
            bits.append(f"shared_with={e.shared_with}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
misunderstanding(H,F) :- hears(H,F), unsure(H,F), not clarified(H,F).
shared(Item,H,F) :- sharing(Item,H), sharing(Item,F), together(H,F).
heartwarming(H,F) :- clarified(H,F), shared(_,H,F), happy(H), happy(F).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("affords", sid, "sharing"))
    for gid, g in GIFTS.items():
        lines.append(asp.fact("gift", gid))
        lines.append(asp.fact("sweet", gid, g.value))
    for iid, it in ITEMS.items():
        lines.append(asp.fact("share_item", iid))
        for g in sorted(it.cherished_by):
            lines.append(asp.fact("cherished_by", iid, g))
        lines.append(asp.fact("share_kind", iid, it.share_kind))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(sorted(SETTINGS))
    gift = args.gift or rng.choice(sorted(GIFTS))
    item = args.item or rng.choice(sorted(ITEMS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    friend = args.friend or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    if not ReasonableGate.valid(SETTINGS[setting], GIFTS[gift], ITEMS[item]):
        raise StoryError(ReasonableGate.explain(SETTINGS[setting], GIFTS[gift], ITEMS[item]))
    return StoryParams(setting=setting, gift=gift, item=item, name=name, gender=gender, friend=friend, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        GIFTS[params.gift],
        ITEMS[params.item],
        params.name,
        params.gender,
        params.friend,
        params.trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming sharing storyworld with a small misunderstanding.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--friend", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
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
    StoryParams(setting="kitchen", gift="cookies", item="book", name="Mia", gender="girl", friend="mother", trait="kind"),
    StoryParams(setting="playroom", gift="blanket", item="toy", name="Leo", gender="boy", friend="father", trait="gentle"),
    StoryParams(setting="garden", gift="crayons", item="swing", name="Nora", gender="girl", friend="mother", trait="careful"),
]


def verify() -> int:
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show misunderstanding/2.\n#show shared/3.\n#show heartwarming/2."))
        return
    if args.verify:
        sys.exit(verify())
    if args.asp:
        print("ASP mode is available via the inline rules in this file.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
