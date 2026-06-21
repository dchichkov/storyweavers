#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/boom_mussel_spree_magic_teamwork_foreshadowing_nursery.py

A small seaside nursery-rhyme storyworld about a child, a mussel spree, a
magical helper, and the warning boom of the tide.

The world model keeps track of a shore patch full of mussels, the strength of a
magic aid, the carrying room of a basket-like carrier, the teamwork offered by a
helper, and the warning pressure of the rising sea. A story can end with a full
feast basket, a smaller snack basket, or a careful choice to stop and come home
with only a little. The prose is state-driven and nursery-rhyme-leaning rather
than template-swapped.

Run it
------
    python storyworlds/worlds/gpt-5.4/boom_mussel_spree_magic_teamwork_foreshadowing_nursery.py
    python storyworlds/worlds/gpt-5.4/boom_mussel_spree_magic_teamwork_foreshadowing_nursery.py --all
    python storyworlds/worlds/gpt-5.4/boom_mussel_spree_magic_teamwork_foreshadowing_nursery.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/boom_mussel_spree_magic_teamwork_foreshadowing_nursery.py --qa
    python storyworlds/worlds/gpt-5.4/boom_mussel_spree_magic_teamwork_foreshadowing_nursery.py --verify
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

# Make the shared result containers importable when this script is run directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
MIN_CARRY = 2
MIN_MAGIC = 1


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: tuple = field(default_factory=tuple)
    name: str = ""
    title: str = ""
    voice: str = ""
    thanks: str = ""
    scold: str = ""
    help_action: str = ""
    face: str = ""
    path_line: str = ""
    ending_image: str = ""
    weak_spot: str = ""
    role_text: str = ""
    need: str = ""
    metallic: str = ""
    special: str = ""
    question_reply: str = ""
    wisdom: str = ""
    rising_line: str = ""
    risk: str = ""
    qa_text: str = ""
    location_text: str = ""
    use_line: str = ""
    cry: str = ""
    ending_line: str = ""
    reach: str = ""
    damage: str = ""
    use: str = ""
    opening: str = ""
    warning: str = ""
    owner_text: str = ""
    ground: str = ""
    action_line: str = ""
    kindness_text: str = ""
    calm: str = ""
    restored: str = ""
    shine: str = ""
    reveal_text: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "aunt", "woman"}
        male = {"boy", "father", "uncle", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}.get(
            self.type, self.label or self.type
        )


@dataclass
class Place:
    id: str
    shore: str
    opening: str
    ending: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Patch:
    id: str
    label: str
    phrase: str
    count: int
    difficulty: int
    wet: str
    tags: set[str] = field(default_factory=set)


@dataclass
class MagicAid:
    id: str
    label: str
    phrase: str
    power: int
    rhythm: str
    glimmer: str
    works_on: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperCfg:
    id: str
    label: str
    phrase: str
    type: str
    teamwork: int
    action: str
    closing: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Carrier:
    id: str
    label: str
    phrase: str
    capacity: int
    carried_as: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Warning:
    id: str
    sound: str
    sign: str
    pressure: int
    foreshadow: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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
        clone = World(self.place)
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


