#!/usr/bin/env python3
"""
storyworlds/worlds/shiny_cat_fire_station_inner_monologue_magic.py
=================================================================

A standalone mystery-leaning storyworld from the seed:

    Words: shiny cat
    Setting: fire station
    Features: Inner Monologue, Magic
    Style: Mystery

Source tale written for this world
----------------------------------
One drizzly evening, a thoughtful child stayed at a fire station while the crew
finished small chores before bed. Strange little signs kept appearing: a shy
click from the engine board, a smoky puff from the hose room, or a tug-tug from
the old bell loft. Then a shiny cat padded out of the shadows.

The cat did not talk, but it had a little magic. Moonlight ran along its fur,
and its whiskers or collar showed the child exactly where the hidden trouble
was. The child's private question was the real turn of the story: was the shiny
cat only playing, or was it asking for help?

By checking the physical clue instead of following a feeling blindly, the child
called the captain to the right place. Together they solved a small fire-station
mystery, and the ending image proved the change: the station grew calm, the real
problem was gone, and the shiny cat settled at last.

Model shape
-----------
The fire station, the child, the shiny cat, the clue channel, and the hidden
mystery are all physical carriers with meters and memes. The child's inner
monologue matters only when it leads to a concrete check, and the cat's magic
only changes the story when it is embedded in a visible clue inside the station.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "captainess", "firefighter"}
        male = {"boy", "man", "captain", "firefighter_man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def reflexive(self) -> str:
        female = {"girl", "woman", "captainess", "firefighter"}
        male = {"boy", "man", "captain", "firefighter_man"}
        if self.type in female:
            return "herself"
        if self.type in male:
            return "himself"
        return "themself"


@dataclass
class FireStation:
    id: str
    name: str
    hall: str
    night_sound: str
    final_image: str
    supports: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class MagicCat:
    id: str
    name: str
    coat: str
    clue_mode: str
    entrance: str
    lead_action: str
    magic_phrase: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    opening_sign: str
    hidden_place: str
    needs: str
    reveal: str
    risk: str
    captain_action: str
    fixed_image: str
    outcome: str
    lesson: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    station: str
    cat: str
    mystery: str
    hero: str
    gender: str
    trait: str
    captain: str
    seed: Optional[int] = None


class World:
    def __init__(self, station: FireStation) -> None:
        self.station = station
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def role(self, role: str) -> Optional[Entity]:
        return next((e for e in self.entities.values() if e.role == role), None)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.station)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_cat_focus(world: World) -> list[str]:
    hero = world.role("hero")
    cat = world.role("cat")
    clue = world.get("clue")
    if not hero or not cat:
        return []
    if cat.memes["guiding"] < THRESHOLD or clue.meters["available"] < THRESHOLD:
        return []
    sig = ("cat_focus", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["attention"] += 1
    clue.meters["visible"] += 1
    return []


def _r_magic_reveals(world: World) -> list[str]:
    hero = world.role("hero")
    cat = world.role("cat")
    mystery = world.get("mystery")
    clue = world.get("clue")
    if not hero or not cat:
        return []
    if hero.memes["caution"] < THRESHOLD or clue.meters["visible"] < THRESHOLD:
        return []
    sig = ("magic_reveal", mystery.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    mystery.meters["revealed"] += 1
    cat.meters["glow"] += 1
    hero.memes["clarity"] += 1
    return []


def _r_call_captain(world: World) -> list[str]:
    hero = world.role("hero")
    captain = world.role("captain")
    mystery = world.get("mystery")
    if not hero or not captain:
        return []
    if hero.memes["choose_check"] < THRESHOLD or mystery.meters["revealed"] < THRESHOLD:
        return []
    sig = ("call_captain", captain.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    captain.meters["called"] += 1
    hero.memes["bravery"] += 1
    return []


def _r_station_calm(world: World) -> list[str]:
    station = world.get("station")
    captain = world.role("captain")
    mystery = world.get("mystery")
    hero = world.role("hero")
    if not captain or not hero:
        return []
    if captain.meters["called"] < THRESHOLD or mystery.meters["revealed"] < THRESHOLD:
        return []
    sig = ("station_calm", station.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    mystery.meters["resolved"] += 1
    station.meters["calm"] += 1
    hero.memes["wonder"] += 1
    captain.memes["trust"] += 1
    return []


CAUSAL_RULES = [
    Rule("cat_focus", "physical_magic", _r_cat_focus),
    Rule("magic_reveals", "magic_inner", _r_magic_reveals),
    Rule("call_captain", "inner_social", _r_call_captain),
    Rule("station_calm", "resolution", _r_station_calm),
]


def propagate(world: World) -> None:
    changed = True
    while changed:
        before = len(world.fired)
        for rule in CAUSAL_RULES:
            for sentence in rule.apply(world):
                world.say(sentence)
        changed = len(world.fired) != before


def mystery_fits_station(station: FireStation, mystery: Mystery) -> bool:
    return mystery.needs in station.supports


def cat_can_solve(cat: MagicCat, mystery: Mystery) -> bool:
    return cat.clue_mode == mystery.needs


def valid_story(station_id: str, cat_id: str, mystery_id: str) -> bool:
    station = STATIONS[station_id]
    cat = CATS[cat_id]
    mystery = MYSTERIES[mystery_id]
    return mystery_fits_station(station, mystery) and cat_can_solve(cat, mystery)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for station_id, station in STATIONS.items():
        for cat_id, cat in CATS.items():
            for mystery_id, mystery in MYSTERIES.items():
                if mystery_fits_station(station, mystery) and cat_can_solve(cat, mystery):
                    combos.append((station_id, cat_id, mystery_id))
    return sorted(combos)


def outcome_of(params: StoryParams) -> str:
    return MYSTERIES[params.mystery].outcome


def travel_phrase(mystery: Mystery) -> str:
    mapping = {
        "behind the brass lockers": "behind the brass lockers",
        "inside the hose-drying vent": "to the hose-drying vent",
        "up in the bell loft": "up to the bell loft",
    }
    return mapping.get(mystery.hidden_place, mystery.hidden_place)


def prompt_clause(mystery: Mystery) -> str:
    mapping = {
        "key": "the engine board keeps giving shy clicks with no real alarm",
        "lantern": "a smoky smell drifts through the hall even though the stove is cold",
        "swallow": "the old bell gives soft tug-tug sounds even though no call has come",
    }
    return mapping.get(mystery.id, mystery.opening_sign.lower())


def explain_rejection(station: FireStation, cat: MagicCat, mystery: Mystery) -> str:
    if mystery.needs not in station.supports:
        return (
            f"(No story: {station.name} does not have the right place for this mystery. "
            f"The clue needs {mystery.hidden_place}, but that station does not support "
            f"the {mystery.needs} channel.)"
        )
    if cat.clue_mode != mystery.needs:
        return (
            f"(No story: {cat.name}'s magic shows {cat.clue_mode}, but this mystery can "
            f"only be revealed through {mystery.needs}. The shiny cat must point to a "
            f"real matching clue.)"
        )
    return "(No story: that fire-station mystery is not physically reasoned.)"


def introduce(world: World, hero: Entity, station: FireStation, captain: Entity) -> None:
    world.say(
        f"One rainy evening, a {hero.traits[0]} little {hero.type} named {hero.id} "
        f"waited inside {station.name}."
    )
    world.say(
        f"{hero.id} sat near {station.hall} while Captain {captain.id} finished "
        f"quiet chores before bed."
    )
    world.say(
        f"The trucks were lined up in the dark like patient red giants, and "
        f"{station.night_sound}."
    )


def opening_mystery(world: World, hero: Entity, mystery: Mystery) -> None:
    hero.memes["question"] += 1
    world.say(mystery.opening_sign)
    world.say(
        f"{hero.id} looked up at once. Something in the station was not wrong enough "
        f"for a big alarm, but it was strange enough to make {hero.pronoun('possessive')} "
        f"heart listen harder."
    )


def cat_arrives(world: World, hero: Entity, cat_cfg: MagicCat) -> None:
    cat = world.add(Entity(
        id=cat_cfg.name, kind="character", type="cat", role="cat",
        traits=["shiny", cat_cfg.coat], attrs={"clue_mode": cat_cfg.clue_mode},
    ))
    cat.memes["guiding"] += 1
    world.say(cat_cfg.entrance)
    world.say(
        f"It was a shiny cat, and its {cat_cfg.coat} coat caught every small lamp in "
        f"the room."
    )
    world.say(
        f"{cat.id} looked straight at {hero.id}, then {cat_cfg.lead_action}."
    )


def first_inner_monologue(world: World, hero: Entity, cat_cfg: MagicCat) -> None:
    hero.memes["doubt"] += 1
    world.say(
        f'"Is this shiny cat only showing off, or is it trying to tell me something?" '
        f"{hero.pronoun()} thought."
    )
    world.say(
        f"{hero.id} did not run after it at once. {hero.pronoun('subject').capitalize()} "
        f"watched where the cat stopped and tried to make {hero.pronoun('possessive')} "
        f"question smaller and sharper."
    )


def follow_and_check(world: World, hero: Entity, station: FireStation,
                     cat_cfg: MagicCat, mystery: Mystery) -> None:
    clue = world.get("clue")
    hero.memes["caution"] += 1
    world.say(
        f"{hero.id} followed the cat {travel_phrase(mystery)}, but only close enough to see."
    )
    world.say(cat_cfg.magic_phrase)
    if cat_cfg.clue_mode == "reflection":
        world.say(
            f"In the brass shine, {hero.id} caught a second picture that the eye could "
            f"not see from the floor."
        )
    elif cat_cfg.clue_mode == "warm_vent":
        world.say(
            f"The air changed there. It was a little too warm for such a sleepy room."
        )
    else:
        world.say(
            f"The tiny ringing matched a second movement above, where the rope ought to "
            f"have been still."
        )
    propagate(world)
    if clue.meters["visible"] >= THRESHOLD:
        clue.attrs["station"] = station.name


def second_inner_monologue(world: World, hero: Entity, mystery: Mystery) -> None:
    if world.get("mystery").meters["revealed"] >= THRESHOLD:
        world.say(
            f'"This is not a pretend mystery," {hero.pronoun()} thought. "There is a real '
            f'reason for this, and I can help by getting the right grown-up."'
        )
    else:
        world.say(
            f'"I still do not understand it yet," {hero.pronoun()} thought, "but I know '
            f'I should not touch things just because I am curious."'
        )
    hero.memes["choose_check"] += 1
    world.say(
        f"{hero.id} backed up one careful step and called for Captain {world.role('captain').id}."
    )
    propagate(world)


def ending(world: World, hero: Entity, station: FireStation, captain: Entity,
           cat_cfg: MagicCat, mystery: Mystery) -> None:
    world.say(mystery.captain_action.format(captain=captain.id))
    world.say(mystery.fixed_image)
    if mystery.outcome == "warning":
        world.say(
            f"Captain {captain.id} knelt beside {hero.id} and said, "
            f"\"You noticed the small trouble before it became a big one.\""
        )
    elif mystery.outcome == "rescue":
        world.say(
            f"Captain {captain.id} smiled and said, "
            f"\"You listened carefully enough to help something smaller than you.\""
        )
    else:
        world.say(
            f"Captain {captain.id} tapped the peg board and said, "
            f"\"A quiet clue matters in a fire station. Good eyes kept our next call clear.\""
        )
    world.say(
        f"When the mystery was over, {cat_cfg.name} curled on a folded coat, and "
        f"{station.final_image}."
    )


def tell(station: FireStation, cat_cfg: MagicCat, mystery: Mystery,
         hero_name: str = "Mina", gender: str = "girl", trait: str = "thoughtful",
         captain_name: str = "Rosa") -> World:
    if not mystery_fits_station(station, mystery) or not cat_can_solve(cat_cfg, mystery):
        raise StoryError(explain_rejection(station, cat_cfg, mystery))

    world = World(station)
    world.add(Entity(
        id="station", kind="place", type="fire_station", role="station",
        label=station.name, attrs={"supports": sorted(station.supports)},
    ))
    hero = world.add(Entity(
        id=hero_name, kind="character", type=gender, role="hero",
        traits=[trait], attrs={"setting": station.name},
    ))
    captain_type = "captainess" if captain_name in {"Rosa", "June", "Marta"} else "captain"
    captain = world.add(Entity(
        id=captain_name, kind="character", type=captain_type, role="captain",
        traits=["steady"], attrs={"job": "captain"},
    ))
    world.add(Entity(
        id="clue", kind="thing", type="clue", label=cat_cfg.clue_mode,
        attrs={"mode": cat_cfg.clue_mode, "place": mystery.hidden_place},
        meters=defaultdict(float, {"available": 1.0}),
    ))
    world.add(Entity(
        id="mystery", kind="thing", type="mystery", role="mystery",
        label=mystery.id,
        attrs={"needs": mystery.needs, "place": mystery.hidden_place, "outcome": mystery.outcome},
    ))

    introduce(world, hero, station, captain)
    world.para()
    opening_mystery(world, hero, mystery)
    cat_arrives(world, hero, cat_cfg)
    first_inner_monologue(world, hero, cat_cfg)

    world.para()
    follow_and_check(world, hero, station, cat_cfg, mystery)
    second_inner_monologue(world, hero, mystery)

    world.para()
    ending(world, hero, station, captain, cat_cfg, mystery)

    world.facts.update(
        hero=hero,
        station=station,
        cat=cat_cfg,
        mystery_cfg=mystery,
        captain=captain,
        clue_mode=cat_cfg.clue_mode,
        revealed=world.get("mystery").meters["revealed"] >= THRESHOLD,
        resolved=world.get("mystery").meters["resolved"] >= THRESHOLD,
        outcome=mystery.outcome,
    )
    return world


STATIONS = {
    "maple": FireStation(
        "maple",
        "Maple Street Fire Station",
        "the brass locker wall",
        "rain tapped gently on the truck-bay windows",
        "the truck mirrors held one calm gold line",
        supports={"reflection", "warm_vent"},
        tags={"fire_station", "mystery", "safety", "rain"},
    ),
    "harbor": FireStation(
        "harbor",
        "Harbor Bell Fire Station",
        "the hose room under the old bell stairs",
        "the harbor foghorn sounded far away beyond the sleeping boats",
        "the bell rope hung still beside the warm red trucks",
        supports={"warm_vent", "bell_rope"},
        tags={"fire_station", "mystery", "water", "bell"},
    ),
    "hill": FireStation(
        "hill",
        "Pine Hill Fire Station",
        "the polished helmet shelf by the stair",
        "wind brushed the tower windows with soft tree sounds",
        "moonlight rested on the helmets and the station felt settled again",
        supports={"reflection", "bell_rope"},
        tags={"fire_station", "mystery", "tower", "night"},
    ),
}

CATS = {
    "mirror": MagicCat(
        "mirror",
        "Gleam",
        "silver",
        "reflection",
        "Out from beneath the radio table came a shiny cat with silver paws.",
        "padded toward the brass lockers and flicked its tail once",
        "A white stripe slid from the cat's whiskers across the brass and under the locker feet.",
        tags={"cat", "magic", "reflection", "mystery"},
    ),
    "ember": MagicCat(
        "ember",
        "Cinder",
        "black-and-copper",
        "warm_vent",
        "Then a shiny cat stepped out of the dark hose room, dark as soot except where copper light gleamed on its back.",
        "pressed its nose to the vent grate and listened",
        "Blue sparks glimmered at the tips of the cat's whiskers, and the grate shone where warm air hid behind it.",
        tags={"cat", "magic", "warm", "mystery"},
    ),
    "bell": MagicCat(
        "bell",
        "Tinsel",
        "golden",
        "bell_rope",
        "A shiny cat with a tiny collar appeared on the stair rail like a drop of warm lamp light.",
        "looked up toward the bell loft and made no sound at all",
        "The cat's little collar gave one clean ting exactly when the rope above twitched.",
        tags={"cat", "magic", "bell", "mystery"},
    ),
}

MYSTERIES = {
    "key": Mystery(
        "key",
        "From the engine board came one shy click, then another, though no call light was on.",
        "behind the brass lockers",
        "reflection",
        "the spare alarm key had slipped behind the lockers and nudged the board whenever the wall trembled",
        "the station might miss the shape of a real alarm if the board kept muttering nonsense",
        "Captain {captain} took a long hook from the tool peg, fished out the loose key, and hung it back on its red ring.",
        "At once the tiny clicking stopped. The board stood quiet, ready for the next true call.",
        "restore",
        "A mystery feels smaller when you find the real little cause.",
        tags={"mystery", "reflection", "fire_station", "gear"},
    ),
    "lantern": Mystery(
        "lantern",
        "A thin smoky smell drifted through the hall, even though the station stove was cold and clean.",
        "inside the hose-drying vent",
        "warm_vent",
        "a practice lantern had rolled into the vent and was warming the grate from inside",
        "the vent could have filled the room with smoke before anyone expected trouble",
        "Captain {captain} pulled on thick gloves, eased the practice lantern out of the vent, and set it to cool in a tub of water.",
        "Cool air slipped through the hose room again, and the smoky smell melted away.",
        "warning",
        "A small warning matters when people listen early.",
        tags={"mystery", "warm_vent", "fire_station", "safety", "smoke"},
    ),
    "swallow": Mystery(
        "swallow",
        "From high above came a soft tug-tug, as if the old alarm bell wanted to ring but could not decide.",
        "up in the bell loft",
        "bell_rope",
        "a tired swallow had tangled a ribbon around the bell rope and fluttered whenever it tried to get free",
        "the false tugging could have sent everyone running for a fire that was not there",
        "Captain {captain} climbed the loft steps, loosened the ribbon from the rope, and opened the little tower window for the bird.",
        "The swallow zipped into the evening sky, and the bell rope hung quiet at last.",
        "rescue",
        "Sometimes the answer to a mystery is a frightened creature, not a monster.",
        tags={"mystery", "bell_rope", "fire_station", "bird", "rescue"},
    ),
}

GIRL_NAMES = ["Mina", "Nora", "Lila", "Ava", "June", "Elsie"]
BOY_NAMES = ["Theo", "Ben", "Miles", "Owen", "Eli", "Finn"]
TRAITS = ["thoughtful", "careful", "watchful", "quiet", "curious"]
CAPTAINS = ["Rosa", "June", "Marta", "Luis", "Hector", "Sam"]

CURATED = [
    StoryParams("maple", "mirror", "key", "Mina", "girl", "thoughtful", "Rosa"),
    StoryParams("maple", "ember", "lantern", "Theo", "boy", "careful", "Luis"),
    StoryParams("harbor", "ember", "lantern", "Nora", "girl", "watchful", "Marta"),
    StoryParams("harbor", "bell", "swallow", "Ben", "boy", "quiet", "Hector"),
    StoryParams("hill", "mirror", "key", "Ava", "girl", "curious", "Sam"),
    StoryParams("hill", "bell", "swallow", "Miles", "boy", "thoughtful", "June"),
]


KNOWLEDGE = {
    "fire_station": [(
        "What does a fire station do?",
        "A fire station is a place where firefighters keep trucks, tools, and safety gear. It also has to stay orderly so the crew can move fast when a real call comes."
    )],
    "cat": [(
        "Why might a station keep a cat nearby?",
        "A cat can notice tiny sounds, small movements, and hidden corners. In a story, that makes a cat a good guide for a little mystery."
    )],
    "magic": [(
        "What is gentle magic in a story?",
        "Gentle magic is magic that helps reveal or heal instead of hurting. It often shows a clue in a way a child can notice."
    )],
    "mystery": [(
        "What makes something a mystery?",
        "A mystery begins when something strange happens and nobody knows why yet. It becomes satisfying when the clue and the answer truly match."
    )],
    "safety": [(
        "Why should a child call a grown-up in a station problem?",
        "A child can notice a clue, but a grown-up should handle tools, height, or heat. That keeps the helpful choice safe as well as brave."
    )],
    "reflection": [(
        "How can a reflection help you notice something?",
        "A reflection can show a place your eyes cannot see directly. Shiny metal can turn hidden space into a clue."
    )],
    "warm_vent": [(
        "Why does a warm vent matter in a fire station?",
        "A vent should feel normal for the room it serves. If it feels strangely warm or smells smoky, that can warn people to check for a hidden problem."
    )],
    "bell_rope": [(
        "Why must a station bell stay accurate?",
        "People trust a station bell to mean something real. If it rings by mistake, helpers may rush for the wrong reason."
    )],
    "bird": [(
        "Why might a trapped bird cause trouble indoors?",
        "A trapped bird can flap, pull strings, or hide in small places. The kind fix is to free it before it gets more frightened."
    )],
    "gear": [(
        "Why should tools and keys be put back carefully?",
        "A missing tool can waste precious time when people need to act fast. Order is part of safety in a working station."
    )],
}
KNOWLEDGE_ORDER = [
    "fire_station", "cat", "magic", "mystery", "safety",
    "reflection", "warm_vent", "bell_rope", "bird", "gear",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    station = f["station"]
    cat = f["cat"]
    mystery = f["mystery_cfg"]
    return [
        f'Write a TinyStories-style mystery set in a fire station that includes a shiny cat named {cat.name} and a {hero.type} named {hero.id}.',
        f"Tell a child-facing mystery where {hero.id} has an inner monologue, follows magical clues at {station.name}, and solves why {prompt_clause(mystery)}.",
        f"Write a gentle magical story in which a shiny cat reveals a hidden problem at a fire station, and the child solves it by calling Captain {f['captain'].id}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    station = f["station"]
    cat = f["cat"]
    mystery = f["mystery_cfg"]
    captain = f["captain"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a {hero.traits[0]} little {hero.type} at {station.name}. {hero.pronoun('subject').capitalize()} notices a strange problem before bedtime chores are done."
        ),
        (
            "What made the station feel mysterious at the start?",
            f"The mystery began because {mystery.opening_sign.lower()} That odd little sign told {hero.id} that something hidden in the station needed attention."
        ),
        (
            "What did the shiny cat do?",
            f"The shiny cat named {cat.name} led {hero.id} {travel_phrase(mystery)}. Its magic made the right clue visible instead of leaving the child with only a guess."
        ),
        (
            f"What did {hero.id} think to {hero.reflexive()}?",
            f"{hero.id} wondered whether the shiny cat was only playing or truly trying to help. That inner question mattered because it slowed the child down enough to check the clue carefully."
        ),
        (
            "How was the mystery really solved?",
            f"{hero.id} did not grab at the problem alone. {hero.pronoun('subject').capitalize()} called Captain {captain.id}, and the captain handled the real fix once the clue had been revealed."
        ),
    ]
    if mystery.outcome == "warning":
        qa.append((
            "Why was the clue important?",
            f"The clue led to a practice lantern hidden in the vent. Finding it early kept the station safe before smoke could spread."
        ))
    elif mystery.outcome == "rescue":
        qa.append((
            "What was hidden in the bell loft?",
            f"A tired swallow was tangled near the bell rope. Freeing it stopped the false tugging and turned the mystery into a rescue."
        ))
    else:
        qa.append((
            "What was making the engine board click?",
            f"The spare alarm key had slipped behind the brass lockers. It kept nudging the board until Captain {captain.id} hooked it back into place."
        ))
    qa.append((
        "How did the story end?",
        f"The station grew calm again after the real little problem was fixed. {cat.name} curled up to rest, which showed that the magic work was done."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["station"].tags) | set(f["cat"].tags) | set(f["mystery_cfg"].tags)
    tags.add("magic")
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
        attrs = {k: v for k, v in ent.attrs.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if attrs:
            bits.append(f"attrs={attrs}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, C, M) :- station(S), cat(C), mystery(M),
                  supports(S, R), clue_mode(C, R), needs(M, R).

outcome(O) :- chosen_mystery(M), mystery_outcome(M, O).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for station_id, station in STATIONS.items():
        lines.append(asp.fact("station", station_id))
        for support in sorted(station.supports):
            lines.append(asp.fact("supports", station_id, support))
    for cat_id, cat in CATS.items():
        lines.append(asp.fact("cat", cat_id))
        lines.append(asp.fact("clue_mode", cat_id, cat.clue_mode))
    for mystery_id, mystery in MYSTERIES.items():
        lines.append(asp.fact("mystery", mystery_id))
        lines.append(asp.fact("needs", mystery_id, mystery.needs))
        lines.append(asp.fact("mystery_outcome", mystery_id, mystery.outcome))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    model = asp.one_model(
        asp_program(asp.fact("chosen_mystery", params.mystery), "#show outcome/1.")
    )
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    parser = build_parser()
    cases = list(CURATED)
    for seed in range(150):
        try:
            cases.append(resolve_params(parser.parse_args([]), random.Random(seed)))
        except StoryError:
            continue
    bad = [params for params in cases if asp_outcome(params) != outcome_of(params)]
    if not bad:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(bad)}/{len(cases)} outcomes differ.")

    exercised = 0
    for params in cases:
        sample = generate(params)
        if not sample.story.strip():
            rc = 1
            print("MISMATCH: generated an empty story.")
            break
        if "shiny cat" not in sample.story.lower():
            rc = 1
            print(f"MISMATCH: story for seed {params.seed} lost the required words.")
            break
        if len(sample.story_qa) < 5 or len(sample.world_qa) < 3:
            rc = 1
            print("MISMATCH: QA output is too thin.")
            break
        exercised += 1
    if rc == 0:
        print(f"OK: exercised {exercised} generated stories with grounded QA.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a shiny cat, a fire station mystery, inner monologue, and gentle magic."
    )
    ap.add_argument("--station", choices=STATIONS)
    ap.add_argument("--cat", choices=CATS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--captain", choices=CAPTAINS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include generation prompts and QA")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (station, cat, mystery) sets")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and exercise generated stories")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.station and args.cat and args.mystery:
        station = STATIONS[args.station]
        cat = CATS[args.cat]
        mystery = MYSTERIES[args.mystery]
        if not valid_story(args.station, args.cat, args.mystery):
            raise StoryError(explain_rejection(station, cat, mystery))

    combos = [
        combo for combo in valid_combos()
        if (args.station is None or combo[0] == args.station)
        and (args.cat is None or combo[1] == args.cat)
        and (args.mystery is None or combo[2] == args.mystery)
    ]
    if not combos:
        raise StoryError("(No valid shiny-cat fire-station mystery matches the given options.)")

    station_id, cat_id, mystery_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = rng.choice(TRAITS)
    captain = args.captain or rng.choice(CAPTAINS)
    return StoryParams(station_id, cat_id, mystery_id, name, gender, trait, captain)


def generate(params: StoryParams) -> StorySample:
    if not valid_story(params.station, params.cat, params.mystery):
        raise StoryError(explain_rejection(
            STATIONS[params.station], CATS[params.cat], MYSTERIES[params.mystery]
        ))
    world = tell(
        STATIONS[params.station],
        CATS[params.cat],
        MYSTERIES[params.mystery],
        params.hero,
        params.gender,
        params.trait,
        params.captain,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
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
        print(f"{len(combos)} compatible (station, cat, mystery) combos:\n")
        for station_id, cat_id, mystery_id in combos:
            print(f"  {station_id:7} {cat_id:7} {mystery_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.hero}: {p.station} / {p.cat} / {p.mystery} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
