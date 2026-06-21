#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/monopoly_consistency_adventure_magic_comedy.py
=========================================================================

A standalone story world about a magical board-game afternoon: one child tries
to grab a silly little monopoly on the game's treats by using magic for an
unfair shortcut, the board loses consistency in a funny way, and a calmer helper
and grown-up restore the rules so the adventure can continue.

Run it
------
    python storyworlds/worlds/gpt-5.4/monopoly_consistency_adventure_magic_comedy.py
    python storyworlds/worlds/gpt-5.4/monopoly_consistency_adventure_magic_comedy.py --adventure moon_market --spell copy_coins --glitch arguing_bank
    python storyworlds/worlds/gpt-5.4/monopoly_consistency_adventure_magic_comedy.py --glitch melting_map
    python storyworlds/worlds/gpt-5.4/monopoly_consistency_adventure_magic_comedy.py --fix wish_harder
    python storyworlds/worlds/gpt-5.4/monopoly_consistency_adventure_magic_comedy.py --all
    python storyworlds/worlds/gpt-5.4/monopoly_consistency_adventure_magic_comedy.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/monopoly_consistency_adventure_magic_comedy.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
BOLDNESS_INIT = 6.0
CAREFUL_TRAITS = {"careful", "orderly", "patient", "sensible"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    magical: bool = False
    movable: bool = True
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Adventure:
    id: str
    scene: str
    props: str
    route: str
    goal: str
    snack_prize: str
    opening_image: str
    ending_image: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Spell:
    id: str
    label: str
    phrase: str
    exclaim: str
    claim: str
    action: str
    lesson: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Glitch:
    id: str
    label: str
    board_part: str
    chaos_text: str
    qa_text: str
    severity: int = 1
    magical: bool = True
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Fix:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


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
        return [e for e in self.entities.values() if e.role in {"instigator", "helper"}]

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
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_inconsistency(world: World) -> list[str]:
    out: list[str] = []
    board = world.get("board")
    for ent in list(world.entities.values()):
        if ent.meters["glitched"] < THRESHOLD:
            continue
        sig = ("inconsistency", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        board.meters["inconsistency"] += 1
        for kid in world.kids():
            kid.memes["surprise"] += 1
        out.append("__glitch__")
    return out


def _r_chaos(world: World) -> list[str]:
    board = world.get("board")
    room = world.get("room")
    if board.meters["inconsistency"] < THRESHOLD:
        return []
    sig = ("chaos",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    room.meters["chaos"] += 1
    for kid in world.kids():
        kid.memes["wobble"] += 1
    return ["__chaos__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="inconsistency", tag="physical", apply=_r_inconsistency),
    Rule(name="chaos", tag="physical", apply=_r_chaos),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


def compatible(spell: Spell, glitch: Glitch) -> bool:
    matrix = {
        "double_dice": {"runaway_token", "duplicate_squares"},
        "pocket_portal": {"runaway_token", "duplicate_squares"},
        "copy_coins": {"arguing_bank", "duplicate_squares"},
    }
    return glitch.id in matrix.get(spell.id, set())


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= SENSE_MIN]


def glitch_pressure(glitch: Glitch, delay: int) -> int:
    return glitch.severity + delay


def is_restored(fix: Fix, glitch: Glitch, delay: int) -> bool:
    return fix.power >= glitch_pressure(glitch, delay)


def initial_care(trait: str) -> float:
    return 5.0 if trait in CAREFUL_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, helper_age: int, trait: str) -> bool:
    helper_older = relation == "siblings" and helper_age > instigator_age
    authority = (initial_care(trait) + 1.0) + (4.0 if helper_older else 0.0)
    return helper_older and authority > BOLDNESS_INIT


def predict_glitch(world: World, glitch_id: str) -> dict:
    sim = world.copy()
    trigger_magic(sim, sim.get("glitch"), narrate=False)
    return {
        "inconsistency": sim.get("board").meters["inconsistency"],
        "chaos": sim.get("room").meters["chaos"],
    }


def introduce(world: World, a: Entity, b: Entity, adv: Adventure) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"On a rainy afternoon, {a.id} and {b.id} spread a board game across the rug and turned the room into {adv.scene}. "
        f"{adv.props}"
    )
    world.say(
        f"To them, it was not just a game. It was an adventure, and {adv.opening_image}"
    )
    world.say(
        f'"First one to {adv.goal} wins the {adv.snack_prize}!" {a.id} announced.'
    )


def explain_rules(world: World, b: Entity, adv: Adventure) -> None:
    world.say(
        f"{b.id} lined up the little tokens beside {adv.route} and said, "
        f'"If we want this adventure to stay fun, we need consistency. One turn each, and the board gets to tell the truth."'
    )


def tempt(world: World, a: Entity, spell: Spell) -> None:
    a.memes["greed"] += 1
    world.say(
        f"{a.id}'s eyes grew round. {spell.exclaim} "
        f'"With {spell.phrase}, I could {spell.claim}!"'
    )
    world.say(
        f"For one silly second, a tiny {a.id.lower()}-sized monopoly sounded like the best idea in the world."
    )


def warn(world: World, b: Entity, a: Entity, spell: Spell, glitch: Glitch, guide: Entity) -> None:
    pred = predict_glitch(world, glitch.id)
    b.memes["care"] += 1
    world.facts["predicted_inconsistency"] = pred["inconsistency"]
    world.facts["predicted_chaos"] = pred["chaos"]
    world.say(
        f'{b.id} leaned closer. "{a.id}, magic is real in this house, and that is exactly why we have to be careful," '
        f'{b.pronoun()} said. "If you use {spell.label} to skip the rules, {glitch.board_part} could go funny, and then the whole board might lose consistency."'
    )
    if pred["chaos"] >= THRESHOLD:
        world.say(
            f'{guide.label_word.capitalize()} had said the same thing before: "Fast tricks make slow messes." {b.id} remembered every word.'
        )


def back_down(world: World, a: Entity, b: Entity, spell: Spell, guide: Entity) -> None:
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    a.memes["boldness"] = 0.0
    world.say(
        f'{a.id} puffed out {a.pronoun("possessive")} cheeks, then laughed at {a.pronoun("object")}self. '
        f'"A crooked win would be a boring monopoly anyway," {a.pronoun()} said.'
    )
    world.say(
        f"They put {spell.label} back on the shelf and called for {guide.label_word}, just to ask for a fair way to make the game feel magical without bending it."
    )


def defy(world: World, a: Entity, b: Entity, spell: Spell) -> None:
    a.memes["defiance"] += 1
    if a.attrs.get("relation") == "siblings" and a.age > b.age:
        world.say(
            f'"Relax," {a.id} said. "I will only use one tiny sparkle." Then {a.pronoun()} wiggled {a.pronoun("possessive")} fingers before {b.id} could stop {a.pronoun("object")}.'
        )
    else:
        world.say(
            f'"Relax," {a.id} said. "I will only use one tiny sparkle." Then {a.pronoun()} cast the spell anyway.'
        )


def trigger_magic(world: World, glitch_ent: Entity, narrate: bool = True) -> None:
    glitch_ent.meters["glitched"] += 1
    glitch_ent.meters["sparkles"] += 1
    propagate(world, narrate=narrate)


def glitch_happens(world: World, spell: Spell, glitch: Glitch) -> None:
    trigger_magic(world, world.get("glitch"))
    world.say(
        f"{spell.action}. At first it looked wonderful. Then {glitch.chaos_text}"
    )


def alarm(world: World, b: Entity, a: Entity, glitch: Glitch, guide: Entity) -> None:
    world.say(
        f'"{a.id}! Look!" {b.id} yelped. "{glitch.board_part.capitalize()} is wrong now!"'
    )
    world.say(f'"{guide.label_word.upper()}!"')


def repair(world: World, guide: Entity, fix: Fix, a: Entity, b: Entity, adv: Adventure) -> None:
    world.get("glitch").meters["glitched"] = 0.0
    world.get("board").meters["inconsistency"] = 0.0
    world.get("room").meters["chaos"] = 0.0
    for kid in (a, b):
        kid.memes["relief"] += 1
        kid.memes["fairness"] += 1
        kid.memes["embarrassment"] += 1 if kid.role == "instigator" else 0.0
    world.say(
        f"{guide.label_word.capitalize()} came in smiling, saw the wobbling board, and {fix.text}."
    )
    world.say(
        f'The little streets settled down, the tokens faced the right way again, and even the cardboard banker looked less offended.'
    )
    world.say(
        f'"Magic is most helpful when it keeps the game honest," {guide.label_word} said. "No one needs a monopoly on the fun."'
    )
    world.say(
        f"After that, the turns moved neatly along {adv.route}, and the room felt calm enough for giggles instead of gasps."
    )


def repair_fail(world: World, guide: Entity, fix: Fix, glitch: Glitch) -> None:
    world.get("room").meters["chaos"] += 1
    world.get("board").meters["inconsistency"] += 1
    world.say(
        f"{guide.label_word.capitalize()} hurried in and {fix.fail}."
    )
    world.say(
        f"Instead, {glitch.board_part} got sillier, and the board tried to invent three Tuesdays at once."
    )


def comic_escape(world: World, guide: Entity, a: Entity, b: Entity) -> None:
    for kid in (a, b):
        kid.memes["surprise"] += 1
        kid.memes["relief"] += 1
    world.say(
        f"There was nothing dangerous about it, but it was impossible to keep playing. {guide.label_word.capitalize()} scooped up the dice, the children scooped up the snack bowl, and everybody retreated to the sofa while the board hiccuped glitter onto the rug."
    )
    world.say(
        "Soon they were laughing too hard to be upset, especially when one fake street tried to charge rent to a pillow."
    )


def lesson(world: World, guide: Entity, a: Entity, b: Entity, spell: Spell) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["love"] += 1
    world.say(
        f'{guide.label_word.capitalize()} sat with them and tapped the box lid. "A game can have magic and still need consistency," {guide.pronoun()} said gently. "{spell.lesson}"'
    )
    world.say(f'"We know," {b.id} and {a.id} said together.')
    if world.facts.get("mascot"):
        world.say(f'Even {world.facts["mascot"]} sat beside the board as if listening to the rules.')


def fair_finish(world: World, guide: Entity, a: Entity, b: Entity, adv: Adventure) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"The next round was slow in the best way. One roll, one move, one laugh, and then another."
    )
    world.say(
        f"When they finally reached {adv.goal}, they split the {adv.snack_prize} right down the middle."
    )
    world.say(
        f"{adv.ending_image} It was still an adventure, only now it was fair enough to feel bright."
    )


