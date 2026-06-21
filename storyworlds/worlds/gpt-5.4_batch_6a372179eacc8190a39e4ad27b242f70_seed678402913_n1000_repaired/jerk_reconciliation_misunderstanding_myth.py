#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/jerk_reconciliation_misunderstanding_myth.py
=======================================================================

A standalone story world about a child in a mythic place who misunderstands a
small spirit's helpful act, makes things worse with a frightened jerk on a
warning rope, then mends the harm through apology and a fitting peace-offer.

The world aims at TinyStories-scale myth: olive hills, bright springs, shell
shrines, and gentle divine beings close enough to upset and forgive. The
misunderstanding is stateful, not just verbal. The hero sees an offering moving
through dim light, mistakes help for theft, and reacts. That reaction changes
the shrine, the spirit's feelings, and the village's ritual. Reconciliation only
works when the peace-offer suits the spirit's nature.

Run it
------
    python storyworlds/worlds/gpt-5.4/jerk_reconciliation_misunderstanding_myth.py
    python storyworlds/worlds/gpt-5.4/jerk_reconciliation_misunderstanding_myth.py --realm spring --spirit river_nymph
    python storyworlds/worlds/gpt-5.4/jerk_reconciliation_misunderstanding_myth.py --reaction throw_stone
    python storyworlds/worlds/gpt-5.4/jerk_reconciliation_misunderstanding_myth.py --all
    python storyworlds/worlds/gpt-5.4/jerk_reconciliation_misunderstanding_myth.py --trace --seed 7
    python storyworlds/worlds/gpt-5.4/jerk_reconciliation_misunderstanding_myth.py --qa --json
    python storyworlds/worlds/gpt-5.4/jerk_reconciliation_misunderstanding_myth.py --verify
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
SENSE_MIN = 2


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
        female = {"girl", "woman", "priestess", "nymph", "goddess"}
        male = {"boy", "man", "priest", "god", "elder"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"priestess": "priestess", "priest": "priest", "elder": "elder"}.get(
            self.type, self.type
        )


@dataclass
class Realm:
    id: str
    place: str
    shrine: str
    sky: str
    path: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SpiritKind:
    id: str
    label: str
    type: str
    element: str
    movement: str
    voice: str
    domain_tags: set[str] = field(default_factory=set)
    offer_tags: set[str] = field(default_factory=set)
    knowledge_tags: set[str] = field(default_factory=set)


@dataclass
class Omen:
    id: str
    label: str
    phrase: str
    material: str
    purpose: str
    carried_by: set[str] = field(default_factory=set)
    realm_ids: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Reaction:
    id: str
    label: str
    sense: int
    severity: int
    text: str
    damage: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class PeaceOffer:
    id: str
    label: str
    phrase: str
    for_tags: set[str] = field(default_factory=set)
    blessing: str = ""
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


def _r_alarm_stalls_rite(world: World) -> list[str]:
    out: list[str] = []
    shrine = world.get("shrine")
    spirit = world.get("spirit")
    hero = world.get("hero")
    if shrine.meters["alarm"] >= THRESHOLD:
        sig = ("alarm_stalls",)
        if sig not in world.fired:
            world.fired.add(sig)
            shrine.meters["unfinished"] += 1
            hero.memes["fear"] += 1
            spirit.memes["hurt"] += 1
            out.append("__alarm__")
    return out


