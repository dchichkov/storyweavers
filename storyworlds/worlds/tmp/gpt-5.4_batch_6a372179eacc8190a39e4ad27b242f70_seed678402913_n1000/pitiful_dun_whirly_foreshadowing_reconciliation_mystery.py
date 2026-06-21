#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/pitiful_dun_whirly_foreshadowing_reconciliation_mystery.py
=====================================================================================

A small mystery storyworld about a missing club treasure, an early clue that
foreshadows the answer, and a gentle reconciliation after a wrong suspicion.

The world enforces simple common-sense constraints:

- wind can only carry light things
- a puppy can only carry soft things
- a crow only steals shiny things
- each hiding place must be reachable by that mover and able to hold that item

Every generated story includes the words "pitiful", "dun", and "whirly", keeps a
child-facing mystery tone, and ends with reconciliation grounded in the world
state.

Run it
------
    python storyworlds/worlds/gpt-5.4/pitiful_dun_whirly_foreshadowing_reconciliation_mystery.py
    python storyworlds/worlds/gpt-5.4/pitiful_dun_whirly_foreshadowing_reconciliation_mystery.py --item whistle --mover crow --place nest
    python storyworlds/worlds/gpt-5.4/pitiful_dun_whirly_foreshadowing_reconciliation_mystery.py --item key --mover puppy
    python storyworlds/worlds/gpt-5.4/pitiful_dun_whirly_foreshadowing_reconciliation_mystery.py --all --qa
    python storyworlds/worlds/gpt-5.4/pitiful_dun_whirly_foreshadowing_reconciliation_mystery.py --verify
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
    traits: set[str] = field(default_factory=set)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    dun_feature: str
    available_places: set[str] = field(default_factory=set)


@dataclass
class LostItem:
    id: str
    label: str
    phrase: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Mover:
    id: str
    label: str
    verb_past: str
    moves_tags: set[str] = field(default_factory=set)
    clue_line: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class HidingPlace:
    id: str
    label: str
    phrase: str
    accepts_movers: set[str] = field(default_factory=set)
    accepts_item_tags: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Quarrel:
    id: str
    setup: str
    suspicion: str
    apology: str


@dataclass
class StoryParams:
    setting: str
    item: str
    mover: str
    place: str
    quarrel: str
    relationship: str
    finder_name: str
    finder_gender: str
    friend_name: str
    friend_gender: str
    parent_type: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
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


def propagate(world: World) -> None:
    item = world.get("item")
    finder = world.get("finder")
    friend = world.get("friend")

    if item.meters["missing"] >= THRESHOLD and ("missing_worry",) not in world.fired:
        world.fired.add(("missing_worry",))
        finder.memes["worry"] += 1

    if finder.memes["suspects_friend"] >= THRESHOLD and ("hurt",) not in world.fired:
        world.fired.add(("hurt",))
        friend.memes["hurt"] += 1

    if item.meters["found"] >= THRESHOLD and ("relief",) not in world.fired:
        world.fired.add(("relief",))
        finder.memes["relief"] += 1
        friend.memes["relief"] += 1
        finder.memes["suspects_friend"] = 0.0

    if item.meters["found"] >= THRESHOLD and finder.memes["apology"] >= THRESHOLD and ("reconcile",) not in world.fired:
        world.fired.add(("reconcile",))
        finder.memes["trust"] += 1
        friend.memes["trust"] += 1
        finder.memes["warmth"] += 1
        friend.memes["warmth"] += 1


SETTINGS = {
    "courtyard": Setting(
        id="courtyard",
        place="the stone courtyard behind a dun shed",
        dun_feature="a dun shed with one crooked door",
        available_places={"bush", "basket", "nest"},
    ),
    "schoolyard": Setting(
        id="schoolyard",
        place="the little school garden by a dun fence",
        dun_feature="a dun fence with peeling paint",
        available_places={"bush", "basket", "nest"},
    ),
    "farmyard": Setting(
        id="farmyard",
        place="the quiet farm path beside a dun barn",
        dun_feature="a dun barn wall warm from the afternoon sun",
        available_places={"bush", "basket", "nest"},
    ),
}

