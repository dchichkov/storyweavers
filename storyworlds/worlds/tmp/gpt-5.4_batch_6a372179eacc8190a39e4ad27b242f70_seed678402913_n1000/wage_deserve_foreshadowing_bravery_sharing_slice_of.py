#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/wage_deserve_foreshadowing_bravery_sharing_slice_of.py
=================================================================================

A small slice-of-life story world about a child helping at a neighborhood stand,
earning a tiny wage, facing one brave moment, and then sharing a treat.

The seed asked for the words "wage" and "deserve", plus Foreshadowing, Bravery,
and Sharing. This world rebuilds that as a grounded little simulation:

    * A child helps a grown-up at a stand or table.
    * Early clues foreshadow the problem: either wind worries a paper sign, or
      the child's quiet voice hints that speaking to customers will be hard.
    * The child does one brave thing driven by world state.
    * The grown-up pays a small wage for honest work.
    * The child shares a slice or cup from the stand, proving what changed.

The constraint system keeps combinations sensible:
    * a "catch_sign" challenge only happens outdoors
    * a shared treat must actually be sold at that stand

Run it
------
    python storyworlds/worlds/gpt-5.4/wage_deserve_foreshadowing_bravery_sharing_slice_of.py
    python storyworlds/worlds/gpt-5.4/wage_deserve_foreshadowing_bravery_sharing_slice_of.py --booth lemonade --challenge catch_sign
    python storyworlds/worlds/gpt-5.4/wage_deserve_foreshadowing_bravery_sharing_slice_of.py --share cake_slice
    python storyworlds/worlds/gpt-5.4/wage_deserve_foreshadowing_bravery_sharing_slice_of.py --all
    python storyworlds/worlds/gpt-5.4/wage_deserve_foreshadowing_bravery_sharing_slice_of.py --qa --json
    python storyworlds/worlds/gpt-5.4/wage_deserve_foreshadowing_bravery_sharing_slice_of.py --verify
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
    owner: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}.get(
            self.type, self.type
        )


@dataclass
class Booth:
    id: str
    label: str
    place: str
    outdoor: bool
    goods: list[str]
    setup_text: str
    scent_text: str
    clue_wind: str
    clue_voice: str
    closing_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Challenge:
    id: str
    label: str
    requires_outdoor: bool
    mode: str
    clue: str
    trouble: str
    brave_action: str
    solved_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ShareItem:
    id: str
    label: str
    phrase: str
    article: str
    slice_like: bool
    sold_at: set[str]
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
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
        clone = World()
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


def _r_wind_risk(world: World) -> list[str]:
    out: list[str] = []
    booth = world.entities.get("booth")
    sign = world.entities.get("sign")
    hero = world.entities.get("hero")
    if booth is None or sign is None or hero is None:
        return out
    if booth.attrs.get("outdoor") and sign.meters["loose"] >= THRESHOLD and booth.meters["breeze"] >= THRESHOLD:
        sig = ("wind_risk", sign.id)
        if sig not in world.fired:
            world.fired.add(sig)
            booth.meters["risk"] += 1
            hero.memes["worry"] += 1
            out.append("__wind__")
    return out


def _r_line_risk(world: World) -> list[str]:
    out: list[str] = []
    booth = world.entities.get("booth")
    hero = world.entities.get("hero")
    if booth is None or hero is None:
        return out
    if booth.meters["line"] >= THRESHOLD and hero.meters["voice"] < THRESHOLD:
        sig = ("line_risk", hero.id)
        if sig not in world.fired:
            world.fired.add(sig)
            booth.meters["risk"] += 1
            hero.memes["nerves"] += 1
            out.append("__line__")
    return out


