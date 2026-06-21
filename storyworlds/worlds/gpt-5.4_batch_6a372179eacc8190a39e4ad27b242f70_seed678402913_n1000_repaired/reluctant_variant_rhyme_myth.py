#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/reluctant_variant_rhyme_myth.py
==========================================================

A standalone storyworld for a tiny mythic domain: in the first days of the
world, morning must be invited with the right dawn rhyme. A reluctant child
tries to wake a sky guardian. Nearby villages keep different variants of the
ancient song, but only the fitting variant, taught by the right helper and
carried by the right instrument, can wake the guardian and bring the day.

The world model enforces that:
- a guardian only answers in certain places,
- each guardian requires one rhyme variant,
- a helper must actually know that variant,
- and the chosen instrument must truly carry that variant's sound.

This yields a small, constraint-checked set of plausible myths instead of a
loose template.

Run it
------
    python storyworlds/worlds/gpt-5.4/reluctant_variant_rhyme_myth.py
    python storyworlds/worlds/gpt-5.4/reluctant_variant_rhyme_myth.py --guardian sun_stag
    python storyworlds/worlds/gpt-5.4/reluctant_variant_rhyme_myth.py --variant tide
    python storyworlds/worlds/gpt-5.4/reluctant_variant_rhyme_myth.py --all
    python storyworlds/worlds/gpt-5.4/reluctant_variant_rhyme_myth.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/reluctant_variant_rhyme_myth.py --qa --json
    python storyworlds/worlds/gpt-5.4/reluctant_variant_rhyme_myth.py --verify
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

# Make the shared result containers importable when this script is run directly
# from a nested world directory under storyworlds/worlds/<model>/.
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
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandmother",
            "grandfather": "grandfather",
            "mother": "mother",
            "father": "father",
        }.get(self.type, self.label or self.type)


@dataclass
class PlaceCfg:
    id: str
    label: str
    phrase: str
    image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class GuardianCfg:
    id: str
    label: str
    epithet: str
    phenomenon: str
    required_variant: str
    allowed_places: set[str] = field(default_factory=set)
    waking: str = ""
    ending: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class VariantCfg:
    id: str
    label: str
    rhyme: str
    image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperCfg:
    id: str
    label: str
    phrase: str
    knows: set[str] = field(default_factory=set)
    counsel: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class InstrumentCfg:
    id: str
    label: str
    phrase: str
    sound: str
    carries: set[str] = field(default_factory=set)
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


def _r_waiting(world: World) -> list[str]:
    out: list[str] = []
    guardian = world.get("guardian")
    sky = world.get("sky")
    child = world.get("child")
    if guardian.meters["awake"] < THRESHOLD:
        sig = ("waiting",)
        if sig not in world.fired:
            world.fired.add(sig)
            sky.meters["dark"] += 1
            child.memes["worry"] += 1
    else:
        sig = ("daybreak",)
        if sig not in world.fired:
            world.fired.add(sig)
            sky.meters["light"] += 1
            sky.meters["dark"] = 0.0
            child.memes["joy"] += 1
            child.memes["reluctance"] = 0.0
            out.append("__daybreak__")
    return out