def runaway_finish(world: World, guide: Entity, a: Entity, b: Entity, adv: Adventure) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["love"] += 1
    world.say(
        f'{guide.label_word.capitalize()} turned the glimmering board box upside down over the mess, muttered a stronger bedtime spell, and at last the extra streets folded away like sleepy paper.'
    )
    world.say(
        f'"No more magical shortcuts tonight," {guide.pronoun()} said. So {a.id} and {b.id} built {adv.scene} from sofa cushions instead and shared the {adv.snack_prize} there, laughing whenever someone said the word "consistency" in a very serious voice.'
    )


def tell(
    adv: Adventure,
    spell: Spell,
    glitch: Glitch,
    fix: Fix,
    instigator: str = "Milo",
    instigator_gender: str = "boy",
    helper: str = "Tess",
    helper_gender: str = "girl",
    trait: str = "careful",
    guide_type: str = "aunt",
    delay: int = 0,
    instigator_age: int = 6,
    helper_age: int = 4,
    relation: str = "siblings",
    trust: int = 6,
    snack: str = "",
    mascot: str = "",
) -> World:
    world = World()
    a = world.add(Entity(
        id=instigator,
        kind="character",
        type=instigator_gender,
        role="instigator",
        age=instigator_age,
        traits=["bold"],
        attrs={"relation": relation},
    ))
    b = world.add(Entity(
        id=helper,
        kind="character",
        type=helper_gender,
        role="helper",
        age=helper_age,
        traits=[trait],
        attrs={"relation": relation},
    ))
    guide = world.add(Entity(
        id="Guide",
        kind="character",
        type=guide_type,
        role="guide",
        label="the grown-up",
    ))
    board = world.add(Entity(
        id="board",
        type="board",
        label="the board",
        magical=True,
        movable=False,
    ))
    room = world.add(Entity(
        id="room",
        type="room",
        label="the room",
        movable=False,
    ))
    glitch_ent = world.add(Entity(
        id="glitch",
        type="glitch",
        label=glitch.label,
        magical=True,
    ))

    a.memes["boldness"] = BOLDNESS_INIT
    b.memes["trust"] = float(trust)
    b.memes["care"] = initial_care(trait)
    world.facts["mascot"] = mascot
    world.facts["snack_override"] = snack

    introduce(world, a, b, adv)
    explain_rules(world, b, adv)

    world.para()
    tempt(world, a, spell)
    warn(world, b, a, spell, glitch, guide)

    averted = would_avert(relation, instigator_age, helper_age, trait)

    if averted:
        back_down(world, a, b, spell, guide)
        world.para()
        lesson(world, guide, a, b, spell)
        fair_finish(world, guide, a, b, adv)
        pressure = 0
        restored = True
    else:
        defy(world, a, b, spell)
        world.para()
        glitch_happens(world, spell, glitch)
        alarm(world, b, a, glitch, guide)
        pressure = glitch_pressure(glitch, delay)
        restored = is_restored(fix, glitch, delay)

        world.para()
        if restored:
            repair(world, guide, fix, a, b, adv)
            lesson(world, guide, a, b, spell)
            world.para()
            fair_finish(world, guide, a, b, adv)
        else:
            repair_fail(world, guide, fix, glitch)
            comic_escape(world, guide, a, b)
            lesson(world, guide, a, b, spell)
            world.para()
            runaway_finish(world, guide, a, b, adv)

    prize_text = snack or adv.snack_prize
    outcome = "averted" if averted else ("restored" if restored else "runaway")
    world.facts.update(
        adventure=adv,
        spell=spell,
        glitch_cfg=glitch,
        fix=fix,
        instigator=a,
        helper=b,
        guide=guide,
        board=board,
        room=room,
        glitch=glitch_ent,
        outcome=outcome,
        pressure=pressure,
        relation=relation,
        prize_text=prize_text,
        glitched=glitch_ent.meters["sparkles"] >= THRESHOLD,
        promised=a.memes["lesson"] >= THRESHOLD,
        restored=restored,
        averted=averted,
    )
    return world


