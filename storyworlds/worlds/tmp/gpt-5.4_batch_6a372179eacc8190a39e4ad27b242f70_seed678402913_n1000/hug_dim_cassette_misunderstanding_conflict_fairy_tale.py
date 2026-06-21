#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/hug_dim_cassette_misunderstanding_conflict_fairy_tale.py
====================================================================================

A standalone story world for a small fairy-tale misunderstanding: two children
care about a magical cassette that sings the "hug-dim" lullaby, the cassette
goes missing for a real physical reason, one child wrongly blames the other, a
conflict grows, and a gentle helper reveals what truly happened.

The world model tracks:
- typed entities with physical meters and emotional memes
- a simple forward-chaining causal layer for loss -> worry -> conflict
- a reasonableness gate for which meddler can move the cassette to which place
  and which helper can honestly solve the misunderstanding
- an inline ASP twin that mirrors the compatibility gate and the outcome model

Run it
------
    python storyworlds/worlds/gpt-5.4/hug_dim_cassette_misunderstanding_conflict_fairy_tale.py
    python storyworlds/worlds/gpt-5.4/hug_dim_cassette_misunderstanding_conflict_fairy_tale.py --all
    python storyworlds/worlds/gpt-5.4/hug_dim_cassette_misunderstanding_conflict_fairy_tale.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/hug_dim_cassette_misunderstanding_conflict_fairy_tale.py --qa
    python storyworlds/worlds/gpt-5.4/hug_dim_cassette_misunderstanding_conflict_fairy_tale.py --verify
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
        female = {"girl", "princess", "mother", "queen", "fairy"}
        male = {"boy", "prince", "father", "king", "wizard"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    id: str
    place: str
    image: str
    path: str
    tags: set[str] = field(default_factory=set)


@dataclass
class CassetteKind:
    id: str
    phrase: str
    song_name: str
    glow: str
    comfort: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Meddler:
    id: str
    label: str
    leaves_sign: str
    sign_noun: str
    can_reach: set[str]
    manner: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HidingPlace:
    id: str
    phrase: str
    found_line: str
    reach_tag: str
    sign_visible: bool
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    sees_hidden: bool
    reads_signs: bool
    peace: int
    reveal_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    cassette: str
    meddler: str
    place: str
    helper: str
    keeper_name: str
    keeper_gender: str
    friend_name: str
    friend_gender: str
    relation: str
    temper: str
    seed: Optional[int] = None


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


def _r_loss_worry(world: World) -> list[str]:
    out: list[str] = []
    cassette = world.get("cassette")
    if cassette.meters["missing"] < THRESHOLD:
        return out
    for eid in ("keeper", "friend"):
        ent = world.get(eid)
        sig = ("worry", eid)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["worry"] += 1
    return out


def _r_accusation_conflict(world: World) -> list[str]:
    keeper = world.get("keeper")
    friend = world.get("friend")
    if keeper.memes["accusation"] < THRESHOLD:
        return []
    sig = ("conflict", "keeper", "friend")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    keeper.memes["anger"] += 1
    friend.memes["hurt"] += 1
    keeper.memes["conflict"] += 1
    friend.memes["conflict"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="loss_worry", tag="emotion", apply=_r_loss_worry),
    Rule(name="accusation_conflict", tag="social", apply=_r_accusation_conflict),
]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out is not None and len(out) >= 0:
                if out or any(sig[0] == rule.name for sig in world.fired):
                    pass
            before = len(world.fired)
            rule.apply(world)
            after = len(world.fired)
            if after > before:
                changed = True


def meddler_can_hide(meddler: Meddler, place: HidingPlace) -> bool:
    return place.reach_tag in meddler.can_reach


def helper_can_solve(helper: Helper, meddler: Meddler, place: HidingPlace) -> bool:
    sees = place.sign_visible and helper.reads_signs
    hidden = helper.sees_hidden
    return helper.peace >= 2 and (hidden or sees)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for cassette_id in CASSETTES:
            for meddler_id, meddler in MEDDLERS.items():
                for place_id, place in HIDING_PLACES.items():
                    if not meddler_can_hide(meddler, place):
                        continue
                    for helper_id, helper in HELPERS.items():
                        if helper_can_solve(helper, meddler, place):
                            combos.append((setting_id, cassette_id, meddler_id, place_id, helper_id))
    return combos