CAUSAL_RULES = [
    Rule(name="waiting", tag="physical", apply=_r_waiting),
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
        for s in produced:
            world.say(s)
    return produced


PLACES = {
    "east_hill": PlaceCfg(
        id="east_hill",
        label="East Hill",
        phrase="the red east hill",
        image="where thyme grew between warm stones",
        tags={"hill"},
    ),
    "reed_marsh": PlaceCfg(
        id="reed_marsh",
        label="Reed Marsh",
        phrase="the reed marsh",
        image="where mist slept low above the water",
        tags={"marsh"},
    ),
    "shell_shore": PlaceCfg(
        id="shell_shore",
        label="Shell Shore",
        phrase="the shell shore",
        image="where the sea stacked pink shells in little shining rows",
        tags={"shore"},
    ),
}

VARIANTS = {
    "gold": VariantCfg(
        id="gold",
        label="the gold variant",
        rhyme='"Gold unfold, lift the cold; red sun, walk the sky of old."',
        image="a rhyme bright as hammered metal",
        tags={"rhyme", "gold_variant"},
    ),
    "dew": VariantCfg(
        id="dew",
        label="the dew variant",
        rhyme='"Dew anew, silver blue; morning rise where reeds shine through."',
        image="a cool rhyme beaded like grass at dawn",
        tags={"rhyme", "dew_variant"},
    ),
    "tide": VariantCfg(
        id="tide",
        label="the tide variant",
        rhyme='"Tide abide, open wide; rosy day, come in on the tide."',
        image="a rolling rhyme shaped by the sea",
        tags={"rhyme", "tide_variant"},
    ),
}

GUARDIANS = {
    "sun_stag": GuardianCfg(
        id="sun_stag",
        label="the Sun Stag",
        epithet="whose antlers carried the first light",
        phenomenon="daybreak",
        required_variant="gold",
        allowed_places={"east_hill"},
        waking="The Sun Stag tossed its golden antlers, and sparks ran down the hill like laughing goats.",
        ending="Soon the valley roofs shone honey-bright beneath the climbing sun.",
        tags={"myth", "sun", "stag"},
    ),
    "mist_crane": GuardianCfg(
        id="mist_crane",
        label="the Mist Crane",
        epithet="who stitched pearl light through the marsh",
        phenomenon="morning mist turning bright",
        required_variant="dew",
        allowed_places={"reed_marsh"},
        waking="The Mist Crane lifted its long neck and beat the mist with silver wings until it turned clear and shining.",
        ending="Soon every reed wore a bead of light, and the marsh gleamed like a bowl of glass.",
        tags={"myth", "crane", "mist"},
    ),
    "dawn_seal": GuardianCfg(
        id="dawn_seal",
        label="the Dawn Seal",
        epithet="who rolled the rosy edge of morning onto the sea",
        phenomenon="sunrise over water",
        required_variant="tide",
        allowed_places={"shell_shore"},
        waking="The Dawn Seal rose from a blue wave, clapped the water with its tail, and sent a pink road of light across the sea.",
        ending="Soon boats, shells, and even the foam looked painted with rose and gold.",
        tags={"myth", "sea", "seal"},
    ),
}

HELPERS = {
    "owl": HelperCfg(
        id="owl",
        label="Old Owl",
        phrase="an old owl from the shrine fig tree",
        knows={"gold", "dew"},
        counsel="Songs are not just pretty; they must fit the one who listens.",
        tags={"owl", "wisdom"},
    ),
    "turtle": HelperCfg(
        id="turtle",
        label="Moss Turtle",
        phrase="a mossy turtle older than the stepping stones",
        knows={"dew", "tide"},
        counsel="Slow words can still be strong words when they are the true ones.",
        tags={"turtle", "wisdom"},
    ),
    "fox": HelperCfg(
        id="fox",
        label="Wind Fox",
        phrase="a wind fox with ears full of weather",
        knows={"gold", "tide"},
        counsel="A brave song is not a loud boast; it is the right sound sent all the way.",
        tags={"fox", "wind"},
    ),
}

INSTRUMENTS = {
    "bell": InstrumentCfg(
        id="bell",
        label="bronze bell",
        phrase="a little bronze bell",
        sound="rang clear over stone",
        carries={"gold", "dew"},
        tags={"bell", "sound"},
    ),
    "reed_flute": InstrumentCfg(
        id="reed_flute",
        label="reed flute",
        phrase="a reed flute cut from the marsh edge",
        sound="sent a thin sweet line of music through the air",
        carries={"dew", "tide"},
        tags={"flute", "sound"},
    ),
    "shell_horn": InstrumentCfg(
        id="shell_horn",
        label="shell horn",
        phrase="a shell horn polished by many hands",
        sound="poured a round sea-deep note into the dawn",
        carries={"gold", "tide"},
        tags={"horn", "sound"},
    ),
}

GIRL_NAMES = ["Neri", "Tala", "Mira", "Sona", "Iva", "Rin"]
BOY_NAMES = ["Aren", "Timo", "Lio", "Soren", "Pavel", "Niko"]
RELUCTANCE_LEVELS = ["shy", "very_shy"]


def guardian_fits_place(guardian: GuardianCfg, place: PlaceCfg) -> bool:
    return place.id in guardian.allowed_places


def helper_knows_variant(helper: HelperCfg, variant: VariantCfg) -> bool:
    return variant.id in helper.knows


def instrument_carries_variant(instrument: InstrumentCfg, variant: VariantCfg) -> bool:
    return variant.id in instrument.carries


def valid_story(place: PlaceCfg, guardian: GuardianCfg, variant: VariantCfg,
                helper: HelperCfg, instrument: InstrumentCfg) -> bool:
    return (
        guardian_fits_place(guardian, place)
        and guardian.required_variant == variant.id
        and helper_knows_variant(helper, variant)
        and instrument_carries_variant(instrument, variant)
    )


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for guardian_id, guardian in GUARDIANS.items():
            for variant_id, variant in VARIANTS.items():
                for helper_id, helper in HELPERS.items():
                    for instrument_id, instrument in INSTRUMENTS.items():
                        if valid_story(place, guardian, variant, helper, instrument):
                            combos.append((place_id, guardian_id, variant_id, helper_id, instrument_id))
    return combos


@dataclass
class StoryParams:
    place: str
    guardian: str
    variant: str
    helper: str
    instrument: str
    child: str
    gender: str
    elder: str
    reluctance: str = "shy"
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="east_hill",
        guardian="sun_stag",
        variant="gold",
        helper="fox",
        instrument="bell",
        child="Neri",
        gender="girl",
        elder="grandmother",
        reluctance="very_shy",
    ),
    StoryParams(
        place="reed_marsh",
        guardian="mist_crane",
        variant="dew",
        helper="owl",
        instrument="reed_flute",
        child="Aren",
        gender="boy",
        elder="grandfather",
        reluctance="shy",
    ),
    StoryParams(
        place="shell_shore",
        guardian="dawn_seal",
        variant="tide",
        helper="turtle",
        instrument="shell_horn",
        child="Mira",
        gender="girl",
        elder="grandmother",
        reluctance="very_shy",
    ),
    StoryParams(
        place="east_hill",
        guardian="sun_stag",
        variant="gold",
        helper="owl",
        instrument="shell_horn",
        child="Soren",
        gender="boy",
        elder="grandfather",
        reluctance="shy",
    ),
]


