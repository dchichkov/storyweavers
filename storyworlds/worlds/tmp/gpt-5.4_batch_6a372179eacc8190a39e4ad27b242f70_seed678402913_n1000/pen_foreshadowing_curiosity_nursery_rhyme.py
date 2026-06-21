#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/pen_foreshadowing_curiosity_nursery_rhyme.py
========================================================================

A standalone storyworld about a child's curiosity over a pen, told in a
nursery-rhyme-friendly voice. The world models a small temptation:

- a child finds an interesting pen,
- a tiny clue foreshadows that the pen may drip,
- curiosity pulls the child toward drawing on the wrong surface,
- a wiser helper may stop the mistake before it happens,
- otherwise a little ink mark appears and a grown-up must clean it,
- the ending proves what changed by giving the child a proper page for rhymes.

The world prefers a small set of plausible variants over broad coverage. It
refuses unreasonable surfaces or weak cleanup methods, and it includes an inline
ASP twin for parity checks.

Run it
------
    python storyworlds/worlds/gpt-5.4/pen_foreshadowing_curiosity_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4/pen_foreshadowing_curiosity_nursery_rhyme.py --target window
    python storyworlds/worlds/gpt-5.4/pen_foreshadowing_curiosity_nursery_rhyme.py --all
    python storyworlds/worlds/gpt-5.4/pen_foreshadowing_curiosity_nursery_rhyme.py --qa
    python storyworlds/worlds/gpt-5.4/pen_foreshadowing_curiosity_nursery_rhyme.py --verify
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
WONDER_INIT = 5.0
CAUTIOUS_TRAITS = {"careful", "gentle", "tidy", "thoughtful"}


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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    absorbent: bool = False
    washable: bool = False
    makes_mark: bool = False
    gives_page: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Frame:
    id: str
    opening: str
    wish: str
    chant: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class PenCfg:
    id: str
    label: str
    phrase: str
    detail: str
    clue: str
    drip: int
    plural: bool = False
    makes_mark: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class TargetCfg:
    id: str
    label: str
    the: str
    place: str
    material: str
    absorbent: bool
    washable: bool
    spread: int
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.the[0].upper() + self.the[1:]


@dataclass
class PageCfg:
    id: str
    label: str
    phrase: str
    use_line: str
    ending_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ResponseCfg:
    id: str
    label: str
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
        return self.entities[eid]

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"hero", "helper"}]

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


