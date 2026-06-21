#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/wilderness_place_variety_quest_reconciliation_dialogue_rhyming.py
================================================================================================

A standalone storyworld for a gentle wilderness quest told in a lightly rhyming
style. Two children set out to find a hidden place in the wild. They disagree
about how to go, get stuck, talk it through, reconcile, and succeed by joining
their different strengths.

Core domain idea
----------------
A quest should not feel like shuffled nouns. This world models:

* a concrete wilderness place with its own terrain,
* a clue that only makes sense in some kinds of places,
* a piece of gear that only helps on the matching terrain,
* two children whose emotional state shifts from eager -> cross -> sorry ->
  trusting again.

Reasonableness gate
-------------------
Not every clue works in every place, and not every tool fits every trail.
Stories are only generated when:

* the clue is sensible for that place, and
* the gear can handle the place's terrain.

This is enforced in Python and mirrored by an inline ASP twin.

Run it
------
    python storyworlds/worlds/gpt-5.4/wilderness_place_variety_quest_reconciliation_dialogue_rhyming.py
    python storyworlds/worlds/gpt-5.4/wilderness_place_variety_quest_reconciliation_dialogue_rhyming.py --place moon_cave
    python storyworlds/worlds/gpt-5.4/wilderness_place_variety_quest_reconciliation_dialogue_rhyming.py --place pine_ridge --gear lantern
    python storyworlds/worlds/gpt-5.4/wilderness_place_variety_quest_reconciliation_dialogue_rhyming.py --all
    python storyworlds/worlds/gpt-5.4/wilderness_place_variety_quest_reconciliation_dialogue_rhyming.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/wilderness_place_variety_quest_reconciliation_dialogue_rhyming.py --verify
