#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/crumpet_hallelujahs_sound_effects_cautionary_rhyme_pirate.py
========================================================================================

A standalone storyworld for a tiny pirate-play domain built from the seed words
"crumpet" and "hallelujahs", with sound effects, a cautionary turn, and a light
rhyming style.

Premise
-------
Two children are playing pirates indoors. They find a crumpet and decide it is
pirate treasure fit for a feast. The hungry captain is tempted to warm it with a
forbidden flame so the snack will feel more splendid. A cautious mate warns that
cloth nearby could catch fire. Depending on ages, trust, and the chosen method,
the plan is averted, contained, or ends in a smoky loss. In the happy endings, a
grown-up toasts the crumpet safely and the children cry little hallelujahs.

The world model drives the prose: hunger, bravado, caution, heat, smoke, and
danger all live in simulated state, and the rendered story follows those state
changes rather than swapping nouns in one frozen paragraph.

Run it
------
    python storyworlds/worlds/gpt-5.4/crumpet_hallelujahs_sound_effects_cautionary_rhyme_pirate.py
    python storyworlds/worlds/gpt-5.4/crumpet_hallelujahs_sound_effects_cautionary_rhyme_pirate.py --theme galley --forbidden candle --target tea_towel
    python storyworlds/worlds/gpt-5.4/crumpet_hallelujahs_sound_effects_cautionary_rhyme_pirate.py --target stone_hearth
    python storyworlds/worlds/gpt-5.4/crumpet_hallelujahs_sound_effects_cautionary_rhyme_pirate.py --response pan
    python storyworlds/worlds/gpt-5.4/crumpet_hallelujahs_sound_effects_cautionary_rhyme_pirate.py --all
    python storyworlds/worlds/gpt-5.4/crumpet_hallelujahs_sound_effects_cautionary_rhyme_pirate.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/crumpet_hallelujahs_sound_effects_cautionary_rhyme_pirate.py --verify
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
# This file lives in storyworlds/worlds/gpt-5.4/, so we need the storyworlds/
# package directory itself on sys.path.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
BRAVERY_INIT = 6.0
CAUTIOUS_TRAITS = {"careful", "cautious", "steady", "sensible"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    age: int = 0
    owner: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    flammable: bool = False
    makes_flame: bool = False
    safe_heat: bool = False
    edible: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Theme:
    id: str
    scene: str
    rig: str
    titles: tuple[str, str]
    snack_name: str
    dark_spot: str
    voyage_line: str
    ending_line: str
    rhyme_tag: str = ""


@dataclass
class Forbidden:
    id: str
    cry: str
    label: str
    phrase: str
    where: str
    flare: str
    strike: str
    warning: str
    plural: bool = False
    makes_flame: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Target:
    id: str
    label: str
    the: str
    near: str
    detail: str
    spread: int = 2
    flammable: bool = True
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.the[0].upper() + self.the[1:]


@dataclass
class SafeFix:
    id: str
    label: str
    phrase: str
    heat_word: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"captain", "mate"}]

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
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_spread(world: World) -> list[str]:
    out: list[str] = []
    room = world.entities.get("room")
    snack = world.entities.get("crumpet")
    for ent in list(world.entities.values()):
        if ent.meters["burning"] < THRESHOLD:
            continue
        sig = ("spread", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if room is not None:
            room.meters["danger"] += 1
            room.meters["smoke"] += 1
        if snack is not None:
            snack.meters["inedible"] += 1
        for kid in world.kids():
            kid.memes["fear"] += 1
        out.append("__fire__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="spread", tag="physical", apply=_r_spread),
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


def hazard_at_risk(forbidden: Forbidden, target: Target) -> bool:
    return forbidden.makes_flame and target.flammable


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def fire_severity(target: Target, delay: int) -> int:
    return target.spread + delay


def is_contained(response: Response, target: Target, delay: int) -> bool:
    return response.power >= fire_severity(target, delay)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, captain_age: int, mate_age: int, trait: str) -> bool:
    mate_older = relation == "siblings" and mate_age > captain_age
    authority = (initial_caution(trait) + 1.0) + (4.0 if mate_older else 0.0)
    return mate_older and authority > BRAVERY_INIT


def predict_fire(world: World, target_id: str) -> dict:
    sim = world.copy()
    _do_forbidden(sim, sim.get(target_id), narrate=False)
    return {
        "ignites": sim.get(target_id).meters["burning"] >= THRESHOLD,
        "danger": sim.get("room").meters["danger"],
        "smoke": sim.get("room").meters["smoke"],
    }


def _do_forbidden(world: World, target: Entity, narrate: bool = True) -> None:
    target.meters["burning"] += 1
    target.meters["scorched"] += 1
    world.get("crumpet").meters["warmth"] += 0.5
    propagate(world, narrate=narrate)


def sound_triplet() -> str:
    return "Clink-clank, swish-swash, tap-tum-tay!"


def play_setup(world: World, captain: Entity, mate: Entity, theme: Theme) -> None:
    for kid in (captain, mate):
        kid.memes["joy"] += 1
    t1, t2 = theme.titles
    world.say(
        f"{captain.id} and {mate.id} turned the room into {theme.scene}. {theme.rig}"
    )
    world.say(
        f'"{t1} {captain.id} and {t2} {mate.id}!" cried {captain.id}. '
        f'"{sound_triplet()} Off we sail today!"'
    )
    world.say(
        f"On a little plate lay a crumpet, round and pale, and to the hungry crew it looked like {theme.snack_name}."
    )


def dark_need(world: World, mate: Entity, theme: Theme, target: Target) -> None:
    world.say(
        f"But {theme.dark_spot}, {target.detail}, looked shadowy and cold."
    )
    world.say(
        f'"A warm bite would cheer the deck," said {mate.id}. '
        f'"Yet warm things and flames can wreck."'
    )


def tempt(world: World, captain: Entity, forbidden: Forbidden) -> None:
    captain.memes["bravado"] += 1
    world.get("crumpet").memes["temptation"] += 1
    world.say(
        f'{captain.id} rubbed {captain.pronoun("possessive")} tummy. '
        f'"{forbidden.cry} I saw {forbidden.phrase} {forbidden.where}."'
    )
    world.say(
        "The plan felt bold and bright and neat, as if one spark could toast the treat."
    )


def warn(world: World, mate: Entity, captain: Entity, forbidden: Forbidden, target: Target, parent: Entity) -> None:
    pred = predict_fire(world, "target")
    mate.memes["caution"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    world.facts["predicted_smoke"] = pred["smoke"]
    extra = ""
    if mate.memes["caution"] >= 6:
        extra = f" {mate.id} shook {mate.pronoun('possessive')} head and would not grin."
    world.say(
        f'{mate.id} pointed at {target.the}. "{parent.label_word.capitalize()} says no touching {forbidden.label}. '
        f'{forbidden.warning}, and {target.the} could catch."{extra}'
    )
    world.say(
        f'"A spark can leap. A cloth can flare. Then smoke goes poof into the air."'
    )


def defy(world: World, captain: Entity, mate: Entity, forbidden: Forbidden) -> None:
    captain.memes["defiance"] += 1
    older = captain.attrs.get("relation") == "siblings" and captain.age > mate.age
    if older:
        rel = "big brother" if captain.type == "boy" else "big sister"
        world.say(
            f'"Hush now, matey, do not moan," said {captain.id}. '
            f'Because {captain.id} was {mate.pronoun("possessive")} {rel}, {mate.id} could not stop {captain.pronoun("object")}.'
        )
    else:
        world.say(f'"Hush now, matey, do not moan," said {captain.id}, and darted off alone.')
    world.say("Tiptoe, clip-clop, back came the captain with trouble in hand.")


def back_down(world: World, captain: Entity, mate: Entity, forbidden: Forbidden, parent: Entity, theme: Theme) -> None:
    captain.memes["bravery"] = 0.0
    captain.memes["relief"] += 1
    mate.memes["relief"] += 1
    rel = "brother" if mate.type == "boy" else "sister"
    world.say(
        f'"Hush now, matey, do not moan," said {captain.id}. '
        f'But {mate.id} was {captain.pronoun("possessive")} older {rel}, and {captain.id} saw the worry in {mate.pronoun("possessive")} face.'
    )
    world.say(
        f'{captain.id} set the idea down at once. "No flame for feast, no spark for play. We ask {parent.label_word} the proper way."'
    )
    world.say(theme.voyage_line)


def ignite(world: World, forbidden: Forbidden, target: Target) -> None:
    _do_forbidden(world, world.get("target"))
    world.say(
        f'{forbidden.strike} {forbidden.flare} bobbed to life. For one blink it looked like a pirate lantern for the crumpet feast.'
    )
    world.say(
        f"Then the tiny flame bent sideways, kissed {target.near}, and -- ffft! -- a thin orange lick began to climb."
    )


def alarm(world: World, mate: Entity, captain: Entity, target: Target, parent: Entity) -> None:
    world.say(f'"{captain.id}! Fire! {target.The}!" cried {mate.id}.')
    world.say(f'"{parent.label_word.upper()}! Quick-quick, come!"')


def rescue(world: World, parent: Entity, response: Response, target: Target) -> None:
    world.get("target").meters["burning"] = 0.0
    world.get("room").meters["danger"] = 0.0
    body = response.text.replace("{target}", target.label)
    world.say(
        f"{parent.label_word.capitalize()} came running. Whisk-whirl, {parent.pronoun()} {body}."
    )
    world.say(
        "The flame gave one last hiss -- sss! -- and died, leaving only a smoky whiff and two very shaky pirates."
    )


def lesson(world: World, parent: Entity, captain: Entity, mate: Entity, forbidden: Forbidden) -> None:
    for kid in (captain, mate):
        kid.memes["fear"] = 0.0
        kid.memes["relief"] += 1
        kid.memes["lesson"] += 1
        kid.memes["love"] += 1
    world.say("For a beat the room was still.")
    world.say(
        f'Then {parent.label_word.capitalize()} knelt and held them close. '
        f'"I am glad you called me," {parent.pronoun()} said. '
        f'"But remember this little tale: {forbidden.warning}, and cloth plus flame can quickly fail."'
    )


def safe_feast(world: World, parent: Entity, captain: Entity, mate: Entity, theme: Theme, safe_fix: SafeFix) -> None:
    for kid in (captain, mate):
        kid.memes["joy"] += 1
        kid.memes["safety"] += 1
    crumpet = world.get("crumpet")
    crumpet.meters["warmth"] = 1.0
    crumpet.meters["toasted"] = 1.0
    world.say(
        f'After the scare, {parent.label_word} used {safe_fix.phrase}. Ping! Pop! Soon the crumpet was {safe_fix.heat_word} and safe.'
    )
    world.say(
        f'{captain.id} took a small bite. {mate.id} took one too. "Crumbs and cheers and hallelujahs!" they sang.'
    )
    world.say(
        f"{theme.ending_line} They kept their game, their snack, and their safe little day."
    )


def rescue_fail(world: World, parent: Entity, response: Response, target: Target) -> None:
    world.get("room").meters["danger"] += 1
    world.get("room").meters["burning"] += 1
    world.get("target").meters["burning"] += 1
    propagate(world, narrate=False)
    body = response.fail.replace("{target}", target.label)
    world.say(f"{parent.label_word.capitalize()} came running and {body}.")
    world.say(
        f"But the flames skipped from {target.the} to the boxes and blankets nearby. Crackle-crack! Smoke rolled high."
    )


def escape_and_loss(world: World, parent: Entity, captain: Entity, mate: Entity) -> None:
    for kid in (captain, mate):
        kid.memes["fear"] += 1
        kid.memes["sadness"] += 1
    world.say(
        f"{parent.label_word.capitalize()} scooped the children up and hurried them outside into the cool air."
    )
    world.say(
        "From the doorstep they watched firelight flicker in the windows, and the crumpet feast was gone before it had begun."
    )


def grim_lesson(world: World, parent: Entity, captain: Entity, mate: Entity, forbidden: Forbidden) -> None:
    for kid in (captain, mate):
        kid.memes["relief"] += 1
        kid.memes["lesson"] += 1
        kid.memes["love"] += 1
    world.say(
        f'{parent.label_word.capitalize()} hugged them on the path outside. "You are safe, and that is what matters most," {parent.pronoun()} whispered.'
    )
    world.say(
        f"But the pirates never forgot the smoky rhyme of that day: {forbidden.warning}, and one silly spark can steal play away."
    )


def tell(
    theme: Theme,
    forbidden: Forbidden,
    target: Target,
    safe_fix: SafeFix,
    response: Response,
    captain_name: str = "Tom",
    captain_gender: str = "boy",
    mate_name: str = "Lily",
    mate_gender: str = "girl",
    trait: str = "careful",
    parent_type: str = "mother",
    delay: int = 0,
    captain_age: int = 6,
    mate_age: int = 4,
    relation: str = "siblings",
    trust: int = 6,
) -> World:
    world = World()
    captain = world.add(Entity(
        id=captain_name,
        kind="character",
        type=captain_gender,
        role="captain",
        age=captain_age,
        attrs={"relation": relation},
        traits=["bold"],
    ))
    mate = world.add(Entity(
        id=mate_name,
        kind="character",
        type=mate_gender,
        role="mate",
        age=mate_age,
        attrs={"relation": relation},
        traits=[trait],
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    room = world.add(Entity(id="room", type="room", label="the room"))
    crumpet = world.add(Entity(
        id="crumpet",
        type="food",
        label="crumpet",
        phrase="a crumpet on a little plate",
        edible=True,
    ))
    tool = world.add(Entity(
        id="tool",
        type="tool",
        label=forbidden.label,
        makes_flame=True,
    ))
    target_ent = world.add(Entity(
        id="target",
        type="cloth",
        label=target.label,
        flammable=target.flammable,
    ))
    heater = world.add(Entity(
        id="heater",
        type="heater",
        label=safe_fix.label,
        safe_heat=True,
    ))

    captain.memes["bravery"] = BRAVERY_INIT
    mate.memes["trust"] = float(trust)
    mate.memes["caution"] = initial_caution(trait)
    crumpet.memes["desired"] = 1.0
    room.meters["calm"] = 1.0

    play_setup(world, captain, mate, theme)
    dark_need(world, mate, theme, target)

    world.para()
    tempt(world, captain, forbidden)
    warn(world, mate, captain, forbidden, target, parent)

    averted = would_avert(relation, captain_age, mate_age, trait)
    if averted:
        back_down(world, captain, mate, forbidden, parent, theme)
        world.para()
        safe_feast(world, parent, captain, mate, theme, safe_fix)
        severity = 0
        contained = True
    else:
        defy(world, captain, mate, forbidden)

        world.para()
        ignite(world, forbidden, target)
        alarm(world, mate, captain, target, parent)

        severity = fire_severity(target, delay)
        target_ent.meters["severity"] = float(severity)
        contained = is_contained(response, target, delay)

        world.para()
        if contained:
            rescue(world, parent, response, target)
            lesson(world, parent, captain, mate, forbidden)
            world.para()
            safe_feast(world, parent, captain, mate, theme, safe_fix)
        else:
            rescue_fail(world, parent, response, target)
            escape_and_loss(world, parent, captain, mate)
            grim_lesson(world, parent, captain, mate, forbidden)

    outcome = "averted" if averted else ("contained" if contained else "burned")
    world.facts.update(
        theme=theme,
        forbidden=forbidden,
        target_cfg=target,
        safe_fix=safe_fix,
        response=response,
        captain=captain,
        mate=mate,
        parent=parent,
        crumpet=crumpet,
        room=room,
        relation=relation,
        ignited=target_ent.meters["scorched"] >= THRESHOLD,
        severity=severity,
        delay=delay,
        outcome=outcome,
    )
    return world


THEMES = {
    "galley": Theme(
        id="galley",
        scene="a creaky pirate galley",
        rig="The sofa was the stern, a laundry basket was the bow, and a striped sheet hung like a grand sail.",
        titles=("Captain", "First Mate"),
        snack_name="a treasure crumpet from the captain's chest",
        dark_spot="the pretend galley corner",
        voyage_line="They marched away from the spark and told a grown-up about their hungry pirate plan.",
        ending_line="Then the little crew clapped in a row and sang, \"Safe to toast and safe to play, that is the pirate way!\"",
        rhyme_tag="play/way",
    ),
    "cabin": Theme(
        id="cabin",
        scene="a stormy pirate cabin",
        rig="A blanket over two chairs made the cabin roof, and a broom across the backs looked like a mast in spray.",
        titles=("Captain", "Mate"),
        snack_name="a round sea biscuit for brave sailors",
        dark_spot="the snug cabin nook",
        voyage_line="They left the flame where it belonged and went to fetch a grown-up instead.",
        ending_line="Then they drummed the table low and sang, \"Warm with care and bright with cheer, safe toast tastes best right here!\"",
        rhyme_tag="cheer/here",
    ),
    "harbor": Theme(
        id="harbor",
        scene="a bustling pirate harbor",
        rig="A line of cushions became the dock, a cardboard box became the ship, and a dish towel flapped like a harbor flag.",
        titles=("Captain", "Lookout"),
        snack_name="a harbor bun for hungry raiders",
        dark_spot="the shadowy harbor hold",
        voyage_line="The would-be raiders decided a grown-up cook was better than a pirate spark.",
        ending_line="Then they tapped their spoons and crowed, \"Toast it slow and toast it right, no sneaky flame in pirate night!\"",
        rhyme_tag="right/night",
    ),
}

FORBIDDEN = {
    "candle": Forbidden(
        id="candle",
        cry="A candle!",
        label="the candle",
        phrase="a candle",
        where="on the mantel",
        flare="The candle flame",
        strike="Fwick!",
        warning="candles are not for children to play with",
        plural=False,
        tags={"candle", "fire", "call_adult"},
    ),
    "lighter": Forbidden(
        id="lighter",
        cry="A lighter!",
        label="the lighter",
        phrase="a lighter",
        where="by the fruit bowl",
        flare="The little flame",
        strike="Click!",
        warning="lighters are not for children to play with",
        plural=False,
        tags={"lighter", "fire", "call_adult"},
    ),
    "matches": Forbidden(
        id="matches",
        cry="Matches!",
        label="matches",
        phrase="the box of matches",
        where="in the kitchen drawer",
        flare="The first match",
        strike="Scritch!",
        warning="matches are not for children to play with",
        plural=True,
        tags={"matches", "fire", "call_adult"},
    ),
}

TARGETS = {
    "tea_towel": Target(
        id="tea_towel",
        label="tea towel",
        the="the tea towel",
        near="the edge of the tea towel",
        detail="where a tea towel drooped over the side",
        spread=2,
        flammable=True,
        tags={"cloth", "tea_towel"},
    ),
    "sheet_sail": Target(
        id="sheet_sail",
        label="sheet sail",
        the="the sheet sail",
        near="the hem of the sheet sail",
        detail="where the pretend sail hung low",
        spread=3,
        flammable=True,
        tags={"cloth", "sheet"},
    ),
    "flag": Target(
        id="flag",
        label="dish-towel flag",
        the="the dish-towel flag",
        near="the corner of the dish-towel flag",
        detail="where the little harbor flag fluttered",
        spread=2,
        flammable=True,
        tags={"cloth", "flag"},
    ),
    "stone_hearth": Target(
        id="stone_hearth",
        label="stone hearth",
        the="the stone hearth",
        near="the cool stone",
        detail="beside the stone hearth",
        spread=0,
        flammable=False,
        tags={"stone"},
    ),
}

SAFE_FIXES = {
    "toaster": SafeFix(
        id="toaster",
        label="toaster",
        phrase="the toaster",
        heat_word="toasty and golden",
        tags={"toaster", "safe_heat"},
    ),
    "oven": SafeFix(
        id="oven",
        label="oven",
        phrase="the warm oven tray",
        heat_word="warm and soft",
        tags={"oven", "safe_heat"},
    ),
}

RESPONSES = {
    "extinguisher": Response(
        id="extinguisher",
        sense=3,
        power=4,
        text="grabbed the fire extinguisher and sprayed the flames until every bright tongue was gone",
        fail="used the fire extinguisher, but the flames had already spread too far",
        qa_text="put the flames out with the fire extinguisher",
        tags={"extinguisher", "fire"},
    ),
    "smother": Response(
        id="smother",
        sense=3,
        power=3,
        text="snatched the {target} down and smothered the flames under a heavy pan lid",
        fail="tried to smother the burning {target}, but fire had already raced beyond it",
        qa_text="smothered the burning cloth before the fire could spread",
        tags={"smother", "fire"},
    ),
    "pan": Response(
        id="pan",
        sense=1,
        power=1,
        text="banged at the flames with a pan until they gave up",
        fail="waved a pan at the flames, but the fire only jumped higher",
        qa_text="hit at the flames with a pan",
        tags={"pan", "fire"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["careful", "cautious", "steady", "sensible", "clever", "thoughtful"]


@dataclass
class StoryParams:
    theme: str
    forbidden: str
    target: str
    safe_fix: str
    response: str
    captain: str
    captain_gender: str
    mate: str
    mate_gender: str
    parent: str
    trait: str
    delay: int = 0
    captain_age: int = 6
    mate_age: int = 4
    relation: str = "siblings"
    trust: int = 6
    seed: Optional[int] = None


KNOWLEDGE = {
    "crumpet": [(
        "What is a crumpet?",
        "A crumpet is a small round bread with tiny holes on top. People often toast it and eat it warm."
    )],
    "matches": [(
        "What are matches?",
        "Matches are little sticks that make a real flame when you scratch them. They are not for children to play with."
    )],
    "lighter": [(
        "What is a lighter?",
        "A lighter is a small tool that makes a flame. Children should never use one."
    )],
    "candle": [(
        "Why can a candle be dangerous?",
        "A candle has a real flame. If the flame touches cloth or paper, it can start a fire."
    )],
    "cloth": [(
        "Why can cloth catch fire quickly?",
        "Many cloth things are thin and dry, so flame can spread across them fast. That is why cloth should stay far from fire."
    )],
    "call_adult": [(
        "What should a child do if something starts to burn?",
        "Move away and call a grown-up right away. Getting help fast is the safe and brave thing to do."
    )],
    "extinguisher": [(
        "What does a fire extinguisher do?",
        "A fire extinguisher sprays out material that helps put a fire out. It is a grown-up safety tool."
    )],
    "smother": [(
        "What does it mean to smother a small fire?",
        "To smother a fire means to cover it so it cannot keep burning. A grown-up can do that with the right safe object."
    )],
    "toaster": [(
        "What does a toaster do?",
        "A toaster warms bread safely from the inside of the machine. It is made for toasting food, not for playing."
    )],
    "oven": [(
        "What is an oven for?",
        "An oven is for cooking or warming food safely with a grown-up's help. It is not a toy."
    )],
}
KNOWLEDGE_ORDER = [
    "crumpet",
    "matches",
    "lighter",
    "candle",
    "cloth",
    "call_adult",
    "extinguisher",
    "smother",
    "toaster",
    "oven",
]


def pair_noun(captain: Entity, mate: Entity, relation: str) -> str:
    if relation == "siblings":
        if captain.type == "boy" and mate.type == "boy":
            return "two brothers"
        if captain.type == "girl" and mate.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    captain = f["captain"]
    mate = f["mate"]
    theme = f["theme"]
    forbidden = f["forbidden"]
    target = f["target_cfg"]
    safe_fix = f["safe_fix"]
    outcome = f["outcome"]
    base = (
        f'Write a pirate-play story for a 3-to-5-year-old that includes the words "crumpet" and "hallelujahs", '
        f'uses sound effects and light rhyme, and has children tempted to warm food with {forbidden.label}.'
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a gentle cautionary rhyme where {captain.id} wants to toast a crumpet with {forbidden.label}, but {mate.id} warns about {target.the} and stops the mistake before any fire starts.",
            f"Write a tiny pirate tale with little sound effects, a safe ending, and a grown-up who uses {safe_fix.label} instead of a flame.",
        ]
    if outcome == "burned":
        return [
            base,
            f"Tell a sad cautionary pirate rhyme where {captain.id} ignores {mate.id}, {target.the} catches, and the family must hurry outside safely while losing the pirate feast.",
            f"Write a smoky warning story that still stays child-facing: include a crumpet, a pirate game, and the lesson that {forbidden.warning}.",
        ]
    return [
        base,
        f"Tell a pirate rhyme where {captain.id} tries to warm a crumpet with {forbidden.label}, {target.the} catches fire, and a calm grown-up puts it out.",
        f"Write a child-facing cautionary story with sound effects, a pirate snack, and a happy ending where the crumpet is toasted safely in {safe_fix.label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    captain = f["captain"]
    mate = f["mate"]
    parent = f["parent"]
    theme = f["theme"]
    forbidden = f["forbidden"]
    target = f["target_cfg"]
    response = f["response"]
    safe_fix = f["safe_fix"]
    pair = pair_noun(captain, mate, f["relation"])
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {captain.id} and {mate.id}, who were playing pirates indoors. It also includes their {pw}, who helped when the snack plan turned risky."
        ),
        (
            "What treasure did the children find?",
            "They found a crumpet and treated it like pirate treasure for a feast. Their hunger is what made the unsafe idea feel exciting."
        ),
        (
            f"Why did {mate.id} warn {captain.id}?",
            f"{mate.id} knew that {forbidden.label} could make a real flame near {target.the}. {mate.pronoun().capitalize()} could already imagine smoke and danger if the spark jumped to the cloth."
        ),
    ]
    if f["outcome"] == "averted":
        qa.append((
            f"What happened after the warning?",
            f"{captain.id} backed down before lighting anything, so no fire started at all. Instead, they asked their {pw} to warm the crumpet the proper way."
        ))
        qa.append((
            "How did the story end?",
            f"It ended safely with the crumpet warmed in {safe_fix.label}. The children got their pirate feast and shouted little hallelujahs because they chose the safer plan."
        ))
    elif f["outcome"] == "contained":
        qa.append((
            f"What happened when {captain.id} used {forbidden.label}?",
            f"{target.The} caught fire, and the room suddenly felt scary. The danger began because a real flame touched something that could burn."
        ))
        qa.append((
            f"How did the {pw} help?",
            f"{pw.capitalize()} came quickly and {response.qa_text.replace('{target}', target.label)}. That fast response stopped the fire before it could take over the room."
        ))
        qa.append((
            "What changed by the end?",
            f"At first the children wanted a sneaky pirate spark, but by the end they wanted safe toast instead. Their {pw} used {safe_fix.label}, and the crumpet became a happy treat instead of a danger."
        ))
    else:
        qa.append((
            f"Could the {pw} stop the fire in time?",
            f"No. {pw.capitalize()} tried, but the flames spread beyond {target.the} and the family had to run outside to stay safe. The fire had grown too big for that response."
        ))
        qa.append((
            "How did the story end?",
            "It ended sadly but safely: the children got out, but their pirate game and crumpet feast were lost. The ending shows how one careless flame can ruin a happy plan."
        ))
        qa.append((
            f"What lesson did {captain.id} and {mate.id} learn?",
            f"They learned that {forbidden.warning}. They also learned that asking a grown-up for safe help is much better than pretending a dangerous tool is part of the game."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"crumpet", "cloth"}
    tags |= set(f["forbidden"].tags)
    if f["outcome"] == "contained":
        tags |= set(f["response"].tags) | set(f["safe_fix"].tags)
    elif f["outcome"] == "burned":
        tags |= set(f["response"].tags)
    else:
        tags |= set(f["safe_fix"].tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        flags = [n for n, on in (
            ("flammable", e.flammable),
            ("makes_flame", e.makes_flame),
            ("safe_heat", e.safe_heat),
            ("edible", e.edible),
        ) if on]
        if flags:
            bits.append(f"flags={flags}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for theme_id in THEMES:
        for forbidden_id, forbidden in FORBIDDEN.items():
            for target_id, target in TARGETS.items():
                if hazard_at_risk(forbidden, target):
                    combos.append((theme_id, forbidden_id, target_id))
    return combos


def explain_rejection(forbidden: Forbidden, target: Target) -> str:
    if not target.flammable:
        return (
            f"(No story: {forbidden.label} can make a flame, but {target.the} will not catch. "
            f"No fire means no cautionary turn here; choose a cloth target like tea_towel or sheet_sail.)"
        )
    return "(No story: this combination does not create a fire risk.)"


def explain_response(response_id: str) -> str:
    response = RESPONSES[response_id]
    better = ", ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{response_id}': it scores too low on common sense "
        f"(sense={response.sense} < {SENSE_MIN}). Try a safer response such as {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.captain_age, params.mate_age, params.trait):
        return "averted"
    return "contained" if is_contained(RESPONSES[params.response], TARGETS[params.target], params.delay) else "burned"


ASP_RULES = r"""
hazard(F, Tg) :- makes_flame(F), flammable(Tg).
sensible(R)   :- response(R), sense(R, S), sense_min(M), S >= M.
valid(T, F, Tg) :- theme(T), forbidden(F), target(Tg), hazard(F, Tg).

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
mate_older :- relation(siblings), captain_age(CA), mate_age(MA), MA > CA.
bonus(4) :- mate_older.
bonus(0) :- not mate_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- mate_older, authority(A), bravery_init(BR), A > BR.

severity(Sp + D) :- chosen_target(Tg), spread(Tg, Sp), delay(D).
resp_power(P) :- chosen_response(R), power(R, P).
contained :- resp_power(P), severity(V), P >= V.

outcome(averted) :- averted.
outcome(contained) :- not averted, contained.
outcome(burned) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for theme_id in THEMES:
        lines.append(asp.fact("theme", theme_id))
    for forbidden_id, forbidden in FORBIDDEN.items():
        lines.append(asp.fact("forbidden", forbidden_id))
        if forbidden.makes_flame:
            lines.append(asp.fact("makes_flame", forbidden_id))
    for target_id, target in TARGETS.items():
        lines.append(asp.fact("target", target_id))
        lines.append(asp.fact("spread", target_id, target.spread))
        if target.flammable:
            lines.append(asp.fact("flammable", target_id))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        lines.append(asp.fact("power", response_id, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_target", params.target),
        asp.fact("chosen_response", params.response),
        asp.fact("delay", params.delay),
        asp.fact("relation", params.relation),
        asp.fact("captain_age", params.captain_age),
        asp.fact("mate_age", params.mate_age),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


CURATED = [
    StoryParams(
        theme="galley",
        forbidden="matches",
        target="sheet_sail",
        safe_fix="toaster",
        response="extinguisher",
        captain="Tom",
        captain_gender="boy",
        mate="Lily",
        mate_gender="girl",
        parent="mother",
        trait="careful",
        delay=0,
        captain_age=6,
        mate_age=4,
        relation="siblings",
        trust=7,
    ),
    StoryParams(
        theme="cabin",
        forbidden="lighter",
        target="tea_towel",
        safe_fix="oven",
        response="smother",
        captain="Mia",
        captain_gender="girl",
        mate="Ben",
        mate_gender="boy",
        parent="father",
        trait="thoughtful",
        delay=0,
        captain_age=5,
        mate_age=5,
        relation="friends",
        trust=4,
    ),
    StoryParams(
        theme="harbor",
        forbidden="candle",
        target="flag",
        safe_fix="toaster",
        response="smother",
        captain="Sam",
        captain_gender="boy",
        mate="Zoe",
        mate_gender="girl",
        parent="mother",
        trait="cautious",
        delay=2,
        captain_age=6,
        mate_age=4,
        relation="siblings",
        trust=5,
    ),
    StoryParams(
        theme="galley",
        forbidden="lighter",
        target="sheet_sail",
        safe_fix="oven",
        response="extinguisher",
        captain="Finn",
        captain_gender="boy",
        mate="Theo",
        mate_gender="boy",
        parent="father",
        trait="careful",
        delay=0,
        captain_age=5,
        mate_age=7,
        relation="siblings",
        trust=3,
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: pirate play, a crumpet, a forbidden flame, and a safer way to toast."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--forbidden", choices=FORBIDDEN)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--safe-fix", dest="safe_fix", choices=SAFE_FIXES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner against the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.target and not TARGETS[args.target].flammable:
        forbidden = FORBIDDEN[args.forbidden] if args.forbidden else next(iter(FORBIDDEN.values()))
        raise StoryError(explain_rejection(forbidden, TARGETS[args.target]))
    if args.forbidden and args.target:
        forbidden = FORBIDDEN[args.forbidden]
        target = TARGETS[args.target]
        if not hazard_at_risk(forbidden, target):
            raise StoryError(explain_rejection(forbidden, target))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo for combo in valid_combos()
        if (args.theme is None or combo[0] == args.theme)
        and (args.forbidden is None or combo[1] == args.forbidden)
        and (args.target is None or combo[2] == args.target)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme_id, forbidden_id, target_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    safe_fix_id = args.safe_fix or rng.choice(sorted(SAFE_FIXES.keys()))
    captain_name, captain_gender = _pick_kid(rng)
    mate_name, mate_gender = _pick_kid(rng, avoid=captain_name)
    relation = rng.choice(["siblings", "friends"])
    captain_age, mate_age = rng.sample([3, 4, 5, 6, 7], 2)
    return StoryParams(
        theme=theme_id,
        forbidden=forbidden_id,
        target=target_id,
        safe_fix=safe_fix_id,
        response=response_id,
        captain=captain_name,
        captain_gender=captain_gender,
        mate=mate_name,
        mate_gender=mate_gender,
        parent=args.parent or rng.choice(["mother", "father"]),
        trait=rng.choice(TRAITS),
        delay=args.delay if args.delay is not None else rng.randint(0, 2),
        captain_age=captain_age,
        mate_age=mate_age,
        relation=relation,
        trust=rng.randint(0, 10),
    )


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES:
        raise StoryError(f"(Invalid theme: {params.theme})")
    if params.forbidden not in FORBIDDEN:
        raise StoryError(f"(Invalid forbidden tool: {params.forbidden})")
    if params.target not in TARGETS:
        raise StoryError(f"(Invalid target: {params.target})")
    if params.safe_fix not in SAFE_FIXES:
        raise StoryError(f"(Invalid safe fix: {params.safe_fix})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Invalid response: {params.response})")
    forbidden = FORBIDDEN[params.forbidden]
    target = TARGETS[params.target]
    if not hazard_at_risk(forbidden, target):
        raise StoryError(explain_rejection(forbidden, target))
    if RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        theme=THEMES[params.theme],
        forbidden=forbidden,
        target=target,
        safe_fix=SAFE_FIXES[params.safe_fix],
        response=RESPONSES[params.response],
        captain_name=params.captain,
        captain_gender=params.captain_gender,
        mate_name=params.mate,
        mate_gender=params.mate_gender,
        trait=params.trait,
        parent_type=params.parent,
        delay=params.delay,
        captain_age=params.captain_age,
        mate_age=params.mate_age,
        relation=params.relation,
        trust=params.trust,
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

    py_sensible = {r.id for r in sensible_responses()}
    asp_sens = set(asp_sensible())
    if py_sensible == asp_sens:
        print(f"OK: sensible responses match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(asp_sens)} python={sorted(py_sensible)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(80):
        try:
            args = parser.parse_args([])
            params = resolve_params(args, random.Random(seed))
            cases.append(params)
        except StoryError:
            continue
    bad = sum(1 for params in cases if asp_outcome(params) != outcome_of(params))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: generated story was empty.)")
        print("OK: smoke test story generation passed.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (theme, forbidden, target) combos:\n")
        for theme_id, forbidden_id, target_id in combos:
            print(f"  {theme_id:8} {forbidden_id:8} {target_id}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            params = sample.params
            header = (
                f"### {params.captain} & {params.mate}: {params.forbidden} near "
                f"{params.target} ({params.theme}, {params.response}, {outcome_of(params)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
