#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/scuttle_sup_disc_curiosity_dialogue_ghost_story.py
=============================================================================

A tiny, child-facing ghost-story world about a spooky noise, a rolling disc,
and the brave, curious choice to ask questions instead of letting fear invent a
monster.

The domain is gentle on purpose: every valid story begins with a ghostly-seeming
sound in an old room, turns on dialogue and curiosity, and resolves with a
harmless real cause. The central reasonableness constraint is simple:

    a story is only valid when the chosen little creature plausibly belongs in
    the chosen place, the place plausibly contains the chosen disc-like object,
    and the creature is strong enough to bump that disc and make the spooky sound

That gate is implemented twice:
- directly in Python with `plausible_noise()` / `valid_combos()`
- declaratively in the inline ASP twin below

The generated prose always includes the seed words:
- "scuttle"
- "sup"
- "disc"

Run it
------
    python storyworlds/worlds/gpt-5.4/scuttle_sup_disc_curiosity_dialogue_ghost_story.py
    python storyworlds/worlds/gpt-5.4/scuttle_sup_disc_curiosity_dialogue_ghost_story.py --all
    python storyworlds/worlds/gpt-5.4/scuttle_sup_disc_curiosity_dialogue_ghost_story.py --place attic --creature mouse --disc tin_disc
    python storyworlds/worlds/gpt-5.4/scuttle_sup_disc_curiosity_dialogue_ghost_story.py --disc record_disc --creature mouse
    python storyworlds/worlds/gpt-5.4/scuttle_sup_disc_curiosity_dialogue_ghost_story.py --qa --json
    python storyworlds/worlds/gpt-5.4/scuttle_sup_disc_curiosity_dialogue_ghost_story.py --verify
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
# reach storyworlds/, where results.py and asp.py live.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0
CURIOUS_TRAITS = {"curious", "brave", "gentle", "thoughtful"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"         # "character" | "thing"
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
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    opening: str
    eerie_detail: str
    supports_creatures: set[str] = field(default_factory=set)
    supports_discs: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class CreatureCfg:
    id: str
    label: str
    phrase: str
    article: str
    can_nudge: int
    homes: set[str] = field(default_factory=set)
    reveal_line: str = ""
    trail: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class DiscCfg:
    id: str
    label: str
    phrase: str
    weight: int
    shine: str
    sound: str
    place_hint: str
    tags: set[str] = field(default_factory=set)


@dataclass
class LightCfg:
    id: str
    phrase: str
    glow: str
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
        return self.entities[eid]

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"lead", "companion"}]

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


