#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/rabbi_raffle_sharing_sound_effects_slice_of.py
===========================================================================

A small storyworld about a child at a neighborhood raffle table with a rabbi,
a hopeful friend, and a prize that is only a good sharing story when it can
really be shared.

The world model keeps a simple slice-of-life chain:

    waiting at the raffle table -> excitement
    drawing a winning ticket    -> one child gets a prize
    friend wanted the same kind -> disappointment
    noticing disappointment     -> empathy rises
    shareable prize + willing child -> prize portions split, both children feel better

A reasonableness gate refuses stories built around prizes that cannot be shared
in a concrete child-facing way. The prose includes little sound effects from the
table and the raffle drum.

Run it
------
    python storyworlds/worlds/gpt-5.4/rabbi_raffle_sharing_sound_effects_slice_of.py
    python storyworlds/worlds/gpt-5.4/rabbi_raffle_sharing_sound_effects_slice_of.py --prize cookie_box
    python storyworlds/worlds/gpt-5.4/rabbi_raffle_sharing_sound_effects_slice_of.py --prize kite
    python storyworlds/worlds/gpt-5.4/rabbi_raffle_sharing_sound_effects_slice_of.py --all
    python storyworlds/worlds/gpt-5.4/rabbi_raffle_sharing_sound_effects_slice_of.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/rabbi_raffle_sharing_sound_effects_slice_of.py --json
    python storyworlds/worlds/gpt-5.4/rabbi_raffle_sharing_sound_effects_slice_of.py --verify
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man", "rabbi"}
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
    table_detail: str
    room_sound: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    share_noun: str
    pieces: int
    divisible: bool
    split_text: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class DrawStyle:
    id: str
    drum_sound: str
    ticket_sound: str
    call_line: str
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"winner", "friend"}]

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


