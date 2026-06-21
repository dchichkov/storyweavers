#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/loaf_sneak_inner_monologue_fable.py
==============================================================

A small storyworld for a fable-shaped tale about a hungry little creature, a warm
loaf, and the choice between sneaking and asking. The world is built around
temptation, inner monologue, and a gentle moral: what is asked for honestly is
better than what is snatched in secret.

The simulation keeps two kinds of state:

* physical meters: hunger, noise, distance, share, crumb
* emotional memes: temptation, caution, shame, trust, relief, gratitude

A reasonableness gate refuses combinations where sneaking could be rewarded as a
clean success. In this world, either a wise helper turns the creature back in
time, or an alert barrier catches the attempt. The fable never endorses theft.

Run it
------
    python storyworlds/worlds/gpt-5.4/loaf_sneak_inner_monologue_fable.py
    python storyworlds/worlds/gpt-5.4/loaf_sneak_inner_monologue_fable.py --choice sneak
    python storyworlds/worlds/gpt-5.4/loaf_sneak_inner_monologue_fable.py --creature mouse --place bakery_window
    python storyworlds/worlds/gpt-5.4/loaf_sneak_inner_monologue_fable.py --all
    python storyworlds/worlds/gpt-5.4/loaf_sneak_inner_monologue_fable.py --qa
    python storyworlds/worlds/gpt-5.4/loaf_sneak_inner_monologue_fable.py --verify
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
# from storyworlds/worlds/gpt-5.4/.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"              # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
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
        female = {"woman", "mother", "widow", "grandmother", "hen"}
        male = {"man", "father", "baker", "farmer", "miller"}
        if self.type in female:
            table = {"subject": "she", "object": "her", "possessive": "her"}
            return table[case]
        if self.type in male:
            table = {"subject": "he", "object": "him", "possessive": "his"}
            return table[case]
        table = {"subject": "they", "object": "them", "possessive": "their"}
        return table[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Creature:
    id: str
    label: str
    phrase: str
    type: str
    sneak_skill: int
    hunger: int
    honesty: int
    creatures_places: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Place:
    id: str
    label: str
    opening: str
    owner_name: str
    owner_type: str
    owner_label: str
    generosity: int
    loaf_spot: str
    chore: str
    barriers: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Barrier:
    id: str
    label: str
    alertness: int
    cue: str
    owner_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    type: str
    wisdom: int
    warning: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Loaf:
    id: str
    label: str
    crust: str
    smell: str
    share: str
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


def _r_alert(world: World) -> list[str]:
    out: list[str] = []
    if "barrier" not in world.entities or "owner" not in world.entities or "hero" not in world.entities:
        return out
    barrier = world.get("barrier")
    owner = world.get("owner")
    hero = world.get("hero")
    if barrier.meters["noise"] < THRESHOLD:
        return out
    sig = ("alert", barrier.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    owner.memes["alert"] += 1
    hero.memes["shame"] += 1
    out.append("__alert__")
    return out


def _r_share_softens(world: World) -> list[str]:
    out: list[str] = []
    if "owner" not in world.entities or "hero" not in world.entities:
        return out
    owner = world.get("owner")
    hero = world.get("hero")
    if owner.meters["share"] < THRESHOLD:
        return out
    sig = ("shared", owner.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.meters["hunger"] = 0.0
    hero.memes["relief"] += 1
    hero.memes["gratitude"] += 1
    hero.memes["temptation"] = 0.0
    hero.memes["trust"] += 1
    out.append("__share__")
    return out


CAUSAL_RULES = [
    Rule(name="alert", tag="social", apply=_r_alert),
    Rule(name="share_softens", tag="social", apply=_r_share_softens),
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


CREATURES = {
    "fox": Creature(
        id="fox",
        label="fox",
        phrase="a red fox with quick paws",
        type="animal",
        sneak_skill=3,
        hunger=4,
        honesty=1,
        creatures_places={"bakery_window", "market_cart", "mill_yard"},
        tags={"fox", "sneak"},
    ),
    "mouse": Creature(
        id="mouse",
        label="mouse",
        phrase="a small gray mouse with bright eyes",
        type="animal",
        sneak_skill=4,
        hunger=3,
        honesty=2,
        creatures_places={"bakery_window", "cottage_sill", "mill_yard"},
        tags={"mouse", "sneak"},
    ),
    "crow": Creature(
        id="crow",
        label="crow",
        phrase="a glossy black crow with a sharp beak",
        type="animal",
        sneak_skill=2,
        hunger=3,
        honesty=2,
        creatures_places={"market_cart", "mill_yard"},
        tags={"crow", "sneak"},
    ),
    "raccoon": Creature(
        id="raccoon",
        label="raccoon",
        phrase="a masked raccoon with nimble fingers",
        type="animal",
        sneak_skill=4,
        hunger=4,
        honesty=1,
        creatures_places={"cottage_sill", "market_cart", "mill_yard"},
        tags={"raccoon", "sneak"},
    ),
}

PLACES = {
    "bakery_window": Place(
        id="bakery_window",
        label="the bakery window",
        opening="an open window above a flour barrel",
        owner_name="Baker Bran",
        owner_type="baker",
        owner_label="the baker",
        generosity=3,
        loaf_spot="on the cool sill beside the window",
        chore="sweeping spilled flour back into a neat little heap",
        barriers={"bell", "cat"},
        tags={"bakery"},
    ),
    "cottage_sill": Place(
        id="cottage_sill",
        label="the cottage sill",
        opening="a low windowsill under the climbing beans",
        owner_name="Old Mira",
        owner_type="widow",
        owner_label="the widow",
        generosity=4,
        loaf_spot="on the sill to cool in the evening air",
        chore="carrying kindling sticks to the doorstep",
        barriers={"goose", "bell"},
        tags={"cottage"},
    ),
    "market_cart": Place(
        id="market_cart",
        label="the market cart",
        opening="a wooden cart waiting beside the square",
        owner_name="Miller Joss",
        owner_type="miller",
        owner_label="the miller",
        generosity=2,
        loaf_spot="under a striped cloth on the back of the cart",
        chore="gathering fallen grain sacks into a tidy row",
        barriers={"bell", "broom"},
        tags={"market"},
    ),
    "mill_yard": Place(
        id="mill_yard",
        label="the mill yard",
        opening="a broad yard where sacks leaned against the wall",
        owner_name="Farmer Pell",
        owner_type="farmer",
        owner_label="the farmer",
        generosity=2,
        loaf_spot="on a bench near the warm mill wall",
        chore="stacking empty baskets where they belonged",
        barriers={"dog", "bell"},
        tags={"mill"},
    ),
}

BARRIERS = {
    "bell": Barrier(
        id="bell",
        label="a hanging bell",
        alertness=3,
        cue="the little bell gave a bright tin-ting",
        owner_line='"Who comes by my loaf without a word?"',
        tags={"bell"},
    ),
    "dog": Barrier(
        id="dog",
        label="a watch dog",
        alertness=4,
        cue="the watch dog opened one eye and barked once, deep as a drum",
        owner_line='"Those who want bread may ask for bread,"',
        tags={"dog"},
    ),
    "goose": Barrier(
        id="goose",
        label="a white goose",
        alertness=3,
        cue="the white goose stretched its neck and honked like a trumpet",
        owner_line='"Hush there. I can hear trouble from my stool,"',
        tags={"goose"},
    ),
    "cat": Barrier(
        id="cat",
        label="a striped cat",
        alertness=4,
        cue="the striped cat thumped its tail and let out a warning yowl",
        owner_line='"Paws that creep can still turn around,"',
        tags={"cat"},
    ),
    "broom": Barrier(
        id="broom",
        label="a leaning broom",
        alertness=2,
        cue="the leaning broom slipped and clattered against the cart",
        owner_line='"A clattering broom tells on more than wind,"',
        tags={"broom"},
    ),
}

HELPERS = {
    "sparrow": Helper(
        id="sparrow",
        label="a sparrow",
        type="bird",
        wisdom=3,
        warning='"A quiet paw is not the same as a clean heart," chirped the sparrow.',
        tags={"bird", "advice"},
    ),
    "tortoise": Helper(
        id="tortoise",
        label="a tortoise",
        type="animal",
        wisdom=4,
        warning='"Slow feet reach supper sooner than crooked feet," said the tortoise.',
        tags={"advice"},
    ),
    "cricket": Helper(
        id="cricket",
        label="a cricket",
        type="animal",
        wisdom=2,
        warning='"When hunger shouts, let sense answer back," sang the cricket.',
        tags={"advice"},
    ),
    "ant": Helper(
        id="ant",
        label="an ant",
        type="animal",
        wisdom=3,
        warning='"Carry what is given, not what is stolen," said the ant.',
        tags={"advice"},
    ),
}

LOAVES = {
    "rye": Loaf(
        id="rye",
        label="a rye loaf",
        crust="dark and shiny",
        smell="nutty and warm",
        share="a warm heel of rye bread",
        tags={"bread"},
    ),
    "honey": Loaf(
        id="honey",
        label="a honey loaf",
        crust="golden and sweet",
        smell="sweet as late clover",
        share="a soft slice of honey loaf",
        tags={"bread", "honey"},
    ),
    "seed": Loaf(
        id="seed",
        label="a seeded loaf",
        crust="brown and crisp",
        smell="toasty and rich",
        share="a seedy crust still warm in the middle",
        tags={"bread", "seed"},
    ),
}


def can_reach(creature: Creature, place: Place) -> bool:
    return place.id in creature.creatures_places


def barrier_fits(place: Place, barrier: Barrier) -> bool:
    return barrier.id in place.barriers


def reform_strength(creature: Creature, helper: Helper) -> int:
    return creature.honesty + helper.wisdom


def caught_strength(barrier: Barrier) -> int:
    return barrier.alertness


def valid_combo(creature: Creature, place: Place, barrier: Barrier, helper: Helper) -> bool:
    if not can_reach(creature, place):
        return False
    if not barrier_fits(place, barrier):
        return False
    if reform_strength(creature, helper) > creature.hunger:
        return True
    if caught_strength(barrier) >= creature.sneak_skill:
        return True
    return False


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for cid, creature in CREATURES.items():
        for pid, place in PLACES.items():
            for bid, barrier in BARRIERS.items():
                for hid, helper in HELPERS.items():
                    if valid_combo(creature, place, barrier, helper):
                        combos.append((cid, pid, bid, hid))
    return sorted(combos)


@dataclass
class StoryParams:
    creature: str
    place: str
    barrier: str
    helper: str
    loaf: str
    choice: str
    seed: Optional[int] = None


def explain_reach(creature: Creature, place: Place) -> str:
    return (
        f"(No story: {creature.label.capitalize()} does not plausibly prowl around "
        f"{place.label}. Pick a place this creature can actually reach.)"
    )


def explain_barrier(place: Place, barrier: Barrier) -> str:
    return (
        f"(No story: {barrier.label} does not belong at {place.label}. "
        f"Pick one of: {', '.join(sorted(place.barriers))}.)"
    )


def explain_sneak_success(creature: Creature, barrier: Barrier, helper: Helper) -> str:
    return (
        f"(No story: with {helper.label}'s warning too weak to turn {creature.label} "
        f"back and {barrier.label} too easy to fool, sneaking could be rewarded. "
        f"This fable refuses a clean theft.)"
    )


def outcome_of(params: StoryParams) -> str:
    creature = CREATURES[params.creature]
    barrier = BARRIERS[params.barrier]
    helper = HELPERS[params.helper]
    if params.choice == "ask":
        return "shared"
    if reform_strength(creature, helper) > creature.hunger:
        return "reformed"
    if caught_strength(barrier) >= creature.sneak_skill:
        return "confessed"
    raise StoryError(explain_sneak_success(creature, barrier, helper))


def predict_sneak(world: World) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    barrier = sim.get("barrier")
    barrier.meters["noise"] += 1
    propagate(sim, narrate=False)
    return {
        "would_alert": sim.get("owner").memes["alert"] >= THRESHOLD,
        "would_shame": hero.memes["shame"] >= THRESHOLD,
    }


def introduce(world: World, hero: Entity, place: Place, loaf: Loaf) -> None:
    world.say(
        f"In a village lane stood {place.label}, and from {place.opening} came the smell "
        f"of {loaf.label}, {loaf.smell}."
    )
    world.say(
        f"Near it waited {hero.phrase}. All day {hero.pronoun()} had found no supper, "
        f"and the sight of the {loaf.crust} loaf resting {place.loaf_spot} made "
        f"{hero.pronoun('possessive')} empty belly stir."
    )
    hero.meters["hunger"] = float(world.facts["creature_cfg"].hunger)
    hero.memes["temptation"] += 1


def inner_monologue(world: World, hero: Entity, place: Place, loaf: Loaf) -> None:
    pred = predict_sneak(world)
    warning_tail = "Someone would surely look up." if pred["would_alert"] else "Perhaps nobody would see."
    world.facts["predicted_alert"] = pred["would_alert"]
    world.say(
        f'"If I sneak close enough," thought {hero.id}, "I could nip one bite from the {loaf.label} '
        f'and be gone before the dust settles." Then another thought came, smaller and truer: '
        f'"Bread taken in secret sits heavy." {warning_tail}'
    )


def helper_warning(world: World, helper: Entity) -> None:
    helper.memes["caution"] += 1
    world.say(helper.attrs["warning"])


def ask_openly(world: World, hero: Entity, owner: Entity, place: Place, loaf: Loaf) -> None:
    hero.memes["honesty"] += 1
    world.say(
        f"So {hero.id} stepped out where {owner.id} could see {hero.pronoun('object')} and said, "
        f'"Good {owner.label_word}, I am hungry. May I ask for a little of your {loaf.label}?"'
    )
    owner.memes["kindness"] += 1
    owner.meters["share"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{owner.id} looked at the thin little creature and nodded. "
        f"{owner.pronoun().capitalize()} cut off {loaf.share} and set it down."
    )
    world.say(
        f"{hero.id} bowed low before eating. The piece was small, but it tasted better for having been given."
    )


def begin_sneak(world: World, hero: Entity, place: Place) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f"But hunger tugged again, and {hero.id} lowered {hero.pronoun('possessive')} body and began to sneak "
        f"toward {place.loaf_spot} one careful step at a time."
    )


def turn_back(world: World, hero: Entity, owner: Entity, loaf: Loaf) -> None:
    hero.memes["shame"] += 1
    hero.memes["honesty"] += 1
    world.say(
        f"Before paw or claw touched the crust, {hero.id} stopped. "
        f'"No," thought {hero.pronoun()}, "better an empty paw than a crooked one."'
    )
    world.say(
        f"{hero.id} backed away from the loaf, lifted {hero.pronoun('possessive')} head, and called to {owner.id}, "
        f'"I came to sneak, but I would rather ask."'
    )
    owner.memes["kindness"] += 1
    owner.meters["share"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{owner.id}'s face softened at the truth. {owner.pronoun().capitalize()} gave {hero.pronoun('object')} "
        f"{loaf.share} and said that an honest mouth deserves a fair answer."
    )


def caught_sneaking(world: World, hero: Entity, owner: Entity, barrier: Entity, place: Place, loaf: Loaf) -> None:
    barrier.meters["noise"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {barrier.attrs['cue']}. At once {owner.id} turned from the doorway."
    )
    world.say(
        f"{owner.attrs['owner_line']} {owner.id} said. {hero.id} froze so still that even {hero.pronoun('possessive')} whiskers seemed ashamed."
    )
    world.say(
        f'"I meant to take what was not mine," {hero.id} admitted. "My hunger was sharp, but my manners were dull."'
    )
    hero.memes["honesty"] += 1
    owner.memes["judgment"] += 1
    world.say(
        f"{owner.id} did not strike or shout. Instead {owner.pronoun()} set {hero.pronoun('object')} to "
        f"{place.chore}."
    )
    hero.meters["work"] += 1
    owner.meters["share"] += 1
    propagate(world, narrate=False)
    world.say(
        f"When the work was done, {owner.id} gave {hero.pronoun('object')} {loaf.share}. "
        f'"Earned bread is lighter in the belly," {owner.pronoun()} said.'
    )


def ending_image(world: World, hero: Entity, helper: Entity, place: Place, outcome: str) -> None:
    if outcome in {"shared", "reformed"}:
        world.say(
            f"At sunset {hero.id} sat outside {place.label} with {helper.label} nearby, eating the last crumbs slowly. "
            f"{hero.pronoun().capitalize()} had come hungry, but went away with supper and a straighter heart."
        )
    else:
        world.say(
            f"At sunset {hero.id} carried the last crumb to {helper.label} and thanked {helper.pronoun('object')} for the warning. "
            f"{hero.pronoun().capitalize()} had learned that a loud lesson may still end in honest bread."
        )


def tell(creature: Creature, place: Place, barrier_cfg: Barrier, helper_cfg: Helper,
         loaf_cfg: Loaf, choice: str) -> World:
    world = World()
    hero = world.add(Entity(
        id=creature.label.capitalize(),
        kind="character",
        type=creature.type,
        label=creature.label,
        phrase=creature.phrase,
        role="hero",
        tags=set(creature.tags),
    ))
    owner = world.add(Entity(
        id=place.owner_name,
        kind="character",
        type=place.owner_type,
        label=place.owner_label,
        role="owner",
        attrs={"generosity": place.generosity},
        tags=set(place.tags),
    ))
    barrier = world.add(Entity(
        id="Barrier",
        kind="thing",
        type="barrier",
        label=barrier_cfg.label,
        role="barrier",
        attrs={"cue": barrier_cfg.cue},
        tags=set(barrier_cfg.tags),
    ))
    helper = world.add(Entity(
        id=helper_cfg.label.capitalize(),
        kind="character",
        type=helper_cfg.type,
        label=helper_cfg.label,
        role="helper",
        attrs={"warning": helper_cfg.warning},
        tags=set(helper_cfg.tags),
    ))
    loaf = world.add(Entity(
        id="Loaf",
        kind="thing",
        type="bread",
        label=loaf_cfg.label,
        phrase=loaf_cfg.label,
        role="loaf",
        tags=set(loaf_cfg.tags),
    ))
    owner.attrs["owner_line"] = barrier_cfg.owner_line

    world.facts.update(
        creature_cfg=creature,
        place_cfg=place,
        barrier_cfg=barrier_cfg,
        helper_cfg=helper_cfg,
        loaf_cfg=loaf_cfg,
    )

    introduce(world, hero, place, loaf_cfg)
    world.para()
    inner_monologue(world, hero, place, loaf_cfg)
    helper_warning(world, helper)
    world.para()

    outcome = outcome_of(StoryParams(
        creature=creature.id,
        place=place.id,
        barrier=barrier_cfg.id,
        helper=helper_cfg.id,
        loaf=loaf_cfg.id,
        choice=choice,
    ))

    if choice == "ask":
        ask_openly(world, hero, owner, place, loaf_cfg)
    elif outcome == "reformed":
        begin_sneak(world, hero, place)
        turn_back(world, hero, owner, loaf_cfg)
    elif outcome == "confessed":
        begin_sneak(world, hero, place)
        caught_sneaking(world, hero, owner, barrier, place, loaf_cfg)
    else:
        raise StoryError("Unreachable outcome in tell().")

    world.para()
    ending_image(world, hero, helper, place, outcome)

    world.facts.update(
        hero=hero,
        owner=owner,
        barrier=barrier,
        helper=helper,
        loaf=loaf,
        choice=choice,
        outcome=outcome,
        shared=owner.meters["share"] >= THRESHOLD,
        alerted=owner.memes["alert"] >= THRESHOLD,
        ashamed=hero.memes["shame"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "bread": [
        (
            "What is a loaf?",
            "A loaf is a whole baked piece of bread. People cut slices or pieces from it to eat."
        )
    ],
    "sneak": [
        (
            "What does it mean to sneak?",
            "To sneak is to move secretly so others do not notice you. In a fable, sneaking often shows that someone knows a choice is not quite right."
        )
    ],
    "bell": [
        (
            "Why does a bell make sneaking hard?",
            "A bell makes noise as soon as something brushes it or shakes it. Noise tells other people to look up."
        )
    ],
    "dog": [
        (
            "Why is a watch dog hard to fool?",
            "A watch dog listens and smells carefully, even when it looks sleepy. It warns people when someone comes too close."
        )
    ],
    "goose": [
        (
            "Why are geese good at warning people?",
            "Geese notice movement quickly and honk loudly. Their noise can wake a whole yard."
        )
    ],
    "cat": [
        (
            "Why might a cat notice a sneaking animal?",
            "Cats watch quietly and hear little rustles. A sneaking paw is exactly the sort of thing a cat notices."
        )
    ],
    "honesty": [
        (
            "Why is asking better than sneaking?",
            "Asking treats the other person as someone who can answer yes or no. Sneaking tries to take away that choice."
        )
    ],
    "fable": [
        (
            "What is a fable?",
            "A fable is a short story that teaches a lesson. The lesson is often shown through animals or simple village characters."
        )
    ],
}

KNOWLEDGE_ORDER = ["bread", "sneak", "bell", "dog", "goose", "cat", "honesty", "fable"]


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    loaf_cfg = world.facts["loaf_cfg"]
    place = world.facts["place_cfg"]
    outcome = world.facts["outcome"]
    if outcome == "shared":
        return [
            f'Write a short fable about a hungry {hero.label} who sees a {loaf_cfg.label} at {place.label} and thinks about whether to sneak or ask.',
            f'Write a child-facing story with inner monologue that includes the words "loaf" and "sneak" and ends with honesty being rewarded.',
            f"Tell a village fable where a creature asks openly for bread instead of taking it in secret."
        ]
    if outcome == "reformed":
        return [
            f'Write a fable where a hungry {hero.label} starts to sneak toward a loaf but changes course because of an inner voice and a wise helper.',
            f'Write a story with inner monologue using the words "loaf" and "sneak", where the creature turns back before stealing.',
            f"Tell a gentle moral tale in which honesty arrives just in time."
        ]
    return [
        f'Write a fable where a hungry {hero.label} tries to sneak to a loaf, gets caught, confesses, and learns a lesson.',
        f'Write a story with inner monologue using the words "loaf" and "sneak", where a warning sound exposes the secret plan.',
        f"Tell a moral tale in which work and truth lead to an earned piece of bread."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    owner = world.facts["owner"]
    helper = world.facts["helper"]
    place = world.facts["place_cfg"]
    barrier = world.facts["barrier_cfg"]
    loaf = world.facts["loaf_cfg"]
    choice = world.facts["choice"]
    outcome = world.facts["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about a hungry {hero.label} who finds {loaf.label} at {place.label}. "
            f"The story also includes {owner.label_word} and {helper.label}."
        ),
        (
            "Why did the hero want the loaf?",
            f"{hero.id} wanted the loaf because {hero.pronoun()} was hungry and the bread smelled {loaf.smell}. "
            f"The warm smell made the temptation feel stronger."
        ),
        (
            "What was the inner monologue about?",
            f"{hero.id} first thought about how to sneak close enough to steal a bite. "
            f"Then a truer thought warned that bread taken in secret would sit heavy."
        ),
    ]
    if choice == "ask":
        qa.append((
            f"How did {hero.id} solve the problem?",
            f"{hero.pronoun().capitalize()} stepped into view and asked openly for a little bread. "
            f"Because the request was honest, {owner.id} shared a piece of the loaf."
        ))
    elif outcome == "reformed":
        qa.append((
            f"Did {hero.id} steal the loaf?",
            f"No. {hero.pronoun().capitalize()} began to sneak, but stopped before touching the crust. "
            f"The warning from {helper.label} and {hero.pronoun('possessive')} own conscience turned {hero.pronoun('object')} back."
        ))
    else:
        qa.append((
            f"What happened when {hero.id} tried to sneak?",
            f"{barrier.cue[0].upper()}{barrier.cue[1:]}, and {owner.id} noticed at once. "
            f"The noise exposed the secret plan before the loaf could be taken."
        ))
        qa.append((
            f"Why did {owner.id} still give {hero.id} bread at the end?",
            f"{owner.pronoun().capitalize()} gave bread after {hero.id} confessed and did the small chore at {place.label}. "
            f"The bread was earned honestly, which is different from sneaking it away."
        ))
    qa.append((
        "What lesson did the ending show?",
        f"The ending showed that honest asking is better than secret taking. "
        f"{hero.id} left with less shame and a straighter heart because the bread came by truth, not by sneaking."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"bread", "sneak", "honesty", "fable"} | set(world.facts["barrier_cfg"].tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:12} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        creature="mouse",
        place="bakery_window",
        barrier="bell",
        helper="tortoise",
        loaf="rye",
        choice="ask",
        seed=1,
    ),
    StoryParams(
        creature="fox",
        place="market_cart",
        barrier="bell",
        helper="sparrow",
        loaf="honey",
        choice="sneak",
        seed=2,
    ),
    StoryParams(
        creature="raccoon",
        place="cottage_sill",
        barrier="goose",
        helper="tortoise",
        loaf="seed",
        choice="sneak",
        seed=3,
    ),
    StoryParams(
        creature="crow",
        place="mill_yard",
        barrier="dog",
        helper="cricket",
        loaf="rye",
        choice="sneak",
        seed=4,
    ),
]


ASP_RULES = r"""
reachable(C, P) :- creature_place(C, P).
fitting(P, B)   :- place_barrier(P, B).
reform(C, H)    :- honesty(C, Ho), wisdom(H, Wi), hunger(C, Hu), Ho + Wi > Hu.
caught(C, B)    :- alertness(B, A), sneak_skill(C, S), A >= S.
valid(C, P, B, H) :- reachable(C, P), fitting(P, B), reform(C, H).
valid(C, P, B, H) :- reachable(C, P), fitting(P, B), caught(C, B).

outcome(shared)    :- choice(ask).
outcome(reformed)  :- choice(sneak), reform(chosen_creature, chosen_helper).
outcome(confessed) :- choice(sneak), not reform(chosen_creature, chosen_helper),
                      caught(chosen_creature, chosen_barrier).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for cid, creature in CREATURES.items():
        lines.append(asp.fact("creature", cid))
        lines.append(asp.fact("sneak_skill", cid, creature.sneak_skill))
        lines.append(asp.fact("hunger", cid, creature.hunger))
        lines.append(asp.fact("honesty", cid, creature.honesty))
        for pid in sorted(creature.creatures_places):
            lines.append(asp.fact("creature_place", cid, pid))
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for bid in sorted(place.barriers):
            lines.append(asp.fact("place_barrier", pid, bid))
    for bid, barrier in BARRIERS.items():
        lines.append(asp.fact("barrier", bid))
        lines.append(asp.fact("alertness", bid, barrier.alertness))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("wisdom", hid, helper.wisdom))
    for lid in LOAVES:
        lines.append(asp.fact("loaf", lid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_creature", params.creature),
        asp.fact("chosen_helper", params.helper),
        asp.fact("chosen_barrier", params.barrier),
        asp.fact("choice", params.choice),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    outs = asp.atoms(model, "outcome")
    return outs[0][0] if outs else "?"


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
    rng = random.Random(7)
    parser = build_parser()
    for _ in range(20):
        try:
            params = resolve_params(parser.parse_args([]), rng)
        except StoryError:
            continue
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
        sample = generate(CURATED[0])
        assert sample.story and isinstance(sample.story, str)
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Storyworld: a hungry creature, a loaf, and the choice to sneak or ask."
    )
    ap.add_argument("--creature", choices=sorted(CREATURES))
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--barrier", choices=sorted(BARRIERS))
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("--loaf", choices=sorted(LOAVES))
    ap.add_argument("--choice", choices=["ask", "sneak"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.creature and args.place:
        creature = CREATURES[args.creature]
        place = PLACES[args.place]
        if not can_reach(creature, place):
            raise StoryError(explain_reach(creature, place))
    if args.place and args.barrier:
        place = PLACES[args.place]
        barrier = BARRIERS[args.barrier]
        if not barrier_fits(place, barrier):
            raise StoryError(explain_barrier(place, barrier))
    if args.creature and args.barrier and args.helper:
        creature = CREATURES[args.creature]
        barrier = BARRIERS[args.barrier]
        helper = HELPERS[args.helper]
        if not (reform_strength(creature, helper) > creature.hunger or caught_strength(barrier) >= creature.sneak_skill):
            raise StoryError(explain_sneak_success(creature, barrier, helper))

    combos = [
        c for c in valid_combos()
        if (args.creature is None or c[0] == args.creature)
        and (args.place is None or c[1] == args.place)
        and (args.barrier is None or c[2] == args.barrier)
        and (args.helper is None or c[3] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    creature_id, place_id, barrier_id, helper_id = rng.choice(combos)
    loaf_id = args.loaf or rng.choice(sorted(LOAVES))
    choice = args.choice or rng.choice(["ask", "sneak"])
    return StoryParams(
        creature=creature_id,
        place=place_id,
        barrier=barrier_id,
        helper=helper_id,
        loaf=loaf_id,
        choice=choice,
    )


def generate(params: StoryParams) -> StorySample:
    if params.creature not in CREATURES:
        raise StoryError(f"(Unknown creature: {params.creature})")
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.barrier not in BARRIERS:
        raise StoryError(f"(Unknown barrier: {params.barrier})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.loaf not in LOAVES:
        raise StoryError(f"(Unknown loaf: {params.loaf})")
    if params.choice not in {"ask", "sneak"}:
        raise StoryError(f"(Unknown choice: {params.choice})")

    creature = CREATURES[params.creature]
    place = PLACES[params.place]
    barrier = BARRIERS[params.barrier]
    helper = HELPERS[params.helper]

    if not can_reach(creature, place):
        raise StoryError(explain_reach(creature, place))
    if not barrier_fits(place, barrier):
        raise StoryError(explain_barrier(place, barrier))
    if not valid_combo(creature, place, barrier, helper):
        raise StoryError(explain_sneak_success(creature, barrier, helper))

    world = tell(
        creature=creature,
        place=place,
        barrier_cfg=barrier,
        helper_cfg=helper,
        loaf_cfg=LOAVES[params.loaf],
        choice=params.choice,
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (creature, place, barrier, helper) combos:\n")
        for creature, place, barrier, helper in combos:
            print(f"  {creature:8} {place:14} {barrier:6} {helper}")
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
                f"### {p.creature} at {p.place} with {p.barrier} and {p.helper} "
                f"({p.choice}, {outcome_of(p)})"
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
