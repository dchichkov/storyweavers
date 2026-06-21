#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/husk_crowded_market_lesson_learned_friendship_detective.py
=====================================================================================

A standalone storyworld for a tiny detective tale in a crowded market.

Premise
-------
Two friends visit a crowded market. One child loses a small treasure in the
jostle of the crowd. In a hasty version, the owner almost blames the friend.
Then the pair slow down, gather clues like little detectives, question a nearby
seller, and recover the lost object from a plausible hiding place. The ending
proves two changes: the item is found, and the friendship grows because the
children learn to look for clues before blaming.

The required seed word "husk" appears in every story through the market setting,
and often in the hiding place itself.

Run it
------
python storyworlds/worlds/gpt-5.4/husk_crowded_market_lesson_learned_friendship_detective.py
python storyworlds/worlds/gpt-5.4/husk_crowded_market_lesson_learned_friendship_detective.py --item brass_key --spot bean_sack
python storyworlds/worlds/gpt-5.4/husk_crowded_market_lesson_learned_friendship_detective.py --spot orange_crate --item sketch_card
python storyworlds/worlds/gpt-5.4/husk_crowded_market_lesson_learned_friendship_detective.py --all
python storyworlds/worlds/gpt-5.4/husk_crowded_market_lesson_learned_friendship_detective.py --qa --json
python storyworlds/worlds/gpt-5.4/husk_crowded_market_lesson_learned_friendship_detective.py --verify
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

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
        female = {"girl", "woman", "mother"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    kind: str
    clue_text: str
    found_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Spot:
    id: str
    label: str
    phrase: str
    accepts: set[str] = field(default_factory=set)
    witness_clue: str = ""
    search_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class WitnessCfg:
    id: str
    label: str
    role_phrase: str
    near: str
    line: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


ITEMS = {
    "whistle": Item(
        id="whistle",
        label="whistle",
        phrase="a little wooden whistle",
        kind="rigid",
        clue_text="a tiny nick in the dust where something hard had bounced",
        found_text="wedged between two pale husk leaves",
        tags={"whistle", "clue"},
    ),
    "brass_key": Item(
        id="brass_key",
        label="brass key",
        phrase="a small brass key on a blue string",
        kind="dense",
        clue_text="a round, neat dip where something heavy had sunk",
        found_text="sleeping low in the beans with only its blue string showing",
        tags={"key", "clue"},
    ),
    "bracelet": Item(
        id="bracelet",
        label="bead bracelet",
        phrase="a bead bracelet with a red bead in the middle",
        kind="loop",
        clue_text="one red bead glinting beside a splintered corner",
        found_text="looped around a crate nail like a tiny ring",
        tags={"bracelet", "clue"},
    ),
    "sketch_card": Item(
        id="sketch_card",
        label="sketch card",
        phrase="a folded sketch card with a star drawn on it",
        kind="flat",
        clue_text="a square edge peeking from a fold",
        found_text="slid deep inside a soft cloth fold",
        tags={"paper", "clue"},
    ),
}

SPOTS = {
    "husk_basket": Spot(
        id="husk_basket",
        label="husk basket",
        phrase="a tall basket full of dry corn husk leaves",
        accepts={"rigid", "flat", "loop"},
        witness_clue="I heard a light rustle and saw something vanish into the husk leaves.",
        search_text="The dry husk whispered when they parted it with careful fingers.",
        tags={"husk", "market"},
    ),
    "bean_sack": Spot(
        id="bean_sack",
        label="bean sack",
        phrase="a wide sack of brown beans",
        accepts={"dense"},
        witness_clue="I saw a little flash drop straight down into the beans.",
        search_text="The beans shifted with a soft hush as they scooped through the top layer.",
        tags={"beans", "market"},
    ),
    "cloth_fold": Spot(
        id="cloth_fold",
        label="cloth fold",
        phrase="a tower of folded market cloth",
        accepts={"flat", "loop"},
        witness_clue="The crowd brushed the cloth, and something thin slipped into a fold.",
        search_text="The striped cloth made neat little valleys where a small thing could hide.",
        tags={"cloth", "market"},
    ),
    "orange_crate": Spot(
        id="orange_crate",
        label="orange crate",
        phrase="a wooden crate stacked with bright oranges",
        accepts={"loop"},
        witness_clue="Something caught for one second on the side of the crate and swung there.",
        search_text="Orange leaves and crate slats made little hooks and corners.",
        tags={"oranges", "market"},
    ),
}

WITNESSES = {
    "corn_seller": WitnessCfg(
        id="corn_seller",
        label="corn seller",
        role_phrase="the smiling corn seller",
        near="husk_basket",
        line="The corn seller tapped the basket and lowered his voice like a fellow detective.",
        tags={"husk", "seller"},
    ),
    "bean_seller": WitnessCfg(
        id="bean_seller",
        label="bean seller",
        role_phrase="the bean seller with floury hands",
        near="bean_sack",
        line="The bean seller pointed with her scoop and nodded at the floor.",
        tags={"seller"},
    ),
    "cloth_merchant": WitnessCfg(
        id="cloth_merchant",
        label="cloth merchant",
        role_phrase="the cloth merchant in a green scarf",
        near="cloth_fold",
        line="The cloth merchant lifted one folded corner and spoke very softly.",
        tags={"seller"},
    ),
    "fruit_seller": WitnessCfg(
        id="fruit_seller",
        label="fruit seller",
        role_phrase="the fruit seller behind the orange crate",
        near="orange_crate",
        line="The fruit seller leaned over the crate as if guarding a secret clue.",
        tags={"seller"},
    ),
}

TEMPERAMENTS = {
    "hasty": {
        "opening": "For one hot second, worry made the wrong idea jump into the air.",
        "tags": {"lesson", "apology"},
    },
    "steady": {
        "opening": "The loss felt scary, but both friends stood still and looked carefully.",
        "tags": {"friendship", "teamwork"},
    },
}

GIRL_NAMES = ["Mina", "Lila", "Tara", "Nora", "Asha", "Zoe", "Mira", "Rina"]
BOY_NAMES = ["Omar", "Theo", "Ben", "Arun", "Noah", "Milo", "Ravi", "Eli"]


@dataclass
class StoryParams:
    item: str
    spot: str
    witness: str
    temperament: str
    owner_name: str
    owner_gender: str
    friend_name: str
    friend_gender: str
    parent: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        item="whistle",
        spot="husk_basket",
        witness="corn_seller",
        temperament="hasty",
        owner_name="Mina",
        owner_gender="girl",
        friend_name="Omar",
        friend_gender="boy",
        parent="mother",
    ),
    StoryParams(
        item="brass_key",
        spot="bean_sack",
        witness="bean_seller",
        temperament="steady",
        owner_name="Theo",
        owner_gender="boy",
        friend_name="Lila",
        friend_gender="girl",
        parent="father",
    ),
    StoryParams(
        item="bracelet",
        spot="orange_crate",
        witness="fruit_seller",
        temperament="hasty",
        owner_name="Rina",
        owner_gender="girl",
        friend_name="Ben",
        friend_gender="boy",
        parent="mother",
    ),
    StoryParams(
        item="sketch_card",
        spot="cloth_fold",
        witness="cloth_merchant",
        temperament="steady",
        owner_name="Arun",
        owner_gender="boy",
        friend_name="Mira",
        friend_gender="girl",
        parent="father",
    ),
]