def explain_place(meddler: Meddler, place: HidingPlace) -> str:
    return (
        f"(No story: {meddler.label} cannot plausibly drag the cassette to {place.phrase}. "
        f"That hiding place is out of reach for this meddler.)"
    )


def explain_helper(helper: Helper, meddler: Meddler, place: HidingPlace) -> str:
    return (
        f"(No story: {helper.label} has no honest way to solve the misunderstanding at {place.phrase}. "
        f"The helper must be able to spot the hiding place itself or read {meddler.label}'s sign.)"
    )


def helper_method(helper: Helper, meddler: Meddler, place: HidingPlace) -> str:
    if helper.sees_hidden and helper.reads_signs and place.sign_visible:
        return f"{helper.label} noticed both the hidden cassette and the {meddler.leaves_sign}"
    if helper.sees_hidden:
        return f"{helper.label} noticed where the cassette had been tucked away"
    return f"{helper.label} followed the {meddler.leaves_sign} to the cassette"


def predict_misunderstanding(helper: Helper, meddler: Meddler, place: HidingPlace) -> dict:
    return {
        "can_solve": helper_can_solve(helper, meddler, place),
        "method": helper_method(helper, meddler, place),
    }


def setup_scene(world: World, setting: Setting, keeper: Entity, friend: Entity, cassette: CassetteKind) -> None:
    keeper.memes["love"] += 1
    friend.memes["love"] += 1
    world.say(
        f"Once, in {setting.place}, where {setting.image}, {keeper.id} and {friend.id} liked to sit together at twilight."
    )
    world.say(
        f"They shared {cassette.phrase}, and when it clicked and turned, it sang the {cassette.song_name}, a tune so gentle that even cross faces softened."
    )
    world.say(
        f"In the middle of the song came the funny fairy words 'hug-dim,' and the two children always smiled when they heard them."
    )


def cherish(world: World, keeper: Entity, friend: Entity, cassette: CassetteKind) -> None:
    world.say(
        f"{keeper.id} believed the cassette kept a little piece of moonlight in its spools, and {friend.id} said it made the room feel {cassette.comfort}."
    )


def meddle(world: World, meddler: Meddler, place: HidingPlace) -> None:
    cassette = world.get("cassette")
    cassette.meters["missing"] += 1
    cassette.attrs["hidden_at"] = place.id
    cassette.attrs["moved_by"] = meddler.id
    propagate(world)
    world.say(
        f"But while the children were following {world.facts['setting'].path}, {meddler.label} slipped close, {meddler.manner}, and carried the cassette away."
    )
    world.say(
        f"It vanished into {place.phrase}, and only {meddler.leaves_sign} was left behind."
    )


def discover_loss(world: World, keeper: Entity, friend: Entity) -> None:
    world.say(
        f"When {keeper.id} came back, the cassette was gone. {keeper.pronoun('possessive').capitalize()} heart gave a startled jump, and {friend.id} looked around in worry too."
    )


def accuse(world: World, keeper: Entity, friend: Entity, relation: str) -> None:
    keeper.memes["accusation"] += 1
    propagate(world)
    closeness = "best friend" if relation == "friends" else "little brother" if friend.type == "boy" else "little sister"
    world.say(
        f'"You hid it!" cried {keeper.id}. "You wanted the first turn, so you took it while I was away."'
    )
    world.say(
        f"{friend.id} stepped back as if the words were thorns. {friend.pronoun('subject').capitalize()} had been {keeper.pronoun('possessive')} {closeness}, so the false blame hurt all the more."
    )


def quarrel(world: World, keeper: Entity, friend: Entity) -> None:
    world.say(
        f"Soon their voices rose like two little storms. {keeper.id} folded {keeper.pronoun('possessive')} arms, and shiny tears gathered in {friend.id}'s eyes."
    )