ITEMS = {
    "ribbon": LostItem(
        id="ribbon",
        label="ribbon badge",
        phrase="a red ribbon badge for the Mystery Club",
        tags={"light", "soft"},
    ),
    "map": LostItem(
        id="map",
        label="paper map",
        phrase="a folded paper map with a star drawn on it",
        tags={"light", "flat"},
    ),
    "whistle": LostItem(
        id="whistle",
        label="silver whistle",
        phrase="a silver whistle that flashed in the sun",
        tags={"small", "shiny", "hard"},
    ),
    "key": LostItem(
        id="key",
        label="brass key",
        phrase="a brass key on a blue string",
        tags={"small", "shiny", "hard"},
    ),
}

MOVERS = {
    "wind": Mover(
        id="wind",
        label="wind",
        verb_past="blew",
        moves_tags={"light"},
        clue_line="A whirly little wind toy near the gate kept spinning toward the edge of the yard.",
        tags={"wind", "weather"},
    ),
    "puppy": Mover(
        id="puppy",
        label="puppy",
        verb_past="carried",
        moves_tags={"soft"},
        clue_line="From somewhere nearby came a pitiful little whine, soft enough to miss if nobody listened twice.",
        tags={"dog", "pet"},
    ),
    "crow": Mover(
        id="crow",
        label="crow",
        verb_past="snatched",
        moves_tags={"shiny"},
        clue_line="A black feather drifted down while a crow flapped up above them and gave one sharp caw.",
        tags={"bird", "crow"},
    ),
}

PLACES = {
    "bush": HidingPlace(
        id="bush",
        label="thorn bush",
        phrase="the thorn bush by the path",
        accepts_movers={"wind", "puppy"},
        accepts_item_tags={"light", "soft"},
        tags={"bush"},
    ),
    "basket": HidingPlace(
        id="basket",
        label="picnic basket",
        phrase="the half-open picnic basket under the bench",
        accepts_movers={"puppy"},
        accepts_item_tags={"soft", "small"},
        tags={"basket"},
    ),
    "nest": HidingPlace(
        id="nest",
        label="magpie nest",
        phrase="a nest tucked on a low branch",
        accepts_movers={"crow"},
        accepts_item_tags={"small", "shiny", "light"},
        tags={"nest", "tree"},
    ),
}