def _r_notice_disappointment(world: World) -> list[str]:
    winner = world.get("winner")
    friend = world.get("friend")
    if friend.memes["sad"] < THRESHOLD or winner.memes["empathy"] >= THRESHOLD:
        return []
    sig = ("notice",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    winner.memes["empathy"] += 1
    return ["__noticed__"]


def _r_shared_relief(world: World) -> list[str]:
    prize = world.get("prize")
    winner = world.get("winner")
    friend = world.get("friend")
    if prize.meters["shared"] < THRESHOLD:
        return []
    sig = ("relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    winner.memes["warmth"] += 1
    friend.memes["joy"] += 1
    friend.memes["sad"] = 0.0
    return []


CAUSAL_RULES = [
    Rule(name="notice_disappointment", tag="social", apply=_r_notice_disappointment),
    Rule(name="shared_relief", tag="social", apply=_r_shared_relief),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def shareable(prize: Prize) -> bool:
    return prize.divisible and prize.pieces >= 2


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id in SETTINGS:
        for draw_id in DRAW_STYLES:
            for prize_id, prize in PRIZES.items():
                if shareable(prize):
                    combos.append((setting_id, draw_id, prize_id))
    return combos


@dataclass
class StoryParams:
    setting: str
    draw_style: str
    prize: str
    winner_name: str
    winner_gender: str
    friend_name: str
    friend_gender: str
    rabbi_name: str
    winner_trait: str
    friend_trait: str
    seed: Optional[int] = None


def introduce(world: World, winner: Entity, friend: Entity, rabbi: Entity) -> None:
    world.say(
        f"After school, {winner.id} and {friend.id} went with {winner.pronoun('possessive')} family "
        f"to {world.setting.place}. {world.setting.table_detail}"
    )
    world.say(
        f"{rabbi.label_word} stood by the raffle table with a warm smile, and "
        f"{world.setting.room_sound}."
    )
    world.say(
        f"{winner.id} stayed close enough to hear every little sound, while {friend.id} "
        f"rocked from heel to toe, hoping for a lucky turn."
    )
    winner.memes["anticipation"] += 1
    friend.memes["anticipation"] += 1


def tickets_and_sounds(world: World, winner: Entity, friend: Entity, draw: DrawStyle) -> None:
    world.say(
        f'The ticket strips went "{draw.ticket_sound}" as children tore them apart and dropped their halves into the bowl.'
    )
    world.say(
        f'{winner.id} pressed a coin into the tin -- "plink!" -- and {friend.id} whispered, "Maybe this time."'
    )
    winner.memes["hope"] += 1
    friend.memes["hope"] += 1


def draw_winner(world: World, winner: Entity, friend: Entity, rabbi: Entity, draw: DrawStyle, prize: Prize) -> None:
    prize_ent = world.get("prize")
    world.say(
        f'Then the raffle drum went "{draw.drum_sound}" as {rabbi.label_word} gave it a careful turn.'
    )
    world.say(
        f'{rabbi.label_word} reached in, opened one small slip, and called, "{draw.call_line} {winner.id}!"'
    )
    prize_ent.attrs["owner"] = winner.id
    prize_ent.meters["won"] += 1
    winner.memes["joy"] += 1
    friend.memes["sad"] += 1
    world.say(
        f"{winner.id}'s face lit up when {rabbi.pronoun()} handed over {prize.phrase}. "
        f"But beside {winner.pronoun('object')}, {friend.id}'s smile went small."
    )
    world.facts["friend_wanted_prize"] = True
    propagate(world, narrate=False)


def hesitate(world: World, winner: Entity, friend: Entity, prize: Prize) -> None:
    world.say(
        f"{winner.id} hugged the {prize.label} to {winner.pronoun('possessive')} chest for one quiet second."
    )
    if winner.memes["empathy"] >= THRESHOLD:
        world.say(
            f"Then {winner.pronoun()} looked at {friend.id} again and noticed how hard {friend.pronoun()} was trying not to look disappointed."
        )
    else:
        world.say(
            f"{friend.id} looked down at the floor tiles, and the happy noise around the table felt softer for a moment."
        )


def rabbi_nudges(world: World, winner: Entity, friend: Entity, rabbi: Entity, prize: Prize) -> None:
    winner.memes["reflection"] += 1
    world.say(
        f'{rabbi.label_word} did not hurry anyone. {rabbi.pronoun().capitalize()} only said, '
        f'"A raffle picks one name, but a kind heart can make room for two."'
    )
    world.say(
        f'That made {winner.id} look from the {prize.label} to {friend.id} and back again.'
    )


def share_prize(world: World, winner: Entity, friend: Entity, prize: Prize) -> None:
    prize_ent = world.get("prize")
    if not shareable(prize):
        raise StoryError(explain_rejection(prize))
    prize_ent.meters["shared"] += 1
    prize_ent.attrs["shared_with"] = friend.id
    winner.memes["generosity"] += 1
    world.say(prize.split_text.format(winner=winner.id, friend=friend.id))
    world.say(
        f"Soon each child had {prize.share_noun}, and the tight feeling at the table was gone."
    )
    propagate(world, narrate=False)


def ending(world: World, winner: Entity, friend: Entity, rabbi: Entity, prize: Prize) -> None:
    world.say(
        f'{friend.id} grinned and said, "Thank you for sharing." {winner.id} grinned back, and {rabbi.label_word} gave a small nod.'
    )
    world.say(
        f"On the way home, the evening felt easy again. {prize.ending_image}"
    )


def tell(
    setting: Setting,
    draw: DrawStyle,
    prize: Prize,
    winner_name: str = "Noah",
    winner_gender: str = "boy",
    friend_name: str = "Leah",
    friend_gender: str = "girl",
    rabbi_name: str = "Rabbi Levin",
    winner_trait: str = "careful",
    friend_trait: str = "hopeful",
) -> World:
    world = World(setting)
    winner = world.add(
        Entity(
            id="winner",
            kind="character",
            type=winner_gender,
            label=winner_name,
            role="winner",
            traits=[winner_trait],
        )
    )
    friend = world.add(
        Entity(
            id="friend",
            kind="character",
            type=friend_gender,
            label=friend_name,
            role="friend",
            traits=[friend_trait],
        )
    )
    rabbi = world.add(
        Entity(
            id="rabbi",
            kind="character",
            type="rabbi",
            label=rabbi_name,
            role="rabbi",
            traits=["gentle"],
        )
    )
    prize_ent = world.add(
        Entity(
            id="prize",
            kind="thing",
            type="prize",
            label=prize.label,
            phrase=prize.phrase,
            attrs={"pieces": prize.pieces},
            tags=set(prize.tags),
        )
    )

    introduce(world, winner, friend, rabbi)
    tickets_and_sounds(world, winner, friend, draw)

    world.para()
    draw_winner(world, winner, friend, rabbi, draw, prize)
    hesitate(world, winner, friend, prize)

    world.para()
    rabbi_nudges(world, winner, friend, rabbi, prize)
    share_prize(world, winner, friend, prize)
    ending(world, winner, friend, rabbi, prize)

    world.facts.update(
        winner=winner,
        friend=friend,
        rabbi=rabbi,
        prize_cfg=prize,
        prize=prize_ent,
        setting=setting,
        draw=draw,
        shared=prize_ent.meters["shared"] >= THRESHOLD,
        pieces=prize.pieces,
    )
    return world


SETTINGS = {
    "social_hall": Setting(
        id="social_hall",
        place="the synagogue social hall",
        table_detail="Paper stars hung over the snack table, and the white raffle box sat beside a stack of bright tickets",
        room_sound='chairs scooted, coats rustled, and somewhere near the door a little bell went "ding-ding"',
        tags={"hall", "community"},
    ),
    "school_gym": Setting(
        id="school_gym",
        place="the Hebrew school gym",
        table_detail="Foldout tables lined the wall, and the raffle basket table glowed under strings of soft lights",
        room_sound='sneakers squeaked, grown-ups chatted, and cups touched with a tiny "clink"',
        tags={"gym", "community"},
    ),
    "courtyard": Setting(
        id="courtyard",
        place="the synagogue courtyard",
        table_detail="A long table stood under the evening sky, with tickets in a bowl and prizes laid out on blue cloth",
        room_sound='the gate clicked, leaves whispered, and the folding sign gave a light "tap-tap" in the breeze',
        tags={"courtyard", "community"},
    ),
}

DRAW_STYLES = {
    "drum": DrawStyle(
        id="drum",
        drum_sound="whirr-whirr",
        ticket_sound="rip-rip",
        call_line="And the winning ticket belongs to",
        tags={"sound", "raffle"},
    ),
    "bowl": DrawStyle(
        id="bowl",
        drum_sound="shake-shake",
        ticket_sound="zip-zip",
        call_line="Let's see whose name we have here",
        tags={"sound", "raffle"},
    ),
    "tin": DrawStyle(
        id="tin",
        drum_sound="rattle-rattle",
        ticket_sound="snip-snip",
        call_line="Here comes our lucky name",
        tags={"sound", "raffle"},
    ),
}

PRIZES = {
    "cookie_box": Prize(
        id="cookie_box",
        label="cookie box",
        phrase="a box of rugelach cookies",
        share_noun="two sweet pieces to hold",
        pieces=6,
        divisible=True,
        split_text="{winner} opened the box, counted the cookies, and held it out. \"We can share,\" {winner} said. {friend} chose first, and then they made two neat little piles.",
        ending_image="The paper box rested between them on the car seat, and the cinnamon smell drifted up every time they peeked inside.",
        tags={"cookie", "sharing", "food"},
    ),
    "sticker_pack": Prize(
        id="sticker_pack",
        label="sticker pack",
        phrase="a fat pack of shiny animal stickers",
        share_noun="a small sheet of stickers of their own",
        pieces=8,
        divisible=True,
        split_text="{winner} peeled apart the sticker sheets and laughed. \"There are plenty,\" {winner} said. {friend} got a whole half, and both children started choosing favorites right away.",
        ending_image="Later, two backpacks rode home with matching bright stickers on the zipper pulls.",
        tags={"stickers", "sharing"},
    ),
    "muffin_plate": Prize(
        id="muffin_plate",
        label="muffin plate",
        phrase="a paper plate with four blueberry mini muffins",
        share_noun="two warm muffins each",
        pieces=4,
        divisible=True,
        split_text="{winner} looked at the muffins, then at {friend}, and smiled. \"Two for me and two for you,\" {winner} said, sliding the paper plate between them.",
        ending_image="Blueberry crumbs dotted their napkins while the last of the evening light faded outside the windows.",
        tags={"muffin", "sharing", "food"},
    ),
    "kite": Prize(
        id="kite",
        label="kite",
        phrase="a bright red kite with a long tail",
        share_noun="",
        pieces=1,
        divisible=False,
        split_text="",
        ending_image="",
        tags={"kite"},
    ),
}


KNOWLEDGE = {
    "raffle": [
        (
            "What is a raffle?",
            "A raffle is a game where people get tickets and one ticket is picked to win a prize. It is a way groups often raise money for a school or community event.",
        )
    ],
    "rabbi": [
        (
            "What does a rabbi do?",
            "A rabbi is a Jewish teacher and community leader. A rabbi can help people learn, pray, and treat each other kindly.",
        )
    ],
    "sharing": [
        (
            "Why is sharing kind?",
            "Sharing lets another person enjoy something good with you. It can turn one child's lonely feeling into a happy feeling for two people.",
        )
    ],
    "tickets": [
        (
            "Why do raffle tickets make a ripping sound?",
            "Many raffle tickets come in long strips or joined pairs. When people tear them apart, the paper makes a little ripping sound.",
        )
    ],
    "cookie": [
        (
            "What is rugelach?",
            "Rugelach is a small rolled pastry that is often sweet and flaky. People may fill it with cinnamon, jam, or chocolate.",
        )
    ],
    "stickers": [
        (
            "Why are stickers easy to share?",
            "A sticker pack has many separate stickers or sheets. That makes it easy to divide so more than one child can enjoy some.",
        )
    ],
    "muffin": [
        (
            "What is a mini muffin?",
            "A mini muffin is a very small muffin baked in a tiny cup. Because there are several on one plate, they can be easy to share.",
        )
    ],
}
KNOWLEDGE_ORDER = ["raffle", "rabbi", "sharing", "tickets", "cookie", "stickers", "muffin"]

GIRL_NAMES = ["Leah", "Mira", "Talia", "Rina", "Noa", "Dina", "Arielle", "Esti"]
BOY_NAMES = ["Noah", "Eli", "Jonah", "Ari", "Ben", "Micah", "Lev", "Daniel"]
TRAITS = ["careful", "hopeful", "bouncy", "thoughtful", "patient", "gentle"]


CURATED = [
    StoryParams(
        setting="social_hall",
        draw_style="drum",
        prize="cookie_box",
        winner_name="Noah",
        winner_gender="boy",
        friend_name="Leah",
        friend_gender="girl",
        rabbi_name="Rabbi Levin",
        winner_trait="thoughtful",
        friend_trait="hopeful",
    ),
    StoryParams(
        setting="school_gym",
        draw_style="bowl",
        prize="sticker_pack",
        winner_name="Mira",
        winner_gender="girl",
        friend_name="Eli",
        friend_gender="boy",
        rabbi_name="Rabbi Stein",
        winner_trait="careful",
        friend_trait="patient",
    ),
    StoryParams(
        setting="courtyard",
        draw_style="tin",
        prize="muffin_plate",
        winner_name="Jonah",
        winner_gender="boy",
        friend_name="Talia",
        friend_gender="girl",
        rabbi_name="Rabbi Adler",
        winner_trait="gentle",
        friend_trait="bouncy",
    ),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    winner = f["winner"]
    friend = f["friend"]
    rabbi = f["rabbi"]
    prize = f["prize_cfg"]
    setting = f["setting"]
    return [
        'Write a short slice-of-life story for a 3-to-5-year-old that includes the words "rabbi" and "raffle" and uses little sound effects.',
        f"Tell a gentle community story set in {setting.place} where {winner.label} wins {prize.phrase} in a raffle, notices {friend.label}'s disappointment, and chooses to share.",
        f"Write a cozy story where {rabbi.label_word} says something kind, a raffle table makes small sounds, and two children end the evening sharing one prize.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    winner = f["winner"]
    friend = f["friend"]
    rabbi = f["rabbi"]
    prize = f["prize_cfg"]
    setting = f["setting"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {winner.label} and {friend.label} at {setting.place}, and {rabbi.label_word} at the raffle table. The story follows how one child's win became something both children could enjoy.",
        ),
        (
            "What happened at the raffle?",
            f"{winner.label} won {prize.phrase} when {rabbi.label_word} picked the winning ticket. {friend.label} had hoped for the same prize, so the win brought one happy feeling and one disappointed feeling at the same time.",
        ),
        (
            f"How did {winner.label} know {friend.label} felt bad?",
            f"{winner.label} saw {friend.label}'s smile grow small and noticed {friend.pronoun()} looking down instead of cheering. That quiet change is what made empathy rise before the sharing happened.",
        ),
        (
            f"What did {rabbi.label_word} do?",
            f"{rabbi.label_word} did not grab the prize or order anyone around. {rabbi.pronoun().capitalize()} gave a gentle reminder that one winning ticket could still lead to kindness for two children.",
        ),
        (
            f"How did the problem get solved?",
            f"{winner.label} shared the {prize.label} with {friend.label}. Because the prize had enough separate pieces to divide, the kind choice was concrete and fair instead of only being a promise.",
        ),
        (
            "How did the story end?",
            f"It ended with both children carrying part of the prize and feeling light again. The ending image shows that sharing changed the mood at the table and on the trip home.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"raffle", "rabbi", "sharing", "tickets"} | set(f["prize_cfg"].tags)
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(prize: Prize) -> str:
    return (
        f"(No story: {prize.phrase} is not a good sharing prize here. "
        f"A sharing ending in this world needs a prize with at least two concrete pieces, "
        f"like cookies, stickers, or mini muffins.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a rabbi, a raffle, and a shareable prize. Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--draw-style", choices=DRAW_STYLES, dest="draw_style")
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--winner-gender", choices=["girl", "boy"], dest="winner_gender")
    ap.add_argument("--friend-gender", choices=["girl", "boy"], dest="friend_gender")
    ap.add_argument("--rabbi-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.prize:
        prize = PRIZES[args.prize]
        if not shareable(prize):
            raise StoryError(explain_rejection(prize))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.draw_style is None or combo[1] == args.draw_style)
        and (args.prize is None or combo[2] == args.prize)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, draw_id, prize_id = rng.choice(sorted(combos))
    winner_gender = args.winner_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    winner_name = _pick_name(rng, winner_gender)
    friend_name = _pick_name(rng, friend_gender, avoid=winner_name)
    rabbi_name = args.rabbi_name or rng.choice(["Rabbi Levin", "Rabbi Stein", "Rabbi Adler", "Rabbi Bloom"])
    return StoryParams(
        setting=setting_id,
        draw_style=draw_id,
        prize=prize_id,
        winner_name=winner_name,
        winner_gender=winner_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        rabbi_name=rabbi_name,
        winner_trait=rng.choice(TRAITS),
        friend_trait=rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.draw_style not in DRAW_STYLES:
        raise StoryError(f"(Unknown draw style: {params.draw_style})")
    if params.prize not in PRIZES:
        raise StoryError(f"(Unknown prize: {params.prize})")
    prize = PRIZES[params.prize]
    if not shareable(prize):
        raise StoryError(explain_rejection(prize))

    world = tell(
        setting=SETTINGS[params.setting],
        draw=DRAW_STYLES[params.draw_style],
        prize=prize,
        winner_name=params.winner_name,
        winner_gender=params.winner_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        rabbi_name=params.rabbi_name,
        winner_trait=params.winner_trait,
        friend_trait=params.friend_trait,
    )
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


ASP_RULES = r"""
shareable(P) :- prize(P), divisible(P), pieces(P, N), N >= 2.
valid(S, D, P) :- setting(S), draw_style(D), prize(P), shareable(P).
"""

def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for did in DRAW_STYLES:
        lines.append(asp.fact("draw_style", did))
    for pid, prize in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("pieces", pid, prize.pieces))
        if prize.divisible:
            lines.append(asp.fact("divisible", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: generated story was empty.)")
        print("OK: generate() smoke test passed.")
    except Exception as exc:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    try:
        args = build_parser().parse_args([])
        params = resolve_params(args, random.Random(123))
        sample = generate(params)
        if not sample.story.strip():
            raise StoryError("(Random smoke test failed: generated story was empty.)")
        print("OK: random generation smoke test passed.")
    except Exception as exc:  # pragma: no cover - verify path
        rc = 1
        print(f"RANDOM SMOKE TEST FAILED: {exc}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, draw_style, prize) combos:\n")
        for setting_id, draw_id, prize_id in combos:
            print(f"  {setting_id:12} {draw_id:8} {prize_id}")
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
            header = f"### {p.winner_name} and {p.friend_name}: {p.prize} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