def compatible(item_id: str, spot_id: str, witness_id: str) -> bool:
    return (
        item_id in ITEMS
        and spot_id in SPOTS
        and witness_id in WITNESSES
        and ITEMS[item_id].kind in SPOTS[spot_id].accepts
        and WITNESSES[witness_id].near == spot_id
    )


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for item_id in ITEMS:
        for spot_id in SPOTS:
            for witness_id in WITNESSES:
                if compatible(item_id, spot_id, witness_id):
                    combos.append((item_id, spot_id, witness_id))
    return combos


def explain_rejection(item_id: str, spot_id: str, witness_id: Optional[str] = None) -> str:
    if item_id not in ITEMS:
        return "(No story: unknown item.)"
    if spot_id not in SPOTS:
        return "(No story: unknown spot.)"
    if witness_id is not None and witness_id not in WITNESSES:
        return "(No story: unknown witness.)"
    item = ITEMS[item_id]
    spot = SPOTS[spot_id]
    if item.kind not in spot.accepts:
        return (
            f"(No story: {item.phrase} would not plausibly end up in {spot.phrase}. "
            f"This detective world only allows hiding places that fit the lost object.)"
        )
    if witness_id is not None and WITNESSES[witness_id].near != spot_id:
        return (
            f"(No story: {WITNESSES[witness_id].role_phrase} is not standing near "
            f"{spot.phrase}, so that witness would not have the right clue.)"
        )
    return "(No story: that combination does not fit this market mystery.)"