def helper_enters(world: World, helper: Helper) -> None:
    world.say(
        f"Just then {helper.phrase} came along and heard the quarrel."
    )


def reveal(world: World, helper: Helper, meddler: Meddler, place: HidingPlace, keeper: Entity, friend: Entity) -> None:
    cassette = world.get("cassette")
    cassette.meters["missing"] = 0.0
    cassette.meters["found"] += 1
    keeper.memes["anger"] = 0.0
    keeper.memes["conflict"] = 0.0
    friend.memes["conflict"] = 0.0
    friend.memes["hurt"] = max(0.0, friend.memes["hurt"] - 1.0)
    keeper.memes["shame"] += 1
    keeper.memes["relief"] += 1
    friend.memes["relief"] += 1
    friend.memes["forgiveness"] += 1
    method = helper_method(helper, meddler, place)
    world.facts["reveal_method"] = method
    world.say(
        f'{helper.label.capitalize()} did not scold. "{helper.reveal_text}," {helper.pronoun() if hasattr(helper, "pronoun") else "they"} said softly.'
    )
    world.say(
        f"{helper.label.capitalize()} soon found the truth: {method}. There, in {place.phrase}, lay the cassette."
    )


def apology(world: World, keeper: Entity, friend: Entity) -> None:
    keeper.memes["apology"] += 1
    keeper.memes["love"] += 1
    friend.memes["love"] += 1
    world.say(
        f'{keeper.id} picked it up with trembling hands and turned to {friend.id}. "I was wrong," {keeper.pronoun()} whispered. "I let my fear speak before my heart listened."'
    )
    world.say(
        f'{friend.id} rubbed away a tear. "I did not take it," {friend.pronoun()} said, "but I still want to listen with you."'
    )


def reconcile(world: World, keeper: Entity, friend: Entity, cassette: CassetteKind) -> None:
    keeper.memes["trust"] += 1
    friend.memes["trust"] += 1
    keeper.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"So the children sat down together again. When the cassette began its soft turning and the {cassette.song_name} rose once more, {keeper.id} leaned over and gave {friend.id} a long hug."
    )
    world.say(
        f"The room seemed to grow {cassette.glow}, and from that night on, whenever they heard the words 'hug-dim,' they remembered that friendship grows dim only when people stop asking for the truth."
    )


def tell(
    setting: Setting,
    cassette_cfg: CassetteKind,
    meddler_cfg: Meddler,
    place_cfg: HidingPlace,
    helper_cfg: Helper,
    keeper_name: str,
    keeper_gender: str,
    friend_name: str,
    friend_gender: str,
    relation: str,
    temper: str,
) -> World:
    world = World()
    keeper = world.add(Entity(id="keeper", kind="character", type=keeper_gender, label=keeper_name, role="keeper", traits=[temper]))
    friend = world.add(Entity(id="friend", kind="character", type=friend_gender, label=friend_name, role="friend"))
    cassette = world.add(Entity(id="cassette", kind="thing", type="cassette", label="cassette", phrase=cassette_cfg.phrase))
    world.add(Entity(id="meddler", kind="character", type="creature", label=meddler_cfg.label, role="meddler"))
    world.add(Entity(id="helper", kind="character", type=HELPER_ENTITY_TYPES[helper_cfg.id], label=helper_cfg.label, role="helper"))
    world.facts.update(
        setting=setting,
        cassette_cfg=cassette_cfg,
        meddler_cfg=meddler_cfg,
        place_cfg=place_cfg,
        helper_cfg=helper_cfg,
        relation=relation,
        temper=temper,
        keeper=keeper,
        friend=friend,
    )

    setup_scene(world, setting, keeper, friend, cassette_cfg)
    cherish(world, keeper, friend, cassette_cfg)

    world.para()
    meddle(world, meddler_cfg, place_cfg)
    discover_loss(world, keeper, friend)
    accuse(world, keeper, friend, relation)
    quarrel(world, keeper, friend)

    world.para()
    helper_enters(world, helper_cfg)
    reveal(world, helper_cfg, meddler_cfg, place_cfg, keeper, friend)
    apology(world, keeper, friend)

    world.para()
    reconcile(world, keeper, friend, cassette_cfg)

    world.facts.update(
        outcome="reconciled",
        missing=False,
        found=True,
        blamed=True,
        forgiven=friend.memes["forgiveness"] >= THRESHOLD,
        cassette_entity=cassette,
    )
    return world


