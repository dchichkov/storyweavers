#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/astrology_inner_monologue_reconciliation_nursery_rhyme.py
====================================================================================

A standalone story world for a tiny nursery-rhyme-style tale about two children,
a scrap of astrology talk, a quarrel over a shiny craft piece, and a true
reconciliation. The world model tracks physical state (held, torn, mended,
worn, hanging) and emotional state (pride, hurt, regret, trust, joy). The prose
is generated from simulated state rather than from a frozen template.

Run it
------
    python storyworlds/worlds/gpt-5.4/astrology_inner_monologue_reconciliation_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4/astrology_inner_monologue_reconciliation_nursery_rhyme.py --sign leo --craft crown --repair patch_pair
    python storyworlds/worlds/gpt-5.4/astrology_inner_monologue_reconciliation_nursery_rhyme.py --craft kite --repair hang_together
    python storyworlds/worlds/gpt-5.4/astrology_inner_monologue_reconciliation_nursery_rhyme.py --all
    python storyworlds/worlds/gpt-5.4/astrology_inner_monologue_reconciliation_nursery_rhyme.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/astrology_inner_monologue_reconciliation_nursery_rhyme.py --trace
    python storyworlds/worlds/gpt-5.4/astrology_inner_monologue_reconciliation_nursery_rhyme.py --verify
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
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    owner: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "teacher", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"teacher": "teacher", "mother": "mom", "father": "dad"}.get(self.type, self.type)
    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Sign:
    id: str
    sky_name: str
    creature: str
    boast: str
    soften: str
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
class Craft:
    id: str
    label: str
    phrase: str
    opening: str
    end_image: str
    mode: str
    fragile: int
    features: set[str] = field(default_factory=set)
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
class Repair:
    id: str
    label: str
    needs: set[str]
    power: int
    offer: str
    action: str
    ending: str
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
        self.history: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"starter", "friend"}]

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
        clone.history = list(self.history)
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