def outcome_of(params: StoryParams) -> str:
    return "apology" if params.temperament == "hasty" else "teamwork"


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def market_intro(world: World, owner: Entity, friend: Entity, parent: Entity, item: Item) -> None:
    world.say(
        f"On market day, {owner.id} and {friend.id} walked beside {owner.id}'s "
        f"{parent.label_word} through the crowded market."
    )
    world.say(
        "Voices called from every side, baskets bumped gently past, and a breeze "
        "stirred loose bits of husk near the corn stall."
    )
    world.say(
        f"{owner.id} kept {item.phrase} in {owner.pronoun('possessive')} pocket "
        f"and liked to think of it as a detective's lucky clue."
    )


def jostle_and_loss(world: World, owner: Entity, friend: Entity, item: Item) -> None:
    owner.meters["missing"] += 1
    world.say(
        f"When a line of shoppers squeezed by, {friend.id} took {owner.id}'s hand "
        f"for a moment so they would not be parted in the crowd."
    )
    world.say(
        f"A basket brushed {owner.pronoun('possessive')} side, someone laughed, "
        f"and when the crowd opened again, {owner.id} touched {owner.pronoun('possessive')} "
        f"pocket and went still. {item.phrase.capitalize()} was gone."
    )


def hasty_suspicion(world: World, owner: Entity, friend: Entity) -> None:
    owner.memes["suspicion"] += 1
    friend.memes["hurt"] += 1
    world.say(TEMPERAMENTS["hasty"]["opening"])
    world.say(
        f'"Did you still have it?" {owner.id} blurted to {friend.id}. '
        f'{friend.id} blinked, surprised, and looked hurt.'
    )


def steady_pause(world: World, owner: Entity, friend: Entity) -> None:
    owner.memes["care"] += 1
    friend.memes["care"] += 1
    world.say(TEMPERAMENTS["steady"]["opening"])
    world.say(
        f'"Let\'s do this like detectives," {friend.id} said. "{owner.id}, what happened just before it vanished?"'
    )


def detective_turn(world: World, owner: Entity, friend: Entity, item: Item) -> None:
    owner.memes["curiosity"] += 1
    friend.memes["curiosity"] += 1
    owner.attrs["last_clue"] = item.clue_text
    world.say(
        f"{owner.id} took a slow breath. \"I felt the crowd push, and then I saw "
        f"{item.clue_text},\" {owner.pronoun()} said."
    )
    world.say(
        f"{friend.id} nodded. \"Then we follow the clue, not our feelings first.\""
    )


def ask_witness(world: World, owner: Entity, friend: Entity, witness: WitnessCfg, spot: Spot) -> None:
    witness_ent = world.get("witness")
    witness_ent.memes["helpfulness"] += 1
    world.say(
        f"They hurried to {witness.role_phrase}. {witness.line} "
        f'"I was watching {spot.phrase}," {witness_ent.pronoun()} said. '
        f'"{spot.witness_clue}"'
    )
    world.facts["witness_statement"] = spot.witness_clue


def search(world: World, owner: Entity, friend: Entity, item: Item, spot: Spot) -> None:
    owner.memes["hope"] += 1
    friend.memes["hope"] += 1
    world.say(
        f"{owner.id} and {friend.id} knelt beside {spot.phrase}. {spot.search_text}"
    )
    world.say(
        f"Then {friend.id} smiled first. {item.phrase.capitalize()} was there, "
        f"{item.found_text}."
    )
    owner.meters["missing"] = 0.0
    owner.meters["found"] += 1
    owner.memes["relief"] += 1
    friend.memes["relief"] += 1