def _r_mark_spreads(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["marked"] < THRESHOLD:
            continue
        sig = ("mark", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for kid in world.kids():
            kid.memes["surprise"] += 1
        if "grownup" in world.entities:
            world.get("grownup").meters["workload"] += 1
        out.append("__mark__")
    return out


CAUSAL_RULES = [
    Rule(name="mark_spreads", tag="physical", apply=_r_mark_spreads),
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


def hazard_at_risk(pen: PenCfg, target: TargetCfg) -> bool:
    return pen.makes_mark and target.absorbent


def sensible_responses() -> list[ResponseCfg]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def stain_severity(pen: PenCfg, target: TargetCfg, delay: int) -> int:
    return pen.drip + target.spread + delay


def cleans_fully(response: ResponseCfg, pen: PenCfg, target: TargetCfg, delay: int) -> bool:
    return response.power >= stain_severity(pen, target, delay)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, hero_age: int, helper_age: int, trait: str) -> bool:
    helper_older = relation == "siblings" and helper_age > hero_age
    authority = initial_caution(trait) + 1.0 + (2.0 if helper_older else 0.0)
    return helper_older and authority > WONDER_INIT


def _do_mark(world: World, target: Entity, amount: int = 1, narrate: bool = True) -> None:
    target.meters["marked"] += float(amount)
    if not target.washable:
        target.meters["set_stain"] += 1
    propagate(world, narrate=narrate)


def predict_mark(world: World, pen_id: str, target_id: str) -> dict:
    sim = world.copy()
    pen_ent = sim.get(pen_id)
    target_ent = sim.get(target_id)
    amount = int(max(1, pen_ent.meters["dripiness"]))
    _do_mark(sim, target_ent, amount=amount, narrate=False)
    return {
        "marked": sim.get(target_id).meters["marked"] >= THRESHOLD,
        "workload": sim.get("grownup").meters["workload"],
    }


def introduce(world: World, hero: Entity, frame: Frame, pen: PenCfg, target: TargetCfg) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"{frame.opening} {hero.id} found {pen.phrase} resting {target.place}."
    )
    world.say(frame.chant)


def curiosity(world: World, hero: Entity, pen: PenCfg, frame: Frame) -> None:
    hero.memes["wonder"] += 1
    world.say(
        f"{hero.id} tilted {hero.pronoun('possessive')} head. "
        f'"What little song could this pen write?" {hero.pronoun()} wondered. '
        f"{frame.wish}"
    )
    world.say(
        f"The pen looked {pen.detail}, and {pen.clue}."
    )


def warning(world: World, helper: Entity, hero: Entity, pen: PenCfg, target: TargetCfg) -> None:
    pred = predict_mark(world, "pen", "target")
    helper.memes["caution"] += 1
    world.facts["predicted_mark"] = pred["marked"]
    world.facts["predicted_workload"] = pred["workload"]
    extra = ""
    if helper.memes["caution"] >= 6:
        extra = f" {helper.id} had already noticed the tiny bead of ink on the tip."
    world.say(
        f'{helper.id} came close and whispered, "That pen can leave real ink. '
        f'If it touches {target.the}, it may leave a mark that does not belong there."{extra}'
    )


def defy(world: World, hero: Entity, helper: Entity, target: TargetCfg) -> None:
    hero.memes["defiance"] += 1
    older = hero.attrs.get("relation") == "siblings" and hero.age > helper.age
    if older:
        world.say(
            f'"Just one curly line," {hero.id} sang, and because {hero.pronoun()} was the older one, '
            f"{helper.id} could not stop {hero.pronoun('object')} in time."
        )
    else:
        world.say(
            f'"Just one curly line," {hero.id} sang, and {hero.pronoun()} reached toward {target.the}."
        )


def back_down(world: World, hero: Entity, helper: Entity, pen: PenCfg) -> None:
    hero.memes["relief"] += 1
    helper.memes["relief"] += 1
    hero.memes["wonder"] = 0.0
    world.say(
        f"{hero.id} looked again at the shiny nib, then at {helper.id}, and drew {hero.pronoun('possessive')} hand back."
    )
    world.say(
        f'"A pen can wait for the proper page," {hero.id} said, and left {pen.label} where it was.'
    )


def first_mark(world: World, hero: Entity, pen: PenCfg, target: TargetCfg, target_ent: Entity) -> None:
    amount = int(max(1, world.get("pen").meters["dripiness"]))
    _do_mark(world, target_ent, amount=amount)
    world.say(
        f"The tip gave the tiniest kiss to {target.the}. First came a dot, then a curl, "
        f"and then a small blue blot spread like a raindrop waking up."
    )
    hero.memes["shock"] += 1


def call_grownup(world: World, hero: Entity, helper: Entity, grownup: Entity, target: TargetCfg) -> None:
    world.say(f'"Oh!" cried {hero.id}. "{target.The} has an ink spot!"')
    world.say(
        f'{helper.id} called, "{grownup.label_word.capitalize()}, please come see!"'
    )


def clean_success(
    world: World,
    grownup: Entity,
    response: ResponseCfg,
    target: TargetCfg,
    target_ent: Entity,
) -> None:
    target_ent.meters["marked"] = 0.0
    target_ent.meters["clean"] += 1
    world.say(
        f"{grownup.label_word.capitalize()} came with calm hands and {response.text.format(target=target.label)}."
    )
    world.say(
        f"Soon the little blot faded away, and only a damp, clean patch showed where it had been."
    )


def clean_fail(
    world: World,
    grownup: Entity,
    response: ResponseCfg,
    target: TargetCfg,
    target_ent: Entity,
) -> None:
    target_ent.meters["faint_mark"] += 1
    target_ent.meters["set_stain"] += 1
    world.say(
        f"{grownup.label_word.capitalize()} hurried over and {response.fail.format(target=target.label)}."
    )
    world.say(
        f"The biggest smudge lifted, but a pale blue freckle stayed behind on {target.the}."
    )


def lesson(world: World, grownup: Entity, hero: Entity, helper: Entity, pen: PenCfg, target: TargetCfg) -> None:
    for kid in (hero, helper):
        kid.memes["relief"] += 1
        kid.memes["lesson"] += 1
    world.say(
        f'{grownup.label_word.capitalize()} knelt beside them. "Pens are for pages first," '
        f'{grownup.pronoun()} said softly. "Curious hands can ask before they try."'
    )
    world.say(
        f"{hero.id} nodded, and {helper.id} nodded too, both looking at {target.the} much more carefully than before."
    )


def proper_page(world: World, grownup: Entity, hero: Entity, helper: Entity, frame: Frame, page: PageCfg) -> None:
    hero.memes["joy"] += 1
    hero.memes["safety"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"Then {grownup.label_word} brought {page.phrase}. \"Here is where the pen may dance,\" "
        f"{grownup.pronoun()} said."
    )
    world.say(
        f"{hero.id} {page.use_line}, while {helper.id} watched the loops and dots grow in the right place."
    )
    world.say(frame.ending)
    world.say(page.ending_line)


def tell(
    frame: Frame,
    pen: PenCfg,
    target: TargetCfg,
    page: PageCfg,
    response: ResponseCfg,
    hero_name: str = "Nell",
    hero_gender: str = "girl",
    helper_name: str = "Pip",
    helper_gender: str = "boy",
    grownup_type: str = "mother",
    helper_trait: str = "careful",
    delay: int = 0,
    hero_age: int = 5,
    helper_age: int = 7,
    relation: str = "siblings",
) -> World:
    world = World()
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_gender,
            role="hero",
            age=hero_age,
            attrs={"relation": relation},
            traits=["curious"],
        )
    )
    helper = world.add(
        Entity(
            id=helper_name,
            kind="character",
            type=helper_gender,
            role="helper",
            age=helper_age,
            attrs={"relation": relation},
            traits=[helper_trait],
        )
    )
    grownup = world.add(
        Entity(
            id="Grownup",
            kind="character",
            type=grownup_type,
            role="grownup",
            label="the grown-up",
        )
    )
    pen_ent = world.add(
        Entity(
            id="pen",
            type="pen",
            label=pen.label,
            phrase=pen.phrase,
            makes_mark=True,
            tags=set(pen.tags),
        )
    )
    pen_ent.meters["dripiness"] = float(pen.drip)
    target_ent = world.add(
        Entity(
            id="target",
            type="surface",
            label=target.label,
            phrase=target.the,
            absorbent=target.absorbent,
            washable=target.washable,
            tags=set(target.tags),
        )
    )
    page_ent = world.add(
        Entity(
            id="page",
            type="page",
            label=page.label,
            phrase=page.phrase,
            gives_page=True,
            tags=set(page.tags),
        )
    )

    introduce(world, hero, frame, pen, target)
    curiosity(world, hero, pen, frame)

    world.para()
    warning(world, helper, hero, pen, target)

    averted = would_avert(relation, hero.age, helper.age, helper_trait)
    if averted:
        back_down(world, hero, helper, pen)
        world.para()
        proper_page(world, grownup, hero, helper, frame, page)
    else:
        defy(world, hero, helper, target)
        world.para()
        first_mark(world, hero, pen, target, target_ent)
        call_grownup(world, hero, helper, grownup, target)
        world.para()
        cleaned = cleans_fully(response, pen, target, delay)
        if cleaned:
            clean_success(world, grownup, response, target, target_ent)
        else:
            clean_fail(world, grownup, response, target, target_ent)
        lesson(world, grownup, hero, helper, pen, target)
        world.para()
        proper_page(world, grownup, hero, helper, frame, page)

    outcome = "averted" if averted else ("cleaned" if cleans_fully(response, pen, target, delay) else "faint_stain")
    world.facts.update(
        frame=frame,
        pen_cfg=pen,
        target_cfg=target,
        page_cfg=page,
        response=response,
        hero=hero,
        helper=helper,
        grownup=grownup,
        pen=pen_ent,
        target=target_ent,
        page=page_ent,
        relation=relation,
        delay=delay,
        outcome=outcome,
        marked=target_ent.meters["marked"] >= THRESHOLD or target_ent.meters["clean"] >= THRESHOLD or target_ent.meters["faint_mark"] >= THRESHOLD,
        cleaned=target_ent.meters["clean"] >= THRESHOLD,
        faint_stain=target_ent.meters["faint_mark"] >= THRESHOLD,
        averted=averted,
    )
    return world