CAUSAL_RULES = [
    Rule(name="wind_risk", tag="physical", apply=_r_wind_risk),
    Rule(name="line_risk", tag="social", apply=_r_line_risk),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for sentence in produced:
            world.say(sentence)
    return produced


BOOTHS = {
    "lemonade": Booth(
        id="lemonade",
        label="lemonade stand",
        place="the corner by the library",
        outdoor=True,
        goods=["lemon_slice", "cookie_half"],
        setup_text="A folding table held a glass pitcher, a stack of paper cups, and a hand-painted price sign.",
        scent_text="The air smelled bright and sugary from the lemons.",
        clue_wind="The paper sign kept lifting at one corner whenever the breeze passed.",
        clue_voice="Soon people would come back from the library and look for something cool to drink.",
        closing_text="The last cups clinked softly as the evening cooled.",
        tags={"lemonade", "drink", "outdoor"},
    ),
    "fruit": Booth(
        id="fruit",
        label="fruit table",
        place="the Saturday market path",
        outdoor=True,
        goods=["orange_slice", "melon_slice"],
        setup_text="Small bowls of cut fruit sat on a checked cloth beside a jar for coins.",
        scent_text="Everything smelled sweet and fresh, like summer picnic air.",
        clue_wind="Napkins fluttered near the edge of the table, and the paper sign rattled against its stick.",
        clue_voice="Shoppers were already walking past with canvas bags and curious eyes.",
        closing_text="Only a few bright peels were left in the tray by the end.",
        tags={"fruit", "market", "outdoor"},
    ),
    "bakesale": Booth(
        id="bakesale",
        label="bake-sale table",
        place="the school hall",
        outdoor=False,
        goods=["cake_slice", "jam_toast_half"],
        setup_text="Neat plates of buns and cake slices stood under a banner with careful blue letters.",
        scent_text="The hall smelled warm with butter and toast.",
        clue_wind="The air was still inside, and nothing on the table stirred.",
        clue_voice="The room was quiet now, but soon families from the fair would drift in for snacks.",
        closing_text="The hall grew soft and echoey as the fair wound down.",
        tags={"baking", "school", "indoor"},
    ),
}

CHALLENGES = {
    "catch_sign": Challenge(
        id="catch_sign",
        label="catch a loose sign",
        requires_outdoor=True,
        mode="physical",
        clue="The morning kept hinting that the wind was stronger than it looked.",
        trouble="A sudden gust tugged the paper sign free and sent it skittering across the ground.",
        brave_action="ran after it before it could blow into the street, caught it with both hands, and brought it back with a thumping heart",
        solved_text="After that, the sign was clipped down tight and the stand felt steady again.",
        tags={"wind", "bravery"},
    ),
    "speak_up": Challenge(
        id="speak_up",
        label="speak to waiting customers",
        requires_outdoor=False,
        mode="social",
        clue="The busy part of the day had not arrived yet, but it was clearly coming.",
        trouble="When a little line formed, the grown-up's hands were full, and someone had to greet the waiting customers.",
        brave_action="took a slow breath, lifted a clear voice, and told everyone what was fresh and ready",
        solved_text="The line loosened into smiles, and helping no longer felt so scary.",
        tags={"voice", "bravery"},
    ),
}

SHARE_ITEMS = {
    "lemon_slice": ShareItem(
        id="lemon_slice",
        label="lemon slice",
        phrase="a bright lemon slice",
        article="a",
        slice_like=True,
        sold_at={"lemonade"},
        tags={"slice", "fruit"},
    ),
    "cookie_half": ShareItem(
        id="cookie_half",
        label="cookie half",
        phrase="half of a soft cookie",
        article="half of a",
        slice_like=False,
        sold_at={"lemonade"},
        tags={"cookie", "sharing"},
    ),
    "orange_slice": ShareItem(
        id="orange_slice",
        label="orange slice",
        phrase="a sweet orange slice",
        article="a",
        slice_like=True,
        sold_at={"fruit"},
        tags={"slice", "fruit"},
    ),
    "melon_slice": ShareItem(
        id="melon_slice",
        label="melon slice",
        phrase="a cool melon slice",
        article="a",
        slice_like=True,
        sold_at={"fruit"},
        tags={"slice", "fruit"},
    ),
    "cake_slice": ShareItem(
        id="cake_slice",
        label="cake slice",
        phrase="a soft cake slice",
        article="a",
        slice_like=True,
        sold_at={"bakesale"},
        tags={"slice", "cake"},
    ),
    "jam_toast_half": ShareItem(
        id="jam_toast_half",
        label="jam toast half",
        phrase="half of a piece of jam toast",
        article="half of a",
        slice_like=False,
        sold_at={"bakesale"},
        tags={"toast", "sharing"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo", "Owen"]
HELPER_NAMES = ["June", "Ivy", "Milo", "Ruby", "Tess", "Cole", "Penny", "Ned"]
TRAITS = ["careful", "hopeful", "cheerful", "quiet", "steady", "kind"]


def challenge_fits(booth: Booth, challenge: Challenge) -> bool:
    return not challenge.requires_outdoor or booth.outdoor


def share_fits(booth: Booth, share: ShareItem) -> bool:
    return booth.id in share.sold_at and share.id in booth.goods


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for booth_id, booth in BOOTHS.items():
        for challenge_id, challenge in CHALLENGES.items():
            if not challenge_fits(booth, challenge):
                continue
            for share_id, share in SHARE_ITEMS.items():
                if share_fits(booth, share):
                    combos.append((booth_id, challenge_id, share_id))
    return combos


@dataclass
class StoryParams:
    booth: str
    challenge: str
    share: str
    name: str
    gender: str
    helper_name: str
    helper_gender: str
    grownup: str
    trait: str
    wage_cents: int
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        booth="lemonade",
        challenge="catch_sign",
        share="lemon_slice",
        name="Lily",
        gender="girl",
        helper_name="Milo",
        helper_gender="boy",
        grownup="mother",
        trait="careful",
        wage_cents=100,
    ),
    StoryParams(
        booth="fruit",
        challenge="catch_sign",
        share="melon_slice",
        name="Ben",
        gender="boy",
        helper_name="Ruby",
        helper_gender="girl",
        grownup="father",
        trait="steady",
        wage_cents=125,
    ),
    StoryParams(
        booth="bakesale",
        challenge="speak_up",
        share="cake_slice",
        name="Maya",
        gender="girl",
        helper_name="Ned",
        helper_gender="boy",
        grownup="aunt",
        trait="quiet",
        wage_cents=150,
    ),
    StoryParams(
        booth="lemonade",
        challenge="speak_up",
        share="cookie_half",
        name="Noah",
        gender="boy",
        helper_name="June",
        helper_gender="girl",
        grownup="uncle",
        trait="hopeful",
        wage_cents=100,
    ),
]


def cents_text(cents: int) -> str:
    dollars = cents // 100
    rem = cents % 100
    if dollars and rem:
        return f"${dollars}.{rem:02d}"
    if dollars:
        return f"${dollars}"
    return f"{cents} cents"


def foreshadow_setup(world: World, hero: Entity, grownup: Entity, booth_cfg: Booth, challenge_cfg: Challenge) -> None:
    booth = world.get("booth")
    world.say(
        f"On Saturday morning, {hero.id} helped {hero.pronoun('possessive')} {grownup.label_word} at the {booth_cfg.label} at {booth_cfg.place}. "
        f"{booth_cfg.setup_text}"
    )
    world.say(booth_cfg.scent_text)
    hero.memes["hope"] += 1
    world.say(
        f"{hero.id} had been promised a tiny wage for honest work, and the thought of earning it made {hero.pronoun('object')} stand a little taller."
    )
    world.say(f"{challenge_cfg.clue} {booth_cfg.clue_wind if challenge_cfg.id == 'catch_sign' else booth_cfg.clue_voice}")


def add_foreshadow_state(world: World, challenge_cfg: Challenge, booth_cfg: Booth) -> None:
    booth = world.get("booth")
    sign = world.get("sign")
    if challenge_cfg.id == "catch_sign":
        booth.meters["breeze"] += 1
        sign.meters["loose"] += 1
    else:
        booth.meters["line"] += 1
    propagate(world, narrate=False)
    world.facts["foreshadowed_risk"] = booth.meters["risk"] >= THRESHOLD


def introduce_helper(world: World, helper: Entity, share_cfg: ShareItem) -> None:
    helper.memes["hunger"] += 1
    if share_cfg.slice_like:
        world.say(
            f"{helper.id} was nearby, folding napkins and watching the neat rows of slices with patient eyes."
        )
    else:
        world.say(
            f"{helper.id} was nearby, stacking napkins and working quietly without stopping for a snack."
        )


def trouble_arrives(world: World, hero: Entity, challenge_cfg: Challenge) -> None:
    hero.memes["nerves"] += 1
    world.say(challenge_cfg.trouble)


def brave_turn(world: World, hero: Entity, challenge_cfg: Challenge) -> None:
    booth = world.get("booth")
    sign = world.get("sign")
    if challenge_cfg.id == "catch_sign":
        sign.meters["caught"] += 1
        sign.meters["loose"] = 0.0
        booth.meters["risk"] = 0.0
    else:
        hero.meters["voice"] += 1
        booth.meters["risk"] = 0.0
    hero.memes["courage"] += 1
    hero.memes["pride"] += 1
    hero.memes["nerves"] = max(0.0, hero.memes["nerves"] - 1.0)
    world.say(f"{hero.id} {challenge_cfg.brave_action}.")
    world.say(challenge_cfg.solved_text)


def earn_wage(world: World, hero: Entity, grownup: Entity, params: StoryParams) -> None:
    hero.meters["wage"] += params.wage_cents
    hero.memes["relief"] += 1
    amount = cents_text(params.wage_cents)
    world.say(
        f"When the busy moment was over, {hero.pronoun('possessive')} {grownup.label_word} pressed {amount} into {hero.pronoun('possessive')} hand."
    )
    world.say(
        f'"You earned this wage," {grownup.label_word} said. "You were brave, and you helped when it mattered. You deserve it."'
    )


def share_ending(world: World, hero: Entity, helper: Entity, share_cfg: ShareItem, booth_cfg: Booth) -> None:
    hero.memes["generosity"] += 1
    helper.memes["gratitude"] += 1
    world.say(
        f"{hero.id} looked at the coins, then at {helper.id}, who had been working hard too."
    )
    if share_cfg.slice_like:
        world.say(
            f"Instead of keeping every bit for later, {hero.pronoun()} chose {share_cfg.phrase} and shared it with {helper.id} on the edge of the table bench."
        )
    else:
        world.say(
            f"Instead of keeping every treat to {hero.pronoun('object')}, {hero.pronoun()} picked {share_cfg.phrase} and broke it neatly so {helper.id} could have some too."
        )
    world.say(
        f"They ate together while {booth_cfg.closing_text} The small wage felt warm in {hero.pronoun('possessive')} pocket, but the shared bite felt warmer."
    )


def tell(
    booth_cfg: Booth,
    challenge_cfg: Challenge,
    share_cfg: ShareItem,
    name: str,
    gender: str,
    helper_name: str,
    helper_gender: str,
    grownup_type: str,
    trait: str,
    wage_cents: int,
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=gender, label=name, role="hero", attrs={"name": name}))
    helper = world.add(
        Entity(id="helper", kind="character", type=helper_gender, label=helper_name, role="helper", attrs={"name": helper_name})
    )
    grownup = world.add(Entity(id="grownup", kind="character", type=grownup_type, label="the grown-up", role="grownup"))
    booth = world.add(
        Entity(
            id="booth",
            kind="thing",
            type="booth",
            label=booth_cfg.label,
            attrs={"outdoor": booth_cfg.outdoor, "place": booth_cfg.place},
            tags=set(booth_cfg.tags),
        )
    )
    sign = world.add(Entity(id="sign", kind="thing", type="sign", label="paper sign"))

    hero.memes["nerves"] = 2.0 if challenge_cfg.id == "speak_up" or trait == "quiet" else 1.0
    hero.memes["kindness"] = 1.0
    helper.memes["trust"] = 1.0
    world.facts["hero_name"] = name
    world.facts["helper_name"] = helper_name

    foreshadow_setup(world, hero, grownup, booth_cfg, challenge_cfg)
    add_foreshadow_state(world, challenge_cfg, booth_cfg)
    introduce_helper(world, helper, share_cfg)

    world.para()
    trouble_arrives(world, hero, challenge_cfg)
    brave_turn(world, hero, challenge_cfg)

    world.para()
    earn_wage(world, hero, grownup, StoryParams(
        booth=booth_cfg.id,
        challenge=challenge_cfg.id,
        share=share_cfg.id,
        name=name,
        gender=gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        grownup=grownup_type,
        trait=trait,
        wage_cents=wage_cents,
    ))
    share_ending(world, hero, helper, share_cfg, booth_cfg)

    world.facts.update(
        booth_cfg=booth_cfg,
        challenge_cfg=challenge_cfg,
        share_cfg=share_cfg,
        hero=hero,
        helper=helper,
        grownup=grownup,
        foreshadowed=world.facts.get("foreshadowed_risk", False),
        brave=hero.memes["courage"] >= THRESHOLD,
        shared=hero.memes["generosity"] >= THRESHOLD,
        wage_cents=wage_cents,
    )
    return world


KNOWLEDGE = {
    "wage": [
        (
            "What is a wage?",
            "A wage is money someone earns for doing work. Grown-ups often earn wages for jobs, and in a story a child might get a tiny one for helping fairly.",
        )
    ],
    "deserve": [
        (
            "What does deserve mean?",
            "Deserve means something fits what someone has done. If a person works hard or acts kindly, people may say that person deserves thanks or a reward.",
        )
    ],
    "wind": [
        (
            "Why can a loose paper sign be a problem outside?",
            "Paper is light, so wind can push it away quickly. If a sign blows off, people may not see it, and someone has to fetch it safely.",
        )
    ],
    "voice": [
        (
            "Why can speaking up be brave?",
            "Speaking up can feel scary when you are shy or nervous. It is brave because you use your voice even while your heart is fluttering.",
        )
    ],
    "sharing": [
        (
            "Why does sharing food feel kind?",
            "Sharing means making room for someone else in your good moment. A small bite can feel big when it shows you were thinking of another person.",
        )
    ],
    "slice": [
        (
            "What is a slice?",
            "A slice is one thin piece cut from a bigger food, like cake, melon, or orange. Slices are easy to share because one whole thing can become several pieces.",
        )
    ],
}
KNOWLEDGE_ORDER = ["wage", "deserve", "wind", "voice", "sharing", "slice"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    booth_cfg = f["booth_cfg"]
    challenge_cfg = f["challenge_cfg"]
    share_cfg = f["share_cfg"]
    helper = f["helper"]
    return [
        f'Write a short slice-of-life story for a 3-to-5-year-old that includes the words "wage" and "deserve".',
        f"Tell a gentle story where {hero.attrs['name']} helps at a {booth_cfg.label}, notices an early clue about trouble, does one brave thing, and then shares {share_cfg.phrase} with {helper.attrs['name']}.",
        f"Write a child-facing story with foreshadowing, bravery, and sharing, where the brave moment is about {challenge_cfg.label} and the ending image is two children eating together.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    grownup = f["grownup"]
    booth_cfg = f["booth_cfg"]
    challenge_cfg = f["challenge_cfg"]
    share_cfg = f["share_cfg"]
    amount = cents_text(f["wage_cents"])
    hero_name = hero.attrs["name"]
    helper_name = helper.attrs["name"]
    pw = grownup.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero_name}, who helped at a {booth_cfg.label}, and {helper_name}, who worked nearby. {hero_name}'s {pw} was there too and trusted {hero_name} with real helping jobs.",
        ),
        (
            f"How did the story foreshadow the problem?",
            f"It gave a small clue before the hard moment came: {challenge_cfg.clue.lower()} That early hint prepared the reader for the trouble instead of making it appear from nowhere.",
        ),
        (
            f"What brave thing did {hero_name} do?",
            f"{hero_name} {challenge_cfg.brave_action}. That was brave because the problem had already arrived, and {hero_name} acted instead of shrinking back.",
        ),
        (
            f"What wage did {hero_name} earn, and why?",
            f"{hero_name} earned {amount}. {pw.capitalize()} said {hero_name} deserved the wage because {hero_name} worked honestly and helped in the hard moment.",
        ),
        (
            f"How did sharing change the ending?",
            f"{hero_name} did not keep the treat alone. By sharing {share_cfg.phrase} with {helper_name}, {hero_name} showed that the brave moment had opened into kindness.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"wage", "deserve", "sharing"}
    challenge_cfg = world.facts["challenge_cfg"]
    share_cfg = world.facts["share_cfg"]
    if challenge_cfg.id == "catch_sign":
        tags.add("wind")
    if challenge_cfg.id == "speak_up":
        tags.add("voice")
    if share_cfg.slice_like:
        tags.add("slice")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(booth: Booth, challenge: Challenge, share: Optional[ShareItem] = None) -> str:
    if challenge.requires_outdoor and not booth.outdoor:
        return (
            f"(No story: {challenge.label} only makes sense outdoors, but the {booth.label} is at {booth.place}, which is indoors.)"
        )
    if share is not None and not share_fits(booth, share):
        return (
            f"(No story: {share.phrase} is not sold at the {booth.label}, so the sharing ending would feel ungrounded. Pick something the booth actually serves.)"
        )
    return "(No story: this combination does not fit the little world.)"


ASP_RULES = r"""
outdoor(B) :- booth(B), booth_outdoor(B).

challenge_fits(B, C) :- booth(B), challenge(C), not needs_outdoor(C).
challenge_fits(B, C) :- booth(B), challenge(C), needs_outdoor(C), outdoor(B).

share_fits(B, S) :- booth(B), share_item(S), sold_at(S, B), sells(B, S).

valid(B, C, S) :- challenge_fits(B, C), share_fits(B, S).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for booth_id, booth in BOOTHS.items():
        lines.append(asp.fact("booth", booth_id))
        if booth.outdoor:
            lines.append(asp.fact("booth_outdoor", booth_id))
        for good in booth.goods:
            lines.append(asp.fact("sells", booth_id, good))
    for challenge_id, challenge in CHALLENGES.items():
        lines.append(asp.fact("challenge", challenge_id))
        if challenge.requires_outdoor:
            lines.append(asp.fact("needs_outdoor", challenge_id))
    for share_id, share in SHARE_ITEMS.items():
        lines.append(asp.fact("share_item", share_id))
        for booth_id in sorted(share.sold_at):
            lines.append(asp.fact("sold_at", share_id, booth_id))
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
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test produced an empty story")
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: generate/emit smoke test passed.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Slice-of-life story world: a child earns a tiny wage, does one brave thing, and shares a treat."
    )
    ap.add_argument("--booth", choices=BOOTHS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--share", choices=SHARE_ITEMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--grownup", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("--wage-cents", type=int, choices=[75, 100, 125, 150])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid combo set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP twin and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    options = [name for name in pool if name != avoid]
    return rng.choice(options)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.booth and args.challenge:
        booth = BOOTHS[args.booth]
        challenge = CHALLENGES[args.challenge]
        if not challenge_fits(booth, challenge):
            raise StoryError(explain_rejection(booth, challenge))
    if args.booth and args.share:
        booth = BOOTHS[args.booth]
        share = SHARE_ITEMS[args.share]
        if not share_fits(booth, share):
            challenge = CHALLENGES[args.challenge] if args.challenge else next(iter(CHALLENGES.values()))
            raise StoryError(explain_rejection(booth, challenge, share))

    combos = [
        combo
        for combo in valid_combos()
        if (args.booth is None or combo[0] == args.booth)
        and (args.challenge is None or combo[1] == args.challenge)
        and (args.share is None or combo[2] == args.share)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    booth_id, challenge_id, share_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    name = args.name or pick_name(rng, gender)
    helper_name = args.helper_name or rng.choice([n for n in HELPER_NAMES if n != name])
    grownup = args.grownup or rng.choice(["mother", "father", "aunt", "uncle"])
    trait = rng.choice(TRAITS)
    wage_cents = args.wage_cents if args.wage_cents is not None else rng.choice([75, 100, 125, 150])
    return StoryParams(
        booth=booth_id,
        challenge=challenge_id,
        share=share_id,
        name=name,
        gender=gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        grownup=grownup,
        trait=trait,
        wage_cents=wage_cents,
    )


def generate(params: StoryParams) -> StorySample:
    if params.booth not in BOOTHS:
        raise StoryError(f"(Invalid booth: {params.booth})")
    if params.challenge not in CHALLENGES:
        raise StoryError(f"(Invalid challenge: {params.challenge})")
    if params.share not in SHARE_ITEMS:
        raise StoryError(f"(Invalid share item: {params.share})")

    booth_cfg = BOOTHS[params.booth]
    challenge_cfg = CHALLENGES[params.challenge]
    share_cfg = SHARE_ITEMS[params.share]

    if not challenge_fits(booth_cfg, challenge_cfg):
        raise StoryError(explain_rejection(booth_cfg, challenge_cfg))
    if not share_fits(booth_cfg, share_cfg):
        raise StoryError(explain_rejection(booth_cfg, challenge_cfg, share_cfg))

    world = tell(
        booth_cfg=booth_cfg,
        challenge_cfg=challenge_cfg,
        share_cfg=share_cfg,
        name=params.name,
        gender=params.gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        grownup_type=params.grownup,
        trait=params.trait,
        wage_cents=params.wage_cents,
    )
    return StorySample(
        params=params,
        story=world.render().replace("hero", params.name).replace("helper", params.helper_name),
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (booth, challenge, share) combos:\n")
        for booth_id, challenge_id, share_id in combos:
            print(f"  {booth_id:10} {challenge_id:11} {share_id}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.booth}, {p.challenge}, share {p.share}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
