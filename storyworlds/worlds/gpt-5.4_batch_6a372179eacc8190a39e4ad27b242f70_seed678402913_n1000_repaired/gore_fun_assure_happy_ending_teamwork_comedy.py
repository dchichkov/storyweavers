#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/gore_fun_assure_happy_ending_teamwork_comedy.py
============================================================================

A tiny storyworld about two children preparing a silly cake for a child-facing
festival booth. A red spill makes the cake look like "gore" from a grown-up
monster movie, which is exactly the wrong mood for a funny event. By working
together, the children clean it up, add a comic decoration, and end with a
happy, laughing crowd.

The world model is small on purpose:
- typed entities with physical meters and emotional memes
- a reasonableness gate over cake/spill/repair combinations
- a declarative ASP twin of that gate and the happy-ending outcome
- story text rendered from simulated state rather than a frozen template
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "teacher", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Venue:
    id: str
    place: str
    audience: str
    booth: str
    tags: set[str] = field(default_factory=set)


@dataclass
class CakeKind:
    id: str
    label: str
    phrase: str
    joke_line: str
    scare_need: int
    surface: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Spill:
    id: str
    label: str
    phrase: str
    severity: int
    red: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Repair:
    id: str
    label: str
    phrase: str
    clean: int
    silly: int
    sense: int
    method: str
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


def _r_scary(world: World) -> list[str]:
    out: list[str] = []
    cake = world.get("cake")
    if cake.meters["stained"] < THRESHOLD or not world.facts.get("spill_red", False):
        return out
    sig = ("scary", "cake")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    cake.meters["scary"] += float(world.facts["cake_cfg"].scare_need)
    for kid in (world.get("maker"), world.get("helper")):
        kid.memes["worry"] += 1
    out.append("__scary__")
    return out


def _r_sticky(world: World) -> list[str]:
    out: list[str] = []
    table = world.get("table")
    if table.meters["sticky"] < THRESHOLD:
        return out
    sig = ("sticky", "table")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("room").meters["risk"] += 1
    out.append("__sticky__")
    return out