FRAMES = {
    "moon": Frame(
        id="moon",
        opening="In the hush before supper, when the room felt silver and slow,",
        wish="Perhaps it could make a moon-road, a sheep-road, or a sleepy little star.",
        chant='"Hush-a-by, hum-a-pen, what will you write, and where, and when?"',
        ending="So the rhyme went onto the page instead of the room, neat as a tucked-in tune.",
        tags={"rhyme"},
    ),
    "mice": Frame(
        id="mice",
        opening="When the clock said almost tea, and the floorboards seemed to squeak like mice,",
        wish="Perhaps it could draw whiskers for a king, or ladders for a mouse, or a tiny door in a shoe.",
        chant='"Nibble, scribble, little pen, tell your secret once again."',
        ending="And the rhyme stayed with the paper, where even little mice could not smudge it with their paws.",
        tags={"rhyme"},
    ),
    "garden": Frame(
        id="garden",
        opening="By the nursery window, where the light lay soft as buttercups,",
        wish="Perhaps it could make a curling vine, a beetle road, or a row of sleepy peas.",
        chant='"Curl and twirl, little pen, where shall your blue river bend?"',
        ending="So the blue river ran along the page, not across the nursery, and the room looked peaceful again.",
        tags={"rhyme"},
    ),
}

PENS = {
    "fountain": PenCfg(
        id="fountain",
        label="pen",
        phrase="a slim blue pen",
        detail="shiny and important",
        clue="a tiny bead of ink trembled on its nib as if it were holding its breath",
        drip=2,
        tags={"pen", "ink"},
    ),
    "feather": PenCfg(
        id="feather",
        label="pen",
        phrase="a feather-topped pen",
        detail="soft and fancy",
        clue="the nib already wore a dark dot of ink, small but eager",
        drip=1,
        tags={"pen", "ink"},
    ),
    "clicky": PenCfg(
        id="clicky",
        label="pen",
        phrase="a clicky red pen",
        detail="bright and full of promise",
        clue="one shiny drop had gathered at the point like a berry before rain",
        drip=1,
        tags={"pen", "ink"},
    ),
}