def _r_quarrel(world: World) -> list[str]:
    craft = world.get("craft")
    a = world.get("starter")
    b = world.get("friend")
    if craft.meters["held_tight"] < THRESHOLD:
        return []
    if b.memes["want_same"] < THRESHOLD:
        return []
    sig = ("quarrel", craft.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    a.memes["pride"] += 1
    b.memes["hurt"] += 1
    a.memes["distance"] += 1
    b.memes["distance"] += 1
    world.history.append("quarrel")
    return ["__quarrel__"]


def _r_tear(world: World) -> list[str]:
    craft = world.get("craft")
    if craft.meters["tugged"] < THRESHOLD:
        return []
    sig = ("tear", craft.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    craft.meters["torn"] += 1
    for kid in world.kids():
        kid.memes["sad"] += 1
        kid.memes["distance"] += 1
    world.history.append("tear")
    return ["__tear__"]


def _r_regret(world: World) -> list[str]:
    a = world.get("starter")
    craft = world.get("craft")
    if craft.meters["torn"] < THRESHOLD:
        return []
    if a.memes["pride"] < THRESHOLD:
        return []
    sig = ("regret", a.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    a.memes["regret"] += 1
    a.memes["pride"] = 0.0
    world.history.append("regret")
    return ["__regret__"]


def _r_reconcile(world: World) -> list[str]:
    a = world.get("starter")
    b = world.get("friend")
    craft = world.get("craft")
    if craft.meters["mended"] < THRESHOLD:
        return []
    if a.memes["sorry"] < THRESHOLD:
        return []
    sig = ("reconcile", craft.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in (a, b):
        kid.memes["trust"] += 1
        kid.memes["joy"] += 1
        kid.memes["distance"] = 0.0
        kid.memes["sad"] = 0.0
    b.memes["hurt"] = 0.0
    world.history.append("reconcile")
    return ["__reconcile__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="quarrel", tag="social", apply=_r_quarrel),
    Rule(name="tear", tag="physical", apply=_r_tear),
    Rule(name="regret", tag="emotional", apply=_r_regret),
    Rule(name="reconcile", tag="social", apply=_r_reconcile),
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
        for sent in produced:
            world.say(sent)
    return produced


def repair_fits(craft: Craft, repair: Repair) -> bool:
    return repair.needs.issubset(craft.features)


def can_mend(craft: Craft, repair: Repair) -> bool:
    return repair_fits(craft, repair) and repair.power >= craft.fragile


def valid_combos() -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for craft_id, craft in CRAFTS.items():
        for repair_id, repair in REPAIRS.items():
            if can_mend(craft, repair):
                out.append((craft_id, repair_id))
    return sorted(out)


def predict_mend(world: World, repair_id: str) -> dict:
    sim = world.copy()
    repair = REPAIRS[repair_id]
    craft = sim.get("craft")
    if craft.meters["torn"] < THRESHOLD:
        craft.meters["torn"] = 1.0
    if can_mend(CRAFTS[sim.facts["craft_cfg"].id], repair):
        craft.meters["mended"] += 1
    return {
        "mended": craft.meters["mended"] >= THRESHOLD,
        "hurt": sim.get("friend").memes["hurt"],
    }


def introduce(world: World, a: Entity, b: Entity, craft: Craft) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"In the nursery room, with clap-clap light, {a.id} and {b.id} worked on {craft.phrase}. "
        f"{craft.opening}"
    )
    world.say(
        f"They snipped and skipped and hummed a tune, making something fit for star and moon."
    )


def astrology_thought(world: World, a: Entity, sign: Sign) -> None:
    a.memes["pride"] += 1
    world.facts["inner_line"] = (
        f'Inside, {a.id} thought, "This little astrology card says {sign.boast}. '
        f'Maybe the brightest bit should come with me."'
    )
    world.say(world.facts["inner_line"])


def choose_shiny_piece(world: World, a: Entity, b: Entity, craft: Craft, sign: Sign) -> None:
    piece = world.get("piece")
    piece.owner = a.id
    piece.meters["claimed"] += 1
    piece.meters["shiny"] = 1.0
    craft.meters["held_tight"] += 1
    b.memes["want_same"] += 1
    propagate(world, narrate=False)
    world.say(
        f"There was one gold-bright piece in the middle of it all, and {a.id} tucked it close. "
        f'"{sign.soften}," {a.id} sang, "so this shines with me."'
    )
    world.say(
        f"{b.id} blinked and whispered, \"But I helped cut and paste and glue.\""
    )


def tug_and_tear(world: World, a: Entity, b: Entity, craft: Craft) -> None:
    craft_ent = world.get("craft")
    craft_ent.meters["tugged"] += 1
    propagate(world, narrate=False)
    world.say(
        f"One little tug and one little tug, and then came rip-rip-rag. "
        f"The {craft.label} bent and tore, and both children stood still on the rug."
    )
    world.say(
        f"{b.id}'s mouth went small, and {a.id}'s hands did too."
    )


def inner_regret(world: World, a: Entity) -> None:
    propagate(world, narrate=False)
    line = (
        f'Inside, {a.id} thought, "Oh dear, oh my. I wanted to sparkle, not make a friend cry."'
    )
    world.facts["regret_line"] = line
    world.say(line)


def helper_offers(world: World, helper: Entity, a: Entity, b: Entity, craft: Craft, repair: Repair) -> None:
    pred = predict_mend(world, repair.id)
    world.facts["predicted_mend"] = pred["mended"]
    world.say(
        f"{helper.label_word.capitalize()} knelt beside the torn {craft.label} and spoke in a calm, round rhyme: "
        f'"Two small hands can hurt in a hurry, but two kind hands can mend in time."'
    )
    world.say(f'"How about we {repair.offer}?"')


def apologize(world: World, a: Entity, b: Entity) -> None:
    a.memes["sorry"] += 1
    b.memes["listening"] += 1
    world.say(
        f'"I am sorry," said {a.id}. "I let a braggy thought grow bigger than our game."'
    )
    world.say(
        f'"I was hurt," said {b.id}, "but I want us to fix it together."'
    )


def mend(world: World, a: Entity, b: Entity, craft: Craft, repair: Repair) -> None:
    craft_ent = world.get("craft")
    if not can_mend(craft, repair):
        raise StoryError(
            f"(No story: {repair.label} will not truly mend a {craft.label}. "
            f"Pick a repair that fits the craft and is strong enough.)"
        )
    craft_ent.meters["mended"] += 1
    craft_ent.meters["torn"] = 0.0
    piece = world.get("piece")
    piece.owner = ""
    if craft.mode == "wear":
        craft_ent.meters["worn"] += 1
    elif craft.mode == "hang":
        craft_ent.meters["hanging"] += 1
    else:
        craft_ent.meters["shared"] += 1
    propagate(world, narrate=False)
    world.say(
        f"So snip and pat and smooth went {repair.action}. "
        f"Soon the torn place lay flat, and the little thing looked whole again."
    )


def ending(world: World, a: Entity, b: Entity, craft: Craft, repair: Repair, sign: Sign) -> None:
    world.say(
        f'{repair.ending} {craft.end_image}'
    )
    world.say(
        f"And {a.id} learned that astrology might offer a playful picture of the sky, "
        f"but friendship shines best when no one is pushed outside the song."
    )
    if sign.id == "libra":
        extra = "The room felt even as scales, gentle and bright."
    elif sign.id == "pisces":
        extra = "Their laughter bobbed together like two silver fish."
    else:
        extra = "Their laughter padded warm as a lion in the sun."
    world.say(extra)


def tell(
    sign: Sign,
    craft: Craft,
    repair: Repair,
    starter_name: str = "Molly",
    starter_gender: str = "girl",
    friend_name: str = "Pip",
    friend_gender: str = "boy",
    helper_type: str = "teacher",
    trait: str = "eager",
) -> World:
    if not can_mend(craft, repair):
        raise StoryError(
            f"(No story: {repair.label} cannot reasonably mend a {craft.label}. "
            f"Choose one of: {', '.join(sorted(rid for cid, rid in valid_combos() if cid == craft.id))}.)"
        )

    world = World()
    a = world.add(Entity(
        id="starter",
        kind="character",
        type=starter_gender,
        label=starter_name,
        role="starter",
        traits=[trait],
        attrs={"name": starter_name},
    ))
    b = world.add(Entity(
        id="friend",
        kind="character",
        type=friend_gender,
        label=friend_name,
        role="friend",
        traits=["gentle"],
        attrs={"name": friend_name},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_type,
        label="the teacher",
        role="helper",
        attrs={},
    ))
    craft_ent = world.add(Entity(
        id="craft",
        type="craft",
        label=craft.label,
        phrase=craft.phrase,
        attrs={"features": sorted(craft.features), "mode": craft.mode},
    ))
    piece = world.add(Entity(
        id="piece",
        type="shiny_piece",
        label="gold piece",
        phrase="a gold-bright piece",
        attrs={},
    ))

    for ent in (a, b, helper, craft_ent, piece):
        ent.meters["held_tight"] += 0.0
        ent.meters["tugged"] += 0.0
        ent.meters["torn"] += 0.0
        ent.meters["mended"] += 0.0
        ent.meters["shared"] += 0.0
        ent.meters["worn"] += 0.0
        ent.meters["hanging"] += 0.0
        ent.meters["claimed"] += 0.0
        ent.meters["shiny"] += 0.0
        ent.memes["pride"] += 0.0
        ent.memes["hurt"] += 0.0
        ent.memes["sad"] += 0.0
        ent.memes["regret"] += 0.0
        ent.memes["sorry"] += 0.0
        ent.memes["trust"] += 0.0
        ent.memes["joy"] += 0.0
        ent.memes["distance"] += 0.0
        ent.memes["want_same"] += 0.0
        ent.memes["listening"] += 0.0

    world.facts.update(
        sign=sign,
        craft_cfg=craft,
        repair=repair,
        starter=a,
        friend=b,
        helper=helper,
        starter_name=starter_name,
        friend_name=friend_name,
        conflict=False,
        reconciled=False,
        inner_line="",
        regret_line="",
        predicted_mend=False,
    )

    introduce(world, a, b, craft)
    astrology_thought(world, a, sign)

    world.para()
    choose_shiny_piece(world, a, b, craft, sign)
    world.facts["conflict"] = True
    tug_and_tear(world, a, b, craft)

    world.para()
    inner_regret(world, a)
    helper_offers(world, helper, a, b, craft, repair)
    apologize(world, a, b)
    mend(world, a, b, craft, repair)
    world.facts["reconciled"] = craft_ent.meters["mended"] >= THRESHOLD and a.memes["sorry"] >= THRESHOLD

    world.para()
    ending(world, a, b, craft, repair, sign)
    return world


SIGNS = {
    "leo": Sign(
        id="leo",
        sky_name="Leo",
        creature="lion",
        boast="Leo is the lion, the bright one, the bold one",
        soften="My lion likes a sunny gleam",
        tags={"astrology", "leo"},
    ),
    "libra": Sign(
        id="libra",
        sky_name="Libra",
        creature="scales",
        boast="Libra is the scales, neat and shining in a row",
        soften="My scales love a tidy gleam",
        tags={"astrology", "libra"},
    ),
    "pisces": Sign(
        id="pisces",
        sky_name="Pisces",
        creature="fish",
        boast="Pisces is the fish, silver and softly gliding",
        soften="My fish like a silver gleam",
        tags={"astrology", "pisces"},
    ),
}

CRAFTS = {
    "garland": Craft(
        id="garland",
        label="star garland",
        phrase="a paper star garland",
        opening="Blue paper stars lay here, yellow paper stars lay there, all in a sleepy circle chair.",
        end_image="The garland swung above the book corner, twinkling over both of them.",
        mode="share",
        fragile=2,
        features={"string", "paper", "hang"},
        tags={"craft", "garland"},
    ),
    "crown": Craft(
        id="crown",
        label="moon crown",
        phrase="a moon crown of paper and foil",
        opening="A silver moon sat on the band, with little stars to either hand.",
        end_image="They took turns wearing the moon crown and bowing to one another with a giggle.",
        mode="wear",
        fragile=1,
        features={"paper", "wear"},
        tags={"craft", "crown"},
    ),
    "kite": Craft(
        id="kite",
        label="cloud kite",
        phrase="a cloud kite with ribbon tails",
        opening="It had a soft white middle and ribbon tails that wanted a breeze.",
        end_image="The cloud kite hung by the window, nodding whenever the air came through.",
        mode="hang",
        fragile=2,
        features={"paper", "hang", "ribbon"},
        tags={"craft", "kite"},
    ),
}

REPAIRS = {
    "patch_pair": Repair(
        id="patch_pair",
        label="patching with a matching pair",
        needs={"paper"},
        power=2,
        offer="cut a matching pair and patch the tear so the shine belongs to both sides",
        action="careful patch-patch work with two small matching stars",
        ending="They stood shoulder to shoulder to admire the mended shape.",
        qa_text="They cut a matching pair and patched the tear so both sides could shine.",
        tags={"patch"},
    ),
    "hang_together": Repair(
        id="hang_together",
        label="hanging it together",
        needs={"hang"},
        power=2,
        offer="hang it together where two children can enjoy it at once",
        action="string-string work and one careful knot",
        ending="Then they lifted it together, one on each side, and smiled up at it.",
        qa_text="They mended it and hung it where both of them could enjoy it together.",
        tags={"hang"},
    ),
    "take_turns": Repair(
        id="take_turns",
        label="taking turns",
        needs={"wear"},
        power=1,
        offer="mend the little tear and take turns instead of grabbing",
        action="press-press work and a soft strip of tape",
        ending="First one wore it, then the other, and neither child was left out.",
        qa_text="They fixed the small tear and took turns, so the special thing was shared fairly.",
        tags={"turns"},
    ),
}

GIRL_NAMES = ["Molly", "Tess", "Lina", "Poppy", "Nell", "Ivy", "Daisy", "Mina"]
BOY_NAMES = ["Pip", "Ben", "Ollie", "Ned", "Toby", "Finn", "Kit", "Sam"]
TRAITS = ["eager", "bouncy", "dreamy", "careful", "chirpy"]


@dataclass
class StoryParams:
    sign: str
    craft: str
    repair: str
    starter_name: str
    starter_gender: str
    friend_name: str
    friend_gender: str
    helper: str
    trait: str
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
    "astrology": [
        (
            "What is astrology?",
            "Astrology is a way some people talk about stars and signs, often as a playful way to describe feelings or personalities. It is not a rule for how we must treat our friends."
        )
    ],
    "leo": [
        (
            "What is Leo in astrology?",
            "Leo is one of the star signs in astrology, and people often connect it with a lion and bright, bold pictures. In a story, that can be a playful idea, not a reason to boss others."
        )
    ],
    "libra": [
        (
            "What is Libra in astrology?",
            "Libra is a star sign often pictured as scales. People use that picture to think about balance and fairness."
        )
    ],
    "pisces": [
        (
            "What is Pisces in astrology?",
            "Pisces is a star sign often pictured as two fish. People sometimes use it as a gentle, dreamy picture from the sky."
        )
    ],
    "patch": [
        (
            "What does it mean to patch torn paper?",
            "To patch torn paper means to cover the ripped place with another piece so it can hold together again. Careful hands and glue or tape can make it strong enough to use."
        )
    ],
    "hang": [
        (
            "Why can hanging something up help children share it?",
            "When something is hung where everyone can see it, one child does not have to keep it all alone. The object becomes part of the room, so both can enjoy it together."
        )
    ],
    "turns": [
        (
            "What does taking turns mean?",
            "Taking turns means one person uses something first and another person uses it next. It is a fair way to share when both people want the same thing."
        )
    ],
}
KNOWLEDGE_ORDER = ["astrology", "leo", "libra", "pisces", "patch", "hang", "turns"]


def generation_prompts(world: World) -> list[str]:
    sign = world.facts["sign"]
    craft = world.facts["craft_cfg"]
    repair = world.facts["repair"]
    starter = world.facts["starter"]
    friend = world.facts["friend"]
    return [
        f'Write a nursery-rhyme-style story for a 3-to-5-year-old that includes the word "astrology" and shows an inner monologue before a quarrel and a reconciliation after it.',
        f"Tell a gentle rhyme where {starter.label} and {friend.label} make {craft.phrase}, a shiny piece causes trouble, and they reconcile by {repair.label}.",
        f"Write a short rhyming story in which a child thinks about {sign.sky_name} in astrology, makes a selfish choice, feels sorry inside, and fixes the friendship."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    sign = world.facts["sign"]
    craft = world.facts["craft_cfg"]
    repair = world.facts["repair"]
    starter = world.facts["starter"]
    friend = world.facts["friend"]
    helper = world.facts["helper"]
    starter_name = starter.label
    friend_name = friend.label
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {starter_name} and {friend_name}, two children making {craft.phrase}, and their {helper.label_word} who helps them slow down. The story follows how a small grab turns into hurt feelings and then into peace again."
        ),
        (
            f"What made {starter_name} grab the shiny piece?",
            f"{starter_name} had an inner thought about {sign.sky_name} in astrology and let that thought puff up into a reason to keep the brightest part. The choice came from pride inside, not from kindness between the children."
        ),
        (
            f"Why did the {craft.label} tear?",
            f"Both children wanted the same shining piece, so the craft was tugged from two sides. Because the pulling happened in a hurry, the paper ripped and made them both sad."
        ),
        (
            f"How did {starter_name} and {friend_name} reconcile?",
            f"{starter_name} admitted being sorry, and {friend_name} agreed to fix the problem together. Then they {repair.qa_text} That repair changed the object and the friendship at the same time."
        ),
        (
            "What changed by the end of the story?",
            f"At first the shiny part was being kept by one child, but at the end the mended {craft.label} belonged in a shared way. The ending image proves the quarrel is over because both children can enjoy it without grabbing."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    sign = world.facts["sign"]
    repair = world.facts["repair"]
    tags = {"astrology", sign.id, repair.id}
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
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
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    lines.append(f"  history: {world.history}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        sign="leo",
        craft="crown",
        repair="take_turns",
        starter_name="Molly",
        starter_gender="girl",
        friend_name="Pip",
        friend_gender="boy",
        helper="teacher",
        trait="eager",
        seed=101,
    ),
    StoryParams(
        sign="libra",
        craft="garland",
        repair="hang_together",
        starter_name="Tess",
        starter_gender="girl",
        friend_name="Ben",
        friend_gender="boy",
        helper="teacher",
        trait="careful",
        seed=102,
    ),
    StoryParams(
        sign="pisces",
        craft="kite",
        repair="patch_pair",
        starter_name="Ivy",
        starter_gender="girl",
        friend_name="Ollie",
        friend_gender="boy",
        helper="teacher",
        trait="dreamy",
        seed=103,
    ),
    StoryParams(
        sign="leo",
        craft="kite",
        repair="hang_together",
        starter_name="Nell",
        starter_gender="girl",
        friend_name="Finn",
        friend_gender="boy",
        helper="teacher",
        trait="bouncy",
        seed=104,
    ),
]


def explain_rejection(craft: Craft, repair: Repair) -> str:
    if not repair_fits(craft, repair):
        return (
            f"(No story: {repair.label} does not fit a {craft.label}. "
            f"It needs {sorted(repair.needs)}, but the craft offers {sorted(craft.features)}.)"
        )
    return (
        f"(No story: {repair.label} fits a {craft.label}, but it is too weak to mend that tear. "
        f"Choose a sturdier repair.)"
    )


ASP_RULES = r"""
fits(C, R) :- craft(C), repair(R), need(R, F), feature(C, F),
             not missing_feature(C, R).
missing_feature(C, R) :- need(R, F), not feature(C, F).

can_mend(C, R) :- craft(C), repair(R), not missing_feature(C, R),
                  fragile(C, FC), power(R, PR), PR >= FC.

ending_mode(C, wear)  :- mode(C, wear).
ending_mode(C, hang)  :- mode(C, hang).
ending_mode(C, share) :- mode(C, share).

valid(C, R) :- can_mend(C, R).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sign_id in SIGNS:
        lines.append(asp.fact("sign", sign_id))
    for craft_id, craft in CRAFTS.items():
        lines.append(asp.fact("craft", craft_id))
        lines.append(asp.fact("fragile", craft_id, craft.fragile))
        lines.append(asp.fact("mode", craft_id, craft.mode))
        for feature in sorted(craft.features):
            lines.append(asp.fact("feature", craft_id, feature))
    for repair_id, repair in REPAIRS.items():
        lines.append(asp.fact("repair", repair_id))
        lines.append(asp.fact("power", repair_id, repair.power))
        for need in sorted(repair.needs):
            lines.append(asp.fact("need", repair_id, need))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


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

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test failed: generated empty story.)")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    parser = build_parser()
    for seed in range(5):
        args = parser.parse_args([])
        try:
            params = resolve_params(args, random.Random(seed))
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("(Generated empty story during verification.)")
        except Exception as err:  # pragma: no cover - verification path
            rc = 1
            print(f"RANDOM GENERATION FAILED for seed {seed}: {err}")
            break
    else:
        print("OK: random generation smoke-tested on seeds 0-4.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Nursery-rhyme story world: astrology talk, an inner thought, a torn craft, and reconciliation."
    )
    ap.add_argument("--sign", choices=SIGNS)
    ap.add_argument("--craft", choices=CRAFTS)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--starter-name")
    ap.add_argument("--friend-name")
    ap.add_argument("--starter-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["teacher", "mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible (craft, repair) set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate matches the Python logic and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.craft and args.repair:
        craft = CRAFTS[args.craft]
        repair = REPAIRS[args.repair]
        if not can_mend(craft, repair):
            raise StoryError(explain_rejection(craft, repair))

    combos = [
        combo for combo in valid_combos()
        if (args.craft is None or combo[0] == args.craft)
        and (args.repair is None or combo[1] == args.repair)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    craft_id, repair_id = rng.choice(sorted(combos))
    sign = args.sign or rng.choice(sorted(SIGNS))
    starter_gender = args.starter_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    starter_name = args.starter_name or _pick_name(rng, starter_gender)
    friend_name = args.friend_name or _pick_name(rng, friend_gender, avoid=starter_name)
    helper = args.helper or "teacher"
    trait = rng.choice(TRAITS)

    return StoryParams(
        sign=sign,
        craft=craft_id,
        repair=repair_id,
        starter_name=starter_name,
        starter_gender=starter_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        helper=helper,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.sign not in SIGNS:
        raise StoryError(f"(No story: unknown sign '{params.sign}'.)")
    if params.craft not in CRAFTS:
        raise StoryError(f"(No story: unknown craft '{params.craft}'.)")
    if params.repair not in REPAIRS:
        raise StoryError(f"(No story: unknown repair '{params.repair}'.)")
    craft = CRAFTS[params.craft]
    repair = REPAIRS[params.repair]
    if not can_mend(craft, repair):
        raise StoryError(explain_rejection(craft, repair))

    world = tell(
        sign=SIGNS[params.sign],
        craft=craft,
        repair=repair,
        starter_name=params.starter_name,
        starter_gender=params.starter_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        helper_type=params.helper,
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
        print(asp_program("", "#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (craft, repair) combos:\n")
        for craft_id, repair_id in combos:
            print(f"  {craft_id:8} {repair_id}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.starter_name} & {p.friend_name}: {p.craft} with {p.repair} ({p.sign})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