SETTINGS = {
    "moon_cottage": Setting(
        id="moon_cottage",
        place="a little moonlit cottage at the edge of the pines",
        image="the windows shone like buttered gold and the kettle hummed to itself",
        path="the silver stepping-stones to the well",
        tags={"cottage", "moon"},
    ),
    "rose_tower": Setting(
        id="rose_tower",
        place="a rose-wrapped tower above the village",
        image="lanterns blinked behind the ivy and swallows nested under the eaves",
        path="the spiral stair to the herb shelf",
        tags={"tower", "rose"},
    ),
    "willow_hollow": Setting(
        id="willow_hollow",
        place="a willow hollow beside a clear stream",
        image="the branches bowed low and the water carried stars in its ripples",
        path="the pebble path to the reed gate",
        tags={"willow", "stream"},
    ),
}

CASSETTES = {
    "lullaby": CassetteKind(
        id="lullaby",
        phrase="a pearl-colored cassette with a painted silver moon",
        song_name="Moon-Thread Lullaby",
        glow="warmer",
        comfort="safe and sleepy",
        tags={"cassette", "lullaby"},
    ),
    "dawnsong": CassetteKind(
        id="dawnsong",
        phrase="a blue cassette with a tiny sun painted on one corner",
        song_name="Dawn-Bird Round",
        glow="brighter",
        comfort="brave enough for morning",
        tags={"cassette", "song"},
    ),
    "raindance": CassetteKind(
        id="raindance",
        phrase="a green cassette dotted with little drops of gold",
        song_name="Rain-Circle Tune",
        glow="softer",
        comfort="as calm as moss after rain",
        tags={"cassette", "rain"},
    ),
}

MEDDLERS = {
    "magpie": Meddler(
        id="magpie",
        label="a bright-eyed magpie",
        leaves_sign="a black feather caught on the latch",
        sign_noun="feather",
        can_reach={"windowsill", "roof_nest", "reeds"},
        manner="hooking the ribbon in its beak",
        tags={"bird", "magpie"},
    ),
    "wind_sprite": Meddler(
        id="wind_sprite",
        label="a laughing wind-sprite",
        leaves_sign="a twist of silver thistledown on the floor",
        sign_noun="thistledown",
        can_reach={"windowsill", "reeds", "mushroom"},
        manner="twirling it away in a ring of air",
        tags={"wind", "sprite"},
    ),
    "moon_mouse": Meddler(
        id="moon_mouse",
        label="a moon-mouse with velvet feet",
        leaves_sign="a line of tiny dusty pawprints",
        sign_noun="pawprints",
        can_reach={"cupboard", "mushroom"},
        manner="nudging and tugging it with patient little paws",
        tags={"mouse", "moon"},
    ),
}

HIDING_PLACES = {
    "windowsill": HidingPlace(
        id="windowsill",
        phrase="the deep windowsill behind the curtain",
        found_line="behind the curtain on the windowsill",
        reach_tag="windowsill",
        sign_visible=True,
        tags={"window"},
    ),
    "cupboard": HidingPlace(
        id="cupboard",
        phrase="the flour cupboard under the stairs",
        found_line="inside the cupboard under the stairs",
        reach_tag="cupboard",
        sign_visible=True,
        tags={"cupboard"},
    ),
    "roof_nest": HidingPlace(
        id="roof_nest",
        phrase="a twiggy nest in the low part of the roof",
        found_line="tucked inside a nest under the eaves",
        reach_tag="roof_nest",
        sign_visible=False,
        tags={"roof", "nest"},
    ),
    "reeds": HidingPlace(
        id="reeds",
        phrase="the reeds by the stream where dragonflies hovered",
        found_line="half-hidden in the reeds",
        reach_tag="reeds",
        sign_visible=True,
        tags={"stream", "reeds"},
    ),
    "mushroom": HidingPlace(
        id="mushroom",
        phrase="the hollow under a broad red mushroom",
        found_line="under the red mushroom",
        reach_tag="mushroom",
        sign_visible=False,
        tags={"mushroom"},
    ),
}