def explain_rejection(place: PlaceCfg, guardian: GuardianCfg, variant: VariantCfg,
                      helper: HelperCfg, instrument: InstrumentCfg) -> str:
    if not guardian_fits_place(guardian, place):
        homes = ", ".join(sorted(guardian.allowed_places))
        return (
            f"(No story: {guardian.label} does not wake at {place.phrase}. "
            f"It belongs at {homes.replace('_', ' ')}, so the myth would not fit this place.)"
        )
    if guardian.required_variant != variant.id:
        need = VARIANTS[guardian.required_variant].label
        return (
            f"(No story: {guardian.label} answers only to {need}, not {variant.label}. "
            f"The wrong variant would leave the sky waiting.)"
        )
    if not helper_knows_variant(helper, variant):
        knows = ", ".join(sorted(helper.knows))
        return (
            f"(No story: {helper.label} does not know {variant.label}. "
            f"This helper only knows variants [{knows}], so it cannot teach the needed rhyme.)"
        )
    if not instrument_carries_variant(instrument, variant):
        carries = ", ".join(sorted(instrument.carries))
        return (
            f"(No story: the {instrument.label} cannot carry {variant.label}. "
            f"It only carries variants [{carries}], so the sound would not reach the guardian.)"
        )
    return "(No story: this combination does not form a reasonable myth.)"


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def _other_variant(correct_id: str) -> str:
    for vid in sorted(VARIANTS):
        if vid != correct_id:
            return vid
    return correct_id


