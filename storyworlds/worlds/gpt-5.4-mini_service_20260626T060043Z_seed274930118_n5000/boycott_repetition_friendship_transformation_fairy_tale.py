#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/boycott_repetition_friendship_transformation_fairy_tale.py
================================================================================================

A small fairy-tale story world about a child, a friendship, a boycott, and a
gentle transformation.

The premise is simple: a village is upset by a greedy seller who keeps offering
a sour, unfair treat. The child and a new friend begin a boycott. Through a
repeated refrain and a kind act, the greedy seller changes, and the village
learns that a boycott can end when fairness returns.

The world is intentionally small and constraint-checked:
- boycott must be meaningful
- friendship must matter
- repetition must be visible in the prose
- transformation must happen by the end
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


@dataclass
class Character:
    id: str
    kind: str = "character"
    type: str = "person"
    label: str = ""
    role: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def name(self) -> str:
        return self.label or self.id


@dataclass
class Setting:
    place: str
    village_name: str
    season: str
    mood: str


@dataclass
class ObjectOfBoycott:
    label: str
    phrase: str
    unfair_reason: str
    fair_version: str
    repeated_line: str
    symbol: str


@dataclass
class FriendBond:
    child_friendly_name: str
    friend_name: str
    friend_type: str
    helper_gift: str
    promise: str
    shared_action: str


@dataclass
class Transformation:
    before: str
    after: str
    trigger: str
    visible_sign: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Character] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.trace: list[str] = []

    def add(self, entity: Character) -> Character:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    setting: str
    boycott_item: str
    child: str
    friend: str
    seed: Optional[int] = None


SETTINGS = {
    "moss_village": Setting(
        place="Moss Village",
        village_name="Moss Village",
        season="spring",
        mood="quiet",
    ),
    "silver_ford": Setting(
        place="Silver Ford",
        village_name="Silver Ford",
        season="autumn",
        mood="windy",
    ),
    "rose_hollow": Setting(
        place="Rose Hollow",
        village_name="Rose Hollow",
        season="summer",
        mood="golden",
    ),
}

BOYCOTTS = {
    "moon_cakes": ObjectOfBoycott(
        label="moon cakes",
        phrase="sweet moon cakes with too much sugar and no fairness",
        unfair_reason="the baker charged a coin from every child but gave the biggest cakes to the richest table",
        fair_version="small moon cakes for every child",
        repeated_line="No coin, no moon cake, until the baking is fair.",
        symbol="moon",
    ),
    "honey_buns": ObjectOfBoycott(
        label="honey buns",
        phrase="sticky honey buns that were always counted wrong",
        unfair_reason="the seller kept one bun back for herself and called it a mistake",
        fair_version="honey buns shared evenly on a wooden tray",
        repeated_line="No sharing, no honey bun, until the counting is fair.",
        symbol="honey",
    ),
    "starlight_jam": ObjectOfBoycott(
        label="starlight jam",
        phrase="shiny jars of starlight jam that were priced far too high",
        unfair_reason="the jar was made with a spell, but only the seller was allowed to taste it",
        fair_version="starlight jam for every family spoon",
        repeated_line="No fairness, no starlight jam, until the tables are right.",
        symbol="star",
    ),
}

FRIENDSHIPS = {
    "fox": FriendBond(
        child_friendly_name="child",
        friend_name="Brindle",
        friend_type="fox",
        helper_gift="a lantern woven from reeds",
        promise="We will stay side by side and keep the boycott gentle.",
        shared_action="walked the lane together and spoke to every doorway",
    ),
    "goat": FriendBond(
        child_friendly_name="child",
        friend_name="Merry",
        friend_type="goat",
        helper_gift="a basket tied with blue ribbon",
        promise="We will be brave together and ask for a fair bargain.",
        shared_action="tapped every gate and invited the neighbors to listen",
    ),
    "moth": FriendBond(
        child_friendly_name="child",
        friend_name="Pip",
        friend_type="moth",
        helper_gift="a silver thread to sew signs",
        promise="We will remember the reason until the town chooses kindness.",
        shared_action="hung little signs on branches and windows",
    ),
}

TRANSFORMATIONS = {
    "baker": Transformation(
        before="greedy and red-faced",
        after="warm and fair",
        trigger="he saw nobody came to the stall and heard the repeated words from the lane",
        visible_sign="the baker's sour brow softened like dough in warm water",
    ),
    "seller": Transformation(
        before="sharp-tongued and proud",
        after="gentle and honest",
        trigger="she realized the village had chosen not to buy until the prices were right",
        visible_sign="her stiff shoulders loosened and her smile grew rounder",
    ),
}

