#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/lobster_pier_quest_reconciliation_repetition_nursery_rhyme.py
=========================================================================================

A standalone story world for a nursery-rhyme-shaped pier tale about a child,
a lobster friend, a missing treasure, a small quarrel, and a make-up song.

The domain centers on three linked ideas:

* Quest: something dear goes missing on the pier, and the child searches for it.
* Reconciliation: in the worry of the loss, the child unfairly blames the lobster,
  then discovers the truth, apologizes, and repairs the friendship.
* Repetition: the search is carried by a recurring rhyme line that changes place
  while keeping the same beat.

This world models a tiny causal slice rather than swapping nouns into a fixed
paragraph. A cause (breeze / gull / wave) can move only certain kinds of items
to certain hiding places. A stronger apology is needed to mend a prouder
lobster's feelings. Unreasonable explicit choices are rejected with StoryError.

Run it
------
    python storyworlds/worlds/gpt-5.4/lobster_pier_quest_reconciliation_repetition_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4/lobster_pier_quest_reconciliation_repetition_nursery_rhyme.py --item bell --cause gull --spot bait_crate
    python storyworlds/worlds/gpt-5.4/lobster_pier_quest_reconciliation_repetition_nursery_rhyme.py --item bucket --cause breeze
    python storyworlds/worlds/gpt-5.4/lobster_pier_quest_reconciliation_repetition_nursery_rhyme.py --mood proud --apology plain
    python storyworlds/worlds/gpt-5.4/lobster_pier_quest_reconciliation_repetition_nursery_rhyme.py --all
    python storyworlds/worlds/gpt-5.4/lobster_pier_quest_reconciliation_repetition_nursery_rhyme.py --qa --json
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
from typing import Optional

# Make the shared result containers importable when this script is run directly
# from the repo root or from this nested directory.
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
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id


@dataclass
class ItemCfg:
    id: str
    label: str
    phrase: str
    tags: set[str] = field(default_factory=set)
    jingle: str = ""
    plural: bool = False


@dataclass
class CauseCfg:
    id: str
    label: str
    verse: str
    requires: set[str] = field(default_factory=set)
    spots: set[str] = field(default_factory=set)
    clue: str = ""
    clue_place: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class SpotCfg:
    id: str
    label: str
    phrase: str
    reveal: str
    tags: set[str] = field(default_factory=set)


@dataclass
class MoodCfg:
    id: str
    label: str
    hurt: int
    reply: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ApologyCfg:
    id: str
    label: str
    warmth: int
    line: str
    gift: str = ""
    tags: set[str] = field(default_factory=set)


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

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


ITEMS = {
    "ribbon": ItemCfg(
        id="ribbon",
        label="ribbon",
        phrase="a cherry-red ribbon",
        tags={"light", "soft", "ribbon"},
        jingle="red ribbon bright",
    ),
    "bell": ItemCfg(
        id="bell",
        label="bell",
        phrase="a little brass bell",
        tags={"light", "shiny", "bell"},
        jingle="bell that chimed ding-ding",
    ),
    "bucket": ItemCfg(
        id="bucket",
        label="bucket",
        phrase="a small blue bucket",
        tags={"splashable", "bucket"},
        jingle="bucket blue and neat",
    ),
    "shell_chain": ItemCfg(
        id="shell_chain",
        label="shell chain",
        phrase="a pearly shell chain",
        tags={"light", "shiny", "splashable", "shell"},
        jingle="shell chain white",
    ),
}

CAUSES = {
    "breeze": CauseCfg(
        id="breeze",
        label="sea breeze",
        verse="A breeze came skipping from the bay, so soft it seemed to play.",
        requires={"light"},
        spots={"under_bench", "post_hook"},
        clue="a fluttering scrap caught in a splinter",
        clue_place="beside a weathered bench",
        tags={"breeze", "wind"},
    ),
    "gull": CauseCfg(
        id="gull",
        label="gull",
        verse="A gull went flap and peep and prance, then stole away in a hop-and-dance.",
        requires={"shiny"},
        spots={"bait_crate", "post_hook"},
        clue="a gray-white feather by the boards",
        clue_place="near the bait tubs",
        tags={"gull", "bird"},
    ),
    "wave": CauseCfg(
        id="wave",
        label="wave",
        verse="A wave went swish against the side and gave the planks a salty ride.",
        requires={"splashable"},
        spots={"tide_pool"},
        clue="a wet trail shining in the sun",
        clue_place="by the rope rail",
        tags={"wave", "water"},
    ),
}