ADVENTURES = {
    "moon_market": Adventure(
        id="moon_market",
        scene="a moonlit market full of wobbling stalls",
        props="Silver paper became moon-money, a baking tray became the harbor, and the game path curled past tiny shops selling invisible jam buns.",
        route="the crooked market road",
        goal="the Moon Market fountain",
        snack_prize="slice-and-share cinnamon buns",
        opening_image="their elbows were mountains and their giggles were thunder over the stalls.",
        ending_image="At the end, the market road shimmered politely under the lamp, and two sticky cinnamon smiles leaned over it.",
        tags={"market", "board_game", "magic"},
    ),
    "dragon_station": Adventure(
        id="dragon_station",
        scene="a dragon train station with puffing cardboard tunnels",
        props="A shoebox became the station office, the dice cup became the tunnel mouth, and every token looked ready to catch a train with impossible luggage.",
        route="the rattly platform line",
        goal="the golden station clock",
        snack_prize="two peppermints and one extra for sharing",
        opening_image="the rug felt as long as a railway across a tiny kingdom.",
        ending_image="By the last turn, the station clock glowed over a quiet board, and the children tapped their tickets together like cheers.",
        tags={"train", "board_game", "magic"},
    ),
    "cloud_castle": Adventure(
        id="cloud_castle",
        scene="a floating castle with marshmallow towers",
        props="A pillow became the castle gate, a spoon became the silver bridge, and the board squares climbed toward a king who was plainly made from a salt shaker.",
        route="the puffy stair path",
        goal="the Cloud Castle balcony",
        snack_prize="lemon cookies from the treasure tin",
        opening_image="the lamp above them looked exactly like a patient moon watching the game.",
        ending_image="Soon the stair path lay smooth again, and two cookie crumbs rested like tiny flags beside the castle.",
        tags={"castle", "board_game", "magic"},
    ),
}