TARGETS = {
    "wall": TargetCfg(
        id="wall",
        label="wall",
        the="the nursery wall",
        place="on the low shelf by the wall",
        material="painted plaster",
        absorbent=True,
        washable=True,
        spread=2,
        tags={"wall", "ink_mark"},
    ),
    "pillowcase": TargetCfg(
        id="pillowcase",
        label="pillowcase",
        the="the white pillowcase",
        place="beside the bed",
        material="cotton cloth",
        absorbent=True,
        washable=True,
        spread=2,
        tags={"cloth", "ink_mark"},
    ),
    "tablecloth": TargetCfg(
        id="tablecloth",
        label="tablecloth",
        the="the lace tablecloth",
        place="on the little nursery table",
        material="lace cloth",
        absorbent=True,
        washable=False,
        spread=3,
        tags={"cloth", "ink_mark"},
    ),
    "window": TargetCfg(
        id="window",
        label="window",
        the="the window glass",
        place="on the sill by the window",
        material="glass",
        absorbent=False,
        washable=True,
        spread=0,
        tags={"glass"},
    ),
}

PAGES = {
    "notebook": PageCfg(
        id="notebook",
        label="notebook",
        phrase="a square little notebook",
        use_line="made a row of small looping moons in the notebook",
        ending_line="The pen skipped from line to line, and every mark belonged exactly where it landed.",
        tags={"paper", "notebook"},
    ),
    "drawing_pad": PageCfg(
        id="drawing_pad",
        label="drawing pad",
        phrase="a thick drawing pad",
        use_line="drew a mouse with a crown on the drawing pad",
        ending_line="Page after page waited patiently, so no curtain, wall, or cloth had to wear the rhyme instead.",
        tags={"paper", "paper"},
    ),
    "rhyme_book": PageCfg(
        id="rhyme_book",
        label="rhyme book",
        phrase="a blank rhyme book",
        use_line="wrote a tiny crooked verse in the rhyme book",
        ending_line="The words looked proud on the page, like ducklings walking in a neat little row.",
        tags={"paper", "book"},
    ),
}