CAUSAL_RULES = [
    Rule(name="scary", tag="mood", apply=_r_scary),
    Rule(name="sticky", tag="physical", apply=_r_sticky),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            got = rule.apply(world)
            if got:
                changed = True
                produced.extend(s for s in got if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


VENUES = {
    "school_fair": Venue(
        id="school_fair",
        place="the school fair",
        audience="little kids and their families",
        booth="the comedy cake booth",
        tags={"fair", "children"},
    ),
    "library_day": Venue(
        id="library_day",
        place="the library family day",
        audience="small children sitting on bright beanbags",
        booth="the snack-and-smile table",
        tags={"library", "children"},
    ),
    "park_picnic": Venue(
        id="park_picnic",
        place="the park picnic",
        audience="neighbors with folding chairs and baby strollers",
        booth="the joke dessert stand",
        tags={"park", "children"},
    ),
}

CAKES = {
    "dragon": CakeKind(
        id="dragon",
        label="dragon cake",
        phrase="a lopsided dragon cake with candy teeth",
        joke_line="Its tongue kept leaning out as if it wanted to tell a joke.",
        scare_need=2,
        surface="frosting",
        tags={"dragon", "cake"},
    ),
    "monster": CakeKind(
        id="monster",
        label="monster cake",
        phrase="a round monster cake with one big cookie eye",
        joke_line="The single eye made it look surprised by its own eyebrows.",
        scare_need=2,
        surface="frosting",
        tags={"monster", "cake"},
    ),
    "robot": CakeKind(
        id="robot",
        label="robot cake",
        phrase="a square robot cake with cracker buttons",
        joke_line="Its cracker buttons looked as if they might start hiccuping.",
        scare_need=1,
        surface="frosting",
        tags={"robot", "cake"},
    ),
}

SPILLS = {
    "jam": Spill(
        id="jam",
        label="raspberry jam",
        phrase="a spoonful of raspberry jam",
        severity=1,
        red=True,
        tags={"jam", "red_spill"},
    ),
    "syrup": Spill(
        id="syrup",
        label="strawberry syrup",
        phrase="a stripe of strawberry syrup",
        severity=2,
        red=True,
        tags={"syrup", "red_spill"},
    ),
    "icing": Spill(
        id="icing",
        label="beet-red icing",
        phrase="a blob of beet-red icing",
        severity=2,
        red=True,
        tags={"icing", "red_spill"},
    ),
    "berry_juice": Spill(
        id="berry_juice",
        label="berry juice",
        phrase="a splash of berry juice",
        severity=1,
        red=True,
        tags={"juice", "red_spill"},
    ),
}

REPAIRS = {
    "whipped_cream": Repair(
        id="whipped_cream",
        label="whipped cream swirls",
        phrase="a bowl of whipped cream and a clean spoon",
        clean=1,
        silly=2,
        sense=3,
        method="dabbed away the worst of the red mess and piped fluffy white swirls over the spot",
        qa_text="They covered the spill with whipped cream swirls after cleaning the red mess",
        tags={"whipped_cream", "repair"},
    ),
    "sprinkles": Repair(
        id="sprinkles",
        label="rainbow sprinkles",
        phrase="a jar of rainbow sprinkles",
        clean=0,
        silly=2,
        sense=1,
        method="shook rainbow sprinkles over the red mess without cleaning it first",
        qa_text="They just poured sprinkles over the spill",
        tags={"sprinkles", "repair"},
    ),
    "banana_hat": Repair(
        id="banana_hat",
        label="banana slices and cookie eyebrows",
        phrase="banana slices and cookie eyebrows",
        clean=1,
        silly=1,
        sense=2,
        method="wiped the spill, tucked banana slices on top, and gave the cake two foolish cookie eyebrows",
        qa_text="They wiped the spill and turned the cake funny with banana slices and cookie eyebrows",
        tags={"banana", "repair"},
    ),
    "marshmallow_mustache": Repair(
        id="marshmallow_mustache",
        label="a marshmallow mustache",
        phrase="a marshmallow mustache and tiny sugar dots",
        clean=2,
        silly=2,
        sense=3,
        method="cleaned the red frosting, then added a puffy marshmallow mustache and tiny sugar-dot freckles",
        qa_text="They cleaned the spill and added a marshmallow mustache to make the cake look silly",
        tags={"marshmallow", "repair"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["careful", "bouncy", "curious", "thoughtful", "goofy", "helpful"]


def repair_works(cake: CakeKind, spill: Spill, repair: Repair) -> bool:
    return spill.red and repair.clean >= spill.severity and repair.silly >= cake.scare_need


def sensible_repairs() -> list[Repair]:
    return [r for r in REPAIRS.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for venue_id in VENUES:
        for cake_id, cake in CAKES.items():
            for spill_id, spill in SPILLS.items():
                if any(repair_works(cake, spill, r) and r.sense >= SENSE_MIN for r in REPAIRS.values()):
                    out.append((venue_id, cake_id, spill_id))
    return out


@dataclass
class StoryParams:
    venue: str
    cake: str
    spill: str
    repair: str
    maker: str
    maker_gender: str
    helper: str
    helper_gender: str
    adult: str
    maker_trait: str
    helper_trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        venue="school_fair",
        cake="dragon",
        spill="jam",
        repair="whipped_cream",
        maker="Lily",
        maker_gender="girl",
        helper="Tom",
        helper_gender="boy",
        adult="mother",
        maker_trait="goofy",
        helper_trait="careful",
        seed=1,
    ),
    StoryParams(
        venue="library_day",
        cake="monster",
        spill="syrup",
        repair="marshmallow_mustache",
        maker="Max",
        maker_gender="boy",
        helper="Mia",
        helper_gender="girl",
        adult="father",
        maker_trait="bouncy",
        helper_trait="thoughtful",
        seed=2,
    ),
    StoryParams(
        venue="park_picnic",
        cake="robot",
        spill="berry_juice",
        repair="banana_hat",
        maker="Nora",
        maker_gender="girl",
        helper="Finn",
        helper_gender="boy",
        adult="mother",
        maker_trait="curious",
        helper_trait="helpful",
        seed=3,
    ),
]


def explain_rejection(cake: CakeKind, spill: Spill, repair: Repair) -> str:
    reasons = []
    if not spill.red:
        reasons.append("the spill would not make the cake look alarmingly red")
    if repair.clean < spill.severity:
        reasons.append(
            f"{repair.label} does not clean enough of {spill.label}"
        )
    if repair.silly < cake.scare_need:
        reasons.append(
            f"{repair.label} is not funny enough to turn a {cake.label} gentle and silly"
        )
    return "(No story: " + "; ".join(reasons) + ".)"


def explain_response(rid: str) -> str:
    r = REPAIRS[rid]
    better = ", ".join(sorted(x.id for x in sensible_repairs()))
    return (
        f"(Refusing repair '{rid}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def introduce(world: World, venue: Venue, maker: Entity, helper: Entity, cake: CakeKind) -> None:
    for kid in (maker, helper):
        kid.memes["joy"] += 1
        kid.memes["teamwork"] += 1
    world.say(
        f"On the morning of {venue.place}, {maker.id} and {helper.id} stood behind "
        f"{venue.booth} with {cake.phrase}. {cake.joke_line}"
    )
    world.say(
        f"They wanted everyone in {venue.audience} to grin before the first bite."
    )


def comic_boast(world: World, maker: Entity, helper: Entity, cake: CakeKind) -> None:
    world.say(
        f'"This is going to be so much fun," {maker.id} said, puffing up proudly. '
        f'"Our {cake.label} looks ready to tell knock-knock jokes."'
    )
    world.say(
        f'{helper.id} laughed so hard that {helper.pronoun("possessive")} shoulders bounced.'
    )


def accident(world: World, maker: Entity, helper: Entity, spill: Spill) -> None:
    cake = world.get("cake")
    table = world.get("table")
    cake.meters["stained"] += float(spill.severity)
    table.meters["sticky"] += 1.0
    maker.memes["shock"] += 1
    helper.memes["shock"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {helper.id}'s elbow bumped the bowl, and {spill.phrase} slid across the cake."
    )
    world.say(
        f"In one blink, the red smear looked like gore from a grown-up monster movie, "
        f"not a silly dessert for children."
    )


def worry(world: World, maker: Entity, helper: Entity, adult: Entity, cake: CakeKind) -> None:
    cake_ent = world.get("cake")
    if cake_ent.meters["scary"] >= THRESHOLD:
        maker.memes["embarrassed"] += 1
        helper.memes["worry"] += 1
        world.say(
            f'"Oh no," {maker.id} whispered. "Now the {cake.label} looks scary instead of funny."'
        )
        world.say(
            f'{helper.id} pointed at the sticky streak and called for {adult.label_word.capitalize()}.'
        )


def assure(world: World, adult: Entity, maker: Entity, helper: Entity) -> None:
    for kid in (maker, helper):
        kid.memes["reassured"] += 1
    world.say(
        f'{adult.label_word.capitalize()} came over, looked once, and did not panic. '
        f'"I assure you, this can still be fixed," {adult.pronoun()} said. '
        f'"Use teamwork, not tears."'
    )


def choose_repair(world: World, maker: Entity, helper: Entity, repair: Repair) -> None:
    maker.memes["focus"] += 1
    helper.memes["focus"] += 1
    world.say(
        f'{maker.id} grabbed {repair.phrase}, and {helper.id} held the cake stand steady.'
    )


def do_repair(world: World, maker: Entity, helper: Entity, repair: Repair) -> None:
    cake = world.get("cake")
    table = world.get("table")
    cleaned = min(cake.meters["stained"], float(repair.clean))
    cake.meters["stained"] -= cleaned
    cake.meters["scary"] = max(0.0, cake.meters["scary"] - float(repair.silly))
    cake.meters["funny"] += float(repair.silly)
    table.meters["sticky"] = max(0.0, table.meters["sticky"] - 1.0)
    world.get("room").meters["risk"] = 0.0
    for kid in (maker, helper):
        kid.memes["teamwork"] += 1
        kid.memes["joy"] += 1
        kid.memes["worry"] = 0.0
    world.say(
        f"Working shoulder to shoulder, they {repair.method}."
    )
    if cake.meters["scary"] <= 0.0:
        world.say(
            "The cake stopped looking fierce and started looking gloriously ridiculous."
        )


def ending(world: World, venue: Venue, maker: Entity, helper: Entity, adult: Entity, cake: CakeKind, repair: Repair) -> None:
    world.say(
        f"Soon the first children arrived, stared for a tiny moment, and then burst out laughing."
    )
    world.say(
        f'One child pointed at the cake and said, "It looks as if the {cake.label} forgot its own serious face!"'
    )
    world.say(
        f'{maker.id} and {helper.id} looked at each other, grinned, and served slices together. '
        f'The booth stayed bright, busy, and full of fun.'
    )
    world.say(
        f"By the end of {venue.place}, even {adult.label_word} was chuckling, and the once-scary smear had become the best joke on the table."
    )


def tell(
    venue: Venue,
    cake_cfg: CakeKind,
    spill: Spill,
    repair: Repair,
    maker_name: str,
    maker_gender: str,
    helper_name: str,
    helper_gender: str,
    adult_type: str,
    maker_trait: str,
    helper_trait: str,
) -> World:
    world = World()
    maker = world.add(
        Entity(
            id=maker_name,
            kind="character",
            type=maker_gender,
            role="maker",
            traits=[maker_trait],
            label=maker_name,
        )
    )
    helper = world.add(
        Entity(
            id=helper_name,
            kind="character",
            type=helper_gender,
            role="helper",
            traits=[helper_trait],
            label=helper_name,
        )
    )
    adult = world.add(
        Entity(
            id="Adult",
            kind="character",
            type=adult_type,
            role="adult",
            label="the grown-up",
        )
    )
    cake = world.add(
        Entity(
            id="cake",
            kind="thing",
            type="cake",
            label=cake_cfg.label,
            phrase=cake_cfg.phrase,
            tags=set(cake_cfg.tags),
        )
    )
    world.add(Entity(id="table", kind="thing", type="table", label="the table"))
    world.add(Entity(id="room", kind="thing", type="room", label="the booth"))

    world.facts["spill_red"] = spill.red
    world.facts["cake_cfg"] = cake_cfg

    introduce(world, venue, maker, helper, cake_cfg)
    comic_boast(world, maker, helper, cake_cfg)

    world.para()
    accident(world, maker, helper, spill)
    worry(world, maker, helper, adult, cake_cfg)
    assure(world, adult, maker, helper)

    world.para()
    choose_repair(world, maker, helper, repair)
    do_repair(world, maker, helper, repair)

    world.para()
    ending(world, venue, maker, helper, adult, cake_cfg, repair)

    world.facts.update(
        venue=venue,
        cake=cake_cfg,
        spill=spill,
        repair=repair,
        maker=maker,
        helper=helper,
        adult=adult,
        cake_entity=cake,
        teamwork=maker.memes["teamwork"] + helper.memes["teamwork"],
        saved=cake.meters["scary"] <= 0.0 and world.get("room").meters["risk"] <= 0.0,
    )
    return world


KNOWLEDGE = {
    "jam": [
        (
            "What is jam?",
            "Jam is fruit cooked with sugar until it gets thick and spreadable. Raspberry jam is bright red, so a big smear can look dramatic.",
        )
    ],
    "syrup": [
        (
            "What is syrup?",
            "Syrup is a sweet liquid that pours easily. If it spills, it can make a sticky mess.",
        )
    ],
    "icing": [
        (
            "What is icing?",
            "Icing is sweet topping spread on cakes and cookies. Colored icing can change how a cake looks right away.",
        )
    ],
    "repair": [
        (
            "Why is teamwork helpful when something goes wrong?",
            "Teamwork helps because one person can steady, clean, or hand tools while another fixes the main problem. Working together is often faster and calmer than trying to do everything alone.",
        )
    ],
    "whipped_cream": [
        (
            "What does whipped cream do on a cake?",
            "Whipped cream makes soft, fluffy swirls on top of a cake. It can also hide a small messy spot.",
        )
    ],
    "marshmallow": [
        (
            "Why can a silly decoration change the mood of a cake?",
            "Funny decorations make people see the cake as playful instead of scary. A mustache or goofy eyebrows can turn a mistake into a joke.",
        )
    ],
    "banana": [
        (
            "Why are banana slices useful in a dessert decoration?",
            "Banana slices are soft, pale, and easy to place on top of frosting. They can cover a small area and make a design look cheerful.",
        )
    ],
    "children": [
        (
            "Why do little kids like funny food better than scary food?",
            "Many little kids enjoy food that looks friendly and silly because it feels safe and inviting. A gentle joke is easier to enjoy than a frightening surprise.",
        )
    ],
}
KNOWLEDGE_ORDER = ["jam", "syrup", "icing", "repair", "whipped_cream", "marshmallow", "banana", "children"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    venue = f["venue"]
    cake = f["cake"]
    maker = f["maker"]
    helper = f["helper"]
    return [
        f'Write a funny story for a 3-to-5-year-old that includes the words "gore", "fun", and "assure".',
        f"Tell a comedy about {maker.id} and {helper.id} trying to save a {cake.label} at {venue.place} with teamwork and a happy ending.",
        f"Write a gentle story where a red baking accident makes a cake look too scary for children, but a calm grown-up assures the kids and they fix it together.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    maker = f["maker"]
    helper = f["helper"]
    adult = f["adult"]
    venue = f["venue"]
    cake = f["cake"]
    spill = f["spill"]
    repair = f["repair"]
    saved = f["saved"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {maker.id} and {helper.id}, two children working together at {venue.place}. A calm grown-up helps them stay steady when their cake goes wrong.",
        ),
        (
            "What problem happened to the cake?",
            f"{spill.label.capitalize()} smeared across the {cake.label}, and the red mess made it look like gore instead of a friendly joke. The spill also left the table sticky, which made everyone worry for a moment.",
        ),
        (
            "What did the grown-up say to help?",
            f'The grown-up said, "I assure you, this can still be fixed." That mattered because the children stopped panicking and started working as a team.',
        ),
        (
            "How did the children fix the cake?",
            f"{maker.id} and {helper.id} used {repair.label} together. {repair.qa_text}, so the cake looked silly again instead of scary.",
        ),
    ]
    if saved:
        qa.append(
            (
                "How did the story end?",
                f"It ended happily: children came to the booth, laughed at the cake, and the two helpers served slices together. The ending proves the teamwork worked because the scary accident turned into a joke everyone could enjoy.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["spill"].tags) | set(f["repair"].tags) | set(f["venue"].tags)
    tags.add("repair")
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
        if e.traits:
            bits.append(f"traits={e.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% base gate
sensible(R) :- repair(R), sense(R, S), sense_min(M), S >= M.
works(C, S, R) :- cake(C), spill(S), repair(R),
                  red(S),
                  severity(S, Sev), clean(R, Cl), Cl >= Sev,
                  scare_need(C, Need), silly(R, Si), Si >= Need.
valid(V, C, S) :- venue(V), cake(C), spill(S), works(C, S, R), sensible(R).

% chosen outcome
saved :- chosen_cake(C), chosen_spill(S), chosen_repair(R),
         works(C, S, R), sensible(R).
outcome(happy) :- saved.
outcome(oops) :- not saved.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for venue_id in VENUES:
        lines.append(asp.fact("venue", venue_id))
    for cake_id, cake in CAKES.items():
        lines.append(asp.fact("cake", cake_id))
        lines.append(asp.fact("scare_need", cake_id, cake.scare_need))
    for spill_id, spill in SPILLS.items():
        lines.append(asp.fact("spill", spill_id))
        lines.append(asp.fact("severity", spill_id, spill.severity))
        if spill.red:
            lines.append(asp.fact("red", spill_id))
    for repair_id, repair in REPAIRS.items():
        lines.append(asp.fact("repair", repair_id))
        lines.append(asp.fact("clean", repair_id, repair.clean))
        lines.append(asp.fact("silly", repair_id, repair.silly))
        lines.append(asp.fact("sense", repair_id, repair.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
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
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_cake", params.cake),
            asp.fact("chosen_spill", params.spill),
            asp.fact("chosen_repair", params.repair),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    got = asp.atoms(model, "outcome")
    return got[0][0] if got else "?"


def outcome_of(params: StoryParams) -> str:
    cake = CAKES[params.cake]
    spill = SPILLS[params.spill]
    repair = REPAIRS[params.repair]
    return "happy" if repair_works(cake, spill, repair) and repair.sense >= SENSE_MIN else "oops"


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

    c_sens = set(asp_sensible())
    p_sens = {r.id for r in sensible_repairs()}
    if c_sens == p_sens:
        print(f"OK: sensible repairs match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible repairs: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    for p in CURATED:
        if asp_outcome(p) != outcome_of(p):
            rc = 1
            print(f"MISMATCH in outcome for curated case: {p}")
    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story")
        print("OK: smoke test generation succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a comedy cake accident repaired by teamwork."
    )
    ap.add_argument("--venue", choices=VENUES)
    ap.add_argument("--cake", choices=CAKES)
    ap.add_argument("--spill", choices=SPILLS)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--adult", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    names = [n for n in pool if n != avoid]
    return rng.choice(names), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.repair and REPAIRS[args.repair].sense < SENSE_MIN:
        raise StoryError(explain_response(args.repair))
    if args.cake and args.spill and args.repair:
        cake = CAKES[args.cake]
        spill = SPILLS[args.spill]
        repair = REPAIRS[args.repair]
        if not repair_works(cake, spill, repair):
            raise StoryError(explain_rejection(cake, spill, repair))

    combos = [
        c
        for c in valid_combos()
        if (args.venue is None or c[0] == args.venue)
        and (args.cake is None or c[1] == args.cake)
        and (args.spill is None or c[2] == args.spill)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    venue_id, cake_id, spill_id = rng.choice(sorted(combos))
    cake = CAKES[cake_id]
    spill = SPILLS[spill_id]
    repair_choices = [
        rid
        for rid, repair in REPAIRS.items()
        if repair.sense >= SENSE_MIN and repair_works(cake, spill, repair)
    ]
    if args.repair:
        if args.repair not in repair_choices:
            raise StoryError(explain_rejection(cake, spill, REPAIRS[args.repair]))
        repair_id = args.repair
    else:
        repair_id = rng.choice(sorted(repair_choices))
    maker, maker_gender = _pick_kid(rng)
    helper, helper_gender = _pick_kid(rng, avoid=maker)
    adult = args.adult or rng.choice(["mother", "father"])
    maker_trait = rng.choice(TRAITS)
    helper_trait = rng.choice([t for t in TRAITS if t != maker_trait] or TRAITS)
    return StoryParams(
        venue=venue_id,
        cake=cake_id,
        spill=spill_id,
        repair=repair_id,
        maker=maker,
        maker_gender=maker_gender,
        helper=helper,
        helper_gender=helper_gender,
        adult=adult,
        maker_trait=maker_trait,
        helper_trait=helper_trait,
    )


def generate(params: StoryParams) -> StorySample:
    for key, registry in [
        (params.venue, VENUES),
        (params.cake, CAKES),
        (params.spill, SPILLS),
        (params.repair, REPAIRS),
    ]:
        if key not in registry:
            raise StoryError("(No story: a requested option is not in this world's registry.)")
    if REPAIRS[params.repair].sense < SENSE_MIN:
        raise StoryError(explain_response(params.repair))
    if not repair_works(CAKES[params.cake], SPILLS[params.spill], REPAIRS[params.repair]):
        raise StoryError(explain_rejection(CAKES[params.cake], SPILLS[params.spill], REPAIRS[params.repair]))

    world = tell(
        venue=VENUES[params.venue],
        cake_cfg=CAKES[params.cake],
        spill=SPILLS[params.spill],
        repair=REPAIRS[params.repair],
        maker_name=params.maker,
        maker_gender=params.maker_gender,
        helper_name=params.helper,
        helper_gender=params.helper_gender,
        adult_type=params.adult,
        maker_trait=params.maker_trait,
        helper_trait=params.helper_trait,
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
        combos = asp_valid_combos()
        print(f"sensible repairs: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (venue, cake, spill) combos:\n")
        for venue, cake, spill in combos:
            print(f"  {venue:12} {cake:8} {spill}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
            header = f"### {p.maker} & {p.helper}: {p.cake} at {p.venue} ({p.spill} -> {p.repair})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