SPELLS = {
    "double_dice": Spell(
        id="double_dice",
        label="the double-dice charm",
        phrase="the double-dice charm",
        exclaim='"The double-dice charm!"',
        claim="roll twice and race ahead before anyone blinked",
        action="Blue sparkles skipped from the dice and bounced across the board like frogs",
        lesson="Magic is not for sneaking extra turns",
        tags={"dice", "fairness", "magic"},
    ),
    "pocket_portal": Spell(
        id="pocket_portal",
        label="the pocket portal spell",
        phrase="the pocket portal spell",
        exclaim='"A pocket portal!"',
        claim="hop my token right to the best square",
        action="A round purple doorway popped open over the board with a cheerful burp",
        lesson="Magic is not for skipping the road everyone else must travel",
        tags={"portal", "fairness", "magic"},
    ),
    "copy_coins": Spell(
        id="copy_coins",
        label="the copy-coins whisper",
        phrase="the copy-coins whisper",
        exclaim='"The copy-coins whisper!"',
        claim="make enough moon-money to buy every sweet stall at once",
        action="Gold paper coins fluttered upward and multiplied in the air like confused butterflies",
        lesson="Magic is not for making a pretend monopoly out of nowhere",
        tags={"coins", "fairness", "magic", "monopoly"},
    ),
}

GLITCHES = {
    "runaway_token": Glitch(
        id="runaway_token",
        label="runaway token",
        board_part="the token path",
        chaos_text="the top hat token shot forward, backward, sideways, and once somehow under the board, as if it had forgotten what a turn was",
        qa_text="The token would not stay on one honest path. It kept zipping around because the spell had bent the turn order.",
        severity=2,
        tags={"tokens", "board_game", "consistency"},
    ),
    "duplicate_squares": Glitch(
        id="duplicate_squares",
        label="duplicate squares",
        board_part="the street squares",
        chaos_text="three new street squares puffed out of nowhere between two old ones, and each one claimed to be Number Seven",
        qa_text="The board grew extra squares that did not agree with the map. Once the path had two different Number Sevens, no one could know where a move should end.",
        severity=2,
        tags={"squares", "board_game", "consistency"},
    ),
    "arguing_bank": Glitch(
        id="arguing_bank",
        label="arguing bank",
        board_part="the cardboard bank",
        chaos_text='the cardboard bank began arguing with itself in three squeaky voices about which coins were real and which ones were "only emotionally rich"',
        qa_text="The money no longer matched the real count. Because the copied coins did not belong there, the bank could not keep the game straight.",
        severity=3,
        tags={"money", "board_game", "consistency", "monopoly"},
    ),
    "melting_map": Glitch(
        id="melting_map",
        label="melting map",
        board_part="the map edge",
        chaos_text="the map edge drooped like warm cheese and forgot where the road went",
        qa_text="The map melted into nonsense, so the adventure had no trustworthy path left.",
        severity=1,
        tags={"board_game"},
    ),
}