"""

from __future__ import annotations

import argparse
import copy
import io
import json
import os
import random
import sys
from collections import defaultdict
from contextlib import redirect_stdout
from dataclasses import dataclass, field
from typing import Callable, Optional

# Make the shared result containers importable when this script is run directly.
# This file lives under storyworlds/worlds/gpt-5.4/, so three dirname() calls
# reach storyworlds/.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "grandmother", "sister"}
        male = {"boy", "father", "man", "grandfather", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


# ---------------------------------------------------------------------------
# Domain knobs
# ---------------------------------------------------------------------------
@dataclass
class Place:
    id: str
    label: str
    terrain: str
    opening: str
    obstacle: str
    ending_image: str
    clue_ok: set[str] = field(default_factory=set)
    need: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    find_text: str
    read_text: str
    listen_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gear:
    id: str
    label: str
    phrase: str
    use_text: str
    handles: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_stall(world: World) -> list[str]:
    team = world.get("team")
    a = world.get("a")
    b = world.get("b")
    if a.memes["cross"] >= THRESHOLD and b.memes["cross"] >= THRESHOLD and team.meters["progress"] < THRESHOLD:
        sig = ("stall",)
        if sig not in world.fired:
            world.fired.add(sig)
            team.meters["stalled"] += 1
    return []


def _r_reconcile(world: World) -> list[str]:
    team = world.get("team")
    a = world.get("a")
    b = world.get("b")
    if a.memes["sorry"] >= THRESHOLD and b.memes["sorry"] >= THRESHOLD and a.memes["listen"] >= THRESHOLD and b.memes["listen"] >= THRESHOLD:
        sig = ("reconcile",)
        if sig not in world.fired:
            world.fired.add(sig)
            a.memes["cross"] = 0.0
            b.memes["cross"] = 0.0
            a.memes["trust"] += 1
            b.memes["trust"] += 1
            team.meters["together"] += 1
    return []


def _r_progress(world: World) -> list[str]:
    team = world.get("team")
    if team.meters["together"] >= THRESHOLD and team.meters["clue_read"] >= THRESHOLD and team.meters["gear_used"] >= THRESHOLD:
        sig = ("progress",)
        if sig not in world.fired:
            world.fired.add(sig)
            team.meters["progress"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="stall", apply=_r_stall),
    Rule(name="reconcile", apply=_r_reconcile),
    Rule(name="progress", apply=_r_progress),
]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        before = (
            world.get("team").meters["stalled"],
            world.get("team").meters["together"],
            world.get("team").meters["progress"],
            world.get("a").memes["trust"],
            world.get("b").memes["trust"],
        )
        for rule in CAUSAL_RULES:
            rule.apply(world)
        after = (
            world.get("team").meters["stalled"],
            world.get("team").meters["together"],
            world.get("team").meters["progress"],
            world.get("a").memes["trust"],
            world.get("b").memes["trust"],
        )
        if after != before:
            changed = True


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------
PLACES = {
    "fern_glen": Place(
        id="fern_glen",
        label="Fern Glen",
        terrain="soft",
        opening="where fern fronds brushed their knees and bees hummed low",
        obstacle="a soggy patch where the mossy ground drank every toe",
        ending_image="a green round place with a spring that sang below",
        clue_ok={"petals", "footprints"},
        need="boots",
        tags={"wilderness", "glen", "spring"},
    ),
    "pine_ridge": Place(
        id="pine_ridge",
        label="Pine Ridge",
        terrain="steep",
        opening="where pine trees stitched the sky and wind blew bright and wide",
        obstacle="a steep stone step above a narrow, needled side",
        ending_image="a high, bright place where hawks could wheel and glide",
        clue_ok={"footprints", "echo_song"},
        need="rope",
        tags={"wilderness", "ridge", "height"},
    ),
    "moon_cave": Place(
        id="moon_cave",
        label="Moon Cave",
        terrain="dark",
        opening="where the wilderness grew cool and silver shadows swam",
        obstacle="a tunnel deep enough to hide the path in velvet dim",
        ending_image="a still, echoing place with a pool as clear as glass",
        clue_ok={"echo_song", "petals"},
        need="lantern",
        tags={"wilderness", "cave", "echo"},
    ),
}

CLUES = {
    "petals": Clue(
        id="petals",
        label="petals",
        find_text="pink petals lay in a twisty trail like notes that liked to twirl",
        read_text="they followed the petal trail, curl by curl",
        listen_text="The petals showed a gentle way and made the children slow their whirl.",
        tags={"petal", "trail"},
    ),
    "footprints": Clue(
        id="footprints",
        label="footprints",
        find_text="small hoofprints dotted the ground in a neat and bouncy row",
        read_text="they matched the prints from toe to toe",
        listen_text="The prints asked for careful looking, not a rushy go-go-go.",
        tags={"track", "trail"},
    ),
    "echo_song": Clue(
        id="echo_song",
        label="echo song",
        find_text="a far-off echo answered back with a tum-tum, ring-a-rhyme",
        read_text="they paused, called softly, and listened for the second chime",
        listen_text="The echo song could only help if both were quiet at the same time.",
        tags={"echo", "sound"},
    ),
}

GEAR = {
    "boots": Gear(
        id="boots",
        label="boots",
        phrase="their splashy red boots",
        use_text="The boots kept the mud from gulping their feet with a squish and a swoop.",
        handles={"soft"},
        tags={"boots", "trail"},
    ),
    "rope": Gear(
        id="rope",
        label="rope",
        phrase="a sturdy blue rope",
        use_text="The rope gave their climbing steps a safe little loop after loop.",
        handles={"steep"},
        tags={"rope", "trail"},
    ),
    "lantern": Gear(
        id="lantern",
        label="lantern",
        phrase="a starry camping lantern",
        use_text="The lantern poured a warm round light and shooed the shadows from the group.",
        handles={"dark"},
        tags={"lantern", "light"},
    ),
}

GIRL_NAMES = ["Lila", "Maya", "Nora", "Tess", "Wren", "Ivy", "Ruby", "Ella"]
BOY_NAMES = ["Owen", "Milo", "Finn", "Theo", "Jasper", "Noah", "Eli", "Ben"]


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    clue: str
    gear: str
    leader_name: str
    leader_gender: str
    partner_name: str
    partner_gender: str
    relation: str
    leader_age: int = 6
    partner_age: int = 7
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="fern_glen",
        clue="petals",
        gear="boots",
        leader_name="Milo",
        leader_gender="boy",
        partner_name="Lila",
        partner_gender="girl",
        relation="siblings",
        leader_age=5,
        partner_age=7,
    ),
    StoryParams(
        place="pine_ridge",
        clue="footprints",
        gear="rope",
        leader_name="Tess",
        leader_gender="girl",
        partner_name="Owen",
        partner_gender="boy",
        relation="friends",
        leader_age=6,
        partner_age=6,
    ),
    StoryParams(
        place="moon_cave",
        clue="echo_song",
        gear="lantern",
        leader_name="Finn",
        leader_gender="boy",
        partner_name="Ivy",
        partner_gender="girl",
        relation="siblings",
        leader_age=6,
        partner_age=8,
    ),
    StoryParams(
        place="moon_cave",
        clue="petals",
        gear="lantern",
        leader_name="Ruby",
        leader_gender="girl",
        partner_name="Theo",
        partner_gender="boy",
        relation="friends",
        leader_age=7,
        partner_age=7,
    ),
    StoryParams(
        place="pine_ridge",
        clue="echo_song",
        gear="rope",
        leader_name="Ben",
        leader_gender="boy",
        partner_name="Wren",
        partner_gender="girl",
        relation="siblings",
        leader_age=5,
        partner_age=8,
    ),
]


# ---------------------------------------------------------------------------
# Reasonableness gate and outcome
# ---------------------------------------------------------------------------
def valid_combo(place_id: str, clue_id: str, gear_id: str) -> bool:
    if place_id not in PLACES or clue_id not in CLUES or gear_id not in GEAR:
        return False
    place = PLACES[place_id]
    clue = CLUES[clue_id]
    gear = GEAR[gear_id]
    return clue.id in place.clue_ok and place.terrain in gear.handles and gear.id == place.need


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for place_id in sorted(PLACES):
        for clue_id in sorted(CLUES):
            for gear_id in sorted(GEAR):
                if valid_combo(place_id, clue_id, gear_id):
                    out.append((place_id, clue_id, gear_id))
    return out


def outcome_of(params: StoryParams) -> str:
    older_partner = params.relation == "siblings" and params.partner_age > params.leader_age
    return "easy_reconcile" if older_partner else "talked_through"


def explain_rejection(place_id: str, clue_id: str, gear_id: str) -> str:
    if place_id not in PLACES:
        return f"(No story: unknown place '{place_id}'.)"
    if clue_id not in CLUES:
        return f"(No story: unknown clue '{clue_id}'.)"
    if gear_id not in GEAR:
        return f"(No story: unknown gear '{gear_id}'.)"
    place = PLACES[place_id]
    clue = CLUES[clue_id]
    gear = GEAR[gear_id]
    if clue.id not in place.clue_ok:
        return (
            f"(No story: {clue.label} is not a sensible clue for {place.label}. "
            f"Pick one of: {', '.join(sorted(place.clue_ok))}.)"
        )
    if place.terrain not in gear.handles:
        return (
            f"(No story: {gear.label} does not fit the {place.terrain} trail at {place.label}. "
            f"Use {place.need} instead.)"
        )
    if gear.id != place.need:
        return (
            f"(No story: this world keeps one clean fix for {place.label}; "
            f"the right gear there is {place.need}.)"
        )
    return "(No story: unreasonable combination.)"


# ---------------------------------------------------------------------------
# Screenplay helpers
# ---------------------------------------------------------------------------
def relation_word(relation: str) -> str:
    return "siblings" if relation == "siblings" else "friends"


def place_intro(world: World, a: Entity, b: Entity, place: Place) -> None:
    world.say(
        f'In the wilderness one windy day, {a.id} and {b.id} ran out to play. '
        f'They had a quest, a bright-faced race, to find a hidden, singing place.'
    )
    world.say(
        f"They walked toward {place.label}, {place.opening}. "
        f'"Let\'s find it fast," said {a.id}. "{place.label} can be our secret place at last!"'
    )


def clue_found(world: World, a: Entity, b: Entity, clue: Clue) -> None:
    a.memes["eager"] += 1
    b.memes["eager"] += 1
    world.say(
        f"Soon {clue.find_text}. "
        f'"I can read the clue," said {b.id}. "Slow steps help us know."'
    )


def quarrel(world: World, a: Entity, b: Entity) -> None:
    a.memes["cross"] += 1
    b.memes["cross"] += 1
    world.say(
        f'"Slow is too slow," said {a.id}. "Come on, come on, come on!" '
        f'"But rushing makes the path go wrong," said {b.id}. "Please listen till the clue is done."'
    )
    propagate(world)


def stuck(world: World, place: Place) -> None:
    team = world.get("team")
    if team.meters["stalled"] >= THRESHOLD:
        world.say(
            f"They reached {place.obstacle}. One pulled ahead, one held back tight, "
            f"and neither way alone was right."
        )


def pause_and_feel(world: World, a: Entity, b: Entity, outcome: str) -> None:
    a.memes["worry"] += 1
    b.memes["worry"] += 1
    if outcome == "easy_reconcile":
        world.say(
            f'{b.id} took a breath and spoke up first. "We are a team before a race. '
            f'I don\'t want cross words in our place."'
        )
    else:
        world.say(
            f"For one small beat they stood apart, with prickly feelings in each heart. "
            f"Then {a.id} looked down and scuffed a shoe."
        )


def apology(world: World, a: Entity, b: Entity) -> None:
    a.memes["sorry"] += 1
    b.memes["sorry"] += 1
    a.memes["listen"] += 1
    b.memes["listen"] += 1
    propagate(world)
    world.say(
        f'"I was too hasty," said {a.id}. "I rushed ahead of you." '
        f'"And I was sharp," said {b.id}. "I should have spoken kinder too."'
    )
    world.say(
        f'"Let\'s try again together," said {a.id}. '
        f'"Yes," said {b.id}, "your brave feet and my careful eyes make a better pair than two."'
    )


def use_clue_and_gear(world: World, clue: Clue, gear: Gear) -> None:
    team = world.get("team")
    team.meters["clue_read"] += 1
    team.meters["gear_used"] += 1
    propagate(world)
    world.say(clue.read_text)
    world.say(gear.use_text)


def arrival(world: World, a: Entity, b: Entity, place: Place) -> None:
    team = world.get("team")
    if team.meters["progress"] >= THRESHOLD:
        a.memes["joy"] += 1
        b.memes["joy"] += 1
        world.say(
            f"At last they found {place.label}, {place.ending_image}. "
            f"The air held such a happy variety of fern and stone and feather and sky."
        )
        world.say(
            f'"We found it!" laughed {a.id}. "And more than that," said {b.id}, "we found the way to try."'
        )
        world.say(
            f"They sat close down in their new-found place, with kinder words and easy grace. "
            f"In wilderness wide, beneath the blue, their mended friendship felt brand-new."
        )


def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    clue = CLUES[params.clue]
    gear = GEAR[params.gear]

    world = World()
    a = world.add(Entity(id="a", kind="character", type=params.leader_gender, label=params.leader_name, role="leader"))
    b = world.add(Entity(id="b", kind="character", type=params.partner_gender, label=params.partner_name, role="partner"))
    team = world.add(Entity(id="team", type="team", label="the team"))
    a.attrs.update({"name": params.leader_name, "relation": params.relation, "age": params.leader_age})
    b.attrs.update({"name": params.partner_name, "relation": params.relation, "age": params.partner_age})

    world.facts.update(
        place=place,
        clue=clue,
        gear=gear,
        relation=params.relation,
        outcome=outcome_of(params),
        leader=a,
        partner=b,
    )

    place_intro(world, a, b, place)
    clue_found(world, a, b, clue)

    world.para()
    quarrel(world, a, b)
    stuck(world, place)
    pause_and_feel(world, a, b, world.facts["outcome"])

    world.para()
    apology(world, a, b)
    use_clue_and_gear(world, clue, gear)
    arrival(world, a, b, place)

    world.facts.update(
        reconciled=team.meters["together"] >= THRESHOLD,
        progressed=team.meters["progress"] >= THRESHOLD,
        stalled=team.meters["stalled"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "wilderness": [
        (
            "What is wilderness?",
            "Wilderness is a place with lots of nature, like trees, rocks, streams, and animals, and not many buildings. It can feel big and wild, so people walk carefully there."
        )
    ],
    "trail": [
        (
            "What is a trail?",
            "A trail is a path people follow through grass, woods, hills, or other wild places. It helps walkers know where to go."
        )
    ],
    "boots": [
        (
            "Why are boots helpful on soft, muddy ground?",
            "Boots protect your feet and help you step through wet, squishy places. They make slipping and soggy toes less likely."
        )
    ],
    "rope": [
        (
            "What can a rope help with on a steep trail?",
            "A rope can give people something steady to hold while they climb. It helps them move more safely on high or rocky ground."
        )
    ],
    "lantern": [
        (
            "Why is a lantern useful in a dark cave?",
            "A lantern gives light, so people can see where they are going. That makes dark places easier and safer to explore."
        )
    ],
    "echo": [
        (
            "What is an echo?",
            "An echo is a sound that bounces back after you make a noise. In caves or among rocks, you can hear your own voice come back to you."
        )
    ],
    "tracks": [
        (
            "What are footprints or tracks?",
            "Tracks are marks left by feet or hooves on the ground. They can show which way a person or animal went."
        )
    ],
    "sorry": [
        (
            "Why does saying sorry help friends?",
            "Saying sorry shows that you know you hurt someone's feelings. It opens the door for trust and kindness to come back."
        )
    ],
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork means people help one another and use their different strengths together. A problem can become easier when nobody tries to do it all alone."
        )
    ],
}

KNOWLEDGE_ORDER = ["wilderness", "trail", "boots", "rope", "lantern", "echo", "tracks", "sorry", "teamwork"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["leader"]
    b = f["partner"]
    place = f["place"]
    clue = f["clue"]
    gear = f["gear"]
    return [
        'Write a short rhyming story for a 3-to-5-year-old that includes the words "wilderness", "place", and "variety".',
        f"Tell a gentle quest story where {a.label} and {b.label} argue on the way to {place.label}, then reconcile through dialogue and succeed together.",
        f"Write a child-facing rhyming story in which a clue made of {clue.label} and {gear.label} help two children find a hidden place in the wilderness after they make up.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["leader"]
    b = f["partner"]
    place = f["place"]
    clue = f["clue"]
    gear = f["gear"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {a.label} and {b.label}, two {relation_word(f['relation'])} on a quest in the wilderness. They want to find a hidden place together."
        ),
        (
            "What was their quest?",
            f"They were trying to find {place.label}, a special place in the wild. The quest gave them a goal to share, even when they started to disagree."
        ),
        (
            "Why did they argue?",
            f"They argued because {a.label} wanted to hurry and {b.label} wanted to slow down and read the clue carefully. Their different ways of moving turned one trail into a quarrel."
        ),
    ]
    if f.get("stalled"):
        qa.append(
            (
                "What went wrong before they made up?",
                f"They got stuck at {place.obstacle} because one pulled ahead and the other held back. They could not make progress while they were cross with each other."
            )
        )
    if f.get("reconciled"):
        qa.append(
            (
                "How did they reconcile?",
                f"They talked honestly and each said sorry. That helped them listen again, so trust came back between them."
            )
        )
    if f.get("progressed"):
        qa.append(
            (
                f"How did the clue and the {gear.label} help them?",
                f"The clue gave them the right way to look or listen, and the {gear.label} helped them handle the hard part of the trail. They succeeded because they used both careful thinking and the right tool."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"They found {place.label} and sat together in peace. The ending shows that the real change was not only reaching the place, but mending their friendship on the way there."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"wilderness", "trail", "sorry", "teamwork"}
    clue = f["clue"]
    gear = f["gear"]
    if clue.id == "echo_song":
        tags.add("echo")
    if clue.id == "footprints":
        tags.add("tracks")
    if gear.id in {"boots", "rope", "lantern"}:
        tags.add(gear.id)
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        attrs = {k: v for k, v in e.attrs.items() if v != ""}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if attrs:
            bits.append(f"attrs={attrs}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid(P, C, G) :- place(P), clue(C), gear(G), clue_ok(P, C), handles(G, T), terrain(P, T), need(P, G).

older_partner :- relation(siblings), partner_age(PA), leader_age(LA), PA > LA.
outcome(easy_reconcile) :- older_partner.
outcome(talked_through) :- not older_partner.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("terrain", pid, place.terrain))
        lines.append(asp.fact("need", pid, place.need))
        for clue_id in sorted(place.clue_ok):
            lines.append(asp.fact("clue_ok", pid, clue_id))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    for gid, gear in GEAR.items():
        lines.append(asp.fact("gear", gid))
        for terrain in sorted(gear.handles):
            lines.append(asp.fact("handles", gid, terrain))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("relation", params.relation),
            asp.fact("leader_age", params.leader_age),
            asp.fact("partner_age", params.partner_age),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0

    py_gate = set(valid_combos())
    asp_gate = set(asp_valid_combos())
    if py_gate == asp_gate:
        print(f"OK: gate matches valid_combos() ({len(py_gate)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_gate - py_gate:
            print("  only in clingo:", sorted(asp_gate - py_gate))
        if py_gate - asp_gate:
            print("  only in python:", sorted(py_gate - asp_gate))

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    # Smoke test ordinary generation and emit.
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated story was empty.")
        buf = io.StringIO()
        with redirect_stdout(buf):
            emit(sample, trace=True, qa=True, header="### smoke test")
        print("OK: smoke test generation and emit passed.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Standard storyworld interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A rhyming wilderness quest where two children disagree, reconcile, and find a hidden place."
    )
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--clue", choices=sorted(CLUES))
    ap.add_argument("--gear", choices=sorted(GEAR))
    ap.add_argument("--relation", choices=["siblings", "friends"])
    ap.add_argument("--leader-name")
    ap.add_argument("--partner-name")
    ap.add_argument("--leader-gender", choices=["girl", "boy"])
    ap.add_argument("--partner-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.clue and args.gear and not valid_combo(args.place, args.clue, args.gear):
        raise StoryError(explain_rejection(args.place, args.clue, args.gear))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.clue is None or combo[1] == args.clue)
        and (args.gear is None or combo[2] == args.gear)
    ]
    if not combos:
        if args.place and args.clue and args.gear:
            raise StoryError(explain_rejection(args.place, args.clue, args.gear))
        raise StoryError("(No valid combination matches the given options.)")

    place_id, clue_id, gear_id = rng.choice(sorted(combos))
    relation = args.relation or rng.choice(["siblings", "friends"])
    leader_gender = args.leader_gender or rng.choice(["girl", "boy"])
    partner_gender = args.partner_gender or rng.choice(["girl", "boy"])
    leader_name = args.leader_name or _pick_name(rng, leader_gender)
    partner_name = args.partner_name or _pick_name(rng, partner_gender, avoid=leader_name)
    if relation == "siblings":
        ages = sorted(rng.sample([5, 6, 7, 8], 2))
        leader_age, partner_age = ages[0], ages[1]
    else:
        leader_age, partner_age = rng.choice([5, 6, 7]), rng.choice([5, 6, 7])

    return StoryParams(
        place=place_id,
        clue=clue_id,
        gear=gear_id,
        leader_name=leader_name,
        leader_gender=leader_gender,
        partner_name=partner_name,
        partner_gender=partner_gender,
        relation=relation,
        leader_age=leader_age,
        partner_age=partner_age,
    )


def generate(params: StoryParams) -> StorySample:
    if not valid_combo(params.place, params.clue, params.gear):
        raise StoryError(explain_rejection(params.place, params.clue, params.gear))

    world = tell(params)
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
        print(f"{len(combos)} compatible (place, clue, gear) combos:\n")
        for place_id, clue_id, gear_id in combos:
            print(f"  {place_id:10} {clue_id:10} {gear_id}")
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
                f"### {p.leader_name} & {p.partner_name}: {p.place} with {p.clue} "
                f"and {p.gear} ({outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