def _r_eerie_noise(world: World) -> list[str]:
    disc = world.entities.get("disc")
    creature = world.entities.get("creature")
    if not disc or not creature:
        return []
    if disc.meters["rolling"] < THRESHOLD:
        return []
    sig = ("eerie_noise", disc.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    room = world.entities.get("room")
    if room is not None:
        room.meters["eerie"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    return ["__eerie__"]


def _r_curiosity_steadies(world: World) -> list[str]:
    lead = world.entities.get("lead")
    if not lead:
        return []
    if lead.memes["questioned_dark"] < THRESHOLD:
        return []
    sig = ("curiosity_steadies", lead.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    lead.memes["courage"] += 1
    lead.memes["curiosity"] += 1
    comp = world.entities.get("companion")
    if comp is not None:
        comp.memes["courage"] += 0.5
    return ["__steady__"]


def _r_reveal_relief(world: World) -> list[str]:
    creature = world.entities.get("creature")
    if not creature or creature.meters["spotted"] < THRESHOLD:
        return []
    sig = ("reveal_relief", creature.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["fear"] = 0.0
        kid.memes["wonder"] += 1
        kid.memes["relief"] += 1
    room = world.entities.get("room")
    if room is not None:
        room.meters["eerie"] = 0.0
        room.meters["cozy"] += 1
    return ["__relief__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="eerie_noise", tag="physical", apply=_r_eerie_noise),
    Rule(name="curiosity_steadies", tag="emotional", apply=_r_curiosity_steadies),
    Rule(name="reveal_relief", tag="emotional", apply=_r_reveal_relief),
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
    "attic": Place(
        id="attic",
        label="the attic",
        opening="At bedtime, the old attic room above the stairs felt bigger than it did in the day.",
        eerie_detail="Moonlight striped the trunks and rafters, and every beam seemed to be keeping a secret.",
        supports_creatures={"mouse"},
        supports_discs={"tin_disc", "brass_disc"},
        tags={"attic", "night"},
    ),
    "shed": Place(
        id="shed",
        label="the garden shed",
        opening="Near the back garden stood a little shed that always looked mysterious after sunset.",
        eerie_detail="Its wooden walls smelled of rain and old paint, and the corners held deep pockets of shadow.",
        supports_creatures={"mouse", "kitten"},
        supports_discs={"tin_disc", "flying_disc"},
        tags={"shed", "night"},
    ),
    "music_room": Place(
        id="music_room",
        label="the music room",
        opening="At bedtime, the music room beside the hall was quiet in the special way only old houses can be quiet.",
        eerie_detail="The piano slept with its lid shut, and the shelves of songs glimmered softly in the dark.",
        supports_creatures={"mouse", "kitten"},
        supports_discs={"record_disc", "brass_disc"},
        tags={"music_room", "night", "music"},
    ),
}

CREATURES = {
    "mouse": CreatureCfg(
        id="mouse",
        label="mouse",
        phrase="a whiskery little mouse",
        article="a",
        can_nudge=1,
        homes={"attic", "shed", "music_room"},
        reveal_line="There was no ghost at all, only a tiny mouse with bright bead eyes.",
        trail="A few dry crumbs lay near the wall, showing where the little visitor had been.",
        tags={"mouse", "small_animal"},
    ),
    "kitten": CreatureCfg(
        id="kitten",
        label="kitten",
        phrase="a striped kitten from next door",
        article="a",
        can_nudge=2,
        homes={"shed", "music_room"},
        reveal_line="There was no ghost at all, only a small striped kitten with a twitching tail.",
        trail="The kitten batted at the edge again, proud of the noise it had made.",
        tags={"kitten", "pet"},
    ),
}

DISCS = {
    "tin_disc": DiscCfg(
        id="tin_disc",
        label="tin disc lid",
        phrase="a round tin disc lid from an old biscuit tin",
        weight=1,
        shine="A pale tin disc on a shelf caught the moon and flashed once.",
        sound="It tipped, spun, and gave the floor a bright clink-clink.",
        place_hint="on top of a dusty biscuit tin",
        tags={"disc", "tin"},
    ),
    "brass_disc": DiscCfg(
        id="brass_disc",
        label="brass disc",
        phrase="a flat brass disc from an old clock",
        weight=1,
        shine="A brass disc near the wall flashed like a sleepy gold eye.",
        sound="It wobbled in a circle and rang with a small ting.",
        place_hint="beside a box of old clock parts",
        tags={"disc", "brass"},
    ),
    "flying_disc": DiscCfg(
        id="flying_disc",
        label="flying disc",
        phrase="a scuffed red flying disc",
        weight=1,
        shine="A red flying disc leaned against a toolbox and shone in the crack under the door.",
        sound="It skidded sideways with a papery scrape.",
        place_hint="beside a toolbox",
        tags={"disc", "toy"},
    ),
    "record_disc": DiscCfg(
        id="record_disc",
        label="record disc",
        phrase="a black record disc in a paper sleeve",
        weight=2,
        shine="A record disc half out of its sleeve glimmered on the low cabinet.",
        sound="It slipped, turned once, and tapped the wood with a hollow tok.",
        place_hint="half out of its sleeve",
        tags={"disc", "record", "music"},
    ),
}

LIGHTS = {
    "flashlight": LightCfg(
        id="flashlight",
        phrase="a flashlight",
        glow="clicked on with a white circle of light",
        tags={"flashlight"},
    ),
    "lantern": LightCfg(
        id="lantern",
        phrase="a little lantern",
        glow="glowed warm and honey-yellow",
        tags={"lantern"},
    ),
    "nightlight": LightCfg(
        id="nightlight",
        phrase="a blue night-light",
        glow="shone softly like a tiny moon",
        tags={"nightlight"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["curious", "gentle", "thoughtful", "brave", "careful", "shy"]
HELPERS = ["mother", "father", "grandmother", "grandfather"]


def plausible_noise(place: Place, creature: CreatureCfg, disc: DiscCfg) -> bool:
    return (
        creature.id in place.supports_creatures
        and disc.id in place.supports_discs
        and place.id in creature.homes
        and creature.can_nudge >= disc.weight
    )


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for creature_id, creature in CREATURES.items():
            for disc_id, disc in DISCS.items():
                if plausible_noise(place, creature, disc):
                    combos.append((place_id, creature_id, disc_id))
    return combos


@dataclass
class StoryParams:
    place: str
    creature: str
    disc: str
    light: str
    child_name: str
    child_gender: str
    companion_name: str
    companion_gender: str
    helper: str
    trait: str
    bond: int = 5
    seed: Optional[int] = None


def helper_title(helper_type: str) -> str:
    return {
        "mother": "Mom",
        "father": "Dad",
        "grandmother": "Grandma",
        "grandfather": "Grandpa",
    }[helper_type]


def pair_noun(a: Entity, b: Entity) -> str:
    if a.type == "girl" and b.type == "girl":
        return "two children"
    if a.type == "boy" and b.type == "boy":
        return "two children"
    return "two children"


def would_speak_first(trait: str, bond: int) -> bool:
    return trait in CURIOUS_TRAITS or bond >= 7


def predict_calm(world: World, trait: str, bond: int) -> dict:
    sim = world.copy()
    lead = sim.get("lead")
    lead.memes["questioned_dark"] += 1
    propagate(sim, narrate=False)
    return {
        "speak_first": would_speak_first(trait, bond),
        "courage": lead.memes["courage"],
    }


def introduce(world: World, place: Place, lead: Entity, companion: Entity) -> None:
    for kid in (lead, companion):
        kid.memes["cozy"] += 1
    world.say(
        f"{place.opening} {place.eerie_detail} "
        f"{lead.id} and {companion.id} had promised each other a brave little ghost story before sleep."
    )


def settle(world: World, place: Place, lead: Entity, companion: Entity) -> None:
    world.say(
        f"They sat near the doorway of {place.label}, sharing one blanket and listening to the house breathe."
    )
    world.say(
        f"{lead.id} liked mysteries, and {companion.id} liked being close enough to whisper about them."
    )


def start_noise(world: World, place: Place, creature: CreatureCfg, disc: DiscCfg) -> None:
    room = world.get("room")
    disc_ent = world.get("disc")
    creature_ent = world.get("creature")
    room.attrs["place"] = place.id
    creature_ent.meters["moving"] += 1
    disc_ent.meters["rolling"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then something gave a quick scuttle in the dark. {disc.shine} {disc.sound}"
    )


def first_dialogue(world: World, lead: Entity, companion: Entity, helper: Entity) -> None:
    world.say(f'"Did you hear that?" {companion.id} whispered.')
    world.say(
        f'"I did," said {lead.id}, though {lead.pronoun("possessive")} fingers squeezed the blanket.'
    )
    world.say(
        f'"If that is a ghost," {companion.id} breathed, "what do people even say first? Hello? Or... sup?"'
    )
    world.say(
        f'{helper_title(helper.type)} was downstairs, far enough away that the room still felt like it belonged to the dark.'
    )


def ask_into_dark(world: World, lead: Entity, companion: Entity, helper: Entity) -> None:
    lead.memes["questioned_dark"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{lead.id} swallowed and let curiosity stand up taller than fear. '
        f'"Hello?" {lead.pronoun().capitalize()} called softly. "If someone is there, we are listening."'
    )
    world.say(
        f'{companion.id} edged closer and added, "And if you are a ghost... uh, sup?"'
    )
    world.say(
        "Nothing answered with words, but the sound came again, smaller this time, and from much lower than a ghost ought to be."
    )
    world.facts["approach"] = "asked"


def call_helper(world: World, lead: Entity, companion: Entity, helper: Entity) -> None:
    companion.memes["fear"] += 1
    world.say(
        f'{companion.id} tugged at {lead.id}\'s sleeve. "Let\'s get {helper_title(helper.type)}," {companion.pronoun()} said.'
    )
    world.say(
        f'{lead.id} still wanted to know the answer, so {lead.pronoun()} called, "{helper_title(helper.type)}! There is a ghosty sound in here!"'
    )
    world.facts["approach"] = "called"


def helper_arrives(world: World, helper: Entity, light: LightCfg) -> None:
    helper.memes["calm"] += 1
    world.say(
        f"In a moment, {helper_title(helper.type)} came with {light.phrase} that {light.glow}."
    )
    world.say(
        f'"Let us look before we decide what it is," {helper.pronoun()} said in a calm voice.'
    )


def reveal(world: World, creature: CreatureCfg, disc: DiscCfg, helper: Entity) -> None:
    creature_ent = world.get("creature")
    disc_ent = world.get("disc")
    creature_ent.meters["spotted"] += 1
    disc_ent.meters["still"] += 1
    propagate(world, narrate=False)
    world.say(
        f"The light slid under the shelf and found the truth. {creature.reveal_line}"
    )
    world.say(
        f"It had bumped {disc.phrase} {disc.place_hint}, and that was the whole spooky sound."
    )
    world.say(creature.trail)
    world.facts["revealed_not_ghost"] = True


def explain(world: World, helper: Entity, creature: CreatureCfg, disc: DiscCfg, lead: Entity) -> None:
    world.say(
        f'"Not every strange sound is a scary one," {helper_title(helper.type)} said. '
        f'"Sometimes a small {creature.label} and a loose {disc.label} can make a room sound enormous."'
    )
    world.say(
        f'{lead.id} let out the breath {lead.pronoun()} had been holding. '
        f'"So the dark was busy," {lead.pronoun()} said, "not haunted."'
    )


def closing(world: World, place: Place, helper: Entity, lead: Entity, companion: Entity, disc: DiscCfg) -> None:
    for kid in (lead, companion):
        kid.memes["joy"] += 1
    world.say(
        f'{helper_title(helper.type)} set the {disc.label} flat on a folded cloth so it could not rattle again.'
    )
    world.say(
        f'Soon {place.label} looked different. It was still shadowy, but now it felt like a place with corners and shelves instead of secrets and ghosts.'
    )
    world.say(
        f'{companion.id} gave a tiny laugh. "{helper_title(helper.type)}, next time we hear a sound, can we ask a question first?"'
    )
    world.say(
        f'"Yes," said {helper_title(helper.type)}. "Questions turn many big shadows small."'
    )
    world.say(
        f'When they finally went to bed, {lead.id} and {companion.id} were still whispering, but now they were whispering about the brave little mouse-or-kitten mystery they had solved.'
    )


def tell(
    place: Place,
    creature: CreatureCfg,
    disc: DiscCfg,
    light: LightCfg,
    child_name: str,
    child_gender: str,
    companion_name: str,
    companion_gender: str,
    helper_type: str,
    trait: str,
    bond: int,
) -> World:
    world = World()
    lead = world.add(Entity(
        id="lead",
        kind="character",
        type=child_gender,
        label=child_name,
        phrase=child_name,
        role="lead",
        traits=[trait],
        attrs={"name": child_name},
    ))
    companion = world.add(Entity(
        id="companion",
        kind="character",
        type=companion_gender,
        label=companion_name,
        phrase=companion_name,
        role="companion",
        attrs={"name": companion_name, "bond": bond},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_type,
        label=helper_title(helper_type),
        phrase=helper_title(helper_type),
        role="helper",
    ))
    room = world.add(Entity(
        id="room",
        type="room",
        label=place.label,
        phrase=place.label,
        tags=set(place.tags),
    ))
    creature_ent = world.add(Entity(
        id="creature",
        type="creature",
        label=creature.label,
        phrase=creature.phrase,
        tags=set(creature.tags),
    ))
    disc_ent = world.add(Entity(
        id="disc",
        type="disc",
        label=disc.label,
        phrase=disc.phrase,
        tags=set(disc.tags),
    ))

    lead.memes["curiosity"] = 1.0 if trait in CURIOUS_TRAITS else 0.2
    lead.memes["fear"] = 0.0
    companion.memes["fear"] = 0.0
    companion.memes["trust"] = float(bond)

    introduce(world, place, lead, companion)
    settle(world, place, lead, companion)

    world.para()
    start_noise(world, place, creature, disc)
    first_dialogue(world, lead, companion, helper)

    prediction = predict_calm(world, trait, bond)
    world.facts["predicted_speak_first"] = prediction["speak_first"]
    world.facts["predicted_courage"] = prediction["courage"]

    world.para()
    if would_speak_first(trait, bond):
        ask_into_dark(world, lead, companion, helper)
    else:
        call_helper(world, lead, companion, helper)

    helper_arrives(world, helper, light)
    reveal(world, creature, disc, helper)
    explain(world, helper, creature, disc, lead)

    world.para()
    closing(world, place, helper, lead, companion, disc)

    world.facts.update(
        place=place,
        creature_cfg=creature,
        disc_cfg=disc,
        light=light,
        lead=lead,
        companion=companion,
        helper=helper,
        child_name=child_name,
        companion_name=companion_name,
        trait=trait,
        bond=bond,
        outcome=world.facts.get("approach", "asked"),
        sound_made=disc_ent.meters["rolling"] >= THRESHOLD,
        revealed=creature_ent.meters["spotted"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "ghost_story": [
        (
            "What makes a ghost story feel spooky without being too scary?",
            "Soft dark places, strange sounds, and wondering what caused them can make a story feel spooky. A gentle ending makes it safe, because the mystery is understood in the end.",
        )
    ],
    "mouse": [
        (
            "Why do mice make little noises at night?",
            "Mice are small and quick, and they often come out when places are quiet. Their tiny feet and whiskery movements can sound much bigger in the dark.",
        )
    ],
    "kitten": [
        (
            "Why might a kitten make a room noisy?",
            "Kittens like to bat, chase, and pounce on things. A small playful paw can bump an object and make a surprising sound.",
        )
    ],
    "record": [
        (
            "What is a record disc?",
            "A record disc is a flat round music disc. When it slips or taps a hard surface, it can make a hollow sound.",
        )
    ],
    "tin": [
        (
            "Why does tin make a sharp sound?",
            "Tin is light and hard, so when it tips or hits the floor it makes a bright clink. Quiet rooms make that sound seem even louder.",
        )
    ],
    "questions": [
        (
            "Why can asking a question help when you feel scared?",
            "A question turns fear into looking and listening. When you start to learn what is really there, the scary feeling often gets smaller.",
        )
    ],
    "flashlight": [
        (
            "Why does a flashlight help with a mystery?",
            "A flashlight shows what is hiding in the dark. Good light can turn a guess into an answer.",
        )
    ],
    "lantern": [
        (
            "What does a lantern do in the dark?",
            "A lantern spreads a gentle glow so people can see around them. Warm light can make a room feel calmer and less spooky.",
        )
    ],
    "nightlight": [
        (
            "What is a night-light for?",
            "A night-light gives a small soft glow in the dark. It helps children see shapes in a room and feel more comfortable.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "ghost_story",
    "mouse",
    "kitten",
    "record",
    "tin",
    "questions",
    "flashlight",
    "lantern",
    "nightlight",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    lead = f["lead"]
    companion = f["companion"]
    place = f["place"]
    disc = f["disc_cfg"]
    creature = f["creature_cfg"]
    return [
        'Write a gentle ghost story for a 3-to-5-year-old that includes the words "scuttle", "sup", and "disc".',
        f"Tell a spooky-but-safe story where {lead.label} and {companion.label} hear a strange sound in {place.label}, talk about it out loud, and discover that a {creature.label} moved a {disc.label}.",
        "Write a short story where curiosity and dialogue shrink a scary mystery into something small, real, and friendly.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    lead = f["lead"]
    companion = f["companion"]
    helper = f["helper"]
    place = f["place"]
    creature = f["creature_cfg"]
    disc = f["disc_cfg"]
    approach = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(lead, companion)}, {lead.label} and {companion.label}, who heard a spooky sound at bedtime. {helper_title(helper.type)} helped them solve the mystery.",
        ),
        (
            "What made the room seem spooky at first?",
            f"A quick scuttle came from the dark, and the {disc.label} moved and made a sharp sound. In a quiet room, that tiny noise felt much bigger than it really was.",
        ),
        (
            "Why did the children think about a ghost?",
            f"They could not see what was moving, only hear it, so their imaginations filled the dark with guesses. That is why the ordinary sound felt ghostly at first.",
        ),
    ]
    if approach == "asked":
        qa.append(
            (
                "How did curiosity change what happened next?",
                f"{lead.label} chose to ask a question into the dark instead of only hiding from it. That made the children listen more carefully, and soon they noticed the sound was low and small, not like a giant ghost at all.",
            )
        )
    else:
        qa.append(
            (
                f"Why did {lead.label} call for {helper_title(helper.type)}?",
                f"The sound felt too strange to solve alone, so {lead.label} asked a calm grown-up for help. Even then, {lead.pronoun().capitalize()} still wanted to know the real answer, not just stay scared.",
            )
        )
    qa.append(
        (
            "What was the truth behind the spooky sound?",
            f"It was {creature.phrase} bumping {disc.phrase}. The mystery ended when the light showed the real cause clearly.",
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"The room stopped feeling haunted once the children understood the noise. {helper_title(helper.type)} set the disc flat so it would stay quiet, and the children went to bed feeling relieved and a little proud.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"ghost_story", "questions"}
    creature = f["creature_cfg"]
    disc = f["disc_cfg"]
    light = f["light"]
    if creature.id == "mouse":
        tags.add("mouse")
    if creature.id == "kitten":
        tags.add("kitten")
    if disc.id == "record_disc":
        tags.add("record")
    if disc.id == "tin_disc":
        tags.add("tin")
    tags |= set(light.tags)
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits: list[str] = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(place: Place, creature: CreatureCfg, disc: DiscCfg) -> str:
    if creature.id not in place.supports_creatures or place.id not in creature.homes:
        return (
            f"(No story: {creature.article} {creature.label} does not plausibly belong in {place.label}, "
            f"so the ghostly noise would feel forced.)"
        )
    if disc.id not in place.supports_discs:
        return (
            f"(No story: {place.label} does not naturally contain {disc.phrase}, "
            f"so the mystery object would not fit the room.)"
        )
    if creature.can_nudge < disc.weight:
        return (
            f"(No story: {creature.article} {creature.label} is too small to bump {disc.phrase} hard enough "
            f"to make the spooky sound. Pick a lighter disc or a stronger little culprit.)"
        )
    return "(No story: this place, creature, and disc do not make a reasonable mystery together.)"


def explain_key(name: str, key: str, registry: dict) -> str:
    choices = ", ".join(sorted(registry))
    return f"(Unknown {name} '{key}'. Choose one of: {choices}.)"


def outcome_of(params: StoryParams) -> str:
    return "asked" if would_speak_first(params.trait, params.bond) else "called"


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
valid(P, C, D) :- place(P), creature(C), disc(D),
                  supports_creature(P, C), supports_disc(P, D),
                  home(C, P), nudge(C, N), weight(D, W), N >= W.

% --- outcome model ---------------------------------------------------------
curious_trait(T) :- trait(T), trait_kind(T, curious).
curious_trait(T) :- trait(T), not trait_kind(T, curious), bond(B), B >= 7.

asked  :- curious_trait(_).
called :- not asked.

outcome(asked)  :- asked.
outcome(called) :- called.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for creature_id in sorted(place.supports_creatures):
            lines.append(asp.fact("supports_creature", place_id, creature_id))
        for disc_id in sorted(place.supports_discs):
            lines.append(asp.fact("supports_disc", place_id, disc_id))
    for creature_id, creature in CREATURES.items():
        lines.append(asp.fact("creature", creature_id))
        lines.append(asp.fact("nudge", creature_id, creature.can_nudge))
        for home in sorted(creature.homes):
            lines.append(asp.fact("home", creature_id, home))
    for disc_id, disc in DISCS.items():
        lines.append(asp.fact("disc", disc_id))
        lines.append(asp.fact("weight", disc_id, disc.weight))
    for trait in sorted(TRAITS):
        kind = "curious" if trait in CURIOUS_TRAITS else "cautious"
        lines.append(asp.fact("trait_kind", trait, kind))
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
        asp.fact("trait", params.trait),
        asp.fact("bond", params.bond),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


CURATED = [
    StoryParams(
        place="attic",
        creature="mouse",
        disc="tin_disc",
        light="lantern",
        child_name="Nora",
        child_gender="girl",
        companion_name="Ben",
        companion_gender="boy",
        helper="grandfather",
        trait="curious",
        bond=6,
    ),
    StoryParams(
        place="music_room",
        creature="kitten",
        disc="record_disc",
        light="flashlight",
        child_name="Leo",
        child_gender="boy",
        companion_name="Mia",
        companion_gender="girl",
        helper="grandmother",
        trait="thoughtful",
        bond=8,
    ),
    StoryParams(
        place="shed",
        creature="mouse",
        disc="flying_disc",
        light="nightlight",
        child_name="Ava",
        child_gender="girl",
        companion_name="Tom",
        companion_gender="boy",
        helper="mother",
        trait="shy",
        bond=4,
    ),
    StoryParams(
        place="music_room",
        creature="kitten",
        disc="brass_disc",
        light="lantern",
        child_name="Finn",
        child_gender="boy",
        companion_name="Rose",
        companion_gender="girl",
        helper="father",
        trait="brave",
        bond=5,
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A gentle ghost-story world about a spooky sound, a rolling disc, and curiosity."
    )
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--creature", choices=sorted(CREATURES))
    ap.add_argument("--disc", choices=sorted(DISCS))
    ap.add_argument("--light", choices=sorted(LIGHTS))
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("--trait", choices=sorted(TRAITS))
    ap.add_argument("--bond", type=int, choices=list(range(0, 11)))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid (place, creature, disc) combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test story generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place is not None and args.place not in PLACES:
        raise StoryError(explain_key("place", args.place, PLACES))
    if args.creature is not None and args.creature not in CREATURES:
        raise StoryError(explain_key("creature", args.creature, CREATURES))
    if args.disc is not None and args.disc not in DISCS:
        raise StoryError(explain_key("disc", args.disc, DISCS))
    if args.light is not None and args.light not in LIGHTS:
        raise StoryError(explain_key("light", args.light, LIGHTS))

    if args.place and args.creature and args.disc:
        place = PLACES[args.place]
        creature = CREATURES[args.creature]
        disc = DISCS[args.disc]
        if not plausible_noise(place, creature, disc):
            raise StoryError(explain_rejection(place, creature, disc))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.creature is None or combo[1] == args.creature)
        and (args.disc is None or combo[2] == args.disc)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, creature_id, disc_id = rng.choice(sorted(combos))
    light_id = args.light or rng.choice(sorted(LIGHTS))
    child_name, child_gender = _pick_child(rng)
    companion_name, companion_gender = _pick_child(rng, avoid=child_name)
    helper = args.helper or rng.choice(sorted(HELPERS))
    trait = args.trait or rng.choice(sorted(TRAITS))
    bond = args.bond if args.bond is not None else rng.randint(0, 10)

    return StoryParams(
        place=place_id,
        creature=creature_id,
        disc=disc_id,
        light=light_id,
        child_name=child_name,
        child_gender=child_gender,
        companion_name=companion_name,
        companion_gender=companion_gender,
        helper=helper,
        trait=trait,
        bond=bond,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(explain_key("place", params.place, PLACES))
    if params.creature not in CREATURES:
        raise StoryError(explain_key("creature", params.creature, CREATURES))
    if params.disc not in DISCS:
        raise StoryError(explain_key("disc", params.disc, DISCS))
    if params.light not in LIGHTS:
        raise StoryError(explain_key("light", params.light, LIGHTS))
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper '{params.helper}'. Choose one of: {', '.join(sorted(HELPERS))}.)")
    if params.trait not in TRAITS:
        raise StoryError(f"(Unknown trait '{params.trait}'. Choose one of: {', '.join(sorted(TRAITS))}.)")

    place = PLACES[params.place]
    creature = CREATURES[params.creature]
    disc = DISCS[params.disc]
    if not plausible_noise(place, creature, disc):
        raise StoryError(explain_rejection(place, creature, disc))

    world = tell(
        place=place,
        creature=creature,
        disc=disc,
        light=LIGHTS[params.light],
        child_name=params.child_name,
        child_gender=params.child_gender,
        companion_name=params.companion_name,
        companion_gender=params.companion_gender,
        helper_type=params.helper,
        trait=params.trait,
        bond=params.bond,
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


def asp_verify() -> int:
    rc = 0

    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases: list[StoryParams] = list(CURATED)
    for seed in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    diffs = []
    for params in cases:
        ao = asp_outcome(params)
        po = outcome_of(params)
        if ao != po:
            diffs.append((params, ao, po))
    if not diffs:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(diffs)} outcome differences.")
        for params, ao, po in diffs[:5]:
            print(f"  {params} -> asp={ao} python={po}")

    # Smoke test normal generation and emit.
    try:
        sample = generate(CURATED[0])
        buf = io.StringIO()
        with redirect_stdout(buf):
            emit(sample, trace=False, qa=True, header="### smoke")
        text = buf.getvalue()
        if not sample.story.strip():
            raise StoryError("Generated story was empty.")
        if "scuttle" not in sample.story.lower():
            raise StoryError("Generated story did not include required seed word 'scuttle'.")
        if "sup" not in sample.story.lower():
            raise StoryError("Generated story did not include required seed word 'sup'.")
        if "disc" not in sample.story.lower():
            raise StoryError("Generated story did not include required seed word 'disc'.")
        if "### smoke" not in text:
            raise StoryError("emit() smoke test did not produce output.")
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, creature, disc) combos:\n")
        for place, creature, disc in combos:
            print(f"  {place:10} {creature:8} {disc}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            header = f"### {p.child_name} & {p.companion_name}: {p.place} / {p.creature} / {p.disc} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
