#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/maid_curiosity_myth.py
=================================================

A standalone storyworld about a curious little maid in a mythic household.

This world models a small family-friendly myth pattern:

    a young maid is trusted near a sacred vessel,
    curiosity pulls at her,
    she either asks first or opens it alone,
    a hidden wonder escapes into the hall,
    and a wise keeper restores what can be restored.

The domain is intentionally narrow. A story is only valid when:

* the chosen realm actually keeps the chosen vessel;
* the chosen remedy truly fits what escaped from that vessel; and
* the remedy is sensible enough for the world to tell.

The world state drives the prose: vessels open, brightness dims, petals scatter,
fear rises, help arrives, and the ending image shows whether curiosity learned to
ask first or had to learn after harm.

Run it
------
    python storyworlds/worlds/gpt-5.4/maid_curiosity_myth.py
    python storyworlds/worlds/gpt-5.4/maid_curiosity_myth.py --realm dawn_hall
    python storyworlds/worlds/gpt-5.4/maid_curiosity_myth.py --vessel moon_lantern
    python storyworlds/worlds/gpt-5.4/maid_curiosity_myth.py --mentor near --trait patient
    python storyworlds/worlds/gpt-5.4/maid_curiosity_myth.py --all
    python storyworlds/worlds/gpt-5.4/maid_curiosity_myth.py --qa --json
    python storyworlds/worlds/gpt-5.4/maid_curiosity_myth.py --verify
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import io
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

# Make the shared result containers importable when this script is run directly.
# This file lives under storyworlds/worlds/gpt-5.4/, so we add storyworlds/ to
# the path.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
CURIOSITY_INIT = 5.0
PATIENT_TRAITS = {"patient", "careful"}


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
        female = {"girl", "woman", "mother", "priestess", "keeper_woman"}
        male = {"boy", "man", "father", "priest", "keeper_man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def title_word(self) -> str:
        return self.attrs.get("title_word", self.label or self.type)


@dataclass
class Realm:
    id: str
    label: str
    place_line: str
    wonder_line: str
    loss_line: str
    safe_line: str
    vessels: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Vessel:
    id: str
    label: str
    phrase: str
    essence: str
    contents: str
    opening_line: str
    escape_line: str
    spread: int
    warning: str
    lesson: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Remedy:
    id: str
    label: str
    handles: str
    sense: int
    power: int
    use_line: str
    fail_line: str
    qa_line: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, realm: Realm) -> None:
        self.realm = realm
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
        clone = World(self.realm)
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