def apology_end(world: World, owner: Entity, friend: Entity, parent: Entity, item: Item) -> None:
    owner.memes["lesson"] += 1
    owner.memes["gratitude"] += 1
    friend.memes["trust"] += 1
    world.say(
        f'{owner.id} held {item.phrase} tight. "I am sorry I almost blamed you," '
        f'{owner.pronoun()} said.'
    )
    world.say(
        f'{friend.id} gave a small nod. "{owner.id}, you came back to the clues. '
        f'That is what matters."'
    )
    world.say(
        f"{owner.id}'s {parent.label_word} squeezed both their shoulders. "
        "\"A good detective looks before guessing,\" "
        f"{parent.pronoun()} said."
    )
    world.say(
        "They walked on together, sharing a warm corn cake, and the market no longer "
        "felt noisy and mixed-up. It felt full of clues, kindness, and room for two friends."
    )


def teamwork_end(world: World, owner: Entity, friend: Entity, parent: Entity, item: Item) -> None:
    owner.memes["lesson"] += 1
    owner.memes["gratitude"] += 1
    friend.memes["trust"] += 1
    owner.memes["trust"] += 1
    world.say(
        f'"Case solved," {friend.id} whispered, and {owner.id} laughed with relief.'
    )
    world.say(
        f"{owner.id} tucked {item.phrase} away more carefully this time and thanked "
        f"{friend.id} for thinking like a real detective."
    )
    world.say(
        f"{owner.id}'s {parent.label_word} smiled. \"The best clues are easier to see "
        f"when friends stay calm together,\" {parent.pronoun()} said."
    )
    world.say(
        "After that, the two friends moved through the crowded market shoulder to shoulder, "
        "noticing rustles, colors, and footprints as if the whole morning were one bright mystery."
    )