def _r_apology_mends(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    spirit = world.get("spirit")
    shrine = world.get("shrine")
    if hero.memes["apology"] >= THRESHOLD and hero.meters["gift_given"] >= THRESHOLD:
        sig = ("mended",)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["shame"] = 0.0
            hero.memes["trust"] += 1
            spirit.memes["hurt"] = 0.0
            spirit.memes["grace"] += 1
            shrine.meters["unfinished"] = 0.0
            shrine.meters["blessed"] += 1
            out.append("__mended__")
    return out


CAUSAL_RULES = [
    Rule(name="alarm_stalls_rite", tag="social", apply=_r_alarm_stalls_rite),
    Rule(name="apology_mends", tag="social", apply=_r_apology_mends),
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


REALMS = {
    "spring": Realm(
        id="spring",
        place="the white spring under a fig tree",
        shrine="a ring of pale stones around the spring",
        sky="the air smelled of water and mint",
        path="a stepping-stone path beside the water",
        tags={"spring", "water"},
    ),
    "orchard": Realm(
        id="orchard",
        place="the olive orchard on the low hill",
        shrine="a little altar of warm clay among the roots",
        sky="the leaves flashed silver whenever the wind turned them",
        path="a dusty path between the trees",
        tags={"orchard", "wind"},
    ),
    "shore": Realm(
        id="shore",
        place="the moon-bright shore below the cliffs",
        shrine="a shell shrine built where the foam reached and fell back",
        sky="the sea kept breathing over the stones",
        path="a narrow path above the tide pools",
        tags={"shore", "sea"},
    ),
}

SPIRITS = {
    "river_nymph": SpiritKind(
        id="river_nymph",
        label="river nymph",
        type="nymph",
        element="water",
        movement="rose from the water with shining drops on her arms",
        voice="like a cup filling at a fountain",
        domain_tags={"spring"},
        offer_tags={"water", "sweet"},
        knowledge_tags={"nymph", "spring"},
    ),
    "breeze_child": SpiritKind(
        id="breeze_child",
        label="breeze child",
        type="thing",
        element="air",
        movement="came skipping out of the wind as light as thistle fluff",
        voice="like leaves laughing together",
        domain_tags={"orchard"},
        offer_tags={"air", "song"},
        knowledge_tags={"wind", "offering"},
    ),
    "tide_messenger": SpiritKind(
        id="tide_messenger",
        label="tide messenger",
        type="thing",
        element="sea",
        movement="stepped from the foam with a hem of silver bubbles",
        voice="like small shells clinking in the surf",
        domain_tags={"shore"},
        offer_tags={"sea", "sweet"},
        knowledge_tags={"sea", "offering"},
    ),
}

OMENS = {
    "reed_crown": Omen(
        id="reed_crown",
        label="reed crown",
        phrase="a green reed crown braided at dawn",
        material="reeds",
        purpose="to float on the spring as a welcome to the water powers",
        carried_by={"river_nymph"},
        realm_ids={"spring"},
        tags={"offering", "reeds"},
    ),
    "olive_ribbon": Omen(
        id="olive_ribbon",
        label="olive ribbon",
        phrase="an olive ribbon woven with tiny bells",
        material="olive leaves and bells",
        purpose="to hang above the altar and call for a kind wind",
        carried_by={"breeze_child"},
        realm_ids={"orchard"},
        tags={"offering", "wind"},
    ),
    "shell_lamp": Omen(
        id="shell_lamp",
        label="shell lamp",
        phrase="a shell lamp with a pearl-white flame",
        material="shell and oil",
        purpose="to shine beside the tide and ask the sea for calm water",
        carried_by={"tide_messenger"},
        realm_ids={"shore"},
        tags={"offering", "lamp"},
    ),
}

REACTIONS = {
    "warning_jerk": Reaction(
        id="warning_jerk",
        label="warning rope",
        sense=3,
        severity=1,
        text="seized the shrine rope and gave it a frightened jerk",
        damage="The bronze bell boomed once, and everyone in the village looked up in alarm.",
        qa_text="pulled the warning rope in fright",
        tags={"bell", "misunderstanding"},
    ),
    "rush_forward": Reaction(
        id="rush_forward",
        label="rush forward",
        sense=2,
        severity=2,
        text="ran forward and caught at the moving offering with both hands",
        damage="The offering tipped, and bright drops and petals spilled over the shrine stones.",
        qa_text="rushed forward and grabbed at the offering",
        tags={"misunderstanding"},
    ),
    "bar_gate": Reaction(
        id="bar_gate",
        label="bar the path",
        sense=2,
        severity=2,
        text="spread both arms across the shrine path and shouted for the spirit to stop",
        damage="The path was blocked, and the rite halted while dust and silence gathered around them.",
        qa_text="blocked the path and shouted",
        tags={"misunderstanding"},
    ),
    "throw_stone": Reaction(
        id="throw_stone",
        label="throw a stone",
        sense=1,
        severity=3,
        text="snatched up a stone and hurled it in anger",
        damage="It was a cruel thing to do, and this world refuses it.",
        qa_text="threw a stone",
        tags={"harm"},
    ),
}

PEACE_OFFERS = {
    "honey_cake": PeaceOffer(
        id="honey_cake",
        label="honey cake",
        phrase="a round honey cake on a fig leaf",
        for_tags={"sweet", "sea"},
        blessing="The air turned gentle, and sweetness seemed to brighten even the stones.",
        tags={"honey", "offering"},
    ),
    "spring_water": PeaceOffer(
        id="spring_water",
        label="spring water",
        phrase="a fresh bowl of spring water with mint leaves floating on top",
        for_tags={"water"},
        blessing="The water cleared until every pebble looked newly washed.",
        tags={"water", "offering"},
    ),
    "olive_song": PeaceOffer(
        id="olive_song",
        label="olive song",
        phrase="a quiet song sung beneath the olive leaves",
        for_tags={"air", "song"},
        blessing="The leaves answered with a soft silver shimmer.",
        tags={"song", "offering"},
    ),
    "shell_sweets": PeaceOffer(
        id="shell_sweets",
        label="sesame sweets",
        phrase="three sesame sweets set in a little shell bowl",
        for_tags={"sea", "sweet"},
        blessing="The next wave came in smooth and bright, without a single angry splash.",
        tags={"sea", "offering"},
    ),
}

GIRL_NAMES = ["Thaleia", "Ione", "Myrto", "Daphne", "Nerina", "Clio"]
BOY_NAMES = ["Lykos", "Damon", "Nikos", "Theron", "Phaon", "Melas"]
TRAITS = ["quick", "dutiful", "proud", "eager", "watchful", "earnest"]


def spirit_fits_realm(realm: Realm, spirit: SpiritKind) -> bool:
    return realm.id in spirit.domain_tags


def omen_fits(realm: Realm, spirit: SpiritKind, omen: Omen) -> bool:
    return realm.id in omen.realm_ids and spirit.id in omen.carried_by


def compatible_offers(spirit: SpiritKind) -> list[PeaceOffer]:
    return [
        offer for offer in PEACE_OFFERS.values()
        if spirit.offer_tags & offer.for_tags
    ]


def sensible_reactions() -> list[Reaction]:
    return [reaction for reaction in REACTIONS.values() if reaction.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for realm_id, realm in REALMS.items():
        for spirit_id, spirit in SPIRITS.items():
            if not spirit_fits_realm(realm, spirit):
                continue
            if not compatible_offers(spirit):
                continue
            for omen_id, omen in OMENS.items():
                if omen_fits(realm, spirit, omen):
                    combos.append((realm_id, spirit_id, omen_id))
    return combos


def explain_combo_rejection(realm: Realm, spirit: SpiritKind, omen: Omen) -> str:
    if not spirit_fits_realm(realm, spirit):
        return (
            f"(No story: a {spirit.label} does not belong at {realm.place}. "
            f"This myth keeps each spirit close to its own place.)"
        )
    if realm.id not in omen.realm_ids:
        return (
            f"(No story: {omen.phrase} does not belong at {realm.place}. "
            f"The offering must fit the shrine and the place.)"
        )
    return (
        f"(No story: a {spirit.label} would not be the one carrying {omen.phrase}. "
        f"The misunderstanding must be plausible before it can be mended.)"
    )


def explain_reaction_rejection(reaction_id: str) -> str:
    reaction = REACTIONS[reaction_id]
    better = ", ".join(sorted(r.id for r in sensible_reactions()))
    return (
        f"(Refusing reaction '{reaction_id}': it scores too low on common sense "
        f"(sense={reaction.sense} < {SENSE_MIN}). This world allows fear and error, "
        f"but not needless cruelty. Try: {better}.)"
    )


def explain_offer_rejection(spirit: SpiritKind, offer: PeaceOffer) -> str:
    return (
        f"(No story: {offer.label} is not a fitting peace-offer for the {spirit.label}. "
        f"Reconciliation works here only when the apology matches the spirit's nature.)"
    )


def outcome_of(params: "StoryParams") -> str:
    reaction = REACTIONS[params.reaction]
    return "easy" if reaction.severity <= 1 else "deep"


def predict_theft(world: World, reaction: Reaction) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    shrine = sim.get("shrine")
    hero.memes["suspicion"] += 1
    shrine.meters["alarm"] += 1
    if reaction.id == "rush_forward":
        shrine.meters["spilled"] += 1
    if reaction.id == "bar_gate":
        shrine.meters["blocked"] += 1
    propagate(sim, narrate=False)
    return {
        "rite_stalls": sim.get("shrine").meters["unfinished"] >= THRESHOLD,
        "spirit_hurt": sim.get("spirit").memes["hurt"] >= THRESHOLD,
    }


def introduce(world: World, hero: Entity, elder: Entity, realm: Realm, omen: Omen) -> None:
    hero.memes["duty"] += 1
    world.say(
        f"In the old days, when streams answered songs and sea-foam remembered names, "
        f"{hero.id} lived near {realm.place}."
    )
    world.say(
        f"Each year the village set {omen.phrase} at {realm.shrine}, and {elder.label_word} "
        f"{elder.id} said it was a sign of thanks {omen.purpose}."
    )


def assign_watch(world: World, hero: Entity, elder: Entity, realm: Realm) -> None:
    world.say(
        f"Before sunrise, {elder.id} asked {hero.id} to watch {realm.path} while the coals "
        f"were lit and the bowls were arranged."
    )
    world.say(
        f"{realm.sky.capitalize()}, and the hour before dawn made every moving thing look half like a dream."
    )


def spirit_appears(world: World, spirit_ent: Entity, spirit: SpiritKind, omen: Omen) -> None:
    spirit_ent.meters["carrying"] += 1
    world.say(
        f"Then the {omen.label} began to move. Out of the dimness the {spirit.label} {spirit.movement}, "
        f"holding it carefully as if it were something precious."
    )


def misunderstand(world: World, hero: Entity, spirit_ent: Entity, omen: Omen, reaction: Reaction) -> None:
    pred = predict_theft(world, reaction)
    hero.memes["suspicion"] += 1
    hero.memes["fear"] += 1
    world.facts["predicted_stall"] = pred["rite_stalls"]
    world.facts["predicted_hurt"] = pred["spirit_hurt"]
    extra = " and the whole rite would stop" if pred["rite_stalls"] else ""
    world.say(
        f"From where {hero.id} stood, it seemed as though the stranger were stealing {omen.phrase}. "
        f"{hero.pronoun().capitalize()} thought the blessing would be lost{extra}."
    )


def react(world: World, hero: Entity, shrine: Entity, reaction: Reaction) -> None:
    hero.memes["defiance"] += 1
    shrine.meters["alarm"] += 1
    if reaction.id == "rush_forward":
        shrine.meters["spilled"] += 1
    if reaction.id == "bar_gate":
        shrine.meters["blocked"] += 1
    propagate(world, narrate=False)
    world.say(f"So {hero.id} {reaction.text}.")
    world.say(reaction.damage)


def reveal(world: World, elder: Entity, spirit_ent: Entity, spirit: SpiritKind, omen: Omen) -> None:
    hero = world.get("hero")
    hero.memes["shame"] += 1
    world.say(
        f"{elder.id} came quickly to the shrine and bowed. The {spirit.label}'s voice was {spirit.voice} "
        f'when {spirit_ent.pronoun()} said, "I was not taking it away. I was setting it in its right place."'
    )
    world.say(
        f"Only then did {hero.id} see that the {omen.label} had slipped crooked in the night, "
        f"and the spirit had been trying to help."
    )


def apology(world: World, hero: Entity, spirit_ent: Entity, offer: PeaceOffer) -> None:
    hero.memes["apology"] += 1
    hero.meters["gift_given"] += 1
    world.say(
        f"{hero.id}'s cheeks burned. {hero.pronoun().capitalize()} bowed low and said, "
        f'"I was wrong. I let fear make me unjust."'
    )
    world.say(
        f"Then {hero.pronoun()} brought {offer.phrase} and set it before the spirit with both hands."
    )
    propagate(world, narrate=False)


def accept(world: World, spirit_ent: Entity, spirit: SpiritKind, offer: PeaceOffer, omen: Omen) -> None:
    world.say(
        f"The {spirit.label} touched the gift, and the hurt look left {spirit_ent.pronoun('possessive')} face. "
        f'"Let the small wrong end here," {spirit_ent.pronoun()} said.'
    )
    world.say(
        f"Together they set the {omen.label} straight at the shrine. {offer.blessing}"
    )


def ending(world: World, hero: Entity, realm: Realm, outcome: str) -> None:
    if outcome == "easy":
        world.say(
            f"When the sun finally rose, it laid one bright band of gold across {realm.place}, "
            f"and {hero.id} felt lighter for having mended the mistake quickly."
        )
    else:
        world.say(
            f"When the sun finally rose, it touched the shrine stones one by one, as if teaching patience. "
            f"{hero.id} never forgot that a frightened heart can mistake help for harm."
        )


def tell(
    realm: Realm,
    spirit: SpiritKind,
    omen: Omen,
    reaction: Reaction,
    offer: PeaceOffer,
    hero_name: str = "Thaleia",
    hero_gender: str = "girl",
    elder_type: str = "priestess",
    trait: str = "watchful",
) -> World:
    world = World()
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_gender,
            role="hero",
            label=hero_name,
            traits=set(),
            attrs={"trait": trait},
        )
    )
    elder = world.add(
        Entity(
            id="Medeon" if elder_type == "priest" else "Ianthe",
            kind="character",
            type=elder_type,
            role="elder",
            label="the elder",
        )
    )
    spirit_ent = world.add(
        Entity(
            id="spirit",
            kind="character",
            type=spirit.type,
            role="spirit",
            label=spirit.label,
            tags=set(spirit.knowledge_tags),
        )
    )
    shrine = world.add(
        Entity(
            id="shrine",
            type="shrine",
            label="shrine",
            phrase=realm.shrine,
            tags=set(realm.tags) | {"shrine"},
        )
    )
    offering = world.add(
        Entity(
            id="offering",
            type="offering",
            label=omen.label,
            phrase=omen.phrase,
            tags=set(omen.tags),
        )
    )

    introduce(world, hero, elder, realm, omen)
    assign_watch(world, hero, elder, realm)

    world.para()
    spirit_appears(world, spirit_ent, spirit, omen)
    misunderstand(world, hero, spirit_ent, omen, reaction)
    react(world, hero, shrine, reaction)

    world.para()
    reveal(world, elder, spirit_ent, spirit, omen)
    apology(world, hero, spirit_ent, offer)
    accept(world, spirit_ent, spirit, offer, omen)

    world.para()
    outcome = outcome_of(
        StoryParams(
            realm=realm.id,
            spirit=spirit.id,
            omen=omen.id,
            reaction=reaction.id,
            peace_offer=offer.id,
            hero_name=hero_name,
            hero_gender=hero_gender,
            elder=elder_type,
            trait=trait,
            seed=None,
        )
    )
    ending(world, hero, realm, outcome)

    world.facts.update(
        realm=realm,
        spirit_cfg=spirit,
        omen_cfg=omen,
        reaction_cfg=reaction,
        offer_cfg=offer,
        hero=hero,
        elder=elder,
        spirit=spirit_ent,
        shrine=shrine,
        offering=offering,
        misunderstood=hero.memes["suspicion"] >= THRESHOLD,
        reconciled=shrine.meters["blessed"] >= THRESHOLD,
        outcome=outcome,
    )
    return world


@dataclass
class StoryParams:
    realm: str
    spirit: str
    omen: str
    reaction: str
    peace_offer: str
    hero_name: str
    hero_gender: str
    elder: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "nymph": [
        (
            "What is a nymph in a myth?",
            "A nymph is a small nature spirit from old stories. People imagined nymphs living near springs, trees, or rivers."
        )
    ],
    "spring": [
        (
            "Why do stories put spirits near springs?",
            "Springs give fresh water, so they feel special and alive in myths. People often treated them as places of blessing."
        )
    ],
    "wind": [
        (
            "Can wind carry light things?",
            "Yes. Wind can lift ribbons, leaves, and petals because they are small and light."
        )
    ],
    "sea": [
        (
            "Why do people in stories bring gifts to the sea?",
            "The sea can feed boats and fishermen, but it can also be dangerous. A gift in a story is a way of asking for kindness and calm water."
        )
    ],
    "offering": [
        (
            "What is an offering?",
            "An offering is a gift given with respect. In myths, people offer food, flowers, or songs to thank a spirit or ask for help."
        )
    ],
    "bell": [
        (
            "Why does a bell make people look up quickly?",
            "A bell carries sound far away. When it rings suddenly, people think something important has happened."
        )
    ],
    "misunderstanding": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when someone believes the wrong thing about what another person is doing or saying. It can cause trouble even when nobody meant harm."
        )
    ],
    "song": [
        (
            "Why can a song be a gift in a myth?",
            "Songs can honor a place or a spirit without taking anything away. In myths, music often shows respect, memory, and peace."
        )
    ],
    "water": [
        (
            "Why is water used in many old stories?",
            "Water keeps people, plants, and animals alive. That is why springs, rivers, and bowls of clear water often feel sacred in myths."
        )
    ],
    "honey": [
        (
            "Why does honey seem special in stories?",
            "Honey is sweet, golden, and slow to make, so it feels precious. Story people often give it as a sign of care."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "nymph",
    "spring",
    "wind",
    "sea",
    "offering",
    "bell",
    "misunderstanding",
    "song",
    "water",
    "honey",
]


CURATED = [
    StoryParams(
        realm="spring",
        spirit="river_nymph",
        omen="reed_crown",
        reaction="warning_jerk",
        peace_offer="spring_water",
        hero_name="Thaleia",
        hero_gender="girl",
        elder="priestess",
        trait="watchful",
    ),
    StoryParams(
        realm="orchard",
        spirit="breeze_child",
        omen="olive_ribbon",
        reaction="rush_forward",
        peace_offer="olive_song",
        hero_name="Lykos",
        hero_gender="boy",
        elder="priest",
        trait="dutiful",
    ),
    StoryParams(
        realm="shore",
        spirit="tide_messenger",
        omen="shell_lamp",
        reaction="bar_gate",
        peace_offer="shell_sweets",
        hero_name="Ione",
        hero_gender="girl",
        elder="priestess",
        trait="earnest",
    ),
    StoryParams(
        realm="shore",
        spirit="tide_messenger",
        omen="shell_lamp",
        reaction="warning_jerk",
        peace_offer="honey_cake",
        hero_name="Damon",
        hero_gender="boy",
        elder="priest",
        trait="quick",
    ),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    realm = f["realm"]
    spirit = f["spirit_cfg"]
    omen = f["omen_cfg"]
    reaction = f["reaction_cfg"]
    offer = f["offer_cfg"]
    return [
        f'Write a short myth for a young child that includes the word "jerk" and a misunderstanding at a shrine.',
        f"Tell a gentle myth where {hero.id} thinks a {spirit.label} is stealing {omen.phrase}, reacts by {reaction.qa_text}, and then makes peace with {offer.label}.",
        f"Write a reconciliation story set at {realm.place} where fear causes a mistake, the truth is revealed, and the ending shows the blessing returning.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    spirit_ent = f["spirit"]
    spirit = f["spirit_cfg"]
    omen = f["omen_cfg"]
    reaction = f["reaction_cfg"]
    offer = f["offer_cfg"]
    realm = f["realm"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a child watching a shrine, and a {spirit.label} who was trying to help. It is also about {elder.id}, who explains the truth."
        ),
        (
            f"What did {hero.id} misunderstand?",
            f"{hero.id} thought the {spirit.label} was stealing {omen.phrase}. The mistake happened because dawn light made the spirit's helpful movement look secret and wrong."
        ),
        (
            f"Why did {hero.id} react?",
            f"{hero.id} was trying to protect the shrine and the village's blessing. Fear came first, so {hero.pronoun()} acted before {hero.pronoun()} understood what was really happening."
        ),
        (
            f"What did {hero.id} do when {hero.pronoun()} was afraid?",
            f"{hero.pronoun().capitalize()} {reaction.qa_text}. That reaction stopped the rite and hurt the spirit's feelings, even though {hero.pronoun()} meant to help."
        ),
        (
            "How was the misunderstanding fixed?",
            f"{elder.id} explained that the spirit was setting the offering in its proper place, not stealing it. Then {hero.id} apologized and brought {offer.phrase}, which turned shame into peace."
        ),
    ]
    if outcome == "easy":
        qa.append(
            (
                "How did the story end?",
                f"It ended with a quick mending. When the sun rose over {realm.place}, the blessing had returned and {hero.id} felt lighter."
            )
        )
    else:
        qa.append(
            (
                "How did the story end?",
                f"It ended with peace and a lasting lesson. The shrine was blessed again, and {hero.id} learned never to let fear speak before truth."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"misunderstanding", "offering"}
    tags |= set(world.facts["realm"].tags)
    tags |= set(world.facts["spirit"].tags)
    tags |= set(world.facts["reaction_cfg"].tags)
    tags |= set(world.facts["offer_cfg"].tags)
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
belongs_in(S, R) :- spirit(S), realm(R), domain(S, R).
omen_fits(R, S, O) :- omen(O), belongs_in(S, R), omen_realm(O, R), carried_by(O, S).

offer_ok(S, P) :- spirit(S), offer(P), wants(S, T), offer_tag(P, T).

valid(R, S, O) :- realm(R), spirit(S), omen(O), omen_fits(R, S, O), offer_ok(S, _).
sensible_reaction(A) :- reaction(A), sense(A, V), sense_min(M), V >= M.

easy_reconcile :- chosen_reaction(A), severity(A, V), V <= 1.
deep_reconcile :- chosen_reaction(A), severity(A, V), V > 1.

outcome(easy) :- easy_reconcile.
outcome(deep) :- deep_reconcile.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for realm_id in REALMS:
        lines.append(asp.fact("realm", realm_id))
    for spirit_id, spirit in SPIRITS.items():
        lines.append(asp.fact("spirit", spirit_id))
        for realm_id in sorted(spirit.domain_tags):
            lines.append(asp.fact("domain", spirit_id, realm_id))
        for tag in sorted(spirit.offer_tags):
            lines.append(asp.fact("wants", spirit_id, tag))
    for omen_id, omen in OMENS.items():
        lines.append(asp.fact("omen", omen_id))
        for realm_id in sorted(omen.realm_ids):
            lines.append(asp.fact("omen_realm", omen_id, realm_id))
        for spirit_id in sorted(omen.carried_by):
            lines.append(asp.fact("carried_by", omen_id, spirit_id))
    for reaction_id, reaction in REACTIONS.items():
        lines.append(asp.fact("reaction", reaction_id))
        lines.append(asp.fact("sense", reaction_id, reaction.sense))
        lines.append(asp.fact("severity", reaction_id, reaction.severity))
    for offer_id, offer in PEACE_OFFERS.items():
        lines.append(asp.fact("offer", offer_id))
        for tag in sorted(offer.for_tags):
            lines.append(asp.fact("offer_tag", offer_id, tag))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_reactions() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible_reaction/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible_reaction"))


def asp_offer_map() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show offer_ok/2."))
    return sorted(set(asp.atoms(model, "offer_ok")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = asp.fact("chosen_reaction", params.reaction)
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    python_combos = set(valid_combos())
    clingo_combos = set(asp_valid_combos())
    if python_combos == clingo_combos:
        print(f"OK: gate matches valid_combos() ({len(python_combos)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_combos - python_combos:
            print("  only in clingo:", sorted(clingo_combos - python_combos))
        if python_combos - clingo_combos:
            print("  only in python:", sorted(python_combos - clingo_combos))

    python_reactions = {r.id for r in sensible_reactions()}
    clingo_reactions = set(asp_sensible_reactions())
    if python_reactions == clingo_reactions:
        print(f"OK: sensible reactions match ({sorted(python_reactions)}).")
    else:
        rc = 1
        print(
            f"MISMATCH in sensible reactions: clingo={sorted(clingo_reactions)} "
            f"python={sorted(python_reactions)}"
        )

    python_offers = {
        (spirit.id, offer.id)
        for spirit in SPIRITS.values()
        for offer in compatible_offers(spirit)
    }
    clingo_offers = set(asp_offer_map())
    if python_offers == clingo_offers:
        print(f"OK: compatible peace-offers match ({len(python_offers)} pairs).")
    else:
        rc = 1
        print("MISMATCH in compatible peace-offers:")
        if clingo_offers - python_offers:
            print("  only in clingo:", sorted(clingo_offers - python_offers))
        if python_offers - clingo_offers:
            print("  only in python:", sorted(python_offers - clingo_offers))

    cases = list(CURATED)
    for reaction_id in REACTIONS:
        params = StoryParams(
            realm="spring",
            spirit="river_nymph",
            omen="reed_crown",
            reaction=reaction_id,
            peace_offer="spring_water",
            hero_name="Testa",
            hero_gender="girl",
            elder="priestess",
            trait="watchful",
        )
        cases.append(params)
    bad = sum(1 for params in cases if asp_outcome(params) != outcome_of(params))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} reaction outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated story was empty.")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke-test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a mythic misunderstanding mended by reconciliation."
    )
    ap.add_argument("--realm", choices=REALMS)
    ap.add_argument("--spirit", choices=SPIRITS)
    ap.add_argument("--omen", choices=OMENS)
    ap.add_argument("--reaction", choices=REACTIONS)
    ap.add_argument("--peace-offer", dest="peace_offer", choices=PEACE_OFFERS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["priestess", "priest"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.reaction and REACTIONS[args.reaction].sense < SENSE_MIN:
        raise StoryError(explain_reaction_rejection(args.reaction))

    if args.realm and args.spirit and args.omen:
        realm = REALMS[args.realm]
        spirit = SPIRITS[args.spirit]
        omen = OMENS[args.omen]
        if not omen_fits(realm, spirit, omen):
            raise StoryError(explain_combo_rejection(realm, spirit, omen))

    combos = [
        combo
        for combo in valid_combos()
        if (args.realm is None or combo[0] == args.realm)
        and (args.spirit is None or combo[1] == args.spirit)
        and (args.omen is None or combo[2] == args.omen)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    realm_id, spirit_id, omen_id = rng.choice(sorted(combos))
    spirit = SPIRITS[spirit_id]

    offers = [offer.id for offer in compatible_offers(spirit)]
    if args.peace_offer is not None:
        if args.peace_offer not in offers:
            raise StoryError(explain_offer_rejection(spirit, PEACE_OFFERS[args.peace_offer]))
        peace_offer = args.peace_offer
    else:
        peace_offer = rng.choice(sorted(offers))

    reaction_choices = [
        reaction.id for reaction in sensible_reactions()
        if args.reaction is None or reaction.id == args.reaction
    ]
    if not reaction_choices:
        raise StoryError("(No sensible reaction matches the given options.)")
    reaction_id = rng.choice(sorted(reaction_choices))

    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    elder = args.elder or rng.choice(["priestess", "priest"])
    trait = rng.choice(TRAITS)

    return StoryParams(
        realm=realm_id,
        spirit=spirit_id,
        omen=omen_id,
        reaction=reaction_id,
        peace_offer=peace_offer,
        hero_name=hero_name,
        hero_gender=hero_gender,
        elder=elder,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        realm = REALMS[params.realm]
        spirit = SPIRITS[params.spirit]
        omen = OMENS[params.omen]
        reaction = REACTIONS[params.reaction]
        offer = PEACE_OFFERS[params.peace_offer]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter key: {err.args[0]})") from err

    if reaction.sense < SENSE_MIN:
        raise StoryError(explain_reaction_rejection(params.reaction))
    if not omen_fits(realm, spirit, omen):
        raise StoryError(explain_combo_rejection(realm, spirit, omen))
    if params.peace_offer not in [item.id for item in compatible_offers(spirit)]:
        raise StoryError(explain_offer_rejection(spirit, offer))

    world = tell(
        realm=realm,
        spirit=spirit,
        omen=omen,
        reaction=reaction,
        offer=offer,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        elder_type=params.elder,
        trait=params.trait,
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
        print(asp_program("", "#show valid/3.\n#show sensible_reaction/1.\n#show offer_ok/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        offers = asp_offer_map()
        print(f"sensible reactions: {', '.join(asp_sensible_reactions())}\n")
        print(f"{len(combos)} compatible (realm, spirit, omen) combos:\n")
        for realm_id, spirit_id, omen_id in combos:
            spirit_offers = sorted(offer for spirit_name, offer in offers if spirit_name == spirit_id)
            print(
                f"  {realm_id:8} {spirit_id:14} {omen_id:12} offers=[{', '.join(spirit_offers)}]"
            )
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples: list[StorySample] = []
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### {p.hero_name}: {p.realm} / {p.spirit} / {p.omen} "
                f"({p.reaction}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