def _r_escape_changes_hall(world: World) -> list[str]:
    hall = world.entities.get("hall")
    maid = world.entities.get("maid")
    if hall is None or maid is None:
        return []
    if hall.meters["escaped"] < THRESHOLD:
        return []
    sig = ("change_hall",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hall.meters["dim"] += 1
    hall.meters["disorder"] += 1
    maid.memes["fear"] += 1
    maid.memes["guilt"] += 1
    return ["__changed__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="escape_changes_hall", tag="physical", apply=_r_escape_changes_hall),
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


REALMS = {
    "dawn_hall": Realm(
        id="dawn_hall",
        label="the Hall of Dawn",
        place_line="Its eastern windows drank the first gold of morning.",
        wonder_line="Every pillar looked as if sunrise had once leaned there and left a little light behind.",
        loss_line="The gold drained from the windows, and the hall looked like morning had forgotten its own name.",
        safe_line="By evening the windows shone warm again, and even the high pillars looked awake.",
        vessels={"sun_jar", "dew_bowl"},
        tags={"dawn"},
    ),
    "moon_tower": Realm(
        id="moon_tower",
        label="the Moon Tower",
        place_line="Round windows poured pale light onto the floor like milk.",
        wonder_line="At night, the steps seemed to climb straight into the silver part of the sky.",
        loss_line="The silver on the floor thinned and trembled, and the tower felt hushed in a worried way.",
        safe_line="Soon moonlight pooled softly over the steps again.",
        vessels={"moon_lantern", "dream_basket"},
        tags={"moon"},
    ),
    "sea_court": Realm(
        id="sea_court",
        label="the Court of the Sea Gate",
        place_line="Blue tiles held the shine of water even when the tide was far away.",
        wonder_line="Shells along the walls hummed as if the shore itself were listening.",
        loss_line="The blue tiles dulled, and the court sounded lonely, like a shell with no sea inside it.",
        safe_line="Afterward the tiles gleamed blue again and the shells sang softly in the walls.",
        vessels={"tide_shell", "rain_pitcher"},
        tags={"sea"},
    ),
}

VESSELS = {
    "sun_jar": Vessel(
        id="sun_jar",
        label="sun jar",
        phrase="a sealed sun jar of warm amber glass",
        essence="light",
        contents="a swirl of tiny golden bees that carried morning on their backs",
        opening_line="A thin bright seam slipped under the lid, as if a trapped sunrise had opened one eye.",
        escape_line="Out whirled the golden bees, and each little wingbeat stole a scrap of morning from the room.",
        spread=2,
        warning="Do not lift the lid unless a keeper stands with you.",
        lesson="Curiosity must use its hands gently and its questions first.",
        tags={"light", "sun_jar"},
    ),
    "dew_bowl": Vessel(
        id="dew_bowl",
        label="dew bowl",
        phrase="a moon-white bowl brimmed with dawn dew",
        essence="dew",
        contents="round silver drops that kept flowers fresh until noon",
        opening_line="The surface trembled like a mirror waking from sleep.",
        escape_line="The dew leapt into the air in bright beads and ran laughing across the floor and petals.",
        spread=1,
        warning="Do not tilt the bowl unless the garden keeper is ready.",
        lesson="Curiosity should bend close enough to wonder, not so close that it spills.",
        tags={"dew", "dew_bowl"},
    ),
    "moon_lantern": Vessel(
        id="moon_lantern",
        label="moon lantern",
        phrase="a closed moon lantern of silver leaves",
        essence="moon",
        contents="soft white moths that kept the tower glowing after sunset",
        opening_line="The leaves of the lantern parted with a cool hush.",
        escape_line="Out floated the moon-moths, brushing silver dust from their wings as they rose.",
        spread=2,
        warning="Do not unlatch the lantern unless night itself is being tended.",
        lesson="A closed wonder may still be a wonder. It does not need to be opened by lonely hands.",
        tags={"moon", "moon_lantern"},
    ),
    "dream_basket": Vessel(
        id="dream_basket",
        label="dream basket",
        phrase="a woven dream basket tied with blue thread",
        essence="dream",
        contents="small blue birds made of sleeping songs",
        opening_line="The blue thread loosened with hardly a sound at all.",
        escape_line="The dream-birds fluttered out and hid in curtains and corners, leaving the room restless and wide-eyed.",
        spread=1,
        warning="Do not untie the thread unless the dream keeper tells you to.",
        lesson="Curiosity grows wiser when it waits long enough to be taught.",
        tags={"dream", "dream_basket"},
    ),
    "tide_shell": Vessel(
        id="tide_shell",
        label="tide shell",
        phrase="a great tide shell banded in green and pearl",
        essence="tide",
        contents="small clear fish of seawater that tugged the tides in and out",
        opening_line="The shell gave a deep sea-sound, low and round.",
        escape_line="Out splashed the tide-fish, skimming over the blue tiles and pulling wet paths behind them.",
        spread=2,
        warning="Do not turn the shell unless the sea gate is watched.",
        lesson="Curiosity should never pull a tide it cannot push back.",
        tags={"tide", "tide_shell"},
    ),
    "rain_pitcher": Vessel(
        id="rain_pitcher",
        label="rain pitcher",
        phrase="a cloud-gray pitcher stoppered with cedar",
        essence="rain",
        contents="cool rain pearls that fed orchards and cisterns",
        opening_line="The cedar stopper sighed as it came free.",
        escape_line="Rain pearls sprang out, bouncing and bursting into quick little showers all across the court.",
        spread=1,
        warning="Do not unstopper the pitcher unless the weather keeper nods.",
        lesson="Questions are lighter than storms. Ask them before you let weather loose.",
        tags={"rain", "rain_pitcher"},
    ),
}

REMEDIES = {
    "gold_bell": Remedy(
        id="gold_bell",
        label="a gold calling bell",
        handles="light",
        sense=3,
        power=3,
        use_line="rang a gold bell, and the golden bees curved back toward its warm note and folded themselves into the jar again",
        fail_line="rang a gold bell, but too many golden bees had already flown beyond the windows to hear",
        qa_line="rang the gold bell and called the golden bees back into the jar",
        tags={"bell", "light"},
    ),
    "pearl_cloth": Remedy(
        id="pearl_cloth",
        label="a pearl-soft cloth",
        handles="dew",
        sense=3,
        power=3,
        use_line="spread a pearl-soft cloth over the dancing drops, and the dew gathered back into the bowl like silver breath on a mirror",
        fail_line="spread the pearl cloth, but the dew had already sunk into too many thirsty roots to gather whole",
        qa_line="used a pearl-soft cloth to gather the dew back into the bowl",
        tags={"cloth", "dew"},
    ),
    "silver_lamp": Remedy(
        id="silver_lamp",
        label="a silver lamp",
        handles="moon",
        sense=3,
        power=3,
        use_line="lifted a silver lamp high, and the moon-moths circled its soft flame and settled back inside the lantern",
        fail_line="lifted the silver lamp, but the moon-moths had already drifted into the upper dark beyond the tower stairs",
        qa_line="raised a silver lamp and guided the moon-moths back into the lantern",
        tags={"lamp", "moon"},
    ),
    "reed_lullaby": Remedy(
        id="reed_lullaby",
        label="a reed pipe",
        handles="dream",
        sense=2,
        power=2,
        use_line="played a sleepy note on a reed pipe, and the blue dream-birds tucked their heads and fluttered meekly back into the basket",
        fail_line="played the reed pipe, but the dream-birds had already hidden too deep in the house for one song to fetch them",
        qa_line="played a lullaby on a reed pipe and coaxed the dream-birds back into the basket",
        tags={"music", "dream"},
    ),
    "shell_basin": Remedy(
        id="shell_basin",
        label="a shell basin",
        handles="tide",
        sense=3,
        power=3,
        use_line="set down a shell basin, and the tide-fish flashed toward its waiting water and slipped back into the great shell",
        fail_line="set down the shell basin, but the tide-fish had already rushed into cracks and channels too far away to gather quickly",
        qa_line="set out a shell basin and drew the tide-fish back into the shell",
        tags={"shell", "tide"},
    ),
    "cedar_flute": Remedy(
        id="cedar_flute",
        label="a cedar flute",
        handles="rain",
        sense=2,
        power=2,
        use_line="blew three steady notes on a cedar flute, and the rain pearls hopped together and rolled back into the pitcher",
        fail_line="blew the cedar flute, but too many rain pearls had already burst into weather beyond the court",
        qa_line="played a cedar flute and rolled the rain pearls back into the pitcher",
        tags={"flute", "rain"},
    ),
    "broom": Remedy(
        id="broom",
        label="a broom",
        handles="any",
        sense=1,
        power=1,
        use_line="waved a broom at the escaping wonder",
        fail_line="waved a broom helplessly while the wonder fled farther away",
        qa_line="tried to sweep the escaping wonder with a broom",
        tags={"broom"},
    ),
}

MAID_NAMES = ["Anya", "Dina", "Iris", "Mira", "Nela", "Rina", "Sia", "Tali"]
TRAITS = ["patient", "careful", "eager", "wondering", "brave", "restless"]
ELDERS = {
    "priestess": {"type": "priestess", "label": "the priestess", "title_word": "priestess"},
    "keeper_woman": {"type": "keeper_woman", "label": "the keeper", "title_word": "keeper"},
    "priest": {"type": "priest", "label": "the priest", "title_word": "priest"},
}
MENTOR_CHOICES = {"near", "away"}


def sensible_remedies() -> list[Remedy]:
    return [r for r in REMEDIES.values() if r.sense >= SENSE_MIN]


def best_remedy_for(vessel: Vessel) -> Remedy:
    options = [r for r in sensible_remedies() if r.handles == vessel.essence]
    return max(options, key=lambda r: r.power)


def realm_keeps_vessel(realm: Realm, vessel: Vessel) -> bool:
    return vessel.id in realm.vessels


def remedy_fits_vessel(remedy: Remedy, vessel: Vessel) -> bool:
    return remedy.handles == vessel.essence


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for realm in REALMS.values():
        for vessel_id in sorted(realm.vessels):
            vessel = VESSELS[vessel_id]
            for remedy in sensible_remedies():
                if remedy_fits_vessel(remedy, vessel):
                    out.append((realm.id, vessel.id, remedy.id))
    return out


def initial_reverence(trait: str) -> float:
    return 6.0 if trait in PATIENT_TRAITS else 3.0


def would_ask_first(mentor: str, trait: str) -> bool:
    return mentor == "near" and trait in PATIENT_TRAITS and initial_reverence(trait) > CURIOSITY_INIT - 1.0


def disturbance(vessel: Vessel, delay: int) -> int:
    return vessel.spread + delay


def restored_by(remedy: Remedy, vessel: Vessel, delay: int) -> bool:
    return remedy.power >= disturbance(vessel, delay)


def predict_opening(world: World, vessel_id: str) -> dict:
    sim = world.copy()
    vessel = VESSELS[vessel_id]
    _open_vessel(sim, vessel, narrate=False)
    hall = sim.get("hall")
    return {
        "escaped": hall.meters["escaped"],
        "dim": hall.meters["dim"],
        "disorder": hall.meters["disorder"],
    }


def _open_vessel(world: World, vessel: Vessel, narrate: bool = True) -> None:
    world.get("vessel").meters["opened"] += 1
    world.get("hall").meters["escaped"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, maid: Entity, elder: Entity, realm: Realm, vessel: Vessel) -> None:
    maid.memes["duty"] += 1
    world.say(
        f"In the old days, when every dawn and tide still answered to a household, there lived a little maid named {maid.id} in {realm.label}."
    )
    world.say(realm.place_line)
    world.say(realm.wonder_line)
    world.say(
        f"{maid.id} swept the quiet floor, polished small bowls and lamps, and each evening passed a shelf where rested {vessel.phrase}."
    )
    world.say(
        f"{elder.title_word.capitalize()} had trusted {maid.pronoun('object')} to dust nearby, but never to touch it."
    )


def warning(world: World, maid: Entity, elder: Entity, vessel: Vessel, mentor: str) -> None:
    pred = predict_opening(world, vessel.id)
    world.facts["predicted_dim"] = pred["dim"]
    place = "beside her" if mentor == "near" else "before walking to the farther court"
    world.say(
        f'One morning {elder.label} paused {place} and said, "{vessel.warning} What sleeps inside is useful, but it is older than your hands."'
    )
    if mentor == "near":
        world.say(f"{maid.id} nodded, because the warning was still warm in the air.")
    else:
        world.say(f"Then {elder.label} went away on another task, and the room grew very still.")


def wonder(world: World, maid: Entity, vessel: Vessel) -> None:
    maid.memes["curiosity"] += CURIOSITY_INIT
    world.say(
        f"But stillness is food for curiosity. {maid.id} kept glancing at the {vessel.label}, wondering whether {vessel.contents} truly rested inside."
    )
    world.say("The more she wondered, the larger the question seemed to grow.")


def ask_instead(world: World, maid: Entity, elder: Entity, vessel: Vessel, realm: Realm) -> None:
    maid.memes["restraint"] += 1
    maid.memes["relief"] += 1
    maid.memes["wisdom"] += 1
    world.say(
        f"Her fingers lifted, then stopped. Instead of touching the vessel, {maid.id} folded her hands and asked, \"Will you show me when the right hour comes?\""
    )
    world.say(
        f"{elder.label.capitalize()} smiled. \"That is how wise curiosity speaks,\" {elder.pronoun()} said."
    )
    world.say(
        f"For just one careful moment, {elder.pronoun()} loosened the vessel enough for {maid.id} to glimpse {vessel.contents}, and then closed it again before even a breath could wander free."
    )
    world.say(
        f"{realm.safe_line} {maid.id} went back to her work carrying not a stolen secret, but an answered question."
    )


def open_anyway(world: World, maid: Entity, vessel: Vessel) -> None:
    maid.memes["defiance"] += 1
    world.say(
        f"At last curiosity pulled harder than caution. {maid.id} looked to the door, heard no returning step, and laid both hands on the {vessel.label}."
    )
    world.say(vessel.opening_line)
    _open_vessel(world, vessel)
    world.say(vessel.escape_line)


def hall_changes(world: World, realm: Realm) -> None:
    hall = world.get("hall")
    if hall.meters["dim"] >= THRESHOLD:
        world.say(realm.loss_line)


def confess(world: World, maid: Entity, elder: Entity) -> None:
    maid.memes["honesty"] += 1
    world.say(
        f"{maid.id}'s heart knocked hard. She did not hide. She ran for {elder.label} and cried, \"Please come quickly. I opened what I was told not to open.\""
    )


def restore(world: World, maid: Entity, elder: Entity, remedy: Remedy, vessel: Vessel, realm: Realm) -> None:
    hall = world.get("hall")
    hall.meters["escaped"] = 0.0
    hall.meters["dim"] = 0.0
    hall.meters["disorder"] = 0.0
    maid.memes["relief"] += 1
    maid.memes["wisdom"] += 1
    world.say(
        f"{elder.label.capitalize()} did not waste one breath on scolding. {elder.pronoun().capitalize()} took up {remedy.label} and {remedy.use_line}."
    )
    world.say(
        f"{realm.safe_line} Only then did {maid.id} let out the breath she had been holding."
    )


def fail_restore(world: World, maid: Entity, elder: Entity, remedy: Remedy, realm: Realm) -> None:
    maid.memes["sorrow"] += 1
    maid.memes["wisdom"] += 1
    world.say(
        f"{elder.label.capitalize()} hurried to help and {remedy.fail_line}."
    )
    world.say(
        "But the wandering wonder had already gone too far. Some of it returned, yet some of it was lost to the wide world."
    )
    world.say(realm.loss_line)


def lesson_after(world: World, maid: Entity, elder: Entity, vessel: Vessel, restored: bool) -> None:
    maid.memes["lesson"] += 1
    if restored:
        world.say(
            f'Then {elder.label} knelt beside {maid.id}. "{vessel.lesson} Asking is slower than grabbing, but it keeps a house whole," {elder.pronoun()} said.'
        )
    else:
        world.say(
            f'That night {elder.label} sat beside {maid.id} and said, "{vessel.lesson} Some things can be mended, and some leave a mark when they go."'
        )
    world.say(
        f"{maid.id} bowed her head and promised that next time her question would go first and her hands would wait."
    )


def ending_image(world: World, maid: Entity, realm: Realm, outcome: str) -> None:
    if outcome == "asked":
        world.say(
            f"After that, the little maid became known for bright questions and patient hands, and the halls trusted her even more."
        )
    elif outcome == "restored":
        world.say(
            f"From then on, whenever {maid.id} passed a sealed wonder, she smiled at it, left it closed, and carried her question to a wiser door."
        )
    else:
        world.say(
            f"Years later people still said that {realm.label} was beautiful, though a little gentler than before, and that its little maid had learned to guard wonder by asking before touching."
        )


def tell(
    realm: Realm,
    vessel: Vessel,
    remedy: Remedy,
    maid_name: str = "Mira",
    trait: str = "patient",
    elder_kind: str = "priestess",
    mentor: str = "away",
    delay: int = 0,
) -> World:
    world = World(realm)
    maid = world.add(Entity(
        id=maid_name,
        kind="character",
        type="girl",
        label="the maid",
        role="maid",
        attrs={"trait": trait, "title_word": "maid"},
    ))
    elder_def = ELDERS[elder_kind]
    elder = world.add(Entity(
        id="Elder",
        kind="character",
        type=elder_def["type"],
        label=elder_def["label"],
        role="elder",
        attrs={"title_word": elder_def["title_word"]},
    ))
    hall = world.add(Entity(
        id="hall",
        kind="thing",
        type="hall",
        label=realm.label,
        role="place",
    ))
    world.add(Entity(
        id="vessel",
        kind="thing",
        type="vessel",
        label=vessel.label,
        phrase=vessel.phrase,
        role="vessel",
    ))

    introduce(world, maid, elder, realm, vessel)
    world.para()
    warning(world, maid, elder, vessel, mentor)
    wonder(world, maid, vessel)

    if would_ask_first(mentor, trait):
        world.para()
        ask_instead(world, maid, elder, vessel, realm)
        outcome = "asked"
    else:
        world.para()
        open_anyway(world, maid, vessel)
        hall_changes(world, realm)
        confess(world, maid, elder)

        world.para()
        if restored_by(remedy, vessel, delay):
            restore(world, maid, elder, remedy, vessel, realm)
            outcome = "restored"
        else:
            fail_restore(world, maid, elder, remedy, realm)
            outcome = "dimmed"

        world.para()
        lesson_after(world, maid, elder, vessel, outcome == "restored")
        ending_image(world, maid, realm, outcome)

    world.facts.update(
        maid=maid,
        elder=elder,
        hall=hall,
        realm=realm,
        vessel_cfg=vessel,
        remedy=remedy,
        mentor=mentor,
        delay=delay,
        outcome=outcome,
        escaped=hall.meters["escaped"] >= THRESHOLD or outcome in {"restored", "dimmed"},
        restored=outcome == "restored",
        asked_first=outcome == "asked",
        disturbance=disturbance(vessel, delay) if outcome != "asked" else 0,
    )
    return world


@dataclass
class StoryParams:
    realm: str
    vessel: str
    remedy: str
    maid_name: str
    trait: str
    elder: str
    mentor: str
    delay: int = 0
    seed: Optional[int] = None


KNOWLEDGE = {
    "dawn": [
        (
            "What is dawn?",
            "Dawn is the first part of the morning, when the sky begins to grow light before the sun is fully up.",
        )
    ],
    "moon": [
        (
            "Why does moonlight look soft?",
            "Moonlight is sunlight reflected from the moon, so it is much dimmer than daytime light and feels soft to our eyes.",
        )
    ],
    "sea": [
        (
            "What is a tide?",
            "A tide is the sea moving in and out along the shore. It changes through the day and night.",
        )
    ],
    "light": [
        (
            "Why is light useful?",
            "Light helps people see where they are going and what they are doing. Without enough light, rooms feel dim and hard to work in.",
        )
    ],
    "dew": [
        (
            "What is dew?",
            "Dew is tiny drops of water that gather on grass and flowers when the air cools. It often appears in the early morning.",
        )
    ],
    "dream": [
        (
            "What is a dream?",
            "A dream is a story or picture your mind makes while you are asleep. Dreams can feel strange, lovely, or silly.",
        )
    ],
    "rain": [
        (
            "Where does rain come from?",
            "Rain comes from clouds when tiny drops of water in the sky join together and grow heavy enough to fall.",
        )
    ],
    "curiosity": [
        (
            "What is curiosity?",
            "Curiosity is the feeling of wanting to know more. It can help you learn, but it should be guided by care and good questions.",
        )
    ],
    "honesty": [
        (
            "Why is it good to tell the truth after a mistake?",
            "Telling the truth helps grown-ups or helpers fix the problem sooner. It also shows courage, even when you feel afraid.",
        )
    ],
    "bell": [
        (
            "How can a bell guide animals?",
            "Some animals learn to follow a sound they know, like a bell. The sound gives them something clear to move toward.",
        )
    ],
    "lamp": [
        (
            "What does a lamp do?",
            "A lamp makes a steady light in one place. That makes it easier to see and easier for small creatures to gather around it.",
        )
    ],
    "music": [
        (
            "Why can music calm someone down?",
            "A soft, steady tune can make bodies and minds slow down and feel safer. That is why lullabies help people rest.",
        )
    ],
    "shell": [
        (
            "Why do shells sound like the sea?",
            "A shell does not really hold the sea inside it, but its curved shape changes the sounds around you in a way that can remind you of waves.",
        )
    ],
    "flute": [
        (
            "What is a flute?",
            "A flute is a musical instrument you blow into to make notes. Different notes can be gentle, bright, or sleepy.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "curiosity",
    "honesty",
    "dawn",
    "moon",
    "sea",
    "light",
    "dew",
    "dream",
    "rain",
    "bell",
    "lamp",
    "music",
    "shell",
    "flute",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    maid = f["maid"]
    realm = f["realm"]
    vessel = f["vessel_cfg"]
    outcome = f["outcome"]
    if outcome == "asked":
        return [
            f'Write a short myth for a 3-to-5-year-old about a curious little maid in {realm.label} who asks a wise elder before opening a sacred thing.',
            f"Tell a gentle myth where a maid named {maid.id} wonders about a {vessel.label}, but chooses a question over a grab and is rewarded with safe knowledge.",
            f'Write a child-facing myth that includes the word "maid" and teaches that curiosity can be wise when it asks first.',
        ]
    if outcome == "restored":
        return [
            f'Write a short myth for a 3-to-5-year-old about a curious maid who opens a sacred {vessel.label}, calls for help, and sees a wise elder put things right.',
            f"Tell a myth where {maid.id}'s curiosity causes trouble in {realm.label}, but honesty and quick help keep the loss from lasting.",
            f'Write a mythic cautionary story that includes the word "maid" and shows curiosity turning into wisdom after a mistake.',
        ]
    return [
        f'Write a sadder child-facing myth about a little maid whose curiosity opens a sacred {vessel.label}, and though help comes, part of the wonder is lost.',
        f"Tell a myth where a maid in {realm.label} learns too late that some doors should be opened only with a keeper beside her.",
        f'Write a simple myth with the word "maid" that shows curiosity, honesty, and a lasting change in a magical house.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    maid = f["maid"]
    elder = f["elder"]
    realm = f["realm"]
    vessel = f["vessel_cfg"]
    remedy = f["remedy"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about a little maid named {maid.id} who lived and worked in {realm.label}. It is also about {elder.label}, the older keeper who knew how to guard the house's wonder.",
        ),
        (
            f"What made {maid.id} curious?",
            f"{maid.id} passed {vessel.phrase} again and again and began wondering what was hidden inside it. The warning itself made the mystery feel larger.",
        ),
    ]
    if f["outcome"] == "asked":
        qa.extend([
            (
                f"Why did {maid.id} not open the {vessel.label} alone?",
                f"She stopped herself and chose to ask first because caution held more strongly than curiosity in that moment. The elder was near, and that helped her turn wondering into a question.",
            ),
            (
                "How did the story end?",
                f"It ended safely, with the wonder still guarded and the maid wiser than before. She learned that questions can open minds without opening dangerous things.",
            ),
        ])
    elif f["outcome"] == "restored":
        qa.extend([
            (
                f"What happened when {maid.id} opened the {vessel.label}?",
                f"{vessel.contents.capitalize()} escaped into the hall, and the room lost some of its order and brightness. Her curiosity changed the place around her right away.",
            ),
            (
                f"How did {elder.label} fix the problem?",
                f"{elder.label.capitalize()} {remedy.qa_line}. The help worked because the remedy matched exactly what had escaped and came soon enough.",
            ),
            (
                f"What did {maid.id} learn?",
                f"She learned to tell the truth quickly after a mistake and to ask before touching sacred things. Curiosity was not wrong, but it needed wiser steps.",
            ),
        ])
    else:
        qa.extend([
            (
                f"Could {elder.label} bring everything back?",
                f"No. {elder.label.capitalize()} tried to help, but some of the wonder had already gone too far away. The delay made the trouble bigger than the remedy could fully mend.",
            ),
            (
                "How did the story end?",
                f"It ended with the house changed a little and the maid changed a lot. She stayed safe, but she remembered that some mistakes leave a mark even after help comes.",
            ),
            (
                f"Why was honesty still important after the mistake?",
                f"Honesty brought help as fast as help could come. Even though not everything was restored, telling the truth kept the loss from growing worse.",
            ),
        ])
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"curiosity", "honesty"} | set(f["realm"].tags) | set(f["vessel_cfg"].tags) | set(f["remedy"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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
        bits = []
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        realm="dawn_hall",
        vessel="sun_jar",
        remedy="gold_bell",
        maid_name="Mira",
        trait="patient",
        elder="priestess",
        mentor="near",
        delay=0,
    ),
    StoryParams(
        realm="moon_tower",
        vessel="moon_lantern",
        remedy="silver_lamp",
        maid_name="Iris",
        trait="eager",
        elder="keeper_woman",
        mentor="away",
        delay=0,
    ),
    StoryParams(
        realm="sea_court",
        vessel="rain_pitcher",
        remedy="cedar_flute",
        maid_name="Anya",
        trait="restless",
        elder="priest",
        mentor="away",
        delay=2,
    ),
    StoryParams(
        realm="dawn_hall",
        vessel="dew_bowl",
        remedy="pearl_cloth",
        maid_name="Rina",
        trait="careful",
        elder="keeper_woman",
        mentor="away",
        delay=1,
    ),
]


def explain_rejection(realm: Realm, vessel: Vessel, remedy: Remedy) -> str:
    if not realm_keeps_vessel(realm, vessel):
        choices = ", ".join(sorted(realm.vessels))
        return (
            f"(No story: {realm.label} does not keep a {vessel.label}. In this world it keeps: {choices}.)"
        )
    if remedy.sense < SENSE_MIN:
        better = ", ".join(sorted(r.id for r in sensible_remedies()))
        return (
            f"(Refusing remedy '{remedy.id}': it is below the common-sense floor for this world. Try one of: {better}.)"
        )
    if not remedy_fits_vessel(remedy, vessel):
        return (
            f"(No story: {remedy.label} does not fit what escapes from the {vessel.label}. The remedy must match the vessel's hidden wonder.)"
        )
    return "(No story: this combination is not reasonable.)"


def outcome_of(params: StoryParams) -> str:
    if would_ask_first(params.mentor, params.trait):
        return "asked"
    vessel = VESSELS[params.vessel]
    remedy = REMEDIES[params.remedy]
    return "restored" if restored_by(remedy, vessel, params.delay) else "dimmed"


ASP_RULES = r"""
% --- gate -------------------------------------------------------------
valid(Realm, Vessel, Remedy) :-
    realm(Realm), vessel(Vessel), remedy(Remedy),
    keeps(Realm, Vessel),
    sensible(Remedy),
    matches(Remedy, Vessel).

sensible(R) :- remedy(R), sense(R, S), sense_min(M), S >= M.
matches(R, V) :- handles(R, E), essence(V, E).

% --- outcome ----------------------------------------------------------
patient_trait(T) :- trait_kind(T), patient(T).
ask_first :- mentor(near), patient_trait(T), chosen_trait(T).

severity(Sp + D) :- chosen_vessel(V), spread(V, Sp), delay(D).
contained :- chosen_remedy(R), power(R, P), severity(S), P >= S.

outcome(asked) :- ask_first.
outcome(restored) :- not ask_first, contained.
outcome(dimmed) :- not ask_first, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for realm in REALMS.values():
        lines.append(asp.fact("realm", realm.id))
        for vessel_id in sorted(realm.vessels):
            lines.append(asp.fact("keeps", realm.id, vessel_id))
    for vessel in VESSELS.values():
        lines.append(asp.fact("vessel", vessel.id))
        lines.append(asp.fact("essence", vessel.id, vessel.essence))
        lines.append(asp.fact("spread", vessel.id, vessel.spread))
    for remedy in REMEDIES.values():
        lines.append(asp.fact("remedy", remedy.id))
        lines.append(asp.fact("sense", remedy.id, remedy.sense))
        lines.append(asp.fact("power", remedy.id, remedy.power))
        lines.append(asp.fact("handles", remedy.id, remedy.handles))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    for trait in TRAITS:
        lines.append(asp.fact("trait_kind", trait))
    for trait in sorted(PATIENT_TRAITS):
        lines.append(asp.fact("patient", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_vessel", params.vessel),
        asp.fact("chosen_remedy", params.remedy),
        asp.fact("delay", params.delay),
        asp.fact("mentor", params.mentor),
        asp.fact("chosen_trait", params.trait),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    python_gate = set(valid_combos())
    clingo_gate = set(asp_valid_combos())
    if python_gate == clingo_gate:
        print(f"OK: gate matches valid_combos() ({len(python_gate)} combos).")
    else:
        rc = 1
        print("MISMATCH in gate:")
        if clingo_gate - python_gate:
            print("  only in clingo:", sorted(clingo_gate - python_gate))
        if python_gate - clingo_gate:
            print("  only in python:", sorted(python_gate - clingo_gate))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(60):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    mismatches = []
    for params in cases:
        py = outcome_of(params)
        cl = asp_outcome(params)
        if py != cl:
            mismatches.append((params, py, cl))
    if not mismatches:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)} outcome differences.")
        for params, py, cl in mismatches[:5]:
            print(f"  {params} python={py} clingo={cl}")

    try:
        sample = generate(CURATED[0])
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample, trace=True, qa=True, header="### smoke")
        if "maid" not in sample.story.lower():
            raise StoryError("smoke test story did not contain the expected seed word 'maid'.")
        print("OK: smoke test generate()/emit() succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a curious little maid in a mythic house."
    )
    ap.add_argument("--realm", choices=REALMS)
    ap.add_argument("--vessel", choices=VESSELS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--elder", choices=ELDERS)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--mentor", choices=sorted(MENTOR_CHOICES))
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long help is delayed")
    ap.add_argument("--maid-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible triples from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.realm and args.vessel and args.remedy:
        realm = REALMS[args.realm]
        vessel = VESSELS[args.vessel]
        remedy = REMEDIES[args.remedy]
        if (args.realm, args.vessel, args.remedy) not in valid_combos():
            raise StoryError(explain_rejection(realm, vessel, remedy))
    elif args.realm and args.vessel:
        realm = REALMS[args.realm]
        vessel = VESSELS[args.vessel]
        if not realm_keeps_vessel(realm, vessel):
            raise StoryError(explain_rejection(realm, vessel, best_remedy_for(vessel)))
    elif args.vessel and args.remedy:
        vessel = VESSELS[args.vessel]
        remedy = REMEDIES[args.remedy]
        if remedy.sense < SENSE_MIN or not remedy_fits_vessel(remedy, vessel):
            some_realm = next(iter(REALMS.values()))
            raise StoryError(explain_rejection(some_realm, vessel, remedy))
    elif args.remedy and REMEDIES[args.remedy].sense < SENSE_MIN:
        some_realm = next(iter(REALMS.values()))
        some_vessel = next(iter(VESSELS.values()))
        raise StoryError(explain_rejection(some_realm, some_vessel, REMEDIES[args.remedy]))

    combos = [
        combo for combo in valid_combos()
        if (args.realm is None or combo[0] == args.realm)
        and (args.vessel is None or combo[1] == args.vessel)
        and (args.remedy is None or combo[2] == args.remedy)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    realm_id, vessel_id, remedy_id = rng.choice(sorted(combos))
    return StoryParams(
        realm=realm_id,
        vessel=vessel_id,
        remedy=remedy_id,
        maid_name=args.maid_name or rng.choice(MAID_NAMES),
        trait=args.trait or rng.choice(TRAITS),
        elder=args.elder or rng.choice(sorted(ELDERS)),
        mentor=args.mentor or rng.choice(sorted(MENTOR_CHOICES)),
        delay=args.delay if args.delay is not None else rng.randint(0, 2),
    )


def generate(params: StoryParams) -> StorySample:
    if params.realm not in REALMS:
        raise StoryError(f"(Unknown realm: {params.realm})")
    if params.vessel not in VESSELS:
        raise StoryError(f"(Unknown vessel: {params.vessel})")
    if params.remedy not in REMEDIES:
        raise StoryError(f"(Unknown remedy: {params.remedy})")
    if params.elder not in ELDERS:
        raise StoryError(f"(Unknown elder: {params.elder})")
    if params.trait not in TRAITS:
        raise StoryError(f"(Unknown trait: {params.trait})")
    if params.mentor not in MENTOR_CHOICES:
        raise StoryError(f"(Unknown mentor state: {params.mentor})")

    realm = REALMS[params.realm]
    vessel = VESSELS[params.vessel]
    remedy = REMEDIES[params.remedy]
    if (params.realm, params.vessel, params.remedy) not in valid_combos():
        raise StoryError(explain_rejection(realm, vessel, remedy))

    world = tell(
        realm=realm,
        vessel=vessel,
        remedy=remedy,
        maid_name=params.maid_name,
        trait=params.trait,
        elder_kind=params.elder,
        mentor=params.mentor,
        delay=params.delay,
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
        print(f"{len(combos)} compatible (realm, vessel, remedy) combos:\n")
        for realm, vessel, remedy in combos:
            print(f"  {realm:10} {vessel:13} {remedy}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
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
            try:
                sample = generate(params)
            except StoryError as err:
                print(err)
                return
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
            header = f"### {p.maid_name}: {p.vessel} in {p.realm} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