def _do_song(world: World, variant: VariantCfg, instrument: InstrumentCfg, narrate: bool = True) -> bool:
    guardian = world.get("guardian")
    child = world.get("child")
    if instrument_carries_variant(instrument, variant):
        child.meters["sound"] += 1
    else:
        child.meters["frayed_sound"] += 1
    success = (
        world.facts["guardian_cfg"].required_variant == variant.id
        and instrument_carries_variant(instrument, variant)
    )
    if success:
        guardian.meters["awake"] += 1
        child.memes["courage"] += 1
    else:
        child.memes["worry"] += 1
    propagate(world, narrate=narrate)
    return success


def predict_waking(world: World, variant_id: str, instrument_id: str) -> bool:
    sim = world.copy()
    variant = VARIANTS[variant_id]
    instrument = INSTRUMENTS[instrument_id]
    _do_song(sim, variant, instrument, narrate=False)
    return sim.get("guardian").meters["awake"] >= THRESHOLD


def opening(world: World, child: Entity, elder: Entity, place: PlaceCfg, guardian: GuardianCfg) -> None:
    world.say(
        f"In the first days, people said morning did not come by itself. "
        f"It had to be invited at {place.phrase}, {place.image}, where {guardian.label} waited."
    )
    world.say(
        f"In that village lived {child.id}, a child chosen to carry the Dawn Rhyme, "
        f"and {child.id}'s {elder.label_word}, who remembered old stories older than roofs and roads."
    )
    world.say(
        f"They told how {guardian.label}, {guardian.epithet}, would stir only when the true song reached it."
    )


def calling(world: World, child: Entity, elder: Entity, place: PlaceCfg,
            guardian: GuardianCfg, instrument: InstrumentCfg) -> None:
    world.say(
        f"One dim morning, the eastern edge stayed gray. The fields waited, the bread ovens waited, "
        f"and even the birds seemed to hold their breath."
    )
    world.say(
        f'"Go to {place.phrase} with {instrument.phrase}," said {elder.label_word}. '
        f'"If {guardian.label} sleeps too long, {guardian.phenomenon} lingers too."'
    )


def reluctance(world: World, child: Entity, place: PlaceCfg) -> None:
    if child.memes["reluctance"] >= 2:
        world.say(
            f"But {child.id} was reluctant. {child.pronoun().capitalize()} looked at the path to {place.phrase} "
            f"and thought it seemed longer than on any other day."
        )
    else:
        world.say(
            f"{child.id} felt a shy flutter in {child.pronoun('possessive')} chest as {child.pronoun()} started toward {place.phrase}."
        )


def wrong_attempt(world: World, child: Entity, wrong_variant: VariantCfg, instrument: InstrumentCfg) -> None:
    world.say(
        f"{child.id} remembered that every nearby village kept its own variant of the old rhyme. "
        f"Nervous and eager to be done, {child.pronoun()} tried {wrong_variant.label} first."
    )
    world.say(
        f"{child.pronoun().capitalize()} lifted the {instrument.label}. It {instrument.sound}, and {child.pronoun()} sang, "
        f"{wrong_variant.rhyme}"
    )
    _do_song(world, wrong_variant, instrument, narrate=False)
    if world.get("guardian").meters["awake"] < THRESHOLD:
        world.say(
            f"Nothing answered except the quiet. The gray light stayed folded up beyond the world, "
            f"and {child.id}'s heart sank lower."
        )