SPOTS = {
    "under_bench": SpotCfg(
        id="under_bench",
        label="bench",
        phrase="under the old bench",
        reveal="there, tucked in the shadow below the bench slats",
        tags={"bench"},
    ),
    "post_hook": SpotCfg(
        id="post_hook",
        label="hook",
        phrase="on a crooked post hook",
        reveal="there, looped neatly over the crooked hook on a pier post",
        tags={"hook"},
    ),
    "bait_crate": SpotCfg(
        id="bait_crate",
        label="crate",
        phrase="behind the bait crate",
        reveal="there, gleaming behind a bait crate beside the buckets",
        tags={"crate"},
    ),
    "tide_pool": SpotCfg(
        id="tide_pool",
        label="tide pool",
        phrase="in the tide pool",
        reveal="there, shining in a little tide pool between two dark stones",
        tags={"tide_pool"},
    ),
}

MOODS = {
    "gentle": MoodCfg(
        id="gentle",
        label="gentle",
        hurt=1,
        reply='"I felt a pinch in my heart, not in my claw," said Pip.',
        tags={"kind"},
    ),
    "proud": MoodCfg(
        id="proud",
        label="proud",
        hurt=2,
        reply='"I do not like sharp words," said Pip, drawing his claws close.',
        tags={"proud"},
    ),
}