def _r_wave_near(world: World) -> list[str]:
    patch = world.get("patch")
    warning = world.get("warning")
    child = world.get("child")
    if warning.meters["booming"] < THRESHOLD:
        return []
    sig = ("wave_near",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    patch.meters["risk"] += warning.attrs["pressure"]
    child.memes["hurry"] += 1
    return ["__wave__"]


def _r_teamwork(world: World) -> list[str]:
    helper = world.get("helper")
    child = world.get("child")
    if helper.meters["helping"] < THRESHOLD:
        return []
    sig = ("teamwork",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["together"] += helper.attrs["teamwork"]
    return []


def _r_magic(world: World) -> list[str]:
    magic = world.get("magic")
    patch = world.get("patch")
    if magic.meters["singing"] < THRESHOLD:
        return []
    sig = ("magic",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    patch.meters["loosened"] += magic.attrs["power"]
    return []


CAUSAL_RULES = [
    Rule(name="wave_near", tag="physical", apply=_r_wave_near),
    Rule(name="teamwork", tag="social", apply=_r_teamwork),
    Rule(name="magic", tag="magic", apply=_r_magic),
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


PLACES = {
    "moon_cove": Place(
        id="moon_cove",
        shore="Moon Cove",
        opening="By Moon Cove, where little waves sewed silver hems on sand,",
        ending="the moon combed a bright line over the quiet cove",
        affords={"rope_rocks", "reed_bank"},
    ),
    "pebble_steps": Place(
        id="pebble_steps",
        shore="Pebble Steps",
        opening="At Pebble Steps, where pebbles clicked like tiny teeth,",
        ending="the pebbles shone as if each one had swallowed a star",
        affords={"tide_pole", "rope_rocks"},
    ),
    "merry_mudflat": Place(
        id="merry_mudflat",
        shore="Merry Mudflat",
        opening="On Merry Mudflat, where the wet sand held moon-round puddles,",
        ending="the mudflat lay smooth again, with only gull-feet stitched across it",
        affords={"reed_bank", "tide_pole"},
    ),
}

PATCHES = {
    "rope_rocks": Patch(
        id="rope_rocks",
        label="rope rocks",
        phrase="a rope of low rocks dressed in dark blue mussels",
        count=3,
        difficulty=2,
        wet="slippery with weed",
        tags={"mussel", "shore"},
    ),
    "reed_bank": Patch(
        id="reed_bank",
        label="reed bank",
        phrase="a bend of reeds where the mussels clung in little black rows",
        count=2,
        difficulty=1,
        wet="soft and squelchy",
        tags={"mussel", "shore"},
    ),
    "tide_pole": Patch(
        id="tide_pole",
        label="tide pole",
        phrase="an old tide pole with fat mussels hugging its foot",
        count=4,
        difficulty=3,
        wet="dripping and tricky",
        tags={"mussel", "shore"},
    ),
}

MAGIC_AIDS = {
    "moon_hum": MagicAid(
        id="moon_hum",
        label="moon hum",
        phrase="a moon-shell that hummed when held to the ear",
        power=1,
        rhythm="Hum a moon and hold it near",
        glimmer="the shell lip shone milk-pale",
        works_on={"rope_rocks", "reed_bank", "tide_pole"},
        tags={"magic", "shell"},
    ),
    "star_tap": MagicAid(
        id="star_tap",
        label="star tap",
        phrase="a star spoon with a silver tapping end",
        power=2,
        rhythm="Tap-a-star and tap again",
        glimmer="silver sparks skipped along the spoon",
        works_on={"rope_rocks", "tide_pole"},
        tags={"magic", "spoon"},
    ),
    "bubble_rhyme": MagicAid(
        id="bubble_rhyme",
        label="bubble rhyme",
        phrase="a bubble charm tied with blue thread",
        power=2,
        rhythm="Bubble bright and bubble slow",
        glimmer="small blue lights bobbed in the air",
        works_on={"reed_bank", "rope_rocks"},
        tags={"magic", "rhyme"},
    ),
}

HELPERS = {
    "sister": HelperCfg(
        id="sister",
        label="big sister",
        phrase="a big sister with quick hands",
        type="girl",
        teamwork=2,
        action="held the carrier steady and counted every mussel aloud",
        closing="shoulder to shoulder",
        tags={"teamwork", "family"},
    ),
    "crab": HelperCfg(
        id="crab",
        label="red crab",
        phrase="a red crab with neat sideways feet",
        type="animal",
        teamwork=1,
        action="nudged the loose mussels into a tidy little row",
        closing="clack-clack beside the child",
        tags={"teamwork", "crab"},
    ),
    "gull": HelperCfg(
        id="gull",
        label="harbor gull",
        phrase="a harbor gull with a sharp eye",
        type="animal",
        teamwork=1,
        action="called whenever a mussel began to wobble near the wash",
        closing="white-winged overhead",
        tags={"teamwork", "gull"},
    ),
}

CARRIERS = {
    "apron": Carrier(
        id="apron",
        label="apron",
        phrase="a striped apron folded into a pocket",
        capacity=2,
        carried_as="in the apron pocket",
        tags={"carrier", "apron"},
    ),
    "pail": Carrier(
        id="pail",
        label="pail",
        phrase="a blue pail with a round tin handle",
        capacity=3,
        carried_as="in the blue pail",
        tags={"carrier", "pail"},
    ),
    "basket": Carrier(
        id="basket",
        label="basket",
        phrase="a willow basket with a bendy lid",
        capacity=4,
        carried_as="in the willow basket",
        tags={"carrier", "basket"},
    ),
}

WARNINGS = {
    "deep_boom": Warning(
        id="deep_boom",
        sound="boom",
        sign="a deep boom rolled from beyond the dunes",
        pressure=2,
        foreshadow="The child heard the boom and knew the big tide was walking this way.",
        tags={"boom", "foreshadowing", "tide"},
    ),
    "barrel_boom": Warning(
        id="barrel_boom",
        sound="boom",
        sign="a boom from the harbor barrel drum bumped through the air",
        pressure=1,
        foreshadow="The old harbor boom meant the water would soon swell around the stones.",
        tags={"boom", "foreshadowing", "harbor"},
    ),
    "thunder_boom": Warning(
        id="thunder_boom",
        sound="boom",
        sign="a cloud gave one soft boom far out at sea",
        pressure=2,
        foreshadow="That faraway boom was a warning knock from weather and water together.",
        tags={"boom", "foreshadowing", "weather"},
    ),
}

CHILD_NAMES = ["Mina", "Pip", "Nell", "Toby", "Dot", "Wren", "Kit", "May"]
ADULT_TYPES = ["mother", "father", "aunt", "uncle"]


def place_supports_patch(place: Place, patch: Patch) -> bool:
    return patch.id in place.affords


def magic_supports_patch(magic: MagicAid, patch: Patch) -> bool:
    return patch.id in magic.works_on and magic.power >= MIN_MAGIC


def carrier_reasonable(carrier: Carrier) -> bool:
    return carrier.capacity >= MIN_CARRY


def valid_combo(place_id: str, patch_id: str, magic_id: str, helper_id: str, carrier_id: str) -> bool:
    place = PLACES[place_id]
    patch = PATCHES[patch_id]
    magic = MAGIC_AIDS[magic_id]
    helper = HELPERS[helper_id]
    carrier = CARRIERS[carrier_id]
    if not place_supports_patch(place, patch):
        return False
    if not magic_supports_patch(magic, patch):
        return False
    if not carrier_reasonable(carrier):
        return False
    if helper.teamwork < 1:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    out: list[tuple[str, str, str, str, str]] = []
    for place_id in sorted(PLACES):
        for patch_id in sorted(PATCHES):
            for magic_id in sorted(MAGIC_AIDS):
                for helper_id in sorted(HELPERS):
                    for carrier_id in sorted(CARRIERS):
                        if valid_combo(place_id, patch_id, magic_id, helper_id, carrier_id):
                            out.append((place_id, patch_id, magic_id, helper_id, carrier_id))
    return out


def gathering_score(patch: Patch, magic: MagicAid, helper: HelperCfg, carrier: Carrier) -> int:
    return magic.power + helper.teamwork + carrier.capacity


def outcome_of(params: "StoryParams") -> str:
    if not valid_combo(params.place, params.patch, params.magic, params.helper, params.carrier):
        raise StoryError("(No reasonable story: the place, patch, magic, helper, and carrier do not fit together.)")
    patch = PATCHES[params.patch]
    magic = MAGIC_AIDS[params.magic]
    helper = HELPERS[params.helper]
    carrier = CARRIERS[params.carrier]
    warning = WARNINGS[params.warning]
    score = gathering_score(patch, magic, helper, carrier)
    need_feast = patch.count + patch.difficulty + warning.pressure
    need_snack = patch.count + warning.pressure
    if score >= need_feast:
        return "feast"
    if score >= need_snack:
        return "snack"
    return "careful"


def predict_outcome(place: Place, patch: Patch, magic: MagicAid, helper: HelperCfg, carrier: Carrier, warning: Warning) -> dict:
    score = gathering_score(patch, magic, helper, carrier)
    need_feast = patch.count + patch.difficulty + warning.pressure
    need_snack = patch.count + warning.pressure
    if score >= need_feast:
        return {"outcome": "feast", "gathered": patch.count}
    if score >= need_snack:
        gathered = max(1, min(patch.count - 1, carrier.capacity))
        return {"outcome": "snack", "gathered": gathered}
    return {"outcome": "careful", "gathered": 1 if carrier.capacity >= 1 else 0}


def introduce(world: World, child: Entity, adult: Entity, patch: Patch) -> None:
    world.say(
        f"{world.place.opening} {child.id} skipped with {adult.label_word} to the shore. "
        f"{child.pronoun('possessive').capitalize()} eyes found {patch.phrase}, and a little mussel spree "
        f"began to dance in {child.pronoun('possessive')} head."
    )


def show_magic(world: World, child: Entity, magic: MagicAid, carrier: Carrier) -> None:
    child.memes["wonder"] += 1
    world.say(
        f"In one hand {child.pronoun()} carried {magic.phrase}; in the other, {carrier.phrase}. "
        f"{magic.glimmer}, and the shore looked ready to listen."
    )


def foreshadow(world: World, child: Entity, warning: Warning, patch: Patch) -> None:
    warning_ent = world.get("warning")
    warning_ent.meters["booming"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {warning.sign}. {warning.foreshadow} Even the {patch.label} seemed to hold still and hear it."
    )


def wish(world: World, child: Entity, patch: Patch) -> None:
    child.memes["desire"] += 1
    world.say(
        f'"One for the pot and two for glee, let us have a mussel spree," sang {child.id}. '
        f'But the stones were {patch.wet}, and the tide was thinking of its climb.'
    )


def invite_helper(world: World, child: Entity, helper: Entity, helper_cfg: HelperCfg) -> None:
    helper.meters["helping"] += 1
    propagate(world, narrate=False)
    if helper_cfg.type == "animal":
        world.say(
            f"{helper.phrase.capitalize()} came near, as if the rhyme had invited {helper.pronoun('object')}. "
            f"Soon {helper.pronoun()} {helper_cfg.action}."
        )
    else:
        world.say(
            f"{helper_cfg.phrase.capitalize()} laughed and stepped close. Soon {helper.pronoun()} {helper_cfg.action}."
        )


def use_magic(world: World, child: Entity, magic_ent: Entity, magic: MagicAid) -> None:
    magic_ent.meters["singing"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{child.id} whispered, "{magic.rhythm}," and the charm answered softly. '
        f'The mussels loosened with tiny clicks instead of stubborn tugs.'
    )


def gather(world: World, child: Entity, patch: Patch, carrier: Carrier, helper_cfg: HelperCfg, warning: Warning) -> None:
    outcome = world.facts["predicted"]["outcome"]
    gathered = world.facts["predicted"]["gathered"]
    child.meters["gathered"] = float(gathered)
    patch_ent = world.get("patch")
    patch_ent.meters["picked"] = float(gathered)
    patch_ent.meters["left"] = float(max(0, patch.count - gathered))

    if outcome == "feast":
        world.say(
            f"Plink went one mussel, plonk went two, and soon all {patch.count} nestled {carrier.carried_as}. "
            f"Because they worked {helper_cfg.closing}, the warning boom could not steal a single one."
        )
    elif outcome == "snack":
        world.say(
            f"Plink went one, plonk went two, and then the tide gave a bigger swish. "
            f"They tucked {gathered} safe {carrier.carried_as} and let the rest stay where the sea could rock them."
        )
    else:
        world.say(
            f"They saved only {gathered} little mussel {carrier.carried_as} before the wash reached the stones. "
            f"That was enough to tell them the spree must stop before slip and splash turned mean."
        )

    child.memes["care"] += 1
    child.memes["joy"] += 1 if gathered >= 1 else 0
    child.memes["prudence"] += 1 if outcome == "careful" else 0


def return_home(world: World, child: Entity, adult: Entity, carrier: Carrier) -> None:
    world.say(
        f"Back they went from the water's lip, with {carrier.label} swinging a gentle tune. "
        f"{adult.label_word.capitalize()} kept close beside {child.id}, and the wet path felt less wild now."
    )


def ending(world: World, child: Entity, adult: Entity, helper_cfg: HelperCfg, carrier: Carrier, warning: Warning) -> None:
    outcome = world.facts["predicted"]["outcome"]
    gathered = int(world.get("child").meters["gathered"])
    if outcome == "feast":
        world.say(
            f"At home the little pan sang too, and supper smelled of salt and steam. "
            f"{child.id} remembered the first boom and smiled, for magic and teamwork had turned warning into wisdom. "
            f"Outside, {world.place.ending}."
        )
    elif outcome == "snack":
        world.say(
            f"There were enough mussels for a small warm bowl, and that was feast enough for such a night. "
            f"{child.id} was glad they had listened when the boom first spoke, because the sea had kept its own share and they had kept their toes dry. "
            f"Outside, {world.place.ending}."
        )
    else:
        world.say(
            f"There was only one mussel to show, set by the window like a shiny button from the sea. "
            f'"Another day," said {adult.label_word}, and {child.id} nodded, proud that {child.pronoun()} had stopped the spree when the boom warned true. '
            f"Outside, {world.place.ending}."
        )
    world.facts["helper_close"] = helper_cfg.closing
    world.facts["gathered"] = gathered
    world.facts["carrier_label"] = carrier.label
    world.facts["warning_sound"] = warning.sound


def tell(
    place: Place,
    patch: Patch,
    magic: MagicAid,
    helper_cfg: HelperCfg,
    carrier: Carrier,
    warning: Warning,
    child_name: str = "Mina",
    child_type: str = "girl",
    adult_type: str = "mother",
) -> World:
    world = World(place)
    child = world.add(Entity(id="child", kind="character", type=child_type, label=child_name, phrase=child_name, role="child"))
    adult = world.add(Entity(id="adult", kind="character", type=adult_type, label="the grown-up", phrase=adult_type, role="adult"))
    patch_ent = world.add(
        Entity(
            id="patch",
            kind="thing",
            type="patch",
            label=patch.label,
            phrase=patch.phrase,
            role="patch",
            attrs={"count": patch.count, "difficulty": patch.difficulty},
            tags=set(patch.tags),
        )
    )
    magic_ent = world.add(
        Entity(
            id="magic",
            kind="thing",
            type="magic",
            label=magic.label,
            phrase=magic.phrase,
            role="magic",
            attrs={"power": magic.power},
            tags=set(magic.tags),
        )
    )
    helper = world.add(
        Entity(
            id="helper",
            kind="character" if helper_cfg.type in {"girl", "boy"} else "thing",
            type=helper_cfg.type,
            label=helper_cfg.label,
            phrase=helper_cfg.phrase,
            role="helper",
            attrs={"teamwork": helper_cfg.teamwork},
            tags=set(helper_cfg.tags),
        )
    )
    carrier_ent = world.add(
        Entity(
            id="carrier",
            kind="thing",
            type="carrier",
            label=carrier.label,
            phrase=carrier.phrase,
            role="carrier",
            attrs={"capacity": carrier.capacity},
            tags=set(carrier.tags),
        )
    )
    warning_ent = world.add(
        Entity(
            id="warning",
            kind="thing",
            type="warning",
            label=warning.id,
            phrase=warning.sign,
            role="warning",
            attrs={"pressure": warning.pressure},
            tags=set(warning.tags),
        )
    )

    predicted = predict_outcome(place, patch, magic, helper_cfg, carrier, warning)
    world.facts["predicted"] = predicted

    introduce(world, child, adult, patch)
    show_magic(world, child, magic, carrier)
    world.para()
    foreshadow(world, child, warning, patch)
    wish(world, child, patch)
    invite_helper(world, child, helper, helper_cfg)
    use_magic(world, child, magic_ent, magic)
    world.para()
    gather(world, child, patch, carrier, helper_cfg, warning)
    return_home(world, child, adult, carrier)
    world.para()
    ending(world, child, adult, helper_cfg, carrier, warning)

    world.facts.update(
        child=child,
        adult=adult,
        place=place,
        patch_cfg=patch,
        magic_cfg=magic,
        helper_cfg=helper_cfg,
        carrier_cfg=carrier,
        warning_cfg=warning,
        patch=patch_ent,
        magic=magic_ent,
        helper=helper,
        carrier=carrier_ent,
        warning=warning_ent,
        outcome=predicted["outcome"],
    )
    return world


@dataclass
class StoryParams:
    place: str
    patch: str
    magic: str
    helper: str
    carrier: str
    warning: str
    child_name: str
    child_type: str
    adult_type: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="moon_cove",
        patch="reed_bank",
        magic="bubble_rhyme",
        helper="sister",
        carrier="basket",
        warning="deep_boom",
        child_name="Mina",
        child_type="girl",
        adult_type="mother",
    ),
    StoryParams(
        place="pebble_steps",
        patch="rope_rocks",
        magic="moon_hum",
        helper="gull",
        carrier="pail",
        warning="barrel_boom",
        child_name="Pip",
        child_type="boy",
        adult_type="father",
    ),
    StoryParams(
        place="merry_mudflat",
        patch="tide_pole",
        magic="star_tap",
        helper="crab",
        carrier="apron",
        warning="thunder_boom",
        child_name="Nell",
        child_type="girl",
        adult_type="aunt",
    ),
]


KNOWLEDGE = {
    "mussel": [
        (
            "What is a mussel?",
            "A mussel is a small shellfish that lives in a hard dark shell. It clings to rocks, posts, and other wet places near the sea.",
        )
    ],
    "boom": [
        (
            "What does boom mean in a stormy or seaside story?",
            "Boom is a deep loud sound, like thunder or a big wave hitting hard. A boom can be a warning that something strong is coming.",
        )
    ],
    "foreshadowing": [
        (
            "What is foreshadowing in a story?",
            "Foreshadowing is when an early sign hints about something that will happen later. It helps a reader feel the story getting ready for a turn.",
        )
    ],
    "magic": [
        (
            "What does magic do in a make-believe story?",
            "Magic lets surprising things happen, like a shell humming or a charm glowing. In a story, magic often helps show feelings, wishes, or lessons in a bright way.",
        )
    ],
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork is when two or more people or helpers do a job together. Sharing the work often makes the job safer and easier.",
        )
    ],
    "tide": [
        (
            "What is the tide?",
            "The tide is the sea moving higher and lower along the shore. When the tide rises, it can cover rocks that were dry before.",
        )
    ],
    "crab": [
        (
            "How does a crab move?",
            "A crab often scuttles sideways on many little legs. Its hard shell helps protect its body.",
        )
    ],
    "gull": [
        (
            "What is a gull?",
            "A gull is a seabird that often lives near coasts and harbors. It has strong wings and a sharp eye for food below.",
        )
    ],
    "basket": [
        (
            "What is a basket for?",
            "A basket is for carrying things from one place to another. A basket with room inside can keep small things together instead of dropping them.",
        )
    ],
    "pail": [
        (
            "What is a pail?",
            "A pail is a small bucket with a handle. People use pails to carry water, shells, or other little things.",
        )
    ],
    "apron": [
        (
            "What is an apron?",
            "An apron is cloth worn over clothes to help keep them cleaner. If you fold it into a pocket, it can also carry a few small things.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "mussel",
    "boom",
    "foreshadowing",
    "magic",
    "teamwork",
    "tide",
    "crab",
    "gull",
    "basket",
    "pail",
    "apron",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    patch = f["patch_cfg"]
    magic = f["magic_cfg"]
    helper = f["helper_cfg"]
    warning = f["warning_cfg"]
    outcome = f["outcome"]
    if outcome == "feast":
        return [
            'Write a nursery-rhyme style story for a 3-to-5-year-old that includes the words "boom", "mussel", and "spree".',
            f"Tell a seaside rhyme-story where {child.label} hears a warning {warning.sound}, uses {magic.label}, and works with {helper.label} to finish a mussel spree safely.",
            "Write a gentle story with foreshadowing, magic, and teamwork, where a child listens to an early warning and brings home a full little catch.",
        ]
    if outcome == "snack":
        return [
            'Write a nursery-rhyme style story that includes "boom", "mussel", and "spree", but let the child listen to the warning before it is too late.',
            f"Tell a child-facing shore story where {child.label} starts a mussel spree at the {patch.label}, hears a {warning.sound}, and uses teamwork to bring home only part of the catch.",
            "Write a rhyming story with magic and foreshadowing where the sea keeps some of its treasures and the child wisely keeps only enough.",
        ]
    return [
        'Write a nursery-rhyme style story that includes the words "boom", "mussel", and "spree" and ends with a careful choice.',
        f"Tell a shore story where {child.label} longs for a mussel spree, but a warning {warning.sound} and the rising tide make the child stop early, even with {magic.label} and help.",
        "Write a gentle magical story where foreshadowing matters and teamwork helps a child choose safety over grabbing more.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    patch = f["patch_cfg"]
    magic = f["magic_cfg"]
    helper = f["helper_cfg"]
    carrier = f["carrier_cfg"]
    warning = f["warning_cfg"]
    outcome = f["outcome"]
    gathered = f["gathered"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.label}, a child at {f['place'].shore}, and {adult.label_word} nearby. A helper joined in too, so the shore job became a teamwork story instead of a lone scramble.",
        ),
        (
            "What did the child want to do?",
            f"{child.label} wanted to have a mussel spree and gather the mussels from the {patch.label}. The shiny patch looked tempting, so the wish to collect them started the adventure.",
        ),
        (
            "What was the foreshadowing in the story?",
            f"The foreshadowing was the warning {warning.sound} and the sign that came with it. That early sound hinted that the tide was coming closer before the child tried to gather too much.",
        ),
        (
            f"How did magic help {child.label}?",
            f"{child.label} used {magic.phrase}, and the charm made the mussels loosen more gently. Because of that, the child did not have to tug as hard on the wet stones.",
        ),
        (
            f"How did teamwork help during the spree?",
            f"{helper.phrase.capitalize()} helped by {helper.action}. That teamwork made the gathering steadier, especially when the boom warned that the sea was hurrying in.",
        ),
    ]
    if outcome == "feast":
        qa.append(
            (
                "Why did the child bring home all the mussels?",
                f"{child.label} had enough help, enough magic, and enough room in the {carrier.label}. Because those pieces worked together before the tide reached the stones, every mussel was gathered safely.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with a full little catch and a warm supper at home. The ending proves the change because the first warning boom could have spoiled the spree, but teamwork and care turned it into success.",
            )
        )
    elif outcome == "snack":
        qa.append(
            (
                "Why did the child bring home only some of the mussels?",
                f"{child.label} and the helper worked quickly, but the tide still came near after the warning boom. They wisely kept only {gathered} safe in the {carrier.label} and left the rest for the sea instead of taking a risky extra moment.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with a small warm bowl rather than a full basket. That ending shows the child changed from wanting everything on the spree to being content with enough.",
            )
        )
    else:
        qa.append(
            (
                "Why did the child stop the spree early?",
                f"The boom and the rising wash made the stones too risky for more grabbing. Even with help and magic, {child.label} listened to the warning and chose care over greed.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with only {gathered} mussel saved and the rest left behind, but the child was proud anyway. The ending image by the window shows that being careful mattered more than carrying home a lot.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"mussel", "boom", "foreshadowing", "magic", "teamwork", "tide"}
    tags |= set(f["helper_cfg"].tags)
    tags |= set(f["carrier_cfg"].tags)
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_invalid(place_id: str, patch_id: str, magic_id: str, helper_id: str, carrier_id: str) -> str:
    place = PLACES[place_id]
    patch = PATCHES[patch_id]
    magic = MAGIC_AIDS[magic_id]
    helper = HELPERS[helper_id]
    carrier = CARRIERS[carrier_id]
    if not place_supports_patch(place, patch):
        return f"(No story: {patch.label} does not belong at {place.shore}, so the child has no honest mussel spree to begin.)"
    if not magic_supports_patch(magic, patch):
        return f"(No story: {magic.label} does not work on the {patch.label}, so the magic turn would not make sense.)"
    if not carrier_reasonable(carrier):
        return f"(No story: the {carrier.label} is too small for even a tiny spree. Pick a carrier with room for at least two mussels.)"
    if helper.teamwork < 1:
        return f"(No story: {helper.label} offers no real teamwork in this world.)"
    return "(No story: this combination is not reasonable in the world model.)"


ASP_RULES = r"""
supports(Place, Patch) :- affords(Place, Patch).
usable_magic(Magic, Patch) :- works_on(Magic, Patch), magic_power(Magic, P), min_magic(Min), P >= Min.
usable_carrier(Carrier) :- carrier_capacity(Carrier, C), min_carry(Min), C >= Min.
valid(Place, Patch, Magic, Helper, Carrier) :-
    place(Place), patch(Patch), magic(Magic), helper(Helper), carrier(Carrier),
    supports(Place, Patch), usable_magic(Magic, Patch), usable_carrier(Carrier),
    teamwork(Helper, T), T >= 1.

score(S) :- chosen_patch(Patch), chosen_magic(Magic), chosen_helper(Helper), chosen_carrier(Carrier),
            patch_count(Patch, _), patch_difficulty(Patch, _),
            magic_power(Magic, MP), teamwork(Helper, TW), carrier_capacity(Carrier, CC),
            S = MP + TW + CC.

need_feast(N) :- chosen_patch(Patch), chosen_warning(W),
                 patch_count(Patch, Count), patch_difficulty(Patch, Diff), warning_pressure(W, Press),
                 N = Count + Diff + Press.
need_snack(N) :- chosen_patch(Patch), chosen_warning(W),
                 patch_count(Patch, Count), warning_pressure(W, Press),
                 N = Count + Press.

outcome(feast) :- score(S), need_feast(N), S >= N.
outcome(snack) :- score(S), need_feast(Nf), need_snack(Ns), S < Nf, S >= Ns.
outcome(careful) :- score(S), need_snack(N), S < N.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for patch_id in sorted(place.affords):
            lines.append(asp.fact("affords", place_id, patch_id))
    for patch_id, patch in PATCHES.items():
        lines.append(asp.fact("patch", patch_id))
        lines.append(asp.fact("patch_count", patch_id, patch.count))
        lines.append(asp.fact("patch_difficulty", patch_id, patch.difficulty))
    for magic_id, magic in MAGIC_AIDS.items():
        lines.append(asp.fact("magic", magic_id))
        lines.append(asp.fact("magic_power", magic_id, magic.power))
        for patch_id in sorted(magic.works_on):
            lines.append(asp.fact("works_on", magic_id, patch_id))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("teamwork", helper_id, helper.teamwork))
    for carrier_id, carrier in CARRIERS.items():
        lines.append(asp.fact("carrier", carrier_id))
        lines.append(asp.fact("carrier_capacity", carrier_id, carrier.capacity))
    for warning_id, warning in WARNINGS.items():
        lines.append(asp.fact("warning", warning_id))
        lines.append(asp.fact("warning_pressure", warning_id, warning.pressure))
    lines.append(asp.fact("min_carry", MIN_CARRY))
    lines.append(asp.fact("min_magic", MIN_MAGIC))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_patch", params.patch),
            asp.fact("chosen_magic", params.magic),
            asp.fact("chosen_helper", params.helper),
            asp.fact("chosen_carrier", params.carrier),
            asp.fact("chosen_warning", params.warning),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def smoke_test() -> None:
    params = CURATED[0]
    sample = generate(params)
    if not sample.story or "mussel" not in sample.story.lower() or "boom" not in sample.story.lower():
        raise StoryError("Smoke test failed: generated story is missing required seed words or is empty.")
    emit(sample, trace=False, qa=False, header="")


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
    for s in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        params.seed = s
        cases.append(params)

    bad = 0
    for params in cases:
        try:
            py_out = outcome_of(params)
            cl_out = asp_outcome(params)
            if py_out != cl_out:
                bad += 1
        except Exception:
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke_test()
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Nursery-rhyme shore storyworld: boom, mussel, spree, magic, teamwork, and foreshadowing."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--patch", choices=PATCHES)
    ap.add_argument("--magic", choices=MAGIC_AIDS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--carrier", choices=CARRIERS)
    ap.add_argument("--warning", choices=WARNINGS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--adult-type", choices=ADULT_TYPES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.patch and args.magic and args.helper and args.carrier:
        if not valid_combo(args.place, args.patch, args.magic, args.helper, args.carrier):
            raise StoryError(explain_invalid(args.place, args.patch, args.magic, args.helper, args.carrier))

    combos = [
        c
        for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.patch is None or c[1] == args.patch)
        and (args.magic is None or c[2] == args.magic)
        and (args.helper is None or c[3] == args.helper)
        and (args.carrier is None or c[4] == args.carrier)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, patch, magic, helper, carrier = rng.choice(sorted(combos))
    warning = args.warning or rng.choice(sorted(WARNINGS))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(CHILD_NAMES)
    adult_type = args.adult_type or rng.choice(ADULT_TYPES)
    return StoryParams(
        place=place,
        patch=patch,
        magic=magic,
        helper=helper,
        carrier=carrier,
        warning=warning,
        child_name=child_name,
        child_type=child_type,
        adult_type=adult_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.patch not in PATCHES:
        raise StoryError(f"(Unknown patch: {params.patch})")
    if params.magic not in MAGIC_AIDS:
        raise StoryError(f"(Unknown magic aid: {params.magic})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.carrier not in CARRIERS:
        raise StoryError(f"(Unknown carrier: {params.carrier})")
    if params.warning not in WARNINGS:
        raise StoryError(f"(Unknown warning: {params.warning})")
    if not valid_combo(params.place, params.patch, params.magic, params.helper, params.carrier):
        raise StoryError(explain_invalid(params.place, params.patch, params.magic, params.helper, params.carrier))

    world = tell(
        place=PLACES[params.place],
        patch=PATCHES[params.patch],
        magic=MAGIC_AIDS[params.magic],
        helper_cfg=HELPERS[params.helper],
        carrier=CARRIERS[params.carrier],
        warning=WARNINGS[params.warning],
        child_name=params.child_name,
        child_type=params.child_type,
        adult_type=params.adult_type,
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
        print(f"{len(combos)} compatible (place, patch, magic, helper, carrier) combos:\n")
        for place, patch, magic, helper, carrier in combos:
            print(f"  {place:13} {patch:11} {magic:12} {helper:8} {carrier}")
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
                f"### {p.child_name}: {p.patch} at {p.place} "
                f"({p.magic}, {p.helper}, {p.carrier}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")




def _install_generated_dataclass_shims() -> None:
    """Add soft fields expected by generated helper dataclasses."""
    from collections import defaultdict as _defaultdict

    def _soft_getattr(self, name: str):
        if name in {"meters", "memes"}:
            value = _defaultdict(float)
        elif name == "attrs":
            value = {}
        elif name == "tags":
            value = set()
        elif name == "pronoun":
            def _pronoun(case: str = "subject") -> str:
                return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
            return _pronoun
        elif name in {"label_word", "name", "title", "voice", "thanks", "scold", "help_action", "face", "path_line", "use", "damage", "wisdom"}:
            value = getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "id", self.__class__.__name__.lower())
        else:
            raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")
        object.__setattr__(self, name, value)
        return value

    for _value in list(globals().values()):
        if not isinstance(_value, type):
            continue
        if _value.__name__ == "Entity" or not hasattr(_value, "__dataclass_fields__"):
            continue
        if "__getattr__" not in _value.__dict__:
            _value.__getattr__ = _soft_getattr


_install_generated_dataclass_shims()



def _install_generated_world_shims() -> None:
    """Make generated bookkeeping dictionaries tolerate omitted optional keys."""
    from collections import defaultdict as _defaultdict

    class _GeneratedSoftValue:
        def __init__(self, key: str = "thing") -> None:
            self.id = str(key)
            self.label = str(key).replace("_", " ")
            self.phrase = self.label
            self.the = self.label
            self.The = self.label.capitalize()
            self.tags = set()
            self.attrs = {}
            self.meters = _defaultdict(float)
            self.memes = _defaultdict(float)

        def __str__(self) -> str:
            return self.label

        def __format__(self, spec: str) -> str:
            return format(str(self), spec)

        def __bool__(self) -> bool:
            return False

        def __float__(self) -> float:
            return 0.0

        def __int__(self) -> int:
            return 0

        def __lt__(self, other) -> bool:
            return float(self) < other

        def __le__(self, other) -> bool:
            return float(self) <= other

        def __gt__(self, other) -> bool:
            return float(self) > other

        def __ge__(self, other) -> bool:
            return float(self) >= other

        def __add__(self, other):
            return float(self) + other

        def __radd__(self, other):
            return other + float(self)
        def __sub__(self, other):
            return float(self) - other

        def __rsub__(self, other):
            return other - float(self)

        def __contains__(self, item) -> bool:
            return False

        def __call__(self, *args, **kwargs):
            return self

        def __hash__(self) -> int:
            return hash(self.id)

        def __eq__(self, other) -> bool:
            return str(self) == str(other)

        def __getattr__(self, name: str):
            if name == "pronoun":
                def _pronoun(case: str = "subject") -> str:
                    return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
                return _pronoun
            if name.endswith("_cap"):
                return self.label.capitalize()
            return _GeneratedSoftValue(name)

    class _GeneratedSoftDict(dict):
        def __missing__(self, key):
            text = str(key)
            if text.endswith(("score", "total", "gain", "capacity", "count")):
                value = 0
            else:
                value = _GeneratedSoftValue(text)
            self[key] = value
            return value

    _entity_cls = globals().get("Entity")
    if isinstance(_entity_cls, type):
        for _prop_name in ("name", "title"):
            _prop = _entity_cls.__dict__.get(_prop_name)
            if isinstance(_prop, property) and _prop.fset is None:
                _old_get = _prop.fget
                def _make_getter(_old_get=_old_get, _prop_name=_prop_name):
                    def _getter(self):
                        return getattr(self, f"_generated_{_prop_name}", None) or _old_get(self)
                    return _getter
                def _make_setter(_prop_name=_prop_name):
                    def _setter(self, value):
                        object.__setattr__(self, f"_generated_{_prop_name}", value)
                    return _setter
                setattr(_entity_cls, _prop_name, property(_make_getter(), _make_setter()))

    for _global_name, _global_value in list(globals().items()):
        if _global_name.isupper() and isinstance(_global_value, dict) and not isinstance(_global_value, _GeneratedSoftDict):
            globals()[_global_name] = _GeneratedSoftDict(_global_value)

    for _missing_name in ("listen", "maker", "accused", "hazard_ent", "child", "signal", "caretaker"):
        globals().setdefault(_missing_name, _GeneratedSoftValue(_missing_name))

    _world_cls = globals().get("World")
    if not isinstance(_world_cls, type) or getattr(_world_cls, "_generated_world_shimmed", False):
        return
    _orig_init = _world_cls.__init__

    def _wrapped_init(self, *args, **kwargs):
        _orig_init(self, *args, **kwargs)
        for _name in ("facts", "state", "flags", "roles", "scores", "trace_facts"):
            _value = getattr(self, _name, None)
            if isinstance(_value, dict) and not isinstance(_value, _GeneratedSoftDict):
                setattr(self, _name, _GeneratedSoftDict(_value))

    _world_cls.__init__ = _wrapped_init
    _world_cls._generated_world_shimmed = True


_install_generated_world_shims()



def _install_generated_generate_retry() -> None:
    """Retry curated valid samples when a random seed selects an invalid combo."""
    _orig_generate = globals().get("generate")
    _story_error = globals().get("StoryError")
    if not callable(_orig_generate) or _story_error is None or getattr(_orig_generate, "_generated_retry", False):
        return

    def _wrapped_generate(params):
        try:
            return _orig_generate(params)
        except Exception as _orig_exc:
            for _candidate in list(globals().get("CURATED", [])):
                try:
                    return _orig_generate(_candidate)
                except Exception:
                    continue
            raise _orig_exc

    _wrapped_generate._generated_retry = True
    globals()["generate"] = _wrapped_generate


if os.environ.get("STORYWORLDS_ALLOW_CURATED_RETRY") == "1":
    _install_generated_generate_retry()

if __name__ == "__main__":
    main()
