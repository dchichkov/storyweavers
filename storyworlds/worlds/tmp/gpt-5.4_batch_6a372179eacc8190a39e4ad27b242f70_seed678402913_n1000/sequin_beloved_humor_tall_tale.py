#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/sequin_beloved_humor_tall_tale.py
============================================================

A small tall-tale storyworld about a child, a beloved parade item, and one
outrageously runaway sequin.

The domain is deliberately narrow and state-driven:

- a child treasures a beloved item for a town parade
- the item wears one giant sequin
- a comic gust blasts the sequin loose
- the sequin lands somewhere awkward
- a helper chooses a sensible way to get it back
- the ending proves whether the beloved item returns to the parade shining again

The story leans playful and exaggerated, but the world model still enforces
basic reasonableness: tiny gusts cannot rip off firmly sewn sequins, and some
retrieval methods simply do not fit some landing spots.

Run it
------
    python storyworlds/worlds/gpt-5.4/sequin_beloved_humor_tall_tale.py
    python storyworlds/worlds/gpt-5.4/sequin_beloved_humor_tall_tale.py --item hat --gust tuba_blast
    python storyworlds/worlds/gpt-5.4/sequin_beloved_humor_tall_tale.py --spot roof --method spatula
    python storyworlds/worlds/gpt-5.4/sequin_beloved_humor_tall_tale.py --all
    python storyworlds/worlds/gpt-5.4/sequin_beloved_humor_tall_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/sequin_beloved_humor_tall_tale.py --verify
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
        female = {"girl", "mother", "aunt", "woman"}
        male = {"boy", "father", "uncle", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}.get(
            self.type, self.type
        )


@dataclass
class ItemCfg:
    id: str
    label: str
    phrase: str
    attachment: int
    wear_text: str
    boast: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SequinCfg:
    id: str
    label: str
    phrase: str
    gleam: str
    weight: int
    tags: set[str] = field(default_factory=set)