QUARRELS = {
    "leader": Quarrel(
        id="leader",
        setup="They had already had a tiny cross moment about who should be captain of the case.",
        suspicion='Because of that, the missing thing suddenly felt like more than a mistake.',
        apology='"I let our captain argument make me think the worst,"',
    ),
    "magnifier": Quarrel(
        id="magnifier",
        setup="A little earlier, they had both reached for the same magnifying glass at once.",
        suspicion='That prickly feeling was still hanging in the air when the item disappeared.',
        apology='"I was still sore about the magnifying glass,"',
    ),
    "chalk": Quarrel(
        id="chalk",
        setup="Before the mystery even began, they had fussed over who could keep the blue chalk.",
        suspicion='So when something went missing, the old grumble puffed up again.',
        apology='"I mixed up the chalk quarrel with this mystery,"',
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Nora", "Lucy", "Maya", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Finn", "Eli", "Theo"]


def mover_can_move(item: LostItem, mover: Mover) -> bool:
    return bool(item.tags & mover.moves_tags)


def place_can_hold(item: LostItem, place: HidingPlace) -> bool:
    return bool(item.tags & place.accepts_item_tags)


def valid_combo(setting_id: str, item_id: str, mover_id: str, place_id: str) -> bool:
    if setting_id not in SETTINGS or item_id not in ITEMS or mover_id not in MOVERS or place_id not in PLACES:
        return False
    setting = SETTINGS[setting_id]
    item = ITEMS[item_id]
    mover = MOVERS[mover_id]
    place = PLACES[place_id]
    return (
        place_id in setting.available_places
        and mover_id in place.accepts_movers
        and mover_can_move(item, mover)
        and place_can_hold(item, place)
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for item_id in ITEMS:
            for mover_id in MOVERS:
                for place_id in PLACES:
                    if valid_combo(setting_id, item_id, mover_id, place_id):
                        out.append((setting_id, item_id, mover_id, place_id))
    return sorted(out)


def explain_rejection(setting_id: str, item_id: str, mover_id: str, place_id: str) -> str:
    if setting_id not in SETTINGS:
        return f"(No story: unknown setting '{setting_id}'.)"
    if item_id not in ITEMS:
        return f"(No story: unknown item '{item_id}'.)"
    if mover_id not in MOVERS:
        return f"(No story: unknown mover '{mover_id}'.)"
    if place_id not in PLACES:
        return f"(No story: unknown place '{place_id}'.)"
    setting = SETTINGS[setting_id]
    item = ITEMS[item_id]
    mover = MOVERS[mover_id]
    place = PLACES[place_id]
    if place_id not in setting.available_places:
        return f"(No story: {place.phrase} does not belong in {setting.place}.)"
    if mover_id not in place.accepts_movers:
        return f"(No story: a {mover.label} would not reasonably hide something in {place.phrase}.)"
    if not mover_can_move(item, mover):
        return f"(No story: {item.phrase} is not the kind of thing a {mover.label} would realistically move.)"
    if not place_can_hold(item, place):
        return f"(No story: {item.phrase} would not plausibly end up in {place.phrase}.)"
    return "(No story: that combination is not reasonable.)"


def relation_phrase(relationship: str) -> str:
    return "siblings" if relationship == "siblings" else "friends"


def clue_notice(world: World, mover: Mover, place: HidingPlace) -> None:
    if mover.id == "wind":
        world.say(mover.clue_line)
        world.say(f"The leaves beside {place.phrase} gave a dry little shiver, but the children were too busy making plans to care.")
    elif mover.id == "puppy":
        world.say(mover.clue_line)
        world.say(f"Near {place.phrase}, something thumped once and then fell quiet.")
    else:
        world.say(mover.clue_line)
        world.say(f"The feather drifted toward {place.phrase}, though nobody guessed yet what it meant.")


def move_item(world: World, mover: Mover, place: HidingPlace) -> None:
    item = world.get("item")
    item.meters["missing"] += 1
    item.attrs["moved_by"] = mover.id
    item.attrs["place"] = place.id
    propagate(world)


def suspicion(world: World, quarrel: Quarrel) -> None:
    finder = world.get("finder")
    friend = world.get("friend")
    finder.memes["suspects_friend"] += 1
    propagate(world)
    world.say(
        f'{finder.id} looked at {friend.id}. "Did you take it?" {finder.pronoun()} asked.'
    )
    if friend.memes["hurt"] >= THRESHOLD:
        world.say(
            f'{friend.id} blinked hard. "No," {friend.pronoun()} said. {friend.pronoun("subject").capitalize()} sounded more hurt than angry.'
        )
    world.say(quarrel.suspicion)


def investigate(world: World, mover: Mover, place: HidingPlace, item_cfg: LostItem) -> None:
    finder = world.get("finder")
    friend = world.get("friend")
    world.para()
    world.say(
        f"Then both children stopped and listened the way real detectives do when a room feels full of secrets."
    )
    if mover.id == "wind":
        world.say(
            f'{friend.id} pointed to the whirly toy and the shaking leaves. "Look," {friend.pronoun()} whispered. "The wind keeps pushing that way."'
        )
    elif mover.id == "puppy":
        world.say(
            f'{friend.id} tipped {friend.pronoun("possessive")} head. "Listen," {friend.pronoun()} whispered. "That pitiful little sound is coming from over there."'
        )
    else:
        world.say(
            f'{friend.id} lifted the black feather. "This fell from above," {friend.pronoun()} said. "Let\'s look up, not down."'
        )
    world.say(f"They hurried to {place.phrase}.")
    if mover.id == "wind":
        world.say(f"There was the {item_cfg.label}, caught and fluttering where the branches snagged it.")
    elif mover.id == "puppy":
        world.say(f"There was the {item_cfg.label}, tucked inside as if it had become part of a small, secret bed.")
    else:
        world.say(f"There was the {item_cfg.label}, shining between twigs like a tiny piece of moon.")
    item = world.get("item")
    item.meters["found"] += 1
    propagate(world)
    finder.attrs["solved_with"] = friend.id
    world.facts["found_place"] = place.label
    world.facts["mover_seen"] = mover.label


def reconcile(world: World, quarrel: Quarrel) -> None:
    finder = world.get("finder")
    friend = world.get("friend")
    finder.memes["apology"] += 1
    propagate(world)
    world.para()
    world.say(
        f'{finder.id} held the treasure with both hands and looked ashamed. {finder.pronoun("subject").capitalize()} took one small breath. {quarrel.apology} {finder.pronoun()} said. "I should have followed the clue before I blamed you."'
    )
    world.say(
        f'{friend.id} touched the edge of the found thing and nodded. "I was hurt," {friend.pronoun()} admitted, "but I know you were worried."'
    )
    if finder.memes["warmth"] >= THRESHOLD and friend.memes["warmth"] >= THRESHOLD:
        world.say(
            f"Then they smiled at each other, and the hard little knot between them came loose."
        )
    world.say(
        f"Together they made a new club rule: in a mystery, clues come first and blame comes last."
    )


def ending(world: World, setting: Setting, item_cfg: LostItem) -> None:
    finder = world.get("finder")
    friend = world.get("friend")
    relation = world.facts["relationship"]
    pair = "siblings" if relation == "siblings" else "friends"
    world.say(
        f"By the time the evening shadows leaned across {setting.dun_feature}, the two {pair} were side by side again."
    )
    world.say(
        f"The {item_cfg.label} was back where it belonged, and the case felt solved in the best way: not only the missing thing, but also the hurt feelings, had been found and mended."
    )


def tell(
    setting: Setting,
    item_cfg: LostItem,
    mover: Mover,
    place: HidingPlace,
    quarrel: Quarrel,
    relationship: str,
    finder_name: str,
    finder_gender: str,
    friend_name: str,
    friend_gender: str,
    parent_type: str,
) -> World:
    world = World()
    finder = world.add(Entity(id="finder", kind="character", type=finder_gender, label=finder_name, phrase=finder_name, role="finder"))
    friend = world.add(Entity(id="friend", kind="character", type=friend_gender, label=friend_name, phrase=friend_name, role="friend"))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the parent", phrase=parent_type, role="parent"))
    item = world.add(Entity(id="item", kind="thing", type="item", label=item_cfg.label, phrase=item_cfg.phrase, traits=set(item_cfg.tags)))
    world.facts.update(
        setting=setting,
        item_cfg=item_cfg,
        mover=mover,
        place=place,
        quarrel=quarrel,
        relationship=relationship,
        finder=finder,
        friend=friend,
        parent=parent,
    )
    finder.attrs["name"] = finder_name
    friend.attrs["name"] = friend_name
    world.facts["relationship"] = relationship

    world.say(
        f"{finder_name} and {friend_name} were {relation_phrase(relationship)} with a club made for small mysteries."
    )
    world.say(
        f"That afternoon they met in {setting.place}, and the password for the day was whispered over {item_cfg.phrase}."
    )
    world.say(quarrel.setup)

    world.para()
    clue_notice(world, mover, place)
    world.say(
        f"A moment later, {finder_name} set down the {item_cfg.label} while the two of them bent over a chalk mark on the ground."
    )
    move_item(world, mover, place)
    world.say(
        f"When {finder_name} looked back, the {item_cfg.label} was gone."
    )
    if world.get("finder").memes["worry"] >= THRESHOLD:
        world.say(
            f"A cold little mystery feeling ran through {finder_name}'s chest."
        )
    suspicion(world, quarrel)

    investigate(world, mover, place, item_cfg)
    reconcile(world, quarrel)
    world.para()
    ending(world, setting, item_cfg)
    return world


def pair_noun(finder: Entity, friend: Entity, relationship: str) -> str:
    if relationship == "siblings":
        if finder.type == "boy" and friend.type == "boy":
            return "two siblings"
        if finder.type == "girl" and friend.type == "girl":
            return "two siblings"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    finder = f["finder"]
    friend = f["friend"]
    item_cfg = f["item_cfg"]
    setting = f["setting"]
    mover = f["mover"]
    return [
        'Write a short mystery for a 3-to-5-year-old that includes the words "pitiful", "dun", and "whirly", and ends with reconciliation.',
        f"Tell a gentle mystery story where {finder.label} wrongly suspects {friend.label} after {item_cfg.phrase} goes missing in {setting.place}, and an early clue foreshadows the true answer.",
        f"Write a child-facing mystery in which a {mover.label} moves a missing object, the children solve the case by noticing clues, and they make up at the end.",
    ]


KNOWLEDGE = {
    "wind": [
        (
            "What can wind do to light things?",
            "Wind can push or carry very light things. If paper or ribbon is loose, a gust may blow it somewhere else."
        )
    ],
    "dog": [
        (
            "Why might a puppy carry something away?",
            "A puppy may pick up soft things because they smell interesting or feel fun to carry. Puppies do not understand that a child may need the thing back."
        )
    ],
    "crow": [
        (
            "Why do crows sometimes take shiny things?",
            "Crows notice bright, shiny objects easily. A shiny thing can catch a bird's eye and make it curious."
        )
    ],
    "bush": [
        (
            "Why can a bush hide things?",
            "A bush has many leaves and branches, so a small object can get caught inside and be hard to see."
        )
    ],
    "basket": [
        (
            "Why is a basket a good hiding place by accident?",
            "A basket is open at the top and can hold many things. Something small can slip inside and disappear from quick eyes."
        )
    ],
    "nest": [
        (
            "What is a nest for?",
            "A nest is a bird's home made from twigs and soft bits. Birds use it to keep eggs or chicks safe."
        )
    ],
    "mystery": [
        (
            "What is a clue in a mystery?",
            "A clue is a small sign that helps you figure something out. A sound, a feather, or shaking leaves can all be clues."
        )
    ],
    "apology": [
        (
            "Why is saying sorry important?",
            "Saying sorry helps mend hurt feelings after a mistake. It shows that you understand the hurt and want to do better."
        )
    ],
}
KNOWLEDGE_ORDER = ["mystery", "wind", "dog", "crow", "bush", "basket", "nest", "apology"]


def story_qa_pairs(world: World) -> list[tuple[str, str]]:
    f = world.facts
    finder = f["finder"]
    friend = f["friend"]
    item_cfg = f["item_cfg"]
    mover = f["mover"]
    place = f["place"]
    setting = f["setting"]
    relationship = f["relationship"]
    pair = pair_noun(finder, friend, relationship)
    out = [
        (
            "Who is the story about?",
            f"It is about {pair}, {finder.label} and {friend.label}, who were trying to solve a small mystery together."
        ),
        (
            f"What went missing?",
            f"The missing thing was {item_cfg.phrase}. Its disappearance is what opened the mystery."
        ),
        (
            "What clue came before the children understood the mystery?",
            (
                f"The story gave an early clue before the answer was known. {mover.clue_line} "
                f"That clue pointed toward {place.phrase}, but the children did not understand it at first."
            ),
        ),
        (
            f"Why did {finder.label} accuse {friend.label}?",
            (
                f"{finder.label} was worried because the {item_cfg.label} vanished right after their small quarrel. "
                f"The worry made {finder.pronoun('object')} jump to blame before following the clue."
            ),
        ),
        (
            "How was the mystery solved?",
            (
                f"They stopped arguing and paid attention to the real clue, which led them to {place.phrase}. "
                f"There they found the {item_cfg.label} and understood that the {mover.label} had moved it."
            ),
        ),
        (
            "How did the children reconcile?",
            (
                f"{finder.label} apologized for blaming {friend.label} too quickly, and {friend.label} admitted the accusation had hurt. "
                f"Because the truth was found and the apology was honest, the two children felt close again."
            ),
        ),
        (
            "How did the story end?",
            (
                f"It ended peacefully in {setting.place}, with the {item_cfg.label} returned and the friendship repaired. "
                f"The final image shows that the mystery and the hurt feelings were both mended."
            ),
        ),
    ]
    return out


def world_knowledge_pairs(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"mystery", "apology"} | set(f["mover"].tags) | set(f["place"].tags)
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits: list[str] = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={sorted(ent.traits)}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A small child-facing mystery storyworld with foreshadowing and reconciliation."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--mover", choices=MOVERS)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quarrel", choices=QUARRELS)
    ap.add_argument("--relationship", choices=["friends", "siblings"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include prompts and QA")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    explicit = all(getattr(args, key) is not None for key in ("setting", "item", "mover", "place"))
    if explicit and not valid_combo(args.setting, args.item, args.mover, args.place):
        raise StoryError(explain_rejection(args.setting, args.item, args.mover, args.place))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.item is None or combo[1] == args.item)
        and (args.mover is None or combo[2] == args.mover)
        and (args.place is None or combo[3] == args.place)
    ]
    if not combos:
        use_setting = args.setting or next(iter(SETTINGS))
        use_item = args.item or next(iter(ITEMS))
        use_mover = args.mover or next(iter(MOVERS))
        use_place = args.place or next(iter(PLACES))
        raise StoryError(explain_rejection(use_setting, use_item, use_mover, use_place))

    setting_id, item_id, mover_id, place_id = rng.choice(combos)
    quarrel_id = args.quarrel or rng.choice(sorted(QUARRELS))
    relationship = args.relationship or rng.choice(["friends", "siblings"])
    finder_name, finder_gender = pick_child(rng)
    friend_name, friend_gender = pick_child(rng, avoid=finder_name)
    parent_type = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        setting=setting_id,
        item=item_id,
        mover=mover_id,
        place=place_id,
        quarrel=quarrel_id,
        relationship=relationship,
        finder_name=finder_name,
        finder_gender=finder_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        parent_type=parent_type,
    )


