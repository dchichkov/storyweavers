#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/row_imperial_dandy_magic_sound_effects_mystery.py
==============================================================================

A standalone storyworld for a tiny child-facing mystery: during a pretend magic
show, something special goes missing from a neat row of props. Strange sound
effects make the loss feel spooky, but the mystery is solved by following
state-driven clues to a plausible culprit and a safe, gentle ending.

Seed constraints rebuilt as world logic
---------------------------------------
This world always includes the words "row", "imperial", and "dandy", uses a
small touch of stage magic, and keeps the tone close to a mystery.

Core premise
------------
Two children are getting ready for a tiny show. Along a row of hooks or shelves
sits one special object: an imperial-looking prop. It disappears. A culprit
creature has really taken it because the object is shiny or soft, and it leaves
a clue (feather, paw prints, ribbon trail, rustle). The children use safe stage
magic -- a glow wand, whisper tube, or echo box -- to notice the right clue.
They solve the mystery and recover the item.

Reasonableness gate
-------------------
Not every culprit can take every item to every hiding spot. The world only
generates combinations where:
- the culprit likes the kind of item,
- the culprit can reach the chosen hiding spot in the venue,
- and the clue left behind fits that culprit.

That gate is implemented in Python and mirrored with an inline ASP twin.

Run it
------
    python storyworlds/worlds/gpt-5.4/row_imperial_dandy_magic_sound_effects_mystery.py
    python storyworlds/worlds/gpt-5.4/row_imperial_dandy_magic_sound_effects_mystery.py --all
    python storyworlds/worlds/gpt-5.4/row_imperial_dandy_magic_sound_effects_mystery.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/row_imperial_dandy_magic_sound_effects_mystery.py --qa
    python storyworlds/worlds/gpt-5.4/row_imperial_dandy_magic_sound_effects_mystery.py --verify
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
    small: bool = False
    shiny: bool = False
    soft: bool = False
    climb: bool = False
    fly: bool = False
    notices_sound: bool = False
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
class Venue:
    id: str
    place: str
    row_text: str
    stage_text: str
    hiding_spots: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class MissingItem:
    id: str
    label: str
    phrase: str
    texture: str
    lure: str
    sparkle_text: str
    tags: set[str] = field(default_factory=set)
    shiny: bool = False
    soft: bool = False


@dataclass
class Culprit:
    id: str
    label: str
    phrase: str
    likes: set[str] = field(default_factory=set)
    clue: str = ""
    sound: str = ""
    move_text: str = ""
    can_reach: set[str] = field(default_factory=set)
    fly: bool = False
    climb: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class MagicTool:
    id: str
    label: str
    phrase: str
    effect: str
    notices: set[str] = field(default_factory=set)
    reveal_text: str = ""
    ending_text: str = ""
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