def tell(
    item: Item,
    spot: Spot,
    witness_cfg: WitnessCfg,
    temperament: str,
    owner_name: str,
    owner_gender: str,
    friend_name: str,
    friend_gender: str,
    parent_type: str,
) -> World:
    world = World()
    owner = world.add(Entity(id=owner_name, kind="character", type=owner_gender, role="owner"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    witness_ent = world.add(
        Entity(
            id="witness",
            kind="character",
            type="woman" if witness_cfg.id in {"bean_seller", "cloth_merchant"} else "man",
            role="witness",
            label=witness_cfg.label,
        )
    )

    market_intro(world, owner, friend, parent, item)
    world.para()
    jostle_and_loss(world, owner, friend, item)

    world.para()
    if temperament == "hasty":
        hasty_suspicion(world, owner, friend)
    else:
        steady_pause(world, owner, friend)
    detective_turn(world, owner, friend, item)

    world.para()
    ask_witness(world, owner, friend, witness_cfg, spot)
    search(world, owner, friend, item, spot)

    world.para()
    if temperament == "hasty":
        apology_end(world, owner, friend, parent, item)
    else:
        teamwork_end(world, owner, friend, parent, item)

    world.facts.update(
        owner=owner,
        friend=friend,
        parent=parent,
        witness=witness_ent,
        item=item,
        spot=spot,
        witness_cfg=witness_cfg,
        temperament=temperament,
        outcome="apology" if temperament == "hasty" else "teamwork",
        friendship_strained=friend.memes["hurt"] >= THRESHOLD,
        recovered=owner.meters["found"] >= THRESHOLD,
        lesson_learned=owner.memes["lesson"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "detective": [
        (
            "What does a detective do?",
            "A detective pays attention to clues and asks careful questions. A good detective does not just guess; a good detective checks what really happened.",
        )
    ],
    "market": [
        (
            "What is a market?",
            "A market is a place where many people sell and buy things. It can be busy, noisy, and full of different smells and colors.",
        )
    ],
    "husk": [
        (
            "What is a husk?",
            "A husk is a dry outer covering around something like corn. It is light, papery, and can rustle when you touch it.",
        )
    ],
    "clue": [
        (
            "What is a clue?",
            "A clue is a small sign that helps you figure something out. A footprint, a rustle, or a shiny bead can all be clues.",
        )
    ],
    "friendship": [
        (
            "How can friends solve a problem together?",
            "Friends can slow down, listen to each other, and look for the truth together. Working as a team often helps them solve the problem more kindly and more quickly.",
        )
    ],
    "apology": [
        (
            "Why is saying sorry important?",
            "Saying sorry matters when you hurt someone's feelings or make an unfair guess. It helps repair trust and shows that you want to do better next time.",
        )
    ],
}

KNOWLEDGE_ORDER = ["market", "husk", "detective", "clue", "friendship", "apology"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    owner = f["owner"]
    friend = f["friend"]
    item = f["item"]
    spot = f["spot"]
    if f["outcome"] == "apology":
        return [
            'Write a short detective-style story for a 3-to-5-year-old set in a crowded market that includes the word "husk".',
            f"Tell a friendship story where {owner.id} loses {item.phrase} in a busy market, almost blames {friend.id}, and then follows clues to {spot.phrase}.",
            "Write a gentle mystery with a lesson learned: look for clues before blaming a friend.",
        ]
    return [
        'Write a short detective-style story for a 3-to-5-year-old set in a crowded market that includes the word "husk".',
        f"Tell a friendship mystery where {owner.id} and {friend.id} work like little detectives to recover {item.phrase}.",
        "Write a calm market mystery that ends with two friends solving the case together and learning that careful clues beat quick guesses.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    owner = f["owner"]
    friend = f["friend"]
    parent = f["parent"]
    item = f["item"]
    spot = f["spot"]
    witness_cfg = f["witness_cfg"]
    out: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two friends, {owner.id} and {friend.id}, in a crowded market. {owner.id}'s {parent.label_word} is with them, and {witness_cfg.role_phrase} helps with a clue.",
        ),
        (
            f"What was missing?",
            f"{owner.id} lost {item.phrase} when the crowd pressed close in the market. The jostle and the brushing basket made the object slip away without {owner.id} noticing right away.",
        ),
        (
            "How did they solve the mystery?",
            f"They slowed down, listened to a witness, and followed the clue to {spot.phrase}. Then they searched carefully until they found the lost object instead of guessing wildly.",
        ),
        (
            f"Where did they find the missing thing?",
            f"They found it in {spot.phrase}. That hiding place made sense because the clue pointed them there, and the object could really get caught there.",
        ),
    ]
    if f["outcome"] == "apology":
        out.append(
            (
                f"What lesson did {owner.id} learn?",
                f"{owner.id} learned not to blame {friend.id} too quickly. The truth came from the clue and the witness, so saying sorry helped mend the friendship after the unfair guess.",
            )
        )
    else:
        out.append(
            (
                f"Why were {owner.id} and {friend.id} good detectives?",
                f"They stayed calm and looked for what actually happened. Because they worked together, they saw the clue clearly and solved the problem without hurting each other's feelings.",
            )
        )
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"detective", "market", "clue", "friendship"}
    tags |= set(f["spot"].tags)
    if f["outcome"] == "apology":
        tags.add("apology")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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
    for ent in list(world.entities.values()):
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
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:10} ({ent.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(I, S, W) :- item(I), spot(S), witness(W), kind(I, K), accepts(S, K), near(W, S).

outcome(apology) :- temperament(hasty).
outcome(teamwork) :- temperament(steady).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        lines.append(asp.fact("kind", item_id, item.kind))
    for spot_id, spot in SPOTS.items():
        lines.append(asp.fact("spot", spot_id))
        for kind in sorted(spot.accepts):
            lines.append(asp.fact("accepts", spot_id, kind))
    for witness_id, witness in WITNESSES.items():
        lines.append(asp.fact("witness", witness_id))
        lines.append(asp.fact("near", witness_id, witness.near))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = asp.fact("temperament", params.temperament)
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py_combos = set(valid_combos())
    asp_combos = set(asp_valid_combos())
    if py_combos == asp_combos:
        print(f"OK: gate matches valid_combos() ({len(py_combos)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_combos - py_combos:
            print("  only in clingo:", sorted(asp_combos - py_combos))
        if py_combos - asp_combos:
            print("  only in python:", sorted(py_combos - asp_combos))

    for params in CURATED:
        if asp_outcome(params) != outcome_of(params):
            rc = 1
            print(
                f"MISMATCH in outcome for {params.item}/{params.spot}/{params.temperament}: "
                f"asp={asp_outcome(params)} python={outcome_of(params)}"
            )

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Verify failed: generated story was empty.)")
        if sample.world is None or not sample.prompts or not sample.story_qa or not sample.world_qa:
            raise StoryError("(Verify failed: generated sample was missing required outputs.)")
        print("OK: smoke test generated a normal story sample.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a crowded-market detective mystery about friendship and a lesson learned."
    )
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--witness", choices=WITNESSES)
    ap.add_argument("--temperament", choices=sorted(TEMPERAMENTS))
    ap.add_argument("--owner-name")
    ap.add_argument("--owner-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid detective-mystery combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.item and args.spot and args.witness:
        if not compatible(args.item, args.spot, args.witness):
            raise StoryError(explain_rejection(args.item, args.spot, args.witness))
    elif args.item and args.spot and ITEMS[args.item].kind not in SPOTS[args.spot].accepts:
        raise StoryError(explain_rejection(args.item, args.spot, None))
    elif args.spot and args.witness and WITNESSES[args.witness].near != args.spot:
        raise StoryError(explain_rejection(next(iter(ITEMS)), args.spot, args.witness))

    combos = [
        combo
        for combo in valid_combos()
        if (args.item is None or combo[0] == args.item)
        and (args.spot is None or combo[1] == args.spot)
        and (args.witness is None or combo[2] == args.witness)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    item_id, spot_id, witness_id = rng.choice(sorted(combos))
    temperament = args.temperament or rng.choice(sorted(TEMPERAMENTS))
    owner_name, owner_gender = (
        (args.owner_name, args.owner_gender)
        if args.owner_name and args.owner_gender
        else _pick_child(rng)
    )
    if args.owner_name and args.owner_gender is None:
        owner_gender = rng.choice(["girl", "boy"])
        owner_name = args.owner_name
    if args.owner_gender and args.owner_name is None:
        owner_gender = args.owner_gender
        owner_name = rng.choice(GIRL_NAMES if owner_gender == "girl" else BOY_NAMES)

    friend_name, friend_gender = (
        (args.friend_name, args.friend_gender)
        if args.friend_name and args.friend_gender
        else _pick_child(rng, avoid=owner_name)
    )
    if args.friend_name and args.friend_gender is None:
        friend_gender = rng.choice(["girl", "boy"])
        friend_name = args.friend_name
    if args.friend_gender and args.friend_name is None:
        friend_gender = args.friend_gender
        friend_name = rng.choice(
            [n for n in (GIRL_NAMES if friend_gender == "girl" else BOY_NAMES) if n != owner_name]
        )

    if friend_name == owner_name:
        pool = [n for n in (GIRL_NAMES + BOY_NAMES) if n != owner_name]
        friend_name = rng.choice(pool)

    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        item=item_id,
        spot=spot_id,
        witness=witness_id,
        temperament=temperament,
        owner_name=owner_name,
        owner_gender=owner_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    if params.item not in ITEMS:
        raise StoryError("(No story: unknown item key.)")
    if params.spot not in SPOTS:
        raise StoryError("(No story: unknown spot key.)")
    if params.witness not in WITNESSES:
        raise StoryError("(No story: unknown witness key.)")
    if params.temperament not in TEMPERAMENTS:
        raise StoryError("(No story: unknown temperament key.)")
    if not compatible(params.item, params.spot, params.witness):
        raise StoryError(explain_rejection(params.item, params.spot, params.witness))

    world = tell(
        item=ITEMS[params.item],
        spot=SPOTS[params.spot],
        witness_cfg=WITNESSES[params.witness],
        temperament=params.temperament,
        owner_name=params.owner_name,
        owner_gender=params.owner_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        parent_type=params.parent,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (item, spot, witness) combos:\n")
        for item_id, spot_id, witness_id in combos:
            print(f"  {item_id:11} {spot_id:12} {witness_id}")
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
            header = f"### {p.owner_name} & {p.friend_name}: {p.item} at {p.spot} ({p.temperament})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