FIXES = {
    "reset_bell": Fix(
        id="reset_bell",
        sense=3,
        power=4,
        text="rang the little brass reset bell, counted backward from five, and asked the board to remember its proper order",
        fail="rang the little brass reset bell, but the echoes only made the fake streets clap",
        qa_text="rang the reset bell and let the board settle into its proper order",
        tags={"reset", "board_game", "magic"},
    ),
    "rule_card": Fix(
        id="rule_card",
        sense=3,
        power=2,
        text="slid a clean rule card under the dice, rewound the last move, and had the children say the turns aloud together",
        fail="tried a clear rule card and a rewind, but the copied magic had already spread too far",
        qa_text="used a clear rule card, rewound the unfair move, and replayed the turn fairly",
        tags={"rules", "consistency", "fairness"},
    ),
    "counting_song": Fix(
        id="counting_song",
        sense=2,
        power=2,
        text="started a steady counting song while everyone matched each coin and square one by one",
        fail="started a counting song, but there were too many extra pieces for the song to catch",
        qa_text="used a counting song to match the pieces one by one until the game made sense again",
        tags={"counting", "consistency", "fairness"},
    ),
    "wish_harder": Fix(
        id="wish_harder",
        sense=1,
        power=1,
        text="wished even harder and blew more glitter at the board",
        fail="wished even harder, which only encouraged the board to be ridiculous",
        qa_text="wished harder at the board",
        tags={"magic"},
    ),
}

GIRL_NAMES = ["Tess", "Mina", "Lulu", "Nora", "Ivy", "Pia", "Ruby", "June", "Cora", "Wren"]
BOY_NAMES = ["Milo", "Finn", "Owen", "Leo", "Jules", "Arlo", "Ned", "Theo", "Bram", "Kit"]
TRAITS = ["careful", "orderly", "patient", "sensible", "curious", "cheerful"]
SNACKS = ["jam biscuits", "cinnamon toast squares", "butter cookies", ""]
MASCOTS = ["the sleepy cat", "the stuffed dragon", "the wind-up duck", ""]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    if not sensible_fixes():
        return combos
    for adv_id in ADVENTURES:
        for spell_id, spell in SPELLS.items():
            for glitch_id, glitch in GLITCHES.items():
                if compatible(spell, glitch):
                    combos.append((adv_id, spell_id, glitch_id))
    return combos


@dataclass
class StoryParams:
    adventure: str
    spell: str
    glitch: str
    fix: str
    instigator: str
    instigator_gender: str
    helper: str
    helper_gender: str
    guide: str
    trait: str
    delay: int = 0
    instigator_age: int = 6
    helper_age: int = 4
    relation: str = "siblings"
    trust: int = 6
    snack: str = ""
    mascot: str = ""
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


