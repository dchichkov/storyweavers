#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/melt_misunderstanding_suspense_tall_tale.py
======================================================================

A standalone storyworld about a child, a giant fair-day creation that can melt,
a misunderstanding, and a suspenseful rescue told in a tall-tale style.

The world model is small and classical:
- typed entities share one representation
- physical meters track heat, softening, shade, and coolness
- emotional memes track pride, worry, relief, and trust
- a misunderstanding causes a wrong first move
- a sensible fix either saves the giant creation in time or arrives too late

Run it
------
    python storyworlds/worlds/gpt-5.4/melt_misunderstanding_suspense_tall_tale.py
    python storyworlds/worlds/gpt-5.4/melt_misunderstanding_suspense_tall_tale.py --meltable stone_rooster
    python storyworlds/worlds/gpt-5.4/melt_misunderstanding_suspense_tall_tale.py --fix fan
    python storyworlds/worlds/gpt-5.4/melt_misunderstanding_suspense_tall_tale.py --all
    python storyworlds/worlds/gpt-5.4/melt_misunderstanding_suspense_tall_tale.py --qa
    python storyworlds/worlds/gpt-5.4/melt_misunderstanding_suspense_tall_tale.py --verify
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meltable: bool = False
    cools: bool = False
    shades: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "aunt", "mother"}
        male = {"boy", "man", "uncle", "father", "giant"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "uncle": "uncle", "aunt": "aunt"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    opening: str
    tall_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Meltable:
    id: str
    label: str
    phrase: str
    material: str
    shape_word: str
    soft_word: str
    drip_word: str
    heat_limit: int
    meltable: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Heat:
    id: str
    label: str
    image: str
    severity: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Misunderstanding:
    id: str
    heard: str
    wrong_action: str
    reveal: str
    delay: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    cools: bool = False
    shades: bool = False
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
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_heat_softens(world: World) -> list[str]:
    out: list[str] = []
    creation = world.get("creation")
    room = world.get("air")
    if not creation.meltable:
        return out
    effective_heat = room.meters["heat"] - creation.meters["shade"] - creation.meters["cool"]
    if effective_heat <= creation.attrs.get("limit", 0):
        return out
    sig = ("soften", int(effective_heat), int(creation.meters["shade"]), int(creation.meters["cool"]))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    creation.meters["soft"] += 1
    creation.meters["wobble"] += 1
    for eid in ("hero", "helper"):
        world.get(eid).memes["worry"] += 1
    out.append("__softening__")
    return out


def _r_soft_to_drip(world: World) -> list[str]:
    out: list[str] = []
    creation = world.get("creation")
    if creation.meters["soft"] < THRESHOLD:
        return out
    sig = ("drip", creation.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    creation.meters["drip"] += 1
    out.append("__drip__")
    return out


CAUSAL_RULES = [
    Rule(name="heat_softens", tag="physical", apply=_r_heat_softens),
    Rule(name="soft_to_drip", tag="physical", apply=_r_soft_to_drip),
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


def hazard_at_risk(meltable: Meltable, heat: Heat) -> bool:
    return meltable.meltable and heat.severity > meltable.heat_limit


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= SENSE_MIN]


def outcome_score(meltable: Meltable, heat: Heat, fix: Fix, misunderstanding: Misunderstanding) -> int:
    return fix.power - (heat.severity + misunderstanding.delay - meltable.heat_limit)


def saved_in_time(meltable: Meltable, heat: Heat, fix: Fix, misunderstanding: Misunderstanding) -> bool:
    return outcome_score(meltable, heat, fix, misunderstanding) >= 0


def explain_rejection(meltable: Meltable, heat: Heat) -> str:
    if not meltable.meltable:
        return (f"(No story: {meltable.label} is not something that would melt in this world, "
                f"so there is no honest melting danger and no suspenseful rescue.)")
    if heat.severity <= meltable.heat_limit:
        return (f"(No story: {heat.label} is not hot enough to threaten {meltable.phrase}, "
                f"so nothing is really in danger of melting.)")
    return "(No story: this combination has no melting danger.)"


def explain_fix(fid: str) -> str:
    fix = FIXES[fid]
    better = ", ".join(sorted(f.id for f in sensible_fixes()))
    return (f"(Refusing fix '{fid}': it scores too low on common sense "
            f"(sense={fix.sense} < {SENSE_MIN}). Try one of: {better}.)")


def predict_softening(world: World) -> dict:
    sim = world.copy()
    propagate(sim, narrate=False)
    creation = sim.get("creation")
    return {
        "soft": creation.meters["soft"] >= THRESHOLD,
        "drip": creation.meters["drip"] >= THRESHOLD,
    }


def introduce(world: World, hero: Entity, helper: Entity, setting: Setting, meltable: Meltable) -> None:
    hero.memes["wonder"] += 1
    helper.memes["pride"] += 1
    world.say(
        f"At {setting.place}, where {setting.tall_image}, {hero.id} helped {helper.id} build "
        f"{meltable.phrase}. Folks said it was so big a sleepy mule could have sheltered in its shadow."
    )
    world.say(
        f"{setting.opening} By breakfast they had it standing tall, shining and grand, and {hero.id} felt proud enough to grin from ear to ear."
    )


def brag(world: World, helper: Entity, meltable: Meltable) -> None:
    world.say(
        f'"That {meltable.material} {meltable.shape_word} will stand straighter than a church steeple," '
        f'{helper.id} boomed. "If the sun minds its manners, we will carry off the blue ribbon for sure."'
    )


def warning(world: World, helper: Entity, hero: Entity, heat: Heat, meltable: Meltable) -> None:
    air = world.get("air")
    air.meters["heat"] = float(heat.severity)
    pred = predict_softening(world)
    world.facts["predicted_soft"] = pred["soft"]
    world.facts["predicted_drip"] = pred["drip"]
    world.say(
        f"But near noon {heat.image}. {helper.id} tipped back his hat and said, "
        f'"{hero.id}, keep it cool and covered, or this great {meltable.label} may melt before the judges arrive."'
    )


def misunderstand(world: World, hero: Entity, misunderstanding: Misunderstanding) -> None:
    hero.memes["trust"] += 1
    hero.memes["mistake"] += 1
    world.say(
        f"{hero.id} heard the word {misunderstanding.heard!r} and meant to help. "
        f"{hero.pronoun().capitalize()} hurried off to {misunderstanding.wrong_action}."
    )


def suspense(world: World, hero: Entity, helper: Entity, meltable: Meltable, heat: Heat) -> None:
    propagate(world, narrate=False)
    creation = world.get("creation")
    hero.memes["worry"] += 1
    helper.memes["worry"] += 1
    wobble = ""
    if creation.meters["drip"] >= THRESHOLD:
        wobble = f" A shiny {meltable.drip_word} slipped down its side."
    world.say(
        f"While {hero.id} was busy, the day grew hotter and hotter. The giant {meltable.label} gave a slow {meltable.soft_word}, "
        f"as if the sun had laid a warm hand right on its nose.{wobble}"
    )
    world.say(
        f"{helper.id} watched the path for {hero.pronoun('object')} and for the judges too. Any minute, one might appear before the other."
    )


def reveal(world: World, helper: Entity, hero: Entity, misunderstanding: Misunderstanding) -> None:
    world.say(
        f'When {hero.id} came back, {helper.id} blinked at once. "{misunderstanding.reveal}" '
        f'For one breath the fairgrounds felt still as a held sneeze.'
    )


def apply_fix(world: World, helper: Entity, hero: Entity, fix: Fix, saved: bool) -> None:
    creation = world.get("creation")
    if fix.shades:
        creation.meters["shade"] += 2
    if fix.cools:
        creation.meters["cool"] += 2
    if saved:
        creation.meters["soft"] = 0.0
        creation.meters["drip"] = 0.0
        creation.meters["wobble"] = 0.0
    body = fix.text if saved else fix.fail
    world.say(
        f"{helper.id} did not waste another blink. With arms like windmill beams, {helper.pronoun()} {body}."
    )


def ending_saved(world: World, hero: Entity, helper: Entity, meltable: Meltable) -> None:
    hero.memes["relief"] += 1
    helper.memes["relief"] += 1
    hero.memes["lesson"] += 1
    world.say(
        f"The judges came over just as the last scare passed. They found the huge {meltable.label} standing cool and proud, "
        f"and the ribbon looked no bigger than a blue raindrop pinned beside it."
    )
    world.say(
        f'"Next time I will ask what you mean before I go galloping off," {hero.id} said. {helper.id} laughed, '
        f'rumbled like a wagon over a bridge, and answered, "That is wisdom bigger than any fair prize."'
    )
    world.say(
        f"That evening the great {meltable.label} still gleamed in the long shade, and everyone in town swore they had seen a thing too stubborn to melt."
    )


def ending_drooped(world: World, hero: Entity, helper: Entity, meltable: Meltable) -> None:
    creation = world.get("creation")
    creation.meters["drooped"] += 1
    hero.memes["sad"] += 1
    helper.memes["sad"] += 1
    hero.memes["lesson"] += 1
    world.say(
        f"The judges arrived a blink too late to see the {meltable.label} at its tallest. It had sagged into a grand, shining heap, "
        f"still astonishing, but no longer fit for the blue ribbon."
    )
    world.say(
        f"{hero.id} looked near tears, but {helper.id} knelt beside {hero.pronoun('object')} and said that asking one clear question can save a mountain of trouble."
    )
    world.say(
        f"Long after the fair, people still told of the day a {meltable.label} nearly reached the sky and then tried to melt back into the earth."
    )


def tell(
    setting: Setting,
    meltable: Meltable,
    heat: Heat,
    misunderstanding: Misunderstanding,
    fix: Fix,
    hero_name: str = "Mae",
    hero_type: str = "girl",
    helper_name: str = "Uncle Buck",
    helper_type: str = "uncle",
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name, phrase=hero_name, role="hero"))
    helper = world.add(Entity(id="helper", kind="character", type=helper_type, label=helper_name, phrase=helper_name, role="helper"))
    air = world.add(Entity(id="air", type="weather", label=heat.label))
    creation = world.add(
        Entity(
            id="creation",
            type="creation",
            label=meltable.label,
            phrase=meltable.phrase,
            meltable=meltable.meltable,
            attrs={"limit": meltable.heat_limit},
            tags=set(meltable.tags),
        )
    )

    introduce(world, hero, helper, setting, meltable)
    brag(world, helper, meltable)

    world.para()
    warning(world, helper, hero, heat, meltable)
    misunderstand(world, hero, misunderstanding)

    world.para()
    suspense(world, hero, helper, meltable, heat)
    reveal(world, helper, hero, misunderstanding)

    world.para()
    saved = saved_in_time(meltable, heat, fix, misunderstanding)
    apply_fix(world, helper, hero, fix, saved)
    if saved:
        ending_saved(world, hero, helper, meltable)
        outcome = "saved"
    else:
        ending_drooped(world, hero, helper, meltable)
        outcome = "drooped"

    world.facts.update(
        hero=hero,
        helper=helper,
        hero_name=hero_name,
        helper_name=helper_name,
        setting=setting,
        meltable_cfg=meltable,
        heat=heat,
        misunderstanding=misunderstanding,
        fix=fix,
        creation=creation,
        outcome=outcome,
        saved=saved,
        softening_before_fix=world.facts.get("predicted_soft", False),
    )
    return world


@dataclass
class StoryParams:
    setting: str
    meltable: str
    heat: str
    misunderstanding: str
    fix: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


SETTINGS = {
    "fairgrounds": Setting(
        id="fairgrounds",
        place="the Red Prairie Fairgrounds",
        opening="The bandstand looked small enough to fit in one boot print beside it.",
        tall_image="the windmills looked like toothpicks against the sky",
        tags={"fair"},
    ),
    "riverbank": Setting(
        id="riverbank",
        place="the Big Bend Riverbank Fair",
        opening="The river rolled by as broad as a silver road.",
        tall_image="the cottonwoods looked like green feathers from a giant hat",
        tags={"river", "fair"},
    ),
    "canyon": Setting(
        id="canyon",
        place="the Echo Canyon Stock Show",
        opening="Even the echoes there sounded oversized.",
        tall_image="the canyon walls rose like orange castle towers",
        tags={"canyon", "fair"},
    ),
}

MELTABLES = {
    "butter_horse": Meltable(
        id="butter_horse",
        label="butter horse",
        phrase="a butter horse taller than the pie tent",
        material="butter",
        shape_word="horse",
        soft_word="sigh",
        drip_word="golden tear",
        heat_limit=1,
        meltable=True,
        tags={"butter", "melt"},
    ),
    "ice_rooster": Meltable(
        id="ice_rooster",
        label="ice rooster",
        phrase="an ice rooster with a tail like glass lace",
        material="ice",
        shape_word="rooster",
        soft_word="shiver",
        drip_word="clear bead",
        heat_limit=0,
        meltable=True,
        tags={"ice", "melt"},
    ),
    "chocolate_wagon": Meltable(
        id="chocolate_wagon",
        label="chocolate wagon",
        phrase="a chocolate wagon so wide three goats could nap under it",
        material="chocolate",
        shape_word="wagon",
        soft_word="wobble",
        drip_word="brown ribbon",
        heat_limit=1,
        meltable=True,
        tags={"chocolate", "melt"},
    ),
    "stone_rooster": Meltable(
        id="stone_rooster",
        label="stone rooster",
        phrase="a stone rooster carved from creek rock",
        material="stone",
        shape_word="rooster",
        soft_word="creak",
        drip_word="dust line",
        heat_limit=99,
        meltable=False,
        tags={"stone"},
    ),
}

HEATS = {
    "blazing_sun": Heat(
        id="blazing_sun",
        label="blazing sun",
        image="the blazing sun climbed so high even the hammer handles felt warm",
        severity=3,
        tags={"sun", "heat"},
    ),
    "fair_oven": Heat(
        id="fair_oven",
        label="fair-oven afternoon",
        image="the fair-oven afternoon wrapped the grounds in breath-hot air",
        severity=2,
        tags={"heat"},
    ),
    "warm_breeze": Heat(
        id="warm_breeze",
        label="warm breeze",
        image="a warm breeze wandered through the tents and hardly troubled anybody",
        severity=1,
        tags={"heat", "breeze"},
    ),
}

MISUNDERSTANDINGS = {
    "story_cool": Misunderstanding(
        id="story_cool",
        heard="cool",
        wrong_action="tell the creation the coolest stories she knew about moonlight trout and snow on fence posts",
        reveal='I meant cool with shade and cold, not cool with a fine story!',
        delay=1,
        tags={"misunderstanding"},
    ),
    "flower_cover": Misunderstanding(
        id="flower_cover",
        heard="covered",
        wrong_action="cover it with parade flowers and ribbons, which looked fancy but did not block the heat at all",
        reveal='I meant covered from the sun, not dressed for the parade!',
        delay=1,
        tags={"misunderstanding"},
    ),
    "blanket_cover": Misunderstanding(
        id="blanket_cover",
        heard="covered",
        wrong_action="fetch a thick wool blanket that held the heat close instead of chasing it away",
        reveal='Not that kind of covered. It needs shade and cold, not a hot blanket!',
        delay=2,
        tags={"misunderstanding"},
    ),
}

FIXES = {
    "shade_wagon": Fix(
        id="shade_wagon",
        label="shade wagon",
        sense=3,
        power=3,
        text="rolled the creation under a high shade wagon and hung wet canvas all around it until the hot light could not bite",
        fail="tried to roll the creation under a high shade wagon, but the heat had already bitten too deep and the corners kept slumping",
        qa_text="rolled it under a high shade wagon and cooled it with wet canvas",
        cools=True,
        shades=True,
        tags={"shade", "cooling"},
    ),
    "icehouse": Fix(
        id="icehouse",
        label="icehouse sled",
        sense=3,
        power=4,
        text="hauled it onto the icehouse sled and packed chipped ice around the base until the air itself seemed to shiver",
        fail="hauled it toward the icehouse sled, but even chipped ice could not undo all the drooping in time",
        qa_text="hauled it onto the icehouse sled and packed ice around it",
        cools=True,
        shades=True,
        tags={"icehouse", "cooling"},
    ),
    "canvas_tarp": Fix(
        id="canvas_tarp",
        label="canvas tarp",
        sense=2,
        power=2,
        text="snapped a pale canvas tarp above it and splashed the cloth with cold pump water",
        fail="snapped up a canvas tarp and splashed cold water on it, but the giant creation had already started giving way",
        qa_text="raised a canvas tarp and cooled the cloth with pump water",
        cools=True,
        shades=True,
        tags={"shade", "water"},
    ),
    "fan": Fix(
        id="fan",
        label="hand fan",
        sense=1,
        power=1,
        text="fanned at it with a seed-sack lid",
        fail="fanned at it with a seed-sack lid, which was no match at all for that heavy heat",
        qa_text="fanned at it with a seed-sack lid",
        cools=False,
        shades=False,
        tags={"fan"},
    ),
}

GIRL_NAMES = ["Mae", "Tilly", "June", "Nell", "Mabel", "Ruth"]
BOY_NAMES = ["Cal", "Jed", "Wes", "Otis", "Beau", "Hank"]
HELPER_NAMES = ["Uncle Buck", "Aunt Pearl", "Big Eli", "Miss Juniper", "Cousin Clay", "Old Maeve"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting in SETTINGS:
        for melt_id, meltable in MELTABLES.items():
            for heat_id, heat in HEATS.items():
                if not hazard_at_risk(meltable, heat):
                    continue
                for fix_id, fix in FIXES.items():
                    if fix.sense < SENSE_MIN:
                        continue
                    combos.append((setting, melt_id, heat_id, fix_id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    meltable = f["meltable_cfg"]
    heat = f["heat"]
    misunderstanding = f["misunderstanding"]
    outcome = f["outcome"]
    prompts = [
        f'Write a tall-tale story for a 3-to-5-year-old that includes the word "melt" and features a misunderstanding.',
        f"Tell a suspenseful fair-day story where {hero.label} misunderstands an urgent warning about a giant {meltable.label} in the {heat.label}.",
        f"Write a child-facing tall tale about {helper.label} and {hero.label}, where the wrong first idea makes the danger feel bigger before the true fix is found.",
    ]
    if outcome == "drooped":
        prompts.append(
            "Let the rescue come almost in time, but not quite, so the ending feels wistful and teaches the child to ask what someone means."
        )
    else:
        prompts.append(
            "End with the giant creation saved at the last moment, and show that asking one clear question can prevent trouble."
        )
    if misunderstanding.id == "story_cool":
        prompts.append('Use the word "cool" in a way that can be misunderstood.')
    return prompts


KNOWLEDGE = {
    "melt": [(
        "What does melt mean?",
        "Melt means something solid gets softer and turns runny when it becomes too warm. Ice, butter, and chocolate can melt."
    )],
    "butter": [(
        "Why can butter melt on a hot day?",
        "Butter gets soft when it is warm. In strong heat, it can slump and turn slippery."
    )],
    "ice": [(
        "Why does ice melt?",
        "Ice is frozen water. When the air around it gets warm, it changes back into liquid water."
    )],
    "chocolate": [(
        "Why can chocolate droop in the sun?",
        "Chocolate softens in heat. If it gets too warm, it loses its shape and starts to sag."
    )],
    "sun": [(
        "Why can the sun make things hot?",
        "Sunlight warms the ground and whatever it shines on. On a very hot day, that heat can build up quickly."
    )],
    "shade": [(
        "How does shade help on a hot day?",
        "Shade blocks direct sunlight. That helps things stay cooler than they would in the open sun."
    )],
    "cooling": [(
        "How can people keep something from melting?",
        "They can move it into shade or put cold things around it. Both ways lower the heat reaching it."
    )],
    "misunderstanding": [(
        "What is a misunderstanding?",
        "A misunderstanding happens when one person means one thing and another person thinks it means something else. Asking a question can help clear it up."
    )],
    "icehouse": [(
        "What is an icehouse?",
        "An icehouse is a cool place where people used to keep big blocks of ice. It helped food and other things stay cold."
    )],
}
KNOWLEDGE_ORDER = ["melt", "butter", "ice", "chocolate", "sun", "shade", "cooling", "misunderstanding", "icehouse"]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    meltable = f["meltable_cfg"]
    heat = f["heat"]
    misunderstanding = f["misunderstanding"]
    fix = f["fix"]
    outcome = f["outcome"]
    qa = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, who wanted to help, and {helper.label}, who was showing a giant {meltable.label} at the fair."
        ),
        (
            f"Why was everyone worried the {meltable.label} might melt?",
            f"They were worried because the {heat.label} was strong enough to soften {meltable.material}. That made the giant creation start to seem unsteady before the judges came."
        ),
        (
            f"What misunderstanding caused the trouble?",
            f"{hero.label} misunderstood the warning and went to {misunderstanding.wrong_action}. {helper.label} had meant to keep the creation cool with real shade and cold, not in that mistaken way."
        ),
    ]
    if outcome == "saved":
        qa.append(
            (
                "How did they save it?",
                f"{helper.label} {fix.qa_text}. That worked because the fix gave the giant creation shade and cooling before it could truly melt."
            )
        )
        qa.append(
            (
                "What did the child learn?",
                f"{hero.label} learned to ask what someone means before rushing off to help. One clear question would have stopped the misunderstanding at the start."
            )
        )
    else:
        qa.append(
            (
                "Did they save it in time?",
                f"Not quite. {helper.label} tried to help with {fix.label}, but the misunderstanding had used up too much time and the heat had already made the giant creation droop."
            )
        )
        qa.append(
            (
                "What lesson came from the ending?",
                f"The story teaches that a brave heart is good, but clear understanding matters too. Asking one question early can keep a small mistake from growing bigger."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"melt", "misunderstanding"}
    tags |= set(f["meltable_cfg"].tags)
    tags |= set(f["heat"].tags)
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
        flags = [name for name, on in (("meltable", e.meltable), ("cools", e.cools), ("shades", e.shades)) if on]
        if flags:
            bits.append(f"flags={flags}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
hazard(M, H) :- meltable(M), heat(H), can_melt(M), severity(H, S), limit(M, L), S > L.
sensible(F) :- fix(F), sense(F, S), sense_min(Min), S >= Min.
valid(St, M, H, F) :- setting(St), hazard(M, H), sensible(F).

score(V) :- chosen_meltable(M), chosen_heat(H), chosen_fix(F), chosen_misunderstanding(U),
            power(F, P), severity(H, S), delay(U, D), limit(M, L), V = P - (S + D - L).
saved :- score(V), V >= 0.
outcome(saved) :- saved.
outcome(drooped) :- not saved.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid, meltable in MELTABLES.items():
        lines.append(asp.fact("meltable", mid))
        lines.append(asp.fact("limit", mid, meltable.heat_limit))
        if meltable.meltable:
            lines.append(asp.fact("can_melt", mid))
    for hid, heat in HEATS.items():
        lines.append(asp.fact("heat", hid))
        lines.append(asp.fact("severity", hid, heat.severity))
    for uid, misunderstanding in MISUNDERSTANDINGS.items():
        lines.append(asp.fact("misunderstanding", uid))
        lines.append(asp.fact("delay", uid, misunderstanding.delay))
    for fid, fix in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("sense", fid, fix.sense))
        lines.append(asp.fact("power", fid, fix.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_meltable", params.meltable),
        asp.fact("chosen_heat", params.heat),
        asp.fact("chosen_fix", params.fix),
        asp.fact("chosen_misunderstanding", params.misunderstanding),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    meltable = MELTABLES[params.meltable]
    heat = HEATS[params.heat]
    fix = FIXES[params.fix]
    misunderstanding = MISUNDERSTANDINGS[params.misunderstanding]
    return "saved" if saved_in_time(meltable, heat, fix, misunderstanding) else "drooped"


CURATED = [
    StoryParams(
        setting="fairgrounds",
        meltable="butter_horse",
        heat="blazing_sun",
        misunderstanding="story_cool",
        fix="icehouse",
        hero_name="Mae",
        hero_type="girl",
        helper_name="Uncle Buck",
        helper_type="uncle",
    ),
    StoryParams(
        setting="riverbank",
        meltable="ice_rooster",
        heat="fair_oven",
        misunderstanding="flower_cover",
        fix="shade_wagon",
        hero_name="Cal",
        hero_type="boy",
        helper_name="Aunt Pearl",
        helper_type="aunt",
    ),
    StoryParams(
        setting="canyon",
        meltable="chocolate_wagon",
        heat="blazing_sun",
        misunderstanding="blanket_cover",
        fix="canvas_tarp",
        hero_name="Tilly",
        hero_type="girl",
        helper_name="Big Eli",
        helper_type="giant",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world: a giant meltable fair creation, a misunderstanding, suspense, and a tall-tale rescue."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--meltable", choices=MELTABLES)
    ap.add_argument("--heat", choices=HEATS)
    ap.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["uncle", "aunt", "giant"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.meltable and not MELTABLES[args.meltable].meltable:
        heat = HEATS[args.heat] if args.heat else next(iter(HEATS.values()))
        raise StoryError(explain_rejection(MELTABLES[args.meltable], heat))
    if args.meltable and args.heat:
        meltable = MELTABLES[args.meltable]
        heat = HEATS[args.heat]
        if not hazard_at_risk(meltable, heat):
            raise StoryError(explain_rejection(meltable, heat))
    if args.fix and FIXES[args.fix].sense < SENSE_MIN:
        raise StoryError(explain_fix(args.fix))

    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.meltable is None or c[1] == args.meltable)
        and (args.heat is None or c[2] == args.heat)
        and (args.fix is None or c[3] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting, meltable, heat, fix = rng.choice(sorted(combos))
    misunderstanding = args.misunderstanding or rng.choice(sorted(MISUNDERSTANDINGS))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)

    helper_type = args.helper_type or rng.choice(["uncle", "aunt", "giant"])
    if args.helper_name:
        helper_name = args.helper_name
    else:
        pool = {
            "uncle": ["Uncle Buck", "Uncle Reed", "Uncle Moss"],
            "aunt": ["Aunt Pearl", "Aunt Fern", "Aunt Iva"],
            "giant": ["Big Eli", "Old Maeve", "Cousin Clay"],
        }[helper_type]
        helper_name = rng.choice(pool)

    return StoryParams(
        setting=setting,
        meltable=meltable,
        heat=heat,
        misunderstanding=misunderstanding,
        fix=fix,
        hero_name=hero_name,
        hero_type=hero_type,
        helper_name=helper_name,
        helper_type=helper_type,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        meltable = MELTABLES[params.meltable]
        heat = HEATS[params.heat]
        misunderstanding = MISUNDERSTANDINGS[params.misunderstanding]
        fix = FIXES[params.fix]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter key: {err.args[0]})") from err

    if not hazard_at_risk(meltable, heat):
        raise StoryError(explain_rejection(meltable, heat))
    if fix.sense < SENSE_MIN:
        raise StoryError(explain_fix(fix.id))

    world = tell(
        setting=setting,
        meltable=meltable,
        heat=heat,
        misunderstanding=misunderstanding,
        fix=fix,
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        helper_name=params.helper_name,
        helper_type=params.helper_type,
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
        print("MISMATCH in compatible combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    c_sens = set(asp_sensible())
    p_sens = {f.id for f in sensible_fixes()}
    if c_sens == p_sens:
        print(f"OK: sensible fixes match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible fixes: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    mismatches = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story or "melt" not in sample.story.lower():
            raise StoryError("(Smoke test failed: generated story is empty or missing the seed word.)")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible fixes: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, meltable, heat, fix) combos:\n")
        for setting, meltable, heat, fix in combos:
            print(f"  {setting:11} {meltable:17} {heat:12} {fix}")
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
            header = f"### {p.hero_name} at {p.setting}: {p.meltable} in {p.heat} ({outcome_of(p)})"
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
