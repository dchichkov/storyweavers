#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/founding_sound_effects_quest_mystery.py

A small storyworld about a child on a Founding Day mystery quest. A treasured
ceremony object has gone missing inside an old public building, and a strange
sound points the way toward where it was hidden. The child follows the sound,
tests a clue, and either finds the object alone or asks a calm grown-up to open
the last hiding place.

Run it
------
python storyworlds/worlds/gpt-5.4/founding_sound_effects_quest_mystery.py
python storyworlds/worlds/gpt-5.4/founding_sound_effects_quest_mystery.py --setting museum --sounder clock --spot cabinet
python storyworlds/worlds/gpt-5.4/founding_sound_effects_quest_mystery.py --spot tower_crate
python storyworlds/worlds/gpt-5.4/founding_sound_effects_quest_mystery.py --all
python storyworlds/worlds/gpt-5.4/founding_sound_effects_quest_mystery.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/founding_sound_effects_quest_mystery.py --verify
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
        female = {"girl", "mother", "woman", "librarian"}
        male = {"boy", "father", "man", "caretaker"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def title_word(self) -> str:
        return {
            "caretaker": "caretaker",
            "librarian": "librarian",
            "mother": "mom",
            "father": "dad",
        }.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    label: str
    intro: str
    tradition: str
    zones: set[str] = field(default_factory=set)
    sounders: set[str] = field(default_factory=set)


@dataclass
class Treasure:
    id: str
    label: str
    phrase: str
    use: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Sounder:
    id: str
    zone: str
    effect: str
    cause: str
    lead: str
    reveals: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class HideSpot:
    id: str
    zone: str
    label: str
    phrase: str
    locked: bool = False
    open_text: str = ""
    found_text: str = ""
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.trace: list[str] = []
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

    def note(self, fact: str) -> None:
        self.trace.append(fact)

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.trace = list(self.trace)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_sound_stirs(world: World) -> list[str]:
    hero = world.get("hero")
    if hero.meters["heard_sound"] < THRESHOLD:
        return []
    sig = ("sound_stirs",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["curiosity"] += 1
    hero.memes["worry"] += 1
    world.note("The strange sound made the hero curious and a little worried.")
    return []


def _r_match_clue(world: World) -> list[str]:
    hero = world.get("hero")
    if hero.meters["checked_clue"] < THRESHOLD:
        return []
    if not world.facts.get("clue_matches"):
        return []
    sig = ("match",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.meters["sure"] += 1
    hero.memes["hope"] += 1
    world.note("The clue matched the sound, so the hero knew the trail was right.")
    return []


def _r_found_relief(world: World) -> list[str]:
    hero = world.get("hero")
    if hero.meters["found"] < THRESHOLD:
        return []
    sig = ("found_relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["relief"] += 1
    hero.memes["joy"] += 1
    hero.memes["worry"] = 0.0
    world.note("Finding the missing object turned the mystery into relief.")
    return []


CAUSAL_RULES = [
    Rule(name="sound_stirs", tag="emotion", apply=_r_sound_stirs),
    Rule(name="match_clue", tag="reasoning", apply=_r_match_clue),
    Rule(name="found_relief", tag="emotion", apply=_r_found_relief),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                produced.extend(out)
                changed = True
            elif any(sig[0] == rule.name for sig in world.fired):
                # a rule can change the world without returning narration
                pass
        new_changed = False
        for rule in CAUSAL_RULES:
            before = len(world.fired)
            rule.apply(world)
            if len(world.fired) != before:
                new_changed = True
        changed = changed or new_changed
    if narrate:
        for text in produced:
            world.say(text)
    return produced


SETTINGS = {
    "museum": Setting(
        id="museum",
        label="the little town museum",
        intro="The museum was full of glass cases, old maps, and polished floorboards.",
        tradition="every Founding Day the missing treasure was meant to be shown before the lantern walk",
        zones={"foyer", "archive", "tower"},
        sounders={"clock", "vent", "pigeon"},
    ),
    "library": Setting(
        id="library",
        label="the old brick library",
        intro="The library smelled like paper and raincoats, and every shelf seemed to keep a secret.",
        tradition="every Founding Day the missing treasure was meant to be shown beside the story rug",
        zones={"foyer", "archive"},
        sounders={"vent", "cart", "clock"},
    ),
    "town_hall": Setting(
        id="town_hall",
        label="the creaky town hall",
        intro="Town hall had a wooden stage, a long corridor, and corners that liked to echo.",
        tradition="every Founding Day the missing treasure was meant to be shown before the mayor spoke",
        zones={"foyer", "stage", "archive"},
        sounders={"cart", "clock", "vent"},
    ),
    "schoolhouse": Setting(
        id="schoolhouse",
        label="the one-room schoolhouse",
        intro="The schoolhouse had hooks for coats, tall windows, and a stair that sighed when anyone climbed it.",
        tradition="every Founding Day the missing treasure was meant to be shown before the children sang",
        zones={"foyer", "stage", "archive"},
        sounders={"vent", "cart"},
    ),
}

TREASURES = {
    "key": Treasure(
        id="key",
        label="founding key",
        phrase="the brass founding key",
        use="unlock the tiny parade chest for the evening ceremony",
        tags={"key", "founding"},
    ),
    "bell": Treasure(
        id="bell",
        label="founding bell",
        phrase="the silver founding bell",
        use="ring the first clear note of the celebration",
        tags={"bell", "founding"},
    ),
    "charter": Treasure(
        id="charter",
        label="founding scroll",
        phrase="the rolled founding scroll",
        use="be unrolled while everyone listened to the oldest town promise",
        tags={"scroll", "founding"},
    ),
}

SOUNDERS = {
    "clock": Sounder(
        id="clock",
        zone="foyer",
        effect='Tick-tock... clink.',
        cause="an old hall clock had a loose brass pendulum piece",
        lead="The tiny metal clink sounded as if it belonged near something brass.",
        reveals={"bench", "cabinet"},
        tags={"clock", "sound"},
    ),
    "vent": Sounder(
        id="vent",
        zone="archive",
        effect='Whoooo... flap.',
        cause="a draft whispered through a floor vent and worried a forgotten paper edge",
        lead="The fluttering sound hinted that paper or ribbon was tucked nearby.",
        reveals={"map_drawer", "bench"},
        tags={"wind", "sound"},
    ),
    "cart": Sounder(
        id="cart",
        zone="stage",
        effect='Rattle-rattle.',
        cause="a supply cart had one wobbly wheel and shook whenever the floorboards trembled",
        lead="The rattling seemed to point toward the stage curtains and the props behind them.",
        reveals={"curtain_chest"},
        tags={"cart", "sound"},
    ),
    "pigeon": Sounder(
        id="pigeon",
        zone="tower",
        effect='Flutter-flutter... coo.',
        cause="a pigeon had slipped into the bell tower and rustled around the rafters",
        lead="The wingbeats made the tower feel worth searching, though the last hiding place sat high up.",
        reveals={"tower_crate"},
        tags={"bird", "sound"},
    ),
}

HIDESPOTS = {
    "bench": HideSpot(
        id="bench",
        zone="foyer",
        label="bench cubby",
        phrase="a bench with a deep cubby under the seat",
        locked=False,
        open_text="knelt and felt under the seat",
        found_text="Inside the dark cubby, careful fingers touched the missing object at last.",
        tags={"bench"},
    ),
    "cabinet": HideSpot(
        id="cabinet",
        zone="foyer",
        label="glass cabinet",
        phrase="a narrow glass cabinet by the front wall",
        locked=True,
        open_text="used the cabinet key and swung the small door open",
        found_text="On the bottom shelf, behind a stack of old programs, the missing object was waiting.",
        tags={"cabinet"},
    ),
    "map_drawer": HideSpot(
        id="map_drawer",
        zone="archive",
        label="map drawer",
        phrase="a flat archive drawer full of curled maps",
        locked=False,
        open_text="slid the drawer open with both hands",
        found_text="Under one rolled map lay the missing object, hidden but safe.",
        tags={"drawer"},
    ),
    "curtain_chest": HideSpot(
        id="curtain_chest",
        zone="stage",
        label="stage chest",
        phrase="a paint-splashed chest behind the curtain",
        locked=False,
        open_text="lifted the creaky lid",
        found_text="Between folded costumes sat the missing object, glimmering in a stripe of light.",
        tags={"stage"},
    ),
    "tower_crate": HideSpot(
        id="tower_crate",
        zone="tower",
        label="tower crate",
        phrase="a wooden crate beneath the bell rope",
        locked=True,
        open_text="worked the crate latch loose and opened it carefully",
        found_text="Wrapped in an old scarf inside the crate was the missing object.",
        tags={"tower"},
    ),
}


def valid_combo(setting_id: str, sounder_id: str, spot_id: str) -> bool:
    setting = SETTINGS[setting_id]
    sounder = SOUNDERS[sounder_id]
    spot = HIDESPOTS[spot_id]
    if sounder_id not in setting.sounders:
        return False
    if sounder.zone not in setting.zones or spot.zone not in setting.zones:
        return False
    if sounder.zone != spot.zone and spot_id not in sounder.reveals:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for setting_id in SETTINGS:
        for sounder_id in SOUNDERS:
            for spot_id in HIDESPOTS:
                if valid_combo(setting_id, sounder_id, spot_id):
                    out.append((setting_id, sounder_id, spot_id))
    return sorted(out)


def outcome_of(params: "StoryParams") -> str:
    return "helped" if HIDESPOTS[params.spot].locked else "direct"


def predict_clue(setting: Setting, sounder: Sounder, spot: HideSpot) -> dict:
    return {
        "same_zone": sounder.zone == spot.zone,
        "matched": sounder.zone == spot.zone or spot.id in sounder.reveals,
        "needs_help": spot.locked,
    }


def introduce(world: World, hero: Entity, helper: Entity, treasure: Treasure) -> None:
    world.say(
        f"{hero.id} arrived at {world.setting.label} on Founding Day with {hero.pronoun('possessive')} "
        f"{helper.title_word}. {world.setting.intro}"
    )
    world.say(
        f"But a hush had fallen over the place, because {treasure.phrase} was missing, and "
        f"{world.setting.tradition}."
    )
    world.say(
        f'"Then we have a quest," {hero.id} whispered, standing a little taller. '
        f'"We have to find it before the crowd comes."'
    )
    world.note("The story begins with a missing ceremony object and a quest.")


def hear_sound(world: World, hero: Entity, sounder: Sounder) -> None:
    hero.meters["heard_sound"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Just then, from the {sounder.zone}, came a strange sound: {sounder.effect} "
        f"{sounder.cause.capitalize()}."
    )
    world.say(
        f"{hero.id} stopped walking. {sounder.lead}"
    )
    world.note(f"The hero heard {sounder.effect} in the {sounder.zone}.")


def begin_search(world: World, hero: Entity, helper: Entity, sounder: Sounder, spot: HideSpot) -> None:
    world.say(
        f'"Listen," said {hero.id}. "{sounder.effect}"'
    )
    world.say(
        f"{helper.title_word.capitalize()} nodded, and together they followed the sound toward {spot.phrase}."
    )
    hero.meters["checked_clue"] += 1
    world.facts["clue_matches"] = predict_clue(world.setting, sounder, spot)["matched"]
    propagate(world, narrate=False)
    if world.facts["clue_matches"]:
        world.say(
            f"The closer they came, the more the little mystery pieces seemed to fit together."
        )
    world.note(f"The search moved toward the {spot.label}.")


def inspect_spot(world: World, hero: Entity, treasure: Treasure, spot: HideSpot) -> None:
    world.say(
        f"{hero.id} {spot.open_text}. {spot.found_text.replace('the missing object', treasure.phrase)}"
    )
    hero.meters["found"] += 1
    propagate(world, narrate=False)
    world.note(f"The hero found the treasure in the {spot.label}.")


def ask_for_help(world: World, hero: Entity, helper: Entity, treasure: Treasure, spot: HideSpot) -> None:
    hero.memes["trust"] += 1
    helper.memes["care"] += 1
    world.say(
        f"But the last clue ended at {spot.phrase}, and its little latch would not budge for small hands."
    )
    world.say(
        f'"I know where it is," {hero.id} said, "but I need help for the last part."'
    )
    world.say(
        f"{helper.title_word.capitalize()} smiled, proud that {hero.pronoun()} had solved the mystery so far, and "
        f"{helper.pronoun()} {spot.open_text}. {spot.found_text.replace('the missing object', treasure.phrase)}"
    )
    hero.meters["found"] += 1
    propagate(world, narrate=False)
    world.note(f"The helper opened the locked {spot.label}, and the treasure was found.")


def ending(world: World, hero: Entity, helper: Entity, treasure: Treasure) -> None:
    world.say(
        f"For one second nobody spoke. Then {hero.id} held up {treasure.phrase}, and all the worry in the room seemed to melt."
    )
    world.say(
        f'"You listened carefully," said {helper.title_word}. "That is how you solved it."'
    )
    world.say(
        f"Soon the hall was bright again. When the evening ceremony began, {treasure.phrase} was back where it belonged, "
        f"and {hero.id} still remembered the mystery sound that had started the whole quest."
    )
    world.note("The ending image proves that the missing treasure returned to the ceremony.")


def tell(
    setting: Setting,
    treasure: Treasure,
    sounder: Sounder,
    spot: HideSpot,
    hero_name: str = "Mina",
    hero_type: str = "girl",
    helper_type: str = "caretaker",
) -> World:
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name, role="hero"))
    helper = world.add(Entity(id="helper", kind="character", type=helper_type, label="the helper", role="helper"))
    item = world.add(Entity(id="treasure", type="treasure", label=treasure.label, phrase=treasure.phrase, tags=set(treasure.tags)))
    source = world.add(Entity(id="sounder", type="sounder", label=sounder.id, attrs={"zone": sounder.zone}, tags=set(sounder.tags)))
    place = world.add(Entity(id="spot", type="spot", label=spot.label, attrs={"zone": spot.zone, "locked": spot.locked}, tags=set(spot.tags)))

    world.facts.update(
        setting=setting,
        treasure=treasure,
        sounder=sounder,
        spot_cfg=spot,
        hero=hero,
        helper=helper,
        item=item,
        source=source,
        place=place,
        clue_matches=predict_clue(setting, sounder, spot)["matched"],
        outcome=outcome_of(StoryParams(
            setting=setting.id,
            treasure=treasure.id,
            sounder=sounder.id,
            spot=spot.id,
            hero_name=hero_name,
            hero_type=hero_type,
            helper_type=helper_type,
        )),
    )

    introduce(world, hero, helper, treasure)
    world.para()
    hear_sound(world, hero, sounder)
    begin_search(world, hero, helper, sounder, spot)
    world.para()
    if spot.locked:
        ask_for_help(world, hero, helper, treasure, spot)
    else:
        inspect_spot(world, hero, treasure, spot)
    world.para()
    ending(world, hero, helper, treasure)
    return world


@dataclass
class StoryParams:
    setting: str
    treasure: str
    sounder: str
    spot: str
    hero_name: str
    hero_type: str
    helper_type: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "founding": [
        (
            "What does founding mean in a town celebration?",
            "Founding means the beginning of something. A Founding Day celebration remembers when a town first started."
        )
    ],
    "mystery": [
        (
            "What is a mystery?",
            "A mystery is a puzzle with missing pieces that someone has to figure out. People solve mysteries by noticing clues."
        )
    ],
    "quest": [
        (
            "What is a quest?",
            "A quest is an important search for something. It usually has a goal, clues, and a reason the search matters."
        )
    ],
    "clock": [
        (
            "Why might an old clock make a clinking sound?",
            "Old clocks have moving parts, and if one piece gets loose it can tap or clink as it swings."
        )
    ],
    "wind": [
        (
            "Why can a vent make a fluttering sound?",
            "Air moving through a vent can push paper or cloth so it flaps and whispers."
        )
    ],
    "cart": [
        (
            "Why does a cart rattle?",
            "A cart can rattle when one wheel is loose or when it rolls over bumpy floorboards."
        )
    ],
    "bird": [
        (
            "Why do birds make fluttering sounds inside a building?",
            "Bird wings push air when they flap. In a building, that sound can echo and seem extra mysterious."
        )
    ],
    "key": [
        (
            "What is a ceremonial key for?",
            "A ceremonial key is a special key kept for an important event or symbol. It usually stands for welcome, trust, or history."
        )
    ],
    "bell": [
        (
            "Why use a bell in a ceremony?",
            "A bell can call people to listen. Its clear sound helps mark the beginning of something important."
        )
    ],
    "scroll": [
        (
            "What is a scroll?",
            "A scroll is a piece of paper or parchment rolled up instead of folded into a book."
        )
    ],
}

KNOWLEDGE_ORDER = [
    "founding",
    "mystery",
    "quest",
    "clock",
    "wind",
    "cart",
    "bird",
    "key",
    "bell",
    "scroll",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    treasure = f["treasure"]
    setting = f["setting"]
    sounder = f["sounder"]
    return [
        f'Write a short mystery story for a 3-to-5-year-old about Founding Day that includes the word "founding".',
        f"Tell a gentle quest story where a {hero.type} named {hero.label} follows the sound {sounder.effect} through {setting.label} to find {treasure.phrase}.",
        f"Write a child-facing mystery with sound effects, a missing ceremony object, and a happy ending where careful listening solves the problem.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    treasure = f["treasure"]
    sounder = f["sounder"]
    spot = f["spot_cfg"]
    setting = f["setting"]
    outcome = f["outcome"]
    qas = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, a child at {setting.label}, and a calm {helper.title_word} who helps with the Founding Day search."
        ),
        (
            f"Why did {hero.label} start a quest?",
            f"{treasure.phrase.capitalize()} had gone missing before the Founding Day ceremony. That made the search feel important instead of just playful."
        ),
        (
            f"What clue started the mystery?",
            f"The first clue was the strange sound {sounder.effect}. {hero.label} listened closely and guessed the sound meant something nearby had been bumped, hidden, or left loose."
        ),
    ]
    if outcome == "direct":
        qas.append(
            (
                f"How did {hero.label} find {treasure.phrase}?",
                f"{hero.label} followed the sound to {spot.phrase} and checked it carefully. The clue matched the place, so {hero.pronoun()} found {treasure.phrase} there without needing anyone to open it."
            )
        )
    else:
        qas.append(
            (
                f"Did {hero.label} solve the mystery alone?",
                f"{hero.label} solved most of it by following the sound and choosing the right hiding place. But the final spot was locked, so {hero.pronoun()} asked the {helper.title_word} for help opening it."
            )
        )
    qas.append(
        (
            "How did the story end?",
            f"It ended with {treasure.phrase} back in time for the ceremony. The last image shows the town ready again because the mystery had been solved."
        )
    )
    return qas


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"founding", "mystery", "quest"}
    sound_tag = next(iter(f["sounder"].tags - {"sound"}), "")
    if sound_tag:
        tags.add(sound_tag)
    tags |= set(f["treasure"].tags)
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append("  trace:")
    for note in world.trace:
        lines.append(f"    - {note}")
    lines.append(f"  fired rules: {sorted(set(sig[0] for sig in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="museum",
        treasure="key",
        sounder="clock",
        spot="cabinet",
        hero_name="Mina",
        hero_type="girl",
        helper_type="caretaker",
    ),
    StoryParams(
        setting="library",
        treasure="charter",
        sounder="vent",
        spot="map_drawer",
        hero_name="Owen",
        hero_type="boy",
        helper_type="librarian",
    ),
    StoryParams(
        setting="town_hall",
        treasure="bell",
        sounder="cart",
        spot="curtain_chest",
        hero_name="June",
        hero_type="girl",
        helper_type="caretaker",
    ),
    StoryParams(
        setting="museum",
        treasure="bell",
        sounder="pigeon",
        spot="tower_crate",
        hero_name="Eli",
        hero_type="boy",
        helper_type="caretaker",
    ),
]