KNOWLEDGE = {
    "board_game": [
        (
            "What is a board game?",
            "A board game is a game you play by moving pieces across a board using rules. The rules help everyone know what is fair.",
        )
    ],
    "magic": [
        (
            "What is magic in a story?",
            "Magic is make-believe power that can do surprising things. In a good story, it still works best when people use it carefully.",
        )
    ],
    "fairness": [
        (
            "Why do games need fairness?",
            "Games need fairness so every player gets the same kind of chance. If one person grabs extra turns or extra money, the game stops feeling fun.",
        )
    ],
    "consistency": [
        (
            "What does consistency mean in a game?",
            "Consistency means the rules stay the same from turn to turn. When the rules keep changing, nobody can tell what should happen next.",
        )
    ],
    "monopoly": [
        (
            "What is a monopoly?",
            "A monopoly is when one person has all of something and nobody else gets a share. In a game, that can feel unfair if it comes from a trick instead of the rules.",
        )
    ],
    "portal": [
        (
            "What is a portal?",
            "A portal is a magical doorway that can take you from one place to another very fast. In stories, it is exciting, but it can also cause mix-ups.",
        )
    ],
    "dice": [
        (
            "What do dice do in a game?",
            "Dice help choose how far a player moves. Because everyone trusts the roll, changing the dice unfairly changes the game.",
        )
    ],
    "coins": [
        (
            "Why do games count coins carefully?",
            "Games count coins carefully so everyone knows how much they really have. If the count is wrong, the game can become confusing.",
        )
    ],
    "reset": [
        (
            "What does it mean to reset something?",
            "To reset something means to put it back into the right starting order. A reset can help after a mistake or a mix-up.",
        )
    ],
    "counting": [
        (
            "Why can counting help after a mix-up?",
            "Counting helps because it lets people check one thing at a time in the right order. Slow counting can fix confusion that rushing created.",
        )
    ],
    "rules": [
        (
            "Why do rules help during play?",
            "Rules help because they tell everyone what to do next. Clear rules make a game calmer and easier to enjoy.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "board_game",
    "magic",
    "fairness",
    "consistency",
    "monopoly",
    "portal",
    "dice",
    "coins",
    "reset",
    "counting",
    "rules",
]


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["instigator"]
    b = f["helper"]
    adv = f["adventure"]
    spell = f["spell"]
    glitch = f["glitch_cfg"]
    outcome = f["outcome"]
    base = (
        f'Write a funny magical story for a 3-to-5-year-old about a board-game adventure that includes the words "monopoly", "consistency", and "adventure".'
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a comedy story where {a.id} wants to use {spell.label} to win fast, but {b.id} talks {a.pronoun('object')} out of it before the board can go wrong.",
            f"Write a gentle magical story set in {adv.scene} where a child remembers that consistency matters more than a silly monopoly.",
        ]
    if outcome == "runaway":
        return [
            base,
            f"Tell a comedic cautionary story where {a.id} uses {spell.label}, {glitch.board_part} goes wrong, and the game becomes too ridiculous to keep playing until a grown-up folds the magic away.",
            f"Write a funny story in which magical cheating ruins a board game, but the ending is warm and everyone learns to share the fun.",
        ]
    return [
        base,
        f"Tell a magical comedy where {a.id} uses {spell.label}, the board loses consistency in a funny way, and a grown-up fixes it so the adventure can continue fairly.",
        f"Write a story where children learn that a monopoly on the game is less fun than sharing the turns honestly.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["helper"]
    guide = f["guide"]
    adv = f["adventure"]
    spell = f["spell"]
    glitch = f["glitch_cfg"]
    fix = f["fix"]
    pair = pair_noun(a, b, f["relation"])
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.id} and {b.id}, and their {guide.label_word} who helps when the game goes wrong.",
        ),
        (
            "What were they doing at the beginning?",
            f"They were playing a magical board game and pretending the room was {adv.scene}. The board game was their adventure for the afternoon.",
        ),
        (
            f"Why did {b.id} talk about consistency?",
            f"{b.id} wanted the turns and rules to stay the same for everybody. That mattered because the game could only feel fair if the board told the truth from move to move.",
        ),
        (
            f"Why was {a.id} tempted to use {spell.label}?",
            f"{a.id} wanted to get ahead fast and win the prize. For a moment, having a little monopoly on the treats sounded exciting, even though it would make the game unfair.",
        ),
    ]
    if f["outcome"] == "averted":
        qa.append(
            (
                f"What happened after {b.id} warned {a.id}?",
                f"{a.id} stopped before casting the spell and admitted that a crooked win would be boring. Because {b.id} spoke up in time, the board never lost consistency at all.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with fair turns, shared treats, and a calmer kind of magic. The ending shows that the adventure became better once nobody tried to grab all the fun.",
            )
        )
    elif f["outcome"] == "restored":
        qa.append(
            (
                f"What went wrong when {a.id} used the magic?",
                f"{glitch.qa_text} The shortcut broke the game because the spell tried to change something the rules were supposed to control.",
            )
        )
        qa.append(
            (
                f"How did {guide.label_word} fix the problem?",
                f"{guide.label_word.capitalize()} {fix.qa_text}. That worked because the fix put the game back into one clear order instead of letting the mixed-up magic keep spreading.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"They went back to taking fair turns and shared {f['prize_text']}. The final image proves the adventure changed from noisy cheating to happy cooperation.",
            )
        )
    else:
        qa.append(
            (
                f"Why could they not keep playing right away?",
                f"The board had become too mixed up to trust, so nobody could tell what a real turn was anymore. Even though the mess was funny instead of dangerous, the game had lost its consistency.",
            )
        )
        qa.append(
            (
                "How did the family handle the runaway magic?",
                f"They moved to the sofa, laughed together, and let the grown-up fold the extra magic away. After that, they made a new game without shortcuts, which turned the mistake into a lesson.",
            )
        )
        qa.append(
            (
                f"What did {a.id} and {b.id} learn?",
                f"They learned that magic does not make unfair play better. It only works nicely when it helps everyone share the adventure instead of chasing a monopoly.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"board_game", "magic", "fairness", "consistency"}
    tags |= set(f["spell"].tags)
    tags |= set(f["glitch_cfg"].tags)
    if f["outcome"] != "averted":
        tags |= set(f["fix"].tags)
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.age:
            bits.append(f"age={e.age}")
        if e.magical:
            bits.append("magical=True")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v != ""}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        adventure="moon_market",
        spell="copy_coins",
        glitch="arguing_bank",
        fix="reset_bell",
        instigator="Milo",
        instigator_gender="boy",
        helper="Tess",
        helper_gender="girl",
        guide="aunt",
        trait="careful",
        delay=0,
        instigator_age=6,
        helper_age=4,
        relation="siblings",
        trust=6,
        snack="jam biscuits",
        mascot="the sleepy cat",
    ),
    StoryParams(
        adventure="dragon_station",
        spell="double_dice",
        glitch="runaway_token",
        fix="rule_card",
        instigator="Ruby",
        instigator_gender="girl",
        helper="Finn",
        helper_gender="boy",
        guide="father",
        trait="patient",
        delay=0,
        instigator_age=7,
        helper_age=5,
        relation="friends",
        trust=5,
        snack="butter cookies",
        mascot="the stuffed dragon",
    ),
    StoryParams(
        adventure="cloud_castle",
        spell="pocket_portal",
        glitch="duplicate_squares",
        fix="counting_song",
        instigator="Owen",
        instigator_gender="boy",
        helper="June",
        helper_gender="girl",
        guide="mother",
        trait="sensible",
        delay=1,
        instigator_age=6,
        helper_age=4,
        relation="siblings",
        trust=4,
        snack="",
        mascot="",
    ),
    StoryParams(
        adventure="moon_market",
        spell="double_dice",
        glitch="duplicate_squares",
        fix="reset_bell",
        instigator="Lulu",
        instigator_gender="girl",
        helper="Nora",
        helper_gender="girl",
        guide="aunt",
        trait="careful",
        delay=0,
        instigator_age=5,
        helper_age=7,
        relation="siblings",
        trust=3,
        snack="cinnamon toast squares",
        mascot="the wind-up duck",
    ),
    StoryParams(
        adventure="dragon_station",
        spell="copy_coins",
        glitch="arguing_bank",
        fix="counting_song",
        instigator="Theo",
        instigator_gender="boy",
        helper="Mina",
        helper_gender="girl",
        guide="uncle",
        trait="cheerful",
        delay=1,
        instigator_age=7,
        helper_age=5,
        relation="friends",
        trust=7,
        snack="",
        mascot="the stuffed dragon",
    ),
]