APOLOGIES = {
    "plain": ApologyCfg(
        id="plain",
        label="plain apology",
        warmth=1,
        line='"I am sorry, Pip. I blamed you before I knew the truth."',
        tags={"sorry"},
    ),
    "rhyme": ApologyCfg(
        id="rhyme",
        label="rhyme apology",
        warmth=2,
        line='"Pip, Pip, pinch no more; I was wrong upon the shore. I am sorry."',
        tags={"sorry", "rhyme"},
    ),
    "gift_shell": ApologyCfg(
        id="gift_shell",
        label="gift and rhyme apology",
        warmth=3,
        line='"Pip, dear Pip, I spoke too quick. Here is a smooth shell, and I am sorry."',
        gift="a smooth pink shell",
        tags={"sorry", "gift", "rhyme"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Tess", "Ruby", "Nell", "Poppy", "Daisy", "Mabel"]
BOY_NAMES = ["Owen", "Jules", "Benji", "Theo", "Nico", "Milo", "Toby", "Finn"]
TRAITS = ["curious", "bright", "humming", "quick-footed", "merry"]


def item_can_move(item: ItemCfg, cause: CauseCfg) -> bool:
    return any(tag in item.tags for tag in cause.requires)


def cause_can_reach(cause: CauseCfg, spot: SpotCfg) -> bool:
    return spot.id in cause.spots


def combo_works(item: ItemCfg, cause: CauseCfg, spot: SpotCfg) -> bool:
    return item_can_move(item, cause) and cause_can_reach(cause, spot)


def apology_heals(apology: ApologyCfg, mood: MoodCfg) -> bool:
    return apology.warmth >= mood.hurt


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for item_id, item in ITEMS.items():
        for cause_id, cause in CAUSES.items():
            for spot_id, spot in SPOTS.items():
                if not combo_works(item, cause, spot):
                    continue
                for mood_id, mood in MOODS.items():
                    for apology_id, apology in APOLOGIES.items():
                        if apology_heals(apology, mood):
                            combos.append((item_id, cause_id, spot_id, mood_id, apology_id))
    return combos


@dataclass
class StoryParams:
    item: str
    cause: str
    spot: str
    mood: str
    apology: str
    child_name: str
    child_gender: str
    child_trait: str
    seed: Optional[int] = None


def refrain(place: str) -> str:
    return f'Tip-tap, clip-clap, along the pier we peep; "{place}, {place} -- do not sleep!"'


def route_for(spot_id: str, cause_id: str) -> list[str]:
    if cause_id == "wave":
        route = ["under_bench", "bait_crate", "tide_pool"]
    elif cause_id == "gull":
        route = ["under_bench", "post_hook", "bait_crate"]
    else:
        route = ["bait_crate", "post_hook", "under_bench"]
    if spot_id in route:
        route = [r for r in route if r != spot_id] + [spot_id]
    else:
        route.append(spot_id)
    seen: list[str] = []
    out: list[str] = []
    for rid in route:
        if rid not in seen:
            seen.append(rid)
            out.append(rid)
    return out


def outcome_of(params: StoryParams) -> str:
    if not combo_works(ITEMS[params.item], CAUSES[params.cause], SPOTS[params.spot]):
        return "invalid"
    return "reconciled" if apology_heals(APOLOGIES[params.apology], MOODS[params.mood]) else "frayed"


def introduce(world: World, child: Entity, lobster: Entity, item: ItemCfg) -> None:
    world.say(
        f"On the old wooden pier, {child.id} the {child.attrs['trait']} child met Pip the lobster by the tide rail."
    )
    world.say(
        f"{child.pronoun('possessive').capitalize()} treasure was {item.phrase}, and Pip liked to tap a claw beside its little song."
    )
    world.say(
        f'"{item.jingle.capitalize()}, {item.jingle}," {child.id} sang, while gulls wheeled and ropes gave a sleepy creak.'
    )


def lose_item(world: World, child: Entity, lobster: Entity, item_ent: Entity, cause: CauseCfg, mood: MoodCfg) -> None:
    item_ent.meters["missing"] += 1
    child.memes["worry"] += 1
    lobster.memes["hurt"] += float(mood.hurt)
    world.say(cause.verse)
    world.say(
        f"When {child.id} looked down again, the {item_ent.label} was gone."
    )
    world.say(
        f'"Oh, Pip," cried {child.id}, "did your claw carry off my {item_ent.label}?"'
    )
    world.say(mood.reply)
    world.facts["quarrel"] = True


def first_clue(world: World, cause: CauseCfg) -> None:
    world.say(
        f"They paused beside {cause.clue_place} and saw {cause.clue}. That clue did not look lobster-made at all."
    )


def search_step(world: World, child: Entity, lobster: Entity, item_ent: Entity, spot_id: str, final_spot: str, seen_clue: bool) -> bool:
    spot = SPOTS[spot_id]
    world.say(refrain(spot.label))
    if not seen_clue:
        world.say(
            f"{child.id} peeped {spot.phrase}, and Pip peeped too, but the {item_ent.label} was not there."
        )
        return False
    if spot_id != final_spot:
        world.say(
            f"{child.id} peeped {spot.phrase}, and Pip lifted one careful claw, but still the {item_ent.label} was not there."
        )
        return False
    item_ent.meters["missing"] = 0.0
    item_ent.meters["found"] += 1
    child.memes["relief"] += 1
    lobster.memes["hope"] += 1
    world.say(
        f"Then they peeped {spot.phrase}, and there it was -- {spot.reveal}."
    )
    return True


def apologize(world: World, child: Entity, lobster: Entity, apology: ApologyCfg) -> None:
    child.memes["regret"] += 1
    world.say(apology.line)
    if apology.gift:
        world.say(f"{child.id} set {apology.gift} beside Pip's claw.")
    if apology_heals(APOLOGIES[world.facts["apology"].id], MOODS[world.facts["mood"].id]):
        lobster.memes["hurt"] = 0.0
        lobster.memes["trust"] += 1
        child.memes["trust"] += 1
        child.memes["joy"] += 1
        lobster.memes["joy"] += 1
        world.say(
            '"Then let us start again," said Pip, and this time his claws opened like a little welcome.'
        )
    else:
        world.say(
            '"I hear your words," said Pip, "but my heart is still tucked up tight."'
        )


def ending(world: World, child: Entity, lobster: Entity, item_ent: Entity) -> None:
    reconciled = lobster.memes["hurt"] < THRESHOLD
    if reconciled:
        world.say(
            f'Soon {child.id} and Pip went side by side along the boards, singing, "Tip-tap, clip-clap, friends upon the pier."'
        )
        world.say(
            f"The {item_ent.label} shone safe once more, and the salty air felt kinder than before."
        )
    else:
        world.say(
            f"{child.id} held the {item_ent.label} close, but the pier felt lonelier than before."
        )


def tell(
    item: ItemCfg,
    cause: CauseCfg,
    spot: SpotCfg,
    mood: MoodCfg,
    apology: ApologyCfg,
    child_name: str,
    child_gender: str,
    child_trait: str,
) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        label=child_name,
        role="child",
        attrs={"trait": child_trait},
        traits=[child_trait],
        tags={"child"},
    ))
    lobster = world.add(Entity(
        id="Pip",
        kind="character",
        type="lobster",
        label="Pip the lobster",
        role="friend",
        traits=[mood.label],
        tags={"lobster", "friend"},
    ))
    item_ent = world.add(Entity(
        id="item",
        type="treasure",
        label=item.label,
        phrase=item.phrase,
        attrs={"plural": item.plural},
        tags=set(item.tags),
    ))
    world.facts.update(
        item=item,
        cause=cause,
        spot=spot,
        mood=mood,
        apology=apology,
        child=child,
        lobster=lobster,
        item_ent=item_ent,
        route=route_for(spot.id, cause.id),
    )

    introduce(world, child, lobster, item)

    world.para()
    lose_item(world, child, lobster, item_ent, cause, mood)

    world.para()
    clue_done = False
    found = False
    search_history: list[str] = []
    for idx, rid in enumerate(world.facts["route"]):
        if idx == 0:
            first_clue(world, cause)
            clue_done = True
        found = search_step(world, child, lobster, item_ent, rid, spot.id, clue_done)
        search_history.append(rid)
        if found:
            break
    world.facts["search_history"] = search_history
    world.facts["found"] = found

    world.para()
    apologize(world, child, lobster, apology)
    world.facts["reconciled"] = lobster.memes["hurt"] < THRESHOLD

    world.para()
    ending(world, child, lobster, item_ent)
    return world


KNOWLEDGE = {
    "lobster": [
        (
            "What is a lobster?",
            "A lobster is a sea animal with a hard shell and two claws. It lives in the water and walks along the bottom."
        )
    ],
    "pier": [
        (
            "What is a pier?",
            "A pier is a long walkway built out over the water. People can walk on it to fish, look at boats, or watch the sea."
        )
    ],
    "gull": [
        (
            "What is a gull?",
            "A gull is a seaside bird with strong wings and a loud call. It likes to look for food near beaches and piers."
        )
    ],
    "breeze": [
        (
            "What is a sea breeze?",
            "A sea breeze is a soft wind that blows near the water. It can flutter light things and make ropes and flags move."
        )
    ],
    "wave": [
        (
            "What does a wave do?",
            "A wave is moving water. It can splash, roll, and carry small things along if they are near the edge."
        )
    ],
    "apology": [
        (
            "What is an apology?",
            "An apology is when you say you are sorry after doing something hurtful or unfair. A real apology tries to mend the other person's feelings."
        )
    ],
    "reconciliation": [
        (
            "What does it mean to reconcile?",
            "To reconcile means to become friends again after a quarrel. It happens when people tell the truth, listen, and make peace."
        )
    ],
    "tide_pool": [
        (
            "What is a tide pool?",
            "A tide pool is a little pool of sea water left among rocks when the water goes back out. Small sea creatures can live or hide there."
        )
    ],
}
KNOWLEDGE_ORDER = ["lobster", "pier", "gull", "breeze", "wave", "apology", "reconciliation", "tide_pool"]


def generation_prompts(world: World) -> list[str]:
    item = world.facts["item"]
    cause = world.facts["cause"]
    return [
        f'Write a short nursery-rhyme-style story set on a pier where a child and a lobster look for {item.phrase}. Include the word "lobster".',
        f"Tell a gentle quest story in singsong prose where a missing {item.label} leads to a quarrel, a clue from the {cause.label}, and a warm reconciliation.",
        "Write a child-facing story with repetition in the middle, a small misunderstanding, and an ending image that shows two friends made up again.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    lobster = world.facts["lobster"]
    item = world.facts["item"]
    cause = world.facts["cause"]
    spot = world.facts["spot"]
    mood = world.facts["mood"]
    apology = world.facts["apology"]
    search_history = [SPOTS[sid].label for sid in world.facts.get("search_history", [])]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child on the pier, and Pip the lobster. They begin as friends, have a small quarrel, and search together for {item.phrase}."
        ),
        (
            f"Why did {child.id} think Pip had the {item.label}?",
            f"{child.id} looked down and saw the {item.label} was missing, so worry made {child.pronoun('object')} speak too quickly. In that upset moment, {child.pronoun()} blamed Pip before understanding what had really happened."
        ),
        (
            "What clue helped them know the truth?",
            f"They found {cause.clue} {cause.clue_place}. That clue pointed toward the {cause.label}, not toward Pip's claw."
        ),
        (
            "Where did they search on their quest?",
            f"They searched along the pier in a little rhyme-like trail: {', '.join(search_history)}. The repeated peeping shows how they kept going instead of giving up."
        ),
        (
            f"Where was the {item.label} at last?",
            f"It was found {spot.phrase}. The place fit what the {cause.label} could do, which is why the clue led them there."
        ),
    ]
    if world.facts.get("reconciled"):
        qa.append(
            (
                f"How did {child.id} and Pip reconcile?",
                f"{child.id} apologized with {apology.label} after learning Pip had been blamed unfairly. That apology was warm enough for a {mood.label} lobster, so Pip opened back up and the friendship felt mended."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with {child.id} and Pip walking side by side and singing together on the pier. The safe {item.label} and the shared song both show that the missing treasure and the friendship were restored."
            )
        )
    else:
        qa.append(
            (
                "Did the apology fix the quarrel right away?",
                f"No. {child.id} did say sorry, but Pip was still too hurt to feel easy again. The truth was found, yet the feelings took longer to settle."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"lobster", "pier", "apology", "reconciliation"}
    cause = world.facts["cause"]
    if "gull" in cause.tags:
        tags.add("gull")
    if "wind" in cause.tags or "breeze" in cause.tags:
        tags.add("breeze")
    if "water" in cause.tags or "wave" in cause.tags:
        tags.add("wave")
    if world.facts["spot"].id == "tide_pool":
        tags.add("tide_pool")
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
            out.extend(KNOWLEDGE[key])
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
    lines.append(f"  route: {world.facts.get('route', [])}")
    lines.append(f"  search_history: {world.facts.get('search_history', [])}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        item="bell",
        cause="gull",
        spot="bait_crate",
        mood="gentle",
        apology="plain",
        child_name="Mina",
        child_gender="girl",
        child_trait="humming",
    ),
    StoryParams(
        item="ribbon",
        cause="breeze",
        spot="post_hook",
        mood="proud",
        apology="rhyme",
        child_name="Theo",
        child_gender="boy",
        child_trait="bright",
    ),
    StoryParams(
        item="bucket",
        cause="wave",
        spot="tide_pool",
        mood="gentle",
        apology="plain",
        child_name="Poppy",
        child_gender="girl",
        child_trait="merry",
    ),
    StoryParams(
        item="shell_chain",
        cause="gull",
        spot="post_hook",
        mood="proud",
        apology="gift_shell",
        child_name="Nico",
        child_gender="boy",
        child_trait="curious",
    ),
]