def _r_missing_worry(world: World) -> list[str]:
    item = world.get("item")
    if item.meters["missing"] < THRESHOLD:
        return []
    sig = ("missing_worry", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for ent in list(world.entities.values()):
        if ent.role in {"hero", "friend"}:
            ent.memes["worry"] += 1
            ent.memes["curiosity"] += 1
    return ["__mystery__"]


def _r_culprit_clue(world: World) -> list[str]:
    culprit = world.get("culprit")
    item = world.get("item")
    if culprit.meters["took_item"] < THRESHOLD or item.meters["missing"] < THRESHOLD:
        return []
    sig = ("clue", culprit.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    clue = world.get("clue")
    clue.meters["visible"] += 1
    clue.meters["fresh"] += 1
    return []


def _r_magic_notice(world: World) -> list[str]:
    magic = world.get("magic")
    clue = world.get("clue")
    if magic.meters["used"] < THRESHOLD or clue.meters["visible"] < THRESHOLD:
        return []
    sig = ("noticed", clue.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    clue.meters["noticed"] += 1
    for ent in list(world.entities.values()):
        if ent.role in {"hero", "friend"}:
            ent.memes["hope"] += 1
            ent.memes["wonder"] += 1
    return []


def _r_found_relief(world: World) -> list[str]:
    item = world.get("item")
    if item.meters["found"] < THRESHOLD:
        return []
    sig = ("found_relief", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for ent in list(world.entities.values()):
        if ent.role in {"hero", "friend"}:
            ent.memes["worry"] = 0.0
            ent.memes["relief"] += 1
            ent.memes["joy"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="missing_worry", tag="emotion", apply=_r_missing_worry),
    Rule(name="culprit_clue", tag="physical", apply=_r_culprit_clue),
    Rule(name="magic_notice", tag="epistemic", apply=_r_magic_notice),
    Rule(name="found_relief", tag="emotion", apply=_r_found_relief),
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
        for sent in produced:
            world.say(sent)
    return produced


VENUES = {
    "theater": Venue(
        id="theater",
        place="the little theater",
        row_text="a row of brass hooks beside the curtain",
        stage_text="the stage smelled faintly of dust and velvet",
        hiding_spots={"rafters", "costume_chest", "behind_curtain"},
        tags={"theater", "stage"},
    ),
    "museum": Venue(
        id="museum",
        place="the museum's children room",
        row_text="a row of polished pegs under a moonlit window",
        stage_text="the tall room held old maps, soft shadows, and one tiny stage",
        hiding_spots={"window_ledge", "display_table", "behind_screen"},
        tags={"museum", "stage"},
    ),
    "hall": Venue(
        id="hall",
        place="the town hall attic",
        row_text="a row of painted hooks near the eaves",
        stage_text="the attic felt hushed, as if every trunk were keeping a secret",
        hiding_spots={"beam", "hat_box", "under_table"},
        tags={"attic", "stage"},
    ),
}

ITEMS = {
    "cloak": MissingItem(
        id="cloak",
        label="imperial cloak pin",
        phrase="an imperial cloak pin with a red stone",
        texture="cool and smooth",
        lure="shiny",
        sparkle_text="The red stone gave off a tiny wink of light.",
        tags={"pin", "imperial", "shiny"},
        shiny=True,
        soft=False,
    ),
    "feather": MissingItem(
        id="feather",
        label="imperial plume",
        phrase="an imperial plume trimmed with gold thread",
        texture="soft and feathery",
        lure="soft",
        sparkle_text="The gold thread glimmered whenever anyone moved.",
        tags={"feather", "imperial", "soft"},
        shiny=False,
        soft=True,
    ),
    "medal": MissingItem(
        id="medal",
        label="imperial medal",
        phrase="a round imperial medal on a blue ribbon",
        texture="heavy and bright",
        lure="shiny",
        sparkle_text="Its silver face flashed like a tiny moon.",
        tags={"medal", "imperial", "shiny"},
        shiny=True,
        soft=False,
    ),
}

CULPRITS = {
    "magpie": Culprit(
        id="magpie",
        label="magpie",
        phrase="a black-and-white magpie",
        likes={"shiny"},
        clue="a feather and a scratch on the wood",
        sound="Caw-caw! Flit-flit!",
        move_text="liked bright things and could whisk them up high in a blink",
        can_reach={"rafters", "window_ledge", "beam"},
        fly=True,
        climb=False,
        tags={"bird", "shiny"},
    ),
    "kitten": Culprit(
        id="kitten",
        label="kitten",
        phrase="a velvet-pawed kitten",
        likes={"soft", "ribbon"},
        clue="tiny paw prints and one loose thread",
        sound="Mrrp! Skitter-skitter!",
        move_text="could bat light things into cozy hiding places",
        can_reach={"costume_chest", "behind_curtain", "hat_box", "under_table", "behind_screen"},
        fly=False,
        climb=True,
        tags={"cat", "soft"},
    ),
    "raccoon": Culprit(
        id="raccoon",
        label="raccoon",
        phrase="a masked raccoon with clever paws",
        likes={"shiny", "soft"},
        clue="a dusty handprint and a crinkled ribbon trail",
        sound="Rustle-rustle! Tap-tap!",
        move_text="could open lids and tug treasures into boxes or under cloth",
        can_reach={"costume_chest", "display_table", "hat_box", "under_table", "behind_screen"},
        fly=False,
        climb=True,
        tags={"raccoon", "shiny", "soft"},
    ),
}

MAGIC_TOOLS = {
    "glow_wand": MagicTool(
        id="glow_wand",
        label="glow wand",
        phrase="a glow wand painted with stars",
        effect="made soft blue light spill across the floorboards",
        notices={"feather", "paw", "ribbon"},
        reveal_text="When the wand glimmered, the smallest clue stopped hiding in the dark.",
        ending_text="The wand glowed like a tiny moon over the solved mystery.",
        tags={"magic", "light"},
    ),
    "whisper_tube": MagicTool(
        id="whisper_tube",
        label="whisper tube",
        phrase="a whisper tube wrapped in silver paper",
        effect="turned tiny sounds into clear little clues",
        notices={"sound", "rustle", "paw"},
        reveal_text="The tube caught the faintest rustle and pointed their ears the right way.",
        ending_text="The whisper tube hummed softly, as if pleased to have helped.",
        tags={"magic", "sound"},
    ),
    "echo_box": MagicTool(
        id="echo_box",
        label="echo box",
        phrase="an echo box with a brass latch",
        effect="sent a gentle ping! around the room and woke up hidden corners",
        notices={"sound", "feather", "ribbon"},
        reveal_text="Each small ping! answered from the secret place where the clue waited.",
        ending_text="The echo box gave one proud ping! as the curtain mystery ended.",
        tags={"magic", "sound"},
    ),
}

HIDING_SPOTS = {
    "rafters": "up in the rafters above the curtain",
    "costume_chest": "inside the half-open costume chest",
    "behind_curtain": "in a fold behind the stage curtain",
    "window_ledge": "on the moonlit window ledge",
    "display_table": "under the old display table",
    "behind_screen": "behind a painted folding screen",
    "beam": "on a dusty roof beam",
    "hat_box": "inside a round hat box",
    "under_table": "under a long tablecloth",
}

SPOT_CLUE_TAG = {
    "rafters": "feather",
    "window_ledge": "feather",
    "beam": "feather",
    "costume_chest": "paw",
    "behind_curtain": "paw",
    "hat_box": "paw",
    "under_table": "ribbon",
    "display_table": "ribbon",
    "behind_screen": "ribbon",
}

GIRL_NAMES = ["Lila", "Mina", "Nora", "Ivy", "Lucy", "Tessa", "June", "Maya"]
BOY_NAMES = ["Owen", "Theo", "Eli", "Max", "Finn", "Sam", "Leo", "Jude"]
TRAITS = ["careful", "bright", "curious", "gentle", "patient", "clever"]
DANDY_BITS = [
    "a dandy velvet hat with a curled brim",
    "a dandy cane painted with silver swirls",
    "a dandy little coat with shining buttons",
]


def item_lure(item: MissingItem) -> str:
    if item.shiny:
        return "shiny"
    if item.soft:
        return "soft"
    return "ribbon"


def culprit_fits(item: MissingItem, culprit: Culprit) -> bool:
    lure = item_lure(item)
    return lure in culprit.likes or (item.id == "medal" and "ribbon" in culprit.likes)


def clue_tag_for(culprit: Culprit, spot: str) -> str:
    if culprit.id == "magpie":
        return "feather"
    if culprit.id == "kitten":
        return "paw"
    return SPOT_CLUE_TAG.get(spot, "ribbon")


def valid_combo(venue_id: str, item_id: str, culprit_id: str, spot_id: str, magic_id: str) -> bool:
    venue = VENUES[venue_id]
    item = ITEMS[item_id]
    culprit = CULPRITS[culprit_id]
    magic = MAGIC_TOOLS[magic_id]
    if spot_id not in venue.hiding_spots:
        return False
    if spot_id not in culprit.can_reach:
        return False
    if not culprit_fits(item, culprit):
        return False
    needed = clue_tag_for(culprit, spot_id)
    if needed not in magic.notices:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    out: list[tuple[str, str, str, str, str]] = []
    for venue_id in VENUES:
        for item_id in ITEMS:
            for culprit_id in CULPRITS:
                for spot_id in HIDING_SPOTS:
                    for magic_id in MAGIC_TOOLS:
                        if valid_combo(venue_id, item_id, culprit_id, spot_id, magic_id):
                            out.append((venue_id, item_id, culprit_id, spot_id, magic_id))
    return out


@dataclass
class StoryParams:
    venue: str
    item: str
    culprit: str
    spot: str
    magic: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
    parent: str
    trait: str
    dandy_prop: str
    seed: Optional[int] = None


def introduce(world: World, hero: Entity, friend: Entity, venue: Venue, dandy_prop: str) -> None:
    world.say(
        f"On show night, {hero.id} and {friend.id} were in {venue.place}, where {venue.stage_text}."
    )
    world.say(
        f"Beside them stood {venue.row_text}. On it hung capes, paper stars, and {dandy_prop} for the last trick."
    )


def set_special_item(world: World, hero: Entity, item: MissingItem) -> None:
    hero.memes["pride"] += 1
    world.say(
        f"At the center of the row rested {item.phrase}. {item.sparkle_text}"
    )


def begin_show(world: World, hero: Entity, friend: Entity, magic: MagicTool) -> None:
    for child in (hero, friend):
        child.memes["joy"] += 1
        child.memes["wonder"] += 1
    world.say(
        f'"Tonight we do the moon trick first," {hero.id} whispered. {friend.id} lifted {magic.phrase}, ready to make pretend magic feel real.'
    )


def item_goes_missing(world: World, item_ent: Entity, culprit: Culprit, spot_id: str) -> None:
    item_ent.meters["missing"] += 1
    world.get("culprit").meters["took_item"] += 1
    world.facts["spot_phrase"] = HIDING_SPOTS[spot_id]
    propagate(world, narrate=False)
    world.say(
        f"Then the room made a strange little noise -- {culprit.sound} -- and when {hero_pair(world)} looked back, the {item_ent.label} was gone."
    )


def hero_pair(world: World) -> str:
    hero = world.get("hero")
    friend = world.get("friend")
    return f"{hero.id} and {friend.id}"


def worry_and_guess(world: World, hero: Entity, friend: Entity, parent: Entity) -> None:
    world.say(
        f'{friend.id} gasped. "{hero.id}, did the trick really work all by itself?"'
    )
    world.say(
        f"{hero.id} felt a shiver of mystery, but {parent.label_word} only knelt beside them and said, "
        f'"Magic can sparkle, but clues tell the truth. Let us look carefully."'
    )


def use_magic(world: World, magic: MagicTool) -> None:
    magic_ent = world.get("magic")
    magic_ent.meters["used"] += 1
    propagate(world, narrate=False)
    world.say(
        f"So {hero_pair(world)} tried the {magic.label}. It {magic.effect}."
    )
    world.say(magic.reveal_text)


def notice_clue(world: World, culprit: Culprit) -> None:
    clue = world.get("clue")
    if clue.meters["noticed"] < THRESHOLD:
        raise StoryError("The chosen magic did not reveal the clue.")
    world.say(
        f"There it was: {culprit.clue}. It was fresh enough to follow."
    )


def follow_clue(world: World, venue: Venue) -> None:
    world.say(
        f"The clue led across the boards and deeper into {venue.place}, where every shadow seemed to be keeping the answer."
    )


def solve(world: World, item: MissingItem, culprit: Culprit, spot_id: str) -> None:
    item_ent = world.get("item")
    item_ent.meters["found"] += 1
    item_ent.meters["missing"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"Behind the last dark fold they found {culprit.phrase} {HIDING_SPOTS[spot_id]}, curled around the missing {item.label}."
    )
    world.say(
        f"It was no ghost at all. The {culprit.label} had taken it because {culprit.move_text}."
    )


def gentle_fix(world: World, hero: Entity, friend: Entity, parent: Entity, item: MissingItem, culprit: Culprit, magic: MagicTool) -> None:
    for child in (hero, friend):
        child.memes["kindness"] += 1
    world.say(
        f'{parent.label_word.capitalize()} smiled. "The poor little {culprit.label} was not trying to ruin the show. {hero.id}, can you trade it a ribbon toy instead?"'
    )
    world.say(
        f"{hero.id} offered a soft spare ribbon, and the {culprit.label} let go. {friend.id} held the {item.label} carefully in both hands."
    )
    world.say(
        f"Soon the row of props was neat again, and the mystery felt smaller than before."
    )
    world.say(
        f"When the curtain rose, the children did their trick, and {magic.ending_text}"
    )


def tell(
    venue: Venue,
    item: MissingItem,
    culprit: Culprit,
    spot_id: str,
    magic: MagicTool,
    hero_name: str = "Lila",
    hero_gender: str = "girl",
    friend_name: str = "Theo",
    friend_gender: str = "boy",
    parent_type: str = "mother",
    trait: str = "curious",
    dandy_prop: str = "a dandy velvet hat with a curled brim",
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, role="hero", traits=[trait]))
    friend = world.add(Entity(id="friend", kind="character", type=friend_gender, label=friend_name, role="friend", traits=["brave"]))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the parent", role="parent"))
    item_ent = world.add(
        Entity(
            id="item",
            kind="thing",
            type="prop",
            label=item.label,
            phrase=item.phrase,
            shiny=item.shiny,
            soft=item.soft,
            tags=set(item.tags),
        )
    )
    world.add(
        Entity(
            id="culprit",
            kind="thing",
            type=culprit.label,
            label=culprit.label,
            phrase=culprit.phrase,
            fly=culprit.fly,
            climb=culprit.climb,
            tags=set(culprit.tags),
        )
    )
    world.add(
        Entity(
            id="magic",
            kind="thing",
            type="magic_tool",
            label=magic.label,
            phrase=magic.phrase,
            notices_sound=True,
            tags=set(magic.tags),
        )
    )
    world.add(
        Entity(
            id="clue",
            kind="thing",
            type="clue",
            label=culprit.clue,
            phrase=culprit.clue,
            tags={clue_tag_for(culprit, spot_id)},
        )
    )

    world.facts.update(
        venue=venue,
        item_cfg=item,
        culprit_cfg=culprit,
        magic_cfg=magic,
        spot=spot_id,
        hero_name=hero_name,
        friend_name=friend_name,
        parent=parent,
        hero=hero,
        friend=friend,
        dandy_prop=dandy_prop,
    )

    introduce(world, hero, friend, venue, dandy_prop)
    set_special_item(world, hero, item)
    begin_show(world, hero, friend, magic)

    world.para()
    item_goes_missing(world, item_ent, culprit, spot_id)
    worry_and_guess(world, hero, friend, parent)

    world.para()
    use_magic(world, magic)
    notice_clue(world, culprit)
    follow_clue(world, venue)

    world.para()
    solve(world, item, culprit, spot_id)
    gentle_fix(world, hero, friend, parent, item, culprit, magic)

    world.facts.update(
        clue_tag=clue_tag_for(culprit, spot_id),
        solved=item_ent.meters["found"] >= THRESHOLD,
        culprit_label=culprit.label,
        spot_phrase=HIDING_SPOTS[spot_id],
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    venue = f["venue"]
    item = f["item_cfg"]
    culprit = f["culprit_cfg"]
    magic = f["magic_cfg"]
    return [
        'Write a gentle mystery story for a 3-to-5-year-old that includes the words "row", "imperial", and "dandy".',
        f"Tell a child-friendly mystery set in {venue.place} where a missing {item.label} is found by following clues with {magic.label}.",
        f"Write a magical mystery with sound effects where a {culprit.label} causes a small problem, but the children solve it kindly.",
    ]


KNOWLEDGE = {
    "magic": [(
        "What is stage magic?",
        "Stage magic is pretend magic used in a show. It feels surprising, but it is really made with careful tricks and props."
    )],
    "mystery": [(
        "What is a mystery?",
        "A mystery is a problem with something hidden or unknown. You solve it by noticing clues and thinking carefully."
    )],
    "magpie": [(
        "Why do magpies take shiny things sometimes?",
        "Magpies are curious birds, and bright objects can catch their eyes. That is why a shiny trinket may tempt one."
    )],
    "kitten": [(
        "Why does a kitten hide things?",
        "Kittens like to bat and chase little objects. They sometimes push them into cozy corners while they play."
    )],
    "raccoon": [(
        "Why are raccoons good at finding hidden things?",
        "Raccoons have clever paws and like to explore boxes, lids, and cloth. They can tug small objects into new places."
    )],
    "glow_wand": [(
        "What does a glow wand do in a pretend show?",
        "A glow wand makes a soft light for a trick or game. Light helps people notice what was hidden in the dark."
    )],
    "whisper_tube": [(
        "How can listening help solve a mystery?",
        "Listening helps you catch tiny sounds like rustles or taps. Those sounds can point toward the thing you need to find."
    )],
    "echo_box": [(
        "What is an echo?",
        "An echo is a sound that bounces back after it hits a wall or other surface. It can make a room seem lively and mysterious."
    )],
    "imperial": [(
        "What does imperial mean?",
        "Imperial is a word for something grand and royal-looking. It often makes people think of crowns, medals, and old palaces."
    )],
}
KNOWLEDGE_ORDER = [
    "mystery",
    "magic",
    "imperial",
    "magpie",
    "kitten",
    "raccoon",
    "glow_wand",
    "whisper_tube",
    "echo_box",
]


def story_qa_pairs(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    parent = f["parent"]
    venue = f["venue"]
    item = f["item_cfg"]
    culprit = f["culprit_cfg"]
    magic = f["magic_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label} and {friend.label}, two children getting ready for a small show, and their {parent.label_word} who helps them think calmly."
        ),
        (
            "What went missing?",
            f"The missing object was {item.phrase}. It mattered because it sat in the middle of the prop row and was part of their show."
        ),
        (
            "Why did the disappearance feel mysterious?",
            f"It vanished right after a strange sound -- {culprit.sound} -- and the children did not see who took it. The dark corners of {venue.place} made the mystery feel even bigger."
        ),
        (
            f"How did {hero.label} and {friend.label} solve the mystery?",
            f"They used the {magic.label} to notice {culprit.clue}. That clue led them to {HIDING_SPOTS[f['spot']]}, where the missing {item.label} was hidden."
        ),
        (
            f"Why had the {culprit.label} taken the {item.label}?",
            f"The {culprit.label} took it because {culprit.move_text}. The object matched what the animal liked, so the mystery had a real cause instead of a spooky one."
        ),
        (
            "How did the story end?",
            f"It ended gently. The children traded the animal a safe ribbon toy, put the prop row back in order, and performed their trick at last."
        ),
    ]
    return qa


def world_knowledge_qa_pairs(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"mystery", "magic", "imperial", f["culprit_cfg"].id, f["magic_cfg"].id}
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
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
likes_item(C, I) :- item_lure(I, L), likes(C, L).
reachable_in_venue(V, C, S) :- venue_spot(V, S), can_reach(C, S).
magic_fits(C, S, M) :- clue_tag(C, S, T), notices(M, T).
valid(V, I, C, S, M) :- venue(V), item(I), culprit(C), spot(S), magic(M),
                        reachable_in_venue(V, C, S),
                        likes_item(C, I),
                        magic_fits(C, S, M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for venue_id, venue in VENUES.items():
        lines.append(asp.fact("venue", venue_id))
        for spot in sorted(venue.hiding_spots):
            lines.append(asp.fact("venue_spot", venue_id, spot))
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        lines.append(asp.fact("item_lure", item_id, item_lure(item)))
    for culprit_id, culprit in CULPRITS.items():
        lines.append(asp.fact("culprit", culprit_id))
        for like in sorted(culprit.likes):
            lines.append(asp.fact("likes", culprit_id, like))
        for spot in sorted(culprit.can_reach):
            lines.append(asp.fact("can_reach", culprit_id, spot))
    for magic_id, magic in MAGIC_TOOLS.items():
        lines.append(asp.fact("magic", magic_id))
        for n in sorted(magic.notices):
            lines.append(asp.fact("notices", magic_id, n))
    for spot in sorted(HIDING_SPOTS):
        lines.append(asp.fact("spot", spot))
    for culprit_id, culprit in CULPRITS.items():
        for spot in sorted(HIDING_SPOTS):
            lines.append(asp.fact("clue_tag", culprit_id, spot, clue_tag_for(culprit, spot)))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


CURATED = [
    StoryParams(
        venue="theater",
        item="cloak",
        culprit="magpie",
        spot="rafters",
        magic="echo_box",
        hero="Lila",
        hero_gender="girl",
        friend="Theo",
        friend_gender="boy",
        parent="mother",
        trait="curious",
        dandy_prop="a dandy velvet hat with a curled brim",
    ),
    StoryParams(
        venue="museum",
        item="feather",
        culprit="kitten",
        spot="behind_screen",
        magic="glow_wand",
        hero="Mina",
        hero_gender="girl",
        friend="Eli",
        friend_gender="boy",
        parent="father",
        trait="patient",
        dandy_prop="a dandy cane painted with silver swirls",
    ),
    StoryParams(
        venue="hall",
        item="medal",
        culprit="raccoon",
        spot="hat_box",
        magic="whisper_tube",
        hero="Owen",
        hero_gender="boy",
        friend="June",
        friend_gender="girl",
        parent="mother",
        trait="bright",
        dandy_prop="a dandy little coat with shining buttons",
    ),
    StoryParams(
        venue="museum",
        item="medal",
        culprit="raccoon",
        spot="display_table",
        magic="echo_box",
        hero="Nora",
        hero_gender="girl",
        friend="Finn",
        friend_gender="boy",
        parent="father",
        trait="clever",
        dandy_prop="a dandy velvet hat with a curled brim",
    ),
    StoryParams(
        venue="hall",
        item="feather",
        culprit="kitten",
        spot="hat_box",
        magic="glow_wand",
        hero="Sam",
        hero_gender="boy",
        friend="Ivy",
        friend_gender="girl",
        parent="mother",
        trait="gentle",
        dandy_prop="a dandy cane painted with silver swirls",
    ),
]


def explain_rejection(venue_id: str, item_id: str, culprit_id: str, spot_id: str, magic_id: str) -> str:
    venue = VENUES.get(venue_id)
    item = ITEMS.get(item_id)
    culprit = CULPRITS.get(culprit_id)
    magic = MAGIC_TOOLS.get(magic_id)
    if venue and spot_id not in venue.hiding_spots:
        return f"(No story: {HIDING_SPOTS.get(spot_id, spot_id)} is not a hiding place in {venue.place}.)"
    if culprit and spot_id not in culprit.can_reach:
        return f"(No story: a {culprit.label} cannot reasonably hide the item {HIDING_SPOTS.get(spot_id, spot_id)}.)"
    if item and culprit and not culprit_fits(item, culprit):
        return f"(No story: {item.phrase} would not tempt a {culprit.label} in this world.)"
    if culprit and magic:
        needed = clue_tag_for(culprit, spot_id)
        if needed not in magic.notices:
            return f"(No story: the {magic.label} would not reveal the right kind of clue for this mystery.)"
    return "(No story: this combination does not make a reasonable mystery.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a tiny magical mystery with a missing imperial prop."
    )
    ap.add_argument("--venue", choices=VENUES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--spot", choices=HIDING_SPOTS)
    ap.add_argument("--magic", choices=MAGIC_TOOLS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    venue_id = args.venue
    item_id = args.item
    culprit_id = args.culprit
    spot_id = args.spot
    magic_id = args.magic

    if all(v is not None for v in [venue_id, item_id, culprit_id, spot_id, magic_id]):
        if not valid_combo(venue_id, item_id, culprit_id, spot_id, magic_id):
            raise StoryError(explain_rejection(venue_id, item_id, culprit_id, spot_id, magic_id))

    combos = [
        combo for combo in valid_combos()
        if (args.venue is None or combo[0] == args.venue)
        and (args.item is None or combo[1] == args.item)
        and (args.culprit is None or combo[2] == args.culprit)
        and (args.spot is None or combo[3] == args.spot)
        and (args.magic is None or combo[4] == args.magic)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    venue_id, item_id, culprit_id, spot_id, magic_id = rng.choice(sorted(combos))
    hero, hero_gender = _pick_child(rng)
    friend, friend_gender = _pick_child(rng, avoid=hero)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    dandy_prop = rng.choice(DANDY_BITS)
    return StoryParams(
        venue=venue_id,
        item=item_id,
        culprit=culprit_id,
        spot=spot_id,
        magic=magic_id,
        hero=hero,
        hero_gender=hero_gender,
        friend=friend,
        friend_gender=friend_gender,
        parent=parent,
        trait=trait,
        dandy_prop=dandy_prop,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        venue = VENUES[params.venue]
        item = ITEMS[params.item]
        culprit = CULPRITS[params.culprit]
        magic = MAGIC_TOOLS[params.magic]
    except KeyError as err:
        raise StoryError(f"Unknown parameter value: {err}") from err
    if params.spot not in HIDING_SPOTS:
        raise StoryError(f"Unknown hiding spot: {params.spot}")
    if not valid_combo(params.venue, params.item, params.culprit, params.spot, params.magic):
        raise StoryError(explain_rejection(params.venue, params.item, params.culprit, params.spot, params.magic))

    world = tell(
        venue=venue,
        item=item,
        culprit=culprit,
        spot_id=params.spot,
        magic=magic,
        hero_name=params.hero,
        hero_gender=params.hero_gender,
        friend_name=params.friend,
        friend_gender=params.friend_gender,
        parent_type=params.parent,
        trait=params.trait,
        dandy_prop=params.dandy_prop,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa_pairs(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa_pairs(world)],
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


def asp_verify() -> int:
    rc = 0
    try:
        clingo_set = set(asp_valid_combos())
    except Exception as err:
        print(f"ASP verify failed to run clingo: {err}")
        return 1
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    smoke_cases = list(CURATED)
    try:
        smoke_cases.append(resolve_params(build_parser().parse_args([]), random.Random(123)))
    except StoryError as err:
        rc = 1
        print(f"Smoke-test resolve failed: {err}")

    for idx, params in enumerate(smoke_cases, 1):
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("Generated empty story.")
            emit(sample, trace=False, qa=False, header="" if idx > 1 else "== smoke test ==")
        except Exception as err:
            rc = 1
            print(f"Smoke-test generation failed on case {idx}: {err}")
            break
    if rc == 0:
        print("OK: smoke-test generation succeeded.")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (venue, item, culprit, spot, magic) combos:\n")
        for venue_id, item_id, culprit_id, spot_id, magic_id in combos:
            print(f"  {venue_id:8} {item_id:7} {culprit_id:8} {spot_id:14} {magic_id}")
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
            header = f"### {p.hero} & {p.friend}: {p.item} at {p.venue} ({p.culprit}, {p.magic})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