def explain_rejection(spell: Spell, glitch: Glitch) -> str:
    if glitch.id == "melting_map":
        return (
            f"(No story: {glitch.label} is a silly visual gag, but it is not one of the world's grounded board-game glitches. "
            f"Pick a glitch that affects play, like runaway_token, duplicate_squares, or arguing_bank.)"
        )
    return (
        f"(No story: {spell.label} does not plausibly cause {glitch.label}. "
        f"Choose a spell and glitch that belong to the same kind of magical mix-up.)"
    )


def explain_fix(fid: str) -> str:
    fix = FIXES[fid]
    better = ", ".join(sorted(f.id for f in sensible_fixes()))
    return (
        f"(Refusing fix '{fid}': it scores too low on common sense (sense={fix.sense} < {SENSE_MIN}). "
        f"Try one of the calmer fixes: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.instigator_age, params.helper_age, params.trait):
        return "averted"
    return "restored" if is_restored(FIXES[params.fix], GLITCHES[params.glitch], params.delay) else "runaway"


ASP_RULES = r"""
compatible(double_dice, runaway_token).
compatible(double_dice, duplicate_squares).
compatible(pocket_portal, runaway_token).
compatible(pocket_portal, duplicate_squares).
compatible(copy_coins, arguing_bank).
compatible(copy_coins, duplicate_squares).

valid(A, S, G) :- adventure(A), spell(S), glitch(G), compatible(S, G).
sensible(F)    :- fix(F), sense(F, X), sense_min(M), X >= M.

care_now(T)    :- trait(T), careful_trait(T).
init_care(5)   :- trait(T), care_now(T).
init_care(3)   :- trait(T), not care_now(T).
helper_older   :- relation(siblings), instigator_age(IA), helper_age(HA), HA > IA.
bonus(4)       :- helper_older.
bonus(0)       :- not helper_older.
authority(C + 1 + B) :- init_care(C), bonus(B).
averted        :- helper_older, authority(A), boldness_init(BI), A > BI.

pressure(SV + D) :- chosen_glitch(G), severity(G, SV), delay(D).
fix_power(P)     :- chosen_fix(F), power(F, P).
restored         :- fix_power(P), pressure(PR), P >= PR.

outcome(averted) :- averted.
outcome(restored) :- not averted, restored.
outcome(runaway) :- not averted, not restored.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for aid in ADVENTURES:
        lines.append(asp.fact("adventure", aid))
    for sid in SPELLS:
        lines.append(asp.fact("spell", sid))
    for gid, glitch in GLITCHES.items():
        lines.append(asp.fact("glitch", gid))
        lines.append(asp.fact("severity", gid, glitch.severity))
    for fid, fix in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("sense", fid, fix.sense))
        lines.append(asp.fact("power", fid, fix.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("boldness_init", int(BOLDNESS_INIT)))
    for trait in sorted(CAREFUL_TRAITS):
        lines.append(asp.fact("careful_trait", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_fixes() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join(
        [
            asp.fact("chosen_glitch", params.glitch),
            asp.fact("chosen_fix", params.fix),
            asp.fact("delay", params.delay),
            asp.fact("relation", params.relation),
            asp.fact("instigator_age", params.instigator_age),
            asp.fact("helper_age", params.helper_age),
            asp.fact("trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0

    c_valid = set(asp_valid_combos())
    p_valid = set(valid_combos())
    if c_valid == p_valid:
        print(f"OK: gate matches valid_combos() ({len(c_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if c_valid - p_valid:
            print("  only in clingo:", sorted(c_valid - p_valid))
        if p_valid - c_valid:
            print("  only in python:", sorted(p_valid - c_valid))

    c_fix = set(asp_sensible_fixes())
    p_fix = {f.id for f in sensible_fixes()}
    if c_fix == p_fix:
        print(f"OK: sensible fixes match ({sorted(c_fix)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible fixes: clingo={sorted(c_fix)} python={sorted(p_fix)}")

    cases: list[StoryParams] = list(CURATED)
    parser = build_parser()
    for seed in range(200):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError while resolving seed {seed}.")
            break

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        buf = io.StringIO()
        with redirect_stdout(buf):
            emit(sample, trace=True, qa=True, header="### smoke test")
        if not sample.story.strip():
            raise StoryError("Generated story was empty in smoke test.")
        print("OK: smoke test generation and emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a magical board game, an unfair shortcut, and a fair funny ending."
    )
    ap.add_argument("--adventure", choices=ADVENTURES)
    ap.add_argument("--spell", choices=SPELLS)
    ap.add_argument("--glitch", choices=GLITCHES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--guide", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the glitch runs before help settles it")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.spell and args.glitch:
        if not compatible(SPELLS[args.spell], GLITCHES[args.glitch]):
            raise StoryError(explain_rejection(SPELLS[args.spell], GLITCHES[args.glitch]))
    if args.glitch and args.glitch == "melting_map":
        spell = SPELLS[args.spell] if args.spell else next(iter(SPELLS.values()))
        raise StoryError(explain_rejection(spell, GLITCHES[args.glitch]))
    if args.fix and FIXES[args.fix].sense < SENSE_MIN:
        raise StoryError(explain_fix(args.fix))

    combos = [
        combo
        for combo in valid_combos()
        if (args.adventure is None or combo[0] == args.adventure)
        and (args.spell is None or combo[1] == args.spell)
        and (args.glitch is None or combo[2] == args.glitch)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    adventure, spell, glitch = rng.choice(sorted(combos))
    fix = args.fix or rng.choice(sorted(f.id for f in sensible_fixes()))
    instigator, instigator_gender = _pick_kid(rng)
    helper, helper_gender = _pick_kid(rng, avoid=instigator)
    guide = args.guide or rng.choice(["mother", "father", "aunt", "uncle"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, helper_age = rng.sample([3, 4, 5, 6, 7], 2)
    trust = rng.randint(0, 10)
    snack = rng.choice(SNACKS)
    mascot = rng.choice(MASCOTS)

    return StoryParams(
        adventure=adventure,
        spell=spell,
        glitch=glitch,
        fix=fix,
        instigator=instigator,
        instigator_gender=instigator_gender,
        helper=helper,
        helper_gender=helper_gender,
        guide=guide,
        trait=trait,
        delay=delay,
        instigator_age=instigator_age,
        helper_age=helper_age,
        relation=relation,
        trust=trust,
        snack=snack,
        mascot=mascot,
    )


def generate(params: StoryParams) -> StorySample:
    if params.adventure not in ADVENTURES:
        raise StoryError(f"Unknown adventure: {params.adventure}")
    if params.spell not in SPELLS:
        raise StoryError(f"Unknown spell: {params.spell}")
    if params.glitch not in GLITCHES:
        raise StoryError(f"Unknown glitch: {params.glitch}")
    if params.fix not in FIXES:
        raise StoryError(f"Unknown fix: {params.fix}")
    if FIXES[params.fix].sense < SENSE_MIN:
        raise StoryError(explain_fix(params.fix))
    if not compatible(SPELLS[params.spell], GLITCHES[params.glitch]):
        raise StoryError(explain_rejection(SPELLS[params.spell], GLITCHES[params.glitch]))
    if params.guide not in {"mother", "father", "aunt", "uncle"}:
        raise StoryError(f"Unknown guide: {params.guide}")

    world = tell(
        adv=ADVENTURES[params.adventure],
        spell=SPELLS[params.spell],
        glitch=GLITCHES[params.glitch],
        fix=FIXES[params.fix],
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        helper=params.helper,
        helper_gender=params.helper_gender,
        trait=params.trait,
        guide_type=params.guide,
        delay=params.delay,
        instigator_age=params.instigator_age,
        helper_age=params.helper_age,
        relation=params.relation,
        trust=params.trust,
        snack=params.snack,
        mascot=params.mascot,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible fixes: {', '.join(asp_sensible_fixes())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (adventure, spell, glitch) combos:\n")
        for adventure, spell, glitch in combos:
            print(f"  {adventure:14} {spell:13} {glitch}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
                f"### {p.instigator} & {p.helper}: {p.spell} -> {p.glitch} "
                f"({p.adventure}, {p.fix}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