HELPERS = {
    "owl": Helper(
        id="owl",
        label="the old owl",
        phrase="the old owl from the cedar beam",
        sees_hidden=True,
        reads_signs=True,
        peace=3,
        reveal_text="Slow hearts see straightest",
        tags={"owl", "wisdom"},
    ),
    "fairy": Helper(
        id="fairy",
        label="the seamstress fairy",
        phrase="the seamstress fairy with a lantern-needle",
        sees_hidden=False,
        reads_signs=True,
        peace=2,
        reveal_text="A true story leaves a trail if you kneel low enough",
        tags={"fairy", "signs"},
    ),
    "grandmother": Helper(
        id="grandmother",
        label="Grandmother Rowan",
        phrase="Grandmother Rowan carrying a basket of mint",
        sees_hidden=False,
        reads_signs=False,
        peace=2,
        reveal_text="Harsh guesses are poor lanterns",
        tags={"grandmother", "peace"},
    ),
}

HELPER_ENTITY_TYPES = {
    "owl": "owl",
    "fairy": "fairy",
    "grandmother": "woman",
}

GIRL_NAMES = ["Elin", "Mara", "Nella", "Poppy", "Iris", "Lina"]
BOY_NAMES = ["Tobin", "Rowan", "Finn", "Ari", "Milo", "Bram"]
TEMPER_TRAITS = ["quick", "eager", "proud", "sensitive", "earnest"]