RESPONSES = {
    "soap_cloth": ResponseCfg(
        id="soap_cloth",
        label="soapy cloth",
        sense=3,
        power=4,
        text="dabbed the {target} with a soft soapy cloth until the ink lifted",
        fail="dabbed the {target} with a soft soapy cloth, but the stain had already settled too deep",
        qa_text="used a soft soapy cloth to lift the ink",
        tags={"cleaning", "soap"},
    ),
    "milk_paste": ResponseCfg(
        id="milk_paste",
        label="milk paste",
        sense=2,
        power=3,
        text="blotted the {target} at once and worked the spot gently with cleaning paste",
        fail="tried a quick blot and gentle cleaning paste, but some blue stayed behind",
        qa_text="blotted the spot quickly and cleaned it gently",
        tags={"cleaning"},
    ),
    "shirt_sleeve": ResponseCfg(
        id="shirt_sleeve",
        label="shirt sleeve",
        sense=1,
        power=1,
        text="rubbed the {target} with a shirt sleeve",
        fail="rubbed the {target} with a shirt sleeve, only smearing the ink wider",
        qa_text="rubbed at the ink with a shirt sleeve",
        tags={"smear"},
    ),
}

GIRL_NAMES = ["Nell", "Mina", "Tess", "Ivy", "Lulu", "Ada", "Poppy", "Wren"]
BOY_NAMES = ["Pip", "Otis", "Ben", "Milo", "Toby", "Finn", "Ned", "Jem"]
TRAITS = ["careful", "gentle", "tidy", "thoughtful", "bright", "cheerful"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for frame_id in FRAMES:
        for pen_id, pen in PENS.items():
            for target_id, target in TARGETS.items():
                if hazard_at_risk(pen, target):
                    combos.append((frame_id, pen_id, target_id))
    return combos


@dataclass
class StoryParams:
    frame: str
    pen: str
    target: str
    page: str
    response: str
    hero_name: str
    hero_gender: str
    helper_name: str
    helper_gender: str
    grownup: str
    helper_trait: str
    delay: int = 0
    hero_age: int = 5
    helper_age: int = 7
    relation: str = "siblings"
    seed: Optional[int] = None


KNOWLEDGE = {
    "pen": [
        (
            "What is a pen for?",
            "A pen is a tool for making marks and words on paper. It works best on the right page, not on walls or cloth.",
        )
    ],
    "ink": [
        (
            "What is ink?",
            "Ink is a colored liquid that pens use to write or draw. It can soak into things and leave stains if it lands in the wrong place.",
        )
    ],
    "wall": [
        (
            "Why is drawing on a wall a problem?",
            "Walls are for holding up a room, not for being scribbled on. Ink on a wall can leave a mark that a grown-up has to clean.",
        )
    ],
    "cloth": [
        (
            "Why can cloth be hard to clean after ink gets on it?",
            "Cloth has tiny spaces between its threads, so liquid ink can sink in fast. That can make the mark harder to wash away.",
        )
    ],
    "paper": [
        (
            "Why is paper a good place for a pen?",
            "Paper is made for writing and drawing. It lets the pen make lines where they belong.",
        )
    ],
    "soap": [
        (
            "Why does a soapy cloth help clean a small ink spot?",
            "Soap helps loosen dirt and some stains so they can lift away with water and gentle rubbing. A grown-up can use it carefully on a little mark.",
        )
    ],
    "cleaning": [
        (
            "What should you do if you make a mark where it should not be?",
            "Tell a grown-up right away. Quick help can stop a little mark from becoming a bigger stain.",
        )
    ],
}
KNOWLEDGE_ORDER = ["pen", "ink", "wall", "cloth", "paper", "soap", "cleaning"]


def pair_noun(hero: Entity, helper: Entity, relation: str) -> str:
    if relation == "siblings":
        if hero.type == "boy" and helper.type == "boy":
            return "two brothers"
        if hero.type == "girl" and helper.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two children"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    frame = f["frame"]
    target = f["target_cfg"]
    page = f["page_cfg"]
    outcome = f["outcome"]
    if outcome == "averted":
        return [
            'Write a nursery-rhyme style story for a 3-to-5-year-old that includes the word "pen" and uses curiosity plus foreshadowing.',
            f"Tell a gentle story where {hero.id} is curious about a pen, but {helper.id} notices a clue that it may drip and stops {hero.pronoun('object')} before any mark is made.",
            f"Write a sing-song story with a quiet warning, no real mess, and an ending where the pen finally writes in {page.label} instead of on {target.the}.",
        ]
    if outcome == "cleaned":
        return [
            'Write a nursery-rhyme style story for a 3-to-5-year-old that includes the word "pen" and uses curiosity plus foreshadowing.',
            f"Tell a story where a child wonders what a pen can do, a tiny bead of ink foreshadows trouble, and a grown-up calmly cleans a small mark from {target.the}.",
            f"Write a lyrical story with a curious child, a wrong surface, and a happy ending where the pen is used on {page.label} the right way.",
        ]
    return [
        'Write a nursery-rhyme style story for a 3-to-5-year-old that includes the word "pen" and uses curiosity plus foreshadowing.',
        f"Tell a gentle cautionary story where {hero.id} touches a pen to {target.the}, the ink leaves a faint mark, and the lesson is to ask before trying.",
        f"Write a sing-song story where a tiny clue warns of trouble, curiosity leads to a small mistake, and the ending shows the pen used properly on paper.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    grownup = f["grownup"]
    pen = f["pen_cfg"]
    target = f["target_cfg"]
    page = f["page_cfg"]
    response = f["response"]
    relation = f["relation"]
    pair = pair_noun(hero, helper, relation)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {hero.id} and {helper.id}, and the grown-up who helped them. The story begins when {hero.id} notices {pen.phrase} and grows curious about it.",
        ),
        (
            f"Why was {hero.id} curious about the pen?",
            f"{hero.id} wondered what little song or picture the pen could make. That wondering is what pulled {hero.pronoun('object')} toward trying it.",
        ),
        (
            "What was the clue that foreshadowed trouble?",
            f"The pen already had a tiny bead of ink on its tip. That small clue showed it might drip or mark something before anyone meant it to.",
        ),
        (
            f"Why did {helper.id} warn {hero.id}?",
            f"{helper.id} knew the pen could leave real ink on {target.the}. The warning came before the mistake because {helper.pronoun()} could already imagine the mark and the cleaning it would bring.",
        ),
    ]
    if f["outcome"] == "averted":
        qa.append(
            (
                f"What changed after {helper.id} spoke?",
                f"{hero.id} pulled {hero.pronoun('possessive')} hand back and chose not to touch the pen to {target.the}. The danger stayed only a possibility, so the rhyme could end gently.",
            )
        )
    elif f["outcome"] == "cleaned":
        qa.append(
            (
                f"What happened when the pen touched {target.the}?",
                f"A small blue blot appeared on {target.the}. The little clue from before became real trouble because the ink finally landed where it did not belong.",
            )
        )
        qa.append(
            (
                f"How did the grown-up fix the problem?",
                f"{grownup.label_word.capitalize()} {response.qa_text}. Because the grown-up came quickly, the mark could be cleaned before it stayed.",
            )
        )
    else:
        qa.append(
            (
                f"What happened when the pen touched {target.the}?",
                f"A small blue blot appeared on {target.the}, and later a pale mark still remained. The stain was smaller than before, but it did not disappear all the way.",
            )
        )
        qa.append(
            (
                f"Why did a faint stain stay behind?",
                f"The ink had time to settle, or the surface held onto it too strongly. Even after cleaning, a little blue freckle stayed to show what had happened.",
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with the pen writing on {page.label} instead of on the room. The final image proves the lesson changed the child's choice, not just the words.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set(f["pen_cfg"].tags) | set(f["target_cfg"].tags) | set(f["page_cfg"].tags) | set(f["response"].tags)
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
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.age:
            bits.append(f"age={ent.age}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        flags = []
        if ent.absorbent:
            flags.append("absorbent")
        if ent.washable:
            flags.append("washable")
        if ent.makes_mark:
            flags.append("makes_mark")
        if ent.gives_page:
            flags.append("gives_page")
        if flags:
            bits.append(f"flags={flags}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        frame="moon",
        pen="fountain",
        target="wall",
        page="notebook",
        response="soap_cloth",
        hero_name="Nell",
        hero_gender="girl",
        helper_name="Pip",
        helper_gender="boy",
        grownup="mother",
        helper_trait="careful",
        delay=0,
        hero_age=5,
        helper_age=7,
        relation="siblings",
    ),
    StoryParams(
        frame="mice",
        pen="feather",
        target="pillowcase",
        page="drawing_pad",
        response="milk_paste",
        hero_name="Milo",
        hero_gender="boy",
        helper_name="Ada",
        helper_gender="girl",
        grownup="father",
        helper_trait="bright",
        delay=0,
        hero_age=6,
        helper_age=5,
        relation="friends",
    ),
    StoryParams(
        frame="garden",
        pen="fountain",
        target="tablecloth",
        page="rhyme_book",
        response="milk_paste",
        hero_name="Ivy",
        hero_gender="girl",
        helper_name="Ben",
        helper_gender="boy",
        grownup="mother",
        helper_trait="thoughtful",
        delay=1,
        hero_age=6,
        helper_age=6,
        relation="friends",
    ),
    StoryParams(
        frame="moon",
        pen="clicky",
        target="pillowcase",
        page="notebook",
        response="soap_cloth",
        hero_name="Jem",
        hero_gender="boy",
        helper_name="Nell",
        helper_gender="girl",
        grownup="father",
        helper_trait="gentle",
        delay=0,
        hero_age=4,
        helper_age=7,
        relation="siblings",
    ),
]


def explain_rejection(pen: PenCfg, target: TargetCfg) -> str:
    if not target.absorbent:
        return (
            f"(No story: {pen.label} can make an ink mark, but {target.the} is {target.material} "
            f"and would not soak up the trouble in the way this little world needs. "
            f"Pick a surface like a wall, pillowcase, or tablecloth.)"
        )
    return "(No story: this pen and surface do not make a plausible little ink-mistake.)"


def explain_response(response_id: str) -> str:
    response = RESPONSES[response_id]
    better = ", ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{response_id}': it scores too low on common sense "
        f"(sense={response.sense} < {SENSE_MIN}). Try one of the sensible cleanup methods: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.hero_age, params.helper_age, params.helper_trait):
        return "averted"
    pen = PENS[params.pen]
    target = TARGETS[params.target]
    response = RESPONSES[params.response]
    return "cleaned" if cleans_fully(response, pen, target, params.delay) else "faint_stain"


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
hazard(P, T) :- makes_mark(P), absorbent(T).
sensible(R)  :- response(R), sense(R, S), sense_min(M), S >= M.
valid(F, P, T) :- frame(F), pen(P), target(T), hazard(P, T).

% --- outcome model ---------------------------------------------------------
cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
helper_older :- relation(siblings), hero_age(H), helper_age(A), A > H.
bonus(2) :- helper_older.
bonus(0) :- not helper_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- helper_older, authority(A), wonder_init(W), A > W.

severity(Dp + Sp + Dl) :- chosen_pen(P), drip(P, Dp), chosen_target(T), spread(T, Sp), delay(Dl).
full_clean :- chosen_response(R), power(R, P), severity(S), P >= S.

outcome(averted) :- averted.
outcome(cleaned) :- not averted, full_clean.
outcome(faint_stain) :- not averted, not full_clean.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for frame_id in FRAMES:
        lines.append(asp.fact("frame", frame_id))
    for pen_id, pen in PENS.items():
        lines.append(asp.fact("pen", pen_id))
        if pen.makes_mark:
            lines.append(asp.fact("makes_mark", pen_id))
        lines.append(asp.fact("drip", pen_id, pen.drip))
    for target_id, target in TARGETS.items():
        lines.append(asp.fact("target", target_id))
        if target.absorbent:
            lines.append(asp.fact("absorbent", target_id))
        lines.append(asp.fact("spread", target_id, target.spread))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        lines.append(asp.fact("power", response_id, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("wonder_init", int(WONDER_INIT)))
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

    scenario = "\n".join(
        [
            asp.fact("chosen_pen", params.pen),
            asp.fact("chosen_target", params.target),
            asp.fact("chosen_response", params.response),
            asp.fact("delay", params.delay),
            asp.fact("relation", params.relation),
            asp.fact("hero_age", params.hero_age),
            asp.fact("helper_age", params.helper_age),
            asp.fact("trait", params.helper_trait),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    clingo_sens, python_sens = set(asp_sensible()), {r.id for r in sensible_responses()}
    if clingo_sens == python_sens:
        print(f"OK: sensible responses match ({sorted(clingo_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(clingo_sens)} python={sorted(python_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(50):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(p)

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
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("Smoke test generated an empty story.")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a curious child, a pen, a warning clue, and the right page at last."
    )
    ap.add_argument("--frame", choices=FRAMES)
    ap.add_argument("--pen", choices=PENS)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--page", choices=PAGES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--grownup", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the ink gets to settle before cleaning")
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


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.target and not TARGETS[args.target].absorbent:
        pen = PENS[args.pen] if args.pen else next(iter(PENS.values()))
        raise StoryError(explain_rejection(pen, TARGETS[args.target]))
    if args.pen and args.target:
        pen = PENS[args.pen]
        target = TARGETS[args.target]
        if not hazard_at_risk(pen, target):
            raise StoryError(explain_rejection(pen, target))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo
        for combo in valid_combos()
        if (args.frame is None or combo[0] == args.frame)
        and (args.pen is None or combo[1] == args.pen)
        and (args.target is None or combo[2] == args.target)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    frame_id, pen_id, target_id = rng.choice(sorted(combos))
    page_id = args.page or rng.choice(sorted(PAGES))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    hero_name, hero_gender = _pick_child(rng)
    helper_name, helper_gender = _pick_child(rng, avoid=hero_name)
    grownup = args.grownup or rng.choice(["mother", "father"])
    helper_trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    hero_age, helper_age = rng.sample([4, 5, 6, 7], 2)

    return StoryParams(
        frame=frame_id,
        pen=pen_id,
        target=target_id,
        page=page_id,
        response=response_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        grownup=grownup,
        helper_trait=helper_trait,
        delay=delay,
        hero_age=hero_age,
        helper_age=helper_age,
        relation=relation,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        frame = FRAMES[params.frame]
        pen = PENS[params.pen]
        target = TARGETS[params.target]
        page = PAGES[params.page]
        response = RESPONSES[params.response]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter choice: {err})") from err

    if not hazard_at_risk(pen, target):
        raise StoryError(explain_rejection(pen, target))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        frame=frame,
        pen=pen,
        target=target,
        page=page,
        response=response,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        grownup_type=params.grownup,
        helper_trait=params.helper_trait,
        delay=params.delay,
        hero_age=params.hero_age,
        helper_age=params.helper_age,
        relation=params.relation,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (frame, pen, target) combos:\n")
        for frame_id, pen_id, target_id in combos:
            print(f"  {frame_id:8} {pen_id:8} {target_id}")
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
            header = f"### {p.hero_name} and {p.helper_name}: {p.pen} pen by {p.target} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