GIRL_NAMES = ["Mina", "Lina", "Suri", "Nora", "Elsa"]
BOY_NAMES = ["Tobin", "Elias", "Rowan", "Pip", "Oren"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for boycott_item in BOYCOTTS:
            for friend in FRIENDSHIPS:
                combos.append((setting, boycott_item, friend))
    return combos


def choose_name(gender: str, rng: random.Random) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def is_meaningful(setting: Setting, item: ObjectOfBoycott) -> bool:
    return bool(setting.place and item.unfair_reason and item.repeated_line)


def reasonableness_gate(setting: Setting, item: ObjectOfBoycott, friendship: FriendBond) -> None:
    if not is_meaningful(setting, item):
        raise StoryError("The boycott must have a clear unfairness and a clear repeated refrain.")
    if friendship.friend_name == "":
        raise StoryError("A friendship is required to carry the boycott story forward.")


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    item = BOYCOTTS[params.boycott_item]
    friend = FRIENDSHIPS[params.friend]
    rng = random.Random(params.seed or 0)

    reasonableness_gate(setting, item, friend)

    world = World(setting)
    child = world.add(Character(id=params.child, type="child", label=params.child, role="hero"))
    ally = world.add(Character(id=friend.friend_name, type=friend.friend_type, label=friend.friend_name, role="friend"))
    seller = world.add(Character(id="seller", type="seller", label="the baker", role="seller"))

    transformation = TRANSFORMATIONS["baker"]

    world.facts.update(
        child=child,
        ally=ally,
        seller=seller,
        item=item,
        friend=friend,
        transformation=transformation,
        setting=setting,
    )

    child.memes["care"] = 1
    ally.memes["care"] = 1
    seller.memes["greed"] = 1
    seller.memes["pride"] = 1

    # Act 1: the problem.
    world.say(
        f"In {setting.place}, under a {setting.season} sky, there was a little {child.type} named {child.name()} who loved sweet treats and honest promises."
    )
    world.say(
        f"Each market day, the village looked toward the stall of {seller.name()}, because {item.phrase} seemed bright but was never fair."
    )
    world.say(
        f"The people whispered that {item.unfair_reason}."
    )

    # Act 2: friendship and repeated boycott.
    world.para()
    world.say(
        f"Then {friend.friend_name}, a kind {friend.friend_type}, came to {child.name()} with {friend.helper_gift}."
    )
    world.say(friend.promise)
    world.say(
        f"Together they began a boycott. They did not shout or break anything; they simply chose not to buy."
    )
    world.say(
        f'"{item.repeated_line}" they said on Monday, and again on Tuesday, and again on Wednesday.'
    )
    world.say(
        f"{friend.shared_action.capitalize()}, while {child.name()} repeated the same small, steady words at every door."
    )

    # repeated state effect
    child.memes["resolve"] = 1
    ally.memes["resolve"] = 1
    seller.meters["empty_stall"] = 1
    seller.memes["worry"] = 1 + rng.random()

    # Act 3: transformation.
    world.para()
    world.say(
        f"By the third evening, {seller.name()} stood alone beside the stall, listening to the quiet."
    )
    world.say(
        f"{transformation.trigger}, and {transformation.visible_sign}."
    )
    seller.memes["greed"] = 0
    seller.memes["pride"] = 0
    seller.memes["kindness"] = 1
    seller.memes["gratitude"] = 1
    seller.label = "the baker, now a kinder baker"

    world.say(
        f"{seller.name()} bowed low and said that from then on there would be {item.fair_version} for everyone."
    )
    world.say(
        f"The boycott ended at once, and {child.name()} and {friend.friend_name} shared the first fair piece while the village laughed in relief."
    )
    world.say(
        f"That night, the moon over {setting.place} shone on a changed stall, a changed heart, and two friends walking home together."
    )

    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    item: ObjectOfBoycott = f["item"]  # type: ignore[assignment]
    friend: FriendBond = f["friend"]  # type: ignore[assignment]
    setting: Setting = f["setting"]  # type: ignore[assignment]
    return [
        f'Write a short fairy tale about a boycott in {setting.place} using the word "{item.label}".',
        f"Tell a gentle story where a child and {friend.friend_name} stay friends, repeat a refrain, and change an unfair market.",
        f"Write a child-friendly tale with repetition, friendship, and transformation that ends when fairness returns.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Character = f["child"]  # type: ignore[assignment]
    ally: Character = f["ally"]  # type: ignore[assignment]
    seller: Character = f["seller"]  # type: ignore[assignment]
    item: ObjectOfBoycott = f["item"]  # type: ignore[assignment]
    friend: FriendBond = f["friend"]  # type: ignore[assignment]
    setting: Setting = f["setting"]  # type: ignore[assignment]

    return [
        QAItem(
            question=f"Why did {child.name()} and {friend.friend_name} begin a boycott in {setting.place}?",
            answer=f"They began the boycott because {item.unfair_reason}. They wanted the stall to become fair for everyone.",
        ),
        QAItem(
            question=f"What repeated words did {child.name()} and {friend.friend_name} say while they boycotted {item.label}?",
            answer=f'They repeated: "{item.repeated_line}" They said it more than once so the village would remember the reason.',
        ),
        QAItem(
            question=f"How did the friendship help the boycott work?",
            answer=f"{friend.friend_name} brought support, courage, and a shared plan. With a friend beside them, {child.name()} could keep the boycott kind and steady.",
        ),
        QAItem(
            question=f"What changed after the boycott ended?",
            answer=f"The seller changed from greedy to fair, and the village could buy {item.fair_version}. The boycott ended because the unfairness was fixed.",
        ),
        QAItem(
            question=f"What did {seller.name()} become by the end of the story?",
            answer=f"{seller.name()} became warm and fair after hearing the village's repeated refusal to buy until things changed.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    f = world.facts
    item: ObjectOfBoycott = f["item"]  # type: ignore[assignment]
    friend: FriendBond = f["friend"]  # type: ignore[assignment]
    setting: Setting = f["setting"]  # type: ignore[assignment]
    trans: Transformation = f["transformation"]  # type: ignore[assignment]
    return [
        QAItem(
            question="What is a boycott?",
            answer="A boycott is when people choose not to buy or use something until a problem is made fair or right.",
        ),
        QAItem(
            question="Why can repetition help in a fairy tale?",
            answer="Repetition helps because the same words or actions can make an important message easy to remember.",
        ),
        QAItem(
            question=f"Why did {friend.friend_name} help the child in {setting.place}?",
            answer=f"{friend.friend_name} helped so the child would not face the problem alone. Friendship gave the boycott courage and patience.",
        ),
        QAItem(
            question=f"What kind of change did {trans.before} turn into?",
            answer=f"It turned into {trans.after}, which is a transformation from being unfair to being kind and honest.",
        ),
        QAItem(
            question=f"Why did the village stop the boycott in the end?",
            answer=f"The village stopped the boycott because the stall became fair, so there was no longer a reason to keep refusing the goods.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== (3) World knowledge questions ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: role={e.role}, type={e.type}, meters={e.meters}, memes={e.memes}")
    lines.append("story beats:")
    lines.extend(f"  - {t}" for t in world.trace)
    return "\n".join(lines)


ASP_RULES = r"""
setting(S) :- setting_fact(S).
item(I) :- item_fact(I).
friend(F) :- friend_fact(F).

valid_story(S, I, F) :- setting(S), item(I), friend(F), boycott_reason(I), friendship_help(F), transformation_possible(I).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting_fact", sid))
    for iid, item in BOYCOTTS.items():
        lines.append(asp.fact("item_fact", iid))
        lines.append(asp.fact("boycott_reason", iid))
        lines.append(asp.fact("transformation_possible", iid))
    for fid in FRIENDSHIPS:
        lines.append(asp.fact("friend_fact", fid))
        lines.append(asp.fact("friendship_help", fid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale story world about boycott, repetition, friendship, and transformation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--boycott-item", choices=BOYCOTTS)
    ap.add_argument("--friend", choices=FRIENDSHIPS)
    ap.add_argument("--child")
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
    combos = valid_combos()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.boycott_item:
        combos = [c for c in combos if c[1] == args.boycott_item]
    if args.friend:
        combos = [c for c in combos if c[2] == args.friend]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    setting, item, friend = rng.choice(sorted(combos))
    if args.child:
        child = args.child
    else:
        child = rng.choice(GIRL_NAMES + BOY_NAMES)
    return StoryParams(setting=setting, boycott_item=item, child=child, friend=friend)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, boycott_item, friend) combos:\n")
        for s, i, f in combos:
            print(f"  {s:14} {i:16} {f}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for setting in SETTINGS:
            for item in BOYCOTTS:
                for friend in FRIENDSHIPS:
                    params = StoryParams(setting=setting, boycott_item=item, child="Ayla", friend=friend, seed=base_seed)
                    samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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
        header = ""
        if len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