def relation_phrase(relation: str) -> str:
    return "siblings" if relation == "siblings" else "friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    keeper = f["keeper"]
    friend = f["friend"]
    cassette = f["cassette_cfg"]
    helper = f["helper_cfg"]
    meddler = f["meddler_cfg"]
    return [
        f'Write a fairy-tale story for a 3-to-5-year-old that includes the words "hug-dim" and "cassette".',
        f"Tell a gentle misunderstanding story where {keeper.label} wrongly blames {friend.label} after a magical cassette disappears, and {helper.label} helps uncover the truth.",
        f"Write a fairy-tale conflict story in which {meddler.label} moves a treasured cassette, two children quarrel, and they make peace at the end.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    keeper = f["keeper"]
    friend = f["friend"]
    cassette = f["cassette_cfg"]
    meddler = f["meddler_cfg"]
    place = f["place_cfg"]
    helper = f["helper_cfg"]
    method = f.get("reveal_method", helper_method(helper, meddler, place))
    return [
        (
            "Who is the story about?",
            f"It is about {keeper.label} and {friend.label}, two {relation_phrase(f['relation'])} who shared a magical cassette. It is also about {helper.label}, who helped them see the truth."
        ),
        (
            "Why did the children start fighting?",
            f"They started fighting because the cassette went missing and {keeper.label} wrongly thought {friend.label} had hidden it. Fear made {keeper.pronoun()} speak too fast, so the misunderstanding turned into a quarrel."
        ),
        (
            "What really happened to the cassette?",
            f"{meddler.label.capitalize()} carried it away and left {meddler.leaves_sign}. The cassette was really in {place.phrase}, so {friend.label} had not taken it at all."
        ),
        (
            f"How did {helper.label} solve the problem?",
            f"{helper.label.capitalize()} solved it by finding the truth instead of choosing sides. {method}, and that showed everyone what had really happened."
        ),
        (
            f"What did {keeper.label} learn?",
            f"{keeper.label} learned not to blame {friend.label} before asking what was true. The story shows that friendship can be hurt by quick guesses but healed by apology and honesty."
        ),
        (
            "How did the story end?",
            f"It ended with the children listening to the cassette together again and sharing a hug. The song became proof that peace had returned after the misunderstanding."
        ),
    ]


KNOWLEDGE = {
    "cassette": [
        (
            "What is a cassette?",
            "A cassette is a small plastic case that can hold recorded sounds or songs on a ribbon inside. People used cassettes to play music and stories."
        )
    ],
    "magpie": [
        (
            "Why do magpies pick up shiny things?",
            "Magpies are curious birds, and they sometimes carry off interesting little objects. They do it because the object catches their eye, not because they understand who owns it."
        )
    ],
    "wind": [
        (
            "What can a strong wind do to light objects?",
            "A strong wind can push, roll, or lift light objects and move them somewhere else. That is why windy days can make little things disappear."
        )
    ],
    "mouse": [
        (
            "Can a mouse drag something small into a hiding place?",
            "Yes, a mouse can tug or nudge a small object into a corner or hole if it is light enough. Mice often hide things while exploring."
        )
    ],
    "owl": [
        (
            "Why do stories often use an owl as a wise helper?",
            "Owls are quiet and watchful, so fairy tales often make them seem wise. A wise helper notices things that upset people miss."
        )
    ],
    "fairy": [
        (
            "What does a fairy helper do in a fairy tale?",
            "A fairy helper often sees tiny clues and helps people act kindly. Fairy-tale helpers do not only use magic; they also help characters understand each other."
        )
    ],
    "apology": [
        (
            "Why is saying sorry important after a misunderstanding?",
            "Saying sorry helps mend hurt feelings after someone was blamed unfairly. It shows that the speaker knows the truth matters more than pride."
        )
    ],
    "friendship": [
        (
            "How can friends fix a quarrel?",
            "Friends can fix a quarrel by telling the truth, listening calmly, and apologizing when they were wrong. Kind words help trust grow back."
        )
    ],
}
KNOWLEDGE_ORDER = ["cassette", "magpie", "wind", "mouse", "owl", "fairy", "apology", "friendship"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"cassette", "apology", "friendship"}
    meddler = f["meddler_cfg"]
    helper = f["helper_cfg"]
    if meddler.id == "magpie":
        tags.add("magpie")
    elif meddler.id == "wind_sprite":
        tags.add("wind")
    elif meddler.id == "moon_mouse":
        tags.add("mouse")
    if helper.id == "owl":
        tags.add("owl")
    if helper.id == "fairy":
        tags.add("fairy")
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(sig[0] for sig in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="moon_cottage",
        cassette="lullaby",
        meddler="magpie",
        place="windowsill",
        helper="owl",
        keeper_name="Elin",
        keeper_gender="girl",
        friend_name="Tobin",
        friend_gender="boy",
        relation="friends",
        temper="quick",
    ),
    StoryParams(
        setting="rose_tower",
        cassette="dawnsong",
        meddler="wind_sprite",
        place="reeds",
        helper="fairy",
        keeper_name="Mara",
        keeper_gender="girl",
        friend_name="Finn",
        friend_gender="boy",
        relation="siblings",
        temper="proud",
    ),
    StoryParams(
        setting="willow_hollow",
        cassette="raindance",
        meddler="moon_mouse",
        place="cupboard",
        helper="owl",
        keeper_name="Rowan",
        keeper_gender="boy",
        friend_name="Iris",
        friend_gender="girl",
        relation="friends",
        temper="earnest",
    ),
    StoryParams(
        setting="moon_cottage",
        cassette="raindance",
        meddler="moon_mouse",
        place="mushroom",
        helper="owl",
        keeper_name="Lina",
        keeper_gender="girl",
        friend_name="Ari",
        friend_gender="boy",
        relation="siblings",
        temper="sensitive",
    ),
]


