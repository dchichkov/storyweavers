#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/pidgin_snag_foreshadowing_animal_story.py
====================================================================

A standalone story world for a small animal tale about a young pidgin gathering
nest materials, noticing a warning sign first, and then facing a snag if the
wrong choice is made.

The world is built around one tight bit of common sense:
long looped things can snag a small bird, while short dry nesting materials are
safe. The story uses foreshadowing as simulated state: before the main trouble,
the child sees a caught scrap that quietly predicts what could happen later.

Run it
------
    python storyworlds/worlds/gpt-5.4/pidgin_snag_foreshadowing_animal_story.py
    python storyworlds/worlds/gpt-5.4/pidgin_snag_foreshadowing_animal_story.py --all
    python storyworlds/worlds/gpt-5.4/pidgin_snag_foreshadowing_animal_story.py --risky ribbon --spot thornbush
    python storyworlds/worlds/gpt-5.4/pidgin_snag_foreshadowing_animal_story.py --spot pond_reeds
    python storyworlds/worlds/gpt-5.4/pidgin_snag_foreshadowing_animal_story.py --trace --seed 7
    python storyworlds/worlds/gpt-5.4/pidgin_snag_foreshadowing_animal_story.py --qa --json
    python storyworlds/worlds/gpt-5.4/pidgin_snag_foreshadowing_animal_story.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    looped: bool = False
    hanging: bool = False
    safe_nesting: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "hen"}
        male = {"boy", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    home: str
    sky: str
    ground: str


@dataclass
class RiskyItem:
    id: str
    label: str
    phrase: str
    caught_example: str
    carry_text: str
    looped: bool = True
    hanging: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Spot:
    id: str
    label: str
    phrase: str
    snag_text: str
    can_snag: bool
    tags: set[str] = field(default_factory=set)


@dataclass
class SafeItem:
    id: str
    label: str
    phrase: str
    carry_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperAction:
    id: str
    label: str
    works_on: set[str]
    text: str
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


def _r_snag_fear(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.meters["snagged"] >= THRESHOLD:
        sig = ("snag_fear", "hero")
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["fear"] += 1
            world.get("nest").meters["unfinished"] += 1
            out.append("__snag__")
    return out


def _r_help_relief(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    helper = world.get("helper")
    if hero.meters["freed"] >= THRESHOLD:
        sig = ("help_relief", "hero")
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["relief"] += 1
            hero.memes["trust"] += 1
            helper.memes["care"] += 1
            out.append("__freed__")
    return out


CAUSAL_RULES = [
    Rule("snag_fear", "physical", _r_snag_fear),
    Rule("help_relief", "social", _r_help_relief),
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


def hazard_at_risk(item: RiskyItem, spot: Spot) -> bool:
    return item.looped and item.hanging and spot.can_snag


def action_fits(action: HelperAction, spot: Spot) -> bool:
    return spot.id in action.works_on


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place in PLACES:
        for item_id, item in RISKY_ITEMS.items():
            for spot_id, spot in SPOTS.items():
                for act_id, act in HELPER_ACTIONS.items():
                    if hazard_at_risk(item, spot) and action_fits(act, spot):
                        combos.append((place, item_id, spot_id, act_id))
    return combos


def predict_snag(world: World, item: RiskyItem, spot: Spot) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    if hazard_at_risk(item, spot):
        hero.meters["snagged"] += 1
        propagate(sim, narrate=False)
    return {
        "snagged": hero.meters["snagged"] >= THRESHOLD,
        "fear": hero.memes["fear"],
    }


def introduce(world: World, hero: Entity, place: Place) -> None:
    hero.memes["hope"] += 1
    world.say(
        f"In {place.label}, a young pidgin named {hero.id} was helping build a nest in {place.home}."
    )
    world.say(
        f"The morning sky over {place.sky} was pale and quiet, and {hero.id} wanted to bring back the finest things from {place.ground}."
    )


def foreshadow(world: World, hero: Entity, helper: Entity, item: RiskyItem, spot: Spot) -> None:
    hero.memes["notice"] += 1
    world.facts["foreshadowed"] = True
    world.say(
        f"Before {hero.id} began, {hero.pronoun()} noticed {item.caught_example} at {spot.phrase}."
    )
    world.say(
        f'"See that?" said {helper.id}. "Long things can catch there. A little pull can turn into a big snag."'
    )


def tempt(world: World, hero: Entity, item: RiskyItem) -> None:
    hero.memes["greed"] += 1
    world.say(
        f"But then {hero.id} spotted {item.phrase}. It looked soft and grand, and {hero.pronoun()} thought it would make the nest look special."
    )
    world.say(item.carry_text.format(name=hero.id))


def warn(world: World, hero: Entity, helper: Entity, item: RiskyItem, spot: Spot) -> None:
    pred = predict_snag(world, item, spot)
    world.facts["predicted_snag"] = pred["snagged"]
    helper.memes["care"] += 1
    if pred["snagged"]:
        world.say(
            f'"Please leave {item.label} alone," said {helper.id}. "If you tug it near {spot.label}, your little foot or wing could get caught."'
        )


def choose_risk(world: World, hero: Entity, item: RiskyItem) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f'{hero.id} fluttered closer. "I will be quick," {hero.pronoun()} said, and reached for {item.label} anyway.'
    )


def choose_safe(world: World, hero: Entity, safe_item: SafeItem, helper: Entity) -> None:
    hero.memes["wisdom"] += 1
    hero.memes["relief"] += 1
    helper.memes["care"] += 1
    world.say(
        f"{hero.id} looked again at the caught scrap and remembered the warning."
    )
    world.say(
        f"Instead of taking the long thing, {hero.pronoun()} chose {safe_item.phrase}. {safe_item.carry_text.format(name=hero.id)}"
    )


def snag(world: World, hero: Entity, item: RiskyItem, spot: Spot) -> None:
    hero.meters["snagged"] += 1
    hero.meters["struggle"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But the warning came true. {spot.snag_text}, and in one blink {item.label} made a hard little snag around {hero.id}'s foot."
    )
    world.say(
        f"{hero.id} beat {hero.pronoun('possessive')} wings and called out in a thin, frightened voice."
    )


def rescue(world: World, hero: Entity, helper: Entity, action: HelperAction) -> None:
    hero.meters["snagged"] = 0.0
    hero.meters["freed"] += 1
    hero.meters["struggle"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"{helper.id} hurried over and {action.text}."
    )
    world.say(
        f"Soon {hero.id} was free again, though {hero.pronoun()} stayed pressed close to {helper.id} for a moment while {hero.pronoun('possessive')} heart slowed down."
    )


def lesson(world: World, hero: Entity, helper: Entity, safe_item: SafeItem) -> None:
    hero.memes["lesson"] += 1
    helper.memes["care"] += 1
    world.say(
        f'"A pretty thing is not always a safe thing," said {helper.id} gently. "For a nest, {safe_item.label} is better than loops and strings."'
    )
    world.say(
        f"{hero.id} nodded. The small warning from the morning no longer felt like a small warning at all."
    )


def ending_safe(world: World, hero: Entity, helper: Entity, safe_item: SafeItem, place: Place) -> None:
    world.get("nest").meters["built"] += 1
    hero.memes["joy"] += 1
    hero.memes["pride"] += 1
    world.say(
        f"Together they gathered {safe_item.label} until the nest in {place.home} grew round, dry, and strong."
    )
    world.say(
        f"At sunset, {hero.id} tucked the last piece into place and felt proud that the nest held warmth, not trouble."
    )


def tell(place: Place, risky_item: RiskyItem, spot: Spot, safe_item: SafeItem,
         action: HelperAction, heed_warning: bool,
         hero_name: str = "Pip", helper_name: str = "Mara") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type="bird", role="hero", label="the young pidgin"))
    helper = world.add(Entity(id=helper_name, kind="character", type="bird", role="helper", label="the older dove"))
    nest = world.add(Entity(id="nest", type="nest", label="the nest"))
    risky = world.add(Entity(id="risky", type="material", label=risky_item.label, looped=risky_item.looped, hanging=risky_item.hanging))
    safe = world.add(Entity(id="safe", type="material", label=safe_item.label, safe_nesting=True))
    snag_spot = world.add(Entity(id="spot", type="spot", label=spot.label))
    world.facts["heeded"] = heed_warning

    introduce(world, hero, place)
    foreshadow(world, hero, helper, risky_item, spot)

    world.para()
    tempt(world, hero, risky_item)
    warn(world, hero, helper, risky_item, spot)

    world.para()
    if heed_warning:
        choose_safe(world, hero, safe_item, helper)
        ending_safe(world, hero, helper, safe_item, place)
        outcome = "averted"
    else:
        choose_risk(world, hero, risky_item)
        snag(world, hero, risky_item, spot)
        world.para()
        rescue(world, hero, helper, action)
        lesson(world, hero, helper, safe_item)
        world.para()
        choose_safe(world, hero, safe_item, helper)
        ending_safe(world, hero, helper, safe_item, place)
        outcome = "rescued"

    world.facts.update(
        place=place,
        risky_item=risky_item,
        spot_cfg=spot,
        safe_item=safe_item,
        action=action,
        hero=hero,
        helper=helper,
        nest=nest,
        outcome=outcome,
        snagged=outcome == "rescued",
    )
    return world


PLACES = {
    "rooftop": Place("rooftop", "the old market rooftop", "the chimneys", "the warm roof tiles"),
    "garden": Place("garden", "the bakery garden wall", "the plum tree", "the soft grass below"),
    "harbor": Place("harbor", "a beam above the harbor", "the masts", "the windy boards"),
}

RISKY_ITEMS = {
    "ribbon": RiskyItem(
        "ribbon",
        "the ribbon",
        "a long pink ribbon trailing from a crate",
        "a strip of pink ribbon already caught",
        "{name} gripped one end in {name}'s beak and gave it an eager tug.",
        tags={"ribbon", "snag"},
    ),
    "string": RiskyItem(
        "string",
        "the string",
        "a silver-gray string hanging from a basket",
        "a loose string already wrapped around a twig",
        "{name} pecked at the dangling string and tried to pull it free.",
        tags={"string", "snag"},
    ),
    "yarn": RiskyItem(
        "yarn",
        "the yarn",
        "a soft piece of blue yarn dangling from a fence post",
        "a blue thread twisted around a thorn",
        "{name} lifted the yarn and tried to drag the long tail after it.",
        tags={"yarn", "snag"},
    ),
}

SPOTS = {
    "thornbush": Spot(
        "thornbush",
        "the thornbush",
        "the thornbush below the wall",
        "The loose end slid through the thorns",
        True,
        tags={"thorn", "snag"},
    ),
    "crate_corner": Spot(
        "crate_corner",
        "the sharp crate corner",
        "the cracked corner of an old fruit crate",
        "The end whipped around the splintered corner",
        True,
        tags={"crate", "snag"},
    ),
    "pond_reeds": Spot(
        "pond_reeds",
        "the pond reeds",
        "the reeds by the pond",
        "The end drifted over the reeds",
        False,
        tags={"pond"},
    ),
}

SAFE_ITEMS = {
    "straw": SafeItem(
        "straw",
        "straw",
        "a short bundle of dry straw",
        "{name} carried the short straw easily, and nothing trailed behind.",
        tags={"straw", "nest"},
    ),
    "twigs": SafeItem(
        "twigs",
        "twigs",
        "two neat little twigs",
        "{name} picked up the twigs one by one, and they sat neatly in {name}'s beak.",
        tags={"twig", "nest"},
    ),
    "grass": SafeItem(
        "grass",
        "grass",
        "soft dry grass",
        "{name} gathered the grass in small mouthfuls that did not loop or drag.",
        tags={"grass", "nest"},
    ),
}

HELPER_ACTIONS = {
    "lift_thorn": HelperAction(
        "lift_thorn",
        "lifted the thorn aside",
        {"thornbush"},
        "lifted the thorn aside with one careful tug and unwound the loop with her beak",
        "lifted the thorn aside and unwound the loop with her beak",
        tags={"help", "thorn"},
    ),
    "backtrack_corner": HelperAction(
        "backtrack_corner",
        "backtracked the loop",
        {"crate_corner"},
        "followed the loop back around the crate corner and eased it loose instead of yanking",
        "followed the loop back around the crate corner and eased it loose",
        tags={"help", "crate"},
    ),
}

TRAITS = ["eager", "bright", "small", "curious", "quick"]
NAMES = ["Pip", "Tala", "Nico", "Mimi", "Luma", "Bibi"]


@dataclass
class StoryParams:
    place: str
    risky: str
    spot: str
    safe: str
    action: str
    heed_warning: bool
    hero_name: str
    helper_name: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "ribbon": [("Why can a ribbon be risky for a little bird?",
                "A long ribbon can trail, wrap, and catch on things. That can trap a little foot or wing.")],
    "string": [("Why can string be dangerous for birds?",
                "String can loop around toes, wings, or branches. Something soft can still be unsafe when it tangles.")],
    "yarn": [("Can yarn cause trouble for animals?",
              "Yes. Yarn can twist into loops and catch on claws or sticks, so animals can get stuck.")],
    "thorn": [("Why do thorns snag things?",
               "Thorns are sharp little points. They catch cloth, fur, and string when something brushes past them.")],
    "crate": [("Why can a sharp corner catch a loop?",
               "A loop can hook around a hard corner and tighten when you pull. Pulling harder can make it worse.")],
    "straw": [("Why is straw good for a nest?",
               "Dry straw is light, short, and easy to carry. It helps make a nest warm without trailing in loops.")],
    "twig": [("Why do birds use twigs in nests?",
              "Twigs are stiff and short, so they help hold the nest's shape. They are easier to place than long dangling things.")],
    "grass": [("Why is dry grass useful for nesting?",
               "Dry grass is soft and light. Birds can tuck it into a nest to make a cozy lining.")],
    "help": [("What should an animal do if something gets tangled?",
              "It should stop struggling and get help if it can. Calm help can loosen a tangle more safely than yanking harder.")],
}
KNOWLEDGE_ORDER = ["ribbon", "string", "yarn", "thorn", "crate", "straw", "twig", "grass", "help"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    risky = f["risky_item"]
    safe = f["safe_item"]
    spot = f["spot_cfg"]
    outcome = f["outcome"]
    if outcome == "averted":
        return [
            'Write an Animal Story for a 3-to-5-year-old that includes the word "pidgin" and the word "snag". Use gentle foreshadowing before the problem is avoided.',
            f"Tell a small bird story where a young pidgin sees a warning sign near {spot.label}, remembers it, and chooses {safe.label} instead of {risky.label}.",
            f"Write a child-facing animal tale where {hero.id} learns that a pretty thing can still be unsafe, and the ending shows a strong warm nest made with {safe.label}.",
        ]
    return [
        'Write an Animal Story for a 3-to-5-year-old that includes the word "pidgin" and the word "snag". Use foreshadowing so the warning appears before the trouble.',
        f"Tell a gentle cautionary story where a young pidgin ignores a warning about {risky.label}, gets caught in a snag near {spot.label}, and is helped free.",
        f"Write a simple animal tale where the ending turns scary trouble into wisdom, and the bird finishes the nest safely with {safe.label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    risky = f["risky_item"]
    safe = f["safe_item"]
    spot = f["spot_cfg"]
    action = f["action"]
    outcome = f["outcome"]

    qa: list[tuple[str, str]] = [
        ("Who is the story about?",
         f"It is about a young pidgin named {hero.id} and {helper.id}, the older bird helping with the nest."),
        ("What was the young pidgin trying to do?",
         f"{hero.id} was trying to gather nest materials. The goal was to make the nest warm and strong."),
        ("What was the warning sign at the beginning?",
         f"{hero.id} first saw {risky.caught_example} at {spot.phrase}. That early image quietly warned what kind of trouble could happen later."),
        (f"Why did {helper.id} warn {hero.id} about {risky.label}?",
         f"{helper.id} warned that the long piece could catch near {spot.label}. The danger was not how pretty it looked, but how it could loop and trap a small bird."),
    ]
    if outcome == "rescued":
        qa.append((
            f"What happened when {hero.id} tried to take {risky.label}?",
            f"{hero.id} got caught in a snag when the long piece tightened around {hero.pronoun('possessive')} foot. The earlier warning came true because the trailing end caught at {spot.label}."
        ))
        qa.append((
            f"How did {helper.id} help?",
            f"{helper.id} {action.qa_text}. She solved the problem by loosening it carefully instead of pulling harder."
        ))
        qa.append((
            "How did the story end?",
            f"It ended safely, with the nest finished from {safe.label} instead of {risky.label}. The ending proves that {hero.id} changed from chasing a pretty thing to choosing a safe one."
        ))
    else:
        qa.append((
            f"What did {hero.id} do after remembering the warning?",
            f"{hero.id} left {risky.label} alone and picked {safe.label} instead. The foreshadowing mattered because the warning sign helped {hero.pronoun('object')} make a wiser choice."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with a warm, strong nest made from {safe.label}. Nothing got tangled because {hero.id} listened before trouble began."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["risky_item"].tags) | set(f["safe_item"].tags)
    tags |= set(f["spot_cfg"].tags)
    if f["outcome"] == "rescued":
        tags |= set(f["action"].tags)
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
        flags = [n for n, on in (("looped", e.looped), ("hanging", e.hanging), ("safe_nesting", e.safe_nesting)) if on]
        if flags:
            bits.append(f"flags={flags}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("rooftop", "ribbon", "thornbush", "straw", "lift_thorn", False, "Pip", "Mara", "eager"),
    StoryParams("garden", "string", "crate_corner", "twigs", "backtrack_corner", False, "Luma", "Mara", "curious"),
    StoryParams("harbor", "yarn", "thornbush", "grass", "lift_thorn", True, "Nico", "Mimi", "bright"),
    StoryParams("garden", "ribbon", "crate_corner", "straw", "backtrack_corner", True, "Bibi", "Tala", "quick"),
]


def explain_rejection(item: RiskyItem, spot: Spot, action: Optional[HelperAction] = None) -> str:
    if not spot.can_snag:
        return (
            f"(No story: {item.label} may trail, but {spot.label} does not create a believable snag here. "
            f"Without a real trap, the foreshadowing and rescue do not have a solid cause.)"
        )
    if action is not None and not action_fits(action, spot):
        return (
            f"(No story: the helper action '{action.id}' does not fit {spot.label}. "
            f"Pick a rescue that matches the place where the tangle happens.)"
        )
    return "(No story: this combination does not create a plausible snag.)"


def outcome_of(params: StoryParams) -> str:
    return "averted" if params.heed_warning else "rescued"


ASP_RULES = r"""
hazard(I, S) :- risky(I), spot(S), looped(I), hanging(I), can_snag(S).
fits(A, S) :- action(A), works_on(A, S).
valid(P, I, S, A) :- place(P), hazard(I, S), fits(A, S).

outcome(averted) :- heed_warning.
outcome(rescued) :- not heed_warning.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for iid, item in RISKY_ITEMS.items():
        lines.append(asp.fact("risky", iid))
        if item.looped:
            lines.append(asp.fact("looped", iid))
        if item.hanging:
            lines.append(asp.fact("hanging", iid))
    for sid, spot in SPOTS.items():
        lines.append(asp.fact("spot", sid))
        if spot.can_snag:
            lines.append(asp.fact("can_snag", sid))
    for aid, action in HELPER_ACTIONS.items():
        lines.append(asp.fact("action", aid))
        for sid in sorted(action.works_on):
            lines.append(asp.fact("works_on", aid, sid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = asp.fact("heed_warning") if params.heed_warning else ""
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    cset, pset = set(asp_valid_combos()), set(valid_combos())
    if cset == pset:
        print(f"OK: gate matches valid_combos() ({len(cset)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cset - pset:
            print("  only in clingo:", sorted(cset - pset))
        if pset - cset:
            print("  only in python:", sorted(pset - cset))

    cases = list(CURATED)
    for s in range(20):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(s))
            p.seed = s
            cases.append(p)
        except StoryError:
            rc = 1
            print(f"resolve_params crashed on seed {s}")
            break

    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal story world: a young pidgin, a foreshadowed snag, and a safer nesting choice."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--risky", choices=RISKY_ITEMS)
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--safe", choices=SAFE_ITEMS)
    ap.add_argument("--action", choices=HELPER_ACTIONS)
    ap.add_argument("--heed-warning", dest="heed_warning", action="store_true",
                    help="the young bird listens and avoids the snag")
    ap.add_argument("--ignore-warning", dest="heed_warning", action="store_false",
                    help="the young bird ignores the warning and gets snagged")
    ap.set_defaults(heed_warning=None)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.risky and args.spot:
        item, spot = RISKY_ITEMS[args.risky], SPOTS[args.spot]
        if not hazard_at_risk(item, spot):
            raise StoryError(explain_rejection(item, spot))
    if args.action and args.spot:
        act, spot = HELPER_ACTIONS[args.action], SPOTS[args.spot]
        probe = RISKY_ITEMS[args.risky] if args.risky else next(iter(RISKY_ITEMS.values()))
        if not action_fits(act, spot):
            raise StoryError(explain_rejection(probe, spot, act))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.risky is None or c[1] == args.risky)
        and (args.spot is None or c[2] == args.spot)
        and (args.action is None or c[3] == args.action)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, risky, spot, action = rng.choice(sorted(combos))
    safe = args.safe or rng.choice(sorted(SAFE_ITEMS))
    heed = args.heed_warning if args.heed_warning is not None else rng.choice([True, False])
    names = rng.sample(NAMES, 2)
    trait = rng.choice(TRAITS)
    return StoryParams(place, risky, spot, safe, action, heed, names[0], names[1], trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place],
        RISKY_ITEMS[params.risky],
        SPOTS[params.spot],
        SAFE_ITEMS[params.safe],
        HELPER_ACTIONS[params.action],
        params.heed_warning,
        params.hero_name,
        params.helper_name,
    )
    world.get("hero").traits.append(params.trait)
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
        print(f"{len(combos)} compatible (place, risky, spot, action) combos:\n")
        for place, risky, spot, action in combos:
            print(f"  {place:8} {risky:7} {spot:12} {action}")
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
            header = f"### {p.hero_name}: {p.risky} near {p.spot} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()