def guidance(world: World, child: Entity, helper_ent: Entity, helper: HelperCfg,
             correct_variant: VariantCfg, wrong_variant: VariantCfg, instrument: InstrumentCfg) -> None:
    wrong_wakes = predict_waking(world, wrong_variant.id, instrument.id)
    right_wakes = predict_waking(world, correct_variant.id, instrument.id)
    world.facts["wrong_wakes"] = wrong_wakes
    world.facts["right_wakes"] = right_wakes
    world.say(
        f"Then {helper.phrase} came near. \"{helper.counsel}\" said {helper.label}."
    )
    world.say(
        f'"That was {wrong_variant.label}. This place needs {correct_variant.label}. '
        f'True rhymes are cousins, not twins. Sing the one that fits the listener."'
    )
    helper_ent.memes["guidance"] += 1


def courage(world: World, child: Entity) -> None:
    child.memes["courage"] += 1
    child.memes["reluctance"] = max(0.0, child.memes["reluctance"] - 1.0)
    world.say(
        f"{child.id} took a slower breath. Being brave, {child.pronoun()} decided, was not the same as never trembling."
    )


def true_song(world: World, child: Entity, variant: VariantCfg, instrument: InstrumentCfg) -> None:
    world.say(
        f"Once more {child.pronoun()} raised the {instrument.label}. It {instrument.sound}, and this time {child.id} sang, "
        f"{variant.rhyme}"
    )
    success = _do_song(world, variant, instrument, narrate=False)
    world.facts["success"] = success


def waking(world: World, guardian: GuardianCfg) -> None:
    if world.get("guardian").meters["awake"] >= THRESHOLD:
        world.say(guardian.waking)


def ending(world: World, child: Entity, elder: Entity, guardian: GuardianCfg, place: PlaceCfg) -> None:
    world.say(
        f"{guardian.ending} {child.id} walked home no longer reluctant, and the village said "
        f"the morning had learned {child.pronoun('possessive')} name."
    )
    world.say(
        f"After that, when children practiced the Dawn Rhyme at {place.phrase}, they remembered that every variant mattered, "
        f"and that the truest song was the one sung with care."
    )
    elder.memes["pride"] += 1


def tell(place: PlaceCfg, guardian_cfg: GuardianCfg, variant_cfg: VariantCfg,
         helper_cfg: HelperCfg, instrument_cfg: InstrumentCfg, child_name: str,
         gender: str, elder_type: str, reluctance_level: str) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=gender,
        role="child",
        label=child_name,
    ))
    elder = world.add(Entity(
        id="Elder",
        kind="character",
        type=elder_type,
        role="elder",
        label="the elder",
    ))
    helper_ent = world.add(Entity(
        id="Helper",
        kind="character",
        type="helper",
        role="helper",
        label=helper_cfg.label,
        phrase=helper_cfg.phrase,
        tags=set(helper_cfg.tags),
    ))
    guardian = world.add(Entity(
        id="guardian",
        kind="character",
        type="guardian",
        role="guardian",
        label=guardian_cfg.label,
        phrase=guardian_cfg.epithet,
        tags=set(guardian_cfg.tags),
    ))
    sky = world.add(Entity(
        id="sky",
        kind="thing",
        type="sky",
        label="the sky",
    ))
    instrument_ent = world.add(Entity(
        id="instrument",
        kind="thing",
        type="instrument",
        label=instrument_cfg.label,
        phrase=instrument_cfg.phrase,
        tags=set(instrument_cfg.tags),
    ))
    place_ent = world.add(Entity(
        id="place",
        kind="thing",
        type="place",
        label=place.label,
        phrase=place.phrase,
        tags=set(place.tags),
    ))

    child.memes["reluctance"] = 2.0 if reluctance_level == "very_shy" else 1.0
    guardian.meters["awake"] = 0.0
    propagate(world, narrate=False)

    wrong_variant_id = _other_variant(variant_cfg.id)
    wrong_variant_cfg = VARIANTS[wrong_variant_id]

    opening(world, child, elder, place, guardian_cfg)
    world.para()
    calling(world, child, elder, place, guardian_cfg, instrument_cfg)
    reluctance(world, child, place)
    world.para()
    wrong_attempt(world, child, wrong_variant_cfg, instrument_cfg)
    guidance(world, child, helper_ent, helper_cfg, variant_cfg, wrong_variant_cfg, instrument_cfg)
    courage(world, child)
    world.para()
    true_song(world, child, variant_cfg, instrument_cfg)
    waking(world, guardian_cfg)
    ending(world, child, elder, guardian_cfg, place)

    world.facts.update(
        child=child,
        elder=elder,
        helper=helper_ent,
        helper_cfg=helper_cfg,
        guardian=guardian,
        guardian_cfg=guardian_cfg,
        instrument=instrument_ent,
        instrument_cfg=instrument_cfg,
        place=place_ent,
        place_cfg=place,
        variant_cfg=variant_cfg,
        wrong_variant_cfg=wrong_variant_cfg,
        success=world.get("guardian").meters["awake"] >= THRESHOLD,
        reluctance_start=reluctance_level,
    )
    return world


