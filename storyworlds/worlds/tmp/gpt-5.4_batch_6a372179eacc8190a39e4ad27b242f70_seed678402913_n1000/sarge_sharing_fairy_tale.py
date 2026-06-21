#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/sarge_sharing_fairy_tale.py
=====================================================

A standalone storyworld about Sarge, a small traveler in a fairy-tale forest,
who learns that sharing what he carries can open the way forward.

This world models one gentle pattern:

    Sarge sets out for a lovely place with a useful gift or snack.
    On the way, he meets a creature in need.
    He can only make a reasonable story when what he shares truly matches that need.
    Once comforted, the creature helps him through the last hard part of the journey.
    The ending proves the change: the path opens because Sarge shared.

Run it
------
    python storyworlds/worlds/gpt-5.4/sarge_sharing_fairy_tale.py
    python storyworlds/worlds/gpt-5.4/sarge_sharing_fairy_tale.py --gift honey_bun --need thirsty
    python storyworlds/worlds/gpt-5.4/sarge_sharing_fairy_tale.py --all
    python storyworlds/worlds/gpt-5.4/sarge_sharing_fairy_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/sarge_sharing_fairy_tale.py --verify
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "doe"}
        male = {"boy", "father", "man", "stag"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    id: str
    place: str
    opening: str
    obstacle: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gift:
    id: str
    label: str
    phrase: str
    kind: str
    give_verb: str
    carry_text: str
    comfort_text: str
    divisible: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Need:
    id: str
    label: str
    state_text: str
    relief_text: str
    kind: str
    tags: set[str] = field(default_factory=set)


@dataclass
class FriendType:
    id: str
    label: str
    phrase: str
    help_text: str
    thank_text: str
    tags: set[str] = field(default_factory=set)


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


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_share_soothes(world: World) -> list[str]:
    out: list[str] = []
    sarge = world.get("sarge")
    friend = world.get("friend")
    gift = world.get("gift")
    need = world.facts["need_cfg"]
    if friend.meters["shared_help"] < THRESHOLD:
        return out
    sig = ("soothe", need.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if gift.attrs.get("kind") == need.kind:
        friend.meters[need.id] = 0.0
        friend.meters["comfort"] += 1
        friend.memes["gratitude"] += 1
        sarge.memes["kindness"] += 1
        out.append("__soothed__")
    return out


def _r_gratitude_guides(world: World) -> list[str]:
    out: list[str] = []
    sarge = world.get("sarge")
    friend = world.get("friend")
    if friend.memes["gratitude"] < THRESHOLD:
        return out
    sig = ("guide", friend.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    sarge.meters["progress"] += 1
    sarge.memes["hope"] += 1
    friend.memes["trust"] += 1
    out.append("__guided__")
    return out


CAUSAL_RULES = [
    Rule(name="share_soothes", tag="social", apply=_r_share_soothes),
    Rule(name="gratitude_guides", tag="social", apply=_r_gratitude_guides),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            items = rule.apply(world)
            if items:
                changed = True
                produced.extend(items)
    if narrate:
        for text in produced:
            if not text.startswith("__"):
                world.say(text)
    return produced


def satisfies(gift: Gift, need: Need) -> bool:
    return gift.kind == need.kind


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for gift_id, gift in GIFTS.items():
            for friend_id in FRIENDS:
                for need_id, need in NEEDS.items():
                    if satisfies(gift, need):
                        combos.append((setting_id, gift_id, friend_id, need_id))
    return combos


def explain_rejection(gift: Gift, need: Need) -> str:
    return (
        f"(No story: sharing {gift.phrase} would not solve a {need.label} problem. "
        f"{gift.label.capitalize()} helps with {gift.kind}, but the friend needs help with "
        f"{need.kind}. Pick a matching gift instead.)"
    )


def predict_sharing(world: World, gift: Gift, need: Need) -> dict:
    sim = world.copy()
    sim.get("friend").meters[need.id] = 1
    sim.get("gift").attrs["kind"] = gift.kind
    sim.get("friend").meters["shared_help"] += 1
    propagate(sim, narrate=False)
    return {
        "soothed": sim.get("friend").meters[need.id] < THRESHOLD,
        "progress": sim.get("sarge").meters["progress"],
    }


def introduce(world: World, sarge: Entity, setting: Setting, gift: Gift, destination: Entity) -> None:
    sarge.memes["wonder"] += 1
    world.say(
        f"In {setting.place}, where moss shone softly and even the stones looked old and wise, "
        f"there lived a little traveler named {sarge.id}."
    )
    world.say(
        f"That morning {sarge.id} set out for {destination.label}, carrying {gift.phrase}. "
        f"{gift.carry_text}"
    )
    world.say(setting.opening)


def meet_friend(world: World, sarge: Entity, friend: Entity, need: Need) -> None:
    friend.meters[need.id] += 1
    sarge.memes["worry"] += 1
    world.say(
        f"Before long, {sarge.id} came to {world.setting.obstacle}. There {sarge.pronoun()} found "
        f"{friend.phrase}, who looked {need.state_text}."
    )
    world.say(
        f'"Oh dear," said {sarge.id}, "you look {need.label}.'
        f' What has happened?"'
    )


def explain_need(world: World, friend: Entity, need: Need) -> None:
    line = {
        "hungry": "I have not had even a crumb since the sun climbed over the trees.",
        "thirsty": "My little throat feels dry as dust, and the brook is too far below the bank.",
        "cold": "The wind slipped through the ferns, and now I cannot stop shivering.",
    }[need.id]
    world.say(f'"{line}" {friend.label} said.')


def consider(world: World, sarge: Entity, gift: Gift, need: Need) -> None:
    pred = predict_sharing(world, gift, need)
    world.facts["predicted_soothed"] = pred["soothed"]
    world.facts["predicted_progress"] = pred["progress"]
    sarge.memes["hesitation"] += 1
    world.say(
        f"{sarge.id} looked at {gift.phrase} in {sarge.pronoun('possessive')} paws and then at the "
        f"small creature by the path. {sarge.pronoun().capitalize()} had meant to keep it for the road."
    )
    if pred["soothed"]:
        world.say(
            f"But {sarge.pronoun()} could see that sharing it would truly help. A matching gift could "
            f"turn a hard moment into a hopeful one."
        )


def share(world: World, sarge: Entity, friend: Entity, gift: Gift, need: Need) -> None:
    world.get("gift").attrs["kind"] = gift.kind
    world.get("gift").meters["amount"] = 1.0
    world.get("gift").meters["shared"] += 1
    friend.meters["shared_help"] += 1
    sarge.meters["supplies"] -= 1
    propagate(world, narrate=False)
    world.say(
        f"So {sarge.id} knelt beside {friend.label} and {gift.give_verb}."
    )
    world.say(
        f"{friend.label.capitalize()} accepted it gently. {gift.comfort_text} {need.relief_text}"
    )


def thank_and_help(world: World, sarge: Entity, friend_cfg: FriendType, friend: Entity) -> None:
    world.say(friend_cfg.thank_text)
    world.say(
        f"Then {friend_cfg.help_text} Because kindness had reached {friend.pronoun('object')}, "
        f"{friend.pronoun()} chose to help {sarge.id} in return."
    )


def arrive(world: World, sarge: Entity, destination: Entity, setting: Setting) -> None:
    sarge.memes["joy"] += 1
    world.say(
        f"Together they came at last to {destination.label}, and {setting.ending}"
    )
    world.say(
        f"{sarge.id} learned that day that a shared gift does not grow smaller in a fairy tale. "
        f"It comes back as a brighter road, a lighter heart, and a friend beside you."
    )


def tell(setting: Setting, gift: Gift, friend_cfg: FriendType, need: Need) -> World:
    world = World(setting)
    sarge = world.add(Entity(id="Sarge", kind="character", type="boy", label="Sarge", role="hero"))
    friend = world.add(
        Entity(
            id="friend",
            kind="character",
            type="creature",
            label=friend_cfg.label,
            phrase=friend_cfg.phrase,
            role="friend",
            tags=set(friend_cfg.tags),
        )
    )
    destination = world.add(
        Entity(
            id="destination",
            kind="thing",
            type="place",
            label="the Moonlit Feast",
            phrase="the Moonlit Feast",
            role="goal",
        )
    )
    world.add(
        Entity(
            id="gift",
            kind="thing",
            type="gift",
            label=gift.label,
            phrase=gift.phrase,
            role="gift",
            attrs={"kind": gift.kind},
            tags=set(gift.tags),
        )
    )
    sarge.meters["supplies"] = 1.0

    world.facts.update(
        setting=setting,
        gift_cfg=gift,
        friend_cfg=friend_cfg,
        need_cfg=need,
        hero=sarge,
        friend=friend,
        destination=destination,
    )

    introduce(world, sarge, setting, gift, destination)
    world.para()
    meet_friend(world, sarge, friend, need)
    explain_need(world, friend, need)
    consider(world, sarge, gift, need)
    world.para()
    share(world, sarge, friend, gift, need)
    thank_and_help(world, sarge, friend_cfg, friend)
    world.para()
    arrive(world, sarge, destination, setting)

    world.facts.update(
        shared=world.get("gift").meters["shared"] >= THRESHOLD,
        soothed=friend.meters[need.id] < THRESHOLD,
        progressed=sarge.meters["progress"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "fernwood": Setting(
        id="fernwood",
        place="the Fernwood",
        opening="A silver mist drifted between the trunks, and every fern bowed as if the day itself were greeting him.",
        obstacle="a crooked stretch of path where thorny vines tangled over the stones",
        ending="lantern flowers swung above the tables, and the feast-song sounded warm as firelight.",
        tags={"forest", "feast"},
    ),
    "meadow": Setting(
        id="meadow",
        place="the Dewdrop Meadow",
        opening="Buttercups leaned together like tiny queens, and a round moon still shone pale in the morning sky.",
        obstacle="the long meadow lane where the grass grew high enough to hide the stepping stones",
        ending="the dew on the grass flashed like tiny stars around the feast blankets.",
        tags={"meadow", "feast"},
    ),
    "glen": Setting(
        id="glen",
        place="the Willow Glen",
        opening="The willow branches trailed like green ribbons, and the brook hummed a sleepy tune under them.",
        obstacle="a bend in the brook where the little bridge had slipped loose from its pegs",
        ending="the willow leaves whispered over the feast, and little cups of light floated on the water.",
        tags={"brook", "feast"},
    ),
}

GIFTS = {
    "honey_bun": Gift(
        id="honey_bun",
        label="honey bun",
        phrase="a warm honey bun wrapped in a leaf",
        kind="food",
        give_verb="broke the honey bun in two and offered the sweetest half",
        carry_text="The bun smelled of butter and clover, and he hoped to nibble it when the way grew long.",
        comfort_text="The soft bread and honey filled the air with a sweet smell.",
        divisible=True,
        tags={"food", "bread", "sharing"},
    ),
    "berry_cup": Gift(
        id="berry_cup",
        label="berry cup",
        phrase="a little cup of cool berry water",
        kind="drink",
        give_verb="held out the berry cup with both paws",
        carry_text="Drops of red sweetness winked at the rim, and he had saved every sip for later.",
        comfort_text="The cool drink slid down like a tiny stream.",
        divisible=False,
        tags={"drink", "water", "sharing"},
    ),
    "golden_scarf": Gift(
        id="golden_scarf",
        label="golden scarf",
        phrase="a little golden scarf soft as lamb's wool",
        kind="warmth",
        give_verb="wrapped the golden scarf around the creature's shoulders",
        carry_text="It was light in his paws but very cozy, and he had meant to wear it when evening came.",
        comfort_text="The wool held the wind away at once.",
        divisible=False,
        tags={"scarf", "warmth", "sharing"},
    ),
}

NEEDS = {
    "hungry": Need(
        id="hungry",
        label="hungry",
        state_text="small and hollow-bellied",
        relief_text="Soon the worried look in the creature's eyes softened.",
        kind="food",
        tags={"food"},
    ),
    "thirsty": Need(
        id="thirsty",
        label="thirsty",
        state_text="dry-mouthed and tired",
        relief_text="Soon the creature gave a long, relieved sigh.",
        kind="drink",
        tags={"drink"},
    ),
    "cold": Need(
        id="cold",
        label="cold",
        state_text="shivery and tucked into itself",
        relief_text="Soon the trembling grew still.",
        kind="warmth",
        tags={"warmth"},
    ),
}

FRIENDS = {
    "rabbit": FriendType(
        id="rabbit",
        label="rabbit",
        phrase="a white rabbit in a blue cap",
        help_text="the rabbit twitched his nose, found a secret hare-track through the brambles, and led Sarge safely around the snarl of thorns.",
        thank_text='"You shared with me when you could have hurried past," said the rabbit. "Please let me show you the hidden way."',
        tags={"rabbit", "path"},
    ),
    "wren": FriendType(
        id="wren",
        label="wren",
        phrase="a tiny brown wren with rumpled feathers",
        help_text="the wren fluttered up, spotted the lost stepping stones from above, and called Sarge from one safe stone to the next.",
        thank_text='"You were kind," chirped the wren. "Then I will use my sharp eyes for you."',
        tags={"bird", "path"},
    ),
    "mole": FriendType(
        id="mole",
        label="mole",
        phrase="a velvet mole with earth on his paws",
        help_text="the mole dug a neat little tunnel under the tangle and popped out grinning on the other side.",
        thank_text='"A warm heart deserves a clever paw," said the mole. "Come after me."',
        tags={"mole", "tunnel"},
    ),
    "fawn": FriendType(
        id="fawn",
        label="fawn",
        phrase="a speckled fawn with bright, worried eyes",
        help_text="the fawn danced lightly over the loose bridge, steadied it with careful hooves, and showed Sarge exactly where to step.",
        thank_text='"Kindness should not walk alone," said the fawn. "I will go with you."',
        tags={"fawn", "bridge"},
    ),
}


@dataclass
class StoryParams:
    setting: str
    gift: str
    friend: str
    need: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "sharing": [
        (
            "Why is sharing kind?",
            "Sharing is kind because you let someone else use something good that you have. It can help another person feel safe, full, or included."
        )
    ],
    "food": [
        (
            "What does food do for your body?",
            "Food gives your body energy to move and think. When you are hungry, eating can help you feel strong again."
        )
    ],
    "drink": [
        (
            "Why do people need water or a drink?",
            "Bodies need water so they do not get too dry. A drink can help when someone feels thirsty and tired."
        )
    ],
    "warmth": [
        (
            "Why does a scarf help when someone is cold?",
            "A scarf helps hold warm air close to the body. That makes it harder for the cold wind to steal the body's heat."
        )
    ],
    "rabbit": [
        (
            "What are rabbits good at in stories and in life?",
            "Rabbits are quick and notice paths through grass and bushes. In stories, they often make good guides because they know little hidden ways."
        )
    ],
    "bird": [
        (
            "How can a bird help someone find the way?",
            "A bird can fly up high and see more than someone on the ground. That makes it easier to spot safe paths and bridges."
        )
    ],
    "mole": [
        (
            "What can a mole do with its paws?",
            "A mole has strong digging paws. It can move through soft earth and make tunnels."
        )
    ],
    "bridge": [
        (
            "Why should you step carefully on a loose bridge?",
            "A loose bridge can wobble or slip if you rush. Stepping carefully helps you keep your balance and stay safe."
        )
    ],
}
KNOWLEDGE_ORDER = ["sharing", "food", "drink", "warmth", "rabbit", "bird", "mole", "bridge"]


def generation_prompts(world: World) -> list[str]:
    gift = world.facts["gift_cfg"]
    friend = world.facts["friend_cfg"]
    need = world.facts["need_cfg"]
    setting = world.facts["setting"]
    return [
        'Write a gentle fairy tale for a 3-to-5-year-old about sharing, and include the word "Sarge".',
        f"Tell a fairy tale where Sarge travels through {setting.place} with {gift.phrase}, meets {friend.phrase} who is {need.label}, and shares what truly helps.",
        f'Write a small fairy-tale story that teaches that sharing can open the way forward when kindness matches a real need.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    sarge = world.facts["hero"]
    friend = world.facts["friend"]
    gift = world.facts["gift_cfg"]
    need = world.facts["need_cfg"]
    friend_cfg = world.facts["friend_cfg"]
    setting = world.facts["setting"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about Sarge, a little traveler in a fairy-tale place, and a {friend.label} Sarge meets on the road. The story follows what happens when Sarge chooses to share."
        ),
        (
            "What was Sarge carrying at the start?",
            f"Sarge was carrying {gift.phrase} on the way to the Moonlit Feast. He had planned to keep it for his own journey at first."
        ),
        (
            f"Why did Sarge stop on the path?",
            f"He stopped because he found {friend.phrase} looking {need.state_text}. The creature's trouble made Sarge pause and think about helping."
        ),
        (
            "Why was sharing the right thing to do in this story?",
            f"Sharing was the right thing because {gift.label} matched the creature's need for {need.kind}. Sarge was not just giving something away; he was giving the kind of help that could really comfort someone."
        ),
    ]
    if world.facts.get("shared"):
        qa.append(
            (
                f"What happened after Sarge shared the {gift.label}?",
                f"The {friend.label} felt better, because the gift matched the need and soothed the problem. Then the creature helped Sarge with the hard part of the road, so kindness changed what happened next."
            )
        )
    if world.facts.get("progressed"):
        qa.append(
            (
                "How did the story end?",
                f"It ended with Sarge reaching the Moonlit Feast in {setting.place}. The ending image shows that sharing opened the path and left Sarge with a friend instead of walking alone."
            )
        )
    if friend_cfg.id == "fawn":
        qa.append(
            (
                "How did the fawn help Sarge?",
                "The fawn steadied the loose bridge and showed Sarge where to step. That help mattered because Sarge could not safely hurry across by himself."
            )
        )
    elif friend_cfg.id == "rabbit":
        qa.append(
            (
                "How did the rabbit help Sarge?",
                "The rabbit found a hidden track through the thorny place. That turned a blocked path into a safe way forward."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"sharing"}
    tags |= set(world.facts["gift_cfg"].tags)
    tags |= set(world.facts["need_cfg"].tags)
    tags |= set(world.facts["friend_cfg"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in world.entities.values():
        bits = []
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:11} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="fernwood", gift="honey_bun", friend="rabbit", need="hungry"),
    StoryParams(setting="meadow", gift="berry_cup", friend="wren", need="thirsty"),
    StoryParams(setting="glen", gift="golden_scarf", friend="fawn", need="cold"),
    StoryParams(setting="fernwood", gift="golden_scarf", friend="mole", need="cold"),
    StoryParams(setting="glen", gift="honey_bun", friend="rabbit", need="hungry"),
]


ASP_RULES = r"""
satisfies(G, N) :- gift_kind(G, K), need_kind(N, K).
valid(S, G, F, N) :- setting(S), gift(G), friend(F), need(N), satisfies(G, N).

shared_happy(S, G, F, N) :- valid(S, G, F, N).
#show valid/4.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for gid, gift in GIFTS.items():
        lines.append(asp.fact("gift", gid))
        lines.append(asp.fact("gift_kind", gid, gift.kind))
    for fid in FRIENDS:
        lines.append(asp.fact("friend", fid))
    for nid, need in NEEDS.items():
        lines.append(asp.fact("need", nid))
        lines.append(asp.fact("need_kind", nid, need.kind))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated story was empty.")
        print("OK: smoke-tested normal story generation.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale storyworld about Sarge learning that sharing can open the way."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--friend", choices=FRIENDS)
    ap.add_argument("--need", choices=NEEDS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible stories from ASP")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.gift and args.need:
        gift = GIFTS.get(args.gift)
        need = NEEDS.get(args.need)
        if gift is None or need is None:
            raise StoryError("(Unknown gift or need.)")
        if not satisfies(gift, need):
            raise StoryError(explain_rejection(gift, need))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.gift is None or combo[1] == args.gift)
        and (args.friend is None or combo[2] == args.friend)
        and (args.need is None or combo[3] == args.need)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting, gift, friend, need = rng.choice(sorted(combos))
    return StoryParams(setting=setting, gift=gift, friend=friend, need=need)


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS.get(params.setting)
    gift = GIFTS.get(params.gift)
    friend = FRIENDS.get(params.friend)
    need = NEEDS.get(params.need)
    if setting is None or gift is None or friend is None or need is None:
        raise StoryError("(Invalid story parameters.)")
    if not satisfies(gift, need):
        raise StoryError(explain_rejection(gift, need))

    world = tell(setting, gift, friend, need)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, gift, friend, need) combos:\n")
        for setting, gift, friend, need in combos:
            print(f"  {setting:9} {gift:13} {friend:8} {need}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

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
        header = ""
        if args.all:
            p = sample.params
            header = f"### Sarge: {p.gift} for a {p.need} {p.friend} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