def generate(params: StoryParams) -> StorySample:
    if not valid_combo(params.setting, params.item, params.mover, params.place):
        raise StoryError(explain_rejection(params.setting, params.item, params.mover, params.place))
    if params.quarrel not in QUARRELS:
        raise StoryError(f"(No story: unknown quarrel '{params.quarrel}'.)")
    world = tell(
        setting=SETTINGS[params.setting],
        item_cfg=ITEMS[params.item],
        mover=MOVERS[params.mover],
        place=PLACES[params.place],
        quarrel=QUARRELS[params.quarrel],
        relationship=params.relationship,
        finder_name=params.finder_name,
        finder_gender=params.finder_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        parent_type=params.parent_type,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa_pairs(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_pairs(world)],
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


CURATED = [
    StoryParams(
        setting="courtyard",
        item="ribbon",
        mover="puppy",
        place="basket",
        quarrel="leader",
        relationship="friends",
        finder_name="Lily",
        finder_gender="girl",
        friend_name="Tom",
        friend_gender="boy",
        parent_type="mother",
    ),
    StoryParams(
        setting="schoolyard",
        item="whistle",
        mover="crow",
        place="nest",
        quarrel="magnifier",
        relationship="siblings",
        finder_name="Ben",
        finder_gender="boy",
        friend_name="Mia",
        friend_gender="girl",
        parent_type="father",
    ),
    StoryParams(
        setting="farmyard",
        item="map",
        mover="wind",
        place="bush",
        quarrel="chalk",
        relationship="friends",
        finder_name="Zoe",
        finder_gender="girl",
        friend_name="Max",
        friend_gender="boy",
        parent_type="mother",
    ),
]


ASP_RULES = r"""
movable(I, M) :- item_tag(I, T), mover_moves(M, T).
fits(I, P) :- item_tag(I, T), place_accepts_tag(P, T).
reachable(P, M) :- place_accepts_mover(P, M).
valid(S, I, M, P) :- setting(S), item(I), mover(M), place(P),
                     available(S, P), movable(I, M), fits(I, P), reachable(P, M).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        for place_id in sorted(setting.available_places):
            lines.append(asp.fact("available", setting_id, place_id))
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        for tag in sorted(item.tags):
            lines.append(asp.fact("item_tag", item_id, tag))
    for mover_id, mover in MOVERS.items():
        lines.append(asp.fact("mover", mover_id))
        for tag in sorted(mover.moves_tags):
            lines.append(asp.fact("mover_moves", mover_id, tag))
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for mover_id in sorted(place.accepts_movers):
            lines.append(asp.fact("place_accepts_mover", place_id, mover_id))
        for tag in sorted(place.accepts_item_tags):
            lines.append(asp.fact("place_accepts_tag", place_id, tag))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: ASP valid set matches Python valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_set - py_set:
            print("  only in ASP:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in Python:", sorted(py_set - asp_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story")
        if len(sample.story_qa) < 3 or len(sample.world_qa) < 2:
            raise StoryError("QA generation too small")
        print("OK: smoke test generation succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    parser = build_parser()
    for seed in range(10):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("empty story during random verify")
        except Exception as err:  # pragma: no cover
            rc = 1
            print(f"RANDOM GENERATION FAILED at seed {seed}: {err}")
            break
    else:
        print("OK: random generation smoke test passed on 10 seeds.")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (setting, item, mover, place) combos:\n")
        for setting_id, item_id, mover_id, place_id in combos:
            print(f"  {setting_id:10} {item_id:8} {mover_id:6} {place_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
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
            header = f"### {p.finder_name} and {p.friend_name}: {p.item} / {p.mover} / {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