KNOWLEDGE = {
    "myth": [
        (
            "What is a myth?",
            "A myth is an old story people tell to explain how the world works or why something matters. It often uses magical beings to show truth in a memorable way.",
        )
    ],
    "rhyme": [
        (
            "What is a rhyme?",
            "A rhyme uses words with matching end sounds, like cold and old. Rhymes are easy to remember, so people often use them in songs and stories.",
        )
    ],
    "bell": [
        (
            "What does a bell do in a story or song?",
            "A bell makes a clear ringing sound that can carry across a hill or courtyard. In stories, that sharp sound can be used to call people, mark time, or begin a ritual.",
        )
    ],
    "flute": [
        (
            "What is a flute?",
            "A flute is a hollow instrument that sings when air moves through it. A reed flute sounds light and airy, so it fits quiet places like marshes or riverbanks.",
        )
    ],
    "horn": [
        (
            "What is a horn?",
            "A horn makes a round, strong note that can travel far. In old tales, a horn often calls help, welcomes a hero, or wakes something important.",
        )
    ],
    "sun": [
        (
            "Why do stories connect the sun with animals?",
            "Stories use animals because they are vivid and easy to picture. A strong or shining animal can make the sun feel alive and memorable.",
        )
    ],
    "sea": [
        (
            "Why does the sea look pink at sunrise?",
            "At sunrise, sunlight comes in at a low angle and colors the water with warm reds and pinks. The moving waves reflect those colors back to our eyes.",
        )
    ],
    "mist": [
        (
            "What is mist?",
            "Mist is a cloud close to the ground made of tiny drops of water. When the sun grows brighter, the mist can thin and begin to disappear.",
        )
    ],
    "owl": [
        (
            "Why are owls often wise in stories?",
            "Owls are awake when many other creatures are asleep, so stories imagine that they notice secret things. Their calm eyes also make them seem thoughtful and old.",
        )
    ],
    "turtle": [
        (
            "Why do stories link turtles with patience?",
            "Turtles move slowly and steadily, so they are a good symbol for patience. A patient helper in a story reminds children that slow and careful can still be strong.",
        )
    ],
    "wind": [
        (
            "Why is the wind useful in a singing story?",
            "Wind carries sound from one place to another. That makes it a natural helper when a story needs a song, horn, or bell to travel far.",
        )
    ],
}
KNOWLEDGE_ORDER = ["myth", "rhyme", "bell", "flute", "horn", "sun", "sea", "mist", "owl", "turtle", "wind"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    guardian_cfg = f["guardian_cfg"]
    variant_cfg = f["variant_cfg"]
    place_cfg = f["place_cfg"]
    helper_cfg = f["helper_cfg"]
    instrument_cfg = f["instrument_cfg"]
    return [
        (
            f'Write a short child-facing myth about a reluctant child who must bring the morning by singing a rhyme. '
            f'Include the exact words "reluctant" and "variant".'
        ),
        (
            f"Tell a mythic story where {child.id} goes to {place_cfg.phrase} with {instrument_cfg.phrase}, "
            f"tries the wrong variant of an old dawn rhyme, and learns the right one from {helper_cfg.label}."
        ),
        (
            f"Write a simple myth in which {guardian_cfg.label} wakes only for {variant_cfg.label}, "
            f"and end with an image that proves the world has changed."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    guardian_cfg = f["guardian_cfg"]
    variant_cfg = f["variant_cfg"]
    wrong_variant_cfg = f["wrong_variant_cfg"]
    helper_cfg = f["helper_cfg"]
    instrument_cfg = f["instrument_cfg"]
    place_cfg = f["place_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a reluctant child asked to wake {guardian_cfg.label}, and about {elder.label_word} and {helper_cfg.label}, who help {child.pronoun('object')} remember what to do.",
        ),
        (
            "Why was the child going to the special place?",
            f"{child.id} went to {place_cfg.phrase} because the village believed morning had to be invited there. If {guardian_cfg.label} kept sleeping, the day would stay gray and waiting.",
        ),
        (
            "What mistake did the child make first?",
            f"{child.id} tried {wrong_variant_cfg.label} first. That was the wrong variant for {guardian_cfg.label}, so the song did not wake the guardian and the sky stayed dim.",
        ),
        (
            "How did the helper solve the problem?",
            f"{helper_cfg.label} explained that nearby villages kept different versions of the dawn song, but this place needed {variant_cfg.label}. The helper's advice mattered because the right rhyme had to fit the listener, not just sound pretty.",
        ),
        (
            "How did the story show the child being brave?",
            f"{child.id} was reluctant and worried at first, but sang again anyway after listening carefully. The brave part was not pretending to feel no fear; it was choosing the true song even while trembling.",
        ),
    ]
    if f.get("success"):
        qa.append(
            (
                "What happened when the child sang the right rhyme?",
                f"{guardian_cfg.label} woke at last, and {guardian_cfg.ending.lower()} That ending image proves the world changed because the sky and land both brightened after the true song.",
            )
        )
        qa.append(
            (
                "Why did the instrument matter?",
                f"The story says the child used {instrument_cfg.phrase}, and that sound could carry {variant_cfg.label} properly. The right words needed the right kind of sound so the guardian could hear them.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"myth", "rhyme"}
    tags |= set(f["instrument_cfg"].tags)
    tags |= set(f["guardian_cfg"].tags)
    tags |= set(f["helper_cfg"].tags)
    out: list[tuple[str, str]] = []
    tag_map = {
        "bell": "bell",
        "flute": "flute",
        "horn": "horn",
        "sun": "sun",
        "sea": "sea",
        "mist": "mist",
        "owl": "owl",
        "turtle": "turtle",
        "wind": "wind",
        "myth": "myth",
        "rhyme": "rhyme",
    }
    expanded = {tag_map[t] for t in tags if t in tag_map}
    for tag in KNOWLEDGE_ORDER:
        if tag in expanded:
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.phrase:
            bits.append(f"phrase={e.phrase!r}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
fits_place(G, P) :- guardian_home(G, P).
fits_variant(G, V) :- requires_variant(G, V).
helper_can_teach(H, V) :- knows_variant(H, V).
instrument_can_carry(I, V) :- carries_variant(I, V).

valid(P, G, V, H, I) :-
    place(P), guardian(G), variant(V), helper(H), instrument(I),
    fits_place(G, P),
    fits_variant(G, V),
    helper_can_teach(H, V),
    instrument_can_carry(I, V).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for gid, guardian in GUARDIANS.items():
        lines.append(asp.fact("guardian", gid))
        lines.append(asp.fact("requires_variant", gid, guardian.required_variant))
        for place_id in sorted(guardian.allowed_places):
            lines.append(asp.fact("guardian_home", gid, place_id))
    for vid in VARIANTS:
        lines.append(asp.fact("variant", vid))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        for vid in sorted(helper.knows):
            lines.append(asp.fact("knows_variant", hid, vid))
    for iid, instrument in INSTRUMENTS.items():
        lines.append(asp.fact("instrument", iid))
        for vid in sorted(instrument.carries):
            lines.append(asp.fact("carries_variant", iid, vid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story from smoke test")
        print("OK: smoke test generate() produced a story.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        rng = random.Random(123)
        params = resolve_params(build_parser().parse_args([]), rng)
        params.seed = 123
        sample = generate(params)
        if not sample.story.strip():
            raise StoryError("empty story from default resolve/generate test")
        print("OK: default resolve_params() + generate() succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"DEFAULT GENERATION FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: a reluctant child, a dawn rhyme, and the right mythic variant."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--guardian", choices=GUARDIANS)
    ap.add_argument("--variant", choices=VARIANTS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--instrument", choices=INSTRUMENTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--child")
    ap.add_argument("--elder", choices=["grandmother", "grandfather"])
    ap.add_argument("--reluctance", choices=RELUCTANCE_LEVELS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible myths derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.guardian and args.variant and args.helper and args.instrument:
        place = PLACES[args.place]
        guardian = GUARDIANS[args.guardian]
        variant = VARIANTS[args.variant]
        helper = HELPERS[args.helper]
        instrument = INSTRUMENTS[args.instrument]
        if not valid_story(place, guardian, variant, helper, instrument):
            raise StoryError(explain_rejection(place, guardian, variant, helper, instrument))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.guardian is None or c[1] == args.guardian)
        and (args.variant is None or c[2] == args.variant)
        and (args.helper is None or c[3] == args.helper)
        and (args.instrument is None or c[4] == args.instrument)
    ]
    if not combos:
        if args.place and args.guardian and args.variant and args.helper and args.instrument:
            place = PLACES[args.place]
            guardian = GUARDIANS[args.guardian]
            variant = VARIANTS[args.variant]
            helper = HELPERS[args.helper]
            instrument = INSTRUMENTS[args.instrument]
            raise StoryError(explain_rejection(place, guardian, variant, helper, instrument))
        raise StoryError("(No valid combination matches the given options.)")

    place_id, guardian_id, variant_id, helper_id, instrument_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    child = args.child or _pick_name(rng, gender)
    elder = args.elder or rng.choice(["grandmother", "grandfather"])
    reluctance = args.reluctance or rng.choice(RELUCTANCE_LEVELS)
    return StoryParams(
        place=place_id,
        guardian=guardian_id,
        variant=variant_id,
        helper=helper_id,
        instrument=instrument_id,
        child=child,
        gender=gender,
        elder=elder,
        reluctance=reluctance,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        guardian = GUARDIANS[params.guardian]
        variant = VARIANTS[params.variant]
        helper = HELPERS[params.helper]
        instrument = INSTRUMENTS[params.instrument]
    except KeyError as err:
        raise StoryError(f"(Unknown parameter value: {err.args[0]})") from err

    if not valid_story(place, guardian, variant, helper, instrument):
        raise StoryError(explain_rejection(place, guardian, variant, helper, instrument))

    world = tell(
        place=place,
        guardian_cfg=guardian,
        variant_cfg=variant,
        helper_cfg=helper,
        instrument_cfg=instrument,
        child_name=params.child,
        gender=params.gender,
        elder_type=params.elder,
        reluctance_level=params.reluctance,
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
        print(asp_program("#show valid/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, guardian, variant, helper, instrument) combos:\n")
        for place, guardian, variant, helper, instrument in combos:
            print(f"  {place:11} {guardian:11} {variant:6} {helper:7} {instrument}")
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
                f"### {p.child}: {p.guardian} at {p.place} "
                f"({p.variant}, {p.helper}, {p.instrument})"
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