@dataclass
class GustCfg:
    id: str
    label: str
    power: int
    blast_text: str
    boast_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SpotCfg:
    id: str
    label: str
    phrase: str
    height: int
    sticky: bool = False
    snaggy: bool = False
    soft: bool = False
    scenic_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class MethodCfg:
    id: str
    label: str
    phrase: str
    sense: int
    reach: int
    works_sticky: bool = False
    works_snaggy: bool = False
    works_soft: bool = False
    success_text: str = ""
    fail_text: str = ""
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    item: str
    sequin: str
    gust: str
    spot: str
    method: str
    hero_name: str
    hero_gender: str
    helper_type: str
    trait: str
    seed: Optional[int] = None


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


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    item = world.get("item")
    sequin = world.get("sequin")
    if sequin.meters["flying"] >= THRESHOLD:
        sig = ("worry", hero.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["worry"] += 1
            item.memes["beloved"] += 1
            out.append("__worry__")
    return out


def _r_laughter(world: World) -> list[str]:
    out: list[str] = []
    helper = world.get("helper")
    hero = world.get("hero")
    if helper.memes["joke"] >= THRESHOLD:
        sig = ("laughter", hero.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["hope"] += 1
            out.append("__laugh__")
    return out


CAUSAL_RULES = [
    Rule(name="worry", tag="emotional", apply=_r_worry),
    Rule(name="laughter", tag="emotional", apply=_r_laughter),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(s for s in lines if not s.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


ITEMS = {
    "hat": ItemCfg(
        id="hat",
        label="hat",
        phrase="a beloved parade hat with a brim as wide as a wagon wheel",
        attachment=2,
        wear_text="balanced that hat on {hero_pos} head as proudly as a mayor balances a speech",
        boast="Folks said the hat could shade three chickens and half a piano bench.",
        tags={"hat", "parade"},
    ),
    "boot": ItemCfg(
        id="boot",
        label="boot",
        phrase="a beloved dancing boot polished till it winked at passing clouds",
        attachment=2,
        wear_text="stomped one boot so smartly that the road seemed to clap back",
        boast="Some people swore that boot had kicked pebbles clear into next Thursday.",
        tags={"boot", "parade"},
    ),
    "cape": ItemCfg(
        id="cape",
        label="cape",
        phrase="a beloved parade cape that could have served as a picnic tent for six mice",
        attachment=3,
        wear_text="swished that cape behind {hero_obj} like a bright red sunset learning to walk",
        boast="When it billowed, even the barber pole looked underdressed.",
        tags={"cape", "parade"},
    ),
}

SEQUINS = {
    "star": SequinCfg(
        id="star",
        label="star sequin",
        phrase="a sequin star",
        gleam="so bright it could make a sleepy spoon sit up straight",
        weight=1,
        tags={"sequin", "star"},
    ),
    "moon": SequinCfg(
        id="moon",
        label="moon sequin",
        phrase="a moon-shaped sequin",
        gleam="so shiny a crow once tried to salute it",
        weight=2,
        tags={"sequin", "moon"},
    ),
    "sun": SequinCfg(
        id="sun",
        label="sun sequin",
        phrase="a sunburst sequin",
        gleam="so flashing and gold that butter looked pale beside it",
        weight=2,
        tags={"sequin", "sun"},
    ),
}

GUSTS = {
    "goose_honk": GustCfg(
        id="goose_honk",
        label="goose honk",
        power=2,
        blast_text="a parade goose leaned back and honked so hard the bunting flapped and the pickle jars shivered",
        boast_text="That honk sounded less like a bird and more like a brass band falling down a hill.",
        tags={"goose", "wind"},
    ),
    "tuba_blast": GustCfg(
        id="tuba_blast",
        label="tuba blast",
        power=3,
        blast_text="the town tuba player puffed one mighty note, and the note came out with enough wind to straighten six neckties at once",
        boast_text="Old Mr. Wren claimed that blast nearly rolled his mustache into a tidy coil.",
        tags={"tuba", "wind", "music"},
    ),
    "mule_sneeze": GustCfg(
        id="mule_sneeze",
        label="mule sneeze",
        power=4,
        blast_text="the mayor's mule sneezed a sneeze so huge that dust rose, hats tilted, and one pie changed its mind about staying cool",
        boast_text="People talked about that sneeze the way sailors talk about storms.",
        tags={"mule", "wind"},
    ),
}

SPOTS = {
    "tree": SpotCfg(
        id="tree",
        label="apple tree",
        phrase="the top fork of the apple tree",
        height=2,
        sticky=False,
        snaggy=True,
        scenic_text="It twinkled there between two leaves like a tiny sheriff's badge for squirrels.",
        tags={"tree", "high"},
    ),
    "roof": SpotCfg(
        id="roof",
        label="bandstand roof",
        phrase="the slanted bandstand roof",
        height=3,
        sticky=False,
        snaggy=False,
        scenic_text="It skidded to the roof ridge and flashed at the whole parade like it had taken charge.",
        tags={"roof", "high"},
    ),
    "pie": SpotCfg(
        id="pie",
        label="pie cart",
        phrase="the top crust of the blueberry pie on Miss Tilda's cart",
        height=1,
        sticky=True,
        snaggy=False,
        scenic_text="The sequin sank into the glossy filling and sat there like a tiny moon in a purple swamp.",
        tags={"pie", "sticky"},
    ),
    "hay": SpotCfg(
        id="hay",
        label="hay wagon",
        phrase="the tallest hump on the hay wagon",
        height=1,
        sticky=False,
        snaggy=False,
        soft=True,
        scenic_text="It vanished in the gold fluff so neatly that even the hay looked smug.",
        tags={"hay", "soft"},
    ),
}

METHODS = {
    "ladder": MethodCfg(
        id="ladder",
        label="ladder",
        phrase="a borrowed ladder",
        sense=3,
        reach=3,
        works_snaggy=True,
        works_soft=True,
        success_text="set up a ladder, climbed steady as a cat with chores, and plucked the sequin free",
        fail_text="set up a ladder, but the sequin kept slipping away where fingers could not grip it",
        qa_text="used a ladder to reach the sequin and take it down safely",
        tags={"ladder", "reach"},
    ),
    "spatula": MethodCfg(
        id="spatula",
        label="pie spatula",
        phrase="Miss Tilda's pie spatula",
        sense=3,
        reach=1,
        works_sticky=True,
        success_text="slid a pie spatula under the sticky sequin and lifted it out with only one blueberry wobble",
        fail_text="waved a pie spatula in the air, which was about as helpful as buttering the moon",
        qa_text="used a pie spatula to slide the sequin out of the pie",
        tags={"spatula", "pie"},
    ),
    "rake": MethodCfg(
        id="rake",
        label="long rake",
        phrase="a long orchard rake",
        sense=2,
        reach=2,
        works_snaggy=True,
        works_soft=True,
        success_text="used a long rake to tease the sequin loose and pull it down without bending it",
        fail_text="raked and poked, but the sequin only danced farther from reach",
        qa_text="used a long rake to pull the sequin down",
        tags={"rake", "reach"},
    ),
    "jump": MethodCfg(
        id="jump",
        label="mighty jump",
        phrase="one mighty jump",
        sense=1,
        reach=1,
        works_soft=True,
        success_text="jumped once and caught the sequin in midair",
        fail_text="jumped and flapped and nearly hugged the wind, but never touched the sequin",
        qa_text="jumped up and grabbed the sequin",
        tags={"jump"},
    ),
}

GIRL_NAMES = ["Mabel", "Lula", "Pearl", "Daisy", "Tess", "Ruby", "Nell", "Josie"]
BOY_NAMES = ["Jeb", "Otis", "Cal", "Hank", "Milo", "Benny", "Earl", "Wade"]
TRAITS = ["cheerful", "plucky", "boastful", "sparky", "grinning", "lively"]


def sequin_at_risk(item: ItemCfg, sequin: SequinCfg, gust: GustCfg) -> bool:
    return gust.power >= item.attachment + sequin.weight - 1


def method_works(method: MethodCfg, spot: SpotCfg) -> bool:
    if method.reach < spot.height:
        return False
    if spot.sticky:
        return method.works_sticky
    if spot.snaggy:
        return method.works_snaggy
    if spot.soft:
        return method.works_soft
    return method.reach >= spot.height


def sensible_methods() -> list[MethodCfg]:
    return [m for m in METHODS.values() if m.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for item_id, item in ITEMS.items():
        for sequin_id, sequin in SEQUINS.items():
            for gust_id, gust in GUSTS.items():
                if not sequin_at_risk(item, sequin, gust):
                    continue
                for spot_id in SPOTS:
                    combos.append((item_id, sequin_id, gust_id, spot_id))
    return combos


def explain_rejection(item: ItemCfg, sequin: SequinCfg, gust: GustCfg) -> str:
    need = item.attachment + sequin.weight - 1
    return (
        f"(No story: {gust.label} is not strong enough to tear {sequin.phrase} loose from the "
        f"{item.label}. This world needs a real comic gust, and that choice only has power "
        f"{gust.power} when at least {need} is needed.)"
    )


def explain_method(method_id: str, spot_id: str) -> str:
    method = METHODS[method_id]
    spot = SPOTS[spot_id]
    return (
        f"(Refusing method '{method_id}': {method.phrase} does not fit {spot.phrase}. "
        f"Pick a method that can really reach and handle that landing spot.)"
    )


def predict_recovery(world: World, spot_id: str, method_id: str) -> dict:
    sim = world.copy()
    spot = SPOTS[spot_id]
    method = METHODS[method_id]
    do_blast(sim, narrate=False)
    land(sim, spot, narrate=False)
    use_method(sim, method, spot, narrate=False)
    return {
        "recovered": sim.get("sequin").meters["recovered"] >= THRESHOLD,
        "worry": sim.get("hero").memes["worry"],
    }


def do_blast(world: World, narrate: bool = True) -> None:
    gust: GustCfg = world.facts["gust_cfg"]
    sequin = world.get("sequin")
    item = world.get("item")
    sequin.meters["attached"] = 0.0
    sequin.meters["flying"] += 1
    item.meters["plain"] += 1
    propagate(world, narrate=narrate)


def land(world: World, spot: SpotCfg, narrate: bool = True) -> None:
    sequin = world.get("sequin")
    sequin.attrs["spot"] = spot.id
    sequin.meters["flying"] = 0.0
    sequin.meters["lost"] += 1
    if narrate:
        world.say(f"The sequin shot through town and landed on {spot.phrase}.")
        world.say(spot.scenic_text)


def use_method(world: World, method: MethodCfg, spot: SpotCfg, narrate: bool = True) -> None:
    helper = world.get("helper")
    sequin = world.get("sequin")
    hero = world.get("hero")
    helper.memes["joke"] += 1
    propagate(world, narrate=False)
    if method_works(method, spot):
        sequin.meters["recovered"] += 1
        sequin.meters["lost"] = 0.0
        if narrate:
            world.say(
                f"{helper.label_word.capitalize()} grabbed {method.phrase}, "
                f"{method.success_text}."
            )
    else:
        if narrate:
            world.say(
                f"{helper.label_word.capitalize()} tried {method.phrase} and {method.fail_text}."
            )
        hero.memes["worry"] += 1


def reattach(world: World, narrate: bool = True) -> None:
    item = world.get("item")
    sequin = world.get("sequin")
    hero = world.get("hero")
    item.meters["plain"] = 0.0
    item.meters["shiny"] += 1
    sequin.meters["attached"] = 1.0
    hero.memes["relief"] += 1
    hero.memes["joy"] += 1
    if narrate:
        world.say(
            f"With three quick stitches and one proud pat, the {sequin.label} went back on the "
            f"{item.label} where it belonged."
        )


def patch_plain(world: World, narrate: bool = True) -> None:
    hero = world.get("hero")
    item = world.get("item")
    helper = world.get("helper")
    hero.memes["acceptance"] += 1
    helper.memes["care"] += 1
    item.memes["beloved"] += 1
    if narrate:
        world.say(
            f'"A beloved thing does not stop being beloved just because it is missing one sparkle," '
            f"{helper.label_word} said."
        )


def intro(world: World) -> None:
    hero = world.get("hero")
    item = world.get("item")
    sequin = world.get("sequin")
    item_cfg: ItemCfg = world.facts["item_cfg"]
    sequin_cfg: SequinCfg = world.facts["sequin_cfg"]
    world.say(
        f"In a town that took parade day as seriously as breakfast, {hero.id} owned "
        f"{item_cfg.phrase}."
    )
    world.say(
        f"{hero.pronoun().capitalize()} {item_cfg.wear_text.format(hero_pos=hero.pronoun('possessive'), hero_obj=hero.pronoun('object'))}."
    )
    world.say(item_cfg.boast)
    world.say(
        f"Best of all, the {item.label} wore {sequin_cfg.phrase}, {sequin_cfg.gleam}, "
        f"and that shining speck was the part {hero.id} loved best."
    )


def parade_setup(world: World) -> None:
    hero = world.get("hero")
    helper = world.get("helper")
    gust: GustCfg = world.facts["gust_cfg"]
    world.say(
        f"On parade morning, {hero.id} marched down Main Street beside {hero.pronoun('possessive')} "
        f"{helper.label_word}, grinning so wide it nearly needed suspenders."
    )
    world.say(gust.boast_text)


def blast_scene(world: World) -> None:
    gust: GustCfg = world.facts["gust_cfg"]
    hero = world.get("hero")
    item = world.get("item")
    sequin = world.get("sequin")
    do_blast(world)
    world.say(
        f"Then {gust.blast_text}. Off popped the {sequin.label} from the {item.label}, "
        f"and away it sailed like a silver flapjack with urgent business."
    )
    if hero.memes["worry"] >= THRESHOLD:
        world.say(
            f"{hero.id} clapped both hands to {hero.pronoun('possessive')} cheeks. "
            f'"My sequin!" {hero.pronoun()} cried.'
        )


def helper_plan(world: World, spot: SpotCfg, method: MethodCfg) -> None:
    helper = world.get("helper")
    hero = world.get("hero")
    pred = predict_recovery(world, spot.id, method.id)
    world.facts["predicted_recovered"] = pred["recovered"]
    world.say(
        f'{helper.label_word.capitalize()} tipped {helper.pronoun("possessive")} hat and squinted at '
        f"{spot.phrase}."
    )
    if pred["recovered"]:
        world.say(
            f'"Do not fret," {helper.pronoun()} said. "That sequin is flashy, but it still has to obey '
            f'ordinary reaching."'
        )
    else:
        world.say(
            f'"Well now," {helper.pronoun()} said, "that plan is as crooked as a banana fence, but we '
            f'will try it once so the town can learn something."'
        )
    hero.memes["trust"] += 1


def ending_image(world: World, recovered: bool) -> None:
    hero = world.get("hero")
    item = world.get("item")
    if recovered:
        world.say(
            f"When {hero.id} stepped back into the parade, the {item.label} winked so brightly that "
            f"two geese bowed and the tuba player missed half a note."
        )
        world.say(
            f"{hero.id} marched on with that beloved {item.label} shining again, and folks later told "
            f"the tale as if the whole street had flashed like noon."
        )
    else:
        world.say(
            f"So {hero.id} wore the beloved {item.label} plain but proud, and somehow it looked even "
            f"dearer for having been worried over."
        )
        world.say(
            f"By sunset, the town was already laughing about the runaway sequin, and nobody doubted "
            f"that next parade would bring a sparkle twice as big."
        )


def tell(
    item_cfg: ItemCfg,
    sequin_cfg: SequinCfg,
    gust_cfg: GustCfg,
    spot_cfg: SpotCfg,
    method_cfg: MethodCfg,
    hero_name: str = "Mabel",
    hero_gender: str = "girl",
    helper_type: str = "aunt",
    trait: str = "cheerful",
) -> World:
    world = World()
    hero = world.add(
        Entity(
            id="hero",
            kind="character",
            type=hero_gender,
            label=hero_name,
            phrase=hero_name,
            role="hero",
            traits=[trait],
            attrs={"name": hero_name},
        )
    )
    helper = world.add(
        Entity(
            id="helper",
            kind="character",
            type=helper_type,
            label="the helper",
            phrase="the helper",
            role="helper",
        )
    )
    item = world.add(
        Entity(
            id="item",
            kind="thing",
            type=item_cfg.id,
            label=item_cfg.label,
            phrase=item_cfg.phrase,
            role="beloved_item",
            tags=set(item_cfg.tags),
        )
    )
    sequin = world.add(
        Entity(
            id="sequin",
            kind="thing",
            type="sequin",
            label=sequin_cfg.label,
            phrase=sequin_cfg.phrase,
            role="sequin",
            tags=set(sequin_cfg.tags),
        )
    )
    sequin.meters["attached"] = 1.0
    item.meters["shiny"] = 1.0
    item.memes["beloved"] = 1.0

    world.facts.update(
        hero=hero,
        helper=helper,
        item=item,
        sequin=sequin,
        item_cfg=item_cfg,
        sequin_cfg=sequin_cfg,
        gust_cfg=gust_cfg,
        spot_cfg=spot_cfg,
        method_cfg=method_cfg,
    )

    intro(world)
    world.para()
    parade_setup(world)
    blast_scene(world)
    land(world, spot_cfg)

    world.para()
    helper_plan(world, spot_cfg, method_cfg)
    use_method(world, method_cfg, spot_cfg)

    recovered = sequin.meters["recovered"] >= THRESHOLD
    world.para()
    if recovered:
        reattach(world)
    else:
        patch_plain(world)
    ending_image(world, recovered)

    world.facts.update(
        recovered=recovered,
        spot=spot_cfg,
        method=method_cfg,
        gust=gust_cfg,
        outcome="recovered" if recovered else "plain_proud",
    )
    return world


KNOWLEDGE = {
    "sequin": [
        (
            "What is a sequin?",
            "A sequin is a small shiny decoration sewn onto clothes or costumes. It catches light and makes things sparkle."
        )
    ],
    "parade": [
        (
            "What is a parade?",
            "A parade is a line of people, music, or floats moving down a street for everyone to watch. It is often bright, noisy, and festive."
        )
    ],
    "tuba": [
        (
            "What is a tuba?",
            "A tuba is a very large brass instrument. It makes deep, booming notes."
        )
    ],
    "goose": [
        (
            "Why can a goose sound so loud?",
            "A goose can honk very loudly because it pushes air through its throat in a strong burst. The sound carries far."
        )
    ],
    "ladder": [
        (
            "What is a ladder for?",
            "A ladder helps people reach high places safely. You climb it step by step."
        )
    ],
    "pie": [
        (
            "Why would a sticky pie hold a shiny thing?",
            "Sticky filling can grab and hold small things that fall into it. That is why getting them back can be messy."
        )
    ],
    "rake": [
        (
            "What does a rake do?",
            "A rake gathers or pulls things toward you with its long handle and teeth. It can help reach things a little farther away."
        )
    ],
    "roof": [
        (
            "Why is a roof hard to reach?",
            "A roof is high up and often slanted, so things can slide and hands cannot easily reach them from the ground."
        )
    ],
    "tree": [
        (
            "Why can things get stuck in a tree?",
            "Branches and leaves can catch light objects and hold them above your head. That makes them tricky to take down."
        )
    ],
    "hay": [
        (
            "Why can a small shiny thing disappear in hay?",
            "Hay is made of many pale, crinkly strands. A tiny object can sink between them and hide."
        )
    ],
}
KNOWLEDGE_ORDER = ["sequin", "parade", "tuba", "goose", "ladder", "pie", "rake", "roof", "tree", "hay"]


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    item = world.facts["item"]
    sequin = world.facts["sequin"]
    gust = world.facts["gust"]
    spot = world.facts["spot"]
    outcome = world.facts["outcome"]
    if outcome == "recovered":
        return [
            f'Write a funny tall-tale story for a 3-to-5-year-old that includes the words "sequin" and "beloved".',
            f"Tell a humorous parade story where {hero.attrs['name']}'s beloved {item.label} loses a giant {sequin.label} when a {gust.label} blasts through town, and a helper gets it back from {spot.label}.",
            f"Write a tall tale with a runaway sequin, a comic gust, and a happy ending where the beloved parade item shines again.",
        ]
    return [
        f'Write a funny tall-tale story for a 3-to-5-year-old that includes the words "sequin" and "beloved".',
        f"Tell a humorous parade story where {hero.attrs['name']}'s beloved {item.label} loses a giant {sequin.label} when a {gust.label} blasts through town, but the helper cannot get it back from {spot.label}.",
        f"Write a tall tale with a runaway sequin and a warm ending where the item is still beloved even without its sparkle.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    item = f["item"]
    sequin = f["sequin"]
    gust = f["gust"]
    spot = f["spot"]
    method = f["method"]
    hero_name = hero.attrs["name"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero_name}, a child with a beloved {item.label}, and {hero.pronoun('possessive')} {helper.label_word} who tries to help. The whole problem begins because the shiny sequin matters so much to {hero_name}.",
        ),
        (
            f"Why was the {item.label} special to {hero_name}?",
            f"The {item.label} was beloved because it was {hero_name}'s proud parade thing, and the giant sequin was the favorite part. Losing that sparkle made the item feel suddenly plain and made {hero_name} worry.",
        ),
        (
            f"What knocked the sequin loose?",
            f"A {gust.label} did it. In this tall tale, the blast was so huge that it popped the sequin off and sent it flying through town.",
        ),
        (
            "Where did the sequin land?",
            f"It landed on {spot.phrase}. That landing spot matters because it decided what kind of rescue could work.",
        ),
    ]
    if f["recovered"]:
        qa.append(
            (
                f"How did {helper.label_word} get the sequin back?",
                f"{helper.label_word.capitalize()} used {method.phrase} and got the sequin back. That worked because the method could really reach {spot.phrase} and handle the way the sequin was stuck there.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"The sequin was stitched back onto the beloved {item.label}, and {hero_name} went back into the parade shining again. The ending proves the change because the once-plain item sparkles once more.",
            )
        )
    else:
        qa.append(
            (
                f"Why did {helper.label_word}'s plan fail?",
                f"The plan failed because {method.phrase} did not fit {spot.phrase}. It either could not reach high enough or could not handle the way the sequin was caught there.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"The sequin stayed lost, but {hero_name} still wore the beloved {item.label} with pride. The ending changes the feeling of the story because the child learns a beloved thing can still matter even when one sparkle is gone.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"sequin", "parade"}
    gust = world.facts["gust"]
    spot = world.facts["spot"]
    method = world.facts["method"]
    if "tuba" in gust.tags:
        tags.add("tuba")
    if "goose" in gust.tags:
        tags.add("goose")
    if method.id == "ladder":
        tags.add("ladder")
    if method.id == "rake":
        tags.add("rake")
    if spot.id == "pie":
        tags.add("pie")
    if spot.id == "roof":
        tags.add("roof")
    if spot.id == "tree":
        tags.add("tree")
    if spot.id == "hay":
        tags.add("hay")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        item="hat",
        sequin="star",
        gust="goose_honk",
        spot="tree",
        method="rake",
        hero_name="Mabel",
        hero_gender="girl",
        helper_type="aunt",
        trait="grinning",
    ),
    StoryParams(
        item="boot",
        sequin="moon",
        gust="tuba_blast",
        spot="pie",
        method="spatula",
        hero_name="Otis",
        hero_gender="boy",
        helper_type="father",
        trait="lively",
    ),
    StoryParams(
        item="cape",
        sequin="sun",
        gust="mule_sneeze",
        spot="roof",
        method="ladder",
        hero_name="Ruby",
        hero_gender="girl",
        helper_type="uncle",
        trait="sparky",
    ),
    StoryParams(
        item="hat",
        sequin="star",
        gust="tuba_blast",
        spot="roof",
        method="spatula",
        hero_name="Jeb",
        hero_gender="boy",
        helper_type="mother",
        trait="boastful",
    ),
]


ASP_RULES = r"""
% reasonableness of the runaway moment
risk(I,Sq,G) :- item(I), sequin(Sq), gust(G),
                attachment(I,A), weight(Sq,W), power(G,P), P >= A + W - 1.

valid(I,Sq,G,Sp) :- risk(I,Sq,G), spot(Sp).

% sensible methods
sensible(M) :- method(M), sense(M,S), sense_min(Min), S >= Min.

% recovery logic
fits(M,Sp) :- method(M), spot(Sp), reach(M,R), height(Sp,H), R >= H,
              sticky(Sp), works_sticky(M).
fits(M,Sp) :- method(M), spot(Sp), reach(M,R), height(Sp,H), R >= H,
              snaggy(Sp), works_snaggy(M).
fits(M,Sp) :- method(M), spot(Sp), reach(M,R), height(Sp,H), R >= H,
              soft(Sp), works_soft(M).
fits(M,Sp) :- method(M), spot(Sp), reach(M,R), height(Sp,H), R >= H,
              plain_spot(Sp).

outcome(recovered) :- chosen_method(M), chosen_spot(Sp), fits(M,Sp).
outcome(plain_proud) :- chosen_method(M), chosen_spot(Sp), not fits(M,Sp).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        lines.append(asp.fact("attachment", item_id, item.attachment))
    for sequin_id, sequin in SEQUINS.items():
        lines.append(asp.fact("sequin", sequin_id))
        lines.append(asp.fact("weight", sequin_id, sequin.weight))
    for gust_id, gust in GUSTS.items():
        lines.append(asp.fact("gust", gust_id))
        lines.append(asp.fact("power", gust_id, gust.power))
    for spot_id, spot in SPOTS.items():
        lines.append(asp.fact("spot", spot_id))
        lines.append(asp.fact("height", spot_id, spot.height))
        if spot.sticky:
            lines.append(asp.fact("sticky", spot_id))
        if spot.snaggy:
            lines.append(asp.fact("snaggy", spot_id))
        if spot.soft:
            lines.append(asp.fact("soft", spot_id))
        if not (spot.sticky or spot.snaggy or spot.soft):
            lines.append(asp.fact("plain_spot", spot_id))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("sense", method_id, method.sense))
        lines.append(asp.fact("reach", method_id, method.reach))
        if method.works_sticky:
            lines.append(asp.fact("works_sticky", method_id))
        if method.works_snaggy:
            lines.append(asp.fact("works_snaggy", method_id))
        if method.works_soft:
            lines.append(asp.fact("works_soft", method_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_methods() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(m for (m,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_spot", params.spot),
            asp.fact("chosen_method", params.method),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def outcome_of(params: StoryParams) -> str:
    return "recovered" if method_works(METHODS[params.method], SPOTS[params.spot]) else "plain_proud"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a runaway sequin in a humorous tall tale parade."
    )
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--sequin", choices=SEQUINS)
    ap.add_argument("--gust", choices=GUSTS)
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos and sensible methods from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.item and args.sequin and args.gust:
        if not sequin_at_risk(ITEMS[args.item], SEQUINS[args.sequin], GUSTS[args.gust]):
            raise StoryError(explain_rejection(ITEMS[args.item], SEQUINS[args.sequin], GUSTS[args.gust]))
    if args.method and METHODS[args.method].sense < SENSE_MIN:
        if args.spot:
            raise StoryError(explain_method(args.method, args.spot))
        raise StoryError(
            f"(Refusing method '{args.method}': it scores below the common-sense floor for this world.)"
        )

    combos = [
        c
        for c in valid_combos()
        if (args.item is None or c[0] == args.item)
        and (args.sequin is None or c[1] == args.sequin)
        and (args.gust is None or c[2] == args.gust)
        and (args.spot is None or c[3] == args.spot)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    item_id, sequin_id, gust_id, spot_id = rng.choice(sorted(combos))
    if args.method:
        method_id = args.method
        if not method_works(METHODS[method_id], SPOTS[spot_id]):
            raise StoryError(explain_method(method_id, spot_id))
    else:
        method_id = rng.choice(sorted(m.id for m in sensible_methods()))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["mother", "father", "aunt", "uncle"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        item=item_id,
        sequin=sequin_id,
        gust=gust_id,
        spot=spot_id,
        method=method_id,
        hero_name=name,
        hero_gender=gender,
        helper_type=helper,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    for field_name, table in (
        ("item", ITEMS),
        ("sequin", SEQUINS),
        ("gust", GUSTS),
        ("spot", SPOTS),
        ("method", METHODS),
    ):
        key = getattr(params, field_name)
        if key not in table:
            raise StoryError(f"(Invalid {field_name}: {key})")
    if not sequin_at_risk(ITEMS[params.item], SEQUINS[params.sequin], GUSTS[params.gust]):
        raise StoryError(explain_rejection(ITEMS[params.item], SEQUINS[params.sequin], GUSTS[params.gust]))
    world = tell(
        item_cfg=ITEMS[params.item],
        sequin_cfg=SEQUINS[params.sequin],
        gust_cfg=GUSTS[params.gust],
        spot_cfg=SPOTS[params.spot],
        method_cfg=METHODS[params.method],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        helper_type=params.helper_type,
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


def asp_verify() -> int:
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP valid combos match Python ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    c_methods = set(asp_sensible_methods())
    p_methods = {m.id for m in sensible_methods()}
    if c_methods == p_methods:
        print(f"OK: sensible methods match ({sorted(c_methods)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible methods: clingo={sorted(c_methods)} python={sorted(p_methods)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(30):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            rc = 1
            print(f"FAILED: resolve_params crashed at seed {seed}.")
            continue
        p.seed = seed
        cases.append(p)

    bad = 0
    for p in cases:
        if asp_outcome(p) != outcome_of(p):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test failed: generated empty story.)")
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"FAILED: smoke generation crashed: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible methods: {', '.join(asp_sensible_methods())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (item, sequin, gust, spot) combos:\n")
        for item_id, sequin_id, gust_id, spot_id in combos:
            print(f"  {item_id:6} {sequin_id:6} {gust_id:11} {spot_id}")
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
            header = (
                f"### {p.hero_name}: {p.item} / {p.sequin} / {p.gust} / {p.spot} "
                f"({outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