def explain_combo(item: ItemCfg, cause: CauseCfg, spot: SpotCfg) -> str:
    if not item_can_move(item, cause):
        need = " or ".join(sorted(cause.requires))
        return (
            f"(No story: {cause.label} in this world only carries things that are {need}, "
            f"but {item.phrase} is not that kind of item.)"
        )
    if not cause_can_reach(cause, spot):
        good = ", ".join(sorted(cause.spots))
        return (
            f"(No story: {cause.label} would not leave the lost thing at {spot.phrase}. "
            f"Try a spot like: {good}.)"
        )
    return "(No story: this item, cause, and spot do not fit together.)"


def explain_apology(apology: ApologyCfg, mood: MoodCfg) -> str:
    return (
        f"(No story: a {apology.label} is too small to mend a {mood.label} lobster's hurt feelings. "
        f"Choose a warmer apology.)"
    )


ASP_RULES = r"""
% movement logic
movable(I, C) :- item_tag(I, T), cause_needs(C, T).
reachable(C, S) :- cause_spot(C, S).

% reconciliation logic
heals(A, M) :- apology_warmth(A, W), mood_hurt(M, H), W >= H.

valid(I, C, S, M, A) :- item(I), cause(C), spot(S), mood(M), apology(A),
                        movable(I, C), reachable(C, S), heals(A, M).

chosen_valid :- chosen_item(I), chosen_cause(C), chosen_spot(S),
                movable(I, C), reachable(C, S).

outcome(reconciled) :- chosen_mood(M), chosen_apology(A), heals(A, M), chosen_valid.
outcome(frayed) :- chosen_mood(M), chosen_apology(A), not heals(A, M), chosen_valid.
outcome(invalid) :- not chosen_valid.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        for tag in sorted(item.tags):
            lines.append(asp.fact("item_tag", item_id, tag))
    for cause_id, cause in CAUSES.items():
        lines.append(asp.fact("cause", cause_id))
        for tag in sorted(cause.requires):
            lines.append(asp.fact("cause_needs", cause_id, tag))
        for spot_id in sorted(cause.spots):
            lines.append(asp.fact("cause_spot", cause_id, spot_id))
    for spot_id in SPOTS:
        lines.append(asp.fact("spot", spot_id))
    for mood_id, mood in MOODS.items():
        lines.append(asp.fact("mood", mood_id))
        lines.append(asp.fact("mood_hurt", mood_id, mood.hurt))
    for apology_id, apology in APOLOGIES.items():
        lines.append(asp.fact("apology", apology_id))
        lines.append(asp.fact("apology_warmth", apology_id, apology.warmth))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_item", params.item),
        asp.fact("chosen_cause", params.cause),
        asp.fact("chosen_spot", params.spot),
        asp.fact("chosen_mood", params.mood),
        asp.fact("chosen_apology", params.apology),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combinations:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases: list[StoryParams] = list(CURATED)
    for item_id in ITEMS:
        for cause_id in CAUSES:
            for spot_id in SPOTS:
                for mood_id in MOODS:
                    for apology_id in APOLOGIES:
                        cases.append(StoryParams(
                            item=item_id,
                            cause=cause_id,
                            spot=spot_id,
                            mood=mood_id,
                            apology=apology_id,
                            child_name="Mina",
                            child_gender="girl",
                            child_trait="bright",
                        ))
    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated story was empty.")
        _ = sample.to_json()
        print("OK: smoke test generated a normal story sample.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child and a lobster search the pier, make up, and sing again."
    )
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--mood", choices=MOODS)
    ap.add_argument("--apology", choices=APOLOGIES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.item and args.cause and not item_can_move(ITEMS[args.item], CAUSES[args.cause]):
        cause = CAUSES[args.cause]
        item = ITEMS[args.item]
        spot = SPOTS[args.spot] if args.spot else SPOTS[next(iter(cause.spots))]
        raise StoryError(explain_combo(item, cause, spot))
    if args.cause and args.spot and not cause_can_reach(CAUSES[args.cause], SPOTS[args.spot]):
        item = ITEMS[args.item] if args.item else ITEMS[next(iter(ITEMS))]
        raise StoryError(explain_combo(item, CAUSES[args.cause], SPOTS[args.spot]))
    if args.mood and args.apology and not apology_heals(APOLOGIES[args.apology], MOODS[args.mood]):
        raise StoryError(explain_apology(APOLOGIES[args.apology], MOODS[args.mood]))

    combos = [
        c for c in valid_combos()
        if (args.item is None or c[0] == args.item)
        and (args.cause is None or c[1] == args.cause)
        and (args.spot is None or c[2] == args.spot)
        and (args.mood is None or c[3] == args.mood)
        and (args.apology is None or c[4] == args.apology)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    item_id, cause_id, spot_id, mood_id, apology_id = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if child_gender == "girl" else BOY_NAMES
    child_name = args.child_name or rng.choice(name_pool)
    child_trait = rng.choice(TRAITS)
    return StoryParams(
        item=item_id,
        cause=cause_id,
        spot=spot_id,
        mood=mood_id,
        apology=apology_id,
        child_name=child_name,
        child_gender=child_gender,
        child_trait=child_trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item: {params.item})")
    if params.cause not in CAUSES:
        raise StoryError(f"(Unknown cause: {params.cause})")
    if params.spot not in SPOTS:
        raise StoryError(f"(Unknown spot: {params.spot})")
    if params.mood not in MOODS:
        raise StoryError(f"(Unknown mood: {params.mood})")
    if params.apology not in APOLOGIES:
        raise StoryError(f"(Unknown apology: {params.apology})")

    item = ITEMS[params.item]
    cause = CAUSES[params.cause]
    spot = SPOTS[params.spot]
    mood = MOODS[params.mood]
    apology = APOLOGIES[params.apology]

    if not combo_works(item, cause, spot):
        raise StoryError(explain_combo(item, cause, spot))
    if not apology_heals(apology, mood):
        raise StoryError(explain_apology(apology, mood))

    world = tell(
        item=item,
        cause=cause,
        spot=spot,
        mood=mood,
        apology=apology,
        child_name=params.child_name,
        child_gender=params.child_gender,
        child_trait=params.child_trait,
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
        print(f"{len(combos)} compatible (item, cause, spot, mood, apology) combos:\n")
        for item_id, cause_id, spot_id, mood_id, apology_id in combos:
            print(f"  {item_id:11} {cause_id:7} {spot_id:12} {mood_id:6} {apology_id}")
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
            header = (
                f"### {p.child_name}: {p.item} / {p.cause} / {p.spot} "
                f"({p.mood}, {p.apology}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