def explain_rejection(setting_id: str, sounder_id: str, spot_id: str) -> str:
    setting = SETTINGS[setting_id]
    sounder = SOUNDERS[sounder_id]
    spot = HIDESPOTS[spot_id]
    if sounder_id not in setting.sounders:
        return f"(No story: {setting.label} does not plausibly contain the clue sound '{sounder_id}'.)"
    if sounder.zone not in setting.zones or spot.zone not in setting.zones:
        return f"(No story: {setting.label} does not contain the needed search area for that mystery path.)"
    return (
        f"(No story: the sound from the {sounder.zone} does not reasonably point to {spot.phrase}. "
        f"Choose a hiding place in the same zone or one this sound can honestly reveal.)"
    )


ASP_RULES = r"""
valid(Setting, Sounder, Spot) :-
    setting(Setting), sounder(Sounder), spot(Spot),
    setting_has_sound(Setting, Sounder),
    sound_zone(Sounder, Zs), setting_zone(Setting, Zs),
    spot_zone(Spot, Zp), setting_zone(Setting, Zp),
    (Zs = Zp; reveals(Sounder, Spot)).

locked_spot(Spot) :- spot_locked(Spot).
outcome(helped) :- chosen_spot(S), locked_spot(S).
outcome(direct) :- chosen_spot(S), not locked_spot(S).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for zone in sorted(setting.zones):
            lines.append(asp.fact("setting_zone", sid, zone))
        for sound in sorted(setting.sounders):
            lines.append(asp.fact("setting_has_sound", sid, sound))
    for sound_id, sound in SOUNDERS.items():
        lines.append(asp.fact("sounder", sound_id))
        lines.append(asp.fact("sound_zone", sound_id, sound.zone))
        for spot in sorted(sound.reveals):
            lines.append(asp.fact("reveals", sound_id, spot))
    for spot_id, spot in HIDESPOTS.items():
        lines.append(asp.fact("spot", spot_id))
        lines.append(asp.fact("spot_zone", spot_id, spot.zone))
        if spot.locked:
            lines.append(asp.fact("spot_locked", spot_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = asp.fact("chosen_spot", params.spot)
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))

    scenarios = list(CURATED)
    for params in scenarios:
        if asp_outcome(params) != outcome_of(params):
            rc = 1
            print("MISMATCH in outcome:", params, asp_outcome(params), outcome_of(params))

    try:
        sample = generate(CURATED[0])
        if not sample.story or "Founding Day" not in sample.story:
            raise StoryError("smoke test story missing expected content")
        emit(sample, trace=False, qa=False)
        print("OK: smoke test generation succeeded.")
    except Exception as err:  # pragma: no cover - defensive CLI path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    if rc == 0:
        print(f"OK: outcome model matches on {len(scenarios)} curated scenarios.")
    return rc


GIRL_NAMES = ["Mina", "June", "Nora", "Lila", "Tess", "Ruby"]
BOY_NAMES = ["Owen", "Eli", "Noah", "Finn", "Milo", "Jude"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A small Founding Day mystery quest storyworld with sound clues."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--sounder", choices=SOUNDERS)
    ap.add_argument("--spot", choices=HIDESPOTS)
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper-type", choices=["caretaker", "librarian", "mother", "father"])
    ap.add_argument("--hero-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible mystery combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP model and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.sounder and args.spot and not valid_combo(args.setting, args.sounder, args.spot):
        raise StoryError(explain_rejection(args.setting, args.sounder, args.spot))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.sounder is None or combo[1] == args.sounder)
        and (args.spot is None or combo[2] == args.spot)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, sounder_id, spot_id = rng.choice(combos)
    treasure_id = args.treasure or rng.choice(sorted(TREASURES))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or rng.choice(["caretaker", "librarian", "mother", "father"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    return StoryParams(
        setting=setting_id,
        treasure=treasure_id,
        sounder=sounder_id,
        spot=spot_id,
        hero_name=hero_name,
        hero_type=hero_type,
        helper_type=helper_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.treasure not in TREASURES:
        raise StoryError(f"(Unknown treasure: {params.treasure})")
    if params.sounder not in SOUNDERS:
        raise StoryError(f"(Unknown sounder: {params.sounder})")
    if params.spot not in HIDESPOTS:
        raise StoryError(f"(Unknown spot: {params.spot})")
    if not valid_combo(params.setting, params.sounder, params.spot):
        raise StoryError(explain_rejection(params.setting, params.sounder, params.spot))

    world = tell(
        setting=SETTINGS[params.setting],
        treasure=TREASURES[params.treasure],
        sounder=SOUNDERS[params.sounder],
        spot=HIDESPOTS[params.spot],
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        helper_type=params.helper_type,
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
        print(f"{len(combos)} compatible (setting, sounder, spot) combos:\n")
        for setting_id, sounder_id, spot_id in combos:
            print(f"  {setting_id:11} {sounder_id:8} {spot_id}")
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
            header = f"### {p.hero_name}: {p.setting}, {p.sounder} -> {p.spot} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