ASP_RULES = r"""
reachable(M, P) :- meddler(M), place(P), can_reach(M, R), place_tag(P, R).
solves(H, M, P) :- helper(H), reachable(M, P), peace(H, V), V >= 2, hidden_eye(H).
solves(H, M, P) :- helper(H), reachable(M, P), peace(H, V), V >= 2,
                   visible_sign(P), sign_reader(H).

valid(S, C, M, P, H) :- setting(S), cassette(C), reachable(M, P), solves(H, M, P).

outcome(reconciled) :- chosen_meddler(M), chosen_place(P), chosen_helper(H), reachable(M, P), solves(H, M, P).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid in CASSETTES:
        lines.append(asp.fact("cassette", cid))
    for mid, meddler in MEDDLERS.items():
        lines.append(asp.fact("meddler", mid))
        for tag in sorted(meddler.can_reach):
            lines.append(asp.fact("can_reach", mid, tag))
    for pid, place in HIDING_PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("place_tag", pid, place.reach_tag))
        if place.sign_visible:
            lines.append(asp.fact("visible_sign", pid))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("peace", hid, helper.peace))
        if helper.sees_hidden:
            lines.append(asp.fact("hidden_eye", hid))
        if helper.reads_signs:
            lines.append(asp.fact("sign_reader", hid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_meddler", params.meddler),
            asp.fact("chosen_place", params.place),
            asp.fact("chosen_helper", params.helper),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    meddler = MEDDLERS[params.meddler]
    place = HIDING_PLACES[params.place]
    helper = HELPERS[params.helper]
    return "reconciled" if meddler_can_hide(meddler, place) and helper_can_solve(helper, meddler, place) else "?"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    cases = list(CURATED)
    for seed in range(20):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            cases.append(params)
        except StoryError:
            pass
    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale story world: a magical cassette goes missing, two children misunderstand, and peace returns."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--cassette", choices=CASSETTES)
    ap.add_argument("--meddler", choices=MEDDLERS)
    ap.add_argument("--place", choices=HIDING_PLACES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--relation", choices=["friends", "siblings"])
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def _pick_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    picks = [name for name in pool if name != avoid]
    return rng.choice(picks), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.meddler and args.place:
        meddler = MEDDLERS[args.meddler]
        place = HIDING_PLACES[args.place]
        if not meddler_can_hide(meddler, place):
            raise StoryError(explain_place(meddler, place))
    if args.helper and args.place and args.meddler:
        helper = HELPERS[args.helper]
        meddler = MEDDLERS[args.meddler]
        place = HIDING_PLACES[args.place]
        if not helper_can_solve(helper, meddler, place):
            raise StoryError(explain_helper(helper, meddler, place))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.cassette is None or combo[1] == args.cassette)
        and (args.meddler is None or combo[2] == args.meddler)
        and (args.place is None or combo[3] == args.place)
        and (args.helper is None or combo[4] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, cassette_id, meddler_id, place_id, helper_id = rng.choice(sorted(combos))
    keeper_name, keeper_gender = _pick_name(rng)
    friend_name, friend_gender = _pick_name(rng, avoid=keeper_name)
    relation = args.relation or rng.choice(["friends", "siblings"])
    temper = rng.choice(TEMPER_TRAITS)
    return StoryParams(
        setting=setting_id,
        cassette=cassette_id,
        meddler=meddler_id,
        place=place_id,
        helper=helper_id,
        keeper_name=keeper_name,
        keeper_gender=keeper_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        relation=relation,
        temper=temper,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        cassette = CASSETTES[params.cassette]
        meddler = MEDDLERS[params.meddler]
        place = HIDING_PLACES[params.place]
        helper = HELPERS[params.helper]
    except KeyError as err:
        raise StoryError(f"(Invalid option: {err.args[0]})") from None

    if not meddler_can_hide(meddler, place):
        raise StoryError(explain_place(meddler, place))
    if not helper_can_solve(helper, meddler, place):
        raise StoryError(explain_helper(helper, meddler, place))

    world = tell(
        setting=setting,
        cassette_cfg=cassette,
        meddler_cfg=meddler,
        place_cfg=place,
        helper_cfg=helper,
        keeper_name=params.keeper_name,
        keeper_gender=params.keeper_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        relation=params.relation,
        temper=params.temper,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/5.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, cassette, meddler, place, helper) combos:\n")
        for combo in combos:
            print("  " + " ".join(f"{part:12}" for part in combo))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### {p.keeper_name} and {p.friend_name}: {p.cassette} / {p.meddler} / "
                f"{p.place} / {p.helper}"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
